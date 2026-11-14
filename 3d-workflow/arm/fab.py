"""Cut and machined parts: everything that is made but not 3D printed.   python run.py cut

For each part this writes, under fab/:
  dxf/mm/<part>.dxf and dxf/inch/<part>.dxf   CNC router / laser / waterjet profiles, true size, origin at the
                                              lower-left corner; layers CUT_OUTSIDE, CUT_INSIDE, POCKET_*, MARK, NOTES
  templates/<part>.svg (+ .pdf if Playwright)   1:1 drill and cut templates with a 100 mm and a 4 in check bar
  drawings/<part>.svg                         production sheet (arm/sheets.py): views, section, hole + fastener table
  step/<part>.step                            solid model
and fab/CUTLIST.md + cutlist.csv (stock, cut lengths, kerf, offcuts), fab/FASTENERS.md (every screw, its length,
washer, nut and torque). Every dimension marked MEASURE in arm/hardware.py HW depends on the part you receive:
measure, edit HW, rerun."""
import csv, json, math
from pathlib import Path

import cadquery as cq

from . import hardware as Hh, sheets as S
from .fasteners import FASTENERS, label

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "fab"
HW = Hh.HW
IN = 25.4

# ------------------------------------------------------------------ 2D primitives
# outline: ("rrect", w, h, r) centred on (0,0) | ("circle", d) | ("ring", od, id)
# holes:   ("c", x, y, d, note) | ("rect", x, y, w, h, r, note) | ("slot", x, y, length, width, angle_deg, note)
# pockets: ("rrect", x, y, w, h, r, depth, "bottom"|"top", note)
# marks:   ("rect", x, y, w, h, label) | ("x", x, y, label)       engrave / centre-punch only, not cut


class Plate:
    def __init__(self, pid, title, t, qty, material, process, outline, holes=(), pockets=(), marks=(), notes=(),
                 tol="metal", density=2.70, specs=None):
        self.pid, self.title, self.t, self.qty, self.material, self.process = pid, title, t, qty, material, process
        self.outline, self.holes, self.pockets, self.marks = outline, list(holes), list(pockets), list(marks)
        self.notes, self.tol, self.density, self.specs = list(notes), tol, density, specs or {}

    def size(self):
        o = self.outline
        return (o[1], o[2]) if o[0] == "rrect" else (o[1], o[1])

    def solid(self):
        o = self.outline
        wp = cq.Workplane("XY")
        if o[0] == "rrect":
            s = wp.rect(o[1], o[2]).extrude(self.t)
            if o[3] > 0:
                s = s.edges("|Z").fillet(o[3])
        elif o[0] == "circle":
            s = wp.circle(o[1] / 2).extrude(self.t)
        else:
            s = wp.circle(o[1] / 2).circle(o[2] / 2).extrude(self.t)
        for h in self.holes:
            if h[0] == "c":
                s = s.cut(cq.Workplane("XY").center(h[1], h[2]).circle(h[3] / 2).extrude(self.t))
            elif h[0] == "rect":
                c = cq.Workplane("XY").center(h[1], h[2]).rect(h[3], h[4]).extrude(self.t)
                if h[5] > 0:
                    c = c.edges("|Z").fillet(h[5])
                s = s.cut(c)
            elif h[0] == "slot":
                s = s.cut(cq.Workplane("XY").center(h[1], h[2]).slot2D(h[3], h[4], h[5]).extrude(self.t))
        for p in self.pockets:
            z0 = 0 if p[7] == "bottom" else self.t - p[6]
            c = cq.Workplane("XY").workplane(offset=z0).center(p[1], p[2]).rect(p[3], p[4]).extrude(p[6])
            if p[5] > 0:
                c = c.edges("|Z").fillet(p[5])
            s = s.cut(c)
        return s

    def extras(self):
        out = []
        for h in self.holes:
            if h[0] == "rect":
                out.append(dict(kind="rect", dia=min(h[3], h[4]), axis="Z", thru=True, depth=self.t, cb=None, at=(h[1], h[2], self.t),
                                callout=f"RECT CUTOUT {S.mm_in(h[3])} x {S.mm_in(h[4])} R{h[5]:g} THRU",
                                spec=self.specs.get(h[6], h[6])))
        for pk in self.pockets:
            out.append(dict(kind="rect", dia=min(pk[3], pk[4]), axis="Z", thru=False, depth=pk[6], cb=None,
                            at=(pk[1], pk[2], 0.0 if pk[7] == "bottom" else self.t),
                            callout=f"POCKET {S.mm_in(pk[3])} x {S.mm_in(pk[4])} R{pk[5]:g} DEEP {S.mm_in(pk[6], 1)} FROM {pk[7].upper()}",
                            spec=pk[8]))
        return out

    def spec(self, f):
        x = f["entry"].x if f["entry"] else 0
        for (dia, txt) in self.specs.items():
            if abs(f["dia"] - dia) < 0.06:
                return txt
        return "See notes"


def _rr_points(cx, cy, w, h, r):
    """Rounded rectangle as LWPOLYLINE points with bulges (counter-clockwise)."""
    if r <= 0:
        return [(cx - w / 2, cy - h / 2, 0), (cx + w / 2, cy - h / 2, 0), (cx + w / 2, cy + h / 2, 0), (cx - w / 2, cy + h / 2, 0)]
    b = math.tan(math.pi / 8)
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    return [(x0 + r, y0, 0), (x1 - r, y0, b), (x1, y0 + r, 0), (x1, y1 - r, b), (x1 - r, y1, 0), (x0 + r, y1, b),
            (x0, y1 - r, 0), (x0, y0 + r, b)]


def _slot_points(cx, cy, L, W, ang):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    d = (L - W) / 2; r = W / 2
    loc = [(-d, -r, 0), (d, -r, 1), (d, r, 0), (-d, r, 1)]
    return [(cx + x * c - y * s, cy + x * s + y * c, b) for x, y, b in loc]


def write_dxf(p, path, scale=1.0, units=4):
    import ezdxf
    doc = ezdxf.new("R2010", setup=True)
    doc.units = units
    doc.header["$INSUNITS"] = units
    doc.header["$MEASUREMENT"] = 1 if units == 4 else 0
    for name, col in (("CUT_OUTSIDE", 7), ("CUT_INSIDE", 1), ("POCKET", 5), ("MARK", 3), ("NOTES", 8)):
        doc.layers.add(name, color=col)
    msp = doc.modelspace()
    w, h = p.size()
    ox, oy = w / 2, h / 2                          # DXF origin = lower-left corner of the part
    k = scale
    P = lambda pts: [((x + ox) * k, (y + oy) * k, b) for x, y, b in pts]
    o = p.outline
    if o[0] == "rrect":
        msp.add_lwpolyline(P(_rr_points(0, 0, o[1], o[2], o[3])), format="xyb", close=True, dxfattribs={"layer": "CUT_OUTSIDE"})
    else:
        msp.add_circle((ox * k, oy * k), o[1] / 2 * k, dxfattribs={"layer": "CUT_OUTSIDE"})
        if o[0] == "ring":
            msp.add_circle((ox * k, oy * k), o[2] / 2 * k, dxfattribs={"layer": "CUT_INSIDE"})
    for hh in p.holes:
        if hh[0] == "c":
            msp.add_circle(((hh[1] + ox) * k, (hh[2] + oy) * k), hh[3] / 2 * k, dxfattribs={"layer": "CUT_INSIDE"})
        elif hh[0] == "rect":
            msp.add_lwpolyline(P(_rr_points(hh[1], hh[2], hh[3], hh[4], hh[5])), format="xyb", close=True, dxfattribs={"layer": "CUT_INSIDE"})
        elif hh[0] == "slot":
            msp.add_lwpolyline(P(_slot_points(hh[1], hh[2], hh[3], hh[4], hh[5])), format="xyb", close=True, dxfattribs={"layer": "CUT_INSIDE"})
    for pk in p.pockets:
        lay = f"POCKET_{pk[6]:g}MM_{pk[7].upper()}"
        if lay not in doc.layers:
            doc.layers.add(lay, color=5)
        msp.add_lwpolyline(P(_rr_points(pk[1], pk[2], pk[3], pk[4], pk[5])), format="xyb", close=True, dxfattribs={"layer": lay})
    for m in p.marks:
        if m[0] == "rect":
            msp.add_lwpolyline(P(_rr_points(m[1], m[2], m[3], m[4], 0)), format="xyb", close=True, dxfattribs={"layer": "MARK"})
        else:
            for dx, dy in ((3, 0), (0, 3)):
                msp.add_line(((m[1] - dx + ox) * k, (m[2] - dy + oy) * k), ((m[1] + dx + ox) * k, (m[2] + dy + oy) * k), dxfattribs={"layer": "MARK"})
    u = "mm" if units == 4 else "in"
    msp.add_text(f"{p.pid} {p.title}  t={p.t:g} mm [{p.t / IN:.3f} in]  {p.material}  units {u}", height=4 * k,
                 dxfattribs={"layer": "NOTES"}).set_placement((0, -10 * k))
    doc.saveas(path)


def template_svg(p):
    """1:1 template: print at 100 % (no 'fit to page'), check both bars, tape to the stock, centre-punch, drill."""
    w, h = p.size(); m = 25
    W, H = w + 2 * m, h + 2 * m + 30
    X = lambda x: x + w / 2 + m
    Y = lambda y: h / 2 + m - y
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}mm" height="{H:.1f}mm" viewBox="0 0 {W:.2f} {H:.2f}" '
         f'font-family="Helvetica,Arial,sans-serif"><rect width="100%" height="100%" fill="#fff"/>')
    o = p.outline
    if o[0] == "rrect":
        s += f'<rect x="{m}" y="{m}" width="{w}" height="{h}" rx="{o[3]}" fill="none" stroke="#000" stroke-width="0.35"/>'
    else:
        s += f'<circle cx="{X(0)}" cy="{Y(0)}" r="{o[1] / 2}" fill="none" stroke="#000" stroke-width="0.35"/>'
        if o[0] == "ring":
            s += f'<circle cx="{X(0)}" cy="{Y(0)}" r="{o[2] / 2}" fill="none" stroke="#000" stroke-width="0.35"/>'
    for hh in p.holes:
        if hh[0] == "c":
            x, y, d = X(hh[1]), Y(hh[2]), hh[3]
            s += (f'<circle cx="{x}" cy="{y}" r="{d / 2}" fill="none" stroke="#c00" stroke-width="0.3"/>'
                  f'<path d="M{x - d / 2 - 2},{y}h{d + 4}M{x},{y - d / 2 - 2}v{d + 4}" stroke="#c00" stroke-width="0.15"/>'
                  f'<text x="{x + d / 2 + 1}" y="{y - d / 2 - 0.6}" font-size="2.2" fill="#c00">Ø{d:g} [{d / IN:.3f}]</text>')
        elif hh[0] == "rect":
            s += (f'<rect x="{X(hh[1]) - hh[3] / 2}" y="{Y(hh[2]) - hh[4] / 2}" width="{hh[3]}" height="{hh[4]}" rx="{hh[5]}" fill="none" stroke="#c00" stroke-width="0.3"/>'
                  f'<text x="{X(hh[1]) + hh[3] / 2 + 1}" y="{Y(hh[2])}" font-size="2.2" fill="#c00">{hh[3]:g} x {hh[4]:g}</text>')
        elif hh[0] == "slot":
            pts = _slot_points(X(hh[1]), 0, hh[3], hh[4], -hh[5])
            yc = Y(hh[2])
            d = f"M{pts[0][0]},{pts[0][1] + yc}"
            r = hh[4] / 2
            d = (f'M{pts[0][0]},{pts[0][1] + yc} L{pts[1][0]},{pts[1][1] + yc} A{r},{r} 0 0 0 {pts[2][0]},{pts[2][1] + yc} '
                 f'L{pts[3][0]},{pts[3][1] + yc} A{r},{r} 0 0 0 {pts[0][0]},{pts[0][1] + yc} Z')
            s += f'<path d="{d}" fill="none" stroke="#c00" stroke-width="0.3"/>'
    for pk in p.pockets:
        s += (f'<rect x="{X(pk[1]) - pk[3] / 2}" y="{Y(pk[2]) - pk[4] / 2}" width="{pk[3]}" height="{pk[4]}" rx="{pk[5]}" fill="none" '
              f'stroke="#06c" stroke-width="0.3" stroke-dasharray="2,1"/><text x="{X(pk[1]) - pk[3] / 2 + 1}" y="{Y(pk[2]) - pk[4] / 2 - 1}" '
              f'font-size="2.2" fill="#06c">POCKET {pk[6]:g} DEEP FROM {pk[7].upper()}</text>')
    for mk in p.marks:
        if mk[0] == "rect":
            s += (f'<rect x="{X(mk[1]) - mk[3] / 2}" y="{Y(mk[2]) - mk[4] / 2}" width="{mk[3]}" height="{mk[4]}" fill="none" stroke="#090" '
                  f'stroke-width="0.25" stroke-dasharray="1.5,1"/><text x="{X(mk[1]) - mk[3] / 2 + 1}" y="{Y(mk[2]) + mk[4] / 2 - 1}" font-size="2.4" fill="#090">{mk[5]}</text>')
        else:
            s += f'<path d="M{X(mk[1]) - 3},{Y(mk[2])}h6M{X(mk[1])},{Y(mk[2]) - 3}v6" stroke="#090" stroke-width="0.25"/>'
    yb = h + 2 * m + 8
    s += (f'<g stroke="#000" stroke-width="0.3"><line x1="{m}" y1="{yb}" x2="{m + 100}" y2="{yb}"/>'
          + "".join(f'<line x1="{m + 10 * i}" y1="{yb - (2 if i % 5 else 3)}" x2="{m + 10 * i}" y2="{yb}"/>' for i in range(11))
          + f'<line x1="{m}" y1="{yb + 8}" x2="{m + 101.6}" y2="{yb + 8}"/>'
          + "".join(f'<line x1="{m + 25.4 * i}" y1="{yb + 5}" x2="{m + 25.4 * i}" y2="{yb + 8}"/>' for i in range(5)) + "</g>"
          f'<text x="{m + 104}" y="{yb}" font-size="2.6">100 mm: measure this before drilling</text>'
          f'<text x="{m + 104}" y="{yb + 8}" font-size="2.6">4 in</text>'
          f'<text x="{m}" y="{m - 8}" font-size="4" font-weight="bold">{p.pid} {p.title} · 1:1 TEMPLATE · qty {p.qty} · t {p.t:g} mm [{p.t / IN:.3f} in]</text>'
          f'<text x="{m}" y="{m - 3}" font-size="2.6">Print at 100 % (actual size). Red = cut / drill, blue dashed = pocket, green = mark only. '
          f'Centre-punch every cross, pilot 3 mm, then drill to size.</text></svg>')
    return s


# ------------------------------------------------------------------ the parts
def mega_holes(X0, Y0):
    """Arduino Mega 2560 mounting holes (mm from the board's USB corner), board rotated 180° at (X0, Y0)."""
    pts = [(13.97, 2.54), (15.24, 50.8), (66.04, 7.62), (66.04, 35.56), (90.17, 50.8), (96.52, 2.54)]
    return [(X0 - x, Y0 - y) for x, y in pts]


ENC = dict(W=480.0, D=320.0, H=110.0, t=3.0)


def parts():
    hw = HW
    ps = []
    # ---- BASE-01 base board
    s = hw["motor_pcd_sq"] / 2
    leg = 200.0
    holes = [("c", 0, 0, hw["motor_pilot"] + 1.0, "gearbox pilot")] + [("c", x, y, 5.5, "F05") for x in (-s, s) for y in (-s, s)]
    a0 = math.pi / 4
    holes += [("c", hw["turntable_fixed_pcd"] / 2 * math.cos(a0 + k * 2 * math.pi / hw["turntable_ring_holes"]),
               hw["turntable_fixed_pcd"] / 2 * math.sin(a0 + k * 2 * math.pi / hw["turntable_ring_holes"]), 8.0, "F07T")
              for k in range(hw["turntable_ring_holes"])]
    for sx in (-1, 1):
        for sy in (-1, 1):
            holes += [("c", sx * leg + 12, sy * leg + 12, 5.2, "F14"), ("c", sx * leg - 12, sy * leg - 12, 5.2, "F14")]
    holes += [("c", -150, 0, 32.0, "harness")]
    ah = math.radians(-150)
    holes += [("c", 165 * math.cos(ah) + dx * math.sin(ah), 165 * math.sin(ah) - dx * math.cos(ah), 3.4, "F13") for dx in (-11.1, 11.1)]
    ps.append(Plate("BASE-01", "BASE BOARD", 19.0, 1, "3/4 in Baltic birch plywood (18-19 mm)", "CNC router or jigsaw + drill press",
                    ("rrect", 457.2, 457.2, 12), holes,
                    pockets=[("rrect", 0, 0, hw["yaw_flange_sq"] + 1.5, hw["yaw_flange_sq"] + 1.5, 4, 12.0, "bottom",
                             "Yaw gearbox output flange sits here (MEASURE flange); leaves 7 [.28] of wood under F05")],
                    marks=[("rect", sx * leg, sy * leg, 45, 45, "LEG") for sx in (-1, 1) for sy in (-1, 1)],
                    notes=["Pocket 61.5 [2.42] sq x 12 [.47] deep FROM BOTTOM for the yaw gearbox flange (MEASURE flange).",
                           "Countersink E holes 90° x Ø10.5 [.413] on the TOP face. Press F07T tee nuts in from below.",
                           "Seal with 2 coats of polyurethane before assembly. Clamp to the bench when running."],
                    tol="wood", density=0.68,
                    specs={hw["motor_pilot"] + 1.0: "Yaw gearbox pilot clearance (MEASURE pilot)", 5.5: label("F05") + " + fender washer",
                           8.0: label("F07") + " into F07T tee nut, turntable fixed ring",
                           5.2: label("F14") + "; countersink top 90° Ø10.5", 32.0: "Harness pass-through: 32 mm rubber grommet",
                           3.4: label("F13") + "; yaw limit switch (MEASURE switch hole spacing)"}))
    # ---- YAW-01 turntable adapter disc
    holes = [("c", 0, 0, hw["hub_flange_od"] + 4, "hub")]
    holes += [("c", hw["turntable_pcd"] / 2 * math.cos(k * math.pi / 4), hw["turntable_pcd"] / 2 * math.sin(k * math.pi / 4), 6.5, "F06") for k in range(8)]
    holes += [("c", hw["turntable_rot_pcd"] / 2 * math.cos(a0 + k * 2 * math.pi / hw["turntable_ring_holes"]),
               hw["turntable_rot_pcd"] / 2 * math.sin(a0 + k * 2 * math.pi / hw["turntable_ring_holes"]), hw["turntable_ring_hole"], "F08")
              for k in range(hw["turntable_ring_holes"])]
    holes += [("c", 135, dy, 3.4, "dog") for dy in (-8, 8)]
    ps.append(Plate("YAW-01", "TURNTABLE ADAPTER DISC", 6.0, 1, "6061-T6 aluminium plate 6 mm [.236] (or 12 mm Baltic birch)",
                    "Waterjet / CNC, or saw + drill from the 1:1 template", ("circle", min(300.0, hw["turntable_od"] - 5)), holes,
                    notes=["Carries base_top_plate (8x M6) on the turntable rotating ring (4x M5).",
                           "Fixes the bolt-circle mismatch: a 12 in turntable ring cannot reach the 170 mm circle of the printed plate.",
                           "Yaw home dog: bolt a 20 x 10 x 3 aluminium tab across the two Ø3.4 holes."],
                    specs={hw["hub_flange_od"] + 4: "Clamp-hub flange clearance (MEASURE hub flange OD)", 6.5: label("F06"),
                           hw["turntable_ring_hole"]: label("F08") + "; turntable rotating ring (MEASURE)",
                           3.4: "M3 x 10 + nut: yaw home dog for the limit switch"}))
    # ---- gaskets and pads
    ps.append(Plate("GSK-01", "TURNTABLE SEAT GASKET", 1.5, 1, "Neoprene 60A sheet 1.5 mm [1/16 in]", "Knife, laser or drag-knife plotter",
                    ("ring", hw["turntable_od"], hw["turntable_od"] - 50),
                    [("c", hw["turntable_fixed_pcd"] / 2 * math.cos(a0 + k * 2 * math.pi / hw["turntable_ring_holes"]),
                      hw["turntable_fixed_pcd"] / 2 * math.sin(a0 + k * 2 * math.pi / hw["turntable_ring_holes"]), 6.0, "F07")
                     for k in range(hw["turntable_ring_holes"])],
                    notes=["Between the turntable fixed ring and BASE-01: levels the plywood and damps motor noise."],
                    tol="soft", density=1.23, specs={6.0: label("F07") + " passes through"}))
    ps.append(Plate("GSK-02", "GRIPPER JAW PAD", 3.0, 2, "TPU 95A (print flat) or 3 mm neoprene with adhesive back", "Knife or laser; or print",
                    ("rrect", 56.0, 50.0, 3.0), [], notes=["Bond to the fixed jaw and to gripper_jaw faces with contact cement or CA."],
                    tol="soft", density=1.2))
    ps.append(Plate("GSK-03", "LEG FOOT PAD", 3.0, 4, "Rubber sheet 3 mm [1/8 in], 60A", "Knife", ("rrect", 45.0, 45.0, 3.0), [],
                    notes=["Glue under each LEG-01."], tol="soft", density=1.2))
    # ---- enclosure (W x D x H, panels t thick; walls stand on the base, lid on the walls)
    E = ENC; W, D, Ht, t = E["W"], E["D"], E["H"], E["t"]
    base_holes = [("c", x - W / 2, y - D / 2, 3.4, "F15") for x in (60, 240, 420) for y in (t + 6, D - t - 6)]
    base_holes += [("c", x - W / 2, y - D / 2, 3.4, "F15") for x in (t + 6, W - t - 6) for y in (80, 240)]
    feet = [("c", x - W / 2, y - D / 2, 4.5, "F18") for x in (18, W - 18) for y in (18, D - 18)]
    marks = [("rect", 28 + 107.5 - W / 2, 185 + 57.5 - D / 2, 215, 115, "PSU 24V 15A (drill from part)")]
    marks += [("rect", 25 + i * 87.5 + 37.75 - W / 2, 30 + 59 - D / 2, 75.5, 118, f"DRV{i}") for i in range(5)]
    marks += [("rect", 462 - 50.8 - W / 2, 290 - 26.67 - D / 2, 101.6, 53.34, "ARDUINO MEGA")]
    marks += [("x", x - W / 2, y - D / 2, "mega") for x, y in mega_holes(462, 290)]
    marks += [("rect", 300 - W / 2, 202 - D / 2, 80, 35, "FUSE + 24V/GND BUS")]
    ps.append(Plate("ENC-01", "ENCLOSURE BASE PLATE", t, 1, "5052 aluminium 3 mm (earth it) or 3 mm acrylic", "Laser / waterjet / CNC",
                    ("rrect", W, D, 4), base_holes + feet, marks=marks,
                    notes=["Green outlines are mark-only: drill driver, PSU and Mega holes from the parts you have (F16, F17).",
                           "Aluminium panels: bond all panels to the PSU earth terminal with a 2.5 mm² green/yellow lead."],
                    specs={3.4: label("F15") + " into 10x10 angle", 4.5: label("F18")}))
    lid_holes = [h for h in base_holes] + [("c", 400 - W / 2, 90 - D / 2, 22.5, "estop")]
    lid_holes += [("slot", x - W / 2, 89 - D / 2, 60, 5, 90, "vent") for x in range(60, 391, 30)]
    ps.append(Plate("ENC-02", "ENCLOSURE LID", t, 1, "5052 aluminium 3 mm or 3 mm acrylic", "Laser / waterjet / CNC", ("rrect", W, D, 4), lid_holes,
                    notes=["E-stop Ø22.5 [.886]: file a 3.2 x 1.7 anti-rotation notch if your button has a tab.", "Vent slots sit over the driver row."],
                    specs={3.4: label("F15") + " into 10x10 angle", 22.5: "22 mm E-stop mushroom button (NC), panel nut", 5.0: "Vent"}))

    def wall(length, u_bottom, corner_u, corner_v):
        hs = [("c", u - length / 2, v - Ht / 2, 3.4, "F15") for u in u_bottom for v in (6, Ht - 6)]
        hs += [("c", u - length / 2, v - Ht / 2, 3.4, "F15") for u in corner_u for v in corner_v]
        return hs
    fb = wall(W, (30, 150, 330, 450), (t + 6, W - t - 6), (30, 80))
    front = fb + [("slot", u - W / 2, 0, 50, 5, 90, "vent") for u in range(40, 441, 25)]
    ps.append(Plate("ENC-03", "ENCLOSURE FRONT WALL", t, 1, "5052 aluminium 3 mm or 3 mm acrylic", "Laser / waterjet / CNC", ("rrect", W, Ht, 0), front,
                    notes=["Seen from outside. Intake vents across the driver row."], specs={3.4: label("F15"), 5.0: "Intake vent"}))
    back = fb + [("rect", 420 - W / 2, 55 - Ht / 2, 27.5, 47.5, 1.0, "Snap-in IEC C14 inlet + switch + fuse (MEASURE)"), ("c", 380 - W / 2, 30 - Ht / 2, 5.2, "PE")]
    ps.append(Plate("ENC-04", "ENCLOSURE BACK WALL", t, 1, "5052 aluminium 3 mm or 3 mm acrylic", "Laser / waterjet / CNC", ("rrect", W, Ht, 0), back,
                    notes=["Seen from outside. Snap-in IEC C14 inlet with switch + fuse: cutout 27.5 x 47.5 [1.083 x 1.870] (MEASURE).",
                           "PE: M5 earth stud, star washers both sides, to the PSU earth terminal."],
                    specs={3.4: label("F15"), 5.2: "M5 x 16 earth stud + 2 star washers + nut (PE)"}))
    L = D - 2 * t
    side = lambda gys, right: wall(L, [(gy - t) if right else (D - t - gy) for gy in gys], (6, L - 6), (55,))
    left = side((40, 160, 280), False) + [("slot", u - L / 2, 0, 60, 5, 90, "vent") for u in range(20, 131, 14)]
    ps.append(Plate("ENC-05", "ENCLOSURE LEFT WALL", t, 1, "5052 aluminium 3 mm or 3 mm acrylic", "Laser / waterjet / CNC", ("rrect", L, Ht, 0), left,
                    notes=["Seen from outside. Exhaust vents beside the PSU fan."], specs={3.4: label("F15"), 5.0: "Exhaust vent"}))
    right = side((40, 160, 280), True)
    right += [("rect", (290 - 38.1 - t) - L / 2, 17.1 - Ht / 2, 16, 14, 2.0, "USB-B cable access to the Mega")]
    right += [("c", u - L / 2, 45 - Ht / 2, 15.5, "PG9") for u in (35, 80, 125, 170, 215)]
    right += [("c", u - L / 2, 82 - Ht / 2, 12.5, "PG7") for u in (35, 80, 125, 170, 215)]
    ps.append(Plate("ENC-06", "ENCLOSURE RIGHT WALL (ARM SIDE)", t, 1, "5052 aluminium 3 mm or 3 mm acrylic", "Laser / waterjet / CNC",
                    ("rrect", L, Ht, 0), right,
                    notes=["Seen from outside. Faces the arm. Motor cables through PG9, limit-switch cables through PG7.",
                           "USB-B cutout lines up with the Mega's USB jack on 10 mm standoffs (check before cutting)."],
                    specs={3.4: label("F15"), 15.5: "PG9 cable gland (motor cable 6-8 mm)", 12.5: "PG7 cable gland (limit cable 3-6.5 mm)"}))
    return ps


# ------------------------------------------------------------------ round / long parts (not plates)
def tube(length, pins, title, pid, note):
    od, wall_t = HW["tube_od"], 1.651
    s = cq.Workplane("YZ").circle(od / 2).circle(od / 2 - wall_t).extrude(length)
    for x in pins:
        s = s.cut(cq.Workplane("XY").workplane(offset=-od).center(x, 0).circle(2.75).extrude(2 * od))
    return dict(pid=pid, title=title, solid=s, qty=1, material="6061-T6 tube 1.5 in OD x 0.065 in wall [38.1 x 1.65 mm]",
                process="Chop saw / hacksaw, square + deburr; cross-drill on a V-block", length=length, pins=pins, note=note,
                tol="metal", density=2.70)


def tubes(d):
    l1, l2 = d["l1_mm"] - 55, d["l2_mm"] - 55
    return [
        tube(l1, (27.0, l1 - 30.0), "UPPER ARM TUBE", "TUBE-01", "Shoulder end in tube_socket (pin 27 from end), elbow end in elbow_tube_block (pin 30)"),
        tube(l2, (27.0, l2 - 30.0), "FOREARM TUBE", "TUBE-02", "Elbow end in tube_socket (pin 27 from end), wrist end in wrist_tube_block (pin 30)"),
        tube(150.0, (150.0 - 30.0,), "RISER TUBE", "TUBE-03", "Bottom bonded in base_top_plate (70 deep, epoxy); top in shoulder_tube_block (pin 30)"),
        tube(120.0, (27.0,), "WRIST STUB TUBE", "TUBE-04", "Wrist tube_socket end (pin 27); gripper_adapter end bonded 55 deep"),
    ]


def shaft():
    L, dia = 150.0, HW["shaft"]
    s = cq.Workplane("YZ").circle(dia / 2).extrude(L).faces("<X or >X").edges().chamfer(0.5)
    s = s.cut(cq.Workplane("XY").box(25, dia, dia, centered=(False, True, False)).translate((8, 0, dia / 2 - 0.5)))
    return dict(pid="SHAFT-01", title="JOINT SHAFT", solid=s, qty=3, material="12 mm h6 hardened or 303 stainless rod, 150 mm",
                process="Grind or file one flat 0.5 [.020] deep x 25 [.98] long; chamfer ends 0.5 x 45°", tol="metal", density=7.9)


def leg():
    s = cq.Workplane("XY").box(45, 45, 200, centered=(True, True, False))
    s = s.cut(cq.Workplane("XY").workplane(offset=140).pushPoints([(12, 12), (-12, -12)]).circle(1.5).extrude(60))
    return dict(pid="LEG-01", title="BASE LEG", solid=s, qty=4, material="Hardwood 45 x 45 [1.75 x 1.75] (2x2 nominal)",
                process="Saw square to length; drill pilots on the drill press", tol="wood", density=0.7)


ROUND_SPECS = {"TUBE": {5.5: "Ø5.5 [.217] cross-pin hole THRU both walls: drill on a V-block, then transfer-drill through the printed part",
                        34.8: "Tube ID (as bought)"},
               "SHAFT": {}, "LEG": {3.0: label("F14") + "; pilot Ø3.0 [.118] x 60 deep, match BASE-01 E holes"}}

ANGLE_CUTS = [("10 x 10 x 1.5 aluminium angle", 470.0, 4, "front/back walls, top and bottom"),
              ("10 x 10 x 1.5 aluminium angle", 294.0, 4, "side walls, top and bottom"),
              ("10 x 10 x 1.5 aluminium angle", 90.0, 4, "vertical corners")]


def harness():
    """Cable cut lengths: routed length + 300 mm service loop at the enclosure + 10 % drape."""
    runs = [("J1 yaw motor", 0.9), ("J2 shoulder motor", 1.4), ("J3 elbow motor", 1.8), ("J4 wrist motor", 2.2), ("J5 gripper motor", 2.5)]
    rows = []
    for n, r in runs:
        cut = round((r * 1.1 + 0.3) * 10) / 10
        rows.append((n.replace("motor", "motor cable"), "4-core shielded 18 AWG", cut, "ferrules at driver; motor plug or solder + heatshrink at motor"))
        rows.append((n.replace("motor", "limit switch"), "2-core 22 AWG (twisted)", cut, "ferrule at Mega terminal, 100 nF across switch"))
    rows += [("PSU V+ to fuse to E-stop to bus", "14 AWG red silicone", 0.6, "ferrules"), ("PSU V- to GND bus", "14 AWG black silicone", 0.4, "ferrules"),
             ("Bus to each driver VCC/GND (x5)", "18 AWG red + black", 5 * 0.35, "ferrules, 350 mm each"),
             ("Mega to drivers STEP/DIR/ENA", "22 AWG hookup, 3 colours", 15 * 0.3, "15 leads of 300 mm, ferrules at drivers"),
             ("Mains IEC inlet to PSU L/N/PE", "18 AWG 3-core mains flex (H05VV-F 1.0 mm²)", 0.4, "fork terminals at PSU; qualified person only")]
    return rows


# ------------------------------------------------------------------ writers
def _png(svg_path):
    try:
        from . import render
        render.svg_to_png(svg_path, svg_path.with_suffix(".png"))
    except Exception:
        pass


def main(argv=None):
    d = json.loads((HERE / "design" / "design.json").read_text(encoding="utf-8"))
    for sub in ("dxf/mm", "dxf/inch", "templates", "drawings", "step"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    index = []
    for p in parts():
        sol = p.solid()
        info = dict(title=p.title, partno=p.pid, material=p.material, process=p.process, qty=p.qty, tol=p.tol,
                    density=p.density, notes=p.notes, extra=p.extras())
        svg, feats = S.sheet(sol, info, p.spec)
        (OUT / "drawings" / f"{p.pid}.svg").write_text(svg, encoding="utf-8")
        write_dxf(p, OUT / "dxf/mm" / f"{p.pid}.dxf", 1.0, 4)
        write_dxf(p, OUT / "dxf/inch" / f"{p.pid}.dxf", 1 / IN, 1)
        (OUT / "templates" / f"{p.pid}.svg").write_text(template_svg(p), encoding="utf-8")
        cq.exporters.export(sol, str(OUT / "step" / f"{p.pid}.step"))
        w, h = p.size()
        index.append(dict(pid=p.pid, title=p.title, qty=p.qty, material=p.material, process=p.process, t=p.t, w=w, h=h,
                          kind="plate", holes=len(feats), outline=list(p.outline),
                          cut=[list(h[:-1]) for h in p.holes]))
    for r in tubes(d) + [shaft(), leg()]:
        fam = r["pid"].split("-")[0]
        spec = lambda f, fam=fam: next((t for dia, t in ROUND_SPECS[fam].items() if abs(f["dia"] - dia) < 0.15), "See notes")
        info = dict(title=r["title"], partno=r["pid"], material=r["material"], process=r["process"], qty=r["qty"], tol=r["tol"],
                    density=r["density"], notes=[r.get("note", "")] if r.get("note") else [])
        svg, feats = S.sheet(r["solid"], info, spec)
        (OUT / "drawings" / f"{r['pid']}.svg").write_text(svg, encoding="utf-8")
        cq.exporters.export(r["solid"], str(OUT / "step" / f"{r['pid']}.step"))
        bb = r["solid"].val().BoundingBox()
        index.append(dict(pid=r["pid"], title=r["title"], qty=r["qty"], material=r["material"], process=r["process"],
                          t=None, w=round(bb.xlen, 1), h=round(max(bb.ylen, bb.zlen), 1), kind="round", holes=len(feats)))
    write_cutlist(d, index)
    write_fasteners()
    (OUT / "fab.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    print(f"wrote {OUT}: {len(index)} parts, DXF (mm + inch), templates, drawings, STEP, CUTLIST.md, FASTENERS.md")
    return 0


def write_cutlist(d, index):
    tl = tubes(d)
    kerf = 3.0
    used = sum(t["length"] for t in tl) + kerf * len(tl)
    rows = [("Tube", t["pid"], t["title"], f"{t['length']:.0f}", f"{t['length'] / IN:.3f}", 1, t["material"],
             "pins at " + ", ".join(f"{x:g}" for x in t["pins"]) + " mm from the left end") for t in tl]
    rows += [("Angle", "ANG", f"enclosure corner angle, {u}", f"{L:.0f}", f"{L / IN:.3f}", q, m, "deburr, transfer-drill from panels")
             for m, L, q, u in ANGLE_CUTS]
    rows += [("Wood", "LEG-01", "base leg", "200", f"{200 / IN:.3f}", 4, "Hardwood 45 x 45", "square ends"),
             ("Rod", "SHAFT-01", "joint shaft (as bought 150)", "150", f"{150 / IN:.3f}", 3, "12 mm h6 rod", "one flat, chamfer ends")]
    plates = [i for i in index if i["kind"] == "plate"]
    with open(OUT / "cutlist.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Type", "Part", "Description", "Length / size mm", "Length / size in", "Qty", "Stock / material", "Notes"])
        for r in rows:
            w.writerow(r)
        for p in plates:
            w.writerow(["Sheet", p["pid"], p["title"], f"{p['w']:.1f} x {p['h']:.1f} x {p['t']:g}",
                        f"{p['w'] / IN:.3f} x {p['h'] / IN:.3f} x {p['t'] / IN:.3f}", p["qty"], p["material"], f"DXF fab/dxf/mm/{p['pid']}.dxf"])
        for n, kind, m, how in harness():
            w.writerow(["Cable", "", n, f"{m * 1000:.0f}", f"{m * 1000 / IN:.1f}", 1, kind, how])
    tip_payload = 2.27 * 9.81 * (d["extension_m"] if "extension_m" in d else 1.0)
    L = ["# Cut list and fabrication package (generated)", "",
         "Everything that is cut, drilled or machined rather than printed. Each part has a DXF in **mm and inch** "
         "(`fab/dxf/mm`, `fab/dxf/inch`), a 1:1 drill template (`fab/templates`, print at 100 %), a production drawing "
         "(`fab/drawings`, mm [in], hole and fastener tables) and a STEP model (`fab/step`).", "",
         "DXF layers: `CUT_OUTSIDE` profile, `CUT_INSIDE` holes and cutouts, `POCKET_<depth>MM_<side>` pockets, `MARK` engrave or "
         "centre-punch only (drill these from the real part), `NOTES` never cut. Origin is the part's lower-left corner.", "",
         "## Tube (1.5 in OD x 0.065 in wall 6061-T6)", "",
         f"All four pieces come out of **one 48 in (1219 mm) length**: {used:.0f} mm including {kerf:g} mm saw kerf per cut, "
         f"{1219 - used:.0f} mm left over. A 36 in length is too short for all four.", "",
         "| Part | Description | Cut length mm [in] | Cross-pin holes from left end | Mates with |", "|---|---|---|---|---|"]
    L += [f"| {t['pid']} | {t['title'].title()} | {t['length']:.0f} [{t['length'] / IN:.3f}] | "
          + ", ".join(f"{x:g} [{x / IN:.3f}]" for x in t["pins"]) + f" | {t['note']} |" for t in tl]
    L += ["", "Cut square (within 0.5°), deburr inside and out. Drill one pin hole Ø5.5 [.217] on a V-block, assemble into the printed "
          "part, then drill the printed part's hole through the tube as a guide for any second hole so both line up.", "",
          "## Sheet and plate parts", "", "| Part | Description | Qty | Size mm [in] | Material | Process | Features |", "|---|---|---|---|---|---|---|"]
    L += [f"| {p['pid']} | {p['title'].title()} | {p['qty']} | {p['w']:.1f} x {p['h']:.1f} x {p['t']:g} "
          f"[{p['w'] / IN:.3f} x {p['h'] / IN:.3f} x {p['t'] / IN:.3f}] | {p['material']} | {p['process']} | {p['holes']} |" for p in plates]
    L += ["", "## Other cut parts", "", "| Part | Description | Qty | Length mm [in] | Stock | Notes |", "|---|---|---|---|---|---|"]
    L += [f"| {r[1]} | {r[2]} | {r[5]} | {r[3]} [{r[4]}] | {r[6]} | {r[7]} |" for r in rows[len(tl):]]
    L += ["", "## Wire harness cut list", "", "| Run | Cable | Cut length m [ft] | Ends |", "|---|---|---|---|"]
    L += [f"| {n} | {k} | {m:.1f} [{m / 0.3048:.1f}] | {how} |" for n, k, m, how in harness()]
    tot = {}
    for n, k, m, how in harness():
        tot[k] = tot.get(k, 0) + m
    L += ["", "Totals: " + "; ".join(f"{k} {v:.1f} m" for k, v in tot.items()) + ". Cut lengths include a 300 mm service loop and 10 % drape.", "",
          "## Stability check", "",
          f"At 5 lb and full reach the payload alone puts about {tip_payload:.0f} N·m of tipping moment on the base, plus about 10 N·m "
          "from the arm. BASE-01 with motors and legs resists only about 15 N·m about its front edge, so **clamp or bolt the base to the "
          "bench** (two C-clamps on the board edge, or screws through the GSK-03 pads into the bench top).", ""]
    (OUT / "CUTLIST.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def write_fasteners():
    count_f15 = sum(1 for p in parts() for h in p.holes if h[0] == "c" and h[4] == "F15")
    L = ["# Fastener schedule (generated from arm/fasteners.py)", "",
         "Every screw in the arm, with its standard, length, what it clamps and its torque. Drawings call these numbers out in "
         "their hole tables. Stainless A2-70 throughout; blue threadlocker on metal threads without a nyloc nut. "
         "Torque values for screws bearing on printed PETG are deliberately low (the plastic creeps): snug with washers, then the value shown.", "",
         "| No. | Fastener | Standard | Qty | Torque N·m [lbf·in] | Length check (stack) | Where |", "|---|---|---|---|---|---|---|"]
    for k, (desc, std, q, tq, stack, where) in FASTENERS.items():
        if k == "F15":
            q = count_f15
        t = f"{tq:g} [{tq * 8.851:.0f}]" if tq else "-"
        L.append(f"| {k} | {desc} | {std} | {q} | {t} | {stack} | {where} |")
    L += ["", "Hole sizes: M3 clearance Ø3.4 [.134], M4 Ø4.5 [.177], M5 Ø5.5 [.217], M6 Ø6.5 [.256] (ISO 273 medium). "
          "Heat-set M4 insert pilot Ø5.6 [.220]. Tee nut barrel Ø8.0 [.315].", ""]
    (OUT / "FASTENERS.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def fastener_count(fid):
    if fid == "F15":
        return sum(1 for p in parts() for h in p.holes if h[0] == "c" and h[4] == "F15")
    return FASTENERS[fid][2]


if __name__ == "__main__":
    main()
