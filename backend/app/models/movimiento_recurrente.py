import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.core.encrypted_types import EncryptedString


class MovimientoRecurrente(Base):
    __tablename__ = "movimientos_recurrentes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete="CASCADE"), nullable=False)
    cuenta_id = Column(UUID(as_uuid=True), ForeignKey('cuentas.id'), nullable=False)
    nombre = Column(EncryptedString(), nullable=False)
    tipo = Column(String(20), nullable=False)  # INGRESO, GASTO_FIJO, GASTO_VARIABLE, etc.
    monto = Column(Numeric(15, 2), nullable=False)
    dia_mes = Column(SmallInteger, nullable=False, default=1)
    activo = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
