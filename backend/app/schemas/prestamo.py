from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID

class PrestamoBase(BaseModel):
    entidad: str
    tipo: str = "BANCO"
    descripcion: Optional[str] = None
    monto_total: float
    saldo_pendiente: float
    cuota_mensual_esperada: float = 0
    tasa_interes_mensual: Optional[float] = None
    dia_pago: Optional[int] = None
    estado: str = "ACTIVO"
    fecha_inicio: Optional[date] = None
    fecha_fin_esperada: Optional[date] = None

class PrestamoCreate(PrestamoBase):
    cuenta_pago_id: Optional[UUID] = None  # Cuenta desde la que se paga

class PrestamoUpdate(BaseModel):
    es_objetivo: Optional[bool] = None
    prioridad: Optional[int] = None
    saldo_pendiente: Optional[float] = None
    cuota_mensual_esperada: Optional[float] = None
    estado: Optional[str] = None

class Prestamo(PrestamoBase):
    id: UUID
    usuario_id: UUID
    es_objetivo: bool = False
    prioridad: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
