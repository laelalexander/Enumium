import re

import pytest
from fastapi.testclient import TestClient

from pyslate.app import create_app
from pyslate.config import Settings
from pyslate.library import originals
from pyslate.library import shapes as S
from pyslate.library.catalog import LICENSES, SOURCES
from pyslate.library.originals import _panel


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    cfg = Settings(data_dir=tmp_path_factory.mktemp("lib") / "data", admin_token="x", secret_key="k" * 32)
    cfg.stripe_secret_key = None
    return TestClient(create_app(cfg))


@pytest.mark.parametrize("w,d,h,top", [(100, 100, 100, True), (150, 100, 70, True), (200, 120, 50, False)])
def test_finger_box_panels_fill_the_shell_exactly(w, d, h, top):
    t = 3.0
    faces = {(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)} | ({(2, 1)} if top else set())
    volume = sum(_panel((w, d, h), a, s, faces, t, 12).area for a, s in faces) * t
    inner_h = h - 2 * t if top else h - t
    assert volume == pytest.approx(w * d * h - (w - 2 * t) * (d - 2 * t) * inner_h)


def test_every_original_is_a_valid_studio_design():
    for slug, _title, _cat, _tags, _summary, fn in originals.ENTRIES:
        shapes = fn()
        assert len(shapes) <= 200, slug
        if not S.has_text(shapes):
            S.server_design(shapes)


def test_every_bundled_design_has_a_qualifying_license(client):
    catalog = client.app.state.library
    assert len(catalog.items) > 4000
    for d in catalog.items:
        assert d.license in LICENSES
        assert SOURCES[d.source]["status"] == "included"
        if LICENSES[d.license]["attribution"]:
            assert d.author and d.attribution


def test_browse_search_and_filter(client):
    r = client.get("/designs")
    assert r.status_code == 200 and "Design library" in r.text
    r = client.get("/designs", params={"q": "dragon"})
    assert r.status_code == 200 and "/designs/art-dragon" in r.text
    r = client.get("/designs", params={"process": "print"})
    assert "nasa-" in r.text and "art-" not in r.text
    r = client.get("/designs", params={"category": "Boxes and storage"})
    assert "finger-box-100x100x100" in r.text
    assert client.get("/designs/sources").status_code == 200


def test_design_page_preview_and_studio_json(client):
    r = client.get("/designs/finger-box-100x100x100")
    assert r.status_code == 200 and "Get a price" in r.text and "<svg" in r.text
    j = client.get("/designs/finger-box-100x100x100/studio.json").json()
    assert j["shapes"] and j["machine"] == "m2"
    r = client.get("/designs/art-acorn", params={"variant": "keychain"})
    assert r.status_code == 200 and "CC BY 3.0" in r.text
    j = client.get("/designs/art-acorn/studio.json", params={"as": "keychain"}).json()
    assert any(s.get("engrave") for s in j["shapes"]) and "game-icons" in j["credit"]
    assert client.get("/designs/art-acorn/art.svg").headers["content-type"].startswith("image/svg")
    assert client.get("/designs/coaster-round-mandala/download.dxf").status_code == 200
    svg = client.get("/designs/art-acorn/download.svg").text
    assert "CC BY 3.0" in svg
    assert client.get("/designs/no-such-design").status_code == 404


def test_order_a_laser_design_creates_a_quote(client):
    r = client.post("/designs/gear-24t/quote", data={}, follow_redirects=False)
    assert r.status_code == 303 and re.match(r"/quote/[\w-]+$", r.headers["location"])
    page = client.get(r.headers["location"])
    assert page.status_code == 200 and "gear-24t" in page.text
    r = client.post("/designs/art-anchor/quote", data={"variant": "coaster"}, follow_redirects=False)
    assert r.status_code == 303


def test_text_designs_go_to_the_studio(client):
    r = client.post("/designs/welcome-sign/quote", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"].startswith("/studio?design=")
