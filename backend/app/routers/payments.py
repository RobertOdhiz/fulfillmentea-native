from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, require_roles
from ..models import Parcel, Receipt, Payment, StaffRole
from ..schemas import ReceiptOut

router = APIRouter()


@router.post("/{parcel_id}/receipt", response_model=ReceiptOut)
def generate_receipt(parcel_id: str, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.RECEIVING, StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    if parcel.receipt:
        return parcel.receipt

    total = sum(p.amount for p in parcel.payments)
    receipt_number = f"RCPT-{parcel_id}-{int(datetime.utcnow().timestamp())}"
    receipt = Receipt(parcel_id=parcel_id, receipt_number=receipt_number, total_amount=total, currency=parcel.amount_paid_currency)
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return receipt


@router.get("/{parcel_id}/payments")
def list_payments(parcel_id: str, db: Session = Depends(get_db)):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel.payments
