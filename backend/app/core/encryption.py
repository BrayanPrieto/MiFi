"""
Módulo de encriptación para campos sensibles en BD.
Usa Fernet (AES-128-CBC) con una clave de aplicación.

La clave se genera una vez y se almacena en variable de entorno ENCRYPTION_KEY.
Para generar: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import os
import base64
from cryptography.fernet import Fernet

# Clave de encriptación desde variable de entorno
_KEY = os.environ.get("ENCRYPTION_KEY")

def _get_fernet() -> Fernet:
    """Get Fernet instance. Generates key if not set (dev mode)."""
    global _KEY
    if not _KEY:
        # Dev fallback: generate and warn
        _KEY = Fernet.generate_key().decode()
        print(f"⚠️ ENCRYPTION_KEY no configurada. Usando clave temporal: {_KEY}")
        print("⚠️ Configura ENCRYPTION_KEY en docker-compose.yml para producción!")
    return Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)


def encrypt_value(value: str) -> str:
    """Encrypt a string value. Returns base64-encoded encrypted string."""
    if not value:
        return value
    f = _get_fernet()
    return f.encrypt(value.encode('utf-8')).decode('utf-8')


def decrypt_value(value: str) -> str:
    """Decrypt an encrypted string value."""
    if not value:
        return value
    try:
        f = _get_fernet()
        return f.decrypt(value.encode('utf-8')).decode('utf-8')
    except Exception:
        # If decryption fails (old data), return as-is
        return value


def encrypt_number(value: float) -> str:
    """Encrypt a number as string."""
    if value is None:
        return None
    return encrypt_value(str(float(value)))


def decrypt_number(value: str) -> float:
    """Decrypt an encrypted number."""
    if value is None:
        return 0.0
    try:
        decrypted = decrypt_value(str(value))
        return float(decrypted)
    except (ValueError, TypeError):
        # If it's already a plain number (migration period)
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
