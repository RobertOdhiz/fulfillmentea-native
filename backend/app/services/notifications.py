from typing import Optional, List, Dict
from .sms_service import send_sms as send_sms_service, send_bulk_sms, check_sms_balance


def send_sms(phone: str, message: str, reference: Optional[str] = None) -> bool:
    """
    Send SMS using the configured SMS service
    
    Args:
        phone: Phone number (with country code)
        message: SMS message content
        reference: Optional reference ID for tracking
        
    Returns:
        bool: True if SMS sent successfully, False otherwise
    """
    return send_sms_service(phone, message, reference)


def send_bulk_sms(messages: List[Dict[str, str]]) -> Dict[str, int]:
    """
    Send bulk SMS messages
    
    Args:
        messages: List of message dictionaries with 'phone' and 'message' keys
        
    Returns:
        Dict with success count and failure count
    """
    result = send_bulk_sms(messages)
    return {
        "success": result["success"],
        "failed": result["failed"]
    }


def check_sms_balance() -> Optional[Dict]:
    """Check SMS account balance"""
    return check_sms_balance()


def send_push(user_id: Optional[int], title: str, body: str) -> None:
    # Placeholder for push notifications
    print(f"[PUSH] -> {user_id}: {title} - {body}")
