from typing import Any, Dict, Optional

import razorpay

from app.core.config import settings


def get_razorpay_client() -> razorpay.Client:
    if (
        not settings.razorpay_key_id
        or not settings.razorpay_key_secret
    ):
        raise RuntimeError(
            "Razorpay credentials are not configured."
        )

    return razorpay.Client(
        auth=(
            settings.razorpay_key_id,
            settings.razorpay_key_secret,
        )
    )


def create_razorpay_order(
    *,
    amount: int,
    receipt: str,
    notes: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    client = get_razorpay_client()

    return client.order.create(
        {
            "amount": amount,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes or {},
        }
    )


def verify_razorpay_payment(
    *,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    expected_amount: int,
    expected_currency: str = "INR",
    expected_receipt: Optional[str] = None,
) -> Dict[str, Any]:
    client = get_razorpay_client()

    client.utility.verify_payment_signature(
        {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }
    )

    order = client.order.fetch(razorpay_order_id)

    if expected_receipt is not None and order.get("receipt") != expected_receipt:
        raise ValueError(
            "Razorpay order does not belong to this invoice."
        )

    payment = client.payment.fetch(razorpay_payment_id)

    if payment.get("order_id") != razorpay_order_id:
        raise ValueError(
            "Razorpay payment does not belong to this order."
        )

    if int(payment.get("amount", 0)) != expected_amount:
        raise ValueError(
            "Razorpay payment amount is invalid."
        )

    if payment.get("currency") != expected_currency:
        raise ValueError(
            "Razorpay payment currency is invalid."
        )

    if payment.get("status") != "captured":
        raise ValueError(
            "Razorpay payment has not been captured."
        )

    return payment
