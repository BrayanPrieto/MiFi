"""Prompt del modo: crear categorías."""

PROMPT = """

[TASK]
Create new master financial organization categories.

[DATA CONTRACT - "data" ARRAY]
Each object MUST have:
- "nombre" (String): Title of the category.
- "tipo" (String): "INGRESO" | "GASTO_FIJO" | "GASTO_VARIABLE" | "PRESTAMO_CUOTA" | "AHORRO"

[OUTPUT EXAMPLE]
{"data": [{"nombre": "Mascotas", "tipo": "GASTO_VARIABLE"}], "reply": "¡Listo! Ya creé la categoría 'Mascotas' para tus gastos."}"""
