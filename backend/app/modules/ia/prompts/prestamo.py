"""Prompt del modo: registrar préstamos / deudas."""

PROMPT = """

[TASK]
Register a new loan or acquired debt.
IMPORTANT: Note that the system automatically handles monthly installments based on the starting date/month if "cuota_mensual" is provided.

[DATA CONTRACT - "data" ARRAY]
Each object MUST have:
- "entidad" (String): Person or institution owed.
- "tipo" (String): "BANCO" | "TERCERO"
- "monto_total" (Integer | null): Original total value of the debt.
- "saldo_pendiente" (Integer | null): Amount currently owed.
- "cuota_mensual" (Integer | null): Installment value if mentioned.
- "dia_pago" (Integer | null): Day of the month for payment (1-31).
- "cuenta_nombre" (String | null): Account from which it is paid.

[OUTPUT EXAMPLE]
{"data": [{"entidad": "Nu", "tipo": "BANCO", "monto_total": null, "saldo_pendiente": 5000000, "cuota_mensual": null, "dia_pago": null, "cuenta_nombre": null}], "reply": "Ya dejé anotado tu préstamo con Nu por un saldo de $5.000.000. ¿De cuánto serán las cuotas mensuales?"}"""
