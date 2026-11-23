"""Pyslate originals: designs the shop draws itself, from code.

Pyslate owns these outright, so customers can make, sell and change them freely.
Every generator returns studio shapes (see shapes.py). Sizes are in millimetres
and drawn without kerf compensation; the shop adjusts for kerf at the machine.
"""

from __future__ import annotations

import math
import random

from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import linemerge, unary_union

from . import shapes as S

GAP = 4.0  # space between parts when a design is laid out flat


# ---------------------------------------------------------------- finger-joint boxes

# Faces: (fixed axis, side) -> panel. Axes: 0 = x (width), 1 = y (depth), 2 = z (height).
# Side walls win corner cubes over front/back, which win over top/bottom.
_PRIORITY = {0: 3, 1: 2, 2: 1}


def _odd_count(length: float, finger: float) -> int:
    n = max(3, int(round(length / finger)))
    return n if n % 2 else n + 1


def _panel(dims, axis, side, faces, t, finger, holes=()):
    """Outline of one panel of a box laid flat, as a shapely polygon in its own (u, v) plane."""
    u_ax, v_ax = [a for a in (0, 1, 2) if a != axis]
    lu, lv = dims[u_ax], dims[v_ax]
    me = _PRIORITY[axis]
    parts = [box(t, t, lu - t, lv - t)]

    def owner(edge_axis, edge_side):
        return (edge_axis, edge_side) in faces

    # Edge strips. An edge at u = 0 / lu meets the panel whose fixed axis is u_ax.
    for e_axis, e_side, along, span in ((u_ax, 0, v_ax, lv), (u_ax, 1, v_ax, lv), (v_ax, 0, u_ax, lu), (v_ax, 1, u_ax, lu)):
        n = _odd_count(span - 2 * t, finger)
        seg = (span - 2 * t) / n
        present = owner(e_axis, e_side)
        mine_even = not present or me > _PRIORITY[e_axis]
        for k in range(n):
            if not present or (k % 2 == 0) == mine_even:
                a0, a1 = t + k * seg, t + (k + 1) * seg
                if e_axis == u_ax:  # strip along v at u = 0 or lu
                    u0 = 0 if e_side == 0 else lu - t
                    parts.append(box(u0, a0, u0 + t, a1))
                else:
                    v0 = 0 if e_side == 0 else lv - t
                    parts.append(box(a0, v0, a1, v0 + t))
    # Corner squares belong to the highest-priority panel present at that corner.
    for su in (0, 1):
        for sv in (0, 1):
            others = [_PRIORITY[a] for a, s in ((u_ax, su), (v_ax, sv)) if owner(a, s)]
            if all(me > p for p in others):
                u0 = 0 if su == 0 else lu - t
                v0 = 0 if sv == 0 else lv - t
                parts.append(box(u0, v0, u0 + t, v0 + t))
    poly = unary_union(parts).buffer(0.01, join_style=2).buffer(-0.01, join_style=2)
    for h in holes:
        poly = poly.difference(h)
    return poly


def _layout(polys, max_w=None):
    """Shelf-pack polygons left to right, top to bottom, to fit the M2 bed, else the X1 bed."""
    if max_w is None:
        for w in (416.0, 605.0):
            placed = _layout(polys, w)
            if unary_union(placed).bounds[3] <= 310:
                return placed
        return placed
    placed, x, y, row_h = [], 0.0, 0.0, 0.0
    for p in sorted(polys, key=lambda q: -(q.bounds[3] - q.bounds[1])):
        minx, miny, maxx, maxy = p.bounds
        w, h = maxx - minx, maxy - miny
        if x > 0 and x + w > max_w:
            x, y, row_h = 0.0, y + row_h + GAP, 0.0
        placed.append(affinity.translate(p, x - minx, y - miny))
        x += w + GAP
        row_h = max(row_h, h)
    return placed


def finger_box(w, d, h, t=3.0, top=True, finger=None, lid_hole=None):
    """A box with finger joints on every edge. w, d, h are outside sizes."""
    finger = finger or max(8.0, min(20.0, min(w, d, h) / 5))
    dims = (w, d, h)
    faces = {(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)}
    if top:
        faces.add((2, 1))
    polys = []
    for axis, side in sorted(faces):
        holes = []
        if lid_hole and (axis, side) == (2, 1):
            hw, hh = lid_hole
            holes.append(box(w / 2 - hw / 2, d / 2 - hh / 2, w / 2 + hw / 2, d / 2 + hh / 2)
                         if hw != hh else Point(w / 2, d / 2).buffer(hw / 2, 48))
            if hw > 2 * hh:
                holes = [affinity.scale(Point(w / 2, d / 2).buffer(hh / 2, 32), hw / hh, 1)]
        polys.append(_panel(dims, axis, side, faces, t, finger, holes))
    out = []
    for p in _layout(polys):
        out += S.polygon_paths(p)
    return S.centre(out)


def divided_tray(w, d, h, cells, t=3.0):
    """An open tray with slotted dividers across its width."""
    shapes = finger_box(w, d, h, t, top=False)
    x0, y0, x1, y1 = S.bounds(shapes)
    pitch = (w - 2 * t) / cells
    inner_d = d - 2 * t
    divs = []
    for _ in range(cells - 1):
        divs.append(box(0, 0, inner_d, h - t))
    placed = []
    x = x0
    for p in divs:
        placed.append(affinity.translate(p, x, y1 + GAP))
        x += inner_d + GAP
    for p in placed:
        shapes += S.polygon_paths(p)
    _ = pitch
    return shapes


# ---------------------------------------------------------------- flat goods

def _circle(r, n=96):
    return Point(0, 0).buffer(r, n // 4)


def _rpoly(n, r, rot=-90):
    return Polygon([(r * math.cos(math.radians(rot + 360 * k / n)), r * math.sin(math.radians(rot + 360 * k / n)))
                    for k in range(n)])


def _star(n, r_out, r_in, rot=-90):
    pts = []
    for k in range(2 * n):
        r = r_out if k % 2 == 0 else r_in
        a = math.radians(rot + 180 * k / n)
        pts.append((r * math.cos(a), r * math.sin(a)))
    return Polygon(pts)


def _heart(size):
    pts = []
    for k in range(160):
        a = 2 * math.pi * k / 160
        x = 16 * math.sin(a) ** 3
        y = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((x * size / 34, y * size / 34))
    return Polygon(pts)


def _engraved_lines(lines):
    return [S.path(list(l.coords), closed=False, engrave=True) for l in lines]


def coaster(shape="round", pattern="rings", size=95.0, seed=0):
    r = size / 2
    blank = {"round": _circle(r), "square": box(-r, -r, r, r).buffer(6).buffer(-6) if False else box(-r, -r, r, r),
             "hexagon": _rpoly(6, r, 0)}[shape]
    if shape == "square":
        blank = box(-r + 6, -r + 6, r - 6, r - 6).buffer(6, 16)
    out = S.polygon_paths(blank)
    inner = blank.buffer(-6)
    if pattern == "rings":
        for k in range(1, 6):
            ring = blank.buffer(-6 * k).exterior
            if ring.length > 0:
                out += _engraved_lines([ring])
    elif pattern == "sunburst":
        lines = [LineString([(0, 0), (r * 1.5 * math.cos(2 * math.pi * k / 36), r * 1.5 * math.sin(2 * math.pi * k / 36))])
                 .intersection(inner).difference(_circle(r * 0.18)) for k in range(36)]
        out += _engraved_lines([l for l in lines if not l.is_empty and l.geom_type == "LineString"])
        out.append(S.ring(0, 0, r * 0.36))
    elif pattern == "hexgrid":
        cell, cells = 9.0, []
        for i in range(-8, 9):
            for j in range(-8, 9):
                cx = i * cell * 1.5
                cy = j * cell * math.sqrt(3) + (i % 2) * cell * math.sqrt(3) / 2
                hx = affinity.translate(_rpoly(6, cell * 0.92, 0), cx, cy)
                if inner.contains(hx):
                    cells.append(hx)
        out += _engraved_lines([c.exterior for c in cells])
    elif pattern == "mandala":
        out += mandala_lines((r * math.cos(math.pi / 6) if shape == "hexagon" else r) - 8, seed)
    return S.centre(out)


def mandala_lines(r, seed):
    rnd = random.Random(seed)
    folds = rnd.choice([8, 10, 12, 16])
    out = []
    radii = sorted(rnd.uniform(0.15, 0.95) * r for _ in range(4)) + [r]
    out.append(S.ring(0, 0, radii[0] * 2))
    prev = radii[0]
    for rr in radii[1:]:
        kind = rnd.choice(["petal", "arc", "spike", "dots"])
        for k in range(folds):
            a = 2 * math.pi * k / folds
            if kind == "petal":
                pts = []
                for i in range(25):
                    tt = i / 24
                    rad = prev + (rr - prev) * math.sin(math.pi * tt) * 0.98 if False else prev + (rr - prev) * tt
                    spread = math.sin(math.pi * tt) * math.pi / folds * 0.9
                    pts.append((rad * math.cos(a - spread), rad * math.sin(a - spread)))
                back = [(rad2 * math.cos(a + (sp)), rad2 * math.sin(a + sp)) for rad2, sp in
                        ((prev + (rr - prev) * (i / 24), math.sin(math.pi * i / 24) * math.pi / folds * 0.9) for i in range(24, -1, -1))]
                out.append(S.path(pts + back[1:-1], closed=True, engrave=True))
            elif kind == "arc":
                mid = (prev + rr) / 2
                pts = [(mid * math.cos(a + math.pi / folds * (i / 10 - 1)) + 0, mid * math.sin(a + math.pi / folds * (i / 10 - 1)))
                       for i in range(21)]
                pts = [(x * (1 + 0.12 * math.sin(math.pi * i / 20)), y * (1 + 0.12 * math.sin(math.pi * i / 20)))
                       for i, (x, y) in enumerate(pts)]
                out.append(S.path(pts, closed=False, engrave=True))
            elif kind == "spike":
                b1 = (prev * math.cos(a - math.pi / folds), prev * math.sin(a - math.pi / folds))
                tip = (rr * 0.97 * math.cos(a), rr * 0.97 * math.sin(a))
                b2 = (prev * math.cos(a + math.pi / folds), prev * math.sin(a + math.pi / folds))
                out.append(S.path([b1, tip, b2], closed=False, engrave=True))
            else:
                mid = (prev + rr) / 2
                d = min((rr - prev) * 0.6, 2 * math.pi * mid / folds * 0.5)
                if d > 1:
                    out.append(S.ring(mid * math.cos(a), mid * math.sin(a), d, seg=32))
        out.append(S.ring(0, 0, rr * 2))
        prev = rr
    return out


def snowflake(seed, size=90.0, hole=True):
    rnd = random.Random(seed)
    r = size / 2
    w = rnd.uniform(2.6, 3.6)
    arm = [LineString([(0, 0), (r, 0)])]
    for _ in range(rnd.randint(2, 4)):
        p = rnd.uniform(0.25, 0.85) * r
        ln = rnd.uniform(0.15, 0.4) * r * (1.1 - p / r)
        ang = math.radians(rnd.choice([45, 60, 60, 50]))
        for sgn in (1, -1):
            arm.append(LineString([(p, 0), (p + ln * math.cos(ang), sgn * ln * math.sin(ang))]))
    if rnd.random() < 0.6:
        hx = affinity.translate(_rpoly(6, r * rnd.uniform(0.12, 0.22), 0), r * rnd.uniform(0.35, 0.6), 0)
        arm.append(hx.exterior)
    arm_shape = unary_union([g.buffer(w / 2, 8) for g in arm])
    flake = unary_union([affinity.rotate(arm_shape, 60 * k, origin=(0, 0)) for k in range(6)])
    flake = unary_union([flake, _rpoly(6, r * rnd.uniform(0.12, 0.2), 0)])
    flake = affinity.rotate(flake, 90, origin=(0, 0))
    tip = r + w / 2
    if hole:
        flake = unary_union([flake, Point(0, -tip - 3).buffer(5, 24)]).difference(Point(0, -tip - 3).buffer(2, 24))
    flake = flake.simplify(0.05)
    return S.centre(S.polygon_paths(flake))


def ornament(kind, size=80.0, seed=0):
    r = size / 2
    body = {"star": _star(5, r, r * 0.45), "heart": _heart(size), "circle": _circle(r),
            "bell": None, "tree": None, "hexagon": _rpoly(6, r, 0)}[kind] if kind not in ("bell", "tree") else None
    if kind == "tree":
        body = unary_union([Polygon([(0, -r), (r * 0.5, -r * 0.3), (-r * 0.5, -r * 0.3)]),
                            Polygon([(0, -r * 0.6), (r * 0.7, r * 0.3), (-r * 0.7, r * 0.3)]),
                            Polygon([(0, -r * 0.2), (r * 0.9, r * 0.8), (-r * 0.9, r * 0.8)]),
                            box(-r * 0.12, r * 0.75, r * 0.12, r)])
    if kind == "bell":
        pts = [(r * 0.55 * math.sin(math.pi * k / 40) * (0.5 + 0.5 * k / 40) + 0, -r + 2 * r * k / 40) for k in range(41)]
        right = [(x + r * 0.2 * (k / 40) ** 3, y) for k, (x, y) in enumerate(pts)]
        body = Polygon([(r * 0.08, -r)] + right[1:] + [(-x, y) for x, y in reversed(right[1:])] + [(-r * 0.08, -r)])
        body = unary_union([body.buffer(1), Point(0, r).buffer(r * 0.15)])
    top = body.bounds[1]
    tab = Point(0, top - 2).buffer(5.5, 24)
    shape = unary_union([body, tab]).difference(Point(0, top - 2).buffer(2.2, 24))
    out = S.polygon_paths(shape.simplify(0.05))
    if kind in ("circle", "hexagon"):
        out += mandala_lines(r * (0.72 if kind == "hexagon" else 0.8), seed)
    return S.centre(out)


def keychain(kind, size=40.0):
    r = size / 2
    body = {"round": _circle(r), "square": box(-r + 4, -r + 4, r - 4, r - 4).buffer(4, 12),
            "hexagon": _rpoly(6, r, 0), "heart": _heart(size * 1.1), "shield": None, "tag": None}.get(kind)
    if kind == "shield":
        body = Polygon([(-r, -r), (r, -r), (r, 0)] + [(r * math.cos(a), r * 0.2 + r * 0.8 * math.sin(a)) for a in
                       [math.pi * k / 20 for k in range(1, 20)]] + [(-r, 0)])
    if kind == "tag":
        body = box(-r * 1.4 + 5, -r * 0.7 + 5, r * 1.4 - 5, r * 0.7 - 5).buffer(5, 12)
    minx, miny, maxx, maxy = body.bounds
    hole_y = miny + 5.5
    hx, hy = (0, hole_y) if kind not in ("tag", "heart") else ((minx + 6, 0) if kind == "tag" else (-size * 0.26, miny + 9))
    shape = body.difference(Point(hx, hy).buffer(2.5, 24))
    return S.centre(S.polygon_paths(shape))


def bookmark(pattern, seed=0):
    w, h = 40.0, 150.0
    body = box(0, 0, w, h).buffer(0)
    body = box(4, 4, w - 4, h - 4).buffer(4, 12)
    body = body.difference(Point(w / 2, 10).buffer(2.5, 24))
    cut = []
    rnd = random.Random(seed)
    if pattern == "lattice":
        for j in range(8):
            for i in range(2):
                cut.append(affinity.translate(_rpoly(4, 6.5, 0), 11 + i * 18 + (j % 2) * 0, 30 + j * 14))
    elif pattern == "leaves":
        for j in range(6):
            leaf = affinity.scale(_circle(6, 48), 0.5, 1.4)
            leaf = affinity.rotate(leaf, 30 if j % 2 else -30)
            cut.append(affinity.translate(leaf, w / 2 + (6 if j % 2 else -6), 32 + j * 18))
    elif pattern == "stars":
        for j in range(7):
            cut.append(affinity.translate(_star(5, rnd.uniform(4, 6.5), 2.4), w / 2 + rnd.uniform(-8, 8), 28 + j * 16))
    elif pattern == "waves":
        for j in range(9):
            ln = LineString([(8 + x, 28 + j * 12 + 3 * math.sin(x / 4)) for x in range(0, 25)])
            cut.append(ln.buffer(1.4, 8))
    body = body.difference(unary_union(cut))
    return S.centre(S.polygon_paths(body))


def plant_marker(width=25.0, length=150.0):
    w = width
    head = box(0, 0, w * 2.4, w).buffer(3, 8)
    stake = Polygon([(w * 0.9, w), (w * 1.5, w), (w * 1.2, length)])
    return S.centre(S.polygon_paths(unary_union([head, stake]).simplify(0.05)))


def maze(seed, cells=12, cell=8.0):
    rnd = random.Random(seed)
    n = cells
    visited = [[False] * n for _ in range(n)]
    walls_h = [[True] * n for _ in range(n + 1)]  # horizontal walls above row j
    walls_v = [[True] * (n + 1) for _ in range(n)]  # vertical walls left of col i
    stack = [(0, 0)]
    visited[0][0] = True
    while stack:
        i, j = stack[-1]
        nbrs = [(i + di, j + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= i + di < n and 0 <= j + dj < n
                and not visited[j + dj][i + di]]
        if not nbrs:
            stack.pop()
            continue
        ni, nj = rnd.choice(nbrs)
        if ni != i:
            walls_v[j][max(i, ni)] = False
        else:
            walls_h[max(j, nj)][i] = False
        visited[nj][ni] = True
        stack.append((ni, nj))
    walls_v[0][0] = False
    walls_v[n - 1][n] = False
    m = 8.0
    segs = []
    for j in range(n + 1):
        run = None
        for i in range(n + 1):
            if i < n and walls_h[j][i]:
                run = run if run is not None else i
            elif run is not None:
                segs.append([(m + run * cell, m + j * cell), (m + i * cell, m + j * cell)])
                run = None
    for i in range(n + 1):
        run = None
        for j in range(n + 1):
            if j < n and walls_v[j][i]:
                run = run if run is not None else j
            elif run is not None:
                segs.append([(m + i * cell, m + run * cell), (m + i * cell, m + j * cell)])
                run = None
    size = n * cell + 2 * m
    out = S.polygon_paths(box(4, 4, size - 4, size - 4).buffer(4, 12))
    merged = linemerge([LineString(sg) for sg in segs])
    lines = list(getattr(merged, "geoms", [merged]))
    out += [S.path(list(l.coords), closed=False, engrave=True) for l in lines]
    return S.centre(out)


def jigsaw(cols, rows, piece=40.0, seed=0):
    rnd = random.Random(seed)
    w, h = cols * piece, rows * piece

    def edge(p0, p1, flip):
        (x0, y0), (x1, y1) = p0, p1
        dx, dy = x1 - x0, y1 - y0
        nx, ny = -dy, dx
        pts = []
        prof = [(0, 0), (0.35, 0), (0.37, 0.05), (0.33, 0.15), (0.35, 0.24), (0.5, 0.3), (0.65, 0.24), (0.67, 0.15),
                (0.63, 0.05), (0.65, 0), (1, 0)]
        jit = rnd.uniform(-0.04, 0.04)
        for t, o in prof:
            t2 = t + (jit if 0 < t < 1 else 0)
            o2 = o * flip
            pts.append((x0 + dx * t2 + nx * o2, y0 + dy * t2 + ny * o2))
        return LineString(pts).buffer(0.001) and LineString(_smooth(pts))

    out = S.polygon_paths(box(0, 0, w, h))
    for i in range(1, cols):
        segs = []
        for j in range(rows):
            segs += list(edge((i * piece, j * piece), (i * piece, (j + 1) * piece), rnd.choice((-1, 1))).coords)
        out.append(S.path(segs, closed=False))
    for j in range(1, rows):
        segs = []
        for i in range(cols):
            segs += list(edge((i * piece, j * piece), ((i + 1) * piece, j * piece), rnd.choice((-1, 1))).coords)
        out.append(S.path(segs, closed=False))
    return S.centre(out)


def _smooth(pts, n=6):
    """Catmull-Rom through the points."""
    out = []
    p = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[c] + (-p0[c] + p2[c]) * t + (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2
                                    + (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    out.append(pts[-1])
    return out


def gear(teeth, module=2.5, bore=6.0):
    pitch_r = teeth * module / 2
    outer = pitch_r + module
    root = pitch_r - 1.25 * module
    pts = []
    for k in range(teeth):
        base = 2 * math.pi * k / teeth
        step = 2 * math.pi / teeth
        for frac, rad in ((0.0, root), (0.18, root), (0.3, outer), (0.5, outer), (0.62, root), (1.0, root)):
            a = base + step * frac
            pts.append((rad * math.cos(a), rad * math.sin(a)))
    g = Polygon(pts).buffer(0.4, 8).buffer(-0.4, 8).difference(_circle(bore / 2, 48))
    if teeth >= 24:
        for k in range(5):
            a = 2 * math.pi * k / 5
            g = g.difference(Point((root * 0.55) * math.cos(a), (root * 0.55) * math.sin(a)).buffer(root * 0.22, 24))
    return S.centre(S.polygon_paths(g.simplify(0.03)))


def tangram(size=150.0):
    """The classic seven tangram pieces on a square, as cut lines."""
    q = size / 4
    pieces = [
        [(0, 0), (4 * q, 0), (2 * q, 2 * q)],                    # large triangle
        [(0, 0), (2 * q, 2 * q), (0, 4 * q)],                    # large triangle
        [(4 * q, 2 * q), (4 * q, 4 * q), (2 * q, 4 * q)],        # medium triangle
        [(4 * q, 0), (4 * q, 2 * q), (3 * q, q)],                # small triangle
        [(2 * q, 2 * q), (3 * q, q), (4 * q, 2 * q), (3 * q, 3 * q)],  # square
        [(q, 3 * q), (2 * q, 2 * q), (3 * q, 3 * q)],            # small triangle
        [(0, 4 * q), (q, 3 * q), (3 * q, 3 * q), (2 * q, 4 * q)],  # parallelogram
    ]
    inner = unary_union([Polygon(p).boundary for p in pieces]).difference(box(0, 0, size, size).exterior.buffer(0.01))
    merged = linemerge(inner) if inner.geom_type != "LineString" else inner
    out = S.polygon_paths(box(0, 0, size, size))
    out += [S.path(list(l.coords), closed=False) for l in getattr(merged, "geoms", [merged])]
    return S.centre(out)


def tic_tac_toe(size=150.0):
    s = size
    out = S.polygon_paths(box(6, 6, s - 6, s - 6).buffer(6, 12))
    m = 15
    for k in (1, 2):
        x = m + (s - 2 * m) * k / 3
        out.append(S.path([(x, m), (x, s - m)], closed=False, engrave=True))
        out.append(S.path([(m, x), (s - m, x)], closed=False, engrave=True))
    pieces = []
    for k in range(5):
        x = affinity.rotate(unary_union([box(-15, -3.5, 15, 3.5), box(-3.5, -15, 3.5, 15)]), 45)
        pieces.append(affinity.translate(x, s + 25 + (k % 3) * 38, 22 + (k // 3) * 38))
        o = _circle(14).difference(_circle(8))
        pieces.append(affinity.translate(o, s + 25 + (k % 3) * 38, 22 + 76 + (k // 3) * 38))
    for p in pieces:
        out += S.polygon_paths(p)
    return S.centre(out)


def picture_frame(photo_w, photo_h, border=25.0):
    W, H = photo_w + 2 * border, photo_h + 2 * border
    front = box(0, 0, W, H).difference(box(border + 4, border + 4, W - border - 4, H - border - 4))
    back = affinity.translate(box(0, 0, W, H).difference(box(W / 2 - 15, H * 0.4, W / 2 + 15, H * 0.4 + 6)), W + GAP, 0)
    stand = affinity.translate(Polygon([(0, 0), (30, 0), (24, H * 0.6), (6, H * 0.6)]), 2 * W + 2 * GAP, 0)
    out = []
    for p in (front, back, stand):
        out += S.polygon_paths(p)
    return S.centre(out)


def clock_face(size=250.0, style="ticks"):
    r = size / 2
    out = S.polygon_paths(_circle(r).difference(_circle(4.5, 32)))
    for k in range(60):
        a = 2 * math.pi * k / 60
        ln = 14 if k % 5 == 0 else 6
        if style == "dots" and k % 5:
            continue
        p0 = ((r - 10) * math.cos(a), (r - 10) * math.sin(a))
        p1 = ((r - 10 - ln) * math.cos(a), (r - 10 - ln) * math.sin(a))
        out.append(S.path([p0, p1], closed=False, engrave=True))
    if style == "numbers":
        for h in range(1, 13):
            a = math.radians(h * 30 - 90)
            out.append({"type": "text", "x": S.r2((r - 40) * math.cos(a)), "y": S.r2((r - 40) * math.sin(a)),
                        "text": str(h), "size": 18, "font": "sans", "engrave": True, "rot": 0})
    return S.centre(out)


def sign(text, w=300.0, h=100.0, font="sans"):
    out = S.polygon_paths(box(10, 10, w - 10, h - 10).buffer(10, 12).difference(
        unary_union([Point(18, h / 2).buffer(2.5, 24), Point(w - 18, h / 2).buffer(2.5, 24)])))
    out.append({"type": "text", "x": w / 2, "y": h / 2, "text": text, "size": h * 0.38, "font": font, "engrave": True, "rot": 0})
    return S.centre(out)


def phone_stand(t=3.0):
    # Two parts that slide together with a cross-lap joint.
    back = Polygon([(0, 0), (80, 0), (80, 10), (70, 10), (20, 110), (0, 110)])
    back = back.difference(box(30 - t / 2, 0, 30 + t / 2, 25)).difference(Point(15, 60).buffer(8, 24))
    lip = Polygon([(0, 0), (90, 0), (90, 30), (78, 30), (78, 12), (0, 12)]).difference(box(45 - t / 2, 6, 45 + t / 2, 12))
    out = []
    for p in _layout([back, lip]):
        out += S.polygon_paths(p)
    return S.centre(out)


def trivet(size=180.0, cell=14.0):
    r = size / 2
    blank = _rpoly(6, r, 0)
    inner = blank.buffer(-8)
    holes = []
    for i in range(-10, 11):
        for j in range(-10, 11):
            cx = i * cell * 1.5
            cy = j * cell * math.sqrt(3) + (i % 2) * cell * math.sqrt(3) / 2
            hx = affinity.translate(_rpoly(6, cell * 0.78, 0), cx, cy)
            if inner.contains(hx):
                holes.append(hx)
    return S.centre(S.polygon_paths(blank.difference(unary_union(holes))))


def wall_art_sunburst(size=300.0, rays=24):
    r = size / 2
    rays_geo = []
    for k in range(rays):
        a = 2 * math.pi * k / rays
        da = math.pi / rays * 0.55
        L = r if k % 2 == 0 else r * 0.72
        rays_geo.append(Polygon([(r * 0.2 * math.cos(a - da), r * 0.2 * math.sin(a - da)),
                                 (L * math.cos(a), L * math.sin(a)),
                                 (r * 0.2 * math.cos(a + da), r * 0.2 * math.sin(a + da))]))
    g = unary_union(rays_geo + [_circle(r * 0.26)]).difference(_circle(r * 0.16))
    return S.centre(S.polygon_paths(g))


def lantern(w=100.0, h=160.0, t=3.0, pattern="stars", seed=0):
    """An open-bottom lantern box with patterned windows on all four sides."""
    rnd = random.Random(seed)
    shapes = finger_box(w, w, h, t, top=False)
    # Add window cutouts to the four wall panels: find tall panels by bounds.
    out = []
    for s in shapes:
        out.append(s)
    x0, y0, x1, y1 = S.bounds(shapes)
    walls = [s for s in shapes if s["type"] == "path" and len(s["pts"]) > 8]
    for s in walls:
        xs = [p[0] for p in s["pts"]]
        ys = [p[1] for p in s["pts"]]
        pw, ph = max(xs) - min(xs), max(ys) - min(ys)
        if ph < h * 0.9 and pw < h * 0.9:
            continue
        tall = ph >= pw
        cx, cy = s["x"], s["y"]
        for k in range(6):
            if pattern == "stars":
                st = _star(5, rnd.uniform(6, 10), 3.5)
            else:
                st = _circle(rnd.uniform(4, 8), 32)
            ox = rnd.uniform(-0.28, 0.28) * (pw if tall else ph)
            oy = (k - 2.5) * (ph if tall else pw) * 0.13
            if not tall:
                ox, oy = oy, ox
            out += S.polygon_paths(affinity.translate(st, cx + ox, cy + oy))
    return out


# ---------------------------------------------------------------- catalogue of originals

def _box_entries():
    e = []
    for w, d, h, label in ((60, 60, 60, "Small cube box"), (100, 100, 100, "Cube box"), (150, 100, 70, "Keepsake box"),
                           (200, 140, 80, "Large storage box"), (120, 80, 50, "Jewellery box"), (95, 65, 30, "Business card box"),
                           (180, 100, 40, "Pencil box")):
        e.append((f"finger-box-{w}x{d}x{h}", label, "Boxes and storage", ["box", "finger joint", "lid", "storage"],
                  f"A {w} x {d} x {h} mm box with finger joints and a drop-in top. Made from 3 mm sheet.",
                  lambda w=w, d=d, h=h: finger_box(w, d, h)))
    for w, d, h, label in ((80, 80, 100, "Pencil cup"), (200, 120, 50, "Open tray"), (150, 150, 60, "Square catch-all tray"),
                           (300, 200, 60, "Large serving tray"), (100, 70, 70, "Desk organiser cup")):
        e.append((f"open-box-{w}x{d}x{h}", label, "Boxes and storage", ["box", "tray", "open top", "finger joint"],
                  f"An open-top {w} x {d} x {h} mm box with finger joints. Made from 3 mm sheet.",
                  lambda w=w, d=d, h=h: finger_box(w, d, h, top=False)))
    e.append(("coin-bank-box", "Coin bank", "Boxes and storage", ["box", "money", "kids"],
              "A 100 mm cube coin bank with a coin slot in the lid.", lambda: finger_box(100, 100, 100, lid_hole=(40, 4))))
    e.append(("tissue-box-cover", "Tissue box cover", "Boxes and storage", ["box", "bathroom", "home"],
              "A cover for a standard 240 x 125 mm tissue box, with an oval opening.",
              lambda: finger_box(250, 132, 95, lid_hole=(120, 40))))
    for cells in (2, 3, 4):
        e.append((f"divided-tray-{cells}", f"Divided tray, {cells} compartments", "Boxes and storage",
                  ["tray", "organiser", "dividers"], f"An open tray with {cells - 1} loose dividers.",
                  lambda c=cells: divided_tray(200, 120, 50, c)))
    for pat in ("stars", "dots"):
        e.append((f"lantern-{pat}", f"Lantern with {pat}", "Home decor", ["lantern", "light", "candle", "box"],
                  "A 100 x 100 x 160 mm lantern with cut-out windows. Use an LED tea light, not a flame.",
                  lambda p=pat: lantern(pattern=p, seed=3)))
    return e


def _entries():
    e = _box_entries()
    for shape in ("round", "square", "hexagon"):
        for pat in ("rings", "sunburst", "hexgrid", "mandala"):
            e.append((f"coaster-{shape}-{pat}", f"{shape.title()} coaster, {pat}", "Home decor",
                      ["coaster", "kitchen", "engraved", pat], f"A 95 mm {shape} coaster with an engraved {pat} pattern.",
                      lambda s=shape, p=pat: coaster(s, p, seed=len(s) * 31 + len(p))))
    for size in (180, 220):
        e.append((f"hex-trivet-{size}", f"Honeycomb trivet {size} mm", "Kitchen", ["trivet", "hexagon", "kitchen"],
                  "A hexagon trivet with a honeycomb of cut-outs.", lambda s=size: trivet(s)))
    for k in range(24):
        e.append((f"snowflake-{k + 1:02d}", f"Snowflake ornament no. {k + 1}", "Seasonal", ["snowflake", "christmas", "winter", "ornament"],
                  "A 90 mm six-armed snowflake with a hanging loop. Every number is a different flake.",
                  lambda k=k: snowflake(1000 + k)))
    for kind in ("star", "heart", "circle", "hexagon", "tree"):
        e.append((f"ornament-{kind}", f"{kind.title()} ornament", "Seasonal", ["ornament", "christmas", kind],
                  f"An 80 mm {kind} ornament with a hanging loop.", lambda k=kind: ornament(k, seed=7)))
    for k in range(16):
        e.append((f"mandala-disc-{k + 1:02d}", f"Mandala wall disc no. {k + 1}", "Wall art", ["mandala", "wall art", "engraved"],
                  "A 200 mm disc with an engraved mandala. Every number is a different pattern.",
                  lambda k=k: S.centre(S.polygon_paths(_circle(100)) + mandala_lines(92, 500 + k))))
    for size in (300, 400):
        e.append((f"sunburst-wall-art-{size}", f"Sunburst wall art {size} mm", "Wall art", ["sunburst", "wall art", "sun"],
                  "A cut-out sunburst for a wall.", lambda s=size: wall_art_sunburst(s)))
    for kind in ("round", "square", "hexagon", "heart", "shield", "tag"):
        e.append((f"keychain-{kind}", f"{kind.title()} keychain blank", "Gifts and accessories", ["keychain", "tag", "blank", kind],
                  "A keychain blank with a key-ring hole. Add a name or picture in the studio.", lambda k=kind: keychain(k)))
    for pat in ("lattice", "leaves", "stars", "waves"):
        e.append((f"bookmark-{pat}", f"Bookmark with {pat}", "Gifts and accessories", ["bookmark", "reading", pat],
                  "A 40 x 150 mm bookmark with a cut-out pattern and a tassel hole.", lambda p=pat: bookmark(p, seed=4)))
    e.append(("plant-marker", "Plant marker", "Garden", ["garden", "plant", "marker", "stake"],
              "A garden stake with a label head. Add the plant name in the studio.", lambda: plant_marker()))
    for k, cells in enumerate((8, 10, 12, 14, 16, 18, 20, 24, 10, 12, 14, 16)):
        e.append((f"maze-{k + 1:02d}", f"Maze board no. {k + 1} ({cells} x {cells})", "Games and puzzles",
                  ["maze", "puzzle", "kids", "engraved"], f"An engraved {cells} x {cells} maze. Enter on the left, exit on the right.",
                  lambda k=k, c=cells: maze(200 + k, c, 8.0 if c <= 16 else 7.0)))
    for cols, rows in ((3, 3), (4, 3), (5, 4), (6, 4), (6, 5), (8, 6)):
        e.append((f"jigsaw-{cols}x{rows}", f"Jigsaw puzzle {cols * rows} pieces", "Games and puzzles", ["jigsaw", "puzzle", "kids"],
                  f"A {cols} x {rows} jigsaw with 40 mm pieces. Engrave a picture on it in the studio.",
                  lambda c=cols, r=rows: jigsaw(c, r, 40.0, seed=c * 10 + r)))
    e.append(("tangram", "Tangram puzzle", "Games and puzzles", ["tangram", "puzzle", "geometry"],
              "The classic seven-piece tangram on a 150 mm square.", lambda: tangram()))
    e.append(("tic-tac-toe", "Tic-tac-toe set", "Games and puzzles", ["game", "tic tac toe", "kids"],
              "A board with an engraved grid and five X and five O pieces.", lambda: tic_tac_toe()))
    for teeth in (12, 16, 20, 24, 32, 40):
        e.append((f"gear-{teeth}t", f"Gear, {teeth} teeth", "Mechanical", ["gear", "mechanical", "toy", "steam punk"],
                  f"A {teeth}-tooth spur gear (module 2.5) with a 6 mm bore. Gears of any size here mesh together.",
                  lambda t=teeth: gear(t)))
    for pw, ph in ((100, 150), (130, 180), (200, 250)):
        e.append((f"picture-frame-{pw}x{ph}", f"Picture frame for {pw} x {ph} mm photos", "Home decor", ["frame", "photo", "gift"],
                  "A front, back and stand that hold a photo.", lambda w=pw, h=ph: picture_frame(w, h)))
    for style in ("ticks", "dots", "numbers"):
        e.append((f"clock-face-{style}", f"Clock face with {style}", "Home decor", ["clock", "wall", "engraved"],
                  "A 250 mm clock face with an 9 mm hole for a standard clock movement.", lambda s=style: clock_face(250, s)))
    for text, slug in (("WELCOME", "welcome-sign"), ("HOME", "home-sign"), ("OFFICE", "office-door-sign"), ("YOUR NAME", "name-plate")):
        e.append((slug, f"{text.title()} sign", "Signs", ["sign", "text", "door"],
                  "A 300 x 100 mm sign with screw holes. Change the words in the studio.", lambda t=text: sign(t)))
    return e


ENTRIES = _entries()
