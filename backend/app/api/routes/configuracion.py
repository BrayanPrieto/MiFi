from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.configuracion_ciclo import ConfiguracionCiclo
from app.schemas.configuracion_ciclo import (
    ConfiguracionCiclo as ConfigSchema,
    ConfiguracionCicloUpdate,
)

router = APIRouter()


def get_or_create_config(db: Session, user_id) -> ConfiguracionCiclo:
    cfg = db.query(ConfiguracionCiclo).filter(ConfiguracionCiclo.usuario_id == user_id).first()
    if not cfg:
        cfg = ConfiguracionCiclo(usuario_id=user_id)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


@router.get("/", response_model=ConfigSchema)
def get_config(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    return get_or_create_config(db, current_user.id)


@router.put("/", response_model=ConfigSchema)
def update_config(
    *,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
    data: ConfiguracionCicloUpdate,
) -> Any:
    cfg = get_or_create_config(db, current_user.id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cfg, field, value)
    db.commit()
    db.refresh(cfg)
    return cfg
