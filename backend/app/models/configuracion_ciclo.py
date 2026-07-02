import uuid
from sqlalchemy import Column, Numeric, SmallInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base


class ConfiguracionCiclo(Base):
    """Reglas del ciclo quincenal por usuario (Proyecto Espartano).

    Una fila por usuario. Define diezmo, caja menor y días clave del ciclo.
    """
    __tablename__ = "configuraciones_ciclo"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete="CASCADE"), nullable=False, unique=True)

    # "Págate a ti mismo primero": % del ingreso neto que se separa como ahorro intocable
    diezmo_porcentaje = Column(Numeric(5, 2), nullable=False, default=10.00)
    # "Caja menor / chicles": monto fijo discrecional por quincena
    caja_menor_monto = Column(Numeric(15, 2), nullable=False, default=250000)

    # Días clave del ciclo mensual
    dia_quincena_1 = Column(SmallInteger, nullable=False, default=15)
    dia_quincena_2 = Column(SmallInteger, nullable=False, default=30)
    dia_disparo = Column(SmallInteger, nullable=False, default=28)  # "Día del ataque" a la deuda
    dia_ahorro = Column(SmallInteger, nullable=False, default=17)  # Día en que se aparta el 10%

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
