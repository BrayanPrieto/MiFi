import uuid
from sqlalchemy import Column, Numeric, SmallInteger, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.core.encrypted_types import EncryptedString
import enum


class EstadoRecibo(str, enum.Enum):
    PENDIENTE = 'PENDIENTE'
    CONGELADO = 'CONGELADO'  # Reservado en bolsillo, no tocar
    PAGADO = 'PAGADO'


class Recibo(Base):
    """Instancia mensual de una obligación (checklist de ciclo, PRD 3.2).

    Se genera automáticamente cada mes a partir de recurrentes y cuotas de deuda.
    Reemplaza el matching difuso por nombre: aquí el estado es explícito y auditable.
    """
    __tablename__ = "recibos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete="CASCADE"), nullable=False)

    # Origen que generó este recibo (uno u otro, o ninguno si es manual)
    recurrente_id = Column(UUID(as_uuid=True), ForeignKey('movimientos_recurrentes.id', ondelete="SET NULL"), nullable=True)
    prestamo_id = Column(UUID(as_uuid=True), ForeignKey('prestamos.id', ondelete="SET NULL"), nullable=True)
    # Transacción que lo saldó (cuando se marca PAGADO)
    transaccion_id = Column(UUID(as_uuid=True), ForeignKey('transacciones.id', ondelete="SET NULL"), nullable=True)

    nombre = Column(EncryptedString(), nullable=False)  # snapshot del nombre de la obligación
    monto = Column(Numeric(15, 2), nullable=False)

    mes = Column(SmallInteger, nullable=False)
    anio = Column(SmallInteger, nullable=False)
    quincena = Column(SmallInteger, nullable=False, default=1)  # 1 (fase supervivencia) o 2 (fase deuda)
    dia_mes = Column(SmallInteger, nullable=True)

    estado = Column(Enum(EstadoRecibo), nullable=False, default=EstadoRecibo.PENDIENTE)
    fecha_pago = Column(DateTime(timezone=True), nullable=True)  # timestamp exacto al marcar PAGADO
    es_ahorro = Column(Boolean, nullable=False, default=False)  # recibo del diezmo 10% -> alimenta la meta

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
