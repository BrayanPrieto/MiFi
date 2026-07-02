from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS - Abierto para desarrollo (sin whitelist)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-crear tablas + migrar columnas encriptadas a TEXT
@app.on_event("startup")
def on_startup():
    from app.db.base_class import Base
    from app.db.session import engine
    from sqlalchemy import text
    import app.models  # Importar todos los modelos para que Base los conozca
    Base.metadata.create_all(bind=engine)

    # Migrar columnas encriptadas de VARCHAR → TEXT
    encrypted_columns = [
        ("cuentas", "nombre"),
        ("transacciones", "descripcion"),
        ("transacciones", "texto_original"),
        ("movimientos_recurrentes", "nombre"),
        ("prestamos", "entidad"),
        ("prestamos", "descripcion"),
        ("metas_ahorro", "nombre"),
    ]
    # Columnas nuevas (V2): agregar si no existen, sin romper datos existentes
    add_columns = [
        ("prestamos", "es_objetivo", "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("prestamos", "prioridad", "SMALLINT"),
        ("recibos", "es_ahorro", "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("cuentas", "cuota_mensual", "NUMERIC(15,2)"),
        ("cuentas", "es_objetivo", "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("cuentas", "prioridad", "SMALLINT"),
        ("movimientos_recurrentes", "cuenta_destino_id", "UUID REFERENCES cuentas(id) ON DELETE SET NULL"),
        ("configuraciones_ciclo", "dia_ahorro", "SMALLINT NOT NULL DEFAULT 17"),
    ]
    with engine.connect() as conn:
        for table, col in encrypted_columns:
            try:
                conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN {col} TYPE TEXT"))
                conn.commit()
            except Exception:
                conn.rollback()  # Column might already be TEXT
        for table, col, coldef in add_columns:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {coldef}"))
                conn.commit()
            except Exception:
                conn.rollback()
    print("Migraciones de columnas aplicadas")

# Manejador global de errores para que CORS no se pierda en errores 500
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Error interno del servidor: {str(exc)}"},
    )

@app.get("/health", tags=["System"])
def health_check():
    """
    Endpoint básico para verificar que el servidor está vivo.
    """
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": settings.VERSION}

from app.api.main import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)
