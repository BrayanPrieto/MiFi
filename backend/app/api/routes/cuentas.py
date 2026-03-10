from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.api import deps
from app.models.usuario import Usuario
from app.models.cuenta import Cuenta
from app.schemas.cuenta import CuentaCreate, CuentaUpdate, Cuenta as CuentaSchema

router = APIRouter()

@router.get("/", response_model=List[CuentaSchema])
def read_cuentas(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Usuario = Depends(deps.get_current_user)
) -> Any:
    """
    Obtener todas las cuentas del usuario actual.
    """
    cuentas = db.query(Cuenta).filter(Cuenta.usuario_id == current_user.id, Cuenta.activa == True).offset(skip).limit(limit).all()
    return cuentas

@router.post("/", response_model=CuentaSchema)
def create_cuenta(
    *,
    db: Session = Depends(deps.get_db),
    cuenta_in: CuentaCreate,
    current_user: Usuario = Depends(deps.get_current_user)
) -> Any:
    """
    Crear nueva cuenta.
    """
    # Enforce: solo 1 cuenta nómina por usuario
    if cuenta_in.es_nomina:
        db.query(Cuenta).filter(
            Cuenta.usuario_id == current_user.id,
            Cuenta.es_nomina == True,
        ).update({"es_nomina": False})

    cuenta = Cuenta(
        usuario_id=current_user.id,
        nombre=cuenta_in.nombre,
        tipo=cuenta_in.tipo,
        saldo=cuenta_in.saldo_inicial,
        cupo_total=cuenta_in.cupo_total,
        color=cuenta_in.color,
        icono=cuenta_in.icono,
        es_principal=cuenta_in.es_principal,
        es_nomina=cuenta_in.es_nomina,
    )
    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)
    return cuenta

@router.delete("/{cuenta_id}")
def deactivate_cuenta(
    cuenta_id: str,
    db: Session = Depends(deps.get_db),
    current_user: Usuario = Depends(deps.get_current_user)
) -> Any:
    """Desactivar una cuenta (soft delete)."""
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id, Cuenta.usuario_id == current_user.id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    cuenta.activa = False
    db.commit()
    return {"ok": True, "message": "Cuenta desactivada"}


@router.put("/{cuenta_id}", response_model=CuentaSchema)
def update_cuenta(
    cuenta_id: str,
    *,
    db: Session = Depends(deps.get_db),
    cuenta_in: CuentaUpdate,
    current_user: Usuario = Depends(deps.get_current_user)
) -> Any:
    """Editar una cuenta."""
    cuenta = db.query(Cuenta).filter(Cuenta.id == cuenta_id, Cuenta.usuario_id == current_user.id).first()
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    update_data = cuenta_in.model_dump(exclude_unset=True)

    # Enforce 1 sola nómina
    if update_data.get("es_nomina"):
        db.query(Cuenta).filter(
            Cuenta.usuario_id == current_user.id,
            Cuenta.es_nomina == True,
            Cuenta.id != cuenta_id,
        ).update({"es_nomina": False})

    for field, value in update_data.items():
        setattr(cuenta, field, value)
    db.commit()
    db.refresh(cuenta)
    return cuenta
