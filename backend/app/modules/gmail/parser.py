"""Parser de correos de notificación bancaria (Colombia) → movimiento.

ponytail: regex sobre asunto+cuerpo; si un banco no matchea, agregar su patrón aquí.
"""
import re
from typing import Optional

# Palabras que indican movimiento real (filtra promos, extractos, publicidad)
_GASTO_KW = (
    "compra por", "compraste", "pago por", "pagaste", "pago de", "retiro por",
    "retiraste", "enviaste", "transferencia por", "transaccion por", "transacción por",
    "cargo por", "debito por", "débito por",
)
_INGRESO_KW = (
    "recibiste", "te envio", "te envió", "consignacion", "consignación",
    "abono por", "abono de", "transferencia recibida", "pago de nomina", "pago de nómina",
)

_MONTO_RE = re.compile(r"(?:COP\s*)?\$\s*(\d[\d\.,]*)")
_COMERCIO_RE = re.compile(r"\ben\s+([A-Z0-9ÁÉÍÓÚÑ][\w\.\*ÁÉÍÓÚÑáéíóúñ-]*(?:\s+[\w\.\*ÁÉÍÓÚÑáéíóúñ-]+){0,4})")


def _parse_monto(raw: str) -> Optional[float]:
    """Normaliza '$1.234.567,89' (CO), '$1,234,567.89' (US) o '$123456'."""
    raw = raw.strip().rstrip(".,")
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")  # formato CO
        else:
            raw = raw.replace(",", "")  # formato US
    elif "," in raw:
        ent, _, dec = raw.rpartition(",")
        raw = f"{ent.replace('.', '')}.{dec}" if len(dec) == 2 else raw.replace(",", "")
    elif "." in raw:
        _, _, dec = raw.rpartition(".")
        if len(dec) != 2:
            raw = raw.replace(".", "")  # '123.456' son miles en CO
    try:
        v = float(raw)
        return v if v > 0 else None
    except ValueError:
        return None


def parse_email(subject: str, body: str) -> Optional[dict]:
    """Devuelve {monto, tipo, comercio} si el correo describe un movimiento; None si no."""
    texto = f"{subject}\n{body}"
    low = texto.lower()

    es_ingreso = any(k in low for k in _INGRESO_KW)
    es_gasto = any(k in low for k in _GASTO_KW)
    if not es_ingreso and not es_gasto:
        return None

    m = _MONTO_RE.search(texto)
    if not m:
        return None
    monto = _parse_monto(m.group(1))
    if not monto:
        return None

    # Comercio: lo que sigue a " en " después del monto (o en todo el texto)
    comercio = None
    cm = _COMERCIO_RE.search(texto[m.end():]) or _COMERCIO_RE.search(texto)
    if cm:
        comercio = re.sub(r"\s+", " ", cm.group(1)).strip(" .*-")

    return {
        "monto": monto,
        "tipo": "INGRESO" if (es_ingreso and not es_gasto) else "GASTO_VARIABLE",
        "comercio": comercio,
    }


if __name__ == "__main__":
    # Self-check con formatos reales de notificación
    r = parse_email(
        "Bancolombia le informa",
        "Bancolombia le informa Compra por $185.400,00 en EXITO CALLE 80 15:32. 01/07/2026 T.Cred *1234.",
    )
    assert r and r["monto"] == 185400.0 and r["tipo"] == "GASTO_VARIABLE" and "EXITO" in r["comercio"], r

    r = parse_email("Nequi", "Realizaste un pago por $50.000 en NETFLIX con tu cuenta Nequi")
    assert r and r["monto"] == 50000.0 and "NETFLIX" in r["comercio"], r

    r = parse_email("Davivienda", "Te informamos: recibiste una transferencia recibida por COP $2.106.500")
    assert r and r["monto"] == 2106500.0 and r["tipo"] == "INGRESO", r

    r = parse_email("Gran promo", "Aprovecha descuentos de hasta $100.000 en tu proxima compra... visita la web")
    # 'compra' sola no es keyword ('compra por' sí): las promos no deben crear movimientos
    assert r is None, r

    assert _parse_monto("1,234,567.89") == 1234567.89
    assert _parse_monto("123456") == 123456.0
    assert _parse_monto("185.400") == 185400.0
    assert _parse_monto("185.40") == 185.40
    print("parser OK")
