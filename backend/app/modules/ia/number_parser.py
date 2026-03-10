"""
Parser de números en español colombiano.
Extrae y normaliza montos del texto ANTES de enviarlo al LLM.
"""
import re
from typing import List, Tuple


def parse_colombian_numbers(text: str) -> Tuple[str, List[float]]:
    """
    Extrae montos del texto y los reemplaza con [MONTO:X].
    Retorna (texto_normalizado, lista_de_montos).
    
    Ejemplos:
      "pagué 300mil"           → ("pagué [MONTO:300000]", [300000])
      "me pagaron 5.200.000"   → ("me pagaron [MONTO:5200000]", [5200000])
      "costó 2 millones"       → ("costó [MONTO:2000000]", [2000000])
      "gasté 50k y 80k"        → ("gasté [MONTO:50000] y [MONTO:80000]", [50000, 80000])
      "vale 1.5 millones"      → ("vale [MONTO:1500000]", [1500000])
    """
    montos: List[float] = []
    
    # Orden importa: patrones más específicos primero
    patterns = [
        # "5.200.000" o "5,200,000" (formato largo con puntos/comas)
        (r'(\d{1,3}(?:[.,]\d{3})+)', _parse_dotted),
        # "4.9 millones", "1.5 millones"
        (r'(\d+[.,]\d+)\s*(?:millones|millon|mill)', _parse_decimal_millions),
        # "2 millones", "10 millones"
        (r'(\d+)\s*(?:millones|millon|mill)', _parse_millions),
        # "300mil", "300 mil", "50mil"
        (r'(\d+)\s*mil\b', _parse_mil),
        # "50k", "80k", "300K"
        (r'(\d+)\s*[kK]\b', _parse_k),
        # "$50.000" con signo peso
        (r'\$\s*(\d{1,3}(?:[.,]\d{3})+)', _parse_dotted),
        # "$50000" número plano con $
        (r'\$\s*(\d{4,})', _parse_plain),
    ]
    
    result = text
    
    for pattern, parser_fn in patterns:
        def replacer(match):
            try:
                val = parser_fn(match.group(1))
                if val and val > 0:
                    montos.append(val)
                    return f"[MONTO:{int(val)}]"
            except (ValueError, IndexError):
                pass
            return match.group(0)
        result = re.sub(pattern, replacer, result, flags=re.IGNORECASE)
    
    return result, montos


def _parse_dotted(s: str) -> float:
    """Parse "5.200.000" or "5,200,000" → 5200000"""
    # Remove dots/commas used as thousands separators
    clean = s.replace('.', '').replace(',', '')
    return float(clean)


def _parse_decimal_millions(s: str) -> float:
    """Parse "4.9" from "4.9 millones" → 4900000"""
    clean = s.replace(',', '.')
    return float(clean) * 1_000_000


def _parse_millions(s: str) -> float:
    """Parse "2" from "2 millones" → 2000000"""
    return float(s) * 1_000_000


def _parse_mil(s: str) -> float:
    """Parse "300" from "300mil" → 300000"""
    return float(s) * 1_000


def _parse_k(s: str) -> float:
    """Parse "50" from "50k" → 50000"""
    return float(s) * 1_000


def _parse_plain(s: str) -> float:
    """Parse plain number string"""
    return float(s)


def validate_amount(amount: float, max_amount: float = 100_000_000) -> bool:
    """Validate that an amount is within reasonable bounds."""
    return 0 < amount <= max_amount


def get_first_amount(montos: List[float]) -> float:
    """Get the first valid amount or 0."""
    return montos[0] if montos else 0
