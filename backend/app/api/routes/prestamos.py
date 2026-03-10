from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.prestamo import Prestamo
from app.models.movimiento_recurrente import MovimientoRecurrente
from app.schemas.prestamo import PrestamoCreate, Prestamo as PrestamoSchema

router = APIRouter()

@router.get("/", response_model=List[PrestamoSchema])
def list_prestamos(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
) -> Any:
    return db.query(Prestamo).filter(Prestamo.usuario_id == current_user.id).all()

@router.post("/", response_model=PrestamoSchema)
def create_prestamo(
    *,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
    data: PrestamoCreate,
) -> Any:
    obj = Prestamo(
        usuario_id=current_user.id,
        entidad=data.entidad,
        tipo=data.tipo,
        descripcion=data.descripcion,
        monto_total=data.monto_total,
        saldo_pendiente=data.saldo_pendiente,
        cuota_mensual_esperada=data.cuota_mensual_esperada,
        tasa_interes_mensual=data.tasa_interes_mensual,
        dia_pago=data.dia_pago,
        estado=data.estado,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)

    # Auto-crear recurrente para la cuota mensual
    if data.cuota_mensual_esperada and data.cuota_mensual_esperada > 0 and data.cuenta_pago_id:
        rec = MovimientoRecurrente(
            usuario_id=current_user.id,
            cuenta_id=data.cuenta_pago_id,
            nombre=f"Cuota {data.entidad}",
            tipo="PRESTAMO_CUOTA",
            monto=data.cuota_mensual_esperada,
            dia_mes=data.dia_pago or 1,
        )
        db.add(rec)
        db.commit()

    return obj

@router.delete("/{prestamo_id}")
def delete_prestamo(
    prestamo_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
) -> Any:
    obj = db.query(Prestamo).filter(Prestamo.id == prestamo_id, Prestamo.usuario_id == current_user.id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    db.delete(obj)
    db.commit()
    return {"ok": True}
