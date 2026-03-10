from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import date
from decimal import Decimal

from app.api import deps
from app.models.transaccion import Transaccion
from app.models.cuenta import Cuenta
from app.models.movimiento_recurrente import MovimientoRecurrente

router = APIRouter()


@router.get("/resumen-mensual")
def resumen_mensual(
    mes: int = None,
    anio: int = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    """Retorna el resumen financiero del mes."""
    hoy = date.today()
    mes = mes or hoy.month
    anio = anio or hoy.year

    # Transacciones del mes
    txns = db.query(Transaccion).filter(
        Transaccion.usuario_id == current_user.id,
        extract('month', Transaccion.fecha) == mes,
        extract('year', Transaccion.fecha) == anio,
    ).all()

    # Cuentas activas
    cuentas = db.query(Cuenta).filter(
        Cuenta.usuario_id == current_user.id,
        Cuenta.activa == True,
    ).all()

    # Recurrentes activos
    recurrentes = db.query(MovimientoRecurrente).filter(
        MovimientoRecurrente.usuario_id == current_user.id,
        MovimientoRecurrente.activo == True,
    ).all()

    # Calcular totales
    ingresos = sum(float(t.monto) for t in txns if t.tipo.value == "INGRESO")
    gastos_fijos = sum(float(t.monto) for t in txns if t.tipo.value == "GASTO_FIJO")
    gastos_variables = sum(float(t.monto) for t in txns if t.tipo.value == "GASTO_VARIABLE")
    cuotas_prestamo = sum(float(t.monto) for t in txns if t.tipo.value == "PRESTAMO_CUOTA")
    ahorros = sum(float(t.monto) for t in txns if t.tipo.value == "AHORRO")
    total_gastos = gastos_fijos + gastos_variables + cuotas_prestamo

    # Tarjetas de crédito con cupo
    tarjetas = []
    for c in cuentas:
        if c.tipo.value == "TARJETA_CREDITO" and c.cupo_total:
            cupo_total = float(c.cupo_total)
            cupo_disponible = float(c.saldo)
            consumido = cupo_total - cupo_disponible
            tarjetas.append({
                "id": str(c.id),
                "nombre": c.nombre,
                "cupo_total": cupo_total,
                "cupo_disponible": cupo_disponible,
                "consumido": consumido,
                "porcentaje_usado": round((consumido / cupo_total) * 100, 1) if cupo_total > 0 else 0,
            })

    # Recurrentes: cuáles ya se pagaron este mes (matching estricto por nombre)
    recurrentes_status = []
    for rec in recurrentes:
        rec_name = (rec.nombre or "").lower().strip()
        rec_monto = float(rec.monto)
        # Match ONLY by name similarity (not just by amount)
        pagado = False
        for t in txns:
            t_desc = (t.descripcion or "").lower().strip()
            # Name must match (contains in either direction)
            name_match = (rec_name and t_desc and
                         (rec_name in t_desc or t_desc in rec_name))
            if name_match:
                pagado = True
                break
        recurrentes_status.append({
            "id": str(rec.id),
            "nombre": rec.nombre,
            "tipo": rec.tipo,
            "monto": rec_monto,
            "dia_mes": rec.dia_mes,
            "pagado": pagado,
        })

    # Cuentas resumen
    cuentas_resumen = []
    for c in cuentas:
        cuentas_resumen.append({
            "id": str(c.id),
            "nombre": c.nombre,
            "tipo": c.tipo.value,
            "saldo": float(c.saldo),
            "cupo_total": float(c.cupo_total) if c.cupo_total else None,
        })
    # Últimas transacciones del mes (para bloque Movimientos)
    ultimas_txns = sorted(txns, key=lambda t: t.fecha, reverse=True)[:15]
    ultimas = []
    for t in ultimas_txns:
        ultimas.append({
            "id": str(t.id),
            "tipo": t.tipo.value,
            "monto": float(t.monto),
            "descripcion": t.descripcion,
            "fecha": str(t.fecha),
        })

    return {
        "mes": mes,
        "anio": anio,
        "ingresos": ingresos,
        "gastos_fijos": gastos_fijos,
        "gastos_variables": gastos_variables,
        "cuotas_prestamo": cuotas_prestamo,
        "ahorros": ahorros,
        "total_gastos": total_gastos,
        "balance": ingresos - total_gastos,
        "tarjetas": tarjetas,
        "recurrentes": recurrentes_status,
        "cuentas": cuentas_resumen,
        "ultimas_transacciones": ultimas,
    }
