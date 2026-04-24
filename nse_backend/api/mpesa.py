"""
Safaricom Daraja 3.0 — M-Pesa STK Push integration.
Docs: https://developer.safaricom.co.ke/Documentation
"""
import base64
import logging
import os
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

DARAJA_BASE = os.getenv("DARAJA_ENV", "sandbox")
_BASE_URL = (
    "https://sandbox.safaricom.co.ke"
    if DARAJA_BASE == "sandbox"
    else "https://api.safaricom.co.ke"
)
_CONSUMER_KEY = os.getenv("DARAJA_CONSUMER_KEY", "")
_CONSUMER_SECRET = os.getenv("DARAJA_CONSUMER_SECRET", "")
_SHORTCODE = os.getenv("DARAJA_SHORTCODE", "174379")
_PASSKEY = os.getenv("DARAJA_PASSKEY", "")
_CALLBACK_URL = os.getenv("DARAJA_CALLBACK_URL", "")

TIER_PRICES = {
    "pro": 500,
    "club": 3000,
}

TOPUP_PACKAGES = {
    "topup_10": {"requests": 10, "price": 50},
    "topup_25": {"requests": 25, "price": 100},
    "topup_50": {"requests": 50, "price": 200},
}


def _get_token() -> str:
    creds = base64.b64encode(f"{_CONSUMER_KEY}:{_CONSUMER_SECRET}".encode()).decode()
    r = requests.get(
        f"{_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
        headers={"Authorization": f"Basic {creds}"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _password_and_timestamp():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    raw = f"{_SHORTCODE}{_PASSKEY}{ts}"
    pwd = base64.b64encode(raw.encode()).decode()
    return pwd, ts


def stk_push(phone: str, tier: str, user_id: int) -> dict:
    """Initiate STK Push. Returns Daraja response dict."""
    amount = TIER_PRICES.get(tier, 500)
    phone = phone.lstrip("+").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    token = _get_token()
    password, timestamp = _password_and_timestamp()

    payload = {
        "BusinessShortCode": _SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": _SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": _CALLBACK_URL,
        "AccountReference": f"NSEPro-{user_id}",
        "TransactionDesc": f"NSE Pro {tier.capitalize()} subscription",
    }

    r = requests.post(
        f"{_BASE_URL}/mpesa/stkpush/v1/processrequest",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def topup_stk_push(phone: str, price: int, user_id: int) -> dict:
    """Initiate STK Push for a request top-up package."""
    phone = phone.lstrip("+").replace(" ", "")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    token = _get_token()
    password, timestamp = _password_and_timestamp()

    payload = {
        "BusinessShortCode": _SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": price,
        "PartyA": phone,
        "PartyB": _SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": _CALLBACK_URL,
        "AccountReference": f"NSETopUp-{user_id}",
        "TransactionDesc": "NSE Analytics AI request top-up",
    }

    r = requests.post(
        f"{_BASE_URL}/mpesa/stkpush/v1/processrequest",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def verify_stk(checkout_request_id: str) -> dict:
    """Query STK Push status. Returns {'ResultCode': 0} on success."""
    token = _get_token()
    password, timestamp = _password_and_timestamp()

    payload = {
        "BusinessShortCode": _SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }

    r = requests.post(
        f"{_BASE_URL}/mpesa/stkpushquery/v1/query",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    r.raise_for_status()
    return r.json()
