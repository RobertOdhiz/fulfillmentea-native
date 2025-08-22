from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, require_roles, get_current_staff
from ..models import Parcel, Assignment, Rider, StaffRole, ParcelStatus, OTP
from ..schemas import AssignmentCreate, AssignmentOut
from ..utils.otp import generate_otp_code, hash_otp, expiry_time
from ..services.notifications import send_sms

router = APIRouter()


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
    try:
        # Notify sender about rider assignment
        sender_message = f"Parcel {parcel_id} has been assigned to rider {rider.full_name} ({rider.phone}). Your parcel is now out for delivery!"
        send_sms(parcel.sender_phone, sender_message)
        
        # Notify receiver with OTP and rider details
        receiver_message = f"Your parcel {parcel_id} is out for delivery! Rider: {rider.full_name} ({rider.phone}). Delivery OTP: {code}. Please have this code ready when the rider arrives."
        send_sms(parcel.receiver_phone, receiver_message)
        
        # Notify rider about new assignment
        rider_message = f"You have been assigned parcel {parcel_id}. Pickup from: {parcel.sender_name} ({parcel.sender_phone}) at {parcel.sender_location}. Deliver to: {parcel.receiver_name} ({parcel.receiver_phone}) at {parcel.receiver_location}."
        send_sms(rider.phone, rider_message)
        
    except Exception as e:
        print(f"Failed to send SMS notifications: {e}")
        # Continue even if SMS fails
    
    return assignment


@router.get("/", response_model=list[AssignmentOut])
def list_assignments(db: Session = Depends(get_db)):
    """List all parcel assignments"""
    assignments = db.query(Assignment).all()
    
    # Enhance with rider and parcel names
    result = []
    for assignment in assignments:
        assignment_data = {
            "id": assignment.id,
            "parcel_id": assignment.parcel_id,
            "rider_id": assignment.rider_id,
            "assigned_by_staff_id": assignment.assigned_by_staff_id,
            "assigned_at": assignment.assigned_at
        }
        
        # Add rider name
        rider = db.get(Rider, assignment.rider_id)
        if rider:
            assignment_data["rider_name"] = rider.full_name
            assignment_data["rider_phone"] = rider.phone
        
        # Add parcel info
        parcel = db.get(Parcel, assignment.parcel_id)
        if parcel:
            assignment_data["parcel_sender"] = parcel.sender_name
            assignment_data["parcel_receiver"] = parcel.receiver_name
        
        result.append(assignment_data)
    
    return result


@router.post("/{parcel_id}/dispatch")
def dispatch_parcel(parcel_id: str, db: Session = Depends(get_db), staff=Depends(require_roles(StaffRole.DISPATCHER, StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
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
    send_sms(parcel.sender_phone, f"Parcel {parcel.id} dispatched.")
    send_sms(parcel.receiver_phone, f"Your delivery OTP is {code}")
    return {"status": "ok"}
