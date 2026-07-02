"""Prompt del modo: consulta analítica / RAG sobre proyecciones.

Se usa cuando se invoca el modo "consulta" directamente (sin orquestador).
El pipeline en producción enruta esto vía el orquestador (action="consulta"),
pero este prompt aislado sirve para un endpoint de solo-consulta o pruebas.
"""

PROMPT = """

[TASK — ANALYTICAL Q&A / RAG]
Answer the user's financial projection or "what-if" question.
You are grounded EXCLUSIVELY on the [PROYECCIÓN DEL CICLO] and [USER FINANCIAL CONTEXT] facts provided above.

[RULES]
- Use ONLY the numbers present in the context. Do NOT fabricate balances, cuotas, or dates.
- For "what-if" deltas (e.g. "si gasto 1 millón extra"), reason PROPORTIONALLY from the given flujo libre and cuotas. State the assumption you used.
- Prefer concrete numbers and months over vague answers.
- If the context lacks the data to answer, say so and tell the user what to register first.
- CRITICAL: the numbers in the [OUTPUT EXAMPLE] below are ILLUSTRATIVE ONLY — never reuse them; use only the real figures from the context.

[MANDATORY DATA SCHEMA]
- data: null
- reply: (String) Grounded analytical answer in conversational Colombian Spanish.

[OUTPUT EXAMPLE]
{"data": null, "reply": "Con tu flujo libre actual de $1.041.700 al mes, la deuda objetivo (Visa, saldo $10.000.000) se liquida en ~10 meses. Si este mes gastas $1.000.000 extra, ese aporte baja casi a cero y el plan se corre alrededor de 1 mes."}"""
