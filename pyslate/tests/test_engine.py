import math

import pytest

from pyslate import geometry as geo
from pyslate.pricing import price_line, total_quote
from pyslate.routing import LASER, PRINT, REVIEW, compatible_materials, default_material, route
from pyslate.shop import Profile, default_profile, validate_profile


@pytest.fixture
def profile():
    return Profile(default_profile())


def test_cube_is_a_3d_part(cube_stl):
    g = geo.analyze(cube_stl)
    assert g.kind == "mesh"
    assert g.extents_mm == pytest.approx([20, 20, 20])
    assert g.volume_mm3 == pytest.approx(8000)
    assert not g.flat
    assert g.watertight


def test_plate_is_flat_with_cut_length(plate_stl):
    g = geo.analyze(plate_stl)
    assert g.flat
    assert g.thickness_mm == pytest.approx(3.0)
    assert g.outline_mm == pytest.approx([60, 40])
    # outer rectangle 200 mm + hole circumference about 31.4 mm
    assert g.cut_length_mm == pytest.approx(200 + 2 * math.pi * 5, rel=0.03)


def test_dxf_measures_outline_and_cut_length(square_dxf):
    g = geo.analyze(square_dxf)
    assert g.kind == "drawing"
    assert g.flat
    assert g.outline_mm == pytest.approx([100, 100])
    assert g.cut_length_mm == pytest.approx(400 + 2 * math.pi * 10, rel=0.01)


def test_bad_file_is_rejected(tmp_path):
    bad = tmp_path / "broken.stl"
    bad.write_bytes(b"not a model")
    with pytest.raises(geo.GeometryError):
        geo.analyze(bad)


def test_routing_sends_flat_parts_to_laser(plate_stl, profile):
    g = geo.analyze(plate_stl)
    material = default_material(g, profile)
    assert profile.material(material)["line"] == LASER
    r = route(g, material, profile)
    assert r.line == LASER and r.machine_id in ("x1", "m2")


def test_flat_part_can_still_be_printed(plate_stl, profile):
    g = geo.analyze(plate_stl)
    r = route(g, "pla", profile)
    assert r.line == PRINT and r.machine_id == "bambu"


def test_wrong_thickness_sheet_is_not_offered(plate_stl, profile):
    g = geo.analyze(plate_stl)
    ids = {m["id"] for m in compatible_materials(g, profile)}
    assert "steel-1" not in ids  # 1 mm steel for a 3 mm part
    assert route(g, "steel-1", profile).line == REVIEW


def test_3d_parts_print_and_oversize_goes_to_review(cube_stl, big_stl, profile):
    assert route(geo.analyze(cube_stl), "pla", profile).line == PRINT
    big = geo.analyze(big_stl)
    assert route(big, "pla", profile).line == REVIEW
    assert route(geo.analyze(cube_stl), "plywood-3", profile).line == REVIEW


def test_dxf_only_offers_sheet_materials(square_dxf, profile):
    g = geo.analyze(square_dxf)
    assert {m["line"] for m in compatible_materials(g, profile)} == {LASER, "router", "plasma"}
    assert route(g, "plasma-steel-6", profile).machine_id == "1300pl"
    assert route(g, "steel-1", profile).machine_id == "metalfab"


def test_print_price_breakdown(cube_stl, profile):
    g = geo.analyze(cube_stl)
    r = route(g, "pla", profile)
    p = price_line(g, "pla", r, 1, profile)
    grams = 8.0 * 1.24 * 0.45
    assert p.material == pytest.approx(grams / 1000 * 22, abs=0.01)
    assert p.machine_minutes == pytest.approx(grams / 12 * 60 + 6, abs=0.1)
    assert p.total == pytest.approx(p.unit_price + 3.0, abs=0.01)


def test_quantity_breaks_lower_unit_price(cube_stl, profile):
    g = geo.analyze(cube_stl)
    r = route(g, "pla", profile)
    one = price_line(g, "pla", r, 1, profile)
    fifty = price_line(g, "pla", r, 50, profile)
    assert fifty.unit_price < one.unit_price
    assert fifty.quantity_multiplier == 0.8


def test_review_parts_have_no_price(big_stl, profile):
    g = geo.analyze(big_stl)
    assert price_line(g, "pla", route(g, "pla", profile), 1, profile) is None


def test_quote_total_applies_rush_and_minimum(profile):
    small = total_quote([4.0], "standard", profile)
    assert small.total == 10.0 and small.minimum_top_up == 6.0
    rush = total_quote([40.0], "rush", profile)
    assert rush.rush_fee == 20.0 and rush.total == 60.0 and rush.lead_days == 3


def test_profile_validation_catches_mistakes():
    data = default_profile()
    assert validate_profile(data) == []
    data["materials"][0]["machines"] = ["nope"]
    del data["machines"][0]["rate_per_hour"]
    problems = validate_profile(data)
    assert any("unknown machine" in p for p in problems)
    assert any("rate_per_hour" in p for p in problems)
