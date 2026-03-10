"""IA Router — Endpoint /parse"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from .service import process_ia_request

router = APIRouter()


class IARequest(BaseModel):
    text: str
    mode: str = "general"
    history: Optional[List[dict]] = None


@router.post("/parse")
async def parse_ia(
    data: IARequest,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> Any:
    valid_modes = {"general", "transaccion", "recurrente", "prestamo", "meta", "categoria"}
    mode = data.mode if data.mode in valid_modes else "general"

    return await process_ia_request(
        text=data.text,
        mode=mode,
        history=data.history,
        db=db,
        current_user=current_user,
    )
