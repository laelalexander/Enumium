"""Render every design SVG (drawings + schematics) to PNG in design/png/.  python -m arm.render

Backends, tried in order:
  1. cairosvg  (pip install cairosvg; on Windows it also needs the Cairo DLL, see docs/design/README.md)
  2. Inkscape  (inkscape on PATH, or the default Windows install folder)
  3. Playwright Chromium  (pip install playwright && python -m playwright install chromium)
Rendering is optional: the SVGs are the source drawings and open in any browser."""
import os, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DESIGN = HERE / "design"
WIDTH = 2400  # px; A3 sheets are 1600x1131 user units, so this is 1.5x


def sources():
    return sorted([*(DESIGN / "drawings").glob("*.svg"), *(DESIGN / "schematics").glob("*.svg")])


def _cairosvg():
    import cairosvg  # raises ImportError or OSError (missing Cairo DLL on Windows)
    def run(src, dst):
        cairosvg.svg2png(url=str(src), write_to=str(dst), output_width=WIDTH, background_color="white")
    return run


def _inkscape():
    exe = shutil.which("inkscape")
    if not exe and os.name == "nt":
        for base in (os.environ.get("ProgramFiles", r"C:\Program Files"), os.environ.get("ProgramFiles(x86)", "")):
            cand = Path(base) / "Inkscape" / "bin" / "inkscape.exe"
            if base and cand.exists():
                exe = str(cand)
                break
    if not exe:
        raise FileNotFoundError("inkscape not found")
    def run(src, dst):
        subprocess.run([exe, str(src), "--export-type=png", f"--export-filename={dst}",
                        f"--export-width={WIDTH}", "--export-background=white"],
                       check=True, capture_output=True)
    return run


def _playwright():
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch()
    page = browser.new_page(device_scale_factor=WIDTH / 1600)
    def run(src, dst):
        page.set_viewport_size({"width": 1600, "height": 1131})
        page.goto(src.resolve().as_uri())
        page.screenshot(path=str(dst), full_page=False)
    run.close = lambda: (browser.close(), pw.stop())
    return run


def main(argv=None):
    out = DESIGN / "png"
    out.mkdir(parents=True, exist_ok=True)
    srcs = sources()
    if not srcs:
        sys.exit("no SVGs in design/; run `python run.py build` first")
    errors = []
    for name, factory in (("cairosvg", _cairosvg), ("inkscape", _inkscape), ("playwright", _playwright)):
        try:
            run = factory()
        except Exception as e:  # backend unavailable, try the next one
            errors.append(f"{name}: {e.__class__.__name__}: {e}".splitlines()[0])
            continue
        try:
            for s in srcs:
                run(s, out / f"{s.stem}.png")
        finally:
            getattr(run, "close", lambda: None)()
        print(f"rendered {len(srcs)} PNGs to {out} with {name}")
        return True
    print("PNG rendering skipped: no backend available.\n  " + "\n  ".join(errors) +
          "\n  The SVG drawings are complete; see docs/design/README.md to enable PNG export.")
    return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
