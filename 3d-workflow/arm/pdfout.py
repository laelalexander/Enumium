"""HTML -> PDF with whatever is on the machine: Node + Playwright (tools/html2pdf.js), Python Playwright,
or a headless Microsoft Edge / Chrome / Chromium (always present on Windows). The page's @page rule sets size and margins."""
import os, shutil, subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


def _browsers():
    cands = [os.path.expandvars(p) for p in (r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
                                             r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
                                             r"%ProgramFiles%\Google\Chrome\Application\chrome.exe")]
    cands += [shutil.which(n) for n in ("msedge", "google-chrome", "chromium", "chromium-browser")] + ["/opt/pw-browsers/chromium"]
    return [c for c in cands if c and Path(c).is_file()]


def html_to_pdf(html, pdf, landscape=False):
    html, pdf = Path(html).resolve(), Path(pdf).resolve()
    js = HERE / "tools" / "html2pdf.js"
    try:
        if js.exists() and subprocess.run(["node", str(js), str(html), str(pdf), "landscape" if landscape else "portrait"],
                                          capture_output=True, timeout=300).returncode == 0:
            return "node playwright"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(); pg = b.new_page(); pg.goto(html.as_uri())
            pg.pdf(path=str(pdf), prefer_css_page_size=True, print_background=True); b.close()
        return "python playwright"
    except Exception:
        pass
    for exe in _browsers():
        try:
            r = subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
                                f"--print-to-pdf={pdf}", html.as_uri()], capture_output=True, timeout=300)
            if r.returncode == 0 and pdf.exists():
                return Path(exe).stem
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None
