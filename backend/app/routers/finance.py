from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, require_roles
from ..models import Dispute, Refund, Parcel, StaffRole, DisputeStatus
from ..schemas import DisputeCreate, DisputeOut, RefundCreate, RefundOut

router = APIRouter()


@router.post("/{parcel_id}/disputes", response_model=DisputeOut)
def create_dispute(parcel_id: str, payload: DisputeCreate, db: Session = Depends(get_db)):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    dispute = Dispute(parcel_id=parcel_id, raised_by=payload.raised_by, reason=payload.reason)
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return dispute


@router.post("/refunds", response_model=RefundOut)
def process_refund(payload: RefundCreate, db: Session = Depends(get_db), current=Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    dispute = db.get(Dispute, payload.dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    refund = Refund(dispute_id=payload.dispute_id, amount=payload.amount, currency=payload.currency, approved_by_staff_id=current.id)
    dispute.status = DisputeStatus.REFUNDED
    dispute.resolved_at = datetime.utcnow()

    db.add(refund)
    db.add(dispute)
    db.commit()
    db.refresh(refund)
    return refund
