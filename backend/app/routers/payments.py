from datetime import datetime
import hashlib 

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, require_roles
from ..models import Parcel, Receipt, Payment, StaffRole
from ..schemas import ReceiptOut

router = APIRouter()


import hashlib
from datetime import datetime

def generate_receipt_number() -> str:
    now_str = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    full_hash = hashlib.sha1(now_str.encode()).hexdigest().upper()
    # safe characters (exclude O, 0, I, L)
    safe_chars = "ABCDEFGHJKMNPQRSTUVWXYZ123456789"
    # filter hash to safe chars only
    filtered = "".join(ch for ch in full_hash if ch in safe_chars)
    # take first 5 safe chars
    random_part = filtered[:5]
    return f"RCPT-{random_part}"



@router.post("/{parcel_id}/receipt", response_model=ReceiptOut)
def generate_receipt(
    parcel_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_roles(
        StaffRole.RECEIVING,
        StaffRole.MANAGER,
        StaffRole.ADMIN,
        StaffRole.SUPER_ADMIN,
    ))
):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    if parcel.receipt:
        return parcel.receipt

    total = sum(p.amount for p in parcel.payments)

    receipt_number = generate_receipt_number()

    receipt = Receipt(
        parcel_id=parcel_id,
        receipt_number=receipt_number,
        total_amount=total,
        currency=parcel.amount_paid_currency,
    )
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
