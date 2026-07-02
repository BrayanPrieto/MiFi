"""Prompt del modo: registrar transacciones puntuales."""

PROMPT = """

[TASK]
Classify and register one or multiple financial transactions (one-time income or expenses).
Each transaction mentioned MUST be an independent object in the "data" array.

[DATA CONTRACT - "data" ARRAY]
Each object MUST have:
- "tipo" (String): "INGRESO" | "GASTO_FIJO" | "GASTO_VARIABLE" | "PRESTAMO_CUOTA" | "AHORRO"
- "monto" (Integer | null): Numeric value. null if the user did not specify a number.
- "descripcion" (String): Short summary (max 5 words) describing the payment/income.
- "cuenta_nombre" (String | null): Name of the mentioned account, or null.

[CLASSIFICATION RULES]
- "payroll" / "salary" / "got paid" / "nómina" → tipo: "INGRESO"
- "rent" / "utilities" / "netflix" / "arriendo" → tipo: "GASTO_FIJO"
- "food" / "gas" / "purchase" / "comida" / "gasolina" → tipo: "GASTO_VARIABLE"
- "installment" / "loan" / "cuota" → tipo: "PRESTAMO_CUOTA"

[OUTPUT EXAMPLES]
With amount:
{"data": [{"tipo": "GASTO_VARIABLE", "monto": 50000, "descripcion": "Gasolina", "cuenta_nombre": null}], "reply": "¡Listo! Ya registré un pago de $50.000 de gasolina."}

Without amount:
{"data": [{"tipo": "GASTO_FIJO", "monto": null, "descripcion": "Amazon Prime", "cuenta_nombre": null}], "reply": "Dale, registré el pago de Amazon Prime. ¿De cuánto fue?"}

Multiple:
{"data": [{"tipo": "GASTO_FIJO", "monto": null, "descripcion": "Arriendo", "cuenta_nombre": null}, {"tipo": "GASTO_VARIABLE", "monto": null, "descripcion": "Comida perros", "cuenta_nombre": null}], "reply": "¡Hecho! Acabo de registrar el pago del arriendo y la comida para los perros."}"""
