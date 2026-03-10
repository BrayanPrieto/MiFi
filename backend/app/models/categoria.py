import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base
import enum

class TipoTransaccion(str, enum.Enum):
    INGRESO = 'INGRESO'
    GASTO_FIJO = 'GASTO_FIJO'
    GASTO_VARIABLE = 'GASTO_VARIABLE'
    PRESTAMO_CUOTA = 'PRESTAMO_CUOTA'
    AHORRO = 'AHORRO'

class Categoria(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete="CASCADE"), nullable=True)
    nombre = Column(String(100), nullable=False)
    tipo = Column(Enum(TipoTransaccion), nullable=False)
    color = Column(String(7), nullable=True)
    icono = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
