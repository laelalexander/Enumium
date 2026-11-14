import sys, math, pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pipeline
from arm import design, kinematics, control

def test_selection_scales_with_payload():
    light = design.select(300, 0.02)["shoulder"][0]
    heavy = design.select(300, 0.15)["shoulder"][0]
    assert heavy.torque_nm >= light.torque_nm
    with pytest.raises(ValueError):
        design.select(600, 5.0)

def test_parts_validate(tmp_path):
    d = design.design(300, 0.1)
    for p in d["parts"]:
        r = pipeline.run(p["spec"], p["code"], None, 1, tmp_path)
        assert r["ok"], (p["name"], r["errors"])

def test_ik_fk_roundtrip():
    yaw, sh, el, _ = kinematics.ik(150, 80, 40, 150, 150)
    x, y, z = kinematics.fk(yaw, sh, el, 150, 150)
    assert (x, y, z) == pytest.approx((150, 80, 40), abs=0.5)
    with pytest.raises(ValueError):
        kinematics.ik(900, 0, 0, 150, 150)

def test_limits_enforced():
    arm = control.Arm(control.SimDriver(), 150, 150)
    with pytest.raises(ValueError):
        arm.move_to(-100, -5, 0)   # needs yaw ~177°
