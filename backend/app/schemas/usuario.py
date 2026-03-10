from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime

class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr
    avatar_url: Optional[str] = None
    moneda: str = "COP"

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    avatar_url: Optional[str] = None
    moneda: Optional[str] = None
    activo: Optional[bool] = None

class Usuario(UsuarioBase):
    id: UUID
    activo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
