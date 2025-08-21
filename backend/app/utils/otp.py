import secrets
from datetime import datetime, timedelta

from ..core.config import settings
from .security import get_password_hash


def generate_otp_code(length: int = 6) -> str:
    # Numeric OTP
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def hash_otp(code: str) -> str:
    return get_password_hash(code)


def expiry_time() -> datetime:
    # Use naive UTC for DB consistency, add expiry minutes
    return datetime.utcnow() + timedelta(minutes=settings.otp_expiry_minutes)
