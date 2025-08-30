from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_staff, require_roles
from ..models import Staff, StaffRole
from ..schemas import StaffOut, StaffUpdate
from ..utils.security import get_password_hash

router = APIRouter()


@router.get("/me", response_model=StaffOut)
def me(current: Staff = Depends(get_current_staff)):
    return current


@router.get("/", response_model=list[StaffOut])
@router.get("", response_model=list[StaffOut], include_in_schema=False)
def list_staff(db: Session = Depends(get_db), _: Staff = Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    return db.query(Staff).all()


@router.put("/{staff_id}", response_model=StaffOut)
def update_staff(staff_id: str, payload: StaffUpdate, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    staff = db.get(Staff, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Check if phone is being changed and if new phone already exists
    if payload.phone != staff.phone:
        existing = db.query(Staff).filter(Staff.phone == payload.phone, Staff.id != staff_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Phone already exists")
    
    # Check if email is being changed and if new email already exists
    if payload.email and payload.email != staff.email:
        existing = db.query(Staff).filter(Staff.email == payload.email, Staff.id != staff_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    staff.full_name = payload.full_name if payload.full_name else staff.full_name
    staff.phone = payload.phone if payload.phone else staff.phone
    staff.email = payload.email if payload.email else staff.email
    staff.role = payload.role if payload.role else staff.role
    staff.is_active = payload.is_active if payload.is_active else staff.is_active
    
    # Only update password if provided
    if payload.password:
        staff.password_hash = get_password_hash(payload.password)
    
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


@router.delete("/{staff_id}")
def delete_staff(staff_id: str, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.SUPER_ADMIN))):
    staff = db.get(Staff, staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Soft delete by setting is_active to False
    staff.is_active = False
    db.add(staff)
    db.commit()
    
    return {"status": "deleted", "message": f"Staff {staff.full_name} has been deactivated"}
