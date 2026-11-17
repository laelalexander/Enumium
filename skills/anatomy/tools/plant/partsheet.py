"""Vendored from the robot arm package (PR #2, 3d-workflow/arm/sheets.py) with a configurable title block.

Production drawing sheets (A3, third-angle) for every part: printed, cut and machined.

Each sheet has:
  * front / top / right views with hidden lines plus an isometric view, all at one true scale
  * overall dimensions in mm with inches in brackets: 120.00 [4.724]
  * every hole, counterbore, blind bore and slot found automatically on the CAD solid,
    tagged on the view that looks down its axis (A1, A2, B1 ...)
  * a hole table: size mm [in], depth or THRU, counterbore, and the exact fastener / fit for it
  * a location table: X / Y / Z of each tagged feature from the datum corner, mm [in]
  * general tolerances, material, process, mass, quantity, units, projection symbol, revision block

The hole data comes from the solid itself (cylindrical faces), so a hole that is missing in the CAD
is missing on the drawing too: that is how the cheek bearing-seat bug was caught."""
import math, re
from datetime import date
from html import escape

import cadquery as cq
from cadquery import Compound, Shape, Vector
from cadquery.occ_impl.exporters.svg import getPaths
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepLib import BRepLib
from OCP.HLRAlgo import HLRAlgo_Projector
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape
from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt, gp_Pnt2d

W, H = 1600, 1131                 # A3 landscape in px
PXMM = W / 420.0                  # 1:1 = 3.81 px per mm of paper
INK, DIM, HID, CEN, TAG = "#111", "#b00020", "#9aa0a6", "#2e7d32", "#0d47a1"
IN = 25.4


def mm_in(v, d=2):
    """'120.00 [4.724]' (inches to 3 places, leading zero dropped as on US drawings)."""
    i = f"{v / IN:.3f}"
    i = i[1:] if i.startswith("0.") else i.replace("-0.", "-.")
    return f"{v:.{d}f} [{i}]"


def inch(v):
    i = f"{v / IN:.3f}"
    return i[1:] if i.startswith("0.") else i


# ------------------------------------------------------------------ projection
VIEWS = {  # name: (view normal toward the viewer, screen-right direction)
    "FRONT": ((0, -1, 0), (1, 0, 0)),
    "TOP": ((0, 0, 1), (1, 0, 0)),
    "RIGHT": ((1, 0, 0), (0, 1, 0)),
    "ISOMETRIC": ((1, -1, 1), (1, 1, 0)),
}


class View:
    def __init__(self, shape, name):
        n, x = VIEWS[name]
        self.name = name
        self.proj = HLRAlgo_Projector(gp_Ax2(gp_Pnt(), gp_Dir(*n), gp_Dir(*x)))
        hlr = HLRBRep_Algo(); hlr.Add(shape.wrapped); hlr.Projector(self.proj); hlr.Update(); hlr.Hide()
        h = HLRBRep_HLRToShape(hlr)
        vis = [c for c in (h.VCompound(), h.Rg1LineVCompound(), h.OutLineVCompound()) if not c.IsNull()]
        hid = [c for c in (h.HCompound(), h.OutLineHCompound()) if not c.IsNull()]
        for c in vis + hid:
            BRepLib.BuildCurves3d_s(c, 1e-6)
        vis, hid = [Shape(c) for c in vis], [Shape(c) for c in hid]
        self.hid, self.vis = getPaths(vis, hid)
        bb = Compound.makeCompound(vis + hid).BoundingBox()
        self.x0, self.x1, self.y0, self.y1 = bb.xmin, bb.xmax, bb.ymin, bb.ymax
        self.w, self.h = bb.xlen, bb.ylen
        self.ox = self.oy = 0.0; self.s = 1.0
        self.iso = name == "ISOMETRIC"

    def place(self, ox, oy, s):
        self.ox, self.oy, self.s = ox, oy, s

    def pt(self, p):
        """3D model point -> sheet px."""
        o = gp_Pnt2d(); self.proj.Project(gp_Pnt(*p), o)
        return self.ox + (o.X() - self.x0) * self.s, self.oy + (self.y1 - o.Y()) * self.s

    @property
    def pw(self): return self.w * self.s

    @property
    def ph(self): return self.h * self.s

    def svg(self):
        t = f"translate({self.ox - self.x0 * self.s:.3f},{self.oy + self.y1 * self.s:.3f}) scale({self.s:.5f},{-self.s:.5f})"
        hid = "" if self.iso else "".join(f'<path d="{p}"/>' for p in self.hid)
        vis = "".join(f'<path d="{p}"/>' for p in self.vis)
        return (f'<g transform="{t}" fill="none" stroke-linecap="round">'
                f'<g stroke="{HID}" stroke-width="0.8" stroke-dasharray="5,3" vector-effect="non-scaling-stroke">{hid}</g>'
                f'<g stroke="{INK}" stroke-width="{1.0 if self.iso else 1.3}" vector-effect="non-scaling-stroke">{vis}</g></g>')


# ------------------------------------------------------------------ feature recognition
def _canon(d):
    d = [round(c, 6) for c in d]
    for c in d:
        if abs(c) > 1e-6:
            return (d, 1) if c > 0 else ([-x for x in d], -1)
    return d, 1


def _axis_name(d):
    a = [abs(c) for c in d]
    i = a.index(max(a))
    return "XYZ"[i] if max(a) > 0.999 else "skew"


def features(solid, bb):
    """Concave cylinders -> holes (thru / blind / counterbored) and slots, in model coordinates."""
    solid = solid.val() if hasattr(solid, "val") else solid
    full, partial = {}, []
    for f in solid.Faces():
        if f.geomType() != "CYLINDER":
            continue
        a = BRepAdaptor_Surface(f.wrapped)
        c = a.Cylinder(); r = c.Radius(); ax = c.Axis(); P, D = ax.Location(), ax.Direction()
        u1, u2, v1, v2 = a.FirstUParameter(), a.LastUParameter(), a.FirstVParameter(), a.LastVParameter()
        um, vm = (u1 + u2) / 2, (v1 + v2) / 2
        q = a.Value(um, vm)
        p0 = Vector(P.X(), P.Y(), P.Z()); d0 = Vector(D.X(), D.Y(), D.Z())
        qv = Vector(q.X(), q.Y(), q.Z())
        radial = qv - (p0 + d0 * vm)
        if f.normalAt(qv).dot(radial) >= 0:
            continue                                   # convex: boss, fillet, outer surface
        dl, sg = _canon((D.X(), D.Y(), D.Z()))
        dv = Vector(*dl)
        base = p0 - dv * p0.dot(dv)                    # axis point closest to origin
        s1, s2 = sorted(((p0.dot(dv) + sg * v1), (p0.dot(dv) + sg * v2)))
        span = u2 - u1
        rec = dict(r=r, d=dv, base=base, a1=s1, a2=s2)
        if span > 1.2 * math.pi:          # full bore, or a bore that breaks into a pocket on one side
            key = (tuple(dl), round(base.x, 2), round(base.y, 2), round(base.z, 2))
            full.setdefault(key, []).append(rec)
        else:
            mid = (u1 + u2) / 2
            rec["open"] = qv - (base + dv * qv.dot(dv))   # radial direction toward the arc middle
            rec["span"] = span
            partial.append(rec)

    def inside(p):
        return solid.isInside(p, 1e-4)

    out = []
    for key, segs in full.items():
        segs.sort(key=lambda s: s["a1"])
        d, base = segs[0]["d"], segs[0]["base"]
        # merge same-radius segments split by seams, or separated only by empty space (a hole crossing a cavity)
        chains, cur = [], [segs[0]]
        for s in segs[1:]:
            last = cur[-1]
            gap_mid = base + d * ((last["a2"] + s["a1"]) / 2)
            if s["a1"] - last["a2"] < 0.05 or (abs(s["r"] - last["r"]) < 0.01 and not inside(gap_mid)):
                cur.append(s)
            else:
                chains.append(cur); cur = [s]
        chains.append(cur)
        for ch in chains:
            a1, a2 = min(s["a1"] for s in ch), max(s["a2"] for s in ch)
            open1 = not inside(base + d * (a1 - 0.3))
            open2 = not inside(base + d * (a2 + 0.3))
            radii = sorted({round(s["r"], 3) for s in ch})
            rmin = radii[0]
            core = [s for s in ch if round(s["r"], 3) == rmin]
            big = [s for s in ch if round(s["r"], 3) != rmin]
            feat = dict(kind="hole", d=d, axis=_axis_name(d), dia=2 * rmin, thru=open1 and open2,
                        depth=a2 - a1, cb=None)
            if big:
                bmax = max(big, key=lambda s: s["r"])
                bl = [s for s in big if abs(s["r"] - bmax["r"]) < 1e-3]
                b1, b2 = min(s["a1"] for s in bl), max(s["a2"] for s in bl)
                feat["cb"] = (2 * bmax["r"], b2 - b1)
                # entry is the counterbore end
                entry = a1 if abs(b1 - a1) < abs(b2 - a2) else a2
            else:
                entry = a1 if open1 else a2
            if not feat["thru"]:
                feat["depth"] = sum(s["a2"] - s["a1"] for s in core) if not big else a2 - a1
            feat["entry"] = base + d * entry
            feat["exitp"] = base + d * (a2 if entry == a1 else a1)
            out.append(feat)
    # slots: two concave half-cylinders with parallel axes, same radius and same axial extent
    used = set()
    for i, p in enumerate(partial):
        if i in used or abs(p["span"] - math.pi) > 0.05:
            continue
        best = None
        for j, q in enumerate(partial):
            if j <= i or j in used or abs(q["span"] - math.pi) > 0.05 or abs(p["r"] - q["r"]) > 1e-3 or (p["d"] - q["d"]).Length > 1e-4:
                continue
            if abs(p["a1"] - q["a1"]) > 0.05 or abs(p["a2"] - q["a2"]) > 0.05:
                continue
            sep = q["base"] - p["base"]; L = sep.Length
            if L < 1e-3 or L > 60 or p["open"].dot(sep) > 0:   # arcs must face away from each other
                continue
            if best is None or L < best[1]:
                best = (j, L)
        if best:
            j, L = best; used |= {i, j}
            q = partial[j]; d = p["d"]
            c = (p["base"] + q["base"]) * 0.5
            mid = c + d * ((p["a1"] + p["a2"]) / 2)
            open1 = not p.get("_") and not solid.isInside(c + d * (p["a1"] - 0.3), 1e-4)
            open2 = not solid.isInside(c + d * (p["a2"] + 0.3), 1e-4)
            out.append(dict(kind="slot", d=d, axis=_axis_name(d), dia=2 * p["r"], length=L + 2 * p["r"],
                            dirv=(q["base"] - p["base"]).normalized(), thru=open1 and open2, depth=p["a2"] - p["a1"],
                            cb=None, entry=c + d * (p["a1"] if open1 else p["a2"]), exitp=c + d * (p["a2"] if open1 else p["a1"])))
    for f in out:
        e = f["entry"]
        f["xyz"] = (e.x - bb.xmin, e.y - bb.ymin, e.z - bb.zmin)
    return out


def feature_key(f):
    return (f.get("callout"), f["kind"], round(f["dia"], 2), round(f.get("length", 0), 2), f["thru"], round(f["depth"], 1),
            f["cb"] and (round(f["cb"][0], 2), round(f["cb"][1], 1)), f["axis"])


def callout(f):
    if f.get("callout"):
        return f["callout"]
    if f["kind"] == "slot":
        s = f"SLOT {mm_in(f['dia'])} WIDE x {mm_in(f['length'])} LONG"
    else:
        s = f"Ø{mm_in(f['dia'])}"
    s += " THRU" if f["thru"] else f" DEEP {mm_in(f['depth'], 1)}"
    if f["cb"]:
        s += f" / CBORE Ø{mm_in(f['cb'][0])} DEEP {mm_in(f['cb'][1], 1)}"
    return s


# ------------------------------------------------------------------ sheet furniture
def hdim(x1, x2, y, label, ext_from=None):
    ext = ""
    if ext_from is not None:
        ext = (f'<line x1="{x1}" y1="{ext_from}" x2="{x1}" y2="{y + (4 if y > ext_from else -4)}"/>'
               f'<line x1="{x2}" y1="{ext_from}" x2="{x2}" y2="{y + (4 if y > ext_from else -4)}"/>')
    return (f'<g stroke="{DIM}" fill="{DIM}" stroke-width="0.8">{ext}<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}"/>'
            f'<path d="M{x1},{y} l8,-3 v6 z M{x2},{y} l-8,-3 v6 z" stroke="none"/>'
            f'<text x="{(x1 + x2) / 2}" y="{y - 5}" font-size="12" text-anchor="middle" stroke="none">{label}</text></g>')


def vdim(x, y1, y2, label, ext_from=None):
    ext = ""
    if ext_from is not None:
        ext = (f'<line x1="{ext_from}" y1="{y1}" x2="{x + (4 if x > ext_from else -4)}" y2="{y1}"/>'
               f'<line x1="{ext_from}" y1="{y2}" x2="{x + (4 if x > ext_from else -4)}" y2="{y2}"/>')
    return (f'<g stroke="{DIM}" fill="{DIM}" stroke-width="0.8">{ext}<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}"/>'
            f'<path d="M{x},{y1} l-3,8 h6 z M{x},{y2} l-3,-8 h6 z" stroke="none"/>'
            f'<text transform="translate({x - 6},{(y1 + y2) / 2}) rotate(-90)" font-size="12" text-anchor="middle" stroke="none">{label}</text></g>')


def third_angle(x, y):
    return (f'<g stroke="{INK}" fill="none" stroke-width="1"><path d="M{x},{y + 6} L{x + 22},{y + 1} L{x + 22},{y + 19} L{x},{y + 14} Z"/>'
            f'<circle cx="{x + 42}" cy="{y + 10}" r="9"/><circle cx="{x + 42}" cy="{y + 10}" r="4"/>'
            f'<line x1="{x - 3}" y1="{y + 10}" x2="{x + 56}" y2="{y + 10}" stroke-dasharray="6,2,1,2" stroke-width="0.6"/></g>')


def frame():
    z = ""
    for i in range(8):
        x = 20 + (W - 40) * (i + 0.5) / 8
        z += f'<text x="{x}" y="15" font-size="10" text-anchor="middle">{8 - i}</text><text x="{x}" y="{H - 6}" font-size="10" text-anchor="middle">{8 - i}</text>'
    for i in range(6):
        y = 20 + (H - 40) * (i + 0.5) / 6
        z += f'<text x="10" y="{y}" font-size="10" text-anchor="middle">{"FEDCBA"[i]}</text><text x="{W - 10}" y="{y}" font-size="10" text-anchor="middle">{"FEDCBA"[i]}</text>'
    ticks = "".join(f'<line x1="{20 + (W - 40) * i / 8}" y1="20" x2="{20 + (W - 40) * i / 8}" y2="26"/><line x1="{20 + (W - 40) * i / 8}" y1="{H - 20}" x2="{20 + (W - 40) * i / 8}" y2="{H - 26}"/>' for i in range(1, 8))
    ticks += "".join(f'<line x1="20" y1="{20 + (H - 40) * i / 6}" x2="26" y2="{20 + (H - 40) * i / 6}"/><line x1="{W - 20}" y1="{20 + (H - 40) * i / 6}" x2="{W - 26}" y2="{20 + (H - 40) * i / 6}"/>' for i in range(1, 6))
    return (f'<rect width="100%" height="100%" fill="#fff"/><rect x="20" y="20" width="{W - 40}" height="{H - 40}" fill="none" stroke="{INK}" stroke-width="2"/>'
            f'<g stroke="{INK}" stroke-width="1">{ticks}</g><g fill="{INK}">{z}</g>')


def title_block(t):
    """t: dict(title, partno, material, process, qty, mass, scale, rev, tol, drawn, finish)."""
    x, y, w = 1060, 905, 520
    r = lambda yy: f'<line x1="{x}" y1="{yy}" x2="{x + w}" y2="{yy}"/>'
    cell = lambda cx, cy, lab, val, fs=12, bold=False: (f'<text x="{cx}" y="{cy}" font-size="8.5" fill="#555">{escape(lab)}</text>'
                                                     f'<text x="{cx}" y="{cy + 15}" font-size="{fs}"{" font-weight=\"bold\"" if bold else ""}>{escape(str(val))}</text>')
    g = (f'<g stroke="{INK}" fill="none" stroke-width="1.2"><rect x="{x}" y="{y}" width="{w}" height="{H - 20 - y}"/>'
         + r(y + 46) + r(y + 82) + r(y + 118) + r(y + 154)
         + f'<line x1="{x + 260}" y1="{y + 46}" x2="{x + 260}" y2="{y + 154}"/><line x1="{x + 390}" y1="{y + 82}" x2="{x + 390}" y2="{H - 20}"/>'
         + f'<line x1="{x + 130}" y1="{y + 118}" x2="{x + 130}" y2="{H - 20}"/><line x1="{x + 260}" y1="{y + 154}" x2="{x + 260}" y2="{H - 20}"/></g>')
    g += f'<g fill="{INK}" font-family="Helvetica,Arial,sans-serif">'
    g += f'<text x="{x + 8}" y="{y + 20}" font-size="17" font-weight="bold">{escape(t["title"])}</text>'
    g += f'<text x="{x + 8}" y="{y + 38}" font-size="11">{escape(t.get("project", "Anatomy project"))} · {escape(t.get("assy", ""))}</text>'
    g += cell(x + 8, y + 58, "PART NO.", t["partno"], 13, True) + cell(x + 268, y + 58, "MATERIAL", t["material"], 10.5)
    g += cell(x + 8, y + 94, "PROCESS / FINISH", t["process"], 10.5) + cell(x + 268, y + 94, t.get("qty_label", "QTY PER UNIT"), t["qty"], 12, True)
    g += cell(x + 398, y + 94, "MASS (EST.)", t["mass"], 11)
    g += cell(x + 8, y + 130, "SCALE", t["scale"]) + cell(x + 138, y + 130, "SHEET", "A3 · 1 of 1") + cell(x + 268, y + 130, "UNITS", "mm [in]")
    g += cell(x + 398, y + 130, "REV", t.get("rev", "A"), 13, True)
    g += cell(x + 8, y + 166, "DRAWN", "plant/partsheet.py") + cell(x + 138, y + 166, "DATE", date.today().isoformat())
    g += cell(x + 268, y + 166, "CHECKED", "verify before cutting")
    g += f'<text x="{x + 398}" y="{y + 166}" font-size="8.5" fill="#555">PROJECTION</text></g>' + third_angle(x + 405, y + 176)
    return g


def notes_block(lines, x=1060, y=740, w=520, h=160):
    body = "".join(f'<text x="{x + 8}" y="{y + 34 + 13.5 * i}" font-size="10.5">{escape(l)}</text>' for i, l in enumerate(lines[:9]))
    return (f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{INK}" stroke-width="1"/>'
            f'<text x="{x + 8}" y="{y + 17}" font-size="12" font-weight="bold">NOTES (UNLESS OTHERWISE SPECIFIED)</text>{body}</g>')


TOL = {
    "printed": ["Dimensions mm [in]. Linear X ±0.5 [.020], X.X ±0.3 [.012], X.XX ±0.15 [.006]",
                "Holes +0.20/-0 [+.008/-.000]: drill or ream to size after printing", "Angles ±1°. Break sharp edges 0.5 [.02]"],
    "metal": ["Dimensions mm [in]. Linear X.X ±0.2 [.008], X.XX ±0.10 [.004]", "Holes +0.10/-0 [+.004/-.000]. Angles ±0.5°",
              "Deburr all edges, break 0.3 [.01] max"],
    "wood": ["Dimensions mm [in]. Linear ±0.5 [.020], holes +0.3/-0 [+.012/-.000]", "Angles ±0.5°. Sand edges, 1.5 [.06] round-over on top edges"],
    "sheet": ["Dimensions mm [in]. Linear ±0.5 [.020] laser cut, ±0.8 [.030] across bends", "Holes +0.15/-0 [+.006/-.000]. Bend angles ±1°, inside bend radius = 1T",
              "Deburr, no sharp edges. Food-contact faces #4 finish Ra ≤ 0.8 µm [32 µin]"],
    "soft": ["Dimensions mm [in]. Linear ±0.5 [.020], holes ±0.3 [.012]", "Cut with knife, laser or drag-knife plotter"],
}


# ------------------------------------------------------------------ the sheet
def sheet(shape, info, fasteners=None, extra_notes=()):
    """shape: cq Workplane/Shape. info: title, partno, material, process, qty, density, tol, kind.
    fasteners(feature) -> 'fastener / fit' text. Returns (svg, features)."""
    sv = shape.val() if hasattr(shape, "val") else shape
    bb = sv.BoundingBox()
    views = {n: View(sv, n) for n in VIEWS}
    F, T, R, I = views["FRONT"], views["TOP"], views["RIGHT"], views["ISOMETRIC"]
    # one true scale for the orthographic views: front over top on the left, right view beside front
    X, Y, Z = bb.xlen, bb.ylen, bb.zlen
    plate = Z < 0.12 * min(X, Y)            # flat part: big plan view + edge view, no right view
    gap = 165
    ox, oy = 110, 95
    wsum = F.w + (0 if plate else R.w)
    avail_w = 1030 - ox - (110 if plate else gap + 110)
    avail_h = H - 40 - oy - gap - 140
    raw = min(avail_w / wsum, avail_h / (F.h + T.h)) / PXMM
    steps = [5, 4, 2, 1.5, 1, 1 / 1.5, 0.5, 0.4, 1 / 3, 0.25, 0.2, 0.1, 0.05]
    sc = next((k for k in steps if k <= raw + 1e-9), 0.05)
    S = sc * PXMM
    scale_txt = f"{sc:g}:1" if sc >= 1 else f"1:{round(1 / sc, 2):g}"
    # third-angle arrangement: TOP above FRONT, RIGHT to the right of FRONT
    T.place(ox, oy, S)
    F.place(ox, oy + T.h * S + gap, S)
    R.place(ox + F.w * S + gap, F.oy, S)
    ortho = (T, F) if plate else (T, F, R)
    # isometric: the larger free box, right of TOP or right of the FRONT/RIGHT row
    right_edge = (F.ox + F.pw) if plate else (R.ox + R.pw + 110)
    cands = [(T.ox + T.pw + 70, oy + 10, 1030 - (T.ox + T.pw + 70), F.oy - 70 - oy),
             (right_edge + 30, F.oy + 10, 1030 - right_edge - 30, H - 80 - F.oy)]
    ix0, iy0, iw, ih = max(cands, key=lambda c: min(c[2], c[3]))
    show_iso = iw > 140 and ih > 140
    if show_iso:
        si = min(iw / I.w, ih / I.h, S * 1.2) * 0.85
        I.place(ix0 + (iw - I.w * si) / 2, iy0 + 20 + (ih - 20 - I.h * si) / 2, si)
    body = "".join(v.svg() for v in ortho) + (I.svg() if show_iso else "")
    for v, lab in ((T, "TOP"), (F, "FRONT"), (R, "RIGHT"))[: len(ortho)]:
        body += f'<text x="{v.ox}" y="{v.oy - 40}" font-size="13" font-weight="bold">{lab} VIEW</text>'
    if show_iso:
        body += f'<text x="{I.ox}" y="{I.oy - 12}" font-size="13" font-weight="bold">ISOMETRIC (REF.)</text>'
    body += hdim(T.ox, T.ox + T.pw, T.oy - 18, mm_in(X, 1), T.oy - 4)
    body += vdim(T.ox - 22, T.oy, T.oy + T.ph, mm_in(Y, 1), T.ox - 4)
    body += vdim(F.ox - 22, F.oy, F.oy + F.ph, mm_in(Z, 1), F.ox - 4)
    if not plate:
        body += hdim(R.ox, R.ox + R.pw, R.oy - 18, mm_in(Y, 1), R.oy - 4)
    # datum corner (bbox min) marked on every orthographic view
    dpt = (bb.xmin, bb.ymin, bb.zmin)
    for v in ortho:
        px, py = v.pt(dpt)
        body += (f'<g stroke="{CEN}" fill="none" stroke-width="1.2"><circle cx="{px}" cy="{py}" r="6"/>'
                 f'<path d="M{px - 6},{py} A6,6 0 0 1 {px},{py - 6} L{px},{py} Z" fill="{CEN}"/></g>')
    body += (f'<text x="{F.ox}" y="{H - 52}" font-size="10.5" fill="{CEN}">◐ DATUM = bounding-box corner (min X, min Y, min Z). '
             f'Location table X right, Y back, Z up, as in the views. Model origin offset {mm_in(bb.xmin, 1)}, {mm_in(bb.ymin, 1)}, {mm_in(bb.zmin, 1)}.</text>')

    feats = features(sv, bb)
    for e in info.get("extra", []):          # features the solid cannot name by itself: rectangular cutouts, pockets
        e = dict(e); e["entry"] = Vector(*e["at"]); e["exitp"] = e["entry"]
        e["xyz"] = (e["at"][0] - bb.xmin, e["at"][1] - bb.ymin, e["at"][2] - bb.zmin)
        feats.append(e)
    groups = {}
    for f in feats:
        groups.setdefault(feature_key(f), []).append(f)
    order = sorted(groups.values(), key=lambda g: (-g[0]["dia"] if g[0]["kind"] == "hole" else 0, g[0]["axis"], g[0]["kind"]))
    order = sorted(order, key=lambda g: (g[0]["kind"] != "hole", -g[0]["dia"]))
    letters = [chr(65 + i) if i < 26 else "A" + chr(65 + i - 26) for i in range(len(order))]
    view_for = {"Z": T, "Y": F, "X": None if plate else R}
    tags = ""
    rows_h, rows_l = [], []
    for L, g in zip(letters, order):
        g.sort(key=lambda f: (round(f["xyz"][0], 1), round(f["xyz"][1], 1), round(f["xyz"][2], 1)))
        v = view_for.get(g[0]["axis"])
        spec = g[0].get("spec") or (fasteners(g[0]) if fasteners else "")
        rows_h.append((L, len(g), callout(g[0]), g[0]["axis"], spec))
        for k, f in enumerate(g, 1):
            rows_l.append((f"{L}{k}", f["xyz"]))
            if v is None:
                continue
            px, py = v.pt((f["entry"].x, f["entry"].y, f["entry"].z))
            rr = f["dia"] / 2 * S
            # centre mark, then a short leader to a tag balloon
            cm = max(rr + 4, 7)
            tags += (f'<g stroke="{CEN}" stroke-width="0.7"><line x1="{px - cm}" y1="{py}" x2="{px + cm}" y2="{py}" stroke-dasharray="8,2,2,2"/>'
                     f'<line x1="{px}" y1="{py - cm}" x2="{px}" y2="{py + cm}" stroke-dasharray="8,2,2,2"/></g>')
            bx, by = px + max(rr, 4) + 10, py - max(rr, 4) - 10
            tags += (f'<g><line x1="{px + rr * 0.7}" y1="{py - rr * 0.7}" x2="{bx - 9}" y2="{by + 4}" stroke="{TAG}" stroke-width="0.7"/>'
                     f'<rect x="{bx - 9}" y="{by - 8}" width="{9 + 6.2 * len(L + str(k))}" height="13" rx="6" fill="#fff" stroke="{TAG}" stroke-width="0.8"/>'
                     f'<text x="{bx - 4}" y="{by + 2.5}" font-size="9" fill="{TAG}" font-weight="bold">{L}{k}</text></g>')
    body += tags
    body += ordinates([(v, [f for g in order for f in g if view_for.get(f["axis"]) is v]) for v in ortho], S, dpt)
    # hole table (right column, top)
    tx, ty, tw = 1060, 40, 512
    ht = (f'<text x="{tx}" y="{ty + 12}" font-size="13" font-weight="bold">HOLE AND FASTENER TABLE</text>'
          f'<text x="{tx + tw}" y="{ty + 12}" font-size="9.5" text-anchor="end" fill="#555">{len(feats)} features, found on the CAD solid</text>')
    y = ty + 20
    ht += f'<rect x="{tx}" y="{y}" width="{tw}" height="16" fill="#eef1f4" stroke="{INK}" stroke-width="0.6"/>'
    for cx, lab in ((4, "TAG"), (34, "QTY"), (64, "SIZE  mm [in]"), (338, "AXIS"), (370, "FASTENER / FIT")):
        ht += f'<text x="{tx + cx}" y="{y + 12}" font-size="9.5" font-weight="bold">{lab}</text>'
    y += 16
    for L, n, c, ax, spec in rows_h:
        cl = _wrap(c, 48); sp = _wrap(spec, 25)
        hrow = 12 * max(len(cl), len(sp)) + 5
        ht += f'<rect x="{tx}" y="{y}" width="{tw}" height="{hrow}" fill="none" stroke="{INK}" stroke-width="0.4"/>'
        ht += f'<text x="{tx + 6}" y="{y + 12}" font-size="10.5" font-weight="bold" fill="{TAG}">{L}</text><text x="{tx + 38}" y="{y + 12}" font-size="10.5">{n}</text>'
        ht += "".join(f'<text x="{tx + 64}" y="{y + 12 + 12 * i}" font-size="10">{escape(t)}</text>' for i, t in enumerate(cl))
        ht += f'<text x="{tx + 344}" y="{y + 12}" font-size="10">{ax}</text>'
        ht += "".join(f'<text x="{tx + 370}" y="{y + 12 + 12 * i}" font-size="9.5">{escape(t)}</text>' for i, t in enumerate(sp))
        y += hrow
    # location table: two columns of rows if it is long
    y += 14
    ht += f'<text x="{tx}" y="{y + 10}" font-size="13" font-weight="bold">FEATURE LOCATIONS FROM DATUM  mm [in]</text>'
    y += 16
    rows_l = _compress(rows_l)
    room = int((740 - 8 - y) / 12.5) - 1
    ncol = 1 if len(rows_l) <= room else 2
    cw = tw / ncol
    per = math.ceil(len(rows_l) / ncol) if rows_l else 0
    shown = rows_l[: room * ncol]
    for ci in range(ncol):
        cx = tx + ci * cw; yy = y
        ht += f'<rect x="{cx}" y="{yy}" width="{cw}" height="15" fill="#eef1f4" stroke="{INK}" stroke-width="0.5"/>'
        hdr = (("TAG", 3), ("X", 0.20), ("Y", 0.47), ("Z", 0.74)) if ncol == 1 else (("TAG", 3), ("X", 0.22), ("Y", 0.48), ("Z", 0.74))
        for lab, off in hdr:
            ht += f'<text x="{cx + (off if off > 1 else off * cw)}" y="{yy + 11}" font-size="9.5" font-weight="bold">{lab}</text>'
        yy += 15
        for tag, xyz in shown[ci * per:(ci + 1) * per]:
            ht += f'<text x="{cx + 3}" y="{yy + 10}" font-size="9.5" fill="{TAG}" font-weight="bold">{tag}</text>'
            for k, off in ((0, 0.20 if ncol == 1 else 0.22), (1, 0.47 if ncol == 1 else 0.48), (2, 0.74)):
                v = xyz[k]
                txt = f"{v:.2f} [{inch(v)}]" if isinstance(v, float) else v
                ht += f'<text x="{cx + off * cw}" y="{yy + 10}" font-size="{9.5 if ncol == 1 else 8.6}">{txt}</text>'
            yy += 12.5
    if len(rows_l) > len(shown):
        ht += f'<text x="{tx}" y="736" font-size="9.5" fill="{DIM}">+{len(rows_l) - len(shown)} more locations: see the DXF / CSV for this part.</text>'
    body += section_view(sv, feats, F, T, S, bb)
    mass_g = sv.Volume() / 1000 * info.get("density", 1.27) * info.get("fill", 0.75 if info.get("tol", "printed") == "printed" else 1.0)
    notes = TOL[info.get("tol", "printed")] + list(info.get("notes", [])) + list(extra_notes)
    notes.append(f"Overall {mm_in(X, 1)} x {mm_in(Y, 1)} x {mm_in(Z, 1)}. Volume {sv.Volume() / 1000:.1f} cm³.")
    tb = dict(title=info["title"], partno=info["partno"], material=info["material"], process=info["process"],
              qty=info["qty"], mass=f"{mass_g:.0f} g [{mass_g / 453.6:.2f} lb]", scale=scale_txt, rev=info.get("rev", "A"),
              project=info.get("project", "Anatomy project"), assy=info.get("assy", ""), qty_label=info.get("qty_label", "QTY PER UNIT"))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="Helvetica,Arial,sans-serif">{frame()}{body}{ht}{notes_block(notes)}{title_block(tb)}</svg>')
    return svg, feats


def section_view(sv, feats, F, T, S, bb):
    """SECTION A-A through the most informative feature (counterbore, then blind bore, then the largest hole),
    hatched, placed under the top view if there is room. The cutting plane is drawn on its parent view."""
    if not feats:
        return ""
    pick = sorted(feats, key=lambda f: (f["cb"] is None, f["thru"], -f["dia"]))[0]
    c = (pick["entry"] + pick["exitp"]) * 0.5
    big = 1e4
    if pick["axis"] == "Z":      # vertical plane through the feature, keep the back half, look from the front
        keep = cq.Solid.makeBox(big, big, big, cq.Vector(-big / 2, c.y, -big / 2))
        name, parent, normal, val = "FRONT", T, (0, 1, 0), c.y
    else:                        # horizontal plane through the feature, keep the lower half, look from the top
        keep = cq.Solid.makeBox(big, big, big, cq.Vector(-big / 2, -big / 2, c.z - big))
        name, parent, normal, val = "TOP", F, (0, 0, 1), c.z
    try:
        cut = sv.intersect(keep)
        if cut.Volume() < 1e-3:
            return ""
        V = View(cut, name)
    except Exception:
        return ""
    x0, y0 = F.ox, F.oy + F.ph + 125
    if y0 + V.h * S > H - 75 or x0 + V.w * S > 1030:
        return ""
    V.place(x0, y0, S)
    # hatch every cut face that lies in the plane: one path of tessellated triangles -> no seams
    tri = ""
    for f in cut.Faces():
        if f.geomType() != "PLANE":
            continue
        n = f.normalAt()
        if abs(abs(n.x * normal[0] + n.y * normal[1] + n.z * normal[2]) - 1) > 1e-6:
            continue
        cc = f.Center()
        if abs((cc.x, cc.y, cc.z)[normal.index(1)] - val) > 1e-3:
            continue
        vs, ts = f.tessellate(0.05)
        P = [V.pt((q.x, q.y, q.z)) for q in vs]
        tri += "".join(f"M{P[a][0]:.2f},{P[a][1]:.2f}L{P[b][0]:.2f},{P[b][1]:.2f}L{P[c2][0]:.2f},{P[c2][1]:.2f}Z" for a, b, c2 in ts)
    hatch = ('<defs><pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
             f'<line x1="0" y1="0" x2="0" y2="7" stroke="{INK}" stroke-width="0.7"/></pattern></defs>'
             f'<path d="{tri}" fill="url(#hatch)" stroke="none"/>')
    out = hatch + V.svg() + f'<text x="{x0}" y="{y0 - 14}" font-size="13" font-weight="bold">SECTION A-A</text>'
    out += hdim(V.ox, V.ox + V.pw, V.oy + V.ph + 26, mm_in(V.w, 1), V.oy + V.ph + 4)
    # cutting-plane line on the parent view with arrows pointing in the viewing direction
    _, py = parent.pt((c.x, c.y, c.z)); xa, xb = parent.ox - 12, parent.ox + parent.pw + 12
    dy = 1 if name == "TOP" else -1          # arrows point the way the section is viewed
    line = f'<line x1="{xa}" y1="{py}" x2="{xb}" y2="{py}"/>'
    arrows = "".join(f'<path d="M{x},{py} v{14 * dy} M{x - 5},{py + 7 * dy} L{x},{py + 15 * dy} L{x + 5},{py + 7 * dy}"/>' for x in (xa, xb))
    lab = "".join(f'<text x="{x}" y="{py + (30 if dy > 0 else -20)}" font-size="13" font-weight="bold" text-anchor="middle">A</text>' for x in (xa, xb))
    out += (f'<g stroke="{INK}" stroke-width="1.4" fill="none" stroke-dasharray="18,4,3,4">{line}</g>'
            f'<g stroke="{INK}" stroke-width="1.4" fill="none">{arrows}</g><g fill="{INK}">{lab}</g>')
    return out


AXES = {"FRONT": (0, 2), "TOP": (0, 1), "RIGHT": (1, 2)}


def ordinates(view_feats, S, dpt, limit=16):
    """Ordinate dimensions from the datum: X (or Y) values below each view, the vertical values to its right."""
    out = ""
    for v, fs in view_feats:
        if not fs:
            continue
        ia, ib = AXES[v.name]
        for which in (0, 1):
            idx = (ia, ib)[which]
            vals = {}
            for f in fs:
                px, py = v.pt((f["entry"].x, f["entry"].y, f["entry"].z))
                key = round(f["xyz"][idx], 1)
                rr = f["dia"] / 2 * S
                if f["kind"] == "slot":
                    rr = f["length"] / 2 * S
                vals.setdefault(key, []).append((px, py, rr))
            if len(vals) > limit:
                continue
            vals.setdefault(0.0, [])
            if which == 0:
                base = v.oy + v.ph + 16; last = -1e9
                for val in sorted(vals):
                    pts = vals[val]
                    x = pts[0][0] if pts else v.pt(dpt)[0]
                    lx = max(x, last + 12); last = lx
                    y0 = max((py + rr for _, py, rr in pts), default=v.oy + v.ph) + 3
                    out += (f'<g stroke="{DIM}" stroke-width="0.45" fill="none"><polyline points="{x},{y0} {x},{base} {lx},{base + 6}"/></g>'
                            f'<text transform="translate({lx + 3.5},{base + 9}) rotate(-90)" font-size="9" fill="{DIM}" text-anchor="end">{val:.2f} [{inch(val)}]</text>')
            else:
                base = v.ox + v.pw + 16; last = 1e9
                for val in sorted(vals):
                    pts = vals[val]
                    y = pts[0][1] if pts else v.pt(dpt)[1]
                    ly = min(y, last - 11); last = ly
                    x0 = max((px + rr for px, _, rr in pts), default=v.ox + v.pw) + 3
                    out += (f'<g stroke="{DIM}" stroke-width="0.45" fill="none"><polyline points="{x0},{y} {base},{y} {base + 6},{ly}"/></g>'
                            f'<text x="{base + 9}" y="{ly + 3}" font-size="9" fill="{DIM}">{val:.2f} [{inch(val)}]</text>')
    return out


def _wrap(t, n):
    words, lines, cur = str(t).split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    return lines + ([cur] if cur else [])


def _compress(rows):
    """Collapse long equal-pitch runs of one tag into a single pattern row."""
    out, i = [], 0
    while i < len(rows):
        tag = re.match(r"[A-Z]+", rows[i][0]).group(0)
        j = i
        while j + 1 < len(rows) and re.match(r"[A-Z]+", rows[j + 1][0]).group(0) == tag:
            j += 1
        run = rows[i:j + 1]
        if len(run) >= 6:
            d = [tuple(round(b - a, 2) for a, b in zip(run[k][1], run[k + 1][1])) for k in range(len(run) - 1)]
            if len(set(d)) == 1:
                p = d[0]; step = max(abs(c) for c in p); ax = "XYZ"[[abs(c) for c in p].index(step)]
                out.append((f"{run[0][0]}", run[0][1]))
                out.append((f"..{run[-1][0]}", (f"{len(run)}x", f"pitch {step:.2f}", f"[{inch(step)}] in {ax}")))
                i = j + 1
                continue
        out += run
        i = j + 1
    return out


HALO_STYLE = '<style>text{paint-order:stroke;stroke:#fff;stroke-width:3px;stroke-linejoin:round}</style>'


def halo(svg, width=3.0):
    """White halo behind every label, so lines crossing text break around it like on a hand-drawn sheet. Done as an
    explicit white copy under each <text> (every SVG renderer draws that), not with CSS paint-order (some don't)."""
    import re as _re
    svg = _re.sub(r"<style>text\{paint-order[^<]*</style>", "", svg)

    def dup(m):
        attrs, body = m.group(1), m.group(2)
        a = _re.sub(r'\s(fill|stroke|stroke-width)="[^"]*"', "", attrs)
        return f'<text{a} fill="#fff" stroke="#fff" stroke-width="{width}" stroke-linejoin="round">{body}</text>{m.group(0)}'
    return _re.sub(r"<text([^>]*)>(.*?)</text>", dup, svg, flags=_re.S)
