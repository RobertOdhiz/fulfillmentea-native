from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
from ..services.sms_service import sms_service, get_sms_delivery_report, poll_sms_status
from ..deps import require_roles, StaffRole
import uuid

router = APIRouter()

class SMSRequest(BaseModel):
    phone: str
    message: str
    reference: Optional[str] = None

class BulkSMSRequest(BaseModel):
    messages: List[SMSRequest]

class SMSResponse(BaseModel):
    success: bool
    message: str
    reference: Optional[str] = None
    error: Optional[str] = None

@router.get("/balance")
async def check_sms_balance():
    """Check SMS balance"""
    try:
        balance = sms_service.check_balance()
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check balance: {str(e)}")

@router.post("/send", response_model=SMSResponse)
async def send_single_sms(request: SMSRequest):
    """Send a single SMS"""
    try:
        ref = request.reference if request.reference else uuid.uuid4().hex
        success = sms_service.send_single_sms(
            phone=request.phone,
            message=request.message,
            reference=ref
        )
        
        if success:
            return SMSResponse(
                success=True,
                message="SMS sent successfully",
                reference=ref
            )
        else:
            return SMSResponse(
                success=False,
                message="Failed to send SMS",
                error="SMS service returned failure"
            )
            
    except Exception as e:
        return SMSResponse(
            success=False,
            message="Error sending SMS",
            error=str(e)
        )

@router.post("/bulk", response_model=Dict[str, int])
async def send_bulk_sms(request: BulkSMSRequest):
    """Send bulk SMS messages"""
    try:
        # Convert to the format expected by the service
        messages = [
            {
                "phone": msg.phone,
                "message": msg.message
            }
            for msg in request.messages
        ]
        
        result = sms_service.send_bulk_sms(messages)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send bulk SMS: {str(e)}")

@router.get("/reports/{reference_id}")
async def get_delivery_reports(reference_id: str):
    """Get SMS delivery reports"""
    try:
        reports = get_sms_delivery_report(reference_id)
        return reports
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get delivery reports: {str(e)}")

@router.get("/poll/{reference_id}")
async def poll_messages(reference_id: str):
    """Poll for incoming messages"""
    try:
        messages = poll_sms_status(reference_id)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to poll messages: {str(e)}")

@router.post("/test")
async def test_sms_service():
    """Test SMS service connectivity"""
    try:
        # Test with a simple balance check
        balance = sms_service.check_balance()
        
        # Get service configuration info
        config_info = {
            "enabled": sms_service.enabled,
            "base_url": sms_service.base_url,
            "client_id_configured": bool(sms_service.client_id),
            "client_secret_configured": bool(sms_service.client_secret),
            "sender_id": sms_service.sender_id
        }
        
        return {
            "status": "success",
            "message": "SMS service is working",
            "balance": balance,
            "configuration": config_info
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "SMS service test failed",
            "error": str(e)
        }