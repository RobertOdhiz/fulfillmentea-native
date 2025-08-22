from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db
from ..models import Staff, StaffRole
from ..schemas import LoginRequest, TokenOut, StaffCreate, StaffOut
from ..utils.security import verify_password, create_access_token, get_password_hash

router = APIRouter()


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    staff = db.query(Staff).filter(Staff.phone == payload.phone).first()
    if not staff or not verify_password(payload.password, staff.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not staff.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive")
    
    token = create_access_token(staff.id)
    
    # Return token and user information for role-based access control
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": staff.id,
            "full_name": staff.full_name,
            "phone": staff.phone,
            "role": staff.role,
            "is_active": staff.is_active
        }
    }


@router.post("/bootstrap", response_model=StaffOut)
def bootstrap_admin(payload: StaffCreate, db: Session = Depends(get_db)):
    existing = db.query(Staff).filter(Staff.phone == payload.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    staff = Staff(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        role=payload.role,
        password_hash=get_password_hash(payload.password),
        is_active=True,
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff
