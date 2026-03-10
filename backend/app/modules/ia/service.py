"""
IA Service — Lógica de negocio para la interacción con Ollama.
Responsabilidades:
  - Construir contexto del usuario
  - Normalizar números en el texto
  - Llamar a Ollama con el prompt adecuado
  - Procesar la respuesta y persistir en BD
"""
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import date
import httpx
import json

from app.models.transaccion import Transaccion
from app.models.cuenta import Cuenta
from app.models.categoria import Categoria
from app.models.movimiento_recurrente import MovimientoRecurrente
from app.models.meta_ahorro import MetaAhorro
from app.models.prestamo import Prestamo

from .number_parser import parse_colombian_numbers, validate_amount
from .prompts import get_system_prompt

OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = "llama3"


def build_user_context(db: Session, user_id) -> str:
    """Build financial context string for the user."""
    cuentas = db.query(Cuenta).filter(Cuenta.usuario_id == user_id, Cuenta.activa == True).all()
    categorias = db.query(Categoria).filter(
        (Categoria.usuario_id == user_id) | (Categoria.usuario_id == None)
    ).all()
    recurrentes = db.query(MovimientoRecurrente).filter(
        MovimientoRecurrente.usuario_id == user_id,
        MovimientoRecurrente.activo == True,
    ).all()

    mes = date.today().month
    anio = date.today().year
    txns_mes = db.query(Transaccion).filter(
        Transaccion.usuario_id == user_id,
        extract('month', Transaccion.fecha) == mes,
        extract('year', Transaccion.fecha) == anio,
    ).all()

    parts = []

    if cuentas:
        parts.append("Cuentas:")
        for c in cuentas:
            nomina = " [NÓMINA]" if c.es_nomina else ""
            if c.tipo.value == "TARJETA_CREDITO" and c.cupo_total:
                parts.append(f"- {c.nombre} (TC{nomina}): Cupo ${float(c.cupo_total):,.0f}, disponible ${float(c.saldo):,.0f}")
            else:
                parts.append(f"- {c.nombre}{nomina}: ${float(c.saldo):,.0f}")

    if recurrentes:
        parts.append("Recurrentes:")
        for r in recurrentes:
            rn = r.nombre.lower().strip()
            pagado = any(
                rn in (t.descripcion or "").lower().strip()
                or (t.descripcion or "").lower().strip() in rn
                for t in txns_mes
            )
            parts.append(f"- {r.nombre}: ${float(r.monto):,.0f} día {r.dia_mes} {'✅' if pagado else '⏳'}")

    if categorias:
        parts.append("Categorías: " + ", ".join(f"{c.nombre}({c.tipo.value})" for c in categorias))

    ingresos = sum(float(t.monto) for t in txns_mes if t.tipo.value == "INGRESO")
    gastos = sum(float(t.monto) for t in txns_mes if t.tipo.value != "INGRESO")
    parts.append(f"Mes actual: Ingresos ${ingresos:,.0f}, Gastos ${gastos:,.0f}, Balance ${ingresos - gastos:,.0f}")

    return "\n".join(parts) if parts else "Sin datos aún."


def find_account_by_name(cuentas: list, name: str):
    """Find an account by partial name match."""
    if not name:
        return None
    name_lower = name.lower()
    for c in cuentas:
        if name_lower in c.nombre.lower() or c.nombre.lower() in name_lower:
            return c
    return None


def get_default_account(cuentas: list):
    """Get default account: nómina first, then first non-credit-card, then any."""
    # Priority 1: nómina account
    for c in cuentas:
        if c.es_nomina:
            return c
    # Priority 2: first non-credit-card
    for c in cuentas:
        if c.tipo.value != "TARJETA_CREDITO":
            return c
    # Fallback: first account
    return cuentas[0] if cuentas else None


def find_or_create_category(db: Session, user_id, nombre: str, tipo: str):
    """Find existing category or create. Compares decrypted names in Python (encrypted DB)."""
    all_cats = db.query(Categoria).filter(Categoria.usuario_id == user_id).all()
    nombre_lower = nombre.lower().strip()
    for cat in all_cats:
        cat_name = (cat.nombre or "").lower().strip()
        if cat_name == nombre_lower or nombre_lower in cat_name or cat_name in nombre_lower:
            return cat
    cat = Categoria(usuario_id=user_id, nombre=nombre, tipo=tipo)
    db.add(cat)
    return cat


def build_chat_prompt(text: str) -> str:
    """Build prompt with ONLY the current user message. No chat history to LLM."""
    return f"Usuario: {text}"


async def call_ollama(prompt: str, system: str) -> dict:
    """Call Ollama API and return parsed JSON."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1, "num_predict": 1024}
            }
        )
        result = response.json()
        return json.loads(result.get("response", "{}"))


async def process_ia_request(
    text: str,
    mode: str,
    history: Optional[List[dict]],
    db: Session,
    current_user,
) -> Dict[str, Any]:
    """Main IA processing pipeline."""
    # 1. Normalize numbers in the user text
    normalized_text, extracted_montos = parse_colombian_numbers(text)

    # 2. Build context and prompt (NO chat history — only financial context in system prompt)
    user_context = build_user_context(db, current_user.id)
    system_prompt = get_system_prompt(mode, user_context)
    chat_prompt = build_chat_prompt(normalized_text)

    try:
        # 3. Call LLM
        parsed = await call_ollama(chat_prompt, system_prompt)
    except json.JSONDecodeError:
        return {"reply": "No pude entender la respuesta.", "saved": False}
    except httpx.ConnectError:
        return {"reply": "⚠️ IA no disponible. Intenta en unos segundos.", "saved": False}
    except Exception as e:
        return {"reply": f"Error: {str(e)}", "saved": False}

    reply = parsed.get("reply", "Procesado.")

    cuentas = db.query(Cuenta).filter(
        Cuenta.usuario_id == current_user.id, Cuenta.activa == True
    ).all()

    # 4. Process by mode
    if mode == "transaccion":
        return _process_transaccion(parsed, extracted_montos, cuentas, db, current_user, text, reply)
    elif mode == "recurrente":
        return _process_recurrente(parsed, extracted_montos, cuentas, db, current_user, text, reply)
    elif mode == "prestamo":
        return _process_prestamo(parsed, extracted_montos, cuentas, db, current_user, reply)
    elif mode == "meta":
        return _process_meta(parsed, extracted_montos, db, current_user, reply)
    elif mode == "categoria":
        return _process_categoria(parsed, db, current_user, reply)
    else:
        return {"reply": reply, "saved": False}


def _get_amount(ia_amount, extracted_montos: List[float], index: int = 0) -> float:
    """Get amount: prefer extracted regex amount, fallback to IA amount."""
    if extracted_montos and index < len(extracted_montos):
        return extracted_montos[index]
    if ia_amount:
        val = abs(float(ia_amount))
        if validate_amount(val):
            return val
    return 0


def _resolve_amount_from_recurrents(db, user_id, description: str) -> float:
    """If no amount given, try to find a matching recurrent and use its amount."""
    if not description:
        return 0
    keywords = description.lower().split()
    recurrents = db.query(MovimientoRecurrente).filter(
        MovimientoRecurrente.usuario_id == user_id,
        MovimientoRecurrente.activo == True,
    ).all()
    for rec in recurrents:
        rec_name = (rec.nombre or "").lower()
        for kw in keywords:
            if len(kw) > 2 and kw in rec_name:
                return float(rec.monto)
    return 0


def _process_transaccion(parsed, montos, cuentas, db, user, original_text, reply):
    items = parsed.get("data", [])
    if not items and parsed.get("monto"):
        items = [parsed]

    if not items:
        return {"reply": reply, "saved": False}

    saved = 0
    pending_items = []  # Items without amount (need user input)

    for i, item in enumerate(items):
        amount = _get_amount(item.get("monto"), montos, i)

        # Fallback: resolve from recurrents if no amount found
        if amount <= 0:
            desc = item.get("descripcion", original_text)
            resolved = _resolve_amount_from_recurrents(db, user.id, desc)
            if resolved > 0:
                amount = resolved
                reply = reply.rstrip('.') + f" (monto tomado de tus recurrentes: ${int(amount):,})."

        if amount <= 0 or not validate_amount(amount):
            pending_items.append(item.get("descripcion", "item"))
            continue

        target = find_account_by_name(cuentas, item.get("cuenta_nombre", ""))
        if not target and cuentas:
            target = get_default_account(cuentas)
        if target:
            txn = Transaccion(
                usuario_id=user.id,
                cuenta_id=target.id,
                tipo=item.get("tipo", "GASTO_VARIABLE"),
                monto=amount,
                fecha=date.today(),
                descripcion=item.get("descripcion", original_text),
                fuente_ia=True,
                texto_original=original_text,
            )
            db.add(txn)
            saved += 1

    if saved:
        db.commit()
        msg = reply
        if pending_items:
            msg += f"\n⚠️ No pude registrar: {', '.join(pending_items)} — dime el monto para completar."
        return {"reply": msg, "saved": True, "saved_count": saved}

    if pending_items:
        names = ", ".join(pending_items)
        return {"reply": f"Entendido, quieres registrar: {names}. ¿Cuánto fue?", "saved": False}
    return {"reply": reply or "⚠️ No pude identificar transacciones.", "saved": False}


def _process_recurrente(parsed, montos, cuentas, db, user, original_text, reply):
    # Support array of items (multiple recurrents)
    items = parsed.get("data", [])
    if not items and parsed.get("monto"):
        items = [parsed]  # Backward compat: single item

    if not items:
        return {"reply": reply, "saved": False}

    saved = 0
    for i, item in enumerate(items):
        amount = _get_amount(item.get("monto"), montos, i)
        if amount <= 0:
            continue
        target = find_account_by_name(cuentas, item.get("cuenta_nombre", ""))
        if not target:
            target = get_default_account(cuentas)
        if target:
            rec = MovimientoRecurrente(
                usuario_id=user.id,
                cuenta_id=target.id,
                nombre=item.get("nombre", original_text),
                tipo=item.get("tipo", "GASTO_FIJO"),
                monto=amount,
                dia_mes=item.get("dia_mes", 1),
            )
            db.add(rec)
            cat_name = item.get("categoria_sugerida")
            if cat_name:
                find_or_create_category(db, user.id, cat_name, item.get("tipo", "GASTO_FIJO"))
            saved += 1

    if saved:
        db.commit()
        return {"reply": reply, "saved": True, "action": "recurrente", "saved_count": saved}
    return {"reply": "⚠️ No tienes cuentas activas.", "saved": False}


def _process_prestamo(parsed, montos, cuentas, db, user, reply):
    # Extract from data array (v2 prompts)
    data_arr = parsed.get("data", [])
    item = data_arr[0] if data_arr else parsed

    saldo = _get_amount(item.get("saldo_pendiente"), montos, 0)
    if saldo <= 0:
        return {"reply": reply, "saved": False}
    monto_total = _get_amount(item.get("monto_total"), montos, 1) or saldo
    cuota = _get_amount(item.get("cuota_mensual"), montos, 2) if len(montos) > 2 else abs(float(item.get("cuota_mensual", 0) or 0))

    p = Prestamo(
        usuario_id=user.id,
        entidad=item.get("entidad", "Préstamo"),
        tipo=item.get("tipo", "BANCO"),
        monto_total=monto_total,
        saldo_pendiente=saldo,
        cuota_mensual_esperada=cuota,
        dia_pago=item.get("dia_pago"),
        estado="ACTIVO",
    )
    db.add(p)

    target = find_account_by_name(cuentas, item.get("cuenta_nombre", ""))
    if not target:
        target = get_default_account(cuentas)
    if cuota > 0 and target:
        rec = MovimientoRecurrente(
            usuario_id=user.id,
            cuenta_id=target.id,
            nombre=f"Cuota {item.get('entidad', 'Préstamo')}",
            tipo="PRESTAMO_CUOTA",
            monto=cuota,
            dia_mes=item.get("dia_pago") or 1,
        )
        db.add(rec)
    db.commit()
    return {"reply": reply, "saved": True, "action": "prestamo"}


def _process_meta(parsed, montos, db, user, reply):
    data_arr = parsed.get("data", [])
    item = data_arr[0] if data_arr else parsed

    amount = _get_amount(item.get("monto_objetivo"), montos)
    if amount <= 0:
        return {"reply": reply, "saved": False}
    meta = MetaAhorro(
        usuario_id=user.id,
        nombre=item.get("nombre", "Meta de ahorro"),
        monto_objetivo=amount,
        monto_actual=0,
        fecha_objetivo=item.get("fecha_objetivo"),
    )
    db.add(meta)
    db.commit()
    return {"reply": reply, "saved": True, "action": "meta"}


def _process_categoria(parsed, db, user, reply):
    data_arr = parsed.get("data", [])
    item = data_arr[0] if data_arr else parsed

    if not item.get("nombre"):
        return {"reply": reply, "saved": False}
    find_or_create_category(db, user.id, item["nombre"], item.get("tipo", "GASTO_VARIABLE"))
    db.commit()
    return {"reply": reply, "saved": True, "action": "categoria"}

