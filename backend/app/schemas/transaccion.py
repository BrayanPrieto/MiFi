from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.models.categoria import TipoTransaccion

class TransaccionBase(BaseModel):
    cuenta_id: UUID
    categoria_id: Optional[UUID] = None
    prestamo_id: Optional[UUID] = None
    meta_ahorro_id: Optional[UUID] = None
    tipo: TipoTransaccion
    monto: Decimal
    fecha: date
    descripcion: Optional[str] = None
    es_requerido: bool = True
    esta_pagado: bool = False
    
    fuente_ia: bool = False
    texto_original: Optional[str] = None

class TransaccionCreate(TransaccionBase):
    pass

class TransaccionUpdate(BaseModel):
    cuenta_id: Optional[UUID] = None
    categoria_id: Optional[UUID] = None
    monto: Optional[Decimal] = None
    fecha: Optional[date] = None
    descripcion: Optional[str] = None
    esta_pagado: Optional[bool] = None

class Transaccion(TransaccionBase):
    id: UUID
    usuario_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
