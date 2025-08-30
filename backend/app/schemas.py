from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict

from .models import StaffRole, PaymentMethod, ParcelStatus, PhotoType, DisputeStatus, RaisedBy, DeliveryOutcome, DeliveryAttemptStatus


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Auth / Staff
class StaffBase(ORMModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    role: StaffRole
    is_active: bool = True


class StaffCreate(BaseModel):
    full_name: str
    phone: str
    email: Optional[str] = None
    role: StaffRole
    password: str

class StaffUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[StaffRole] = None
    is_active: Optional[bool] = None


class StaffOut(StaffBase):
    id: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    phone: str
    password: str


# Riders
class RiderBase(ORMModel):
    full_name: str
    phone: str
    vehicle_details: Optional[str] = None
    is_active: bool = True


class RiderCreate(BaseModel):
    full_name: str
    phone: str
    vehicle_details: Optional[str] = None


class RiderOut(RiderBase):
    id: str


# Parcels
class Money(BaseModel):
    amount: float = Field(ge=0)
    currency: str = "USD"


class ParcelCreate(BaseModel):
    sender_name: str
    sender_phone: str
    sender_country_code: Optional[str] = None
    sender_location: Optional[str] = None
    receiver_name: str
    receiver_phone: str
    receiver_country_code: Optional[str] = None
    receiver_location: Optional[str] = None
    parcel_type: str
    value: Money
    amount_paid: Money
    special_instructions: Optional[str] = None


class ParcelOut(ORMModel):
    id: str
    sender_name: str
    sender_phone: str
    sender_country_code: Optional[str]
    sender_location: Optional[str]
    receiver_name: str
    receiver_phone: str
    receiver_country_code: Optional[str]
    receiver_location: Optional[str]
    parcel_type: str
    value_amount: float
    value_currency: str
    amount_paid_amount: float
    amount_paid_currency: str
    special_instructions: Optional[str]
    received_by_id: str
    received_at: datetime
    dispatched: bool
    dispatched_at: Optional[datetime]
    delivered: bool
    delivered_at: Optional[datetime]
    current_status: ParcelStatus
    delivery_outcome: DeliveryOutcome
    failure_reason: Optional[str]


class AssignmentCreate(BaseModel):
    rider_id: str


class AssignmentOut(ORMModel):
    id: str
    parcel_id: str
    rider_id: str
    assigned_by_staff_id: str
    assigned_at: datetime


class OTPVerifyRequest(BaseModel):
    code: str


class PhotoOut(ORMModel):
    id: str
    parcel_id: str
    type: PhotoType
    file_path: str


# Delivery attempts
class DeliveryAttemptCreate(BaseModel):
    status: DeliveryAttemptStatus
    note: Optional[str] = None
    rider_id: Optional[str] = None


class DeliveryAttemptOut(ORMModel):
    id: str
    parcel_id: str
    rider_id: Optional[str]
    status: DeliveryAttemptStatus
    note: Optional[str]
    attempted_at: datetime


# Payments / Receipts
class PaymentCreate(BaseModel):
    amount: float
    currency: str = "USD"
    method: PaymentMethod
    reference: Optional[str] = None


class PaymentOut(ORMModel):
    id: str
    parcel_id: str
    amount: float
    currency: str
    method: PaymentMethod
    paid_at: datetime
    reference: Optional[str]


class ReceiptOut(ORMModel):
    id: str
    parcel_id: str
    receipt_number: str
    total_amount: float
    currency: str
    generated_at: datetime
    printed: bool


# Disputes / Refunds
class DisputeCreate(BaseModel):
    raised_by: RaisedBy
    reason: str


class DisputeOut(ORMModel):
    id: str
    parcel_id: str
    raised_by: RaisedBy
    reason: str
    status: DisputeStatus


class RefundCreate(BaseModel):
    dispute_id: str
    amount: float
    currency: str = "USD"


class RefundOut(ORMModel):
    id: str
    dispute_id: str
    amount: float
    currency: str
    processed_at: datetime


# Inventory
class InventoryItemCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    quantity: float = 0
    unit: str = "unit"


class InventoryItemOut(ORMModel):
    id: str
    name: str
    sku: Optional[str]
    quantity: float
    unit: str
    is_active: bool

class ParcelUpdate(BaseModel):
    sender_name: Optional[str] = None
    sender_phone: Optional[str] = None
    sender_country_code: Optional[str] = None
    sender_location: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_country_code: Optional[str] = None
    receiver_location: Optional[str] = None
    parcel_type: Optional[str] = None
    value: Optional[Money] = None
    amount_paid: Optional[Money] = None
    special_instructions: Optional[str] = None

class TrackingHistoryCreate(BaseModel):
    status: ParcelStatus
    location: str
    notes: Optional[str] = None

class TrackingHistoryOut(ORMModel):
    id: str
    parcel_id: str
    status: ParcelStatus
    location: str
    notes: Optional[str]
    updated_by_staff_id: Optional[str]
    rider_id: Optional[str]
    created_at: datetime

class TrackingHistoryUpdate(BaseModel):
    status: Optional[ParcelStatus] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    updated_by_staff_id: Optional[str] = None
    rider_id: Optional[str] = None
    