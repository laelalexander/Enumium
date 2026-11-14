"""python -m arm.build --reach 300 --payload 0.1  -> sized design, parts, BOM."""
import argparse, json, sys
from pathlib import Path
from . import design as D
import pipeline

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reach", type=float, default=300.0, help="mm, shoulder to wrist")
    ap.add_argument("--payload", type=float, default=0.1, help="kg at gripper")
    a = ap.parse_args()
    d = D.design(a.reach, a.payload)
    root = Path(pipeline.HERE) / "out" / "arm"
    ok = True
    for p in d["parts"]:
        r = pipeline.run(p["spec"], p["code"], None, 1, root)
        p["ok"], p["metrics"], p["errors"] = r["ok"], r["metrics"], r["errors"]
        ok &= r["ok"]
        del p["code"]
    (root / "design.json").write_text(json.dumps(d, indent=2))
    print(json.dumps({k: d[k] for k in ("joints", "bom")}, indent=2))
    print("parts:", {p["name"]: p["ok"] for p in d["parts"]}, "->", root)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
