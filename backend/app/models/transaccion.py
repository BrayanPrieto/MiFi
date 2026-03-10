import uuid
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, Enum, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base
from app.models.categoria import TipoTransaccion
from app.core.encrypted_types import EncryptedString

class Transaccion(Base):
    __tablename__ = "transacciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete="CASCADE"), nullable=False)
    cuenta_id = Column(UUID(as_uuid=True), ForeignKey('cuentas.id'), nullable=False)
    categoria_id = Column(UUID(as_uuid=True), ForeignKey('categorias.id'), nullable=True)
    prestamo_id = Column(UUID(as_uuid=True), ForeignKey('prestamos.id'), nullable=True)
    meta_ahorro_id = Column(UUID(as_uuid=True), ForeignKey('metas_ahorro.id'), nullable=True)
    
    tipo = Column(Enum(TipoTransaccion), nullable=False)
    monto = Column(Numeric(15, 2), nullable=False)
    fecha = Column(Date, server_default=func.current_date(), nullable=False)
    descripcion = Column(EncryptedString(), nullable=True)
    
    es_requerido = Column(Boolean, nullable=False, default=True)
    esta_pagado = Column(Boolean, nullable=False, default=False)
    
    fuente_ia = Column(Boolean, nullable=False, default=False)
    texto_original = Column(EncryptedString(), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
