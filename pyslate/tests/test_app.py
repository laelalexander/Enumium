import re

import pytest
from fastapi.testclient import TestClient

from pyslate.app import create_app
from pyslate.config import Settings
from pyslate.models import Job, Order


@pytest.fixture
def app(tmp_path):
    cfg = Settings(data_dir=tmp_path / "data", admin_token="shop-secret", secret_key="k" * 32)
    cfg.stripe_secret_key = None
    return create_app(cfg)


@pytest.fixture
def client(app):
    return TestClient(app)


def upload(client, *paths, token=None):
    files = [("files", (p.name, p.read_bytes(), "application/octet-stream")) for p in paths]
    data = {"quote_token": token} if token else {}
    return client.post("/quote", files=files, data=data, follow_redirects=False)


def quote_token(resp):
    return re.search(r"/quote/([\w-]+)", resp.headers["location"]).group(1)


def admin_login(client):
    r = client.post("/admin/login", data={"token": "shop-secret"}, follow_redirects=False)
    assert r.status_code == 303


def test_landing_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Get instant quote" in r.text
    assert "xTool MetalFab" in r.text


def test_upload_routes_and_prices_each_part(client, cube_stl, plate_stl, square_dxf):
    r = upload(client, cube_stl, plate_stl, square_dxf)
    assert r.status_code == 303
    page = client.get(r.headers["location"]).text
    assert "cube.stl" in page and "plate.stl" in page and "square.dxf" in page
    assert page.count('class="pill">Laser') == 2
    assert page.count('class="pill">3D print') == 1
    assert "Place order" in page


def test_previews(client, cube_stl, square_dxf):
    page = client.get(upload(client, cube_stl, square_dxf).headers["location"]).text
    ids = re.findall(r"/parts/(\w+)/preview", page)
    assert len(ids) == 2
    kinds = {client.get(f"/parts/{i}/preview").headers["content-type"] for i in ids}
    assert kinds == {"model/stl", "image/svg+xml"}


def test_bad_upload_shows_error(client, tmp_path):
    bad = tmp_path / "notes.txt"
    bad.write_text("hello")
    r = upload(client, bad)
    assert r.status_code == 400
    assert "Pyslate accepts" in r.text


def test_changing_material_reroutes(client, plate_stl):
    token = quote_token(upload(client, plate_stl))
    page = client.get(f"/quote/{token}").text
    line_id = re.search(r'id="line-(\w+)"', page).group(1)
    r = client.post(f"/quote/{token}/line/{line_id}", data={"material_id": "petg", "quantity": "5"},
                    follow_redirects=True)
    assert 'class="pill">3D print' in r.text
    bad = client.post(f"/quote/{token}/line/{line_id}", data={"material_id": "steel-1", "quantity": "1"})
    assert bad.status_code == 400 and "does not suit" in bad.text


def test_full_order_flow(app, client, cube_stl, plate_stl):
    token = quote_token(upload(client, cube_stl, plate_stl))
    client.post(f"/quote/{token}/lead", data={"lead_tier": "rush"})
    r = client.post(
        f"/quote/{token}/checkout",
        data={"email": "buyer@example.com", "name": "Test Buyer", "address": "1 Main St"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    order_url = r.headers["location"]
    number = int(re.search(r"/order/(\d+)", order_url).group(1))
    assert "Awaiting payment" in client.get(order_url).text
    assert client.get(f"/order/{number}?t=wrong").status_code == 404

    # Admin is locked until sign-in, and the wrong password is refused.
    assert client.get("/admin", follow_redirects=False).status_code == 303
    assert client.post("/admin/login", data={"token": "nope"}).status_code == 401
    admin_login(client)
    client.post(f"/admin/order/{number}/paid")

    with app.state.session_factory() as db:
        order = db.query(Order).filter_by(number=number).one()
        assert order.status == "in_queue" and order.lead_days == 3
        jobs = db.query(Job).filter_by(order_id=order.id).all()
        assert {j.line for j in jobs} == {"print", "laser"}
        job_ids = [j.id for j in jobs]

    queue = client.get("/admin").text
    assert "cube.stl" in queue and "plate.stl" in queue

    client.post(f"/admin/job/{job_ids[0]}", data={"state": "running"})
    assert "Making" in client.get(order_url).text
    for jid in job_ids:
        if jid != job_ids[0]:
            client.post(f"/admin/job/{jid}", data={"state": "running"})
        client.post(f"/admin/job/{jid}", data={"state": "done"})
    assert "All parts made" in client.get(order_url).text

    client.post(f"/admin/order/{number}/status", data={"status": "shipped", "tracking": "1Z999"})
    page = client.get(order_url).text
    assert "1Z999" in page

    # An ordered quote can no longer be changed.
    assert client.post(f"/quote/{token}/lead", data={"lead_tier": "standard"}).status_code == 200
    with app.state.session_factory() as db:
        assert db.query(Order).filter_by(number=number).one().lead_days == 3


def test_invalid_job_move_is_refused(app, client, cube_stl):
    token = quote_token(upload(client, cube_stl))
    r = client.post(f"/quote/{token}/checkout",
                    data={"email": "a@b.co", "name": "A", "address": "Somewhere"}, follow_redirects=False)
    number = int(re.search(r"/order/(\d+)", r.headers["location"]).group(1))
    admin_login(client)
    client.post(f"/admin/order/{number}/paid")
    with app.state.session_factory() as db:
        job_id = db.query(Job).one().id
    assert client.post(f"/admin/job/{job_id}", data={"state": "done"}).status_code == 400


def test_quote_with_review_part_cannot_be_ordered(client, big_stl):
    token = quote_token(upload(client, big_stl))
    page = client.get(f"/quote/{token}").text
    assert "Needs review" in page and "Place order" not in page
    r = client.post(f"/quote/{token}/checkout", data={"email": "a@b.co", "name": "A", "address": "X"})
    assert r.status_code == 400


def test_rates_editor_validates(client):
    admin_login(client)
    assert client.post("/admin/rates", data={"profile": "{not json"}).status_code == 400
    page = client.get("/admin/rates").text
    assert "rate_per_hour" in page


def test_admin_disabled_without_token(tmp_path):
    cfg = Settings(data_dir=tmp_path / "d2", secret_key="x" * 32)
    cfg.admin_token = None
    c = TestClient(create_app(cfg))
    assert c.get("/admin/login").status_code == 503
