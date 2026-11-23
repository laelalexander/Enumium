"""Stripe Checkout. Without STRIPE_SECRET_KEY, orders wait for the shop to mark them paid."""

from __future__ import annotations

from .config import Settings
from .models import Order


class PaymentError(RuntimeError):
    pass


def create_checkout(order: Order, settings: Settings) -> str:
    """Start a Stripe Checkout session and return the URL to send the customer to."""
    import stripe

    stripe.api_key = settings.stripe_secret_key
    order_url = f"{settings.public_url}/order/{order.number}?t={order.access_token}"
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            customer_email=order.email,
            line_items=[
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": order.total_cents,
                        "product_data": {"name": f"Pyslate order #{order.number}"},
                    },
                }
            ],
            metadata={"order_id": order.id},
            success_url=order_url + "&paid=1",
            cancel_url=order_url,
        )
    except stripe.StripeError as exc:
        raise PaymentError(str(exc)) from exc
    order.stripe_session_id = session.id
    return session.url


def parse_webhook(payload: bytes, signature: str, settings: Settings) -> tuple[str, str | None]:
    """Verify a Stripe webhook. Returns (event type, order id or None)."""
    import stripe

    if not settings.stripe_webhook_secret:
        raise PaymentError("STRIPE_WEBHOOK_SECRET is not set")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise PaymentError("Invalid webhook") from exc
    obj = event["data"]["object"]
    order_id = None
    if event["type"] == "checkout.session.completed" and obj.get("payment_status") == "paid":
        order_id = (obj.get("metadata") or {}).get("order_id")
    return event["type"], order_id
