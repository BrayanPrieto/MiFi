from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.recibo import EstadoRecibo


class ReciboBase(BaseModel):
    nombre: str
    monto: float
    mes: int
    anio: int
    quincena: int = 1
    dia_mes: Optional[int] = None


class ReciboCreate(ReciboBase):
    pass


class ReciboEstadoUpdate(BaseModel):
    estado: EstadoRecibo
    crear_transaccion: bool = False  # al marcar PAGADO, registrar la transacción real
    cuenta_id: Optional[UUID] = None


class Recibo(ReciboBase):
    id: UUID
    usuario_id: UUID
    estado: EstadoRecibo
    es_ahorro: bool = False
    fecha_pago: Optional[datetime] = None
    recurrente_id: Optional[UUID] = None
    prestamo_id: Optional[UUID] = None
    transaccion_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
