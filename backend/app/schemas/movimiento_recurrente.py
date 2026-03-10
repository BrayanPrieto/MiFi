from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class RecurrenteBase(BaseModel):
    cuenta_id: UUID
    nombre: str
    tipo: str = "GASTO_FIJO"
    monto: float
    dia_mes: int = 1

class RecurrenteCreate(RecurrenteBase):
    pass

class RecurrenteUpdate(BaseModel):
    nombre: Optional[str] = None
    monto: Optional[float] = None
    dia_mes: Optional[int] = None
    cuenta_id: Optional[UUID] = None
    tipo: Optional[str] = None

class Recurrente(RecurrenteBase):
    id: UUID
    usuario_id: UUID
    activo: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
