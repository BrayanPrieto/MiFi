"""Prompt del modo: registrar movimientos recurrentes mensuales."""

PROMPT = """

[TASK]
Identify and register monthly recurring transactions (subscriptions, rent, payroll, etc.).

[DATA CONTRACT - "data" ARRAY]
Each object MUST have:
- "nombre" (String): Name of the service or recurring payment.
- "tipo" (String): "INGRESO" | "GASTO_FIJO" | "PRESTAMO_CUOTA" | "AHORRO"
- "monto" (Integer | null): Numeric value. null if not mentioned.
- "dia_mes" (Integer | null): Day of the month for the charge (1-31). null if not mentioned.
- "categoria_sugerida" (String): Logical category (e.g., "Suscripciones", "Vivienda", "Nómina").
- "cuenta_nombre" (String | null): Account from which it is paid. null if not mentioned.

[OUTPUT EXAMPLE]
{"data": [{"nombre": "Netflix", "tipo": "GASTO_FIJO", "monto": 35000, "dia_mes": null, "categoria_sugerida": "Suscripciones", "cuenta_nombre": null}], "reply": "¡Perfecto! Ya configuré Netflix como un pago recurrente mensual de $35.000."}"""
