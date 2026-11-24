"""Stripe Checkout. Without STRIPE_SECRET_KEY, orders wait for the shop to mark them paid."""

from __future__ import annotations

from .config import Settings
from .models import Customer, Order


class PaymentError(RuntimeError):
    pass


def ensure_stripe_customer(customer: Customer, settings: Settings) -> str:
    """The Stripe customer for a Pyslate account, created the first time it is needed.

    The caller commits, so the new id is kept on the account.
    """
    import stripe

    stripe.api_key = settings.stripe_secret_key
    if not customer.stripe_customer_id:
        try:
            sc = stripe.Customer.create(email=customer.email, name=customer.name or None,
                                        metadata={"pyslate_customer": customer.id})
        except stripe.StripeError as exc:
            raise PaymentError(str(exc)) from exc
        customer.stripe_customer_id = sc.id
    return customer.stripe_customer_id


def billing_portal(customer: Customer, settings: Settings) -> str:
    """A Stripe customer portal link where the customer adds, removes or changes saved cards."""
    import stripe

    sc = ensure_stripe_customer(customer, settings)
    try:
        session = stripe.billing_portal.Session.create(customer=sc, return_url=f"{settings.public_url}/account/settings")
    except stripe.StripeError as exc:
        raise PaymentError(str(exc)) from exc
    return session.url


def create_checkout(order: Order, settings: Settings, customer: Customer | None = None) -> str:
    """Start a Stripe Checkout session and return the URL to send the customer to.

    For a signed-in customer the session uses their Stripe customer, so saved cards are
    offered and a new card can be kept for next time.
    """
    import stripe

    stripe.api_key = settings.stripe_secret_key
    order_url = f"{settings.public_url}/order/{order.number}?t={order.access_token}"
    who: dict = {"customer_email": order.email}
    if customer is not None:
        who = {"customer": ensure_stripe_customer(customer, settings),
               "payment_intent_data": {"setup_future_usage": "on_session"},
               "saved_payment_method_options": {"payment_method_save": "enabled"}}
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            **who,
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
