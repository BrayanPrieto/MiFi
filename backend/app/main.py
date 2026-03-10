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

# Auto-crear tablas al iniciar (para Docker con BD nueva)
@app.on_event("startup")
def on_startup():
    from app.db.base_class import Base
    from app.db.session import engine
    import app.models  # Importar todos los modelos para que Base los conozca
    Base.metadata.create_all(bind=engine)

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
