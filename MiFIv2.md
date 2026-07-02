Product Requirements Document (PRD): MiFi V2

Código de Operación: Proyecto Espartano
Objetivo Principal: Desarrollar un sistema automatizado de control financiero personal (PWA) que orqueste la liquidación de pasivos de alto costo antes del Q1 de 2027 y estructure la acumulación de capital para adquisición de activos.

1. Principios Fundamentales (El "Por Qué")

El sistema MiFi V2 no es solo un registro de gastos; es un motor de cambio de comportamiento financiero. Se basa en las siguientes reglas inquebrantables:

1.1. "Págate a ti mismo primero" (El Diezmo del 10%)

Qué es: Separar el 10% del ingreso neto en el instante en que se recibe ($421.300 COP quincenales).

Por qué se hace: Matemáticamente, garantiza que tu patrimonio neto crezca independientemente del estado de tus deudas. Psicológicamente, rompe el ciclo de "trabajar el 100% del tiempo para pagarle a los bancos". Este dinero es intocable y sirve como semilla para futuras inversiones (ej. bienes raíces o vehículos productivos).

1.2. Fricción Cero en Ocio (Caja Menor / "Chicles")

Qué es: Una asignación fija de $250.000 COP quincenales para gastos discrecionales (transportes a la oficina, cafés, salidas).

Por qué se hace: Los presupuestos demasiado estrictos fracasan por fatiga. Al aislar este dinero en un bolsillo, el sistema asume que ya se "gastó". Regla de UX: La aplicación no debe obligar al usuario a registrar la compra de un café de $5.000. Eliminar la micro-gestión garantiza que el usuario no abandone la herramienta.

1.3. La Fusión Quincenal (El Disparo de Nieve)

Qué es: Guardar el excedente de la Quincena 1, sumarlo al excedente de la Quincena 2, y hacer un único pago masivo extra el día 28 a una deuda objetivo.

Por qué se hace: Psicológicamente, un solo pago extra de $2.000.000 genera más dopamina y sensación de avance que cuatro pagos pequeños de $500.000. Financieramente, ataca el capital principal justo antes del corte de intereses del banco.

2. Entidades de Datos y Contexto del Usuario

El sistema maneja las siguientes estructuras de datos basadas en la realidad financiera del usuario:

2.1. Ingresos

Sueldo Neto Operativo: $4.213.000 COP por quincena ($8.426.000 COP mensuales).

Frecuencia: Días 15 y 30/31 de cada mes.

2.2. Obligaciones Estructurales (Gastos Fijos)

Obligaciones que mantienen la vida operativa.

Arriendo Vivienda: $1.900.000

Educación (Clases Daniela): $600.000

Mantenimiento Dependientes (Perros): $400.000

Movilidad (Cuota Carro): $350.000

Ahorro Forzado Vivienda (FNA): $200.000

Suscripciones Digitales: $140.000

2.3. Mapa de Deudas (Pasivos)

El sistema debe gestionar entidades de deuda con cuotas mínimas proyectadas:

Visa Bancolombia: Saldo vivo ~$10M | Cuota aprox: $600.000

NU Bank: Saldo vivo ~$8.8M | Cuota aprox: $600.000

Amex Bancolombia: Saldo vivo ~$2M | Rediferida (Objetivo actual) | Cuota aprox: $100.000

3. Funcionalidades Esperadas de MiFi V2

3.1. Dashboard Táctico (La Pantalla Principal)

El dashboard no debe abrumar. Debe responder a la pregunta: "¿Cuánto dinero tengo que no esté comprometido?"

Barra de Progreso de Deuda Objetivo: Muestra visualmente cuánto falta para aniquilar la deuda prioritaria actual.

Reloj de Liquidez: Un contador que muestra el flujo de caja libre proyectado para el final del mes.

Estado de la Quincena Actual: Indicadores de semáforo (Verde, Amarillo, Rojo) que muestran si el saldo en la cuenta de ahorros es suficiente para cubrir los fijos de los próximos 15 días.

3.2. Módulo de Trazabilidad y Registro de Pagos

Para asegurar la tranquilidad mental del usuario y evitar dobles pagos o moras, el sistema debe incluir un Checklist de Ciclo Mensual.

Generación de Instancias: Cada mes, el sistema genera automáticamente "recibos pendientes" basados en los gastos fijos y cuotas de deuda.

Estados (Status): Cada ítem puede estar en tres estados: [Pendiente], [Congelado/Bolsillo], [Pagado].

Acción de Registro: El usuario hace un simple "Click" o "Swipe" sobre el arriendo y lo marca como [Pagado]. El sistema registra un timestamp (fecha y hora exactas) para guardar la trazabilidad (ej. "Pagado el 01-Jul-2026 a las 08:30 AM").

3.3. Módulo de Proyección y Eventos (Buffer)

Manejo de Imprevistos Predecibles: Permite registrar eventos futuros (ej. "Derechos de Grado: $1.000.000 en Julio").

Efecto: El sistema deduce automáticamente este valor del Flujo Libre del mes correspondiente, ajustando la proyección del "Disparo de Nieve" sin que el usuario tenga que recalcular todo.

3.4. Asistente de IA Local (RAG Module)

Funcionalidad: Un chat integrado impulsado por IA local (ej. Ollama + LLM ligero).

Técnica: Usa Recuperación Aumentada por Generación (RAG) consultando una base de datos vectorial interna.

Casos de uso esperados: El usuario puede preguntar: "¿Si me voy de viaje y gasto un millón extra este mes, en qué mes terminaré de pagar la tarjeta Visa?" El LLM lee las proyecciones y responde con cálculos exactos sin comprometer la privacidad de los datos enviándolos a la nube.

4. El Algoritmo de Ejecución (Flujo Mensual)

Así es como la app organiza el dinero a lo largo del mes. Esto es lo que el código backend debe replicar:

FASE 1: Recepción y Supervivencia (Día 30/31 al 5)

Entrada: +$4.213.000 (Nómina).

Deducción Automática (Día 2): El sistema registra - $421.300 (Ahorro 10%) y - $250.000 (Caja Menor).

Trazabilidad Manual: El usuario marca como [Pagado] el Arriendo, Clases, y FNA.

Cierre Fase 1: El sistema calcula el Remanente Q1 y lo marca visualmente como [Congelado]. Este dinero no se toca.

FASE 2: Operación y Deuda (Día 15 al 20)

Entrada: +$4.213.000 (Nómina).

Deducción Automática (Día 17): El sistema registra - $421.300 (Ahorro 10%) y - $250.000 (Caja Menor).

Trazabilidad Manual: El usuario marca como [Pagado] las cuotas mínimas de las Tarjetas (Visa, NU, Amex) y la comida de los perros.

Cierre Fase 2: El sistema calcula el Remanente Q2.

FASE 3: El Ataque (Día 28)

Alerta del Sistema: MiFi V2 envía una notificación/mensaje: "Día de disparo. Tienes $X.XXX.XXX disponibles para aniquilar capital."

Cálculo interno: $$ Remanente Q1 + Remanente Q2 = Flujo Libre Total $$

Acción: El usuario transfiere ese dinero a la Deuda Objetivo #1 y la registra en el sistema. El gráfico de deuda se actualiza dramáticamente hacia abajo.