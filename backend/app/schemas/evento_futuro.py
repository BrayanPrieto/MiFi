from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class EventoFuturoBase(BaseModel):
    nombre: str
    monto: float
    mes: int
    anio: int
    es_egreso: bool = True


class EventoFuturoCreate(EventoFuturoBase):
    pass


class EventoFuturo(EventoFuturoBase):
    id: UUID
    usuario_id: UUID
    aplicado: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
