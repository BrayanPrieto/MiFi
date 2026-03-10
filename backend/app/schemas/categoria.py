from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.models.categoria import TipoTransaccion

class CategoriaBase(BaseModel):
    nombre: str
    tipo: TipoTransaccion
    color: Optional[str] = None
    icono: Optional[str] = None

class CategoriaCreate(CategoriaBase):
    pass

class Categoria(CategoriaBase):
    id: UUID
    usuario_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
