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


PAID_EVENTS = ("checkout.session.completed", "checkout.session.async_payment_succeeded")


def as_dict(obj) -> dict:
    """Stripe's objects stopped acting like dicts (no .get); turn them into plain dicts."""
    if isinstance(obj, dict) and type(obj) is dict:
        return obj
    to_dict = getattr(obj, "to_dict", None)
    return to_dict() if callable(to_dict) else dict(obj)


def session_payment(obj) -> dict | None:
    """The order id, amount and currency of a paid Checkout session, or None if it isn't paid yet."""
    obj = as_dict(obj)
    if obj.get("payment_status") != "paid":
        return None
    return {
        "order_id": (obj.get("metadata") or {}).get("order_id"),
        "session_id": obj.get("id"),
        "amount": obj.get("amount_total"),
        "currency": (obj.get("currency") or "").lower(),
    }


def matches(order: Order, paid: dict | None) -> bool:
    """A payment counts only for the right order, session and full amount."""
    return bool(
        paid
        and paid["order_id"] == order.id
        and (not order.stripe_session_id or paid["session_id"] == order.stripe_session_id)
        and paid["amount"] == order.total_cents
        and paid["currency"] == "usd"
    )


def parse_webhook(payload: bytes, signature: str, settings: Settings) -> tuple[str, dict | None]:
    """Verify a Stripe webhook. Returns (event type, the paid session's details or None)."""
    import stripe

    if not settings.stripe_webhook_secret:
        raise PaymentError("STRIPE_WEBHOOK_SECRET is not set")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise PaymentError("Invalid webhook") from exc
    paid = session_payment(event["data"]["object"]) if event["type"] in PAID_EVENTS else None
    return event["type"], paid


def check_session(order: Order, settings: Settings) -> bool:
    """Ask Stripe directly whether the order's Checkout session is paid.

    Used when the customer comes back from Stripe, so the order is confirmed even if
    the webhook is slow or not set up yet.
    """
    import stripe

    if not order.stripe_session_id:
        return False
    stripe.api_key = settings.stripe_secret_key
    try:
        obj = stripe.checkout.Session.retrieve(order.stripe_session_id)
    except stripe.StripeError:
        return False
    return matches(order, session_payment(obj))
