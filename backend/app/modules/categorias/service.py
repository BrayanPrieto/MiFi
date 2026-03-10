"""Service de categorías."""
from sqlalchemy.orm import Session
from app.models.categoria import Categoria


def get_categorias(db: Session, user_id):
    return db.query(Categoria).filter(
        (Categoria.usuario_id == None) | (Categoria.usuario_id == user_id)
    ).all()


def create_categoria(db: Session, user_id, nombre: str, tipo: str, color: str = None, icono: str = None):
    cat = Categoria(usuario_id=user_id, nombre=nombre, tipo=tipo, color=color, icono=icono)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def delete_categoria(db: Session, user_id, categoria_id: str) -> bool:
    obj = db.query(Categoria).filter(
        Categoria.id == categoria_id,
        Categoria.usuario_id == user_id,
    ).first()
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
