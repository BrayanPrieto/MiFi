from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class ConfiguracionCicloBase(BaseModel):
    diezmo_porcentaje: float = 10.0
    caja_menor_monto: float = 250000
    dia_quincena_1: int = 15
    dia_quincena_2: int = 30
    dia_disparo: int = 28


class ConfiguracionCicloUpdate(BaseModel):
    diezmo_porcentaje: Optional[float] = None
    caja_menor_monto: Optional[float] = None
    dia_quincena_1: Optional[int] = None
    dia_quincena_2: Optional[int] = None
    dia_disparo: Optional[int] = None


class ConfiguracionCiclo(ConfiguracionCicloBase):
    id: UUID
    usuario_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
