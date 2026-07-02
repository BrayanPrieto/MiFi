import uuid
from sqlalchemy import Column, Numeric, SmallInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.core.encrypted_types import EncryptedString


class EventoFuturo(Base):
    """Imprevisto predecible / buffer (PRD 3.3).

    Ej. "Derechos de grado $1.000.000 en Julio". El motor de proyección lo
    deduce del flujo libre del mes correspondiente.
    """
    __tablename__ = "eventos_futuros"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete="CASCADE"), nullable=False)

    nombre = Column(EncryptedString(), nullable=False)
    monto = Column(Numeric(15, 2), nullable=False)
    mes = Column(SmallInteger, nullable=False)
    anio = Column(SmallInteger, nullable=False)
    # True = gasto que resta flujo libre; False = ingreso extra que lo suma
    es_egreso = Column(Boolean, nullable=False, default=True)
    aplicado = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
