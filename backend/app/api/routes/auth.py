from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.usuario import Usuario
from app.schemas.token import Token
from app.schemas.usuario import UsuarioCreate, Usuario as UsuarioSchema

router = APIRouter()

@router.post("/login/access-token", response_model=Token)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, requiere username (email) y password.
    """
    user = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Email o contraseña incorrectos")
    elif not user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/test-token", response_model=UsuarioSchema)
def test_token(current_user: Usuario = Depends(deps.get_current_user)) -> Any:
    """
    Endpoint para probar que el token JWT es válido.
    """
    return current_user
