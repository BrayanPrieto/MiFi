# MiFi (Mis Finanzas) - Backend

Este es el servidor REST API para la aplicación MiFi. Está construido sobre **Python 3.10+** y **FastAPI**, utilizando **PostgreSQL** como base de datos y **SQLAlchemy** como ORM.

## Estructura del Proyecto

* `app/api/`: Controladores (Endpoints)
* `app/core/`: Configuraciones base (CORS, JWT, settings)
* `app/db/`: Conexión de SQLAlchemy
* `app/models/`: Modelos ORM de Base de Datos
* `app/schemas/`: Validadores Pydantic (DTOs)
* `alembic/`: Control de versiones de la Base de Datos

## Requisitos
* Python 3.10 o superior (Se recomienda 3.11).
* Base de datos PostgreSQL local o remota (Neon/Supabase).

## Configuración Inicial

1. **Clonar repositorio e ir a la carpeta backend**:
   ```bash
   cd backend
   ```

2. **Crear y activar el entorno virtual**:
   ```bash
   # En Windows
   python -m venv venv
   .\venv\Scripts\activate

   # En macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Entorno**:
   Crea o modifica el archivo `.env` en raiz de `/backend`:
   ```env
   DATABASE_URL="postgresql://postgres:TU_CONTRASEÑA@localhost:5432/mifi"
   SECRET_KEY="A_VERY_SECRET_KEY_REPLACE_IN_PRODUCTION"
   ALGORITHM="HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ```

5. **Correr Migraciones (Crear tablas Psql)**:
   ```bash
   alembic upgrade head
   ```

## Ejecución del Servidor

Para iniciar el servidor en modo desarrollo con recarga automática:

```bash
uvicorn app.main:app --reload --port 8000
```
* La API principal estará en: `http://localhost:8000`
* Documentación Swagger interactiva: `http://localhost:8000/docs`

## Hacer Build / Deploy a Producción

Para correr en un ambiente de producción, no se debe usar `--reload`. Se recomienda usar gunicorn con uvicorn workers o dejar que plataformas Serverless (como Render/Railway/Heroku) monten la app usando el siguiente comando:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
