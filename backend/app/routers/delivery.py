from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, require_roles
from ..models import Parcel, OTP, ParcelStatus, PhotoType, ParcelPhoto, StaffRole, DeliveryAttempt, DeliveryAttemptStatus, DeliveryOutcome
from ..utils.otp import generate_otp_code, hash_otp, expiry_time
from ..services.notifications import send_sms
from ..schemas import OTPVerifyRequest, PhotoOut, DeliveryAttemptCreate, DeliveryAttemptOut
from ..utils.security import verify_password
from ..models import Assignment, Rider

router = APIRouter()


@router.post("/{parcel_id}/verify-otp")
def verify_otp(parcel_id: str, payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    otp = (
        db.query(OTP)
        .filter(OTP.parcel_id == parcel_id, OTP.consumed_at.is_(None))
        .order_by(OTP.created_at.desc())
        .first()
    )
    if not otp:
        raise HTTPException(status_code=400, detail="No active OTP")
    if otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")
    if not verify_password(payload.code, otp.code_hash):
        # Invalidate current OTP and rotate a new one
        otp.consumed_at = datetime.utcnow()
        db.add(otp)
        # Create and send a new OTP
        new_code = generate_otp_code()
        new_otp = OTP(parcel_id=parcel_id, code_hash=hash_otp(new_code), expires_at=expiry_time())
        db.add(new_otp)
        db.commit()
        # Notify receiver with the rotated OTP
        send_sms(parcel.receiver_phone, f"Your new delivery OTP is {new_code}")
        raise HTTPException(status_code=400, detail="Invalid OTP. A new code has been sent.")

    otp.consumed_at = datetime.utcnow()
    parcel.current_status = ParcelStatus.OUT_FOR_DELIVERY
    db.add(otp)
    db.add(parcel)
    db.commit()

    return {"status": "otp_verified", "message": "OTP verified successfully. Parcel is now confirmed for delivery."}


@router.get("/{parcel_id}/info")
def get_delivery_info(parcel_id: str, db: Session = Depends(get_db)):
    """Get delivery information for a parcel (public access)"""
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    # Get rider assignment
    assignment = db.query(Assignment).filter(Assignment.parcel_id == parcel_id).first()
    rider_info = None
    if assignment:
        rider = db.get(Rider, assignment.rider_id)
        if rider:
            rider_info = {
                "name": rider.full_name,
                "phone": rider.phone,
                "vehicle_details": rider.vehicle_details
            }
    
    # Get active OTP info
    otp = db.query(OTP).filter(
        OTP.parcel_id == parcel_id, 
        OTP.consumed_at.is_(None),
        OTP.expires_at > datetime.utcnow()
    ).first()
    
    return {
        "parcel_id": parcel_id,
        "status": parcel.current_status,
        "sender_name": parcel.sender_name,
        "receiver_name": parcel.receiver_name,
        "assigned_rider": rider_info,
        "has_active_otp": otp is not None,
        "otp_expires_at": otp.expires_at if otp else None,
        "dispatched": parcel.dispatched,
        "delivered": parcel.delivered
    }


@router.post("/{parcel_id}/attempts", response_model=DeliveryAttemptOut)
def record_attempt(parcel_id: str, payload: DeliveryAttemptCreate, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.DELIVERY, StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    attempt = DeliveryAttempt(parcel_id=parcel_id, rider_id=payload.rider_id, status=payload.status, note=payload.note)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.post("/{parcel_id}/mark-failed")
def mark_failed(parcel_id: str, reason: str, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.DELIVERY, StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    parcel.delivered = False
    parcel.delivery_outcome = DeliveryOutcome.FAILED
    parcel.failure_reason = reason
    parcel.current_status = ParcelStatus.OUT_FOR_DELIVERY
    db.add(parcel)
    db.commit()
    return {"status": "failed"}


@router.post("/{parcel_id}/confirm-delivery")
def confirm_delivery(parcel_id: str, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.DELIVERY, StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    parcel.delivered = True
    parcel.delivered_at = datetime.utcnow()
    parcel.current_status = ParcelStatus.DELIVERED
    parcel.delivery_outcome = DeliveryOutcome.SUCCESS
    parcel.failure_reason = None
    db.add(parcel)
    db.commit()
    # Notify both sender and receiver upon successful delivery
    try:
        send_sms(parcel.sender_phone, f"Parcel {parcel.id} delivered successfully.")
        send_sms(parcel.receiver_phone, f"Your parcel {parcel.id} has been delivered.")
    except Exception:
        pass
    return {"status": "delivered"}
