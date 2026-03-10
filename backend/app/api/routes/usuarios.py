from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import get_password_hash
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, Usuario as UsuarioSchema

router = APIRouter()

@router.post("/", response_model=UsuarioSchema)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UsuarioCreate,
) -> Any:
    """
    Crear nuevo usuario.
    """
    user = db.query(Usuario).filter(Usuario.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un usuario con este email"
        )
    
    user = Usuario(
        nombre=user_in.nombre,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        avatar_url=user_in.avatar_url,
        moneda=user_in.moneda,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.get("/me", response_model=UsuarioSchema)
def read_user_me(
    current_user: Usuario = Depends(deps.get_current_user)
) -> Any:
    """
    Obtener datos del usuario actual.
    """
    return current_user
