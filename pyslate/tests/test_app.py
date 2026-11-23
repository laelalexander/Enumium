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


def test_3d_viewer_page_and_models(client, cube_stl, square_dxf):
    token = quote_token(upload(client, cube_stl, square_dxf))
    page = client.get(f"/quote/{token}").text
    links = re.findall(rf"/quote/{token}/part/(\w+)", page)
    assert len(links) == 2
    for line_id in links:
        view = client.get(f"/quote/{token}/part/{line_id}")
        assert view.status_code == 200
        assert "product-viewer.js" in view.text and "Measure" in view.text
        model_url = re.search(r'"model_url": "([^"]+)"', view.text).group(1)
        model = client.get(model_url)
        assert model.status_code == 200 and model.headers["content-type"] == "model/stl"
        assert len(model.content) > 84  # STL header + at least one triangle
    assert client.get(f"/quote/{token}/part/nope").status_code == 404


def test_dxf_extrudes_to_a_watertight_sheet(square_dxf):
    from pyslate.geometry import dxf_to_mesh

    mesh = dxf_to_mesh(square_dxf, 3.0)
    assert list(mesh.extents) == pytest.approx([100, 100, 3])
    assert mesh.is_watertight
    # 100 x 100 x 3 plate minus a 20 mm hole
    assert mesh.volume == pytest.approx(100 * 100 * 3 - 3.14159 * 100 * 3, rel=0.01)


def test_landing_lists_capabilities(client):
    page = client.get("/").text
    for title in ("Custom System Design", "Mechanical Blueprints", "Electrical Schematics"):
        assert title in page
    assert "/capabilities/system-design" in page
    assert client.get("/request?service=electrical-schematics").status_code == 200


def test_site_pages(client):
    for path in ("/quote", "/capabilities", "/how-it-works", "/materials", "/about"):
        r = client.get(path)
        assert r.status_code == 200, path
    detail = client.get("/capabilities/system-design").text
    assert "/request?service=system-design" in detail
    laser = client.get("/capabilities/laser-cutting").text
    assert "Cast acrylic 3 mm" in laser and "Stainless steel" not in laser
    assert "Stainless steel 1 mm" in client.get("/capabilities/metal-fabrication").text
    assert "xTool MetalFab" in client.get("/materials").text
    assert client.get("/capabilities/nope").status_code == 404


def test_design_request_flow(client):
    desc = "Design a conveyor with a 24 V control panel and full wiring diagrams."
    r = client.post(
        "/request",
        data={"service": "system-design", "name": "Ada", "email": "ada@example.com", "description": desc},
        files=[("files", ("sketch.pdf", b"%PDF-1.4 test", "application/pdf"))],
    )
    assert r.status_code == 200
    assert "R-501" in r.text

    assert client.get("/admin/requests", follow_redirects=False).status_code == 303
    admin_login(client)
    assert "Ada" in client.get("/admin/requests").text
    detail = client.get("/admin/requests/501").text
    assert "conveyor" in detail and "sketch.pdf" in detail
    f = client.get("/admin/requests/501/file/0")
    assert f.status_code == 200 and f.content == b"%PDF-1.4 test"
    client.post("/admin/requests/501", data={"status": "quoted", "shop_notes": "Sent $1,200 quote"})
    assert "Sent $1,200 quote" in client.get("/admin/requests/501").text
    assert client.post("/admin/requests/501", data={"status": "bogus"}).status_code == 400


def test_design_request_validates(client):
    r = client.post("/request", data={"service": "system-design", "name": "Ada",
                                      "email": "ada@example.com", "description": "too short"})
    assert r.status_code == 400
    r = client.post("/request", data={"service": "nope", "name": "Ada", "email": "ada@example.com",
                                      "description": "x" * 40})
    assert r.status_code == 400
    r = client.post(
        "/request",
        data={"service": "product-design", "name": "Ada", "email": "ada@example.com", "description": "x" * 40},
        files=[("files", ("run.exe", b"MZ", "application/octet-stream"))],
    )
    assert r.status_code == 400


PLATE = {"shapes": [
    {"type": "rect", "x": 100, "y": 100, "w": 100, "h": 60, "r": 4},
    {"type": "circle", "x": 60, "y": 80, "d": 5},
    {"type": "slot", "x": 100, "y": 110, "w": 30, "h": 6, "rot": 15},
    {"type": "polygon", "x": 130, "y": 90, "d": 12, "n": 6},
]}


def test_studio_page(client):
    r = client.get("/studio")
    assert r.status_code == 200 and "studio-config" in r.text


def test_studio_laser_quote(client):
    import json
    r = client.post("/studio/quote", data={"design": json.dumps(PLATE), "process": "laser",
                                           "material_id": "acrylic-3", "quantity": "5"})
    assert r.status_code == 200, r.text
    page = client.get(r.json()["url"]).text
    assert "studio-design.dxf" in page and 'class="pill">Laser' in page
    assert 'value="5"' in page


def test_studio_print_quote(client):
    import json
    r = client.post("/studio/quote", data={"design": json.dumps(PLATE), "process": "print",
                                           "material_id": "petg", "height_mm": "20"})
    assert r.status_code == 200, r.text
    page = client.get(r.json()["url"]).text
    assert "studio-design.stl" in page and 'class="pill">3D print' in page
    assert "100.0 × 60.0 × 20.0" in page or "100 × 60 × 20" in page


def test_studio_rejects_bad_designs(client):
    import json
    for design in ("nope", json.dumps({"shapes": []}), json.dumps({"shapes": [{"type": "rect", "x": 0, "y": 0, "w": -1, "h": 5}]})):
        r = client.post("/studio/quote", data={"design": design})
        assert r.status_code == 400 and "error" in r.json()


def test_studio_send_to_engineer(client):
    import json
    r = client.post("/studio/request", data={"design": json.dumps(PLATE), "process": "print", "height_mm": "12",
                                             "name": "Ada", "email": "ada@example.com", "description": ""})
    assert r.status_code == 200 and r.json()["ref"] == "R-501"
    admin_login(client)
    detail = client.get("/admin/requests/501").text
    assert "studio-design.dxf" in detail and "studio-design.stl" in detail and "studio-design.json" in detail


def test_studio_lines_and_engraving(client, tmp_path):
    import json
    from pyslate import studio, geometry as geo
    design = {"shapes": [
        {"type": "rect", "x": 100, "y": 100, "w": 120, "h": 60, "r": 0},
        {"type": "poly", "pts": [[50, 80], [150, 80]], "closed": False, "engrave": False},   # open cut line
        {"type": "poly", "pts": [[60, 90], [80, 90], [80, 110], [60, 110]], "closed": True, "engrave": True},
        {"type": "poly", "pts": [[120, 90], [140, 90], [140, 110]], "closed": True, "engrave": False},  # triangle hole
    ]}
    clean = studio.validate_design(design)
    dxf = tmp_path / "d.dxf"
    studio.design_to_dxf(clean, dxf)
    import ezdxf
    layers = sorted(e.dxf.layer for e in ezdxf.readfile(dxf).modelspace())
    assert layers.count("ENGRAVE") == 1
    mesh = geo.dxf_to_mesh(dxf, 3)
    # the engraved square must not become a hole; the triangle must
    assert abs(mesh.volume - (120 * 60 - 200) * 3) < 1
    r = client.post("/studio/quote", data={"design": json.dumps(design), "process": "print", "height_mm": "5"})
    assert r.status_code == 200
    only_lines = {"shapes": [{"type": "poly", "pts": [[0, 0], [10, 0]], "closed": False}]}
    r = client.post("/studio/quote", data={"design": json.dumps(only_lines), "process": "print"})
    assert r.status_code == 400
