from datetime import datetime
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..core.config import settings
from ..deps import get_db, get_current_staff
from ..models import DeliveryOutcome, Parcel, ParcelPhoto, PhotoType, Payment, PaymentMethod, ParcelStatus, TrackingHistory, Staff
from ..services.notifications import send_sms
from ..schemas import ParcelCreate, ParcelOut, PaymentCreate, PaymentOut, PhotoOut, ParcelUpdate, TrackingHistoryCreate, TrackingHistoryOut, TrackingHistoryUpdate

router = APIRouter()


def validate_status_transition(current_status: ParcelStatus, new_status: ParcelStatus) -> bool:
    """Validate if the status transition is allowed"""
    status_flow = {
        ParcelStatus.RECEIVED: [ParcelStatus.PROCESSING, ParcelStatus.CANCELLED],
        ParcelStatus.PROCESSING: [ParcelStatus.IN_TRANSIT, ParcelStatus.CANCELLED],
        ParcelStatus.IN_TRANSIT: [ParcelStatus.ARRIVED_AT_HUB, ParcelStatus.CANCELLED],
        ParcelStatus.ARRIVED_AT_HUB: [ParcelStatus.OUT_FOR_DELIVERY, ParcelStatus.CANCELLED],
        ParcelStatus.OUT_FOR_DELIVERY: [ParcelStatus.DELIVERY_ATTEMPTED, ParcelStatus.DELIVERED, ParcelStatus.RETURNED],
        ParcelStatus.DELIVERY_ATTEMPTED: [ParcelStatus.OUT_FOR_DELIVERY, ParcelStatus.DELIVERED, ParcelStatus.RETURNED],
        ParcelStatus.DELIVERED: [],  # Final state
        ParcelStatus.RETURNED: [],   # Final state
        ParcelStatus.CANCELLED: [],  # Final state
    }
    return new_status in status_flow.get(current_status, [])


@router.post("/", response_model=ParcelOut)
def create_parcel(
    payload: ParcelCreate, 
    db: Session = Depends(get_db), 
    staff: Staff = Depends(get_current_staff)
):
    parcel = Parcel(
        sender_name=payload.sender_name,
        sender_phone=payload.sender_phone,
        sender_location=payload.sender_location,
        sender_country_code=payload.sender_country_code,
        receiver_name=payload.receiver_name,
        receiver_phone=payload.receiver_phone,
        receiver_location=payload.receiver_location,
        receiver_country_code=payload.receiver_country_code,
        parcel_type=payload.parcel_type,
        value_amount=payload.value.amount,
        value_currency=payload.value.currency,
        amount_paid_amount=payload.amount_paid.amount,
        amount_paid_currency=payload.amount_paid.currency,
        special_instructions=payload.special_instructions,
        received_by_id=staff.id,
        current_status=ParcelStatus.RECEIVED,
    )
    db.add(parcel)
    db.commit()
    db.refresh(parcel)
    
    # Create initial tracking history
    initial_tracking = TrackingHistory(
        parcel_id=parcel.id,
        status=ParcelStatus.RECEIVED,
        location=settings.default_location or "Main Office",
        notes="Parcel received at facility",
        updated_by_staff_id=staff.id
    )
    db.add(initial_tracking)
    db.commit()
    
    # Notify sender and receiver
    try:
        send_sms(parcel.sender_phone, f"Parcel {parcel.id} received at origin.")
        send_sms(parcel.receiver_phone, f"Parcel for you ({parcel.id}) has been received and will be dispatched soon.")
    except Exception:
        pass
    
    return parcel


@router.get("/", response_model=List[ParcelOut])
def list_parcels(
    db: Session = Depends(get_db),
):
    return db.query(Parcel).order_by(Parcel.created_at.desc()).all()


@router.get("/{parcel_id}", response_model=ParcelOut)
def get_parcel(
    parcel_id: str,
    db: Session = Depends(get_db),
):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel


@router.post("/{parcel_id}/photos", response_model=PhotoOut)
def upload_photo(
    parcel_id: str, 
    type: PhotoType = Form(...), 
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    staff: Staff = Depends(get_current_staff)
):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    # Create media directory if it doesn't exist
    os.makedirs(settings.media_dir, exist_ok=True)
    
    filename = f"parcel_{parcel_id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
    dest = os.path.join(settings.media_dir, filename)
    
    try:
        with open(dest, "wb") as f:
            content = file.file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    photo = ParcelPhoto(
        parcel_id=parcel_id, 
        type=type, 
        file_path=dest,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo


@router.post("/{parcel_id}/payments", response_model=PaymentOut)
def add_payment(
    parcel_id: str, 
    payload: PaymentCreate, 
    db: Session = Depends(get_db),
    staff: Staff = Depends(get_current_staff)
):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    payment = Payment(
        parcel_id=parcel_id,
        amount=payload.amount,
        currency=payload.currency,
        method=payload.method,
        reference=payload.reference,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.put("/{parcel_id}", response_model=ParcelOut)
def update_parcel(
    parcel_id: str, 
    payload: ParcelUpdate, 
    db: Session = Depends(get_db),
    staff: Staff = Depends(get_current_staff)
):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    # Update fields
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(parcel, field):
            setattr(parcel, field, value)
        elif field == 'value' and value:
            parcel.value_amount = value.amount
            parcel.value_currency = value.currency
        elif field == 'amount_paid' and value:
            parcel.amount_paid_amount = value.amount
            parcel.amount_paid_currency = value.currency
    
    parcel.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(parcel)
    return parcel


@router.post("/{parcel_id}/track", response_model=TrackingHistoryOut)
def add_tracking_history(
    parcel_id: str, 
    payload: TrackingHistoryCreate, 
    db: Session = Depends(get_db),
    staff: Staff = Depends(get_current_staff)
):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    # Validate status transition
    if not validate_status_transition(parcel.current_status, payload.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {parcel.current_status} to {payload.status}"
        )
    
    # Create tracking history
    tracking_history = TrackingHistory(
        parcel_id=parcel_id,
        status=payload.status,
        location=payload.location,
        notes=payload.notes,
        updated_by_staff_id=staff.id
    )
    
    # Update parcel status
    parcel.current_status = payload.status
    
    # Update specific timestamps based on status
    if payload.status == ParcelStatus.DISPATCHED:
        parcel.dispatched = True
        parcel.dispatched_at = datetime.utcnow()
    elif payload.status == ParcelStatus.DELIVERED:
        parcel.delivered = True
        parcel.delivered_at = datetime.utcnow()
        parcel.delivery_outcome = DeliveryOutcome.SUCCESS
    
    db.add(tracking_history)
    db.commit()
    db.refresh(tracking_history)
    
    # Send notification for important status changes
    if payload.status in [ParcelStatus.DELIVERED, ParcelStatus.OUT_FOR_DELIVERY]:
        try:
            message = f"Your parcel {parcel_id} status updated to: {payload.status}"
            if payload.status == ParcelStatus.OUT_FOR_DELIVERY:
                message += ". Delivery is on the way!"
            send_sms(parcel.receiver_phone, message)
        except Exception:
            pass
    
    return tracking_history


@router.put("/{parcel_id}/track/{tracking_history_id}", response_model=TrackingHistoryOut)
def update_tracking_history(
    parcel_id: str, 
    tracking_history_id: str, 
    payload: TrackingHistoryUpdate, 
    db: Session = Depends(get_db),
    staff: Staff = Depends(get_current_staff)
):
    tracking_history = db.get(TrackingHistory, tracking_history_id)
    if not tracking_history or tracking_history.parcel_id != parcel_id:
        raise HTTPException(status_code=404, detail="Tracking history not found")
    
    # If updating status, validate the transition
    if payload.status and payload.status != tracking_history.status:
        parcel = db.get(Parcel, parcel_id)
        if not validate_status_transition(parcel.current_status, payload.status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot transition from {parcel.current_status} to {payload.status}"
            )
        # Update parcel status if this is the latest tracking entry
        latest_tracking = db.query(TrackingHistory).filter(
            TrackingHistory.parcel_id == parcel_id
        ).order_by(TrackingHistory.created_at.desc()).first()
        
        if latest_tracking and latest_tracking.id == tracking_history_id:
            parcel.current_status = payload.status
    
    # Update tracking history
    if payload.status:
        tracking_history.status = payload.status
    if payload.location:
        tracking_history.location = payload.location
    if payload.notes is not None:
        tracking_history.notes = payload.notes
    
    db.commit()
    db.refresh(tracking_history)
    return tracking_history


@router.get("/{parcel_id}/track", response_model=List[TrackingHistoryOut])
def list_tracking_history(
    parcel_id: str, 
    db: Session = Depends(get_db),
    staff: Optional[Staff] = Depends(get_current_staff)  # Optional auth for public tracking
):
    parcel = db.get(Parcel, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    return db.query(TrackingHistory).filter(
        TrackingHistory.parcel_id == parcel_id
    ).order_by(TrackingHistory.created_at.asc()).all()  # Changed to ascending for timeline


@router.get("/{parcel_id}/track/{tracking_history_id}", response_model=TrackingHistoryOut)
def get_tracking_history(
    parcel_id: str, 
    tracking_history_id: str, 
    db: Session = Depends(get_db),
    staff: Optional[Staff] = Depends(get_current_staff)  # Optional auth
):
    tracking_history = db.get(TrackingHistory, tracking_history_id)
    if not tracking_history or tracking_history.parcel_id != parcel_id:
        raise HTTPException(status_code=404, detail="Tracking history not found")
    return tracking_history


@router.get("/track/{tracking_number}", response_model=List[TrackingHistoryOut])
def track_parcel_public(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """Public endpoint for tracking parcels without authentication"""
    parcel = db.query(Parcel).filter(Parcel.tracking_number == tracking_number).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    return db.query(TrackingHistory).filter(
        TrackingHistory.parcel_id == parcel.id
    ).order_by(TrackingHistory.created_at.asc()).all()