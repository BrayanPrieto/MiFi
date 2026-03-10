"""Router de categorías — GET, POST, DELETE."""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.usuario import Usuario
from app.schemas.categoria import Categoria as CategoriaSchema, CategoriaCreate
from .service import get_categorias, create_categoria, delete_categoria

router = APIRouter()


@router.get("/", response_model=List[CategoriaSchema])
def read_categorias(
    db: Session = Depends(deps.get_db),
    current_user: Usuario = Depends(deps.get_current_user),
) -> Any:
    return get_categorias(db, current_user.id)


@router.post("/", response_model=CategoriaSchema)
def create(
    *,
    db: Session = Depends(deps.get_db),
    categoria_in: CategoriaCreate,
    current_user: Usuario = Depends(deps.get_current_user),
) -> Any:
    return create_categoria(db, current_user.id, categoria_in.nombre, categoria_in.tipo, categoria_in.color, categoria_in.icono)


@router.delete("/{categoria_id}")
def delete(
    categoria_id: str,
    db: Session = Depends(deps.get_db),
    current_user: Usuario = Depends(deps.get_current_user),
) -> Any:
    if not delete_categoria(db, current_user.id, categoria_id):
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return {"ok": True}
