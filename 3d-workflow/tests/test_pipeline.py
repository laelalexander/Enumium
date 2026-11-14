import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pipeline

EX = Path(__file__).parent.parent / "examples"

def test_known_good_part(tmp_path):
    spec = json.loads((EX / "bracket.json").read_text())
    r = pipeline.run(spec, (EX / "bracket.py").read_text(), None, 1, tmp_path)
    assert r["ok"], r["errors"]
    assert (tmp_path / "l_bracket" / "l_bracket.step").exists()
    assert (tmp_path / "l_bracket" / "l_bracket.stl").stat().st_size > 0

def test_bbox_mismatch_detected(tmp_path):
    spec = {"name": "p", "bbox_mm": [100, 100, 100]}
    r = pipeline.run(spec, "result = cq.Workplane('XY').box(10,10,10)", None, 1, tmp_path)
    assert not r["ok"] and "Bounding box" in r["errors"][0]

def test_exception_reported(tmp_path):
    r = pipeline.run({"name": "p"}, "result = cq.Workplane('XY').box(1,1,1).fillet(5)", None, 1, tmp_path)
    assert not r["ok"] and r["errors"][0].startswith("Exception")

def test_missing_result(tmp_path):
    r = pipeline.run({"name": "p"}, "x = 1", None, 1, tmp_path)
    assert not r["ok"] and "result" in r["errors"][0]

def test_disjoint_solids_rejected(tmp_path):
    code = "result = cq.Workplane('XY').box(5,5,5).union(cq.Workplane('XY').box(5,5,5).translate((50,0,0)))"
    r = pipeline.run({"name": "p"}, code, None, 1, tmp_path)
    assert not r["ok"] and "1 solid" in r["errors"][0]
