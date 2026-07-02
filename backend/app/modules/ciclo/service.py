"""Motor de ciclo quincenal (Proyecto Espartano).

Responsabilidades:
  - Generar los recibos del mes (checklist) desde recurrentes canónicos
  - Cambiar estado de un recibo (PENDIENTE/CONGELADO/PAGADO) + registrar la transacción
  - Calcular el resumen del ciclo: diezmo, caja menor, remanentes por quincena y
    flujo libre para el "día de disparo" (bola de nieve), ajustado por eventos futuros
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.recibo import Recibo, EstadoRecibo
from app.models.movimiento_recurrente import MovimientoRecurrente
from app.models.prestamo import Prestamo, EstadoPrestamo
from app.models.transaccion import Transaccion
from app.models.cuenta import Cuenta
from app.models.evento_futuro import EventoFuturo
from app.models.configuracion_ciclo import ConfiguracionCiclo


# ponytail: heurística simple — obligación del día 1-15 pertenece a Q1, resto a Q2.
def _quincena(dia_mes: Optional[int]) -> int:
    return 1 if (dia_mes or 1) <= 15 else 2


def get_config(db: Session, user_id) -> ConfiguracionCiclo:
    cfg = db.query(ConfiguracionCiclo).filter(ConfiguracionCiclo.usuario_id == user_id).first()
    if not cfg:
        cfg = ConfiguracionCiclo(usuario_id=user_id)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


def _default_account(db: Session, user_id):
    cuentas = db.query(Cuenta).filter(Cuenta.usuario_id == user_id, Cuenta.activa == True).all()
    for c in cuentas:
        if c.es_nomina:
            return c
    for c in cuentas:
        if c.tipo.value != "TARJETA_CREDITO":
            return c
    return cuentas[0] if cuentas else None


def generar_recibos(db: Session, user_id, mes: int, anio: int) -> dict:
    """Genera recibos PENDIENTE del mes desde recurrentes (excepto ingresos).

    Idempotente: no duplica un recurrente que ya tiene recibo ese mes.
    """
    existentes = db.query(Recibo).filter(
        Recibo.usuario_id == user_id, Recibo.mes == mes, Recibo.anio == anio
    ).all()
    ya_generados = {r.recurrente_id for r in existentes if r.recurrente_id}

    recurrentes = db.query(MovimientoRecurrente).filter(
        MovimientoRecurrente.usuario_id == user_id,
        MovimientoRecurrente.activo == True,
    ).all()

    creados = 0
    ingreso_q = {1: 0.0, 2: 0.0}
    for rec in recurrentes:
        if "INGRESO" in (rec.tipo or "").upper():
            ingreso_q[_quincena(rec.dia_mes)] += float(rec.monto)
            continue  # los ingresos no son obligaciones a marcar
        if rec.id in ya_generados:
            continue
        db.add(Recibo(
            usuario_id=user_id,
            recurrente_id=rec.id,
            nombre=rec.nombre,
            monto=rec.monto,
            mes=mes,
            anio=anio,
            quincena=_quincena(rec.dia_mes),
            dia_mes=rec.dia_mes,
            estado=EstadoRecibo.PENDIENTE,
        ))
        creados += 1

    # Recibo del diezmo 10% por quincena con ingreso (págate a ti mismo primero)
    cfg = get_config(db, user_id)
    pct = float(cfg.diezmo_porcentaje) / 100.0
    ahorro_q_existente = {r.quincena for r in existentes if r.es_ahorro}
    for q in (1, 2):
        if ingreso_q[q] > 0 and q not in ahorro_q_existente:
            db.add(Recibo(
                usuario_id=user_id,
                nombre="Ahorro 10%",
                monto=ingreso_q[q] * pct,
                mes=mes,
                anio=anio,
                quincena=q,
                dia_mes=cfg.dia_ahorro,
                estado=EstadoRecibo.PENDIENTE,
                es_ahorro=True,
            ))
            creados += 1

    db.commit()
    return {"creados": creados, "total_mes": len(existentes) + creados}


def cambiar_estado(
    db: Session, user_id, recibo_id: UUID, estado: EstadoRecibo,
    crear_transaccion: bool = False, cuenta_id: Optional[UUID] = None,
) -> Recibo:
    recibo = db.query(Recibo).filter(
        Recibo.id == recibo_id, Recibo.usuario_id == user_id
    ).first()
    if not recibo:
        return None

    prev = recibo.estado
    recibo.estado = estado
    if estado == EstadoRecibo.PAGADO:
        recibo.fecha_pago = datetime.now()
        if crear_transaccion and not recibo.transaccion_id:
            txn = _registrar_transaccion(db, user_id, recibo, cuenta_id)
            if txn:
                db.flush()
                recibo.transaccion_id = txn.id
    else:
        recibo.fecha_pago = None

    # Efectos conectados: solo en la transición de/hacia PAGADO
    monto = float(recibo.monto)
    paso_a_pagado = estado == EstadoRecibo.PAGADO and prev != EstadoRecibo.PAGADO
    salio_de_pagado = prev == EstadoRecibo.PAGADO and estado != EstadoRecibo.PAGADO
    signo = 1 if paso_a_pagado else (-1 if salio_de_pagado else 0)

    if signo:
        if recibo.es_ahorro:
            # Diezmo 10%: alimenta la meta "Ahorro 10%" y la cuenta de Ahorros
            _ajustar_meta_ahorro(db, user_id, signo * monto)
            _ajustar_saldo_ahorro(db, user_id, signo * monto)
        else:
            # ¿Este recibo paga la cuota de una tarjeta? Baja/sube su deuda
            card = _card_destino(db, recibo)
            if card:
                card.saldo = max(float(card.saldo) - signo * monto, 0)

    db.commit()
    db.refresh(recibo)
    return recibo


def _ensure_cuenta_ahorro(db: Session, user_id):
    """Busca/crea la cuenta CUENTA_AHORROS 'Ahorro' (nombre encriptado -> comparar en Python)."""
    cuentas = db.query(Cuenta).filter(
        Cuenta.usuario_id == user_id, Cuenta.activa == True,
    ).all()
    c = next((x for x in cuentas if (x.nombre or "").strip().lower() == "ahorro"), None)
    if not c:
        c = Cuenta(usuario_id=user_id, nombre="Ahorro", tipo="CUENTA_AHORROS", saldo=0)
        db.add(c)
        db.flush()
    return c


def _ajustar_saldo_ahorro(db: Session, user_id, delta: float):
    c = _ensure_cuenta_ahorro(db, user_id)
    c.saldo = max(float(c.saldo or 0) + delta, 0)


def _card_destino(db: Session, recibo: Recibo):
    """Si el recibo viene de un recurrente vinculado a una tarjeta, devuelve esa tarjeta."""
    if not recibo.recurrente_id:
        return None
    rec = db.query(MovimientoRecurrente).filter(MovimientoRecurrente.id == recibo.recurrente_id).first()
    if not rec or not rec.cuenta_destino_id:
        return None
    card = db.query(Cuenta).filter(Cuenta.id == rec.cuenta_destino_id).first()
    if card and card.tipo.value == "TARJETA_CREDITO":
        return card
    return None


def _ajustar_meta_ahorro(db: Session, user_id, delta: float):
    """Crea/actualiza la meta 'Ahorro 10%' sumando (o restando) el diezmo realizado.

    nombre está encriptado (Fernet no determinista): se compara desencriptado en Python.
    """
    from app.models.meta_ahorro import MetaAhorro
    metas = db.query(MetaAhorro).filter(MetaAhorro.usuario_id == user_id).all()
    meta = next((m for m in metas if (m.nombre or "").strip().lower() == "ahorro 10%"), None)
    if not meta:
        meta = MetaAhorro(
            usuario_id=user_id, nombre="Ahorro 10%",
            monto_objetivo=0, monto_actual=0,
        )
        db.add(meta)
    meta.monto_actual = max(float(meta.monto_actual or 0) + delta, 0)


def _registrar_transaccion(db: Session, user_id, recibo: Recibo, cuenta_id: Optional[UUID]):
    # Cuenta: la del recurrente origen, o la indicada, o la de nómina/por defecto
    cuenta = None
    if recibo.recurrente_id:
        rec = db.query(MovimientoRecurrente).filter(MovimientoRecurrente.id == recibo.recurrente_id).first()
        if rec:
            cuenta = db.query(Cuenta).filter(Cuenta.id == rec.cuenta_id).first()
    if not cuenta and cuenta_id:
        cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id, Cuenta.usuario_id == user_id).first()
    if not cuenta:
        cuenta = _default_account(db, user_id)
    if not cuenta:
        return None

    tipo = "GASTO_FIJO"
    if recibo.recurrente_id:
        rec = db.query(MovimientoRecurrente).filter(MovimientoRecurrente.id == recibo.recurrente_id).first()
        if rec and (rec.tipo or "").upper() in {"INGRESO", "GASTO_FIJO", "GASTO_VARIABLE", "PRESTAMO_CUOTA", "AHORRO"}:
            tipo = rec.tipo.upper()

    txn = Transaccion(
        usuario_id=user_id,
        cuenta_id=cuenta.id,
        tipo=tipo,
        monto=recibo.monto,
        fecha=date.today(),
        descripcion=recibo.nombre,
        esta_pagado=True,
    )
    db.add(txn)
    return txn


def _norm_prestamo(p) -> dict:
    return {
        "id": str(p.id), "clase": "prestamo", "entidad": p.entidad,
        "saldo": float(p.saldo_pendiente),
        "total": float(p.monto_total) or float(p.saldo_pendiente),
        "cuota": float(p.cuota_mensual_esperada or 0),
        "tasa": float(p.tasa_interes_mensual or 0),
    }


def _norm_tarjeta(c) -> dict:
    saldo = float(c.saldo)  # deuda consumida
    return {
        "id": str(c.id), "clase": "tarjeta", "entidad": c.nombre,
        "saldo": saldo,
        "total": float(c.cupo_total) or saldo,  # cupo como referencia de progreso
        "cuota": float(c.cuota_mensual or 0),
        "tasa": 0.0,
    }


def _find_deuda_objetivo(db: Session, user_id):
    """Deuda objetivo unificada: préstamo o tarjeta marcada; si ninguna, la de menor saldo."""
    p = db.query(Prestamo).filter(
        Prestamo.usuario_id == user_id, Prestamo.estado == EstadoPrestamo.ACTIVO,
        Prestamo.es_objetivo == True,
    ).first()
    if p:
        return _norm_prestamo(p)
    c = db.query(Cuenta).filter(
        Cuenta.usuario_id == user_id, Cuenta.activa == True,
        Cuenta.tipo == "TARJETA_CREDITO", Cuenta.es_objetivo == True,
    ).first()
    if c:
        return _norm_tarjeta(c)

    # Fallback: menor saldo entre préstamos activos + tarjetas con deuda
    cands = [
        _norm_prestamo(pp) for pp in db.query(Prestamo).filter(
            Prestamo.usuario_id == user_id, Prestamo.estado == EstadoPrestamo.ACTIVO,
        ).all()
    ]
    cards = db.query(Cuenta).filter(
        Cuenta.usuario_id == user_id, Cuenta.activa == True,
        Cuenta.tipo == "TARJETA_CREDITO",
    ).all()
    cands += [_norm_tarjeta(c) for c in cards if float(c.saldo) > 0]
    return min(cands, key=lambda x: x["saldo"]) if cands else None


def resumen_ciclo(db: Session, user_id, mes: int, anio: int) -> dict:
    """Proyección del ciclo: diezmo, caja menor, remanentes y flujo libre (día de disparo)."""
    cfg = get_config(db, user_id)
    pct = float(cfg.diezmo_porcentaje) / 100.0
    caja = float(cfg.caja_menor_monto)

    # Ingresos proyectados por quincena (recurrentes tipo INGRESO)
    recurrentes = db.query(MovimientoRecurrente).filter(
        MovimientoRecurrente.usuario_id == user_id,
        MovimientoRecurrente.activo == True,
    ).all()
    ingreso = {1: 0.0, 2: 0.0}
    for r in recurrentes:
        if "INGRESO" in (r.tipo or "").upper():
            ingreso[_quincena(r.dia_mes)] += float(r.monto)

    # Obligaciones (recibos) por quincena — el ahorro NO es obligación (ya se resta como diezmo)
    recibos = db.query(Recibo).filter(
        Recibo.usuario_id == user_id, Recibo.mes == mes, Recibo.anio == anio
    ).all()
    oblig = {1: 0.0, 2: 0.0}
    oblig_pagada = {1: 0.0, 2: 0.0}
    pendientes = {1: 0, 2: 0}
    for r in recibos:
        if r.es_ahorro:
            continue
        q = r.quincena if r.quincena in (1, 2) else 1
        oblig[q] += float(r.monto)
        if r.estado == EstadoRecibo.PAGADO:
            oblig_pagada[q] += float(r.monto)
        elif r.estado == EstadoRecibo.PENDIENTE:
            pendientes[q] += 1

    quincenas = {}
    for q in (1, 2):
        diezmo = ingreso[q] * pct
        caja_q = caja if ingreso[q] > 0 else 0.0
        remanente = ingreso[q] - diezmo - caja_q - oblig[q]
        quincenas[q] = {
            "ingreso": ingreso[q],
            "diezmo": diezmo,
            "caja_menor": caja_q,
            "obligaciones": oblig[q],
            "obligaciones_pagadas": oblig_pagada[q],
            "pendientes": pendientes[q],
            "remanente": remanente,
        }

    # Eventos futuros del mes (buffer)
    eventos = db.query(EventoFuturo).filter(
        EventoFuturo.usuario_id == user_id,
        EventoFuturo.mes == mes, EventoFuturo.anio == anio,
    ).all()
    egresos_evento = sum(float(e.monto) for e in eventos if e.es_egreso)
    ingresos_evento = sum(float(e.monto) for e in eventos if not e.es_egreso)

    flujo_libre = quincenas[1]["remanente"] + quincenas[2]["remanente"]
    flujo_libre_ajustado = flujo_libre - egresos_evento + ingresos_evento

    # Semáforo de la quincena actual: ¿el saldo disponible cubre lo pendiente?
    saldo_disponible = sum(
        float(c.saldo) for c in db.query(Cuenta).filter(
            Cuenta.usuario_id == user_id, Cuenta.activa == True
        ).all() if c.tipo.value != "TARJETA_CREDITO"
    )
    quincena_actual = 1 if date.today().day <= 15 else 2
    pendiente_actual = oblig[quincena_actual] - oblig_pagada[quincena_actual]
    if pendiente_actual <= 0:
        semaforo = "verde"
    elif saldo_disponible >= pendiente_actual * 1.15:
        semaforo = "verde"
    elif saldo_disponible >= pendiente_actual:
        semaforo = "amarillo"
    else:
        semaforo = "rojo"

    # Deuda objetivo (bola de nieve) — unificada: préstamos + tarjetas de crédito
    obj = _find_deuda_objetivo(db, user_id)

    deuda_objetivo = None
    if obj:
        saldo = obj["saldo"]
        total = obj["total"] or saldo
        pagado = max(total - saldo, 0)
        cuota = obj["cuota"]

        # Bola de nieve: cada mes la deuda recibe su cuota + todo el flujo libre (ataque del día de disparo).
        tasa = obj["tasa"] / 100.0
        pago_mensual = cuota + max(flujo_libre_ajustado, 0)
        meses_estimados = None
        fecha_estimada = None
        if pago_mensual > 0:
            s = saldo
            meses = 0
            while s > 0 and meses < 600:
                s = s * (1 + tasa) - pago_mensual
                meses += 1
            if meses < 600:
                meses_estimados = meses
                m = date.today().month - 1 + meses
                fecha_estimada = date(date.today().year + m // 12, m % 12 + 1, 1).isoformat()

        deuda_objetivo = {
            "id": obj["id"],
            "clase": obj["clase"],  # "prestamo" | "tarjeta"
            "entidad": obj["entidad"],
            "saldo_pendiente": saldo,
            "monto_total": total,
            "pagado": pagado,
            "progreso_pct": round((pagado / total) * 100, 1) if total > 0 else 0,
            "cuota_mensual": cuota,
            "pago_mensual_proyectado": pago_mensual,
            "meses_estimados": meses_estimados,
            "fecha_estimada": fecha_estimada,
        }

    return {
        "mes": mes,
        "anio": anio,
        "diezmo_total": quincenas[1]["diezmo"] + quincenas[2]["diezmo"],
        "caja_menor_total": quincenas[1]["caja_menor"] + quincenas[2]["caja_menor"],
        "quincena_1": quincenas[1],
        "quincena_2": quincenas[2],
        "eventos_egreso": egresos_evento,
        "eventos_ingreso": ingresos_evento,
        "flujo_libre": flujo_libre,
        "flujo_libre_ajustado": flujo_libre_ajustado,
        "saldo_disponible": saldo_disponible,
        "quincena_actual": quincena_actual,
        "pendiente_actual": pendiente_actual,
        "semaforo": semaforo,
        "dia_disparo": cfg.dia_disparo,
        "deuda_objetivo": deuda_objetivo,
    }
