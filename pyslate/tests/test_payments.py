"""Card payments through Stripe, with the Stripe library replaced by a fake."""

import re
import sys
import types

import pytest
from fastapi.testclient import TestClient

from pyslate.app import create_app
from pyslate.config import Settings
from pyslate.models import Order
from tests.test_app import quote_token, upload


class FakeStripe:
    def __init__(self):
        self.api_key = None
        self.sessions = {}
        self.StripeError = type("StripeError", (Exception,), {})
        self.SignatureVerificationError = type("SignatureVerificationError", (Exception,), {})
        fake = self

        class _Session:
            @staticmethod
            def create(**kw):
                sid = f"cs_test_{len(fake.sessions) + 1}"
                fake.sessions[sid] = {"id": sid, "kw": kw, "payment_status": "unpaid", "currency": "usd",
                                      "amount_total": kw["line_items"][0]["price_data"]["unit_amount"],
                                      "metadata": kw["metadata"]}
                return types.SimpleNamespace(id=sid, url=f"https://checkout.stripe.test/{sid}")

            @staticmethod
            def retrieve(sid):
                return fake.sessions[sid]

        self.checkout = types.SimpleNamespace(Session=_Session)
        self.event = None

        class _Webhook:
            @staticmethod
            def construct_event(payload, sig, secret):
                if sig != "good":
                    raise fake.SignatureVerificationError("bad")
                return fake.event

        self.Webhook = _Webhook


@pytest.fixture
def stripe(monkeypatch):
    fake = FakeStripe()
    monkeypatch.setitem(sys.modules, "stripe", fake)
    return fake


@pytest.fixture
def app(tmp_path, stripe):
    cfg = Settings(data_dir=tmp_path / "data", admin_token="shop-secret", secret_key="k" * 32)
    cfg.stripe_secret_key, cfg.stripe_webhook_secret = "sk_test_x", "whsec_x"
    return create_app(cfg)


def place(client, path):
    token = quote_token(upload(client, path))
    r = client.post(f"/quote/{token}/checkout", data={"email": "a@b.co", "name": "A", "address": "1 St"},
                    follow_redirects=False)
    return r


def order_of(app, number):
    with app.state.session_factory() as db:
        o = db.query(Order).filter_by(number=number).one()
        return o.id, o.status, o.total_cents, o.access_token


def test_checkout_redirects_to_stripe_and_return_confirms(app, stripe, cube_stl):
    c = TestClient(app)
    r = place(c, cube_stl)
    assert r.headers["location"].startswith("https://checkout.stripe.test/cs_test_1")
    kw = stripe.sessions["cs_test_1"]["kw"]
    number = int(re.search(r"/order/(\d+)", kw["success_url"]).group(1))
    oid, status, total, t = order_of(app, number)
    assert status == "awaiting_payment" and kw["metadata"]["order_id"] == oid

    page = c.get(f"/order/{number}?t={t}").text
    assert "Pay $" in page  # an unpaid order can be paid again
    assert "confirming your payment" in c.get(f"/order/{number}?t={t}&paid=1").text  # not paid yet

    stripe.sessions["cs_test_1"]["payment_status"] = "paid"
    page = c.get(f"/order/{number}?t={t}&paid=1").text
    assert "Payment received" in page
    assert order_of(app, number)[1] == "in_queue"


def test_webhook_marks_paid_only_for_matching_amount(app, stripe, cube_stl, plate_stl):
    c = TestClient(app)
    place(c, cube_stl)
    place(c, plate_stl)
    s1, s2 = stripe.sessions["cs_test_1"], stripe.sessions["cs_test_2"]
    n1 = int(re.search(r"/order/(\d+)", s1["kw"]["success_url"]).group(1))
    n2 = int(re.search(r"/order/(\d+)", s2["kw"]["success_url"]).group(1))

    def send(obj, typ="checkout.session.completed", sig="good"):
        stripe.event = {"type": typ, "data": {"object": obj}}
        return c.post("/stripe/webhook", content=b"{}", headers={"stripe-signature": sig})

    assert send({**s1, "payment_status": "paid"}, sig="forged").status_code == 400
    assert order_of(app, n1)[1] == "awaiting_payment"
    assert send({**s1, "payment_status": "paid", "amount_total": 1}).status_code == 200  # short payment
    assert order_of(app, n1)[1] == "awaiting_payment"
    send({**s1, "payment_status": "paid", "id": "cs_test_2"})  # another order's session
    assert order_of(app, n1)[1] == "awaiting_payment"
    send({**s1, "payment_status": "paid"})
    send({**s1, "payment_status": "paid"})  # Stripe may send twice
    assert order_of(app, n1)[1] == "in_queue"
    send({**s2, "payment_status": "unpaid"})  # bank payment still pending
    assert order_of(app, n2)[1] == "awaiting_payment"
    send({**s2, "payment_status": "paid"}, typ="checkout.session.async_payment_succeeded")
    assert order_of(app, n2)[1] == "in_queue"


def test_pay_again_starts_a_new_session(app, stripe, cube_stl):
    c = TestClient(app)
    place(c, cube_stl)
    number = int(re.search(r"/order/(\d+)", stripe.sessions["cs_test_1"]["kw"]["success_url"]).group(1))
    t = order_of(app, number)[3]
    assert c.post(f"/order/{number}/pay", data={"t": "wrong"}).status_code == 404
    r = c.post(f"/order/{number}/pay", data={"t": t}, follow_redirects=False)
    assert r.headers["location"].endswith("cs_test_2")
    stripe.sessions["cs_test_1"]["payment_status"] = "paid"  # paying the old session no longer counts
    c.get(f"/order/{number}?t={t}&paid=1")
    assert order_of(app, number)[1] == "awaiting_payment"


def test_setup_env_writer(tmp_path):
    from pyslate.stripe_setup import read_env, write_env

    env = tmp_path / "pyslate.env"
    env.write_text("PYSLATE_PUBLIC_URL=https://pyslate.com\n# Add these for card payments:\n# STRIPE_SECRET_KEY=\n# STRIPE_WEBHOOK_SECRET=\nPYSLATE_AGENT_TOKEN=abc\n")
    write_env(env, {"STRIPE_SECRET_KEY": "sk_test_1", "STRIPE_WEBHOOK_SECRET": "whsec_1"})
    got = read_env(env)
    assert got["STRIPE_SECRET_KEY"] == "sk_test_1" and got["STRIPE_WEBHOOK_SECRET"] == "whsec_1"
    assert got["PYSLATE_AGENT_TOKEN"] == "abc" and env.read_text().count("STRIPE_SECRET_KEY") == 1
    write_env(env, {"STRIPE_SECRET_KEY": "sk_live_2"})
    assert read_env(env)["STRIPE_SECRET_KEY"] == "sk_live_2"
