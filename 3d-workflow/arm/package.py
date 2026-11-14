"""Desktop app package for Windows.   python run.py package

Builds dist/RobotArm/ and dist/RobotArm-<date>.zip: the whole test table plus every note, drawing,
guide and file it links to, with three.js bundled so it runs offline. Unzip, double-click
"Install Robot Arm.vbs", and the app opens from a Robot Arm icon on the desktop and Start menu
(local Node server + Microsoft Edge app window, so the Arduino link over Web Serial still works)."""
import shutil, zipfile
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DIST = HERE / "dist"
DESKTOP = HERE / "desktop"

# app/ is the whole 3d-workflow tree (sources + outputs), so the Build wizard can regenerate in place on the PC.
# docs/design (guide, build book, assembly pictures) sits next to it, where the generators write it.
EXCLUDE_TOP = {"dist", "out", "window", ".venv", "venv", ".pytest_cache", "__pycache__", "examples"}
SKIP = {"__pycache__", ".pytest_cache", "window", "server.log", "server.err.log", "gcode"}

README = """Robot Arm desktop app
=====================

Install:   double-click "Install Robot Arm.vbs". It copies the app to C:\\Anatomy\\robot-arm when the Anatomy app is
           on this PC (it then shows up as an Anatomy project with the live 3D viewer), else to %LOCALAPPDATA%\\Programs\\RobotArm,
           installs Node.js LTS with winget if it is missing, and adds a "Robot Arm" icon to the
           desktop and the Start menu. Run it again to update; it keeps your Arduino port permission.
Open:      the Robot Arm icon. It opens in its own window (Microsoft Edge app mode), works offline.
Remove:    right-click Uninstall-RobotArm.ps1 > Run with PowerShell.

Inside the app
  Control, Motors, Test   move the 3D arm, presets, teach and play, load tests (simulated until you connect)
  Parts                   every part on the table; click one for its drawing, CAD, print settings and files.
                          "Assembly steps" walks through the build, new parts in colour.
  Library                 assembly guide, build book, BOM, procurement, fasteners, cut list, wiring notes,
                          every drawing, DXF cut files, Bambu plates, STEP/STL/OBJ. "Open with default app"
                          sends a 3MF to Bambu Studio; "Show in folder" opens Explorer at the file.
  Link                    USB connection to the Arduino Mega running firmware/arm_controller.

Built {date} from laelalexander/Enumium, 3d-workflow. Rebuild with: python run.py package
"""


def icon(path):
    """A simple robot-arm glyph as a multi-size .ico (Pillow); skipped if Pillow is missing."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False
    S = 256
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, S - 8, S - 8), 48, fill=(22, 27, 34, 255))
    o = (238, 120, 40, 255)
    d.rounded_rectangle((52, 196, 204, 216), 8, fill=(150, 160, 172, 255))          # base
    d.rectangle((112, 160, 144, 198), fill=o)                                         # riser
    d.line((128, 160, 92, 92), fill=o, width=26)                                      # upper arm
    d.line((92, 92, 178, 64), fill=o, width=22)                                       # forearm
    for x, y, r in ((128, 160, 18), (92, 92, 16), (178, 64, 13)):
        d.ellipse((x - r, y - r, x + r, y + r), fill=(240, 240, 240, 255))
    d.polygon([(190, 50), (214, 58), (206, 82), (196, 74), (200, 64), (188, 60)], fill=(240, 240, 240, 255))  # gripper
    im.save(path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return True


def _copy(src, dst):
    if src.is_dir():
        shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if n in SKIP], dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


ANATOMY = {
    "title": "Robot arm test table",
    "summary": "4-DOF desktop robot arm (yaw, shoulder, elbow, wrist pitch) with a lead-screw gripper, on a test table with its "
               "electronics enclosure. 5 lb payload at 39.4 in reach. NEMA 23 planetary gearmotors with HTD 5M belt stages, "
               "PETG printed joints, aluminium tubes, Arduino Mega + DM542 drivers. Complete build package: drawings in mm [in], "
               "DXF cut files, Bambu plates and G-code, purchase list, illustrated assembly guide, wiring and firmware.",
    "apps": [{"name": "Robot arm test table", "cwd": ".", "run": ["node server.js"], "url": "http://127.0.0.1:8766/", "needs": ["Node.js"],
              "startup_ms": 3000,
              "description": "3D twin you can drive (simulated until an Arduino is connected), part inspector, Library of every "
                             "drawing and file, and the Build wizard that regenerates the design and the build kit."}],
}
CLAUDE = """# Robot arm test table (Anatomy project)

Prototype standard for Anatomy hardware projects: a design is finished when this folder lets someone build it.

- `app/` is the whole design workflow (Python generators + outputs). Regenerate everything with
  `cd app && python run.py wizard` (or the Build it button in the app). Tests: `python -m pytest -q tests`.
- `app/design/drawings` part and assembly drawings (ASM-001 general arrangement, ASM-002 joint section),
  `app/design/schematics` ELE-001 schematic and ELE-002 wire list, `app/fab` cut files, `app/print` Bambu plates and G-code.
- `app/design/cad/stl/assembly` every part in its assembled position with parts.json (for the live 3D viewer).
- `build/build.json` the build plan (purchase, print, fabricate, assembly, firmware, tests) for the Build wizard;
  the human-readable kit is `app/dist/kit/RobotArm-Build-Kit/START-HERE.html`.
- `docs/design` illustrated assembly guide and build book (PDF).
- Standards: dual units mm [in], full hole callouts, every part BUY (real spec) or BUILD (design file), G-code for every print.
"""


def anatomy(out):
    """Make the package an Anatomy project: anatomy.json (runnable app), build/build.json (Build wizard) and CLAUDE.md."""
    import json
    from . import kit
    (out / "anatomy.json").write_text(json.dumps(ANATOMY, indent=1), encoding="utf-8")
    (out / "CLAUDE.md").write_text(CLAUDE, encoding="utf-8")
    src = out / "app" / "dist" / "kit" / kit.NAME / "build.json"
    if src.exists():
        (out / "build").mkdir(exist_ok=True)
        shutil.copy2(src, out / "build" / "build.json")


def main(argv=None):
    from . import twin
    twin.write()                                   # arm_model.json + Library (control/lib)
    out = DIST / "RobotArm"
    if out.exists():
        shutil.rmtree(out)
    app = out / "app"
    missing = []
    from . import kit
    kit.build(1)                                   # a ready kit ships inside the app (dist/kit)
    for f in HERE.iterdir():
        if f.name not in EXCLUDE_TOP and not f.name.startswith("."):
            _copy(f, app / f.name)
    shutil.copytree(HERE / "dist" / "kit" / kit.NAME, app / "dist" / "kit" / kit.NAME)   # with its gcode (SKIP would drop it)
    _copy(HERE.parent / "docs" / "design", out / "docs" / "design")
    for f in DESKTOP.iterdir():
        if f.is_file():
            shutil.copy2(f, out / f.name)
    (out / "README.txt").write_text(README.format(date=date.today().isoformat()), encoding="utf-8")
    anatomy(out)
    if not icon(out / "robot-arm.ico"):
        missing.append("robot-arm.ico (pip install pillow)")
    shutil.copy2(out / "robot-arm.ico", app / "control" / "favicon.ico") if (out / "robot-arm.ico").exists() else None
    zp = DIST / f"RobotArm-{date.today().isoformat()}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out.rglob("*")):
            if f.is_file():
                z.write(f, Path("RobotArm") / f.relative_to(out))
    n = sum(1 for f in out.rglob("*") if f.is_file())
    mb = zp.stat().st_size / 1e6
    print(f"package: {n} files -> {out}\n         {zp} ({mb:.1f} MB)")
    if missing:
        print("not included (build them first):", ", ".join(missing))
    return 0


if __name__ == "__main__":
    main()
