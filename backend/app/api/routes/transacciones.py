from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.api import deps
from app.models.usuario import Usuario
from app.models.transaccion import Transaccion
from app.schemas.transaccion import TransaccionCreate, Transaccion as TransaccionSchema

router = APIRouter()

@router.get("/", response_model=List[TransaccionSchema])
def read_transacciones(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    mes: int = None,
    anio: int = None,
    cuenta_id: UUID = None,
    current_user: Usuario = Depends(deps.get_current_user)
) -> Any:
    """
    Obtener transacciones del usuario, con filtros opcionales por mes, año o cuenta.
    """
    query = db.query(Transaccion).filter(Transaccion.usuario_id == current_user.id)
    
    if cuenta_id:
        query = query.filter(Transaccion.cuenta_id == cuenta_id)
        
    # Aqui se podrian añadir filtros de SQLAlchemy extract() para mes y año
        
    return query.order_by(Transaccion.fecha.desc()).offset(skip).limit(limit).all()

@router.post("/", response_model=TransaccionSchema)
def create_transaccion(
    *,
    db: Session = Depends(deps.get_db),
    transaccion_in: TransaccionCreate,
    current_user: Usuario = Depends(deps.get_current_user)
) -> Any:
    """
    Registrar una nueva transacción. (El trigger SQL se encarga de cambiar el saldo).
    """
    transaccion = Transaccion(
        usuario_id=current_user.id,
        cuenta_id=transaccion_in.cuenta_id,
        categoria_id=transaccion_in.categoria_id,
        prestamo_id=transaccion_in.prestamo_id,
        meta_ahorro_id=transaccion_in.meta_ahorro_id,
        tipo=transaccion_in.tipo,
        monto=transaccion_in.monto,
        fecha=transaccion_in.fecha,
        descripcion=transaccion_in.descripcion,
        es_requerido=transaccion_in.es_requerido,
        esta_pagado=transaccion_in.esta_pagado,
        fuente_ia=transaccion_in.fuente_ia,
        texto_original=transaccion_in.texto_original
    )
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)
    return transaccion

@router.delete("/{transaccion_id}")
def delete_transaccion(
    transaccion_id: str,
    db: Session = Depends(deps.get_db),
    current_user: Usuario = Depends(deps.get_current_user)
) -> Any:
    obj = db.query(Transaccion).filter(Transaccion.id == transaccion_id, Transaccion.usuario_id == current_user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    db.delete(obj)
    db.commit()
    return {"ok": True}
