import json
import logging
import uuid
from typing import Dict, List, Optional, Union
import requests
from requests.exceptions import RequestException

from ..core.config import settings

logger = logging.getLogger(__name__)
# Optionally configure logger in your app's startup if not already configured:
# logging.basicConfig(level=logging.DEBUG)


class BlkSMSService:
    """
    SMS service client for FastHub / BulkSMS provider.
    """

    def __init__(self):
        base = (settings.blksms_base_url or "").strip()
        # remove trailing slash if present for consistent concatenation
        self.base_url = base[:-1] if base.endswith("/") else base

        self.client_id = settings.blksms_client_id
        self.client_secret = settings.blksms_client_secret
        self.sender_id = settings.blksms_sender_id  # must be approved on provider
        self.enabled = bool(settings.blksms_enabled)

        if not self.enabled:
            logger.warning("BlkSMS service is DISABLED by configuration.")

        logger.debug("BlkSMS config loaded: base_url=%s, client_id_configured=%s, sender_id=%s",
                     self.base_url, bool(self.client_id), self.sender_id)

    # ---------------- Helpers ----------------

    @staticmethod
    def _to_e164(phone: str) -> str:
        """
        Normalize phone number to E.164 style with leading '+'.
        Removes spaces and dashes only; preserves + if present.
        """
        if phone is None:
            return ""
        p = str(phone).strip().replace(" ", "").replace("-", "")
        if not p:
            return ""
        if not p.startswith("+") and p[0].isdigit():
            p = f"+{p}"
        return p

    @staticmethod
    def _ensure_reference(reference: Optional[str]) -> str:
        """
        Ensure reference has at least 20 characters. Use hex uuid (32 chars) by default.
        """
        if not reference:
            return uuid.uuid4().hex  # 32 hex chars without hyphens
        reference = str(reference)
        if len(reference) >= 20:
            print(f'Reference Length: {len(reference)}')
            return reference
        # pad/truncate so result length >= 20
        pad = uuid.uuid4().hex
        new_ref = (reference + pad)[:max(20, len(reference))]
        if len(new_ref) < 20:
            new_ref = new_ref + pad[: (20 - len(new_ref))]
        return new_ref

    def _headers(self) -> Dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _auth_body(self) -> Dict[str, str]:
        return {
            "clientId": self.client_id,
            "clientSecret": self.client_secret,
        }

    def _make_request(self, endpoint: str, payload: Dict, method: str = "POST") -> Optional[Dict]:
        """
        Make HTTP request with error handling.
        - POST sends JSON body.
        - GET sends query params.
        """
        if not self.enabled:
            logger.warning("SMS service disabled; skipping request to %s", endpoint)
            return None

        if not self.client_id or not self.client_secret:
            logger.error("BlkSMS credentials not configured.")
            return None

        url = f"{self.base_url}{endpoint}"
        try:
            logger.info("HTTP %s -> %s", method.upper(), url)
            logger.debug("Request payload:\n%s", json.dumps(payload, indent=2))

            if method.upper() == "POST":
                resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
            else:
                resp = requests.get(url, params=payload, headers=self._headers(), timeout=30)

            logger.info("API Response Status: %s", resp.status_code)
            logger.debug("API Response Headers: %s", dict(resp.headers))
            logger.debug("API Response Text: %s", resp.text)

            # Raise for 400/500 etc so we can capture response in exception handler
            resp.raise_for_status()

            # parse json
            try:
                return resp.json()
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from response at %s", url)
                return None

        except RequestException as e:
            # Provide as much context as possible
            logger.error("HTTP request failed for %s: %s", endpoint, str(e))
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    logger.error("Error response status: %s", resp.status_code)
                    logger.error("Error response headers: %s", dict(resp.headers))
                    logger.error("Error response text: %s", resp.text)
                except Exception:
                    logger.exception("Failed to log response details")
            return None
        except Exception as e:
            logger.exception("Unexpected error in _make_request for %s: %s", endpoint, str(e))
            return None

    # ---------------- Public API ----------------

    def send_single_sms(self, phone: str, message: str, reference: Optional[str] = None) -> bool:
        """
        Send a single SMS message.
        Returns True on success, False otherwise.
        """
        if not self.enabled:
            logger.info("[SMS DISABLED] Would send to %s: %s", phone, message)
            return False

        ref = self._ensure_reference(reference)
        msisdn = self._to_e164(phone)

        if not msisdn:
            logger.error("Invalid phone number provided: %s", phone)
            return False

        payload = {
            "auth": self._auth_body(),
            "messages": [
                {
                    "text": message,
                    "msisdn": msisdn,
                    "source": self.sender_id,
                    "reference": ref,
                    "coding": "GSM7"
                }
            ]
        }

        res = self._make_request("/api/sms/send", payload, method="POST")

        # Interpret gateway response - providers vary
        if isinstance(res, dict):
            # provider returns {"status": false/true, ...}
            status = res.get("status")
            if status in (True, "true", "success", "ok", "OK", "SUCCESS"):
                logger.info("SMS sent successfully to %s (reference=%s)", msisdn, ref)
                return True

            # some providers return 'results' per message
            results = res.get("results") or res.get("data") or None
            if isinstance(results, list):
                # treat success if any item indicates success
                for r in results:
                    if isinstance(r, dict) and r.get("status") in (True, "true", "success", "ok", 200):
                        logger.info("SMS partial success to %s (reference=%s) result=%s", msisdn, ref, r)
                        return True

        # if we reach here, it failed
        logger.error("Failed to send SMS to %s. Gateway response: %s", msisdn, res)
        return False

    def send_bulk_sms(self, messages: List[Dict[str, str]]) -> Dict[str, Union[int, List[int]]]:
        """
        Send bulk SMS messages.
        messages: list of {"phone": "...", "message": "..."}
        Returns: {"success": n, "failed": m, "failed_indices": [i, ...]}
        """
        if not self.enabled:
            logger.info("[BULK SMS DISABLED] -> %d messages", len(messages))
            return {"success": 0, "failed": len(messages), "failed_indices": list(range(len(messages)))}

        # FastHub limit example: 50 per request. If larger, truncate and warn.
        max_batch = 50
        if len(messages) > max_batch:
            logger.warning("Bulk request length %d exceeds %d; truncating to first %d", len(messages), max_batch, max_batch)
            messages = messages[:max_batch]

        sms_messages = []
        for msg in messages:
            msg_phone = msg.get("phone")
            msg_text = msg.get("message", "")
            ref = self._ensure_reference(msg.get("reference"))
            msisdn = self._to_e164(msg_phone)
            if not msisdn:
                # append an invalid placeholder; we'll count it as failure
                sms_messages.append({"invalid": True, "original": msg})
                continue

            sms_messages.append({
                "text": msg_text,
                "msisdn": msisdn,
                "source": self.sender_id,
                "reference": ref,
                "coding": "GSM7"
            })

        # Remove invalid placeholders for payload and track indices
        valid_payload_messages = [m for m in sms_messages if "invalid" not in m]
        failed_indices = [i for i, m in enumerate(sms_messages) if "invalid" in m]
        payload = {
            "auth": self._auth_body(),
            "messages": valid_payload_messages
        }

        res = self._make_request("/api/sms/send", payload, method="POST")

        success_count = 0
        if isinstance(res, dict):
            if res.get("status") in (True, "true", "success", "ok", "OK", "SUCCESS"):
                # assume all valid payload messages succeeded
                success_count = len(valid_payload_messages)
            else:
                # try to parse per-message results
                results = res.get("results") or res.get("data") or None
                if isinstance(results, list) and len(results) == len(valid_payload_messages):
                    for i, r in enumerate(results):
                        if isinstance(r, dict) and r.get("status") in (True, "true", "success", "ok", 200):
                            success_count += 1
                        else:
                            failed_indices.append(i)

        failed_count = len(messages) - success_count
        return {"success": success_count, "failed": failed_count, "failed_indices": failed_indices}

    def check_balance(self) -> Optional[Dict[str, Union[str, float, int]]]:
        """
        Check account balance. Attempts a couple common endpoints and normalizes response.
        """
        if not self.enabled:
            logger.warning("SMS service disabled; cannot check balance.")
            return None

        payload = {"auth": self._auth_body()}
        possible_endpoints = ["/api/account/balance", "/api/sms/balance", "/api/balance"]

        last_response = None
        for ep in possible_endpoints:
            res = self._make_request(ep, payload, method="POST")
            last_response = res
            if not isinstance(res, dict):
                continue
            # common shapes
            if res.get("status") in (True, "true", "success", "ok", "OK", "SUCCESS"):
                # direct balance
                if "balance" in res:
                    return {"status": "success", "balance": res.get("balance")}
                # nested data
                data = res.get("data")
                if isinstance(data, dict) and "balance" in data:
                    out = {"status": "success", "balance": data.get("balance")}
                    if data.get("currency"):
                        out["currency"] = data.get("currency")
                    return out

        logger.error("Balance check failed. Last response: %s", last_response)
        return None

    def get_delivery_reports(self, reference_id: str, channel: str = "default") -> Optional[Dict]:
        """
        Fetch delivery reports for a given reference. Endpoint name may vary with provider.
        """
        if not self.enabled:
            logger.warning("SMS service disabled; cannot fetch delivery reports.")
            return None

        payload = {
            "auth": self._auth_body(),
            "channel": channel,
            "reference_id": reference_id
        }
        res = self._make_request("/api/dlr/request/polling/handler", payload, method="POST")
        if res:
            logger.info("Delivery report fetched for %s: %s", reference_id, res)
            return res

        logger.error("Failed to get delivery report for %s", reference_id)
        return None


# --------- Single module instance + wrappers ---------
sms_service = BlkSMSService()


def send_sms(phone: str, message: str, reference: Optional[str] = None) -> bool:
    return sms_service.send_single_sms(phone, message, reference)


def send_bulk_sms(messages: List[Dict[str, str]]) -> Dict[str, Union[int, List[int]]]:
    return sms_service.send_bulk_sms(messages)


def check_sms_balance() -> Optional[Dict[str, Union[str, float, int]]]:
    return sms_service.check_balance()


def get_sms_delivery_report(reference_id: str, channel: str = "default") -> Optional[Dict]:
    return sms_service.get_delivery_reports(reference_id, channel)

def poll_sms_status(reference_id: str, channel: str = "default") -> Optional[Dict]:
    """
    Backwards-compatible wrapper. Some callers (routers) expect `poll_sms_status`.
    Delegates to the sms_service poll_messages implementation.
    """
    # If sms_service has poll_messages method use it; otherwise try get_delivery_reports
    if hasattr(sms_service, "poll_messages"):
        return sms_service.poll_messages(reference_id, channel)
    # fallback to delivery reports endpoint if poll_messages isn't implemented
    return sms_service.get_delivery_reports(reference_id, channel)