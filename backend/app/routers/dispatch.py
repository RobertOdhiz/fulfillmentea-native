from datetime import datetime
import uuid
from sqlalchemy.orm import joinedload, selectinload
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, require_roles, get_current_staff
from ..models import Parcel, Assignment, Rider, StaffRole, ParcelStatus, OTP, Staff
from ..schemas import AssignmentCreate, AssignmentOut, ParcelOutLite, RiderOutLite, StaffOutLite
from ..utils.otp import generate_otp_code, hash_otp, expiry_time
from ..services.notifications import send_sms

router = APIRouter()

def _to_e164(phone: str) -> str:
    p = str(phone or "").strip().replace(" ", "").replace("-", "")
    if not p:
        return ""
    if not p.startswith("+") and p[0].isdigit():
        p = f"+{p}"
    return p

def _ensure_reference(reference: str = None) -> str:
    if not reference:
        return uuid.uuid4().hex
    reference = str(reference)
    if len(reference) >= 20:
        return reference
    pad = uuid.uuid4().hex
    new_ref = (reference + pad)[:max(20, len(reference))]
    if len(new_ref) < 20:
        new_ref = new_ref + pad[: (20 - len(new_ref))]
    return new_ref


@router.post("/{parcel_id}/assign", response_model=AssignmentOut)
def assign_rider(parcel_id: str, payload: AssignmentCreate, db: Session = Depends(get_db), current=Depends(require_roles(StaffRole.DISPATCHER, StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    parcel = db.get(Parcel, parcel_id)
    rider = db.get(Rider, payload.rider_id)
    if not parcel or not rider:
        raise HTTPException(status_code=404, detail="Parcel or Rider not found")
    
    # Check if parcel already has an assignment
    existing_assignment = db.query(Assignment).filter(Assignment.parcel_id == parcel_id).first()
    if existing_assignment:
        # Update existing assignment
        existing_assignment.rider_id = payload.rider_id
        existing_assignment.assigned_by_staff_id = current.id
        existing_assignment.assigned_at = datetime.utcnow()
        assignment = existing_assignment
    else:
        # Create new assignment
        assignment = Assignment(parcel_id=parcel_id, rider_id=payload.rider_id, assigned_by_staff_id=current.id)
        db.add(assignment)
    
    # Generate OTP for delivery
    code = generate_otp_code()
    otp = OTP(parcel_id=parcel_id, code_hash=hash_otp(code), expires_at=expiry_time())
    db.add(otp)
    
    # Update parcel status to indicate it's ready for delivery
    parcel.current_status = ParcelStatus.OUT_FOR_DELIVERY
    
    db.commit()
    db.refresh(assignment)
    
    # Send SMS notifications
    # try:
    #     # Notify sender about rider assignment
    #     sender_message = f"Parcel {parcel_id} has been assigned to rider {rider.full_name} ({rider.phone}). Your parcel is now out for delivery!"
    #     send_sms(_to_e164(parcel.sender_phone), sender_message)
        
    #     # Notify receiver with OTP and rider details
    #     receiver_message = f"Your parcel {parcel_id} is out for delivery! Rider: {rider.full_name} ({rider.phone}). Delivery OTP: {code}. Please have this code ready when the rider arrives."
    #     send_sms(_to_e164(parcel.receiver_phone), receiver_message)
        
    #     # Notify rider about new assignment
    #     rider_message = f"You have been assigned parcel {parcel_id}. Pickup from: {parcel.sender_name} ({parcel.sender_phone}) at {parcel.sender_location}. Deliver to: {parcel.receiver_name} ({parcel.receiver_phone}) at {parcel.receiver_location}."
    #     send_sms(_to_e164(rider.phone), rider_message)
        
    # except Exception as e:
    #     print(f"Failed to send SMS notifications: {e}")
        # Continue even if SMS fails
    
    # Return the assignment with proper nested structure
    return assignment


@router.get("/", response_model=list[AssignmentOut])
@router.get("", response_model=list[AssignmentOut], include_in_schema=False)
def list_assignments(db: Session = Depends(get_db)):
    """List all parcel assignments with nested relationships"""
    # Use joinedload to fetch all related data in one query
    assignments = db.query(Assignment).options(
        joinedload(Assignment.parcel),
        joinedload(Assignment.rider),
        joinedload(Assignment.assigned_by_staff)
    ).all()
    
    return assignments


@router.post("/{parcel_id}/dispatch")
def dispatch_parcel(parcel_id: str, db: Session = Depends(get_db)):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    if parcel.dispatched:
        return {"status": "already_dispatched"}

    code = generate_otp_code()
    otp = OTP(parcel_id=parcel_id, code_hash=hash_otp(code), expires_at=expiry_time())

    parcel.dispatched = True
    parcel.dispatched_at = datetime.utcnow()
    parcel.current_status = ParcelStatus.DISPATCHED

    db.add(otp)
    db.add(parcel)
    db.commit()

    # Notify both sender and receiver on dispatch and send OTP to receiver
    send_sms(_to_e164(parcel.sender_phone), f"Mzigo {parcel.tracking_number} unasafirishwa .")
    send_sms(_to_e164(parcel.receiver_phone), f"Nambari yako ya OTP kwa kupokea mzigo ni {code}")
    return {"status": "ok"}