#!/usr/bin/env python3
"""One entry point.  python run.py [check|build|png|sim|console]
  check    verify Python + dependencies (default first step)
  build    size drives, generate parts, BOM, CAD, drawings, design/index.html, then PNGs if a renderer exists
  png      re-render design/png/*.png from the SVG drawings only (no CAD rebuild)
  sim      demo motion with the simulated driver
  console  interactive control (auto-detects serial port; add --sim for none)"""
import importlib, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent

def check():
    ok = sys.version_info >= (3, 10)
    print(f"Python {sys.version.split()[0]}:", "ok" if ok else "need 3.10+")
    for m, pipname in (("cadquery", "cadquery"), ("serial", "pyserial")):
        try: importlib.import_module(m); print(f"{pipname}: ok")
        except Exception as e: ok = False; print(f"{pipname}: MISSING ({e.__class__.__name__}) -> pip install -r requirements.txt")
    return ok

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    sys.path.insert(0, str(HERE))
    if cmd == "check": sys.exit(0 if check() else 1)
    if cmd == "png":  # needs only a renderer, not cadquery
        from arm import render; sys.exit(0 if render.main() else 1)
    if not check(): sys.exit("fix the above, then rerun")
    if cmd == "build":
        from arm import build, drawings
        build.build(5.0, 1.0); drawings.main()
        from arm import render; render.main()
        print("\nOpen", HERE / "design" / "index.html", "in a browser. Next: python run.py sim")
    elif cmd == "sim":
        from arm.control import Arm, SimDriver
        a = Arm.from_design(SimDriver(), HERE / "design" / "design.json")
        for p in ((500, 0, 100), (450, 200, 50)): print("go", p, "->", a.move_to(*p))
        a.grip(40)
    elif cmd == "console":
        from arm import cli; cli.main(sys.argv[2:])
    else: print(__doc__)

if __name__ == "__main__":
    main()
