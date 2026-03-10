# MiFi (Mis Finanzas)

Aplicación multiplataforma diseñada para dar control total e inteligente de las finanzas personales (ingresos, gastos fijos, préstamos, ahorros y gastos variables), respaldada por Inteligencia Artificial para captura de facturas y registros en lenguaje natural.

## 🏗️ Estructura del Proyecto

Este monorepo se divide en dos grandes sub-proyectos:

1. **`/backend`**: El cerebro de la aplicación (Python + FastAPI + PostgreSQL). Contiene toda la lógica de negocio, validaciones y conexión con la base de datos y scripts de IA (Ollama).
2. **Raíz `/` (Frontend/App)**: Interfaz gráfica y App de escritorio nativa (Tauri v2 + Vue 3 + TypeScript + PrimeVue).

## 🚀 Despliegue con Docker (Recomendado)

El ecosistema entero de MiFi ha sido orquestado bajo contenedores para garantizar que el entorno de desarrollo y producción funcionen de forma idéntica en cualquier sistema operativo (solucionando problemas frecuentes como CORS y dependencias del sistema).

### Ventajas de esta Arquitectura
- **Cero Instalaciones:** No necesitas tener Python, Node.js ni PostgreSQL instalados en tu computadora local. Basta con Docker Desktop.
- **Aislamiento Nativo:** Cada pieza de la aplicación corre en su propio servidor inmutable (Frontend interactúa con Backend a través de redes cifradas de Docker).
- **Control de Estado:** Las sesiones viajan más rápido usando un servidor **Redis** dedicado en la memoria.
- **Producción Lista:** El Frontend ya no corre bajo un entorno dev (`localhost:5173`) sino que está minificado y servido mediante un servidor **Nginx** de alto rendimiento en el puerto 80.

### 🐳 Iniciar la Suite Completa de MiFi

1. Asegúrate de tener **Docker Desktop** instalado y abierto.
2. Abre tu terminal en la carpeta principal del proyecto (`MiFi`) y ejecuta un solo comando:

```bash
docker compose up -d --build
```

Esto descargará y levantará simultáneamente 4 microservicios en segundo plano:
*   ✨ **Frontend (Vue/Nginx):** `http://localhost:8080` (Abre esto en tu navegador)
*   🧠 **Backend (FastAPI):** `http://localhost:8000/docs`
*   💾 **Base de Datos (PostgreSQL):** `localhost:5432` 
*   ⚡ **Caché (Redis):** `localhost:6379`

### Detener los servicios
Cuando termines de trabajar, puedes apagar la aplicación ejecutando:
```bash
docker compose down
```

---
*Nota sobre Tauri:* Si en un futuro deseas compilar la aplicación de escritorio empaquetada (`.exe` o `.dmg`), todavía puedes usar la carpeta local ejecutando `npm run tauri build`, asegurándote primero de tener el entorno de **Rust** instalado nativamente en tu máquina.
