import uuid
from sqlalchemy import Column, Numeric, DateTime, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base

class Presupuesto(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete="CASCADE"), nullable=False)
    categoria_id = Column(UUID(as_uuid=True), ForeignKey('categorias.id', ondelete="CASCADE"), nullable=False)
    mes = Column(SmallInteger, nullable=False)
    anio = Column(SmallInteger, nullable=False)
    monto_limite = Column(Numeric(15, 2), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
