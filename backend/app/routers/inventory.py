from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..deps import get_db, require_roles
from ..models import InventoryItem, StaffRole
from ..schemas import InventoryItemCreate, InventoryItemOut

router = APIRouter()


@router.get("/", response_model=list[InventoryItemOut])
@router.get("", response_model=list[InventoryItemOut], include_in_schema=False)
def list_items(db: Session = Depends(get_db)):
    return db.query(InventoryItem).filter(InventoryItem.is_active == True).all()


@router.post("/", response_model=InventoryItemOut)
@router.post("", response_model=InventoryItemOut, include_in_schema=False)
def create_item(payload: InventoryItemCreate, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    if payload.sku and db.query(InventoryItem).filter(InventoryItem.sku == payload.sku).first():
        raise HTTPException(status_code=400, detail="SKU already exists")
    item = InventoryItem(name=payload.name, sku=payload.sku, quantity=payload.quantity, unit=payload.unit)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{item_id}/adjust", response_model=InventoryItemOut)
def adjust_item(item_id: str, delta: float, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.quantity += delta
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def deactivate_item(item_id: str, db: Session = Depends(get_db), _=Depends(require_roles(StaffRole.MANAGER, StaffRole.ADMIN, StaffRole.SUPER_ADMIN))):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.is_active = False
    db.add(item)
    db.commit()
    return {"status": "deactivated"}
