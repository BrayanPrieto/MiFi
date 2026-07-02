"""Prompt del modo: crear metas de ahorro."""

PROMPT = """

[TASK]
Establish a savings goal and calculate its feasibility.
Calculate estimated months: monto_objetivo / monthly_free_balance from the context.

[DATA CONTRACT - "data" ARRAY]
Each object MUST have:
- "nombre" (String): Purpose of the goal.
- "monto_objetivo" (Integer | null): Target value. null if not mentioned.
- "meses_estimados" (Integer | null): Feasibility calculation.

[OUTPUT EXAMPLE]
{"data": [{"nombre": "Moto", "monto_objetivo": 16000000, "meses_estimados": 12}], "reply": "¡Excelente meta! Acabo de crear tu meta de ahorro 'Moto' por 16 millones. Viendo tus ingresos y gastos actuales, estimo que podrás lograrlo en 12 meses."}"""
