"""
SQLAlchemy TypeDecorators para campos encriptados.
Se usan en los modelos para auto-encriptar/desencriptar valores.

Uso:
    from app.core.encrypted_types import EncryptedNumeric, EncryptedString

    class MyModel(Base):
        monto = Column(EncryptedNumeric(), nullable=False)
        descripcion = Column(EncryptedString(500), nullable=True)
"""
from sqlalchemy import TypeDecorator, String, Text
from app.core.encryption import encrypt_value, decrypt_value, encrypt_number, decrypt_number


class EncryptedString(TypeDecorator):
    """Encrypts string values transparently."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return encrypt_value(str(value))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return decrypt_value(value)
        return value


class EncryptedNumeric(TypeDecorator):
    """Encrypts numeric values as strings transparently.
    
    Note: SQL aggregate functions (SUM, AVG) won't work on encrypted columns.
    Aggregations must be done in Python after decryption.
    """
    impl = String(500)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return encrypt_number(float(value))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return decrypt_number(value)
        return value
