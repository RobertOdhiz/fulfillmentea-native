from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..deps import get_db
from ..models import Parcel, TrackingHistory
from ..schemas import TrackingHistoryOut

router = APIRouter()

@router.get("/", response_model=list[TrackingHistoryOut])
@router.get("", response_model=list[TrackingHistoryOut], include_in_schema=False)
def list_all_tracking_histories(db: Session = Depends(get_db)):
    return db.query(TrackingHistory).all()

@router.get("/parcel/{parcel_id}", response_model=list[TrackingHistoryOut])
def list_tracking_histories_by_parcel_id(parcel_id: str, db: Session = Depends(get_db)):
    return db.query(TrackingHistory).filter(TrackingHistory.parcel_id == parcel_id).all()

@router.get("/track")
def track_parcel(
    sender_phone: Optional[str] = Query(None), 
    receiver_phone: Optional[str] = Query(None),
    tracking_number: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Parcel)

    if sender_phone and receiver_phone:
        parcel = query.filter(and_(Parcel.sender_phone == sender_phone,
                                   Parcel.receiver_phone == receiver_phone)).first()
    elif sender_phone:
        parcel = query.filter(Parcel.sender_phone == sender_phone).first()
    elif receiver_phone:
        parcel = query.filter(Parcel.receiver_phone == receiver_phone).first()
    elif tracking_number:
        parcel = query.filter(Parcel.tracking_number == tracking_number).first()
    else:
        raise HTTPException(status_code=400, detail="At least one phone number or tracking number is required")

    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    history = db.query(TrackingHistory).filter(TrackingHistory.parcel_id == parcel.id).all()
    
    return {"parcel": parcel, "history": history}
