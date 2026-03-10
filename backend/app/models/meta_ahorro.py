import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.core.encrypted_types import EncryptedString

class MetaAhorro(Base):
    __tablename__ = "metas_ahorro"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete="CASCADE"), nullable=False)
    nombre = Column(EncryptedString(), nullable=False)
    monto_objetivo = Column(Numeric(15, 2), nullable=False)
    monto_actual = Column(Numeric(15, 2), nullable=False, default=0.00)
    porcentaje_meta = Column(Numeric(5, 2), nullable=True)
    fecha_objetivo = Column(Date, nullable=True)
    completada = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
