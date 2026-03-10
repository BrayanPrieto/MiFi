from typing import Any, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx
import json
from datetime import date, timedelta
from decimal import Decimal

from app.api import deps
from app.models.transaccion import Transaccion
from app.models.cuenta import Cuenta
from app.models.categoria import Categoria
from app.models.movimiento_recurrente import MovimientoRecurrente
from app.models.meta_ahorro import MetaAhorro
from app.models.prestamo import Prestamo

router = APIRouter()

# ── System Prompts por Modo ──────────────────────────────────────────────

CONTEXT_HEADER = """## Contexto financiero del usuario
{user_context}

## REGLAS DE NÚMEROS (MUY IMPORTANTE)
- "50 mil" = 50000
- "300 mil" = 300000
- "1.5 millones" = 1500000
- "2 millones" = 2000000
- "50k" = 50000
- Monto SIEMPRE positivo y entero
- Responde en español colombiano
- Responde SOLO con JSON válido"""

PROMPTS = {
    "general": """Eres MiFi IA, asistente financiero personal.
{context}

Responde preguntas sobre las finanzas del usuario. Si pregunta cuánto tiempo para ahorrar X, calcula con su balance mensual promedio.

Formato de respuesta:
{{"reply": "Tu respuesta aquí"}}""",

    "transaccion": """Eres MiFi IA. Registras gastos e ingresos puntuales.
{context}

El usuario describe un gasto o ingreso. Extrae: tipo, monto, descripción, cuenta.
Puedes registrar MÚLTIPLES si menciona varios pagos.

Tipos: INGRESO, GASTO_FIJO, GASTO_VARIABLE, PRESTAMO_CUOTA, AHORRO

Formato (SIEMPRE array de items):
{{"items": [{{"tipo": "GASTO_VARIABLE", "monto": 50000, "descripcion": "Gasolina", "cuenta_nombre": "Bancolombia"}}], "reply": "✅ Registré $50,000 en gasolina."}}

Si son varios:
{{"items": [{{"tipo": "GASTO_FIJO", "monto": 1920000, "descripcion": "Arriendo", "cuenta_nombre": "Bancolombia"}}, {{"tipo": "GASTO_FIJO", "monto": 250000, "descripcion": "Comida perros Barf", "cuenta_nombre": "Bancolombia"}}], "reply": "✅ Registré 2 pagos."}}""",

    "recurrente": """Eres MiFi IA. Registras gastos o ingresos que se repiten CADA MES.
{context}

Extrae: nombre, tipo, monto, cuenta, día del mes.
Tipos: INGRESO, GASTO_FIJO, PRESTAMO_CUOTA, AHORRO
También sugiere una categoría apropiada (categoria_sugerida).

Formato:
{{"nombre": "Netflix", "tipo": "GASTO_FIJO", "monto": 50000, "cuenta_nombre": "Bancolombia", "dia_mes": 15, "categoria_sugerida": "Suscripciones", "reply": "✅ Registré Netflix ($50,000/mes) cada día 15."}}""",

    "prestamo": """Eres MiFi IA. Registras préstamos y deudas.
{context}

Extrae: entidad, monto_total, saldo_pendiente, cuota_mensual, día de pago, cuenta de pago.
Si es avance de tarjeta de crédito, usa la tarjeta como entidad.

Formato:
{{"entidad": "Nu", "tipo": "BANCO", "monto_total": 9900000, "saldo_pendiente": 9500000, "cuota_mensual": 1500000, "dia_pago": 5, "cuenta_nombre": "Bancolombia", "reply": "✅ Registré préstamo Nu: $9.5M pendientes, cuota $1.5M/mes."}}""",

    "meta": """Eres MiFi IA. Ayudas al usuario a crear metas de ahorro.
{context}

Si el usuario dice cuánto quiere ahorrar, calcula en cuántos meses puede lograrlo según su balance mensual.
Extrae: nombre de la meta, monto objetivo, fecha objetivo (opcional).

Formato:
{{"nombre": "Moto", "monto_objetivo": 16000000, "fecha_objetivo": "2026-12-01", "reply": "🎯 Meta 'Moto' creada: $16,000,000. Con tu balance actual podrías lograrlo en ~X meses."}}""",

    "categoria": """Eres MiFi IA. Creas categorías para organizar gastos.
{context}

Tipos disponibles: INGRESO, GASTO_FIJO, GASTO_VARIABLE, PRESTAMO_CUOTA, AHORRO
Sugiere el tipo más apropiado según el nombre.

Formato:
{{"nombre": "Suscripciones", "tipo": "GASTO_FIJO", "reply": "📁 Categoría 'Suscripciones' creada como Gasto Fijo."}}""",
}


class IARequest(BaseModel):
    text: str
    mode: str = "general"
    history: Optional[List[dict]] = None  # [{role: "user"/"assistant", content: "..."}]


def build_user_context(db: Session, user_id) -> str:
    cuentas = db.query(Cuenta).filter(Cuenta.usuario_id == user_id, Cuenta.activa == True).all()
    categorias = db.query(Categoria).filter(
        (Categoria.usuario_id == user_id) | (Categoria.usuario_id == None)
    ).all()
    recurrentes = db.query(MovimientoRecurrente).filter(
        MovimientoRecurrente.usuario_id == user_id,
        MovimientoRecurrente.activo == True,
    ).all()

    from sqlalchemy import extract
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
                cupo = float(c.cupo_total)
                disp = float(c.saldo)
                parts.append(f"- {c.nombre} (TC{nomina}): Cupo ${cupo:,.0f}, disponible ${disp:,.0f}")
            else:
                parts.append(f"- {c.nombre}{nomina}: ${float(c.saldo):,.0f}")

    if recurrentes:
        parts.append("Recurrentes:")
        for r in recurrentes:
            rec_name = r.nombre.lower().strip()
            pagado = any(
                rec_name in (t.descripcion or "").lower().strip()
                or (t.descripcion or "").lower().strip() in rec_name
                for t in txns_mes
            )
            parts.append(f"- {r.nombre}: ${float(r.monto):,.0f} día {r.dia_mes} {'✅' if pagado else '⏳'}")

    if categorias:
        parts.append("Categorías: " + ", ".join(f"{c.nombre}({c.tipo.value})" for c in categorias))

    ingresos = sum(float(t.monto) for t in txns_mes if t.tipo.value == "INGRESO")
    gastos = sum(float(t.monto) for t in txns_mes if t.tipo.value != "INGRESO")
    balance = ingresos - gastos
    parts.append(f"Mes actual: Ingresos ${ingresos:,.0f}, Gastos ${gastos:,.0f}, Balance ${balance:,.0f}")

    return "\n".join(parts) if parts else "Sin datos aún."


def find_account_by_name(cuentas, name: str):
    if not name:
        return None
    name_lower = name.lower()
    for c in cuentas:
        if name_lower in c.nombre.lower() or c.nombre.lower() in name_lower:
            return c
    return None


def find_or_create_category(db, user_id, nombre: str, tipo: str):
    """Find existing category or create a new one."""
    existing = db.query(Categoria).filter(
        Categoria.usuario_id == user_id,
        Categoria.nombre.ilike(f"%{nombre}%"),
    ).first()
    if existing:
        return existing
    cat = Categoria(usuario_id=user_id, nombre=nombre, tipo=tipo)
    db.add(cat)
    return cat


def build_chat_prompt(text: str, history: list = None) -> str:
    """Build prompt with conversation history for context."""
    parts = []
    if history:
        for msg in history[-5:]:  # Last 5 messages
            role = "Usuario" if msg.get("role") == "user" else "Asistente"
            parts.append(f"{role}: {msg.get('content', '')}")
    parts.append(f"Usuario: {text}")
    return "\n".join(parts)


@router.post("/parse")
async def parse_ia(
    data: IARequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    mode = data.mode if data.mode in PROMPTS else "general"
    user_context = build_user_context(db, current_user.id)
    context_block = CONTEXT_HEADER.format(user_context=user_context)
    system_prompt = PROMPTS[mode].format(context=context_block)

    prompt_text = build_chat_prompt(data.text, data.history)

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "llama3",
                    "prompt": prompt_text,
                    "system": system_prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.1, "num_predict": 1024}
                }
            )
            result = response.json()

            try:
                parsed = json.loads(result.get("response", "{}"))
            except json.JSONDecodeError:
                return {"reply": result.get("response", "No pude entender."), "saved": False}

            reply = parsed.get("reply", "Procesado.")

            cuentas = db.query(Cuenta).filter(
                Cuenta.usuario_id == current_user.id, Cuenta.activa == True
            ).all()

            # ── TRANSACCION ──
            if mode == "transaccion":
                items = parsed.get("items", [])
                # Backward compat single item
                if not items and parsed.get("monto"):
                    items = [parsed]
                saved = 0
                for item in items:
                    if not item.get("monto"):
                        continue
                    target = find_account_by_name(cuentas, item.get("cuenta_nombre", ""))
                    if not target and cuentas:
                        target = cuentas[0]
                    if target:
                        txn = Transaccion(
                            usuario_id=current_user.id,
                            cuenta_id=target.id,
                            tipo=item.get("tipo", "GASTO_VARIABLE"),
                            monto=abs(float(item["monto"])),
                            fecha=date.today(),
                            descripcion=item.get("descripcion", data.text),
                            fuente_ia=True,
                            texto_original=data.text,
                        )
                        db.add(txn)
                        saved += 1
                if saved:
                    db.commit()
                    return {"reply": reply, "saved": True, "saved_count": saved}
                return {"reply": "⚠️ No pude registrar la transacción.", "saved": False}

            # ── RECURRENTE ──
            elif mode == "recurrente":
                if not parsed.get("monto"):
                    return {"reply": reply, "saved": False}
                target = find_account_by_name(cuentas, parsed.get("cuenta_nombre", ""))
                if not target and cuentas:
                    target = cuentas[0]
                if target:
                    rec = MovimientoRecurrente(
                        usuario_id=current_user.id,
                        cuenta_id=target.id,
                        nombre=parsed.get("nombre", data.text),
                        tipo=parsed.get("tipo", "GASTO_FIJO"),
                        monto=abs(float(parsed["monto"])),
                        dia_mes=parsed.get("dia_mes", 1),
                    )
                    db.add(rec)
                    # Auto-create category
                    cat_name = parsed.get("categoria_sugerida")
                    if cat_name:
                        find_or_create_category(db, current_user.id, cat_name, parsed.get("tipo", "GASTO_FIJO"))
                    db.commit()
                    return {"reply": reply, "saved": True, "action": "recurrente"}
                return {"reply": "⚠️ No tienes cuentas activas.", "saved": False}

            # ── PRESTAMO ──
            elif mode == "prestamo":
                if not parsed.get("monto_total"):
                    return {"reply": reply, "saved": False}
                p = Prestamo(
                    usuario_id=current_user.id,
                    entidad=parsed.get("entidad", "Préstamo"),
                    tipo=parsed.get("tipo", "BANCO"),
                    monto_total=abs(float(parsed["monto_total"])),
                    saldo_pendiente=abs(float(parsed.get("saldo_pendiente", parsed["monto_total"]))),
                    cuota_mensual_esperada=abs(float(parsed.get("cuota_mensual", 0))),
                    dia_pago=parsed.get("dia_pago"),
                    estado="ACTIVO",
                )
                db.add(p)
                # Auto-create recurrente for monthly payment
                cuota = parsed.get("cuota_mensual", 0)
                target = find_account_by_name(cuentas, parsed.get("cuenta_nombre", ""))
                if not target and cuentas:
                    target = cuentas[0]
                if cuota and float(cuota) > 0 and target:
                    rec = MovimientoRecurrente(
                        usuario_id=current_user.id,
                        cuenta_id=target.id,
                        nombre=f"Cuota {parsed.get('entidad', 'Préstamo')}",
                        tipo="PRESTAMO_CUOTA",
                        monto=abs(float(cuota)),
                        dia_mes=parsed.get("dia_pago", 1),
                    )
                    db.add(rec)
                db.commit()
                return {"reply": reply, "saved": True, "action": "prestamo"}

            # ── META ──
            elif mode == "meta":
                if not parsed.get("monto_objetivo"):
                    return {"reply": reply, "saved": False}
                meta = MetaAhorro(
                    usuario_id=current_user.id,
                    nombre=parsed.get("nombre", "Meta de ahorro"),
                    monto_objetivo=abs(float(parsed["monto_objetivo"])),
                    monto_actual=0,
                    fecha_objetivo=parsed.get("fecha_objetivo"),
                )
                db.add(meta)
                db.commit()
                return {"reply": reply, "saved": True, "action": "meta"}

            # ── CATEGORIA ──
            elif mode == "categoria":
                if not parsed.get("nombre"):
                    return {"reply": reply, "saved": False}
                find_or_create_category(db, current_user.id, parsed["nombre"], parsed.get("tipo", "GASTO_VARIABLE"))
                db.commit()
                return {"reply": reply, "saved": True, "action": "categoria"}

            # ── GENERAL (consulta) ──
            else:
                return {"reply": reply, "saved": False}

    except httpx.ConnectError:
        return {"reply": "⚠️ IA no disponible. Intenta en unos segundos.", "saved": False}
    except Exception as e:
        return {"reply": f"Error: {str(e)}", "saved": False}
