from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.evento_futuro import EventoFuturo
from app.schemas.evento_futuro import EventoFuturoCreate, EventoFuturo as EventoSchema

router = APIRouter()


@router.get("/", response_model=List[EventoSchema])
def list_eventos(
    anio: int = None,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    q = db.query(EventoFuturo).filter(EventoFuturo.usuario_id == current_user.id)
    if anio:
        q = q.filter(EventoFuturo.anio == anio)
    return q.order_by(EventoFuturo.anio, EventoFuturo.mes).all()


@router.post("/", response_model=EventoSchema)
def create_evento(
    *,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    data: EventoFuturoCreate,
) -> Any:
    obj = EventoFuturo(usuario_id=current_user.id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{evento_id}")
def delete_evento(
    evento_id: str,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    obj = db.query(EventoFuturo).filter(
        EventoFuturo.id == evento_id, EventoFuturo.usuario_id == current_user.id
    ).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    db.delete(obj)
    db.commit()
    return {"ok": True}
