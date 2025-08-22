#!/usr/bin/env python3
"""
Simple SMS send test (single message) to your FastAPI /sms/send endpoint.

Sends JSON: {"phone": "...", "message": "...", "reference": "..."}
and prints request + response details for debugging.
"""

import json
import uuid
import requests
from datetime import datetime

# === CONFIG ===
BASE_URL = "http://localhost:8000"
SMS_API_URL = f"{BASE_URL}/sms/send"
TEST_PHONE = "+255748415123"   # E.164 with leading +
TIMEOUT = 30

# If your endpoint requires Authorization: set TOKEN or leave None
AUTH_TOKEN = None
# AUTH_TOKEN = "your_jwt_here"

# === helpers ===
def _to_e164(phone: str) -> str:
    p = str(phone or "").strip().replace(" ", "").replace("-", "")
    if not p:
        return ""
    if not p.startswith("+") and p[0].isdigit():
        p = f"+{p}"
    return p

def _ensure_reference(reference: str = None) -> str:
    if not reference:
        return uuid.uuid4().hex  # 32 chars
    reference = str(reference)
    if len(reference) >= 20:
        return reference
    pad = uuid.uuid4().hex
    new_ref = (reference + pad)[:max(20, len(reference))]
    if len(new_ref) < 20:
        new_ref = new_ref + pad[: (20 - len(new_ref))]
    return new_ref

def print_sep(title: str):
    print("\n" + "="*80)
    print(f" {title} ")
    print("="*80 + "\n")

# === main test ===
def test_send_single_sms(phone: str, message: str, reference: str = None):
    print_sep("SINGLE SMS SEND TEST")
    print("Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    msisdn = _to_e164(phone)
    if not msisdn:
        print("❌ Invalid phone. Aborting.")
        return

    ref = _ensure_reference(reference)

    payload = {
        "phone": msisdn,
        "message": message,
        "reference": ref
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

    print("Request URL:", SMS_API_URL)
    print("Request headers:", json.dumps(headers, indent=2))
    print("Request payload:", json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        resp = requests.post(SMS_API_URL, json=payload, headers=headers, timeout=TIMEOUT)
        print_sep("HTTP RESPONSE")
        print("Status Code:", resp.status_code)
        try:
            print("Response Headers:", json.dumps(dict(resp.headers), indent=2))
        except Exception:
            print("Response Headers:", resp.headers)
        print("\nResponse Body:")
        print(resp.text)

        # Try parse JSON
        try:
            parsed = resp.json()
            print("\nParsed JSON:")
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
        except Exception:
            print("\nResponse is not JSON or could not be parsed.")

        # Simple success check (your endpoint returns SMSResponse model with success flag)
        try:
            parsed = resp.json()
            if isinstance(parsed, dict) and parsed.get("success") is True:
                print("\n✅ Backend reported success sending SMS.")
            else:
                print("\n❌ Backend did not report success. Inspect the printed response above.")
        except Exception:
            pass

    except requests.RequestException as e:
        print_sep("HTTP ERROR")
        print("RequestException:", str(e))
        r = getattr(e, "response", None)
        if r is not None:
            print("Response status:", r.status_code)
            try:
                print("Response headers:", json.dumps(dict(r.headers), indent=2))
            except Exception:
                print("Response headers:", r.headers)
            print("Response body:", r.text)
        else:
            print("No response from server.")

if __name__ == "__main__":
    message_text = f"Test SMS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    test_send_single_sms(TEST_PHONE, message_text)
    print_sep("TEST COMPLETE")
