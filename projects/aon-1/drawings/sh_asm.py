"""AON-1 assembly drawings: AON-001 general arrangement + CDS compliance, AON-002 section + item list, AON-003 illustrated assembly steps."""
import base64
import math

from common import *  # noqa: F401,F403
from sh_parts import frame_outline, rr, ZA, ZB, U_HOLE, CSK_D, CL, AL_FILL, zscrew

E, FR = D.ENV, D.FR
RAIL, H, RI, L = E["rail"], D.HALF, D.RI, E["L"]
X0, X1, B0, T = FR["bar_x0"], FR["bar_x1"], FR["blk0"], FR["t"]
HP = D.BRD["hp"]
P, C = D.PANEL, D.CELL
CELLF, FR4F, BATF = "#c5cae9", "#e8f5e9", "#bbdefb"
RC = H - RAIL / 2                       # rail centre 45.75


def img(S, path, x, y, w, h):
    b = base64.b64encode(path.read_bytes()).decode()
    S.add(f'<image href="data:image/png;base64,{b}" x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"/>')


# ------------------------------------------------------------------ mass properties
MASS_ITEMS = [  # name, g, z (mm from -Z rail end); x, y offsets are symmetric to < 2 mm
    ("rails (4)", 4 * MASS["AON-101"] * 1000, L / 2), ("-Z frame", MASS["AON-103"] * 1000, FR["z"][0] + T / 2),
    ("mid frame", MASS["AON-104"] * 1000, D.Z_MID), ("+Z frame", MASS["AON-105"] * 1000, FR["z"][2] + T / 2),
    ("E07 + Z coil + nuts", 60, 3.5), ("E02 + 4 cells + holder", 48 + 4 * 47 + 38, 45.0), ("E01 EPS", 62, 85.0), ("E03 OBC", 55, 113.0),
    ("E04 COM", 85, 192.0), ("E05 antenna", 70, 338.0), ("E06 panels (4) with cells", 4 * (72 + 7 * 2.6), 168.75),
    ("rods, spacers, standoffs", 64, 169.0), ("harness", 55, 110.0), ("switches, springs, brackets", 22 + 1.2, 170.0), ("fasteners", 30, 170.0), ("thermal", 25, 45.0),
]
M_TOT = sum(m for _, m, _ in MASS_ITEMS)
CG_Z = sum(m * z for _, m, z in MASS_ITEMS) / M_TOT


def rails_front(v, faceholes, sgn_holes, spring_at=None, switch_at=None):
    """elevation of one long face (horizontal = in-face axis u, -50..50; vertical = Z)."""
    for u0 in (-H, RI):
        v.rect(u0, 0, RAIL, L, fill="#cfd8dc")
        v.line(u0 + 1.0, 0, u0 + 1.0, L, "thin"); v.line(u0 + RAIL - 1.0, 0, u0 + RAIL - 1.0, L, "thin")
    v.rect(-P["w"] / 2, P["z0"], P["w"], P["L"], fill=FR4F)
    for k in range(C["n_per_face"]):
        z = D.CELL_Z0 + k * (C["w"] + D.GAP_CELL)
        v.rect(-C["l"] / 2, z, C["l"], C["w"], fill=CELLF)
    for zz in (FR["z"][0] + T / 2, FR["z"][2] + T / 2):
        for yy in (-P["hole_y"], P["hole_y"]):
            v.circle(yy, zz, 1.9); v.circle(yy, zz, 1.0, "thin")
    for i in range(3):
        v.line(-RI, FR["z"][i], RI, FR["z"][i], "hid"); v.line(-RI, FR["z"][i] + T, RI, FR["z"][i] + T, "hid")
    for z in faceholes:
        for s in (-1, 1):
            v.circle(s * D.RAIL_SCREW["bar_mid"], z, CSK_D / 2)
    if spring_at is not None:
        v.rect(spring_at - 1.2, L, 2.4, D.SPRING["protrude"], fill="#90a4ae")
    if switch_at is not None:
        v.rect(switch_at - 1.0, -D.SWITCH["protrude"], 2.0, D.SWITCH["protrude"] + 1.0, fill="#424242")


# ================================================================== AON-001 general arrangement
def ga():
    S = sheet("AON-001", "GENERAL ARRANGEMENT AND CUBESAT ENVELOPE", scale="1:1 · 2:1", material="see AON-002 item list", finish="-",
              mass=f"{M_TOT:.0f} g CBE [{M_TOT / 453.6:.2f} lb]; {M_TOT * 1.2:.0f} g with 20 % margin")
    s1 = SC(1)
    oy = 1800
    v = S.view(560, oy, s1, "VIEW ON +X FACE (1:1) · +Y to the right", (330, oy - L * s1 - 130))
    rails_front(v, ZB, 1, spring_at=-RC, switch_at=X0 + 2.0)
    v.dim((-H, L), (H, L), 60, mmi(E["w"], 1), "h", tol="±0.1 [±.004]")
    v.dim((-H, 0), (-H, L), 80, mmi(L, 1), "v", tol="±0.3 [±.012]")
    v.dim((RI, 0), (H, 0), -50, mmi(RAIL, 1), "h", tol="MIN")
    v.dim((H, P["z0"]), (H, P["z1"]), -50, mmi(P["L"], 1), "v")
    v.dim((H, 0), (H, FR["z"][0]), -110, mmi(FR["z"][0], 1), "v")
    v.dim((H, FR["z"][2] + T), (H, L), -110, mmi(L - FR["z"][2] - T, 1), "v")
    v.leader((-RC, L + D.SPRING["protrude"]), (-80, L + 10), ["SEPARATION SPRING BP-04,", "2.0 [.079] PROUD (AON-102)"], 12, anchor="end")
    v.leader((X0 + 2.0, -D.SWITCH["protrude"]), (-80, -14), ["SWITCH LEVER 1.5 [.059]", "PROUD (AON-101)"], 12, anchor="end")
    v.leader((-20, D.CELL_Z0 + 100), (-80, 150), ["7 CIC CELLS PER FACE (BP-01),", "0 protrusion (limit 6.5)"], 12, anchor="end")
    v.text(4, CG_Z + 5, "CG", 14, "start", color="#b00020")
    v.circle(0, CG_Z, 3.0, "vis", "#b00020")
    v.dim((-H, 0), (0, CG_Z), 0, None, "v") if False else None
    # side view on +Y
    v2 = S.view(1200, oy, s1, "VIEW ON +Y FACE (1:1) · -X to the right", (1000, oy - L * s1 - 130))
    rails_front(v2, ZA, 1, spring_at=RC, switch_at=None)
    v2.dim((-H, L), (H, L), 60, mmi(E["w"], 1), "h", tol="±0.1")
    for i in range(3):
        v2.dim((H, 0), (H, FR["z"][i]), -60 - 45 * i, mmi(FR["z"][i], 2), "v")
    v2.note(-H, -26, ["dashed: frame -Z faces (frames 10.0 [.394] thick)"], 12)
    # top view +Z 2:1
    s2 = SC(2)
    v3 = S.view(1960, 560, s2, "VIEW ON +Z (2:1) · X right, Y up", (1590, 120))
    frame_outline(v3)
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        rr(v3, min(sx * RI, sx * H), min(sy * RI, sy * H), RAIL, RAIL, 1.0, fill="#cfd8dc")
    w, ch = D.BRD["w"] / 2, D.BRD["corner_ch"]
    v3.poly([(-w + ch, -w), (w - ch, -w), (w, -w + ch), (w, w - ch), (w - ch, w), (-w + ch, w), (-w, w - ch), (-w, -w + ch)], fill=FR4F)
    for s in (1, -1):
        v3.rect(-34, min(s * 26.3, s * 39.0), 68, 12.7, fill="#ffe082")
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        v3.circle(sx * HP, sy * HP, 3.2); v3.circle(sx * HP, sy * HP, 1.6, "thin")
    for sx, sy in ((1, -1), (-1, 1)):
        v3.circle(sx * RC, sy * RC, 1.2, fill="#90a4ae"); v3.cmark(sx * RC, sy * RC, 1.2)
    for s in (1, -1):
        v3.rect(X1, -P["w"] / 2, P["t"], P["w"], fill=FR4F); v3.rect(-P["w"] / 2, s * X1 if s > 0 else -X1 - P["t"], P["w"], P["t"], fill=FR4F)
    v3.dim((-H, -H), (H, -H), -50, mmi(E["w"], 1), "h", tol="±0.1")
    v3.dim((H, -H), (H, H), -50, mmi(E["w"], 1), "v", tol="±0.1")
    v3.dim((-H, -H), (-RC, -H), -100, mmi(RAIL / 2, 2), "h")
    v3.leader((RC, -RC), (40, -70), ["SPRING PLUNGER ON THE RAIL AXIS"], 12)
    v3.leader((0, 33), (20, 70), ["E05 + 2 UHF TAPE ELEMENTS (stowed, wound on the board)", "Dyneema restraint over burn resistors R1/R2"], 12)
    # bottom view -Z 2:1
    v4 = S.view(1960, 1460, s2, "VIEW ON -Z (2:1) · X right, Y DOWN (seen from below)", (1590, 1035))
    frame_outline(v4)
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        rr(v4, min(sx * RI, sx * H), min(sy * RI, sy * H), RAIL, RAIL, 1.0, fill="#cfd8dc")
    v4.poly([(-w + ch, -w), (w - ch, -w), (w, -w + ch), (w, w - ch), (w - ch, w), (-w + ch, w), (-w, w - ch), (-w, -w + ch)], fill=FR4F)
    v4.poly([(-33, -33), (33, -33), (33, 33), (-33, 33)], "phan")
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        v4.poly([(sx * HP + 2.75 * math.cos(math.radians(a)), sy * HP + 2.75 * math.sin(math.radians(a))) for a in range(0, 360, 60)])
    for sx, sy in ((1, 1), (-1, -1)):           # Y is flipped in this view
        v4.rect(min(sx * (X0 + 1.0), sx * (X0 + 3.0)), min(-sy * 39.0, -sy * (RI + 4.0)), 2.0, 6.5, fill="#424242")
    v4.leader((X0 + 2.0, -(RI + 2)), (30, -66), ["SW1 LEVER IN THE RAIL NOTCH (+X+Y)"], 12)
    v4.leader((-(X0 + 2.0), RI + 2), (-20, 64), ["SW2 LEVER (-X-Y)"], 12)
    v4.leader((20, 20), (30, 30), ["E07: -Z SUN SENSOR, Z TORQUER (phantom, under)"], 12)
    # tables
    m = BASIS["mass"]
    rows = [
        ("Envelope X, Y", "100.0 ±0.1 [3.937 ±.004]", "100.0 ±0.1 (frames 83.00 +0/-0.05 + 2 rails)", "✓"),
        ("Length Z", "340.5 ±0.3 [13.406 ±.012]", "340.5 ±0.1 (rail)", "✓"),
        ("Rail width / edge radius", "≥ 8.5 / ≥ R1", "8.50 ±0.02 / R1.0", "✓"),
        ("Rail surface", "hard anodised", "MIL-A-8625 Type III", "✓"),
        ("Protrusion past rail plane", "≤ 6.5 [.256]", "0 (cells 0.1 below the plane)", "✓"),
        ("Mass", f"≤ {E['m_max'] * 1000:.0f} g (target {E['m_target'] * 1000:.0f})", f"{M_TOT:.0f} g CBE, {M_TOT * 1.2:.0f} g +20 %", "✓"),
        ("CG from geometric centre", "X, Y ≤ 20; Z ≤ 70", f"X, Y < 2; Z {CG_Z - L / 2:+.1f}", "✓"),
        ("Deployment switches", "≥ 1 on rail standoffs, cut all power", "2 (SW1 in V+, SW2 in V-)", "✓"),
        ("Separation springs", "on +Z rail ends", "2 plungers, 3-7 N", "✓"),
        ("Remove-before-flight", "accessible, inhibits", "RBF1 on +X panel port", "✓"),
        ("Deployables / RF delay", "≥ 30 min / ≥ 45 min", "firmware + E04 hardware timer", "✓"),
        ("Materials", "ASTM E595 TML < 1 %, CVCM < 0.1 %", "per AON-600 notes", "✓"),
    ]
    S.table(2400, 200, [("CUBESAT DESIGN SPEC rev 14.1, 3U", 300), ("REQUIRED", 290), ("AON-1", 380), ("", 30)], rows, "ENVELOPE AND COMPLIANCE", 12, 26)
    S.table(2400, 600, [("MASS PROPERTIES (CBE)", 420), ("g", 110), ("Z mm", 110)], [(n, f"{g:.0f}", f"{z:.1f}") for n, g, z in MASS_ITEMS] +
            [("TOTAL / CG", f"{M_TOT:.0f}", f"{CG_Z:.1f}")], None, 12, 22)
    S.notes(2400, 1000 + 22 * len(MASS_ITEMS) - 20, 1010, [
        "Satellite frame: origin on the long axis at the -Z rail end; +Z = antenna end; X/Y faces as labelled. Third-angle projection.",
        f"Dispenser ICD: AODV-1 dispenser (in house) and commercial 3U dispensers per CDS rev 14.1. Rail ends are the only contact faces; panels and cells sit {E['w'] / 2 - X1 - P['t'] - C['t']:.1f} below the rail plane.",
        f"Orbit-average power {BASIS['power']['orbit_avg_gen_tumble_W']:.1f} W tumbling vs {BASIS['power']['orbit_avg_load_W']:.1f} W load; battery {BASIS['power']['batt_Wh']:.0f} Wh (design/design-basis.md).",
        "Mass is the current best estimate: structure from the CAD volumes, boards and harness estimated until the KiCad boards exist. Weigh at AON-900 T13 and update.",
    ], "NOTES", 12)
    S.save(DWG / "AON-001_general_arrangement.svg")


# ================================================================== AON-002 section and item list
ITEMS = [  # balloon, part, description, qty
    (1, "AON-101", "Rail, -Z switch notch", 2), (2, "AON-102", "Rail, +Z spring bore", 2), (3, "AON-103", "-Z frame", 1), (4, "AON-104", "Mid frame", 1),
    (5, "AON-105", "+Z frame", 1), (6, "AON-106", "Switch bracket", 2), (7, "AON-107-xx", "Stack spacers (6 sets of 4)", 24), (8, "AON-107-R", "Stack rod M3 Ti", 4),
    (9, "E01", "EPS board", 1), (10, "E02", "Battery board + 4 x BP-02", 1), (11, "E03", "OBC + ADCS board", 1), (12, "E04", "COM UHF board", 1),
    (13, "E05", "Antenna deployer board + BP-09 elements", 1), (14, "E06", "Solar panel (E06A x1, E06B x3)", 4), (15, "E07", "-Z end board + Z coil", 1),
    (16, "BP-03", "Deployment switch D2F", 2), (17, "BP-04", "Separation spring plunger", 2), (18, "H1", "Screw M2.5 x 14 csk (rail-frame)", 24),
    (19, "H2", "Screw M2 x 5 + washer (panels)", 16), (20, "H3", "Thin nut M3 (E07)", 4), (21, "H7", "Hex standoff M3 x 5 (E05)", 4), (22, "H9", "Silicone pad (panel mid)", 4),
    (23, "BP-05", "Stack connector ESQ-126", 4), (24, "BP-08", "U.FL coax E04-E05", 1),
]


def section():
    S = sheet("AON-002", "ASSEMBLY SECTION A-A (Y = +36.5) AND ITEM LIST", scale="1:1 · 5:1", material="see item list", finish="-",
              mass=f"{M_TOT:.0f} g CBE")
    s1 = SC(1)
    oy = 1870
    v = S.view(560, oy, s1, "SECTION A-A ON Y = +36.5 THROUGH THE STACK RODS (1:1) · looking toward +Y", (200, oy - L * s1 - 120))
    # rails beyond (visible, not cut)
    for x0 in (-H, RI):
        v.rect(x0, 0, RAIL, L)
    # +Y bars of the frames beyond
    for i in range(3):
        v.rect(-RI, FR["z"][i], 2 * RI, T, "thin")
    # frames cut: block + X bar, with stack hole
    for i in range(3):
        z0, z1 = FR["z"][i], FR["z"][i] + T
        r = 1.25 if i == 0 else 1.7
        for s in (1, -1):
            a, b = sorted((s * B0, s * X1))
            hl, hr = sorted((s * (HP - r), s * (HP + r)))
            v.hatch([(a, z0), (hl, z0), (hl, z1), (a, z1)], "hA"); v.hatch([(hr, z0), (b, z0), (b, z1), (hr, z1)], "hA")
    # panels cut (+X and -X)
    for s in (1, -1):
        a = X1 if s > 0 else -X1 - P["t"]
        v.hatch([(a, P["z0"]), (a + P["t"], P["z0"]), (a + P["t"], P["z1"]), (a, P["z1"])], "hC")
        c0 = a + P["t"] if s > 0 else a - C["t"]
        v.rect(c0, D.CELL_Z0, C["t"], 7 * C["w"] + 6 * D.GAP_CELL, "thin", CELLF)
    # boards cut
    boards = [(bid, z) for bid, _, z, _ in D.STACK] + [("E05", FR["z"][2] + T + 5.0), ("E07", FR["z"][0] - 1.6)]
    for bid, z in boards:
        for a, b in ((-40.5, -HP - 1.6), (-HP + 1.6, HP - 1.6), (HP + 1.6, 40.5)):
            v.hatch([(a, z), (b, z), (b, z + 1.6), (a, z + 1.6)], "hS")
    # component envelopes (phantom)
    for bid, name, z, hh in D.STACK:
        if bid == "E02":
            for zz in (z + 1.6 + 9.6, z + 1.6 + 29.2):
                v.rect(-32.5, zz - 9.2, 65, 18.4, "phan")
        else:
            v.rect(-32, z + 1.6, 64, hh - 2, "phan")
    # rods (not sectioned) and spacers (sectioned)
    for s in (1, -1):
        v.rect(s * HP - 1.5, D.ROD["z0"], 3.0, D.ROD["z1"] - D.ROD["z0"], "vis", "#eceff1")
    solids = sorted([(FR["z"][i], FR["z"][i] + T) for i in range(3)] + [(z, z + D.BRD["t"]) for _, _, z, _ in D.STACK])
    for a, b in zip(solids, solids[1:]):
        for s in (1, -1):
            for xo in (-2.75, 1.6):
                v.hatch([(s * HP + xo, a[1]), (s * HP + xo + 1.15, a[1]), (s * HP + xo + 1.15, b[0]), (s * HP + xo, b[0])], "hB")
    for s in (1, -1):    # standoffs H7 and nuts H3
        v.hatch([(s * HP - 2.75, FR["z"][2] + T), (s * HP + 2.75, FR["z"][2] + T), (s * HP + 2.75, FR["z"][2] + T + 5), (s * HP - 2.75, FR["z"][2] + T + 5)], "hB")
        v.rect(s * HP - 2.75, FR["z"][0] - 1.6 - 1.8, 5.5, 1.8, fill="#90a4ae")
    # antenna tape stowed
    v.rect(-34, FR["z"][2] + T + 6.6 + 0.4, 68, 0.5, fill="#ffb300")
    # dims: board bottoms
    for k, (bid, z) in enumerate(sorted(boards, key=lambda q: q[1])):
        v.dim((-H, 0), (-40.5, z), 70 + 0 * k, mmi(z, 1), "v") if False else None
    zs = sorted([z for _, z in boards])
    for k, z in enumerate(zs):
        v.dim((H, 0), (H, z), -40 - 34 * k, mmi(z, 1), "v")
    v.dim((-H, 0), (-H, L), 60, mmi(L, 1), "v")
    # balloons
    tags = [(1, (RI + 4, 250), (80, 260)), (3, (-40, FR["z"][0] + 5), (-80, 20)), (4, (-40, D.Z_MID), (-80, D.Z_MID)), (5, (-40, FR["z"][2] + 5), (-80, 318)),
            (8, (-HP, 250), (-80, 250)), (7, (-HP - 2.2, 60), (-80, 60)), (10, (0, 33), (-80, 100)), (9, (0, 81), (-80, 140)), (11, (0, 109), (-80, 185)),
            (12, (0, 187), (-80, 215)), (13, (0, FR["z"][2] + T + 5.8), (-80, 352)), (14, (X1 + 0.8, 290), (80, 300)), (15, (0, FR["z"][0] - 0.8), (-80, -12)),
            (21, (HP, FR["z"][2] + T + 2), (80, 350)), (20, (HP, FR["z"][0] - 3), (80, -12)), (2, (-RI - 4, 300), (-80, 290)), (22, (X1 + 0.8, D.Z_MID + 3), (80, 200))]
    for n, at, to in tags:
        v.tag(to[0], to[1], n, at)
    # detail B: rail-frame joint, plan section at the -Z frame screw (5:1)
    s5 = SC(5)
    vb = S.view(521, 1721, s5, "DETAIL B: RAIL TO FRAME JOINT, PLAN SECTION AT Z = 9.25 (5:1)", (1050, 560))
    rr(vb, RI, RI, RAIL, RAIL, 1.0)
    vb.hatch([(RI, RI), (D.RAIL_SCREW["bar_mid"] - CL / 2, RI), (D.RAIL_SCREW["bar_mid"] - CL / 2, H - 1.0), (D.RAIL_SCREW["bar_mid"] - CSK_D / 2, H), (RI + 1, H), (RI, H - 1)], "hA")
    vb.hatch([(D.RAIL_SCREW["bar_mid"] + CL / 2, RI), (H, RI), (H, H - 1), (H - 1, H), (D.RAIL_SCREW["bar_mid"] + CSK_D / 2, H), (D.RAIL_SCREW["bar_mid"] + CL / 2, H - 1.0)], "hA")
    vb.hatch([(X0, 28), (X1, 28), (X1, RI), (X0, RI)], "hB")
    vb.hatch([(B0 + 3, B0 + 3), (X0, B0 + 3), (X0, X0 - FR["relief"]), (X0 - FR["relief"], X0 - FR["relief"]), (X0 - FR["relief"], X0), (B0 + 3, X0)], "hB")
    bm = D.RAIL_SCREW["bar_mid"]
    vb.rect(bm - 1.25, RI - 8.0 + 0.6, 2.5, 8.5 + 8.0 - 0.6 - 1.0, "vis", "#eceff1")
    vb.poly([(bm - CSK_D / 2, H - 0.05), (bm + CSK_D / 2, H - 0.05), (bm + 1.25, H - 0.05 - (CSK_D - 2.5) / 2), (bm - 1.25, H - 0.05 - (CSK_D - 2.5) / 2)], fill="#eceff1")
    vb.rect(X1, 28, P["t"], RI - 28 - 0.5, "vis", FR4F)
    vb.dim((RI, H), (H, H), 40, mmi(RAIL, 2), "h")
    vb.dim((X0, 28), (X1, 28), -40, mmi(X1 - X0, 1), "h")
    vb.leader((bm, H - 0.5), (H + 4, H + 4), ["H1 M2.5 x 14 ISO 14581 A4-70", "0.45 N·m [4.0 lbf·in], head 0-0.05 below the face", "8.5 rail + 5.5 thread engagement"], 12)
    vb.leader((X1 + 0.8, 34), (H + 4, 33), ["E06 panel on the bar outer face"], 12)
    vb.note(28, 26, ["X bar of the frame (hatched B), rail (hatched A); the bar end seats on the rail's inner face"], 12)
    # item list
    S.table(2250, 200, [("ITEM", 60), ("PART", 150), ("DESCRIPTION", 520), ("QTY", 60)], [(n, p, d, q) for n, p, d, q in ITEMS], "ITEM LIST", 13, 26)
    tq = [(h[0], h[1][:58], h[5]) for h in HARDWARE]
    S.table(2250, 200 + 26 * (len(ITEMS) + 1) + 60, [("HW", 50), ("FASTENER", 560), ("TORQUE", 180)], tq, "TORQUES (dry, 316 into 6061; stake with 2216, no thread locker)", 12, 24)
    gaps = [(f"{a[1]:.2f}-{b[0]:.2f}", f"{b[0] - a[1]:.2f}") for a, b in zip(solids, solids[1:])]
    S.table(1100, 1500, [("BAY / GAP Z", 220), ("SPACER L", 140)], gaps, "SPACER STACK (AON-107)", 12, 24)
    S.notes(1100, 1720, 1050, [
        "Section plane on Y = +36.5 passes through the +Y pair of stack rods; rods, screws and standoffs are not sectioned.",
        "Boards: E02 battery, E01 EPS, E03 OBC in the lower bay; E04 COM in the upper bay with the payload bay above (Z 215-318).",
        "Bonding: rails, frames, spacers and the board ground rings form the chassis ground; one point to power ground on E01.",
    ], "NOTES", 12)
    S.save(DWG / "AON-002_assembly_section.svg")


# ================================================================== AON-003 illustrated assembly steps
STEPS = [
    (1, "-Z frame, switch brackets, switches", "Fit AON-106 brackets to the -Z frame W taps with H4 (0.20 N·m). Hang SW1/SW2 (BP-03) on the brackets with H5 (0.10 N·m). Check the lever travel by hand.",
     "levers free; switch clicks at 0.5 mm"),
    (2, "Rails to the -Z frame", "Stand the four rails in a squaring fixture (100.00 gauge block box). Seat the -Z frame bar ends on the rails, fit H1 at A1/B1 (0.45 N·m). Rails AON-101 at +X+Y and -X-Y (notch at -Z).",
     "envelope 100.0 ±0.1 at -Z; levers in the notches, 1.5 proud"),
    (3, "Rods, end board, lower stack", "Thread the 4 Ti rods through the -Z frame; E07 + thin nuts H3 under it. Stack spacers -01 / E02 / -02 / E01 / -03 / E03; measure the gap to the mid frame, face spacer -04 to fit.",
     "stack connectors fully mated; gap -04 recorded"),
    (4, "Mid frame", "Lower the mid frame between the rails over the rods; H1 at A2/B2 (0.45 N·m).", "rails square: diagonals equal within 0.1"),
    (5, "Upper stack: COM", "Spacer -05, E04, coax BP-08 routed up; measure and face spacer -06.", "coax bend radius ≥ 10 mm"),
    (6, "+Z frame, antenna board, springs", "Fit the +Z frame (H1 at A3/B3), standoffs H7 on the rods (0.6 N·m: this preloads the stack), E05 with H8. Screw the spring plungers BP-04 into the AON-102 rails.",
     "spring noses 2.0 proud; rods do not turn"),
    (7, "Solar panels", "Pads H9 on the mid-frame bars. Connect each panel harness (AON-E02), then fit the panels with H2 (0.20 N·m). E06A (RBF port) on +X.",
     "bond < 10 mΩ panel to rail; RBF fitted"),
]


def steps_sheet():
    S = sheet("AON-003", "ILLUSTRATED ASSEMBLY SEQUENCE", scale="NTS", material="-", finish="-", mass="-")
    W, Hh = 760, 780
    for k, (n, title, text, check) in enumerate(STEPS):
        col, row = k % 4, k // 4
        x, y = 90 + col * (W + 50), 110 + row * (Hh + 300)
        img(S, IMG / f"step{n:02d}.png", x, y + 30, W, Hh - 40)
        S.add(f'<rect x="{x}" y="{y}" width="{W}" height="{Hh + 230}" fill="none" stroke="#90a4ae"/>')
        S.text(x + 14, y + 26, f"STEP {n}: {title.upper()}", 20, bold=True)
        S.notes(x + 6, y + Hh - 4, W - 12, [text, "CHECK: " + check], "", 13)
    S.text(90 + 3 * (W + 50), 110 + Hh + 360, "Highlighted (orange tint): the parts added in that step.", 15)
    S.text(90 + 3 * (W + 50), 110 + Hh + 390, "Work in an ISO 8 clean area, ESD controlled; gloves; torque driver calibrated.", 15)
    S.text(90 + 3 * (W + 50), 110 + Hh + 420, "The same 7 steps play in the Anatomy 3D viewer (assembly.json).", 15)
    S.save(DWG / "AON-003_assembly_steps.svg")


def all_asm():
    ga(); section(); steps_sheet()
