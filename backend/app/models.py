from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Float,
    UniqueConstraint,
    Text,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .db import Base


UUID = String(36)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class StaffRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    SALES_AGENT = "SALES_AGENT"
    RECEIVING = "RECEIVING"
    DISPATCHER = "DISPATCHER"
    DELIVERY = "DELIVERY"


class Staff(Base, TimestampMixin):
    __tablename__ = "staff"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, index=True, default=lambda: str(uuid4()))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[StaffRole] = mapped_column(SAEnum(StaffRole), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    received_parcels = relationship("Parcel", back_populates="received_by", foreign_keys="Parcel.received_by_id")
    assignments_made = relationship("Assignment", back_populates="assigned_by_staff", foreign_keys="Assignment.assigned_by_staff_id")
    refunds_approved = relationship("Refund", back_populates="approved_by_staff", foreign_keys="Refund.approved_by_staff_id")


class Rider(Base, TimestampMixin):
    __tablename__ = "riders"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, index=True, default=lambda: str(uuid4()))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    vehicle_details: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    assignments = relationship("Assignment", back_populates="rider")
    delivery_attempts = relationship("DeliveryAttempt", back_populates="rider")


class ParcelStatus(str, Enum):
    RECEIVED = "RECEIVED"
    DISPATCHED = "DISPATCHED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"


class DeliveryOutcome(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class ParcelStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED_AT_HUB = "ARRIVED_AT_HUB"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERY_ATTEMPTED = "DELIVERY_ATTEMPTED"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"

class Parcel(Base, TimestampMixin):
    __tablename__ = "parcels"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, index=True, default=lambda: str(uuid4()))
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    sender_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_country_code: Mapped[Optional[str]] = mapped_column(String(8))

    receiver_name: Mapped[str] = mapped_column(String(255), nullable=False)
    receiver_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    receiver_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    receiver_country_code: Mapped[Optional[str]] = mapped_column(String(8))

    parcel_type: Mapped[str] = mapped_column(String(64), nullable=False)

    value_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    value_currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")

    amount_paid_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    amount_paid_currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")

    special_instructions: Mapped[Optional[str]] = mapped_column(Text)

    received_by_id: Mapped[str] = mapped_column(UUID, ForeignKey("staff.id", ondelete="RESTRICT"), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    dispatched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    current_status: Mapped[ParcelStatus] = mapped_column(SAEnum(ParcelStatus), default=ParcelStatus.RECEIVED, nullable=False)
    delivery_outcome: Mapped[DeliveryOutcome] = mapped_column(SAEnum(DeliveryOutcome), default=DeliveryOutcome.PENDING, nullable=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)

    received_by = relationship("Staff", back_populates="received_parcels", foreign_keys=[received_by_id])
    photos = relationship("ParcelPhoto", back_populates="parcel", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="parcel", cascade="all, delete-orphan")
    otps = relationship("OTP", back_populates="parcel", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="parcel", cascade="all, delete-orphan")
    receipt = relationship("Receipt", back_populates="parcel", uselist=False, cascade="all, delete-orphan")
    disputes = relationship("Dispute", back_populates="parcel", cascade="all, delete-orphan")
    delivery_attempts = relationship("DeliveryAttempt", back_populates="parcel", cascade="all, delete-orphan")

    tracking_history = relationship("TrackingHistory", 
                                  back_populates="parcel", 
                                  cascade="all, delete-orphan",
                                  order_by="TrackingHistory.created_at")

class TrackingHistory(Base, TimestampMixin):
    __tablename__ = "tracking_history"
    
    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=lambda: str(uuid4()))
    parcel_id: Mapped[str] = mapped_column(UUID, ForeignKey("parcels.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[ParcelStatus] = mapped_column(SAEnum(ParcelStatus), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    updated_by_staff_id: Mapped[Optional[str]] = mapped_column(UUID, ForeignKey("staff.id", ondelete="SET NULL"), nullable=True)
    rider_id: Mapped[Optional[str]] = mapped_column(UUID, ForeignKey("riders.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    parcel = relationship("Parcel", back_populates="tracking_history")
    updated_by_staff = relationship("Staff", foreign_keys=[updated_by_staff_id])
    rider = relationship("Rider", foreign_keys=[rider_id])
    
    # Index for better query performance
    __table_args__ = (
        Index('ix_tracking_history_parcel_status', 'parcel_id', 'status'),
        Index('ix_tracking_history_timestamp', 'created_at'),
    )


class PhotoType(str, Enum):
    RECEIVED = "RECEIVED"
    DELIVERED = "DELIVERED"


class ParcelPhoto(Base, TimestampMixin):
    __tablename__ = "parcel_photos"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=lambda: str(uuid4()))
    parcel_id: Mapped[str] = mapped_column(UUID, ForeignKey("parcels.id", ondelete="CASCADE"), index=True)
    type: Mapped[PhotoType] = mapped_column(SAEnum(PhotoType), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

    parcel = relationship("Parcel", back_populates="photos")


class OTP(Base, TimestampMixin):
    __tablename__ = "otps"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=lambda: str(uuid4()))
    parcel_id: Mapped[str] = mapped_column(UUID, ForeignKey("parcels.id", ondelete="CASCADE"), index=True)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    parcel = relationship("Parcel", back_populates="otps")


class Assignment(Base, TimestampMixin):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=lambda: str(uuid4()))
    parcel_id: Mapped[str] = mapped_column(UUID, ForeignKey("parcels.id", ondelete="CASCADE"), index=True)
    rider_id: Mapped[str] = mapped_column(UUID, ForeignKey("riders.id", ondelete="RESTRICT"), index=True)
    assigned_by_staff_id: Mapped[str] = mapped_column(UUID, ForeignKey("staff.id", ondelete="RESTRICT"), index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    parcel = relationship("Parcel", back_populates="assignments")
    rider = relationship("Rider", back_populates="assignments")
    assigned_by_staff = relationship("Staff", back_populates="assignments_made")


class DeliveryAttemptStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class DeliveryAttempt(Base, TimestampMixin):
    __tablename__ = "delivery_attempts"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=lambda: str(uuid4()))
    parcel_id: Mapped[str] = mapped_column(UUID, ForeignKey("parcels.id", ondelete="CASCADE"), index=True)
    rider_id: Mapped[Optional[str]] = mapped_column(UUID, ForeignKey("riders.id", ondelete="SET NULL"), index=True, nullable=True)
    status: Mapped[DeliveryAttemptStatus] = mapped_column(SAEnum(DeliveryAttemptStatus), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    parcel = relationship("Parcel", back_populates="delivery_attempts")
    rider = relationship("Rider", back_populates="delivery_attempts")


class PaymentMethod(str, Enum):
    CASH = "CASH"
    CARD = "CARD"
    MOBILE_MONEY = "MOBILE_MONEY"
    BANK_TRANSFER = "BANK_TRANSFER"


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=lambda: str(uuid4()))
    parcel_id: Mapped[str] = mapped_column(UUID, ForeignKey("parcels.id", ondelete="CASCADE"), index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    method: Mapped[PaymentMethod] = mapped_column(SAEnum(PaymentMethod), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(255))

    parcel = relationship("Parcel", back_populates="payments")


class Receipt(Base, TimestampMixin):
    __tablename__ = "receipts"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=lambda: str(uuid4()))
    parcel_id: Mapped[str] = mapped_column(UUID, ForeignKey("parcels.id", ondelete="CASCADE"), unique=True, index=True)
    receipt_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    printed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    parcel = relationship("Parcel", back_populates="receipt")


class DisputeStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    REFUNDED = "REFUNDED"


class RaisedBy(str, Enum):
    SENDER = "SENDER"
    RECEIVER = "RECEIVER"
    STAFF = "STAFF"


class Dispute(Base, TimestampMixin):
    __tablename__ = "disputes"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=lambda: str(uuid4()))
    parcel_id: Mapped[str] = mapped_column(UUID, ForeignKey("parcels.id", ondelete="CASCADE"), index=True)
    raised_by: Mapped[RaisedBy] = mapped_column(SAEnum(RaisedBy), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[DisputeStatus] = mapped_column(SAEnum(DisputeStatus), default=DisputeStatus.OPEN, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    parcel = relationship("Parcel", back_populates="disputes")
    refund = relationship("Refund", back_populates="dispute", uselist=False)


class Refund(Base, TimestampMixin):
    __tablename__ = "refunds"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=lambda: str(uuid4()))
    dispute_id: Mapped[str] = mapped_column(UUID, ForeignKey("disputes.id", ondelete="CASCADE"), unique=True, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    approved_by_staff_id: Mapped[str] = mapped_column(UUID, ForeignKey("staff.id", ondelete="RESTRICT"), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    dispute = relationship("Dispute", back_populates="refund")
    approved_by_staff = relationship("Staff", back_populates="refunds_approved")


class InventoryItem(Base, TimestampMixin):
    __tablename__ = "inventory_items"

    id: Mapped[str] = mapped_column(UUID, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sku: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="unit", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
