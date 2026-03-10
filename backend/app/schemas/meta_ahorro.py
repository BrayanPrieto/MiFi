from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID

class MetaAhorroBase(BaseModel):
    nombre: str
    monto_objetivo: float
    monto_actual: float = 0
    fecha_objetivo: Optional[date] = None

class MetaAhorroCreate(MetaAhorroBase):
    pass

class MetaAhorro(MetaAhorroBase):
    id: UUID
    usuario_id: UUID
    porcentaje_meta: Optional[float] = None
    completada: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
