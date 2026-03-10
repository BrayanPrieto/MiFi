from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import extract
from datetime import date

from app.api import deps
from app.models.movimiento_recurrente import MovimientoRecurrente
from app.models.transaccion import Transaccion
from app.schemas.movimiento_recurrente import RecurrenteCreate, RecurrenteUpdate, Recurrente as RecurrenteSchema

router = APIRouter()


@router.get("/", response_model=List[RecurrenteSchema])
def list_recurrentes(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    return db.query(MovimientoRecurrente).filter(
        MovimientoRecurrente.usuario_id == current_user.id,
        MovimientoRecurrente.activo == True,
    ).all()


@router.post("/", response_model=RecurrenteSchema)
def create_recurrente(
    *,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    data: RecurrenteCreate,
) -> Any:
    obj = MovimientoRecurrente(
        usuario_id=current_user.id,
        cuenta_id=data.cuenta_id,
        nombre=data.nombre,
        tipo=data.tipo,
        monto=data.monto,
        dia_mes=data.dia_mes,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{recurrente_id}", response_model=RecurrenteSchema)
def update_recurrente(
    recurrente_id: str,
    *,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    data: RecurrenteUpdate,
) -> Any:
    obj = db.query(MovimientoRecurrente).filter(
        MovimientoRecurrente.id == recurrente_id,
        MovimientoRecurrente.usuario_id == current_user.id,
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="No encontrado")
    if data.nombre is not None:
        obj.nombre = data.nombre
    if data.monto is not None:
        obj.monto = data.monto
    if data.dia_mes is not None:
        obj.dia_mes = data.dia_mes
    if data.cuenta_id is not None:
        obj.cuenta_id = data.cuenta_id
    if data.tipo is not None:
        obj.tipo = data.tipo
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{recurrente_id}")
def deactivate_recurrente(
    recurrente_id: str,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    obj = db.query(MovimientoRecurrente).filter(
        MovimientoRecurrente.id == recurrente_id,
        MovimientoRecurrente.usuario_id == current_user.id,
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="No encontrado")
    obj.activo = False
    db.commit()
    return {"ok": True, "message": "Recurrente desactivado"}


@router.post("/aplicar-mes")
def aplicar_mes(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    """
    Genera transacciones para el mes actual a partir de los movimientos recurrentes activos.
    Solo crea si no existe ya una transacción igual en el mismo mes.
    """
    hoy = date.today()
    mes = hoy.month
    anio = hoy.year

    recurrentes = db.query(MovimientoRecurrente).filter(
        MovimientoRecurrente.usuario_id == current_user.id,
        MovimientoRecurrente.activo == True,
    ).all()

    creados = 0
    ya_existentes = 0

    for rec in recurrentes:
        # Verificar si ya hay transacción de este recurrente este mes
        existente = db.query(Transaccion).filter(
            Transaccion.usuario_id == current_user.id,
            Transaccion.cuenta_id == rec.cuenta_id,
            Transaccion.monto == rec.monto,
            Transaccion.descripcion == rec.nombre,
            extract('month', Transaccion.fecha) == mes,
            extract('year', Transaccion.fecha) == anio,
        ).first()

        if existente:
            ya_existentes += 1
            continue

        # Crear la transacción
        dia = min(rec.dia_mes, 28)  # Evitar problemas con febrero
        fecha = date(anio, mes, dia)

        txn = Transaccion(
            usuario_id=current_user.id,
            cuenta_id=rec.cuenta_id,
            tipo=rec.tipo,
            monto=float(rec.monto),
            fecha=fecha,
            descripcion=rec.nombre,
            es_requerido=True,
            esta_pagado=True,
        )
        db.add(txn)
        creados += 1

    db.commit()
    return {
        "ok": True,
        "creados": creados,
        "ya_existentes": ya_existentes,
        "message": f"Se generaron {creados} transacciones. {ya_existentes} ya existían.",
    }
