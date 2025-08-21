import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union
import requests
from requests.exceptions import RequestException

from ..core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

class BlkSMSService:
    """Professional SMS service for FastHub TZ BlkSMS integration"""
    
    def __init__(self):
        self.base_url = settings.blksms_base_url
        self.client_id = settings.blksms_client_id
        self.client_secret = settings.blksms_client_secret
        self.sender_id = settings.blksms_sender_id
        self.enabled = settings.blksms_enabled
        
        if not self.enabled:
            logger.warning("BlkSMS service is disabled. Check configuration.")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _get_auth_payload(self) -> Dict[str, str]:
        """Get authentication payload for API requests"""
        return {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }
    
    def _make_request(self, endpoint: str, payload: Dict, method: str = "POST") -> Optional[Dict]:
        """Make HTTP request to BlkSMS API with error handling"""
        if not self.enabled:
            logger.warning("SMS service is disabled. Cannot send SMS.")
            return None
            
        if not self.client_id or not self.client_secret:
            logger.error("BlkSMS credentials not configured")
            return None
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "POST":
                response = requests.post(
                    url,
                    json=payload,
                    headers=self._get_auth_headers(),
                    timeout=30
                )
            else:
                response = requests.get(
                    url,
                    params=payload,
                    headers=self._get_auth_headers(),
                    timeout=30
                )
            
            response.raise_for_status()
            return response.json()
            
        except RequestException as e:
            logger.error(f"HTTP request failed for {endpoint}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response from {endpoint}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in SMS service: {str(e)}")
            return None
    
    def send_single_sms(self, phone: str, message: str, reference: Optional[str] = None) -> bool:
        """
        Send a single SMS message
        
        Args:
            phone: Phone number (with country code)
            message: SMS message content
            reference: Optional reference ID for tracking
            
        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info(f"[SMS DISABLED] -> {phone}: {message}")
            return False
        
        # Generate reference if not provided
        if not reference:
            reference = f"msg_{uuid.uuid4().hex[:8]}"
        
        # Prepare payload
        payload = {
            "auth": self._get_auth_payload(),
            "messages": [
                {
                    "text": message,
                    "msisdn": phone,
                    "source": self.sender_id,
                    "reference": reference,
                    "coding": "GSM7"
                }
            ]
        }
        
        # Send SMS
        response = self._make_request("/api/sms/send", payload)
        
        if response and response.get("status"):
            logger.info(f"SMS sent successfully to {phone}. Reference: {reference}")
            logger.info(f"Response: {response}")
            return True
        else:
            logger.error(f"Failed to send SMS to {phone}. Response: {response}")
            return False
    
    def send_bulk_sms(self, messages: List[Dict[str, str]]) -> Dict[str, Union[int, List[str]]]:
        """
        Send bulk SMS messages
        
        Args:
            messages: List of message dictionaries with 'phone' and 'message' keys
            
        Returns:
            Dict with success count, failure count, and failed numbers
        """
        if not self.enabled:
            logger.info(f"[BULK SMS DISABLED] -> {len(messages)} messages")
            return {"success": 0, "failed": len(messages), "failed_numbers": []}
        
        # Prepare bulk payload
        sms_messages = []
        for msg in messages:
            reference = f"bulk_{uuid.uuid4().hex[:8]}"
            sms_messages.append({
                "text": msg["message"],
                "msisdn": msg["phone"],
                "source": self.sender_id,
                "reference": reference,
                "coding": "GSM7"
            })
        
        payload = {
            "auth": self._get_auth_payload(),
            "messages": sms_messages
        }
        
        # Send bulk SMS
        response = self._make_request("/api/sms/send", payload)
        
        if response and response.get("status"):
            logger.info(f"Bulk SMS sent successfully. Total: {len(messages)}")
            return {"success": len(messages), "failed": 0, "failed_numbers": []}
        else:
            logger.error(f"Failed to send bulk SMS. Response: {response}")
            return {"success": 0, "failed": len(messages), "failed_numbers": [msg["phone"] for msg in messages]}
    
    def check_balance(self) -> Optional[Dict]:
        """Check account balance"""
        payload = {
            "auth": self._get_auth_payload()
        }
        
        response = self._make_request("/api/account/balance", payload)
        
        if response and response.get("status"):
            balance = response.get("balance", 0)
            logger.info(f"Account balance: {balance}")
            return {"balance": balance, "status": "success"}
        else:
            logger.error(f"Failed to check balance. Response: {response}")
            return None
    
    def get_delivery_reports(self, reference_id: str, channel: str = "default") -> Optional[Dict]:
        """Get delivery reports for a specific message"""
        payload = {
            "channel": channel,
            "reference_id": reference_id
        }
        
        response = self._make_request("/api/dlr/request/polling/handler", payload)
        
        if response:
            logger.info(f"Delivery report retrieved for {reference_id}: {response}")
            return response
        else:
            logger.error(f"Failed to get delivery report for {reference_id}")
            return None
    
    def poll_messages(self, reference_id: str, channel: str = "default") -> Optional[Dict]:
        """Poll for message status updates"""
        payload = {
            "channel": channel,
            "reference_id": reference_id
        }
        
        response = self._make_request("/api/sms/poll", payload)
        
        if response:
            logger.info(f"Message poll successful for {reference_id}: {response}")
            return response
        else:
            logger.error(f"Failed to poll messages for {reference_id}")
            return None

# Global SMS service instance
sms_service = BlkSMSService()

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
    return sms_service.send_single_sms(phone, message, reference)

def send_bulk_sms(messages: List[Dict[str, str]]) -> Dict[str, Union[int, List[str]]]:
    """
    Send bulk SMS messages
    
    Args:
        messages: List of message dictionaries with 'phone' and 'message' keys
        
    Returns:
        Dict with success count, failure count, and failed numbers
    """
    return sms_service.send_bulk_sms(messages)

def check_sms_balance() -> Optional[Dict]:
    """Check SMS account balance"""
    return sms_service.check_balance()
