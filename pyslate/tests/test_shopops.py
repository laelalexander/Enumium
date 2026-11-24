"""Customers, packing and shipping in the shop console."""

import pytest
from fastapi.testclient import TestClient

from pyslate import services
from pyslate.app import create_app
from pyslate.config import Settings
from pyslate.models import Job, Order, Quote


@pytest.fixture
def app(tmp_path):
    cfg = Settings(data_dir=tmp_path / "data", admin_token="shop-secret", secret_key="k" * 32)
    cfg.stripe_secret_key = None
    return create_app(cfg)


@pytest.fixture
def shop(app):
    c = TestClient(app)
    c.post("/admin/login", data={"token": "shop-secret"})
    return c


def order_for(app, part, email="guest@example.com", name="Gus Guest", made=False):
    cfg = app.state.settings
    with app.state.session_factory() as db:
        quote = Quote()
        db.add(quote)
        services.add_part_to_quote(db, quote, services.store_part(db, cfg.upload_dir, part.name, part))
        db.flush()
        order = services.place_order(db, quote, email, name, "5 Elm St\nAustin, TX")
        services.mark_paid(db, order)
        if made:
            for job in order.jobs:
                services.move_job(db, job, "running")
                services.move_job(db, job, "done")
        return order.number, order.access_token


def test_customers_lists_accounts_and_guests(app, shop, cube_stl):
    buyer = TestClient(app)
    buyer.post("/account/signup", data={"email": "ada@example.com", "password": "correct-horse-1", "name": "Ada Park"})
    order_for(app, cube_stl, email="ada@example.com", name="Ada Park")
    order_for(app, cube_stl)
    page = shop.get("/admin/customers").text
    assert "Ada Park" in page and "Gus Guest" in page and "1 account" in page and "1 guest buyer" in page
    assert "Gus" not in shop.get("/admin/customers?q=ada").text
    detail = shop.get("/admin/customers/ada@example.com").text
    assert "Ada Park" in detail and "Close account" in detail and "1001" in detail
    assert "Guest buyer" in shop.get("/admin/customers/guest@example.com").text
    assert shop.get("/admin/customers/nobody@example.com").status_code == 404

    shop.post("/admin/customers/ada@example.com", data={"action": "notes", "shop_notes": "Prefers PETG"})
    assert "Prefers PETG" in shop.get("/admin/customers/ada@example.com").text
    # Closing the account signs the customer out and blocks sign-in; reopening lets them back.
    assert buyer.get("/account", follow_redirects=False).status_code == 200
    shop.post("/admin/customers/ada@example.com", data={"action": "close"})
    assert buyer.get("/account", follow_redirects=False).status_code != 200
    r = buyer.post("/account/login", data={"email": "ada@example.com", "password": "correct-horse-1"})
    assert r.status_code == 403 and "closed" in r.text
    shop.post("/admin/customers/ada@example.com", data={"action": "reopen"})
    r = buyer.post("/account/login", data={"email": "ada@example.com", "password": "correct-horse-1"},
                   follow_redirects=False)
    assert r.status_code == 303


def test_pack_ship_deliver(app, shop, cube_stl):
    number, token = order_for(app, cube_stl, made=True)
    board = shop.get("/admin/shipping").text
    assert f"#{number}" in board and "Mark packed" in board
    slip = shop.get(f"/admin/order/{number}/packing-slip").text
    assert "Packing slip" in slip and "cube.stl" in slip and "Austin, TX" in slip

    # Shipping before packing is refused; a carrier with tracking needs the number.
    shop.post(f"/admin/order/{number}/pack", data={"packages": "2", "weight_g": "450", "dims": "200 x 150 x 100"})
    assert "Mark shipped" in shop.get("/admin/shipping").text
    r = shop.post(f"/admin/order/{number}/ship", data={"carrier": "ups", "tracking": ""}, follow_redirects=False)
    assert "tracking" in r.headers["location"]
    shop.post(f"/admin/order/{number}/ship", data={"carrier": "ups", "service": "Ground", "tracking": "1Z999AA10123456784"})
    customer = TestClient(app).get(f"/order/{number}?t={token}").text
    assert "Shipped with <strong>UPS Ground" in customer
    assert "https://www.ups.com/track?tracknum=1Z999AA10123456784" in customer and "2 boxes" in customer
    assert "Mark delivered" in shop.get("/admin/shipping").text
    shop.post(f"/admin/order/{number}/delivered")
    with app.state.session_factory() as db:
        assert db.query(Order).filter_by(number=number).one().status == "delivered"
    assert "Delivered" in TestClient(app).get(f"/order/{number}?t={token}").text


def test_pickup_needs_no_tracking(app, shop, cube_stl):
    number, token = order_for(app, cube_stl, made=True)
    shop.post(f"/admin/order/{number}/pack", data={"packages": "1"})
    shop.post(f"/admin/order/{number}/ship", data={"carrier": "pickup"})
    assert "ready for pickup" in TestClient(app).get(f"/order/{number}?t={token}").text


def test_orders_still_making_show_as_coming(app, shop, cube_stl):
    number, _ = order_for(app, cube_stl)
    page = shop.get("/admin/shipping").text
    assert "Still being made" in page and f"#{number}" in page and "0/1 parts made" in page
