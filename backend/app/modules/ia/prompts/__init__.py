"""Registro de prompts del sistema.

Cada modo vive en su propio archivo (base + orquestador + uno por acción).
`get_system_prompt` ensambla: contexto base + cuerpo del modo.
"""
from . import (
    base,
    orquestador,
    transaccion,
    recurrente,
    prestamo,
    meta,
    categoria,
    general,
    consulta,
)

# modo -> cuerpo del prompt (se antepone el contexto base)
_REGISTRY = {
    "unificado": orquestador.PROMPT,
    "transaccion": transaccion.PROMPT,
    "recurrente": recurrente.PROMPT,
    "prestamo": prestamo.PROMPT,
    "meta": meta.PROMPT,
    "categoria": categoria.PROMPT,
    "general": general.PROMPT,
    "consulta": consulta.PROMPT,
}


def get_system_prompt(mode: str, user_context: str) -> str:
    """Construye el system prompt completo para un modo dado."""
    ctx = base.build_context(user_context)
    body = _REGISTRY.get(mode, _REGISTRY["general"])
    return ctx + body
