from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, require_roles
from ..models import Rider, StaffRole
from ..schemas import RiderCreate, RiderOut

router = APIRouter()


@router.post("/", response_model=RiderOut)
def create_rider(payload: RiderCreate, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    if db.query(Rider).filter(Rider.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="Phone already exists")
    rider = Rider(full_name=payload.full_name, phone=payload.phone, vehicle_details=payload.vehicle_details)
    db.add(rider)
    db.commit()
    db.refresh(rider)
    return rider


@router.get("/", response_model=list[RiderOut])
def list_riders(db: Session = Depends(get_db)):
    return db.query(Rider).all()


@router.put("/{rider_id}", response_model=RiderOut)
def update_rider(rider_id: str, payload: RiderCreate, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    rider = db.get(Rider, rider_id)
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    
    # Check if phone is being changed and if new phone already exists
    if payload.phone != rider.phone:
        existing = db.query(Rider).filter(Rider.phone == payload.phone, Rider.id != rider_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Phone already exists")
    
    rider.full_name = payload.full_name
    rider.phone = payload.phone
    rider.vehicle_details = payload.vehicle_details
    
    db.add(rider)
    db.commit()
    db.refresh(rider)
    return rider


@router.delete("/{rider_id}")
def delete_rider(rider_id: str, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    rider = db.get(Rider, rider_id)
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    
    # Soft delete by setting is_active to False
    rider.is_active = False
    db.add(rider)
    db.commit()
    
    return {"status": "deleted", "message": f"Rider {rider.full_name} has been deactivated"}
