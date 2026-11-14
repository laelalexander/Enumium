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
