import uuid
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum, SmallInteger, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.core.encrypted_types import EncryptedString
import enum

class EstadoPrestamo(str, enum.Enum):
    ACTIVO = 'ACTIVO'
    PAGADO = 'PAGADO'
    EN_MORA = 'EN_MORA'

class TipoPrestamo(str, enum.Enum):
    BANCO = 'BANCO'
    TERCERO = 'TERCERO'

class Prestamo(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete="CASCADE"), nullable=False)
    entidad = Column(EncryptedString(), nullable=False)
    tipo = Column(Enum(TipoPrestamo), nullable=False, default=TipoPrestamo.BANCO)
    descripcion = Column(EncryptedString(), nullable=True)
    monto_total = Column(Numeric(15, 2), nullable=False)
    saldo_pendiente = Column(Numeric(15, 2), nullable=False)
    cuota_mensual_esperada = Column(Numeric(15, 2), nullable=False)
    tasa_interes_mensual = Column(Numeric(6, 4), nullable=True)
    dia_pago = Column(SmallInteger, nullable=True)
    estado = Column(Enum(EstadoPrestamo), nullable=False, default=EstadoPrestamo.ACTIVO)
    fecha_inicio = Column(Date, server_default=func.current_date(), nullable=False)
    fecha_fin_esperada = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
