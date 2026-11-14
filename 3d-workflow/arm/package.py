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

# What goes into app/ (paths relative to 3d-workflow, mirrored so the twin's relative links keep working)
INCLUDE = ["control", "design/cad", "design/drawings", "design/schematics", "design/png", "design/BOM.md", "design/design.json",
           "fab", "print/plates", "print/stl", "print/profiles", "print/REPORT.md", "print/manifest.json", "docs"]
SKIP = {"__pycache__", ".pytest_cache", "window", "server.log", "server.err.log"}

README = """Robot Arm desktop app
=====================

Install:   double-click "Install Robot Arm.vbs". It copies the app to %LOCALAPPDATA%\\Programs\\RobotArm,
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


def main(argv=None):
    from . import twin
    twin.write()                                   # arm_model.json + Library (control/lib)
    out = DIST / "RobotArm"
    if out.exists():
        shutil.rmtree(out)
    app = out / "app"
    missing = []
    for rel in INCLUDE:
        (_copy(HERE / rel, app / rel) if (HERE / rel).exists() else missing.append(rel))
    for f in DESKTOP.iterdir():
        if f.is_file():
            shutil.copy2(f, out / f.name)
    (out / "README.txt").write_text(README.format(date=date.today().isoformat()), encoding="utf-8")
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
