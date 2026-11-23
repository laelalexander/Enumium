"""Build the design library's data files from the upstream sources.

Run from the pyslate/ folder:

    git clone --depth 1 https://github.com/game-icons/icons.git /tmp/game-icons
    git clone --depth 1 --filter=blob:none --sparse https://github.com/nasa/NASA-3D-Resources.git /tmp/nasa3d
    (cd /tmp/nasa3d && git sparse-checkout set "3D Printing")
    python tools/build_library.py --game-icons /tmp/game-icons --nasa /tmp/nasa3d

Only sources whose licence allows redistribution and commercial use are imported.
Each record keeps its source, author and licence so the site can credit it.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DATA = HERE / "pyslate" / "library" / "data"
THUMBS = HERE / "pyslate" / "static" / "library"

# ------------------------------------------------------------------ game-icons.net

def _authors(license_txt: str) -> dict[str, dict]:
    """Folder name -> {name, url, cc0} from game-icons' license.txt."""
    out = {}
    for line in license_txt.splitlines():
        m = re.match(r"- ([^,]+?)(?:, (https?://\S+))?(?: - (CC0))?\s*$", line.strip())
        if not m:
            continue
        name = m.group(1).strip()
        cc0 = bool(m.group(3))
        if name.endswith(" - CC0"):
            name, cc0 = name[:-6], True
        folder = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        out[folder] = {"name": name, "url": m.group(2) or "", "cc0": cc0}
    return out


def flatten_svg_path(d: str, step: float = 3.0, tol: float = 0.6) -> list[list[tuple[float, float]]]:
    """Turn an SVG path into closed polylines in the icon's 512-unit space."""
    from shapely.geometry import LineString
    from svgelements import Close, Line, Move, Path

    rings, cur = [], []
    for seg in Path(d):
        if isinstance(seg, Move):
            if len(cur) > 2:
                rings.append(cur)
            cur = [(seg.end.x, seg.end.y)]
        elif isinstance(seg, (Line, Close)):
            if seg.end is not None:
                cur.append((seg.end.x, seg.end.y))
        else:
            n = max(2, int(seg.length(error=1e-2) / step))
            for k in range(1, n + 1):
                p = seg.point(k / n)
                cur.append((p.x, p.y))
    if len(cur) > 2:
        rings.append(cur)
    out = []
    for r in rings:
        ls = LineString(r).simplify(tol)
        pts = [(round(x, 1), round(y, 1)) for x, y in ls.coords]
        if len(pts) > 2 and LineString(pts + [pts[0]]).length > 6:
            out.append(pts)
    return out


def build_game_icons(src: Path) -> None:
    authors = _authors((src / "license.txt").read_text())
    rev = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    icons = []
    for svg in sorted(src.glob("*/*.svg")):
        folder = svg.parent.name
        if folder in ("badges",):
            continue
        text = svg.read_text()
        paths = re.findall(r'<path[^>]*?d="([^"]+)"', text)
        body = [d for d in paths if d.strip() not in ("M0 0h512v512H0z",)]
        if not body:
            continue
        rings = []
        for d in body:
            rings += flatten_svg_path(d)
        if not rings or len(rings) > 190 or sum(len(r) for r in rings) > 12000:
            continue
        a = authors.get(folder, {"name": folder.replace("-", " ").title(), "url": "", "cc0": False})
        icons.append({
            "slug": f"{svg.stem}-{folder}" if any(i["slug"] == svg.stem for i in icons) else svg.stem,
            "name": svg.stem.replace("-", " "),
            "folder": folder,
            "author": a["name"],
            "author_url": a["url"],
            "license": "cc0" if a["cc0"] else "cc-by-3.0",
            # Rings as "x y x y ..." in the 512-unit icon space, joined by "|". Decoded on demand.
            "rings": "|".join(" ".join(f"{c:g}" for p in r for c in p) for r in rings),
        })
    payload = {"source": "game-icons", "revision": rev, "count": len(icons), "icons": icons}
    DATA.mkdir(parents=True, exist_ok=True)
    with gzip.open(DATA / "game-icons.json.gz", "wt", compresslevel=9) as fh:
        json.dump(payload, fh, separators=(",", ":"))
    print(f"game-icons: {len(icons)} icons at {rev[:10]}")


# ------------------------------------------------------------------ NASA 3D Resources

NASA_SKIP = re.compile(r"insignia|emblem|medallion|logo|meatball|worm", re.I)
NASA_RAW = "https://raw.githubusercontent.com/nasa/NASA-3D-Resources/{rev}/3D%20Printing/{path}"


def render_thumb(stl: Path, target: Path, size: int = 360) -> None:
    """Flat-shaded picture of a mesh, drawn back to front with Pillow."""
    import numpy as np
    import trimesh
    from PIL import Image, ImageDraw

    mesh = trimesh.load(stl, force="mesh")
    if len(mesh.faces) > 250_000:
        idx = np.random.default_rng(0).choice(len(mesh.faces), 250_000, replace=False)
        mesh = trimesh.Trimesh(mesh.vertices, mesh.faces[idx], process=False)
    v = mesh.vertices - mesh.bounds.mean(axis=0)
    # Iso-style view: turn 35 degrees about z, then tilt 30 degrees towards the viewer.
    az, el = np.radians(35), np.radians(-60)
    rz = np.array([[np.cos(az), -np.sin(az), 0], [np.sin(az), np.cos(az), 0], [0, 0, 1]])
    rx = np.array([[1, 0, 0], [0, np.cos(el), -np.sin(el)], [0, np.sin(el), np.cos(el)]])
    v = v @ rz.T @ rx.T
    tri = v[mesh.faces]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    norm = np.linalg.norm(normals, axis=1)
    keep = norm > 0
    tri, normals = tri[keep], normals[keep] / norm[keep, None]
    light = np.array([0.35, 0.45, 0.82])
    light /= np.linalg.norm(light)
    shade = np.clip(np.abs(normals @ light), 0.15, 1.0)
    order = np.argsort(tri[:, :, 2].mean(axis=1))
    span = max(np.ptp(v[:, 0]), np.ptp(v[:, 1])) or 1
    scale = size * 0.86 / span
    xy = tri[:, :, :2] * scale
    xy[:, :, 1] *= -1
    xy += size / 2
    img = Image.new("RGB", (size, size), (246, 244, 240))
    draw = ImageDraw.Draw(img)
    base = np.array([255, 140, 60])
    for i in order:
        c = tuple(int(x) for x in base * (0.35 + 0.65 * shade[i]))
        draw.polygon([tuple(p) for p in xy[i]], fill=c)
    target.parent.mkdir(parents=True, exist_ok=True)
    img.save(target, "WEBP", quality=80)


def build_nasa(src: Path, thumbs: bool = True) -> None:
    import trimesh

    rev = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    root = src / "3D Printing"
    models = []
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        if NASA_SKIP.search(folder.name):
            continue
        stls = sorted(folder.rglob("*.stl"), key=lambda p: -p.stat().st_size) + sorted(folder.rglob("*.STL"), key=lambda p: -p.stat().st_size)
        stls = list(dict.fromkeys(stls))
        if not stls:
            continue
        slug = "nasa-" + re.sub(r"[^a-z0-9]+", "-", folder.name.lower()).strip("-")
        files = []
        for f in stls:
            rel = f.relative_to(root).as_posix()
            files.append({"name": f.name, "bytes": f.stat().st_size,
                          "url": NASA_RAW.format(rev=rev, path="/".join(_q(p) for p in rel.split("/")))})
        main = stls[0]
        try:
            m = trimesh.load(main, force="mesh")
            ext = [round(float(x), 1) for x in m.extents]
        except Exception:  # noqa: BLE001 - a bad upstream file is skipped, not fatal
            continue
        if thumbs:
            render_thumb(main, THUMBS / "nasa" / f"{slug}.webp")
        models.append({"slug": slug, "title": folder.name, "files": files, "extents_mm": ext})
        print(f"  {slug}: {len(files)} files, {ext}")
    payload = {"source": "nasa-3d", "revision": rev, "count": len(models), "models": models}
    (DATA / "nasa-3d.json").write_text(json.dumps(payload, indent=1))
    print(f"nasa-3d: {len(models)} models at {rev[:10]}")


def _q(part: str) -> str:
    from urllib.parse import quote

    return quote(part)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game-icons", type=Path)
    ap.add_argument("--nasa", type=Path)
    ap.add_argument("--no-thumbs", action="store_true")
    args = ap.parse_args()
    if args.game_icons:
        build_game_icons(args.game_icons)
    if args.nasa:
        build_nasa(args.nasa, thumbs=not args.no_thumbs)


if __name__ == "__main__":
    main()
