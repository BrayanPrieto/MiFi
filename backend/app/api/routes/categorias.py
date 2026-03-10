from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.usuario import Usuario
from app.models.categoria import Categoria
from app.schemas.categoria import Categoria as CategoriaSchema, CategoriaCreate

router = APIRouter()

@router.get("/", response_model=List[CategoriaSchema])
def read_categorias(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: Usuario = Depends(deps.get_current_user)
) -> Any:
    """
    Obtener categorías (Globales + las personalizadas del usuario actual).
    """
    # Filtra donde usuario_id sea null (globales) o sea el id del usuario actual
    categorias = db.query(Categoria).filter(
        (Categoria.usuario_id == None) | (Categoria.usuario_id == current_user.id)
    ).offset(skip).limit(limit).all()
    return categorias

@router.post("/", response_model=CategoriaSchema)
def create_categoria(
    *,
    db: Session = Depends(deps.get_db),
    categoria_in: CategoriaCreate,
    current_user: Usuario = Depends(deps.get_current_user)
) -> Any:
    """
    Crear nueva categoría personalizada para el usuario actual.
    """
    categoria = Categoria(
        usuario_id=current_user.id,
        nombre=categoria_in.nombre,
        tipo=categoria_in.tipo,
        color=categoria_in.color,
        icono=categoria_in.icono
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria
