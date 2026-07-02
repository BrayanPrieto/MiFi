"""Ciclo Router — checklist de recibos y resumen del ciclo quincenal."""
from typing import Any, List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.models.recibo import Recibo, EstadoRecibo
from app.schemas.recibo import Recibo as ReciboSchema, ReciboEstadoUpdate
from . import service

router = APIRouter()


class GenerarRequest(BaseModel):
    mes: Optional[int] = None
    anio: Optional[int] = None


@router.get("/recibos", response_model=List[ReciboSchema])
def listar_recibos(
    mes: int = None,
    anio: int = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    hoy = date.today()
    mes = mes or hoy.month
    anio = anio or hoy.year
    return db.query(Recibo).filter(
        Recibo.usuario_id == current_user.id,
        Recibo.mes == mes, Recibo.anio == anio,
    ).order_by(Recibo.quincena, Recibo.dia_mes).all()


@router.post("/generar")
def generar(
    data: GenerarRequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    hoy = date.today()
    return service.generar_recibos(db, current_user.id, data.mes or hoy.month, data.anio or hoy.year)


@router.patch("/recibos/{recibo_id}", response_model=ReciboSchema)
def actualizar_estado(
    recibo_id: str,
    data: ReciboEstadoUpdate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    recibo = service.cambiar_estado(
        db, current_user.id, recibo_id, data.estado,
        crear_transaccion=data.crear_transaccion, cuenta_id=data.cuenta_id,
    )
    if not recibo:
        raise HTTPException(status_code=404, detail="Recibo no encontrado")
    return recibo


@router.get("/resumen")
def resumen(
    mes: int = None,
    anio: int = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    hoy = date.today()
    return service.resumen_ciclo(db, current_user.id, mes or hoy.month, anio or hoy.year)
