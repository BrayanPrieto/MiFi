# Implementación del Agente IA (Ollama)

Este documento detalla el paso a seguir para integrar modelos LLMs eficientes como `Llama 3.2` o `Phi-3` localmente hacia la aplicación MiFi.

## Flujo del Input Textual:

1.  **Frontend (UI)**: Dispara la captura del micrófono o del input textbox en el Dashboard: 
    *`"Gasté 50 mil pesos colombianos en la gasolinera de la esquina pagando con tarjeta de crédito"`*.
2. **Backend (FastAPI)**: Recibe el prompt crudo en una nueva ruta: `POST /api/v1/ia/parse`.
3. **Controlador IA**: Toma el schema de las Cuentas (`id`, `nombre`) y el schema vacío del modelo Pydantic `TransaccionCreate`.
4. **Ollama Execution**: Inyecta en el System Prompt el contexto financiero junto a los JSONs disponibles pidiendo estrictamente retornar el objeto mapeando el monto, la fecha extraída e ID adivinado para Cuenta y Categoría.
5. **Backend**: Instancia el modelo de `Transaccion` con la key `fuente_ia = True` y lo inserta a BD.
6. **Frontend UI**: Refresca y muesta la nueva tabla donde el gasto ahora aparece con el ícono `IA 🤖`.
