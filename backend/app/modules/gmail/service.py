"""Conexión Gmail: OAuth 2.0 + sync de correos bancarios → transacciones.

Flujo: GET /gmail/conectar devuelve la URL de consentimiento de Google;
el callback guarda el refresh_token (encriptado con Fernet);
POST /gmail/sync trae correos de remitentes bancarios desde la última sync,
los parsea localmente (parser.py) y crea transacciones (dedup por gmail_msg_id).
El contenido de los correos NUNCA sale de tu servidor.
"""
import base64
import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.conexion_gmail import ConexionGmail
from app.models.cuenta import Cuenta
from app.models.transaccion import Transaccion
from app.modules.gmail.parser import parse_email
from app.modules.ia.service import match_tarjeta, get_default_account

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_API = "https://gmail.googleapis.com/gmail/v1/users/me"
_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"

# Remitentes bancarios CO típicos; el parser es el filtro real de contenido
_QUERY_BANCOS = (
    'from:(bancolombia OR nequi OR davivienda OR daviplata OR bbva '
    'OR "banco de bogota" OR colpatria OR falabella OR rappipay OR lulo OR scotiabank)'
)

# ponytail: state OAuth en memoria — suficiente para una sola instancia de backend
_pending_states: dict = {}


def _require_creds():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=400,
            detail="Faltan GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET en el .env. "
                   "Crea las credenciales OAuth en Google Cloud Console (Gmail API).",
        )


def build_auth_url(user_id) -> str:
    _require_creds()
    now = time.time()
    for s in [s for s, (_, exp) in _pending_states.items() if exp < now]:
        _pending_states.pop(s, None)
    state = secrets.token_urlsafe(24)
    _pending_states[state] = (str(user_id), now + 600)
    return _AUTH_URL + "?" + urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GMAIL_REDIRECT_URI,
        "response_type": "code",
        "scope": _SCOPE,
        "access_type": "offline",
        "prompt": "consent",  # fuerza refresh_token en cada conexión
        "state": state,
    })


def finalizar_conexion(db: Session, code: str, state: str) -> ConexionGmail:
    """Callback de Google: intercambia el code y guarda la conexión del usuario del state."""
    item = _pending_states.pop(state or "", None)
    if not item or item[1] < time.time():
        raise HTTPException(status_code=400, detail="Sesión de conexión inválida o expirada. Intenta de nuevo.")
    user_id = item[0]

    resp = httpx.post(_TOKEN_URL, data={
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GMAIL_REDIRECT_URI,
    }, timeout=30)
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Google rechazó el intercambio de código: {resp.text[:200]}")
    data = resp.json()
    refresh = data.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=400, detail="Google no devolvió refresh_token. Revoca el acceso en myaccount.google.com/permissions y reintenta.")

    perfil = httpx.get(
        f"{_API}/profile", headers={"Authorization": f"Bearer {data['access_token']}"}, timeout=30
    ).json()

    conexion = db.query(ConexionGmail).filter(ConexionGmail.usuario_id == user_id).first()
    if not conexion:
        conexion = ConexionGmail(usuario_id=user_id)
        db.add(conexion)
    conexion.refresh_token = refresh
    conexion.email = perfil.get("emailAddress")
    db.commit()
    db.refresh(conexion)
    return conexion


def _access_token(conexion: ConexionGmail) -> str:
    resp = httpx.post(_TOKEN_URL, data={
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "refresh_token": conexion.refresh_token,
        "grant_type": "refresh_token",
    }, timeout=30)
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="La conexión con Gmail expiró o fue revocada. Vuelve a conectar.")
    return resp.json()["access_token"]


def _extract_text(payload: dict) -> str:
    """text/plain del mensaje; si no hay, HTML sin tags; si no, cadena vacía."""
    stack = [payload]
    html = None
    while stack:
        p = stack.pop()
        stack.extend(p.get("parts", []))
        data = p.get("body", {}).get("data")
        if not data:
            continue
        text = base64.urlsafe_b64decode(data + "==").decode("utf-8", "ignore")
        mime = p.get("mimeType", "")
        if mime == "text/plain":
            return text
        if mime == "text/html" and html is None:
            html = text
    return re.sub(r"<[^>]+>", " ", html) if html else ""


def sync(db: Session, user_id) -> dict:
    _require_creds()
    conexion = db.query(ConexionGmail).filter(ConexionGmail.usuario_id == user_id).first()
    if not conexion:
        raise HTTPException(status_code=404, detail="Gmail no está conectado")

    token = _access_token(conexion)
    auth = {"Authorization": f"Bearer {token}"}
    desde = conexion.ultima_sync or (datetime.now(timezone.utc) - timedelta(days=30))
    q = f"{_QUERY_BANCOS} after:{int(desde.timestamp())}"

    existentes = {gid for (gid,) in db.query(Transaccion.gmail_msg_id).filter(
        Transaccion.usuario_id == user_id, Transaccion.gmail_msg_id.isnot(None)
    ).all()}
    cuentas = db.query(Cuenta).filter(Cuenta.usuario_id == user_id, Cuenta.activa == True).all()

    creados, ignorados = 0, 0
    with httpx.Client(timeout=30) as client:
        # ponytail: una página de 100 por sync; suficiente para alertas bancarias diarias
        resp = client.get(f"{_API}/messages", params={"q": q, "maxResults": 100}, headers=auth)
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Gmail API respondió {resp.status_code}: {resp.text[:200]}")
        ids = [m["id"] for m in resp.json().get("messages", [])]

        for mid in ids:
            if mid in existentes:
                continue
            msg = client.get(f"{_API}/messages/{mid}", params={"format": "full"}, headers=auth).json()
            payload = msg.get("payload", {})
            subject = next(
                (h["value"] for h in payload.get("headers", []) if h.get("name", "").lower() == "subject"), ""
            )
            body = _extract_text(payload) or msg.get("snippet", "")
            parsed = parse_email(subject, body)
            if not parsed:
                ignorados += 1
                continue

            texto = f"{subject} {body}"
            cuenta = match_tarjeta(cuentas, texto) or get_default_account(cuentas)
            if not cuenta:
                ignorados += 1
                continue

            fecha = datetime.fromtimestamp(int(msg.get("internalDate", time.time() * 1000)) / 1000).date()
            db.add(Transaccion(
                usuario_id=user_id,
                cuenta_id=cuenta.id,
                tipo=parsed["tipo"],
                monto=parsed["monto"],
                fecha=fecha,
                descripcion=parsed["comercio"] or subject[:120],
                esta_pagado=True,
                fuente_ia=True,
                texto_original=f"[Gmail] {subject} | {msg.get('snippet', '')}"[:400],
                gmail_msg_id=mid,
            ))
            creados += 1

    conexion.ultima_sync = datetime.now(timezone.utc)
    db.commit()
    return {"revisados": len(ids), "creados": creados, "ignorados": ignorados}
