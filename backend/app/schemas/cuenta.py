from typing import Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.models.cuenta import TipoCuenta

class CuentaBase(BaseModel):
    nombre: str
    tipo: TipoCuenta = TipoCuenta.CUENTA_AHORROS
    color: Optional[str] = None
    icono: Optional[str] = None
    es_principal: bool = False

class CuentaCreate(CuentaBase):
    saldo_inicial: Decimal = Decimal('0.00')
    cupo_total: Optional[Decimal] = None
    cuota_mensual: Optional[Decimal] = None
    es_nomina: bool = False

class CuentaUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[TipoCuenta] = None
    saldo: Optional[Decimal] = None
    cupo_total: Optional[Decimal] = None
    cuota_mensual: Optional[Decimal] = None
    es_objetivo: Optional[bool] = None
    prioridad: Optional[int] = None
    color: Optional[str] = None
    icono: Optional[str] = None
    es_principal: Optional[bool] = None
    es_nomina: Optional[bool] = None
    activa: Optional[bool] = None

class Cuenta(CuentaBase):
    id: UUID
    usuario_id: UUID
    saldo: Decimal
    cupo_total: Optional[Decimal] = None
    cuota_mensual: Optional[Decimal] = None
    es_objetivo: bool = False
    prioridad: Optional[int] = None
    es_nomina: bool = False
    activa: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
