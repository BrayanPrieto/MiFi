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

from app.core.config import settings
from .prompts import get_system_prompt
from app.modules.ciclo.service import resumen_ciclo

OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL = settings.OLLAMA_MODEL


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
    ).order_by(Transaccion.fecha.desc(), Transaccion.created_at.desc()).all()

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
            parts.append(f"- {r.nombre}: ${float(r.monto):,.0f} día {r.dia_mes} [{'pagado' if pagado else 'pendiente'}]")

    if categorias:
        parts.append("Categorías: " + ", ".join(f"{c.nombre}({c.tipo.value})" for c in categorias))

    ingresos = sum(float(t.monto) for t in txns_mes if t.tipo.value == "INGRESO")
    gastos = sum(float(t.monto) for t in txns_mes if t.tipo.value != "INGRESO")
    parts.append(f"Mes actual: Ingresos ${ingresos:,.0f}, Gastos ${gastos:,.0f}, Balance ${ingresos - gastos:,.0f}")
    
    ultimas_txns = txns_mes[:10]  # Take the 10 most recent
    if ultimas_txns:
        parts.append("Últimas 10 transacciones (con ID para borrar/editar):")
        for t in ultimas_txns:
            monto_fmt = f"${float(t.monto):,.0f}"
            signo = "+" if t.tipo.value == "INGRESO" else "-"
            parts.append(f"  - [{t.id}] {t.fecha} | {t.descripcion}: {signo}{monto_fmt}")

    # RETRIEVAL: proyección del ciclo (motor determinista) como fuente de verdad para consultas
    parts.append(_build_projection_context(db, user_id))

    return "\n".join(parts) if parts else "Sin datos aún."


def _build_projection_context(db: Session, user_id) -> str:
    """Recupera el resumen del ciclo y lo formatea como hechos para el LLM (RAG)."""
    try:
        r = resumen_ciclo(db, user_id, date.today().month, date.today().year)
    except Exception:
        return ""
    lines = ["[PROYECCIÓN DEL CICLO]"]
    lines.append(f"- Diezmo mensual (10%): ${r['diezmo_total']:,.0f} | Caja menor: ${r['caja_menor_total']:,.0f}")
    lines.append(f"- Remanente Q1: ${r['quincena_1']['remanente']:,.0f} | Remanente Q2: ${r['quincena_2']['remanente']:,.0f}")
    lines.append(f"- Flujo libre mensual (día {r['dia_disparo']}): ${r['flujo_libre_ajustado']:,.0f}")
    lines.append(f"- Semáforo quincena {r['quincena_actual']}: {r['semaforo']} (pendiente ${r['pendiente_actual']:,.0f}, disponible ${r['saldo_disponible']:,.0f})")
    d = r.get("deuda_objetivo")
    if d:
        meses = d["meses_estimados"]
        meses_txt = f"~{meses} meses" if meses is not None else "no proyectable (flujo insuficiente)"
        lines.append(
            f"- Deuda objetivo: {d['entidad']}, saldo ${d['saldo_pendiente']:,.0f}, "
            f"cuota ${d['cuota_mensual']:,.0f}, ataque mensual ${d['pago_mensual_proyectado']:,.0f} → {meses_txt}"
        )
    return "\n".join(lines)


def find_account_by_name(cuentas: list, name: str):
    """Find an account by partial name match."""
    if not name:
        return None
    name_lower = name.lower()
    for c in cuentas:
        if name_lower in c.nombre.lower() or c.nombre.lower() in name_lower:
            return c
    return None


def match_tarjeta(cuentas: list, nombre: str):
    """Encuentra la TARJETA_CREDITO cuyo nombre está contenido en el nombre del recurrente.

    'Cuota Bancolombia VISA' -> tarjeta 'Bancolombia VISA' (por overlap de tokens).
    """
    n = (nombre or "").lower()
    for c in cuentas:
        if c.tipo.value != "TARJETA_CREDITO":
            continue
        tokens = [t for t in (c.nombre or "").lower().split() if len(t) >= 2]
        if tokens and all(t in n for t in tokens):
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


import re

# Filtro central: garantiza que ninguna respuesta al usuario contenga emojis
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002B00-\U00002BFF\U0000FE00-\U0000FE0F\U0000200D\U000023E0-\U000023FF\U00002190-\U000021FF]+",
    flags=re.UNICODE,
)


def strip_emojis(text: str) -> str:
    if not text:
        return text
    return re.sub(r"[ ]{2,}", " ", _EMOJI_RE.sub("", text)).strip()


_TIPOS_VALIDOS = {"INGRESO", "GASTO_FIJO", "GASTO_VARIABLE", "PRESTAMO_CUOTA", "AHORRO"}


def _norm_tipo(raw, default: str = "GASTO_VARIABLE") -> str:
    """Normaliza cualquier variante que devuelva el LLM a un enum válido.

    Corrige casos como 'INGRESO_FIJO' -> 'INGRESO', 'SUELDO' -> 'INGRESO', etc.
    """
    t = str(raw or "").upper().strip()
    if t in _TIPOS_VALIDOS:
        return t
    if any(k in t for k in ("INGRESO", "SUELDO", "NOMINA", "NÓMINA", "SALARIO")):
        return "INGRESO"
    if any(k in t for k in ("PRESTAMO", "PRÉSTAMO", "CUOTA", "DEUDA")):
        return "PRESTAMO_CUOTA"
    if "AHORRO" in t:
        return "AHORRO"
    if "FIJO" in t:
        return "GASTO_FIJO"
    if "VARIABLE" in t:
        return "GASTO_VARIABLE"
    return default


from .number_parser import parse_colombian_numbers


def build_chat_prompt(text: str) -> str:
    """Normaliza los montos del texto de forma determinista antes de mandarlo al LLM.

    '700 mil' -> '[MONTO:700000]', '4 millones' -> '[MONTO:4000000]'. Así el modelo
    ya no adivina números: solo copia el entero del token.
    """
    normalized, montos = parse_colombian_numbers(text)
    hint = ""
    if montos:
        hint = "\n(Montos detectados, usa EXACTAMENTE estos enteros: " + ", ".join(str(int(m)) for m in montos) + ")"
    return f"Usuario: {normalized}{hint}"


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
        if "error" in result:
            raise Exception(f"Ollama error: {result['error']}")
            
        raw_response = result.get("response", "{}")
        # Remove <think>...</think> tags and their contents commonly found in deepseek reasoning models
        clean_response = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL).strip()
        
        return json.loads(clean_response)


async def process_ia_request(
    text: str,
    mode: str,
    history: Optional[List[dict]],
    db: Session,
    current_user,
) -> Dict[str, Any]:
    """Main IA processing pipeline."""
    # 1. Build context and prompt (NO chat history — only financial context in system prompt)
    user_context = build_user_context(db, current_user.id)
    # FORZAMOS USAR EL PROMPT UNIFICADO que decide qué acción hacer
    system_prompt = get_system_prompt("unificado", user_context)
    chat_prompt = build_chat_prompt(text)

    try:
        # 3. Call LLM
        parsed = await call_ollama(chat_prompt, system_prompt)
    except json.JSONDecodeError:
        return {"reply": "No pude entender la respuesta.", "saved": False}
    except httpx.ConnectError:
        return {"reply": "IA no disponible. Intenta en unos segundos.", "saved": False}
    except Exception as e:
        return {"reply": f"Error: {str(e)}", "saved": False}

    reply = parsed.get("reply", "Procesado.")
    action = parsed.get("action", "general")

    cuentas = db.query(Cuenta).filter(
        Cuenta.usuario_id == current_user.id, Cuenta.activa == True
    ).all()

    # 4. Process by action returned by the unified prompt
    if action == "transaccion":
        return _process_transaccion(parsed, cuentas, db, current_user, text, reply)
    elif action == "recurrente":
        return _process_recurrente(parsed, cuentas, db, current_user, text, reply)
    elif action == "prestamo":
        return _process_prestamo(parsed, cuentas, db, current_user, reply)
    elif action == "meta":
        return _process_meta(parsed, db, current_user, reply)
    elif action == "categoria":
        return _process_categoria(parsed, db, current_user, reply)
    elif action == "delete_transaccion":
        return _process_delete_transaccion(parsed, db, current_user, reply)
    elif action == "update_transaccion":
        return _process_update_transaccion(parsed, db, current_user, reply)
    elif action == "cuenta":
        return _process_cuenta(parsed, db, current_user, reply)
    else:
        return {"reply": reply, "saved": False}


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


def _process_transaccion(parsed, cuentas, db, user, original_text, reply):
    items = parsed.get("data", [])
    if not items and parsed.get("monto"):
        items = [parsed]

    if not items:
        return {"reply": reply, "saved": False}

    saved = 0
    pending_items = []  # Items without amount (need user input)

    for i, item in enumerate(items):
        try:
            amount = abs(float(item.get("monto", 0) or 0))
        except (ValueError, TypeError):
            amount = 0

        # Fallback: resolve from recurrents if no amount found
        if amount <= 0:
            desc = item.get("descripcion", original_text)
            resolved = _resolve_amount_from_recurrents(db, user.id, desc)
            if resolved > 0:
                amount = resolved
                reply = reply.rstrip('.') + f" (monto tomado de recurrentes: ${int(amount):,})."

        if amount <= 0:
            pending_items.append(item.get("descripcion", "item"))
            continue

        target = find_account_by_name(cuentas, item.get("cuenta_nombre", ""))
        if not target and cuentas:
            target = get_default_account(cuentas)
        if target:
            txn = Transaccion(
                usuario_id=user.id,
                cuenta_id=target.id,
                tipo=_norm_tipo(item.get("tipo"), "GASTO_VARIABLE"),
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
            msg += f"\nNo pude registrar: {', '.join(pending_items)} — dime el monto para completar."
        return {"reply": msg, "saved": True, "saved_count": saved}

    if pending_items:
        names = ", ".join(pending_items)
        return {"reply": f"Entendido, quieres registrar: {names}. ¿Cuánto fue?", "saved": False}
    return {"reply": reply or "No pude identificar transacciones.", "saved": False}


def _process_recurrente(parsed, cuentas, db, user, original_text, reply):
    # Support array of items (multiple recurrents)
    items = parsed.get("data", [])
    if not items and parsed.get("monto"):
        items = [parsed]  # Backward compat: single item

    if not items:
        return {"reply": reply, "saved": False}

    saved = 0
    for i, item in enumerate(items):
        try:
            amount = abs(float(item.get("monto", 0) or 0))
        except (ValueError, TypeError):
            amount = 0
            
        if amount <= 0:
            continue
        target = find_account_by_name(cuentas, item.get("cuenta_nombre", ""))
        if not target:
            target = get_default_account(cuentas)
        if target:
            tipo_norm = _norm_tipo(item.get("tipo"), "GASTO_FIJO")
            nombre_rec = item.get("nombre", original_text)
            tarjeta = match_tarjeta(cuentas, nombre_rec)  # cuota de tarjeta -> vincular
            rec = MovimientoRecurrente(
                usuario_id=user.id,
                cuenta_id=target.id,
                cuenta_destino_id=tarjeta.id if tarjeta else None,
                nombre=nombre_rec,
                tipo=tipo_norm,
                monto=amount,
                dia_mes=item.get("dia_mes", 1),
            )
            db.add(rec)
            cat_name = item.get("categoria_sugerida")
            if cat_name:
                find_or_create_category(db, user.id, cat_name, tipo_norm)
            saved += 1

    if saved:
        db.commit()
        return {"reply": reply, "saved": True, "action": "recurrente", "saved_count": saved}
    return {"reply": "No tienes cuentas activas.", "saved": False}


def _process_prestamo(parsed, cuentas, db, user, reply):
    # Extract from data array (v2 prompts)
    data_obj = parsed.get("data", [])
    if isinstance(data_obj, dict):
        data_obj = [data_obj]
    item = data_obj[0] if (isinstance(data_obj, list) and len(data_obj) > 0) else parsed

    try:
        saldo = abs(float(item.get("saldo_pendiente", 0) or 0))
        monto_total = abs(float(item.get("monto_total", 0) or 0)) or saldo
        cuota = abs(float(item.get("cuota_mensual", 0) or 0))
    except (ValueError, TypeError):
        return {"reply": "Error leyendo los valores numéricos del préstamo.", "saved": False}
        
    if saldo <= 0:
        return {"reply": reply, "saved": False}

    tipo_str = str(item.get("tipo", "BANCO")).upper()
    if tipo_str not in ["BANCO", "TERCERO"]:
        tipo_str = "BANCO" # Safe fallback to avoid DB parsing errors

    p = Prestamo(
        usuario_id=user.id,
        entidad=item.get("entidad", "Préstamo"),
        tipo=tipo_str,
        monto_total=monto_total,
        saldo_pendiente=saldo,
        cuota_mensual_esperada=cuota,
        dia_pago=item.get("dia_pago"),
        estado="ACTIVO",
    )
    db.add(p)

    target = find_account_by_name(cuentas, item.get("cuenta_nombre", ""))
    
    # NEW LOGIC: Tie this debt tightly to a Credit Card if names match
    matching_cc = next((c for c in cuentas if c.tipo.value == "TARJETA_CREDITO" and 
                        (p.entidad.lower() in c.nombre.lower() or c.nombre.lower() in p.entidad.lower())), None)
    
    if matching_cc:
        # For a credit card, 'saldo' represents the consumed debt. We increase it.
        matching_cc.saldo = float(matching_cc.saldo) + saldo
        reply += f"\nVinculé esta deuda a tu tarjeta de crédito '{matching_cc.nombre}' y actualicé su cupo consumido."
        # If no specific target account was given for the recurrent payment, use the CC
        if not target and cuota > 0:
            target = matching_cc

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


def _process_meta(parsed, db, user, reply):
    data_obj = parsed.get("data", [])
    if isinstance(data_obj, dict):
        data_obj = [data_obj]
    item = data_obj[0] if (isinstance(data_obj, list) and len(data_obj) > 0) else parsed

    try:
        amount = abs(float(item.get("monto_objetivo", 0) or 0))
    except (ValueError, TypeError):
        amount = 0
        
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
    data_obj = parsed.get("data", [])
    if isinstance(data_obj, dict):
        data_obj = [data_obj]
    item = data_obj[0] if (isinstance(data_obj, list) and len(data_obj) > 0) else parsed

    if not item.get("nombre"):
        return {"reply": reply, "saved": False}
    find_or_create_category(db, user.id, item["nombre"], item.get("tipo", "GASTO_VARIABLE"))
    db.commit()
    return {"reply": reply, "saved": True, "action": "categoria"}


def _process_delete_transaccion(parsed, db, user, reply):
    data_arr = parsed.get("data", [])
    item = data_arr[0] if data_arr else parsed
    txn_id = item.get("id")
    if not txn_id:
        return {"reply": "No encontré el ID de la transacción para borrar.", "saved": False}
        
    txn = db.query(Transaccion).filter(Transaccion.id == txn_id, Transaccion.usuario_id == user.id).first()
    if not txn:
        return {"reply": "Esa transacción no existe o ya fue borrada.", "saved": False}
        
    db.delete(txn)
    db.commit()
    return {"reply": reply, "saved": True, "action": "delete_transaccion"}


def _process_update_transaccion(parsed, db, user, reply):
    # Retrieve the target ID from parsed data payload.
    data_obj = parsed.get("data", [])
    if isinstance(data_obj, dict):
        data_obj = [data_obj]
    item = data_obj[0] if (isinstance(data_obj, list) and len(data_obj) > 0) else parsed
    
    txn_id_str = item.get("id")
    if not txn_id_str:
        return {"reply": "No pude identificar qué transacción editar.", "saved": False}
        
    try:
        txn = db.query(Transaccion).filter_by(id=txn_id_str, usuario_id=user.id).first()
        if not txn:
            return {"reply": "No encontré esa transacción para editarla.", "saved": False}
            
        monto_nuevo = item.get("monto")
        desc_nueva = item.get("descripcion")
        
        if monto_nuevo is not None:
            txn.monto = abs(float(monto_nuevo))
        if desc_nueva:
            txn.descripcion = desc_nueva
            
        db.commit()
        return {"reply": reply, "saved": True, "action": "update_transaccion"}
    except Exception as e:
        db.rollback()
        return {"reply": "Ocurrió un error al intentar editar la transacción.", "saved": False}

def _process_cuenta(parsed, db, user, reply):
    data_obj = parsed.get("data", [])
    if isinstance(data_obj, dict):
        data_obj = [data_obj]
    item = data_obj[0] if (isinstance(data_obj, list) and len(data_obj) > 0) else parsed

    nombre = item.get("nombre", "Nueva Cuenta")
    tipo_str = str(item.get("tipo", "EFECTIVO")).upper()
    
    # Validation against Enum mapping
    valid_types = ["EFECTIVO", "CUENTA_AHORROS", "CUENTA_CORRIENTE", "TARJETA_CREDITO", "BILLETERA_DIGITAL", "OTRO"]
    if tipo_str not in valid_types:
        tipo_str = "CUENTA_AHORROS"

    # For credit cards, limit goes to cupo_total. For others, it goes to saldo.
    cupo_total = None
    saldo = 0
    if tipo_str == "TARJETA_CREDITO":
        cupo_total = abs(float(item.get("cupo_total") or 0))
    else:
        saldo = abs(float(item.get("saldo") or item.get("cupo_total") or 0))

    try:
        nueva_cuenta = Cuenta(
            usuario_id=user.id,
            nombre=nombre,
            tipo=tipo_str,
            saldo=saldo,
            cupo_total=cupo_total,
            activa=True
        )
        db.add(nueva_cuenta)
        db.commit()
        return {"reply": reply, "saved": True, "action": "cuenta"}
    except Exception as e:
        db.rollback()
        return {"reply": "Ocurrió un error al intentar crear la cuenta.", "saved": False}
