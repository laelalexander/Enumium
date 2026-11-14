#!/usr/bin/env python3
"""One entry point.  python run.py [check|build|png|cut|print|procure|book|guide|kit|wizard|package|ui|sim|console]
  check    verify Python + dependencies (default first step)
  build    size drives, generate parts, BOM, CAD, drawings, design/index.html, then PNGs if a renderer exists
  png      re-render design/png/*.png from the SVG drawings only (no CAD rebuild)
  cut      cut / machined parts: DXF (mm + inch), 1:1 templates, drawings, cut list, fastener schedule -> fab/
  print    orient printed parts, plate them, slice + verify with PrusaSlicer -> print/  (--bed 256x256x256)
  procure  procurement list with quantities and planning prices -> docs/PROCUREMENT.md, docs/procurement.csv
  book     build book PDF (blueprints, assembly plan, BOM, procurement, print plan) -> ../docs/design/
  guide    illustrated assembly guide: step pictures from the 3D twin (needs Node + Playwright) -> ../docs/design/
  kit      build kit: buy list, print list + 3MF + G-code, shop request, guide, wiring, test checklist (--arms N) -> dist/kit/
  wizard   regenerate everything from specs, then the kit (--payload-lb --reach-in --bed --arms --kit-only)
  package  installable Windows desktop app (offline, Library of every doc and file) -> dist/RobotArm-<date>.zip
  ui       3D control surface / virtual test table in the browser (http://127.0.0.1:8765)
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
        from arm import fab; fab.main()
        from arm import render; render.main()
        print("\nOpen", HERE / "design" / "index.html", "in a browser. Next: python run.py sim")
    elif cmd == "cut":
        from arm import fab; sys.exit(fab.main())
    elif cmd == "print":
        from arm import printprep; sys.exit(printprep.main(sys.argv[2:]))
    elif cmd == "procure":
        from arm import procure; procure.main()
    elif cmd == "book":
        from arm import buildbook; buildbook.main()
    elif cmd == "guide":
        from arm import assembly; sys.exit(assembly.guide(sys.argv[2:]))
    elif cmd == "kit":
        from arm import kit; sys.exit(kit.main(sys.argv[2:]))
    elif cmd == "wizard":
        from arm import wizard; sys.exit(wizard.main(sys.argv[2:]))
    elif cmd == "package":
        from arm import package; sys.exit(package.main(sys.argv[2:]))
    elif cmd == "ui":
        from arm import twin; twin.main(sys.argv[2:])
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
