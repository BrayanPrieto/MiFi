import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.core.encrypted_types import EncryptedString
import enum

class TipoCuenta(str, enum.Enum):
    EFECTIVO = 'EFECTIVO'
    CUENTA_AHORROS = 'CUENTA_AHORROS'
    CUENTA_CORRIENTE = 'CUENTA_CORRIENTE'
    TARJETA_CREDITO = 'TARJETA_CREDITO'
    BILLETERA_DIGITAL = 'BILLETERA_DIGITAL'
    OTRO = 'OTRO'

class Cuenta(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete="CASCADE"), nullable=False)
    nombre = Column(EncryptedString(), nullable=False)
    tipo = Column(Enum(TipoCuenta), nullable=False, default=TipoCuenta.CUENTA_AHORROS)
    saldo = Column(Numeric(15, 2), nullable=False, default=0.00)
    cupo_total = Column(Numeric(15, 2), nullable=True)  # Solo para tarjetas de crédito
    color = Column(String(7), nullable=True)
    icono = Column(String(50), nullable=True)
    es_principal = Column(Boolean, nullable=False, default=False)
    es_nomina = Column(Boolean, nullable=False, default=False)
    activa = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
