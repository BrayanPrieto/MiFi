from fastapi import APIRouter

# New modular imports
from app.modules.ia.router import router as ia_router
from app.modules.categorias.router import router as categorias_router

# Existing routes (will be modularized gradually)
from app.api.routes import auth, usuarios, cuentas, transacciones, prestamos, metas, recurrentes, dashboard

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"])
api_router.include_router(cuentas.router, prefix="/cuentas", tags=["cuentas"])
api_router.include_router(categorias_router, prefix="/categorias", tags=["categorias"])
api_router.include_router(transacciones.router, prefix="/transacciones", tags=["transacciones"])
api_router.include_router(prestamos.router, prefix="/prestamos", tags=["prestamos"])
api_router.include_router(metas.router, prefix="/metas", tags=["metas"])
api_router.include_router(ia_router, prefix="/ia", tags=["ia"])
api_router.include_router(recurrentes.router, prefix="/recurrentes", tags=["recurrentes"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
