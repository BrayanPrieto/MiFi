from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.meta_ahorro import MetaAhorro
from app.schemas.meta_ahorro import MetaAhorroCreate, MetaAhorro as MetaAhorroSchema

router = APIRouter()

@router.get("/", response_model=List[MetaAhorroSchema])
def list_metas(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
) -> Any:
    return db.query(MetaAhorro).filter(MetaAhorro.usuario_id == current_user.id).all()

@router.post("/", response_model=MetaAhorroSchema)
def create_meta(
    *,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
    data: MetaAhorroCreate,
) -> Any:
    obj = MetaAhorro(
        usuario_id=current_user.id,
        nombre=data.nombre,
        monto_objetivo=data.monto_objetivo,
        monto_actual=data.monto_actual,
        fecha_objetivo=data.fecha_objetivo,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/{meta_id}")
def delete_meta(
    meta_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
) -> Any:
    obj = db.query(MetaAhorro).filter(MetaAhorro.id == meta_id, MetaAhorro.usuario_id == current_user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Meta no encontrada")
    db.delete(obj)
    db.commit()
    return {"ok": True}
