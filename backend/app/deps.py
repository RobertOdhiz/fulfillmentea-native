from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Staff, StaffRole
from .utils.security import decode_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_staff(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Staff:
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    staff_id_str = payload.get("sub")
    
    # Since the Staff model uses String(36) for UUID, we can query directly with the string
    staff = db.query(Staff).filter(Staff.id == staff_id_str).first()
    
    if not staff:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff not found")
    
    if not staff.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    
    return staff


def require_roles(*roles: StaffRole):
    def _checker(current: Staff = Depends(get_current_staff)) -> Staff:
        if roles and current.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current

    return _checker
