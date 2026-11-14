"""Assembly drawings built from the real CAD: ASM-002 pitch-joint section (true scale) and ASM-001 general arrangement.

Every solid here is the same geometry the parts are printed or cut from (arm/hardware.py, arm/fab.py) placed the way
the 3D twin places it, plus simple bodies for bought parts at their catalogue sizes. Sheets follow arm/sheets.py:
A3, third-angle, mm [in], balloons keyed to an item list, fits, fastener numbers and torques."""
import math
from html import escape

import cadquery as cq

from . import hardware as Hh, sheets as S
from .fasteners import FASTENERS

HW = Hh.HW
CHEEK_Y, HUB_Y0, HUB_Y1 = 34.0, 42.0, 52.0
PULLEY_Y = -16.5          # belt plane, inside the motor cheek
PULLEY_W = 17.0


def _load(code):
    ns = {"cq": cq, "math": math}
    exec("import math\n" + code, ns)
    r = ns["result"]
    return r.val() if hasattr(r, "val") else r


def cyl_y(r, y0, y1, x=0.0, z=0.0, r_in=0.0):
    s = cq.Workplane("XZ", origin=(x, y1, z)).circle(r)
    if r_in:
        s = s.circle(r_in)
    return s.extrude(y1 - y0).val()            # XZ normal is -Y: extrude from y1 down to y0


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def joint_items(j):
    """Items of one pitch joint in its own frame H: X back along the incoming tube, Y = joint axis
    (motor side -Y), Z up. Returns [(item_no, part_no, description, qty, spec, solid, style, anchor)]."""
    C, x0 = j["belt_center_mm"], j["block_x0"]
    name = j["name"]
    dps, dpl = j["small_teeth"] * 5 / math.pi, j["large_teeth"] * 5 / math.pi
    cm = _load(Hh.cheek(True, C, x0)).rotate((0, 0, 0), (1, 0, 0), 180).translate((0, -CHEEK_Y, 0))
    cp = _load(Hh.cheek(False, C, x0)).translate((0, CHEEK_Y, 0))
    tb = _load(Hh.tube_block(x0))
    so = _load(Hh.tube_socket()).translate((0, HUB_Y1, 0))
    brg = lambda y0: cyl_y(14, y0, y0 + 8, r_in=6)
    pul = lambda x, dp: (cyl_y(dp / 2, PULLEY_Y - 8.5, PULLEY_Y + 8.5, x=x, r_in=6 if x == 0 else 7)
                         .fuse(cyl_y(dp / 2 + 2.5, PULLEY_Y - 10, PULLEY_Y - 8.5, x=x, r_in=6 if x == 0 else 7))
                         .fuse(cyl_y(dp / 2 + 2.5, PULLEY_Y + 8.5, PULLEY_Y + 10, x=x, r_in=6 if x == 0 else 7)))
    hub = cyl_y(25, HUB_Y1 - 6, HUB_Y1, r_in=6).fuse(cyl_y(12, HUB_Y0, HUB_Y1 - 6, r_in=6))
    gm = (box(-C - 30, -C + 30, -CHEEK_Y - 6 - 10, -CHEEK_Y - 6, -30, 30)
          .fuse(cyl_y(30, -CHEEK_Y - 16 - 70, -CHEEK_Y - 16, x=-C))
          .fuse(box(-C - 28.5, -C + 28.5, -CHEEK_Y - 86 - 76, -CHEEK_Y - 86, -28.5, 28.5))
          .fuse(cyl_y(7, -CHEEK_Y - 6, PULLEY_Y + 8.5, x=-C)))
    tube_in = cyl_y(HW["tube_od"] / 2, -1, 1).rotate((0, 0, 0), (0, 0, 1), 90)   # placeholder replaced below
    tube_in = cq.Workplane("YZ", origin=(x0, 0, 0)).circle(HW["tube_od"] / 2).circle(HW["tube_od"] / 2 - 1.65).extrude(150).val()
    sh = cyl_y(6, -55, 65)
    col = lambda yc: cyl_y(11, yc - 4.5, yc + 4.5, r_in=6)
    f = {k: FASTENERS[k][0].split(",")[0] for k in FASTENERS}
    pn = {"shoulder": ("P-01", "P-02", "P-03"), "elbow": ("P-04", "P-05", "P-06"), "wrist": ("P-07", "P-08", "P-09")}[name]
    big = dict(color="#d9d9d9")
    return [
        (1, pn[0], f"{name}_cheek_motor", 1, "PETG, printed", cm, dict(hatch=45), (-C * 0.5, -CHEEK_Y, 40)),
        (2, pn[1], f"{name}_cheek_plain", 1, "PETG, printed", cp, dict(hatch=45), (x0 + 30, CHEEK_Y, 40)),
        (3, pn[2], f"{name}_tube_block", 1, "PETG, printed", tb, dict(hatch=135), (x0 + 40, 15, 30)),
        (4, "P-10", "tube_socket", 1, "PETG, printed", so, dict(hatch=135, gap=5), (40, HUB_Y1 + 5, 30)),
        (5, "SHAFT-01", "joint shaft Ø12 h6 x 120, one flat", 1, "hardened / 303 SS", sh, dict(nocut=True), (0, 8, 0)),
        (6, "-", "ball bearing 6001-2RS 12x28x8", 2, "bought", brg(CHEEK_Y - 2).fuse(brg(-CHEEK_Y - 6)), dict(hatch=0, gap=3), (-10, CHEEK_Y + 2, 0)),
        (7, "-", f"HTD 5M pulley {j['large_teeth']}T, 15 mm belt, 12 mm bore", 1, "aluminium, bought", pul(0, dpl), dict(hatch=90, gap=4), (dpl / 2 - 6, PULLEY_Y, 0)),
        (8, "-", f"HTD 5M pulley {j['small_teeth']}T, bore = gearbox shaft", 1, "aluminium, bought", pul(-C, dps), dict(hatch=90, gap=4), (-C + dps / 2 - 3, PULLEY_Y, 0)),
        (9, "-", f"HTD 5M belt {j['belt_teeth'] * 5} mm ({j['belt_teeth']}T) x 15 mm", 1, "bought", None, {}, None),
        (10, "-", "shaft collar 12 mm, set screw", 2, "steel, bought", col(-45).fuse(col(CHEEK_Y - 10)), dict(hatch=0, gap=3), (-9, CHEEK_Y - 10, 0)),
        (11, "-", "clamp hub 12 mm bore, 4x M5 on PCD 40", 1, "aluminium, bought", hub, dict(hatch=90, gap=3), (-18, HUB_Y1 - 3, 0)),
        (12, "-", "NEMA 23 + 20:1 planetary gearmotor", 1, "bought", gm, dict(nocut=True), (-C - 20, -CHEEK_Y - 120, 0)),
        (13, "TUBE", "incoming tube 1.5 in OD (broken view)", 1, "6061-T6", tube_in, dict(hatch=45, gap=3), (x0 + 120, 0, 19)),
        (14, "F01", f["F01"] + " + F01W + F01N", 4, "A2-70, 2.5 N·m", None, {}, None),
        (15, "F04", f["F04"] + " + F04W", 4, "2.5 N·m + Loctite 243", None, {}, None),
        (16, "F03", f["F03"] + " + F03W", 4, "A2-70, 2.5 N·m", None, {}, None),
        (17, "F01", "cross pin: " + f["F01"] + " + nyloc", 1, "through block and tube", None, {}, None),
    ]


def _hatch_paths(cut, V, normal, val):
    tri = ""
    for fc in cut.Faces():
        if fc.geomType() != "PLANE":
            continue
        n = fc.normalAt()
        if abs(abs(n.x * normal[0] + n.y * normal[1] + n.z * normal[2]) - 1) > 1e-6:
            continue
        cc = fc.Center()
        if abs((cc.x, cc.y, cc.z)[normal.index(1)] - val) > 1e-3:
            continue
        vs, ts = fc.tessellate(0.05)
        P = [V.pt((q.x, q.y, q.z)) for q in vs]
        tri += "".join(f"M{P[a][0]:.2f},{P[a][1]:.2f}L{P[b][0]:.2f},{P[b][1]:.2f}L{P[c][0]:.2f},{P[c][1]:.2f}Z" for a, b, c in ts)
    return tri


def balloon(x, y, n, tx, ty):
    return (f'<g stroke="{S.INK}" fill="none" stroke-width="0.9"><line x1="{tx}" y1="{ty}" x2="{x}" y2="{y}"/>'
            f'<circle cx="{tx}" cy="{ty}" r="2.2" fill="{S.INK}"/><circle cx="{x}" cy="{y}" r="12" fill="#fff"/></g>'
            f'<text x="{x}" y="{y + 4.5}" font-size="12.5" font-weight="bold" text-anchor="middle">{n}</text>')


def leader(tx, ty, x, y, text, anchor="start"):
    lines = text.split("\n")
    t = "".join(f'<text x="{x + (4 if anchor == "start" else -4)}" y="{y - 3 + 12.5 * i}" font-size="10.5" text-anchor="{anchor}">{escape(l)}</text>' for i, l in enumerate(lines))
    w = 5.3 * max(len(l) for l in lines) + 8          # approx. text width at 10.5 px
    ex = x + w if (anchor == "start" and tx > x + w) else x   # land on the side that faces the target
    ey = y - 7
    return (f'<g stroke="{S.DIM}" fill="none" stroke-width="0.8"><line x1="{tx}" y1="{ty}" x2="{ex}" y2="{ey}"/>'
            f'<circle cx="{tx}" cy="{ty}" r="1.8" fill="{S.DIM}"/></g><g fill="{S.DIM}">{t}</g>')


def table(x, y, cols, rows, title=None, fs=10):
    """cols: [(header, width)]; returns svg and height."""
    rh = fs + 7
    out = f'<g font-size="{fs}">'
    yy = y
    if title:
        out += f'<text x="{x}" y="{yy - 6}" font-size="12" font-weight="bold">{escape(title)}</text>'
    w = sum(c[1] for c in cols)
    out += f'<rect x="{x}" y="{yy}" width="{w}" height="{rh}" fill="#eef1f4" stroke="{S.INK}" stroke-width="0.8"/>'
    cx = x
    for h, cw in cols:
        out += f'<text x="{cx + 4}" y="{yy + rh - 5}" font-weight="bold">{escape(h)}</text>'
        cx += cw
    yy += rh
    for r in rows:
        out += f'<rect x="{x}" y="{yy}" width="{w}" height="{rh}" fill="none" stroke="{S.INK}" stroke-width="0.5"/>'
        cx = x
        for (h, cw), v in zip(cols, r):
            out += f'<text x="{cx + 4}" y="{yy + rh - 5}">{escape(str(v))}</text>'
            cx += cw
        yy += rh
    cx = x
    for h, cw in cols[:-1]:
        cx += cw
        out += f'<line x1="{cx}" y1="{y}" x2="{cx}" y2="{yy}" stroke="{S.INK}" stroke-width="0.5"/>'
    return out + "</g>", yy - y


def joint_section(model, which="shoulder"):
    J = {j["name"]: j for j in model["joints"]}
    j = J[which]
    items = joint_items(j)
    S.VIEWS["JSEC"] = ((0, 0, 1), (0, 1, 0))        # look down Z, joint axis to the right, incoming tube downward
    S.VIEWS["JSIDE"] = ((0, -1, 0), (0, 0, 1))      # from the motor side, same vertical as the section
    big = 1e4
    keep = cq.Solid.makeBox(big, big, big, cq.Vector(-big / 2, -big / 2, -big))      # z <= 0
    cuts, whole = [], []
    for it in items:
        sol = it[5]
        if sol is None:
            continue
        if it[6].get("nocut"):
            cuts.append((it, sol, False))
        else:
            cuts.append((it, sol.intersect(keep), True))
        whole.append(sol)
    comp = cq.Compound.makeCompound([c[1] for c in cuts])
    V = S.View(comp, "JSEC")
    scale = 0.5
    s = S.PXMM * scale
    V.place(70, 110, s)
    body = ""
    # per-item hatching (adjacent parts at different angles / spacing)
    defs = "<defs>"
    for it, cut, hatched in cuts:
        st = it[6]
        if not hatched or "hatch" not in st:
            continue
        pid = f"h{it[0]}"
        gap = st.get("gap", 7)
        defs += (f'<pattern id="{pid}" width="{gap}" height="{gap}" patternUnits="userSpaceOnUse" patternTransform="rotate({st["hatch"]})">'
                 f'<line x1="0" y1="0" x2="0" y2="{gap}" stroke="{S.INK}" stroke-width="0.6"/></pattern>')
        tri = _hatch_paths(cut, V, (0, 0, 1), 0.0)
        body += f'<path d="{tri}" fill="url(#{pid})" stroke="none"/>'
    defs += "</defs>"
    body = defs + body + V.svg()
    body += f'<text x="{V.ox}" y="{V.oy - 40}" font-size="15" font-weight="bold">SECTION A-A  ({which.upper()} JOINT, scale 1:2)</text>'
    body += f'<text x="{V.ox}" y="{V.oy - 24}" font-size="10.5">Cut on the plane through the joint axis and the incoming tube. Shaft and gearmotor not sectioned (convention).</text>'
    P = V.pt
    # ---- belt (in plane PULLEY_Y, drawn as the two straight runs seen edge-on: a band between pulleys)
    C = j["belt_center_mm"]
    y_b = PULLEY_Y
    a1, a2 = P((-C, y_b - 7.5, 0)), P((0, y_b + 7.5, 0))
    body += f'<rect x="{min(a1[0], a2[0])}" y="{min(a1[1], a2[1])}" width="{abs(a2[0] - a1[0])}" height="{abs(a2[1] - a1[1])}" fill="none" stroke="{S.INK}" stroke-width="0.8" stroke-dasharray="10,3,2,3"/>'
    # ---- centre lines
    ca, cb = P((0, -CHEEK_Y - 25, 0)), P((0, HUB_Y1 + 70, 0))
    body += f'<line x1="{ca[0]}" y1="{ca[1]}" x2="{cb[0]}" y2="{cb[1]}" stroke="{S.CEN}" stroke-width="0.8" stroke-dasharray="18,4,3,4"/>'
    ma, mb = P((-C, -CHEEK_Y - 170, 0)), P((-C, PULLEY_Y + 20, 0))
    body += f'<line x1="{ma[0]}" y1="{ma[1]}" x2="{mb[0]}" y2="{mb[1]}" stroke="{S.CEN}" stroke-width="0.8" stroke-dasharray="18,4,3,4"/>'
    # ---- dimensions (true values from the model)
    x0 = j["block_x0"]
    yb = P((x0 + 50, 0, 0))[1] + 46
    p1, p2 = P((x0 + 50, -CHEEK_Y + 6, 0)), P((x0 + 50, CHEEK_Y - 6, 0))
    body += S.hdim(p1[0], p2[0], yb, mm_in_s(2 * CHEEK_Y - 12, 1), p1[1])
    q1, q2 = P((x0 + 50, -CHEEK_Y - 6, 0)), P((x0 + 50, CHEEK_Y + 6, 0))
    body += S.hdim(q1[0], q2[0], yb + 30, mm_in_s(2 * CHEEK_Y + 12, 1) + " over cheeks", q1[1])
    # axis -> block face, block length
    r0, r1, r2 = P((0, CHEEK_Y + 6, 0)), P((x0, CHEEK_Y + 6, 0)), P((x0 + 50, CHEEK_Y + 6, 0))
    xr = max(V.pt((0, HUB_Y1 + 75, 0))[0], r0[0]) + 30
    body += S.vdim(xr, r0[1], r1[1], mm_in_s(x0, 1), r0[0])
    body += S.vdim(xr, r1[1], r2[1], mm_in_s(50, 1), r1[0])
    # motor centre distance
    m0, m1 = P((0, -CHEEK_Y - 6, 0)), P((-C, -CHEEK_Y - 6, 0))
    xl = V.ox - 26
    body += S.vdim(xl, m1[1], m0[1], f"C {mm_in_s(C, 1)}", m0[0])
    # shaft length
    s0, s1 = P((0, -55, 0)), P((0, 65, 0))
    ys = V.oy - 8
    body += S.hdim(s0[0], s1[0], ys, "SHAFT-01 " + mm_in_s(120, 0), s0[1])
    # ---- leaders: fits and features; texts sit in the free areas left of the incoming tube and above the plain side
    L0 = 60
    body += leader(*P((-14, CHEEK_Y + 2, 0)), 585, 150,
                   f"BEARING SEAT Ø{HW['bearing_od'] + 0.15:.2f} [{S.inch(HW['bearing_od'] + 0.15)}] x {HW['bearing_w'] + 0.2:.1f} DP\n6001-2RS light press,\nboth cheeks, outer faces")
    body += leader(*P((0, 50, 6)), 585, 205,
                   "Ø12 h6 SHAFT (0/-0.011) in\n6001 bore Ø12 (0/-0.008); flat 0.5 deep\nunder the pulley and collar set screws")
    hb = P((30, HUB_Y1 + 5, 0))
    body += leader(hb[0], hb[1], 585, 258, "4x F03 M5 x 16: tube_socket to clamp hub,\nPCD 40, 2.5 N·m; clamp the hub after")
    sl = P((-C - 23.57, -CHEEK_Y - 6, 0))
    body += leader(sl[0], sl[1], L0, 300, "4x SLOT 5.5 x 14 for F04 (gearmotor):\n±4 [.17] belt tension travel")
    pp = P((dpl_r(j) + 2.5, PULLEY_Y, 0))
    body += leader(pp[0], pp[1], L0, 560,
                   f"{j['large_teeth']}T pulley: OD {2 * dpl_r(j) + 5:.0f} over flanges,\nclears the tube block by {x0 - dpl_r(j) - 2.5:.1f} [{S.inch(x0 - dpl_r(j) - 2.5)}]")
    bb = P((x0 + 8, -CHEEK_Y - 6, 0))
    body += leader(bb[0], bb[1], L0, 612, "4x F01 M5 x 90 cheek-block-cheek,\nwashers both sides, nyloc, 2.5 N·m")
    pin = P((x0 + 25, -10, 0))
    body += leader(pin[0], pin[1], L0, 664, "CROSS PIN Ø5.5 THRU block + tube: F01, nyloc;\ndrill the tube through the block (25 from its end)")
    # ---- balloons (offsets in sheet px, chosen to land in clear space)
    OFF = {1: (-70, 40), 2: (60, 30), 3: (60, 34), 4: (60, -10), 5: (-20, -110), 6: (40, -120), 7: (-90, 40), 8: (60, -40),
           10: (-10, -150), 11: (95, -20), 12: (-20, 115), 13: (50, 0)}
    for it in items:
        if it[7] is None:
            continue
        ax, ay = P(it[7])
        dx, dy = OFF.get(it[0], (40, -40))
        body += balloon(ax + dx, ay + dy, it[0], ax, ay)
    # ---- side view from the motor side (whole parts, hidden lines off)
    side = cq.Compound.makeCompound([it[5] for it in items if it[5] is not None and it[0] in (1, 7, 8, 12, 13)])
    SV = S.View(side, "JSIDE")
    SV.iso = True                                   # visible lines only: keeps the belt geometry readable
    SV.place(V.ox + V.pw + 140, 110, s)
    body += SV.svg()
    body += f'<text x="{SV.ox}" y="{SV.oy - 40}" font-size="15" font-weight="bold">VIEW B (from the motor side, 1:2)</text>'
    # belt tangents in the side view
    dps_r, dpl_rr = j["small_teeth"] * 5 / math.pi / 2, dpl_r(j)
    PS = SV.pt
    for sgn in (1, -1):
        a = PS((-C, -CHEEK_Y - 6, sgn * dps_r)); b = PS((0, -CHEEK_Y - 6, sgn * dpl_rr))
        body += f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{S.TAG}" stroke-width="1.6"/>'
    c0, c1 = PS((0, 0, 0)), PS((-C, 0, 0))
    body += f'<circle cx="{c0[0]}" cy="{c0[1]}" r="{dpl_rr * s}" fill="none" stroke="{S.TAG}" stroke-width="1.6" stroke-dasharray="4,3"/>'
    body += f'<circle cx="{c1[0]}" cy="{c1[1]}" r="{dps_r * s}" fill="none" stroke="{S.TAG}" stroke-width="1.6" stroke-dasharray="4,3"/>'
    body += S.vdim(SV.ox + SV.pw + 22, c1[1], c0[1], f"C {mm_in_s(C, 1)}", c0[0])
    body += f'<text x="{SV.ox}" y="{SV.oy + SV.ph + 22}" font-size="10.5" fill="{S.TAG}">Belt pitch circles dashed, belt runs solid.</text>'
    # ---- item list
    rows = [(it[0], it[1], it[2], it[3], it[4]) for it in items]
    t, th = table(1060, 112, [("ITEM", 36), ("PART NO.", 66), ("DESCRIPTION", 278), ("QTY", 34), ("MATERIAL / SPEC", 106)], rows,
                  f"ITEM LIST, {which.upper()} JOINT (per joint)", fs=9.5)
    body += t
    # ---- joint table (all three joints differ only here)
    jr = []
    for n in ("shoulder", "elbow", "wrist"):
        q = J[n]
        jr.append((n, f"{q['belt_ratio']}:1", f"{q['small_teeth']}T / {q['large_teeth']}T", mm_in_s(q["belt_center_mm"], 1),
                   f"{q['belt_teeth']}T ({q['belt_teeth'] * 5} mm)", mm_in_s(q["block_x0"], 0), f"{q['total_ratio']}:1"))
    t2, th2 = table(1060, 112 + th + 34, [("JOINT", 62), ("BELT", 40), ("PULLEYS", 82), ("CENTRE C", 98), ("BELT", 98), ("AXIS-BLOCK", 74), ("TOTAL", 66)],
                    jr, "JOINT TABLE (elbow and wrist are built the same way)", fs=9.5)
    body += t2
    notes = ["Section at true scale 1:2 from the CAD solids; all dims mm [in].",
             "Press bearings square with an arbor press; seat must not crack (PETG).",
             "Pulleys: set screws on the shaft / gearbox flats, blue threadlocker.",
             "Belt tension: about 3 mm deflection at mid-span under finger load.",
             "Torques: F01, F03, F04 2.5 N·m (screws into PETG: snug, do not crush).",
             "Shaft axial play: collars against bearing inner races, 0.1 mm max.",
             "Gearbox flange, shaft and pilot: MEASURE, then python run.py build.",
             "Fastener specs: fab/FASTENERS.md. Part drawings: P-01..P-10.",
             "Check the joint turns its full range by hand before wiring."]
    body += S.notes_block(notes)
    body += S.title_block(dict(title=f"PITCH JOINT ASSEMBLY - SECTION", partno="ASM-002", material="see item list", process="assembly",
                               qty="3 joints", mass="-", scale="1:2", rev="B", assy=f"drawn for the {which} joint"))
    return S.halo(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S.W} {S.H}" width="{S.W}" height="{S.H}" font-family="Helvetica,Arial,sans-serif">{S.frame()}{body}</svg>')


def dpl_r(j):
    return j["large_teeth"] * 5 / math.pi / 2


def mm_in_s(v, d=1):
    return S.mm_in(v, d)


# ---------------------------------------------------------------- ASM-001 general arrangement
# Views come from the 3D twin itself (tools/ga.js renders hidden-line views of the assembled table in a headless
# browser), so the GA always shows exactly what the app, the guide and the kit show. Same run exports every part as an
# STL in its assembled position (design/cad/stl/assembly/) with parts.json, which the Anatomy live 3D viewer reads.
CAT_ORDER = ["Printed parts", "Cut and machined parts", "Stock materials", "Purchased mechanical", "Motors", "Electronics", "Wiring"]


def run_ga(root, stl_dir, out_json, timeout=900):
    """Run tools/ga.js; returns the parsed views or None if node/playwright is not available."""
    import json, shutil as _sh, subprocess
    node = _sh.which("node")
    if not node:
        return None
    r = subprocess.run([node, str(root / "tools" / "ga.js"), str(root), str(out_json), str(stl_dir)],
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 or not out_json.exists():
        print("ASM-001 views skipped:", (r.stderr or r.stdout).strip()[-300:])
        return None
    print(r.stdout.strip())
    return json.loads(out_json.read_text(encoding="utf-8"))


def items_from(ga, model):
    """Item list in category order; one item per catalog key the views found."""
    names = ga["names"]
    pn = {p["id"]: p for p in model.get("printed", [])}
    fab = {f["pid"]: f for f in model.get("fabricated", [])}
    keys = sorted(names, key=lambda k: (CAT_ORDER.index(names[k]["cat"]) if names[k]["cat"] in CAT_ORDER else 99, list(pn).index(k) if k in pn else 0, k))
    rows = []
    for i, k in enumerate(keys, 1):
        n = names[k]
        mat = fab[k]["material"] if k in fab else ("PETG, printed" if n["cat"] == "Printed parts" else
                                                  {"Motors": "bought", "Electronics": "bought", "Purchased mechanical": "bought"}.get(n["cat"], ""))
        part = k if (k in fab or k.upper() == k) else (f"P-{list(pn).index(k) + 1:02d}" if k in pn else "")
        qty = n["qty"] if isinstance(n["qty"], (int, float)) and n["qty"] else n["n"]
        rows.append(dict(note=n.get("note") or "", item=i, key=k, part=part or "-", name=n["name"], qty=qty, cat=n["cat"], material=mat,
                         drawing=(pn[k].get("drawing") if k in pn else None)))
    return rows


def parts_json(rows):
    return {f"{r['key'].replace('/', '_')}.stl": {"item": r["item"], "name": r["name"], "part_no": r["part"], "category": r["cat"],
                                                   "qty": r["qty"], "material": r["material"], "note": r.get("note", ""), "drawing": r["drawing"]} for r in rows}


def _balloon_rows(anchors, ox, oy, y_row, x_min, x_max, gap=26):
    """Spread balloons along a row at y_row, as close as possible to their anchors' x, without overlapping."""
    a = sorted(anchors, key=lambda t: t[1])
    xs = [max(x_min, min(x_max, t[1])) for t in a]
    for _ in range(60):                       # relax: push apart, then pull back inside
        for i in range(1, len(xs)):
            if xs[i] - xs[i - 1] < gap:
                m = (xs[i] + xs[i - 1]) / 2; xs[i - 1], xs[i] = m - gap / 2, m + gap / 2
        xs = [max(x_min, min(x_max, x)) for x in xs]
    return [(t[0], x, y_row, t[1], t[2]) for t, x in zip(a, xs)]


def general_arrangement(ga, model):
    P = S.PXMM
    rows = items_from(ga, model)
    num = {r["key"]: r["item"] for r in rows}
    F, T = ga["views"]["FRONT"], ga["views"]["TOP"]
    x0 = 60
    ty = 120
    fy = ty + T["h"] * P + 95
    body = ''
    body += f'<text x="{x0}" y="62" font-size="15" font-weight="bold">GENERAL ARRANGEMENT, scale 1:10, pose: all joints 0° (full reach)</text>'
    body += f'<text x="{x0}" y="78" font-size="10.5">Hidden-line views of the assembled 3D model (the same model the app and the build guide use). Table top = datum.</text>'
    for V, y, lab in ((T, ty, "TOP VIEW"), (F, fy, "FRONT VIEW (from the operator side, -Y)")):
        body += f'<image x="{x0}" y="{y}" width="{V["w"] * P}" height="{V["h"] * P}" href="{V["png"]}"/>'
        body += f'<text x="{x0}" y="{y - 8}" font-size="11.5" font-weight="bold">{lab}</text>'
    sc = ga["scale"]

    def fp(V, vy, X, Y, Z, top=False):
        u = X
        w = Y if top else Z
        return x0 + (u - V["u0"]) * sc * P, vy + (V["w1"] - w) * sc * P
    pts = ga["pts"]
    (bx0, by0, bz0), (bx1, by1, bz1) = ga["pts"]["bbox"]
    sh, el, wr, tcp = pts["shoulder"], pts["elbow"], pts["wrist"], pts["tcp"]
    # ---- FRONT dims
    fb = fy + F["h"] * P
    a, b = fp(F, fy, 0, 0, sh[2]), fp(F, fy, el[0], 0, el[2])
    c, d = fp(F, fy, wr[0], 0, wr[2]), fp(F, fy, tcp[0], 0, tcp[2])
    yd = fb + 26
    body += S.hdim(a[0], b[0], yd, f"L1 {mm_in_s(el[0] - sh[0], 0)}", a[1])
    body += S.hdim(b[0], c[0], yd, f"L2 {mm_in_s(wr[0] - el[0], 0)}", b[1])
    body += S.hdim(a[0], d[0], yd + 30, f"REACH (yaw axis to gripper TCP) {mm_in_s(tcp[0], 0)}", d[1])
    l0, r0 = fp(F, fy, bx0, 0, bz0), fp(F, fy, bx1, 0, bz0)
    body += S.hdim(l0[0], r0[0], yd + 60, f"OVERALL {mm_in_s(bx1 - bx0, 0)}", l0[1])
    base = fp(F, fy, bx1, 0, bz0)
    xs = max(fp(F, fy, bx1, 0, 0)[0], d[0]) + 26
    body += S.vdim(xs, a[1], base[1], f"SHOULDER AXIS {mm_in_s(sh[2] - bz0, 0)}", a[0])
    top_ = fp(F, fy, 0, 0, bz1)
    body += S.vdim(xs + 34, top_[1], base[1], f"OVERALL {mm_in_s(bz1 - bz0, 0)}", top_[0])
    for p_, n_ in ((a, "J2"), (b, "J3"), (c, "J4")):
        body += f'<g stroke="{S.CEN}" stroke-width="0.7"><line x1="{p_[0] - 9}" y1="{p_[1]}" x2="{p_[0] + 9}" y2="{p_[1]}"/><line x1="{p_[0]}" y1="{p_[1] - 9}" x2="{p_[0]}" y2="{p_[1] + 9}"/></g>'
    yx = fp(F, fy, 0, 0, bz1 + 40)
    body += f'<line x1="{yx[0]}" y1="{yx[1]}" x2="{yx[0]}" y2="{base[1] + 8}" stroke="{S.CEN}" stroke-width="0.8" stroke-dasharray="18,4,3,4"/>'
    body += f'<text x="{yx[0] + 4}" y="{yx[1] + 2}" font-size="10" fill="{S.DIM}">J1 YAW AXIS</text>'
    # ---- TOP dims
    tl, tr_ = fp(T, ty, bx0, by0, 0, True), fp(T, ty, bx0, by1, 0, True)
    body += S.vdim(x0 - 22, tr_[1], tl[1], f"{mm_in_s(by1 - by0, 0)}", tl[0])
    # ---- balloons: each item once, in the view where most of it shows, on rows outside the views
    rows_by_view = {"FRONT": [], "TOP": []}
    for r in rows:
        k = r["key"]
        af, at = F["anchors"].get(k), T["anchors"].get(k)
        if not af and not at:
            continue
        use = "FRONT" if af and (not at or af["area"] >= 0.6 * at["area"]) else "TOP"
        A = af if use == "FRONT" else at
        V, vy = (F, fy) if use == "FRONT" else (T, ty)
        rows_by_view[use].append((r["item"], x0 + A["x"] * P, vy + A["y"] * P))
    xmax = x0 + max(F["w"], T["w"]) * P
    out = []
    for name, (V, vy) in (("FRONT", (F, fy)), ("TOP", (T, ty))):
        lst = rows_by_view[name]
        mid = vy + V["h"] * P / 2
        up = [t for t in lst if t[2] <= mid]
        dn = [t for t in lst if t[2] > mid]
        y_up = vy - 26 if name == "FRONT" else vy - 26
        y_dn = vy + V["h"] * P + (118 if name == "FRONT" else 22)
        for grp, yr, alt in ((up, y_up, -24), (dn, y_dn, 24)):
            if len(grp) > (xmax - x0) / 26:          # too many for one row: two staggered rows
                g1, g2 = grp[::2], grp[1::2]
                out += _balloon_rows(g1, x0, vy, yr, x0, xmax) + _balloon_rows(g2, x0, vy, yr + alt, x0, xmax)
            else:
                out += _balloon_rows(grp, x0, vy, yr, x0, xmax)
    for n, bx, byy, ax, ay in out:
        body += balloon(bx, byy, n, ax, ay).replace('r="12"', 'r="10"').replace('font-size="12.5"', 'font-size="10"').replace(f'y="{byy + 4.5}"', f'y="{byy + 3.6}"')
    # ---- item list (whole table)
    t, th = table(1060, 40 + 14, [("ITEM", 30), ("PART", 64), ("DESCRIPTION", 280), ("QTY", 30), ("MATERIAL", 116)],
                  [(r["item"], r["part"], r["name"][:58], r["qty"], r["material"][:24]) for r in rows],
                  "PARTS LIST, ONE ARM AND TEST TABLE", fs=8)
    body += t
    notes = ["All dims mm [in]. Views at 1:10 from the assembled 3D model.",
             "Detail of each pitch joint: ASM-002. Wiring: ELE-001.",
             "Part drawings: P-xx (printed), BASE/YAW/ENC/GSK/TUBE/SHAFT (cut).",
             "Fasteners F01..F18 and torques: fab/FASTENERS.md.",
             "Build order: the assembly guide (docs/design), 14 steps.",
             "Purchase: BOM.md and the build kit's shopping list."]
    body += S.notes_block(notes, x=x0 + 0, y=S.H - 20 - 136, w=560, h=116)
    body += S.title_block(dict(title="ROBOT ARM TEST TABLE - GENERAL ARRANGEMENT", partno="ASM-001", material="see parts list",
                               process="assembly", qty="1", mass="-",
                               scale="1:10", rev="B", assy="whole table, joints at 0°"))
    return S.halo(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {S.W} {S.H}" width="{S.W}" height="{S.H}" font-family="Helvetica,Arial,sans-serif">{S.frame()}{body}</svg>')
