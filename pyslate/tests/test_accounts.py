import json
import re

from fastapi.testclient import TestClient

from pyslate.accounts import check_password, hash_password, safe_next
from tests.test_app import app, client, quote_token, upload  # noqa: F401  (fixtures)

PW = "correct-horse-battery"


def signup(c, email="me@example.com", password=PW, next=""):
    return c.post("/account/signup", data={"email": email, "password": password, "name": "Ada Lovelace", "next": next},
                  follow_redirects=False)


def test_password_hashing():
    h = hash_password(PW)
    assert h.startswith("scrypt$") and PW not in h
    assert check_password(PW, h) and not check_password("wrong", h) and not check_password(PW, "junk")


def test_safe_next_stays_on_site():
    assert safe_next("/studio") == "/studio"
    for bad in ("https://evil.example", "//evil.example", "/\\evil", "", None):
        assert safe_next(bad) == "/account"


def test_signup_login_logout(client):
    assert client.get("/account", follow_redirects=False).headers["location"].startswith("/account/login")
    r = signup(client)
    assert r.status_code == 303 and r.headers["location"] == "/account"
    page = client.get("/account").text
    assert "Hi, Ada" in page and "Saved jobs" in page
    assert signup(client).status_code == 400  # same email again
    assert signup(client, email="x@example.com", password="short").status_code == 400
    client.post("/account/logout")
    assert client.get("/account", follow_redirects=False).status_code == 303
    assert client.post("/account/login", data={"email": "ME@example.com ", "password": "nope"}).status_code == 401
    r = client.post("/account/login", data={"email": "ME@example.com", "password": PW, "next": "/studio"},
                    follow_redirects=False)
    assert r.headers["location"] == "/studio"


def test_login_is_throttled(client):
    signup(client)
    client.post("/account/logout")
    for _ in range(8):
        client.post("/account/login", data={"email": "me@example.com", "password": "bad"})
    assert client.post("/account/login", data={"email": "me@example.com", "password": PW}).status_code == 429


def test_forged_cookie_is_ignored(client):
    signup(client)
    raw = client.cookies.get("pyslate_customer")
    cid, ver, exp, mac = raw.split(".")
    client.cookies.set("pyslate_customer", f"{cid}.{ver}.{int(exp) + 999}.{mac}")
    assert client.get("/account", follow_redirects=False).status_code == 303


def test_order_placed_signed_in_shows_on_dashboard(client, cube_stl):
    signup(client)
    client.post("/account/settings/profile", data={"name": "Ada Lovelace", "shipping_address": "1 Engine Way"})
    token = quote_token(upload(client, cube_stl))
    qpage = client.get(f"/quote/{token}").text
    assert 'value="me@example.com"' in qpage and "1 Engine Way" in qpage  # checkout is prefilled
    r = client.post(f"/quote/{token}/checkout", data={"email": "me@example.com", "name": "Ada", "address": "1 Engine Way"},
                    follow_redirects=False)
    number = re.search(r"/order/(\d+)", r.headers["location"]).group(1)
    dash = client.get("/account").text
    assert f"Order #{number}" in dash and "Awaiting payment" in dash
    order_page = client.get(r.headers["location"]).text
    assert "Back to my account" in order_page and "PLA" in order_page  # material name, not its id


def test_add_order_needs_private_link(app, cube_stl):
    buyer = TestClient(app)
    token = quote_token(upload(buyer, cube_stl))
    r = buyer.post(f"/quote/{token}/checkout", data={"email": "me@example.com", "name": "A", "address": "X"},
                   follow_redirects=False)
    number, t = re.search(r"/order/(\d+)\?t=([\w-]+)", r.headers["location"]).groups()
    me = TestClient(app)
    signup(me)
    assert f"Order #{number}" not in me.get("/account").text  # same email is not enough
    assert me.post("/account/orders/add", data={"number": number, "token": "guess"}).status_code == 404
    r = me.post("/account/orders/add", data={"number": number, "token": t}, follow_redirects=True)
    assert "Added to" in r.text
    assert f"Order #{number}" in me.get("/account").text


def test_save_quote(client, cube_stl):
    token = quote_token(upload(client, cube_stl))
    assert "sign in</a> to keep it" in client.get(f"/quote/{token}").text
    signup(client)
    assert "Save to my account" in client.get(f"/quote/{token}").text
    r = client.post("/account/quotes/save", data={"token": token}, follow_redirects=True)
    assert "Saved to" in r.text
    client.post("/account/quotes/save", data={"token": token})  # no duplicate
    dash = client.get("/account").text
    assert dash.count(f'href="/quote/{token}"') == 1 and "cube.stl" in dash
    sid = re.search(r"/account/quotes/(\w+)/delete", dash).group(1)
    client.post(f"/account/quotes/{sid}/delete")
    assert f'href="/quote/{token}"' not in client.get("/account").text


def test_save_and_reopen_design(app, client):
    design = {"shapes": [{"id": 1, "type": "rect", "x": 0, "y": 0, "w": 40, "h": 20, "rot": 0}], "machine": "x1",
              "material": "plywood-3", "quantity": 2, "secret": "dropped"}
    r = client.post("/account/designs", data={"design": json.dumps(design), "name": "Tag"})
    assert r.status_code == 401 and r.json()["error"] == "signin"
    signup(client)
    assert client.post("/account/designs", data={"design": "{}"}).status_code == 400
    saved = client.post("/account/designs", data={"design": json.dumps(design), "name": "Tag"}).json()
    again = client.post("/account/designs", data={"design": json.dumps(design), "name": "Tag v2", "design_id": saved["id"]}).json()
    assert again["id"] == saved["id"]
    got = client.get(f"/account/designs/{saved['id']}.json").json()
    assert got["name"] == "Tag v2" and got["quantity"] == 2 and "secret" not in got
    assert f"/studio?design=/account/designs/{saved['id']}.json" in client.get("/account").text
    other = TestClient(app)
    signup(other, email="other@example.com")
    assert other.get(f"/account/designs/{saved['id']}.json").status_code == 404
    assert other.post(f"/account/designs/{saved['id']}/delete").status_code == 404
    client.post(f"/account/designs/{saved['id']}/delete")
    assert client.get(f"/account/designs/{saved['id']}.json").status_code == 404


def test_settings_profile_password_and_payments(app, client):
    signup(client)
    page = client.get("/account/settings").text
    assert "Card payments aren't switched on yet" in page
    client.post("/account/settings/profile", data={"name": "Ada", "company": "Engines Ltd", "phone": "555", "shipping_address": "1 Way"})
    assert "Engines Ltd" in client.get("/account/settings").text
    assert client.post("/account/settings/payments").status_code == 400
    other_device = TestClient(app)
    other_device.post("/account/login", data={"email": "me@example.com", "password": PW})
    assert other_device.get("/account", follow_redirects=False).status_code == 200
    assert client.post("/account/settings/password", data={"current": "wrong", "new": "another-long-pass"}).status_code == 400
    r = client.post("/account/settings/password", data={"current": PW, "new": "another-long-pass"}, follow_redirects=False)
    assert r.status_code == 303
    assert client.get("/account", follow_redirects=False).status_code == 200  # this device stays signed in
    assert other_device.get("/account", follow_redirects=False).status_code == 303  # others are signed out


def test_header_shows_account_state(client):
    assert ">Sign in<" in client.get("/").text
    signup(client)
    assert ">Account<" in client.get("/").text
    assert "Saved designs are in" in client.get("/studio").text



def test_payment_portal_uses_stripe_customer(tmp_path, monkeypatch):
    import sys
    import types

    from pyslate.app import create_app
    from pyslate.config import Settings

    calls = {}

    def record(name, result):
        def fn(**kw):
            calls[name] = kw
            return result
        return fn

    fake = types.SimpleNamespace(
        api_key=None, StripeError=Exception,
        Customer=types.SimpleNamespace(create=record("customer", types.SimpleNamespace(id="cus_test"))),
        billing_portal=types.SimpleNamespace(Session=types.SimpleNamespace(
            create=record("portal", types.SimpleNamespace(url="https://billing.stripe.test/p")))),
    )
    monkeypatch.setitem(sys.modules, "stripe", fake)
    cfg = Settings(data_dir=tmp_path / "data", admin_token="x", secret_key="k" * 32)
    cfg.stripe_secret_key = "sk_test_fake"
    c = TestClient(create_app(cfg))
    signup(c)
    assert "Manage payment methods" in c.get("/account/settings").text
    r = c.post("/account/settings/payments", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "https://billing.stripe.test/p"
    assert calls["customer"]["email"] == "me@example.com"
    assert calls["portal"]["customer"] == "cus_test" and calls["portal"]["return_url"].endswith("/account/settings")
    calls.clear()
    c.post("/account/settings/payments", follow_redirects=False)
    assert "customer" not in calls  # the Stripe customer id was kept
