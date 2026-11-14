import sys, json, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from arm import design, kinematics, control, build, hardware

def test_5lb_fits_in_4ft_with_margin():
    d = design.design(5.0, 1.0)
    assert d["extension_m"] <= design.MAX_EXTENSION
    for j, v in d["joints"].items():
        assert v["margin"] >= design.SAFETY, (j, v)

def test_full_4ft_still_feasible_and_overreach_not_default():
    assert design.design(5.0, 1.219)["extension_m"] == 1.219
    assert design.max_extension(5 * design.LB)[0] <= design.MAX_EXTENSION

def test_heavier_payload_infeasible():
    with pytest.raises(ValueError):
        design.design(15.0, 1.0)

def test_belt_center_grows_with_ratio():
    assert hardware.belt_center_mm(5) > hardware.belt_center_mm(3) > hardware.belt_center_mm(1)

def test_build_all_parts_valid(tmp_path):
    d = build.build(5.0, 1.0, tmp_path)
    bad = {k: v["errors"] for k, v in d["parts"].items() if not v["ok"]}
    assert not bad, bad
    assert (tmp_path / "BOM.md").exists()

def test_ik_fk_roundtrip():
    yaw, sh, el, _ = kinematics.ik(300, 160, 80, 375, 375)
    x, y, z = kinematics.fk(yaw, sh, el, 375, 375)
    assert (x, y, z) == pytest.approx((300, 160, 80), abs=0.5)
    with pytest.raises(ValueError):
        kinematics.ik(1500, 0, 0, 375, 375)

def test_control_steps_and_limits(tmp_path):
    sent = []
    class Rec:
        def move(self, ch, s): sent.append((ch, s))
        def home(self, ch, d): pass
        def wait(self): pass
    arm = control.Arm(Rec(), 375, 375, {"yaw": 20, "shoulder": 100, "elbow": 60, "wrist": 20})
    arm.move_joints(0, 90, 0, 0)
    assert sent[1] == (1, round((90 - control.Arm.HOME_DEG["shoulder"]) * 200 * control.MICROSTEP * 100 / 360))
    with pytest.raises(ValueError):
        arm.move_joints(0, 170, 0, 0)
    with pytest.raises(ValueError):
        arm.grip(100)

def test_design_package_generates(tmp_path, monkeypatch):
    from arm import drawings
    monkeypatch.setattr(drawings, "OUT", tmp_path)
    import pipeline, json
    if not (pipeline.HERE / "out/arm/design.json").exists():
        build.build(5.0, 1.0)
    drawings.main()
    assert len(list((tmp_path / "cad/step").glob("*.step"))) == 14
    assert (tmp_path / "schematics/ELE-001_wiring.svg").exists()
    import xml.dom.minidom as m
    for f in list((tmp_path / "drawings").glob("*.svg")) + list((tmp_path / "schematics").glob("*.svg")):
        m.parse(str(f))      # well-formed XML

def test_cli_commands_and_port_detection(capsys):
    from arm import cli
    import json
    d = pipeline_design = None
    sent = []
    class Rec:
        def move(self, ch, s): sent.append((ch, s))
        def home(self, ch, dr): sent.append(("home", ch))
        def wait(self): pass
        def stop(self): sent.append("stop")
    arm = control.Arm(Rec(), 375, 375, {"yaw": 20, "shoulder": 100, "elbow": 60, "wrist": 20})
    cli.run_line(arm, "go 500 0 100"); cli.run_line(arm, "grip 40"); cli.run_line(arm, "home"); cli.run_line(arm, "stop")
    assert sent[-1] == "stop" and ("home", 0) in sent and any(c == 4 for c, *_ in [x for x in sent if isinstance(x, tuple)])
    with pytest.raises(ValueError):
        cli.run_line(arm, "grip 999")
    assert hasattr(cli, "find_port")

def test_run_check_and_sim(tmp_path):
    import subprocess
    r = subprocess.run([sys.executable, str(Path(__file__).parent.parent / "run.py"), "sim"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "go (500, 0, 100)" in r.stdout

def test_twin_model_covers_every_part():
    from arm import twin
    m = twin.model()
    stl_dir = Path(__file__).parent.parent / "design" / "cad" / "stl"
    assert {p["id"] for p in m["printed"]} == {p.stem for p in stl_dir.glob("*.stl")}
    assert [j["channel"] for j in m["joints"]] == [0, 1, 2, 3] and m["gripper"]["channel"] == 4
    assert len(m["purchased"]) == len(build.AMAZON_ITEMS)
    for j in m["joints"]:
        lo, hi = j["limits_deg"]
        assert lo <= j["home_deg"] <= hi
    app = (Path(__file__).parent.parent / "control" / "app.js").read_text(encoding="utf-8")
    for cmd in ("'V'", "'G'", "'H'", "'W'", "'X'", "'Z'", "'E'", "'?'"):   # same grammar as the firmware
        assert cmd in app

def test_print_plates_fit_bambu_bed():
    from arm import printprep
    items = [("a#1", 222.9, 100), ("b#1", 210, 210), ("c#1", 60, 56)] + [(f"s#{i}", 140, 50) for i in range(3)]
    plates = printprep.pack(items, 256, 256)
    assert sum(len(p) for p in plates) == len(items)
    for p in plates:
        for key, cx, cy, rot in p:
            assert 0 < cx < 256 and 0 < cy < 256

def test_procurement_covers_bom():
    from arm import procure
    rows = procure.rows()
    assert sum(1 for r in rows if r["cat"] == "Motors") == 4
    assert all(r["qty"] > 0 for r in rows)


def _features(code):
    import math, cadquery as cq
    from arm import sheets
    ns = {"cq": cq, "math": math}; exec("import math\n" + code, ns)
    v = ns["result"].val()
    return sheets.features(v, v.BoundingBox())


def test_cheek_has_bearing_seat_counterbore():
    """Regression: the bearing recess was extruded away from the plate and cut nothing."""
    from arm import hardware as H
    f = _features(H.cheek(True, 107.9))
    cb = [x for x in f if x["cb"]]
    assert len(cb) == 1 and abs(cb[0]["cb"][0] - 28.15) < 0.01 and abs(cb[0]["cb"][1] - 8.2) < 0.01
    assert sum(1 for x in f if x["kind"] == "slot") == 4


def test_gripper_insert_holes_fit_m4_inserts():
    from arm import hardware as H
    f = _features(H.gripper_body())
    assert sum(1 for x in f if abs(x["dia"] - 5.6) < 0.01) == 4      # M4 heat-set pilot, was 4.0
    assert sum(1 for x in f if abs(x["dia"] - 3.4) < 0.01) == 4      # NEMA 17 screws (break into the pocket)


def test_fab_package_dual_units_and_fasteners(tmp_path, monkeypatch):
    import ezdxf
    from arm import fab, fasteners
    monkeypatch.setattr(fab, "OUT", tmp_path)
    assert fab.main() == 0
    for p in fab.parts():
        mm = ezdxf.readfile(tmp_path / "dxf/mm" / f"{p.pid}.dxf"); inch = ezdxf.readfile(tmp_path / "dxf/inch" / f"{p.pid}.dxf")
        assert mm.header["$INSUNITS"] == 4 and inch.header["$INSUNITS"] == 1
        svg = (tmp_path / "drawings" / f"{p.pid}.svg").read_text(encoding="utf-8")
        assert "HOLE AND FASTENER TABLE" in svg and "[" in svg
    # every printed-part hole maps to a fastener or fit, never the fallback
    from arm import hardware as H
    for name, (code, q, n) in H.parts({"shoulder": 5, "elbow": 3}).items():
        spec = fasteners.for_part(name)
        for f in _features(code):
            assert spec(f) != "Fit to the mating part (see assembly)", (name, f["dia"])
    # all four tube cuts fit one 48 in length
    import json
    d = json.loads((fab.HERE / "design" / "design.json").read_text(encoding="utf-8"))
    assert sum(t["length"] + 3 for t in fab.tubes(d)) < 1219


def test_assembly_steps_cover_every_twin_part_and_known_fasteners():
    from arm import assembly as A
    from arm.fasteners import FASTENERS
    from arm.twin import model
    ids = [s["id"] for s in A.STEPS]
    assert len(ids) == len(set(ids)) >= 12
    for s in A.STEPS:
        assert s["do"] and s["check"] and len(s["view"]) == 3
        for f, q in s["fasteners"]:
            assert f in FASTENERS and q > 0, (s["id"], f)
    assert [s["id"] for s in model()["assembly"]] == ids
    # every fab part the twin draws is introduced by some step
    fab = {p["pid"] for p in json.loads((Path(__file__).resolve().parent.parent / "fab" / "fab.json").read_text())} \
        if (Path(__file__).resolve().parent.parent / "fab" / "fab.json").exists() else set()
    sels = {sel.split("~")[0] for s in A.STEPS for sel in s["show"]}
    assert fab <= sels | {"ENC-01"}, fab - sels
