from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.models.conexion_gmail import ConexionGmail
from app.modules.gmail import service

router = APIRouter()


@router.get("/estado")
def estado(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    c = db.query(ConexionGmail).filter(ConexionGmail.usuario_id == current_user.id).first()
    return {
        "configurado": bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET),
        "conectado": bool(c),
        "email": c.email if c else None,
        "ultima_sync": c.ultima_sync.isoformat() if c and c.ultima_sync else None,
    }


@router.get("/conectar")
def conectar(current_user=Depends(deps.get_current_user)):
    return {"auth_url": service.build_auth_url(current_user.id)}


# Sin JWT: Google redirige aquí directamente; el state identifica al usuario
@router.get("/callback", response_class=HTMLResponse)
def callback(
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(deps.get_db),
):
    if error or not code:
        return HTMLResponse(f"<h3>Conexión cancelada ({error or 'sin código'}). Puedes cerrar esta pestaña.</h3>", status_code=400)
    conexion = service.finalizar_conexion(db, code, state)
    return HTMLResponse(
        f"<h3>Gmail conectado: {conexion.email}</h3><p>Vuelve a MiFi y sincroniza. Puedes cerrar esta pestaña.</p>"
    )


@router.post("/sync")
def sync(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    return service.sync(db, current_user.id)


@router.delete("/")
def desconectar(
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    db.query(ConexionGmail).filter(ConexionGmail.usuario_id == current_user.id).delete()
    db.commit()
    return {"ok": True}
