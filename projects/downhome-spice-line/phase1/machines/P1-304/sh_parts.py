"""P1-304-100 base weldment, -200 body weldment, -201 body parts + flat patterns, -300 lid weldment + gaskets, -400 screen deck."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
from mechsheet import dxf_profile

SS = "#f4f6f8"


def P(r, a):
    return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


def circ(r, n=144, cx=0.0, cy=0.0):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rect_pts(w, h, cx=0.0, cy=0.0):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


L_UP = math.pi * (2 * R_I + T14)                 # upstand / shell blank length on the mean diameter
L_SK = math.pi * (SKIRT["od"] - SKIRT["t"])
L_DK = math.pi * (DECK["od"] - DECK["t"])
WELD_TXT = "GTAW, ER316LSi (308LSi on 304-to-304), argon"


def strip(v, L, H, label, slots=()):
    """flat strip (rolled ring blank) drawn at view scale, origin lower-left."""
    v.rect(0, 0, L, H, fill="#fff")
    v.dim((0, 0), (L, 0), -40, f"{mmi(L, 1)} (on mean Ø)", "h")
    v.dim((L, 0), (L, H), -40, None, "v")
    v.note(L / 2, H / 2, label, 13, "middle")


# ================================================================== 100 base weldment
def base():
    S = sheet("P1-304-100", "BASE WELDMENT (FIXED, ON THE DRUM RIM)", scale="1:4 · 1:2 · 1:1", material="seat 304 6 mm; upstand + skirt 316L", finish=FIN_PC + " (skirt, upstand ID)",
              mass=kg("P1-304-101", "P1-304-102", "P1-304-103", "P1-304-104"))
    s = SC(4)
    v = S.view(700, 820, s, "PLAN (1:4)", (150, 330))
    v.circle(0, 0, SEAT["od"] / 2, fill=SS); v.circle(0, 0, SEAT["id"] / 2, fill="#fff")
    v.circle(0, 0, R_O); v.circle(0, 0, R_I, "hid"); v.circle(0, 0, SKIRT["od"] / 2, "hid")
    for a in A_ISO:
        x, y = P(R_ISO, a); v.circle(x, y, 4.5); v.cmark(x, y, 8)
    xb, yb = P(BOND["r"], BOND["a_seat"]); v.circle(xb, yb, 4.5); v.cmark(xb, yb, 6)
    for a in (30.0, 150.0, 270.0):
        c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = [(TAB["r"], -TAB["w"] / 2), (TAB["r"] + TAB["t"], -TAB["w"] / 2), (TAB["r"] + TAB["t"], TAB["w"] / 2), (TAB["r"], TAB["w"] / 2)]
        v.poly([(px * c - py * sn, px * sn + py * c) for px, py in pts], "hid")
    v.circle(0, 0, R_ISO, "cen"); v.cmark(0, 0, SEAT["od"] / 2 + 15)
    v.dia(0, 0, SEAT["od"] / 2, 135, (-420, 330), f"Ø{mmi(SEAT['od'])} ±1")
    v.dia(0, 0, SEAT["id"] / 2, 200, (-420, -300), f"Ø{mmi(SEAT['id'])} ±0.5")
    v.leader(P(R_ISO, 90), (140, 420), [f"3 x Ø9 [.354] THRU on R{mmi(R_ISO)}", "at 90°, 210°, 330° (isolators)"])
    v.leader((xb, yb), (250, 380), [f"Ø9 THRU at 60° on R{mmi(BOND['r'])} (bond strap H5)"])
    v.leader(P(TAB["r"] + 3, 270), (200, -400), ["3 TABS 104 under the ring at 30°, 150°, 270°", f"inside face on R{mmi(TAB['r'])} (drum rim R292 + 1.5)"])
    v.text(0, -SEAT["od"] / 2 - 70, "0° = +x (vibrator side), angles CCW seen from above", 13)
    # half section 1:2
    s2 = SC(2)
    vs = S.view(1800, 900, s2, "SECTION ON Y = 0 (1:2)", (1350, 560))
    for sg in (-1, 1):
        x0 = sg * SEAT["id"] / 2
        vs.hatch([(x0, 0), (sg * SEAT["od"] / 2, 0), (sg * SEAT["od"] / 2, SEAT["t"]), (x0, SEAT["t"])], "hA")
        xu = R_I if sg > 0 else -R_O
        vs.hatch([(xu, UPST["z0"]), (xu + T14, UPST["z0"]), (xu + T14, UPST["z0"] + UPST["h"]), (xu, UPST["z0"] + UPST["h"])], "hC")
        xs = SKIRT["od"] / 2 - SKIRT["t"] if sg > 0 else -SKIRT["od"] / 2
        vs.hatch([(xs, -SKIRT["h"]), (xs + SKIRT["t"], -SKIRT["h"]), (xs + SKIRT["t"], 0), (xs, 0)], "hC")
    vs.rect(TAB["r"] * math.cos(math.radians(30)) - 2, -TAB["h"], 4, TAB["h"], "hid")
    vs.centre(0, -SKIRT["h"] - 20, 0, 60)
    vs.dim((-SKIRT["od"] / 2, -SKIRT["h"]), (SKIRT["od"] / 2, -SKIRT["h"]), -40, f"SKIRT Ø{mmi(SKIRT['od'])} OD", "h")
    vs.dim((-R_O, UPST["z0"] + UPST["h"]), (R_O, UPST["z0"] + UPST["h"]), 40, f"UPSTAND Ø{mmi(2 * R_I)} ID", "h")
    vs.dim((SEAT["od"] / 2, 0), (SEAT["od"] / 2, SEAT["t"]), -30, None, "v")
    vs.dim((-SEAT["od"] / 2, UPST["z0"]), (-SEAT["od"] / 2, UPST["z0"] + UPST["h"]), 30, None, "v") if False else None
    vs.dim((-R_O, 0), (-R_O, UPST["z0"] + UPST["h"]), 60, None, "v")
    vs.dim((SKIRT["od"] / 2, -SKIRT["h"]), (SKIRT["od"] / 2, 0), -70, None, "v")
    vs.datum((150, 0), "A", (0, -1))
    vs.fcf(-SEAT["od"] / 2 + 20, -95, ["⏥", "1.0"])
    vs.note(-SEAT["od"] / 2 + 20, -125, "SEAT UNDERSIDE (sits on the rim): flat 1.0 after welding", 12)
    # detail D welds 1:1
    s1 = SC(1)
    vd = S.view(2900 - 200 * s1, 900, s1, "DETAIL D (1:1): JOINTS AT THE INNER EDGE", (2650, 560))
    xi = SEAT["id"] / 2
    vd.hatch([(xi, 0), (xi + 80, 0), (xi + 80, SEAT["t"]), (xi, SEAT["t"])], "hA")
    vd.hatch([(R_I, UPST["z0"]), (R_O, UPST["z0"]), (R_O, 36), (R_I, 36)], "hC")
    vd.hatch([(SKIRT["od"] / 2 - SKIRT["t"], -40), (SKIRT["od"] / 2, -40), (SKIRT["od"] / 2, 0), (SKIRT["od"] / 2 - SKIRT["t"], 0)], "hC")
    vd.dim((xi, -5), (SKIRT["od"] / 2, -5), 0, None, "h") if False else None
    vd.dim((SKIRT["od"] / 2, SEAT["t"]), (xi, SEAT["t"]), 30, None, "h")
    vd.dim((xi, SEAT["t"]), (R_I, SEAT["t"]), 60, None, "h")
    vd.weld((R_O, UPST["z0"]), (R_O + 50, 40), "fillet", "2", other="fillet", allround=True, tail="W1")
    vd.weld((SKIRT["od"] / 2, 0), (SKIRT["od"] / 2 + 70, -30), "fillet", "2", other="fillet", allround=True, tail="W2")
    vd.note(xi + 5, -60, ["W1/W2 product side: continuous, ground", "flush R1; outside: fillet 2"], 12)
    # parts table, flat patterns
    S.table(150, 1480, [("PART", 120), ("DESCRIPTION", 360), ("QTY", 40), ("STOCK / BLANK", 430), ("FILE", 340)], [
        ("P1-304-101", "Seat ring", 1, f"304 plate 6 mm, Ø{SEAT['od']:.0f} / Ø{SEAT['id']:.0f}, 4 holes", "dxf/P1-304-101_seat_ring_mm/_in.dxf"),
        ("P1-304-102", "Upstand ring (roll, butt weld)", 1, f"316L 14 ga strip {L_UP:.1f} x {UPST['h']:.0f}", "dxf/P1-304-102_upstand_blank"),
        ("P1-304-103", "Skirt (roll, butt weld)", 1, f"316L 16 ga (1.5) strip {L_SK:.1f} x {SKIRT['h']:.0f}", "dxf/P1-304-103_skirt_blank"),
        ("P1-304-104", "Centring tab", 3, f"304 3 mm, {TAB['w']:.0f} x {TAB['h'] + SEAT['t']:.0f}", "dxf/P1-304-104_tab"),
    ], "PARTS", 13, 22)
    S.table(150, 1640, [("WELD", 60), ("JOINT", 420), ("PROCESS", 420), ("NOTES", 500)], [
        ("W1", "Upstand to seat top, both sides", WELD_TXT, "fillet 2 out, seal + grind in (product side)"),
        ("W2", "Skirt to seat underside, both sides", WELD_TXT, "fillet 2 out, seal + grind in; skirt round ±1"),
        ("W3", "Ring butt seams (102, 103)", "GTAW autogenous, full penetration, backed", "ground flush both sides, no crevice"),
        ("W4", "Tabs to seat underside", "GTAW 308LSi", "fillet 3 both sides x 40; inner faces on R293.5 ±0.5"),
    ], "WELD SCHEDULE", 13, 22)
    S.notes(2000, 1480, 1000, [
        "Weld the rings round, then fit to the seat on a flat table; tack 8 places each, weld in short alternating runs to keep the seat flat 1.0.",
        "Tabs last, on a drum rim gauge (Ø584): the base must drop on and lift off a drum freely with ≤ 2 mm play.",
        "Passivate after welding. Product-contact surfaces: skirt ID, upstand ID, seat inner edge.",
    ], "FABRICATION", 13)
    dxf_profile(str(DXF / "P1-304-101_seat_ring"), [circ(SEAT["od"] / 2), circ(SEAT["id"] / 2)],
                holes=[(*P(R_ISO, a), 4.5) for a in A_ISO] + [(*P(BOND["r"], BOND["a_seat"]), 4.5)], text="P1-304-101 SEAT RING 6mm 304")
    dxf_profile(str(DXF / "P1-304-102_upstand_blank"), rect_pts(L_UP, UPST["h"], L_UP / 2, UPST["h"] / 2), text="P1-304-102 UPSTAND 14ga 316L roll ID480")
    dxf_profile(str(DXF / "P1-304-103_skirt_blank"), rect_pts(L_SK, SKIRT["h"], L_SK / 2, SKIRT["h"] / 2), text="P1-304-103 SKIRT 16ga 316L roll OD470")
    dxf_profile(str(DXF / "P1-304-104_tab"), rect_pts(TAB["w"], TAB["h"] + SEAT["t"]), text="P1-304-104 TAB x3 3mm 304")
    S.save(DWG / "P1-304-100_base_weldment.svg")


# ================================================================== 200 body weldment
def body():
    S = sheet("P1-304-200", "BODY WELDMENT (VIBRATING)", scale="1:2 · 1:4", material="shell, flange, bars, ledge 316L; brackets 304", finish=FIN_PC + " (inside)",
              mass=kg("P1-304-201", "P1-304-202", "P1-304-203", "P1-304-204", "P1-304-205", "P1-304-206", "P1-304-207"))
    s = SC(2)
    v = S.view(950, 860, s, "ELEVATION, SECTION ON Y = 0 (1:2)", (150, 380))
    for sg in (-1, 1):
        xs = R_I if sg > 0 else -R_O
        v.hatch([(xs, Z_B0), (xs + T14, Z_B0), (xs + T14, Z_B1), (xs, Z_B1)], "hC")
        xf = R_I if sg > 0 else -TOPFL["od"] / 2
        v.hatch([(xf, Z_B1), (xf + TOPFL["od"] / 2 - R_I, Z_B1), (xf + TOPFL["od"] / 2 - R_I, Z_TOP), (xf, Z_TOP)], "hA")
        xl = LEDGE["id"] / 2 if sg > 0 else -R_I
        v.hatch([(xl, LEDGE["z"]), (xl + LEDGE["w"], LEDGE["z"]), (xl + LEDGE["w"], LEDGE["z"] + LEDGE["t"]), (xl, LEDGE["z"] + LEDGE["t"])], "hA")
    Lb = 2 * math.sqrt(R_I ** 2 - (110 + 12.5) ** 2)
    v.rect(-Lb / 2, BAR["z"], Lb, BAR["t"], "vis", "#eceff1")
    # isolator bracket at 210 (left, front) projected, vibrator bracket right
    v.rect(VBR["x"], VBR["z0"], VBR["t"], VBR["z1"] - VBR["z0"], fill="url(#hA)")
    v.poly([(R_O, VBR["z0"]), (VBR["x"], VBR["z0"]), (VBR["x"], VBR["z1"]), (TOPFL["od"] / 2 + 1, VBR["z1"] - 60), (TOPFL["od"] / 2 + 1, Z_TOP), (R_O, Z_B1)], fill=SS)
    xb = R_ISO * math.cos(math.radians(210))
    v.rect(xb - 25, Z_ISO_TOP, -R_O - (xb - 25), BRK["t"], fill=SS); v.rect(-R_O - BRK["t"], Z_ISO_TOP, BRK["t"], 40, fill=SS)
    v.centre(0, Z_B0 - 30, 0, Z_TOP + 40)
    v.dim((-TOPFL["od"] / 2, Z_TOP), (TOPFL["od"] / 2, Z_TOP), 50, f"Ø{mmi(TOPFL['od'])} ±0.5", "h")
    v.dim((-R_I, Z_B0), (R_I, Z_B0), -40, f"Ø{mmi(2 * R_I)} ID ±1", "h")
    v.dim((-Lb / 2, BAR["z"]), (Lb / 2, BAR["z"]), -90, f"BARS {mmi(Lb, 1)} (fit to shell)", "h")
    v.dim((LEDGE["id"] / 2, LEDGE["z"] + LEDGE["t"]), (-LEDGE["id"] / 2, LEDGE["z"] + LEDGE["t"]), 0, None, "h") if False else None
    v.dim((R_O, Z_B0), (R_O, Z_TOP), -310, f"{mmi(Z_TOP - Z_B0)}", "v")
    v.dim((R_O, Z_B0), (R_O, LEDGE["z"] + LEDGE["t"]), -250, f"{mmi(LEDGE['z'] + LEDGE['t'] - Z_B0)} ±0.5", "v")
    v.dim((R_O, Z_B0), (R_O, BAR["z"] + BAR["t"]), -190, None, "v")
    v.dim((VBR["x"] + VBR["t"], VBR["z0"]), (VBR["x"] + VBR["t"], VBR["z1"]), -40, None, "v")
    v.dim((R_O, VBR["z0"] - 10), (VBR["x"], VBR["z0"] - 10), -20, None, "h")
    v.dim((-R_O, Z_B0), (-R_O, Z_ISO_TOP), 60, f"{mmi(Z_ISO_TOP - Z_B0)}", "v")
    v.datum((-100, Z_TOP), "A", (0, 1))
    v.fcf(-TOPFL["od"] / 2 - 150, Z_TOP + 20, ["⏥", "0.5"])
    v.note(-TOPFL["od"] / 2 - 150, Z_TOP - 5, ["FLANGE TOP = DATUM A,", "flat 0.5 after welding"], 12)
    v.note(-R_O - 60, Z_ISO_TOP - 30, ["bracket at 210°", "rotated into view"], 11, "end")
    v.leader((LEDGE["id"] / 2 + 5, LEDGE["z"] + LEDGE["t"]), (120, LEDGE["z"] + 60), ["LEDGE TOP ∥ 0.5 to A"], anchor="end")
    v.weld((R_I, LEDGE["z"] + 3), (R_I - 120, LEDGE["z"] - 40), "fillet", "2", other="fillet", allround=True, tail="W3")
    v.weld((R_O, Z_B1), (R_O + 60, Z_B1 + 90), "fillet", "3", other="fillet", allround=True, tail="W2")
    v.weld((Lb / 2 - 30, BAR["z"]), (Lb / 2 - 150, BAR["z"] - 50), "fillet", "2", allround=True, tail="W4")
    v.weld((VBR["x"], VBR["z0"] + 20), (VBR["x"] + 80, VBR["z0"] - 40), "fillet", "5", other="fillet", tail="W5 gussets to plate + shell")
    v.weld((-R_O - BRK["t"], Z_ISO_TOP + 30), (-R_O - 120, Z_ISO_TOP + 90), "fillet", "4", other="fillet", tail="W6 brackets")
    # plan 1:4
    s4 = SC(4)
    vp = S.view(2700, 720, s4, "PLAN (1:4)", (2150, 330))
    vp.circle(0, 0, TOPFL["od"] / 2, fill=SS); vp.circle(0, 0, R_I, fill="#fff"); vp.circle(0, 0, LEDGE["id"] / 2, "hid")
    for y in BAR["y"]:
        vp.rect(-Lb / 2, y - BAR["w"] / 2, Lb, BAR["w"], "hid")
    for a in A_ISO:
        c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = [(R_O, -BRK["w"] / 2), (R_ISO + 25, -BRK["w"] / 2), (R_ISO + 25, BRK["w"] / 2), (R_O, BRK["w"] / 2)]
        vp.poly([(px * c - py * sn, px * sn + py * c) for px, py in pts], fill=SS)
        x, y = P(R_ISO, a); vp.circle(x, y, 4.5)
    xb2, yb2 = P(R_ISO + 18, BOND["a_brk"]); vp.circle(xb2, yb2, 4.5)
    for k in range(LATCH["n"]):
        a = LATCH["a0"] + 90 * k; c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = [(R_O, -LPLATE["w"] / 2), (R_O + LPLATE["t"], -LPLATE["w"] / 2), (R_O + LPLATE["t"], LPLATE["w"] / 2), (R_O, LPLATE["w"] / 2)]
        vp.poly([(px * c - py * sn, px * sn + py * c) for px, py in pts], "hid")
    vp.rect(VBR["x"], -VBR["w"] / 2, VBR["t"], VBR["w"], fill=SS)
    for y in (-VBR["w"] / 2 + 14, VBR["w"] / 2 - 14):
        vp.rect(R_O, y - VBR["gus_t"] / 2, VBR["x"] - R_O, VBR["gus_t"], fill=SS)
    vp.cmark(0, 0, TOPFL["od"] / 2 + 15)
    vp.dim((-Lb / 2, BAR["y"][1] + 12.5), (-Lb / 2, BAR["y"][0] - 12.5), 40, None, "v") if False else None
    vp.dim((Lb / 2, BAR["y"][0]), (Lb / 2, BAR["y"][1]), -60, f"BARS {mmi(BAR['y'][1] - BAR['y'][0])} c/c", "v")
    vp.leader(P(R_ISO, 330), (420, -330), ["3 ISOLATOR BRACKETS 205 at 90°, 210°, 330°", f"Ø9 THRU on R{mmi(R_ISO)}; bond Ø9 at 90° (R333)"])
    vp.leader(P(R_O + 2, 45), (330, 380), ["4 LATCH PLATES 207 at 45° + 90k", f"top {mmi(LPLATE['z0'] + LPLATE['h'])} = flange underside"])
    vp.leader((VBR["x"] + VBR["t"], 60), (420, 200), ["VIBRATOR PLATE 206 + 2 GUSSETS", "4 x Ø11: see -201"])
    # parts + welds
    S.table(150, 1560, [("PART", 120), ("DESCRIPTION", 380), ("QTY", 40), ("STOCK / BLANK", 470), ("DRG / FILE", 300)], [
        ("P1-304-201", "Shell (roll, butt weld W1)", 1, f"316L 14 ga strip {L_UP:.1f} x {Z_B1 - Z_B0:.0f}", "-201, dxf"),
        ("P1-304-202", "Top flange ring", 1, f"316L 6 mm Ø{TOPFL['od']:.0f} / Ø{TOPFL['id']:.0f}", "-201, dxf"),
        ("P1-304-203", "Magnet bar", 2, f"316L flat 25 x 5 x {Lb:.0f} (ends radiused R{R_I:.0f})", "-201"),
        ("P1-304-204", "Screen ledge ring", 1, f"316L 6 mm Ø{2 * R_I:.0f} / Ø{LEDGE['id']:.0f}", "-201, dxf"),
        ("P1-304-205", "Isolator bracket (2 pieces welded)", 3, "304 flat 50 x 6: 106 + 40", "-201"),
        ("P1-304-206", "Vibrator plate + 2 gussets", 1, f"304 10 mm {VBR['w']:.0f} x {VBR['z1'] - VBR['z0']:.0f}; gussets 8 mm", "-201, dxf"),
        ("P1-304-207", "Latch plate", 4, f"304 3 mm {LPLATE['w']:.0f} x {LPLATE['h']:.0f}", "-201, dxf"),
    ], "PARTS", 13, 22)
    S.table(1500, 1560, [("WELD", 60), ("JOINT", 430), ("PROCESS", 330), ("NOTES", 520)], [
        ("W1", "Shell butt seam", "GTAW autogenous, backed, full pen.", "ground flush inside, no crevice"),
        ("W2", "Flange to shell, both sides", WELD_TXT, "inside: seal + grind R1; outside fillet 3"),
        ("W3", "Ledge to shell, top and underside", WELD_TXT, "top fillet 2 ground R1; underside seal (no crevice)"),
        ("W4", "Magnet bars to shell, all round", WELD_TXT, "ends saddle-fitted, seal all round, ground"),
        ("W5", "Gussets to shell, flange, plate", "GTAW 308LSi / 309L to 316L", "fillet 5 both sides; plate ⟂ A 0.5"),
        ("W6", "Isolator brackets to shell", "GTAW 309L (304 to 316L)", "fillet 4 both sides; leg undersides coplanar 0.5"),
        ("W7", "Latch plates to shell", "GTAW 309L", "fillet 3 both sides; top at flange underside"),
    ], "WELD SCHEDULE", 13, 22)
    S.notes(1500, 1820, 1050, [
        "Order: roll + seam the shell, weld the flange (A), then ledge and bars, then the outside brackets. Check round ±1 and A flat 0.5 after each step.",
        "Isolator bracket undersides coplanar 0.5 and ∥ A 0.5: shim on the fixture, the body must sit level on 3 isolators.",
        "Vibrator plate face ⟂ A 0.5 and on the 0° line ±1: the motor axis must be vertical.",
    ], "FABRICATION", 13)
    S.save(DWG / "P1-304-200_body_weldment.svg")


def body_parts():
    S = sheet("P1-304-201", "BODY PARTS AND FLAT PATTERNS", scale="1:4 · 1:2 · 1:1", material="see table", finish="see -200", mass="see -200")
    s4 = SC(4)
    v = S.view(150, 480, s4, f"P1-304-201 SHELL BLANK (1:4) · 316L 14 ga · roll to Ø{2 * R_I:.0f} ID", (150, 330))
    v.rect(0, 0, L_UP, Z_B1 - Z_B0, fill="#fff")
    v.dim((0, 0), (L_UP, 0), -40, f"{mmi(L_UP, 1)} = π x {2 * R_I + T14:.1f} (mean)", "h")
    v.dim((L_UP, 0), (L_UP, Z_B1 - Z_B0), -40, f"{mmi(Z_B1 - Z_B0)}", "v")
    v.note(L_UP / 2, (Z_B1 - Z_B0) / 2, "grain along the length; roll, check Ø480 ID ±1, butt weld W1", 13, "middle")
    s2 = SC(2)
    # flange ring
    vf = S.view(500, 1050, s4, "P1-304-202 TOP FLANGE (1:4) · 316L 6 mm", (150, 690))
    vf.circle(0, 0, TOPFL["od"] / 2, fill=SS); vf.circle(0, 0, TOPFL["id"] / 2, fill="#fff"); vf.cmark(0, 0, TOPFL["od"] / 2 + 10)
    vf.dia(0, 0, TOPFL["od"] / 2, 45, (250, 330), f"Ø{mmi(TOPFL['od'])} ±0.5")
    vf.dia(0, 0, TOPFL["id"] / 2, 225, (-250, -340), f"Ø{mmi(TOPFL['id'])} +0.5/0")
    dxf_profile(str(DXF / "P1-304-202_top_flange"), [circ(TOPFL["od"] / 2), circ(TOPFL["id"] / 2)], text="P1-304-202 TOP FLANGE 6mm 316L")
    # ledge ring
    vl = S.view(1250, 1050, s4, "P1-304-204 SCREEN LEDGE (1:4) · 316L 6 mm", (950, 690))
    vl.circle(0, 0, R_I, fill=SS); vl.circle(0, 0, LEDGE["id"] / 2, fill="#fff"); vl.cmark(0, 0, R_I + 10)
    vl.dia(0, 0, R_I, 45, (200, 330), f"Ø{mmi(2 * R_I)} -0.5/-1.0 (fit in shell)")
    vl.dia(0, 0, LEDGE["id"] / 2, 225, (-250, -340), f"Ø{mmi(LEDGE['id'])} ±0.5")
    dxf_profile(str(DXF / "P1-304-204_ledge"), [circ(R_I - 0.4), circ(LEDGE["id"] / 2)], text="P1-304-204 LEDGE 6mm 316L")
    # magnet bar 1:4
    Lb = 2 * math.sqrt(R_I ** 2 - (110 + 12.5) ** 2)
    vb = S.view(2150, 520, s2, "P1-304-203 MAGNET BAR x2 (1:2) · 316L flat 25 x 5", (1950, 330))
    vb.poly([(-Lb / 2, -12.5), (Lb / 2, -12.5)] + [(Lb / 2 + 2, y) for y in (-6, 0, 6)] + [(Lb / 2, 12.5), (-Lb / 2, 12.5)] + [(-Lb / 2 - 2, y) for y in (6, 0, -6)], fill="#fff")
    vb.dim((-Lb / 2, 12.5), (Lb / 2, 12.5), 30, f"{mmi(Lb, 1)} fit to shell (ends dressed to R{R_I:.0f})", "h")
    vb.dim((Lb / 2, -12.5), (Lb / 2, 12.5), -40, None, "v")
    vb.note(0, -45, "edges broken R1 (product contact); top face #4", 12, "middle")
    # isolator bracket 1:1
    s1 = SC(1)
    vi = S.view(2050, 1050, s1, "P1-304-205 ISOLATOR BRACKET x3 (1:1) · 304 flat 50 x 6", (1950, 760))
    vi.rect(0, 0, 106, BRK["t"], fill="url(#hA)"); vi.rect(0, BRK["t"], BRK["t"], 40 - BRK["t"], fill="url(#hA)")
    vi.rect(R_ISO - R_O + 6 - 4.5, 0, 9, BRK["t"], "vis", "#fff")
    vi.dim((0, 0), (106, 0), -30, None, "h"); vi.dim((0, 0), (R_ISO - R_O + 6, 0), -70, f"{mmi(R_ISO - R_O + 6, 1)} TO HOLE", "h")
    vi.dim((0, 0), (0, 40), 40, None, "v")
    vi.leader((R_ISO - R_O + 6, BRK["t"]), (R_ISO - R_O + 40, 50), ["Ø9 [.354] THRU", "(+ bond Ø9 at 18 further out on the 90° bracket)"])
    vi.note(0, -60, ["vertical leg welds to the shell (left), horizontal leg", "sits on the isolator; weld legs together fillet 4"], 12)
    # vibrator plate 1:2 and gusset
    vv = S.view(2600, 1820, s2, "P1-304-206 VIBRATOR PLATE (1:2) · 304 10 mm (view from +x)", (2350, 1330))
    H = VBR["z1"] - VBR["z0"]
    vv.rect(-VBR["w"] / 2, 0, VBR["w"], H, fill=SS)
    zc = Z_VIB - VBR["z0"]
    hp = [(sy * VB_HOLES["sy"] / 2, zc + sz * VB_HOLES["sz"] / 2) for sy in (-1, 1) for sz in (-1, 1)]
    for x, y in hp:
        vv.circle(x, y, VB_HOLES["d"] / 2); vv.cmark(x, y, 8)
    vv.dim((-VBR["w"] / 2, H), (VBR["w"] / 2, H), 30, None, "h"); vv.dim((VBR["w"] / 2, 0), (VBR["w"] / 2, H), -40, None, "v")
    vv.dim((-VB_HOLES["sy"] / 2, zc - VB_HOLES["sz"] / 2), (VB_HOLES["sy"] / 2, zc - VB_HOLES["sz"] / 2), -70, None, "h")
    vv.dim((-VBR["w"] / 2, zc - VB_HOLES["sz"] / 2), (-VBR["w"] / 2, zc + VB_HOLES["sz"] / 2), 50, None, "v")
    vv.dim((-VBR["w"] / 2, 0), (-VBR["w"] / 2, zc), 110, f"{mmi(zc)} (axis z {Z_VIB:.0f})", "v")
    vv.leader(hp[3], (110, H + 40), ["4 x Ø11 [.433] THRU for M10", "CONFIRM on the vibrator drawing"])
    dxf_profile(str(DXF / "P1-304-206_vibrator_plate"), rect_pts(VBR["w"], H, 0, H / 2), holes=[(x, y, VB_HOLES["d"] / 2) for x, y in hp], text="P1-304-206 VIB PLATE 10mm 304")
    gus = [(0, 0), (VBR["x"] - R_O, 0), (VBR["x"] - R_O, H), (TOPFL["od"] / 2 + 1 - R_O, H - 60), (TOPFL["od"] / 2 + 1 - R_O, Z_TOP - VBR["z0"]), (0, Z_B1 - VBR["z0"])]
    vg = S.view(2000, 1820, s2, "GUSSET x2 (1:2) · 304 8 mm", (1850, 1330))
    vg.poly(gus, fill=SS)
    vg.dim((0, 0), (VBR["x"] - R_O, 0), -30, None, "h"); vg.dim((VBR["x"] - R_O, 0), (VBR["x"] - R_O, H), -30, None, "v")
    vg.dim((0, 0), (0, Z_B1 - VBR["z0"]), 30, None, "v")
    vg.note(-10, -70, ["notch at the flange edge", "(flange OD R270)"], 12)
    dxf_profile(str(DXF / "P1-304-206_gusset"), gus, text="P1-304-206 GUSSET x2 8mm 304")
    # latch plate
    vlp = S.view(1500, 2000, s1, "P1-304-207 LATCH PLATE x4 (1:1) · 304 3 mm", (1350, 1700))
    vlp.rect(-LPLATE["w"] / 2, 0, LPLATE["w"], LPLATE["h"], fill=SS)
    for z in (LPLATE["h"] / 2 - 10, LPLATE["h"] / 2 + 10):
        vlp.circle(0, z, 2.75)
    vlp.dim((-20, LPLATE["h"]), (20, LPLATE["h"]), 30, None, "h"); vlp.dim((20, 0), (20, LPLATE["h"]), -30, None, "v")
    vlp.leader((0, LPLATE["h"] / 2 + 12.75), (40, LPLATE["h"] + 30), ["2 x Ø5.5 on 20 (confirm latch)"])
    dxf_profile(str(DXF / "P1-304-207_latch_plate"), rect_pts(LPLATE["w"], LPLATE["h"], 0, LPLATE["h"] / 2), holes=[(0, z, 2.75) for z in (20.0, 40.0)], text="P1-304-207 LATCH PLATE x4 3mm 304")
    dxf_profile(str(DXF / "P1-304-201_shell_blank"), rect_pts(L_UP, Z_B1 - Z_B0, L_UP / 2, (Z_B1 - Z_B0) / 2), text="P1-304-201 SHELL 14ga 316L roll ID480")
    S.table(150, 1870, [("CUT FILE (dxf/, _mm and _in)", 420), ("PART", 120), ("MATERIAL", 280), ("QTY", 60)], [
        ("P1-304-201_shell_blank", "201", "316L 14 ga", 1), ("P1-304-202_top_flange", "202", "316L 6 mm", 1), ("P1-304-204_ledge", "204", "316L 6 mm", 1),
        ("P1-304-206_vibrator_plate", "206", "304 10 mm", 1), ("P1-304-206_gusset", "206", "304 8 mm", 2), ("P1-304-207_latch_plate", "207", "304 3 mm", 4)],
        "CUT FILES", 13, 22)
    S.save(DWG / "P1-304-201_body_parts.svg")


# ================================================================== 300 lid weldment + gaskets
def lid():
    S = sheet("P1-304-300", "LID WELDMENT, GASKETS, PAD CAPS", scale="1:4 · 1:2 · 1:1", material="lid 316L 2 mm; ferrules 316L BPE; tabs 304", finish=FIN_PC + " (underside)",
              mass=kg("P1-304-301", "P1-304-302", "P1-304-303", "P1-304-304"))
    s4 = SC(4)
    v = S.view(700, 820, s4, "PLAN (1:4), FROM ABOVE", (150, 330))
    v.circle(0, 0, LID["od"] / 2, fill=SS); v.circle(0, 0, TC4["fl"] / 2); v.circle(0, 0, TC4["id"] / 2, fill="#fff")
    xd, yd = P(TC3["r"], TC3["a"]); v.circle(xd, yd, TC3["fl"] / 2); v.circle(xd, yd, TC3["id"] / 2, fill="#fff")
    for a in PAD["a"]:
        x, y = P(PAD["r"], a); v.circle(x, y, PAD["d"] / 2, "hid")
    for k in range(LATCH["n"]):
        a = LATCH["a0"] + 90 * k; c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = [(LID["od"] / 2, -KTAB["w"] / 2), (LID["od"] / 2 + KTAB["t"], -KTAB["w"] / 2), (LID["od"] / 2 + KTAB["t"], KTAB["w"] / 2), (LID["od"] / 2, KTAB["w"] / 2)]
        v.poly([(px * c - py * sn, px * sn + py * c) for px, py in pts], fill=SS)
    v.cmark(0, 0, LID["od"] / 2 + 15); v.circle(0, 0, PAD["r"], "cen")
    v.dia(0, 0, LID["od"] / 2, 120, (-400, 330), f"Ø{mmi(LID['od'])} ±0.5")
    v.leader((xd, yd), (-120, -430), [f"3 in BPE FERRULE on R{mmi(TC3['r'])} at {TC3['a']:.0f}°", f"hole Ø{mmi(TC3['id'], 1)} (= ferrule ID)"], anchor="start")
    v.leader((0, TC4["id"] / 2), (150, 380), ["4 in BPE FERRULE on axis", f"hole Ø{mmi(TC4['id'], 1)} (= ferrule ID)"])
    v.leader(P(PAD["r"], 30), (380, 250), [f"3 PADS 303 under, on R{mmi(PAD['r'])}", "at 30°, 150°, 270°"])
    v.leader(P(LID["od"] / 2 + 3, 315), (400, -330), ["4 KEEPER TABS 304 at 45° + 90k", "welded to the lid edge, hanging down"])
    # section 1:2
    s2 = SC(2)
    vs = S.view(1950, 760, s2, "SECTION ON Y = 0 (1:2)", (1400, 330))
    z0 = 0.0
    vs.hatch([(-LID["od"] / 2, 0), (-TC4["id"] / 2, 0), (-TC4["id"] / 2, LID["t"]), (-LID["od"] / 2, LID["t"])], "hA")
    vs.hatch([(TC4["id"] / 2, 0), (LID["od"] / 2, 0), (LID["od"] / 2, LID["t"]), (TC4["id"] / 2, LID["t"])], "hA")
    for sg in (-1, 1):
        xi = sg * TC4["id"] / 2; xo = sg * TC4["od"] / 2; xf = sg * TC4["fl"] / 2
        vs.hatch([(xi, LID["t"]), (xo, LID["t"]), (xo, LID["t"] + TC4["L"] - 8), (xf, LID["t"] + TC4["L"] - 8), (xf, LID["t"] + TC4["L"]), (xi, LID["t"] + TC4["L"])], "hC")
    xpad = PAD["r"] * math.cos(math.radians(150))
    vs.rect(xpad - PAD["d"] / 2, -PAD["steel"], PAD["d"], PAD["steel"], "vis", SS)
    vs.rect(xpad - PAD["d"] / 2 - 2, -PAD["steel"] - 3, PAD["d"] + 4, 13, "vis", "#90a4ae")
    vs.rect(LID["od"] / 2, LID["t"] - KTAB["h"], KTAB["t"], KTAB["h"], fill="url(#hB)")
    vs.centre(0, -50, 0, 60)
    vs.dim((-TC4["fl"] / 2, LID["t"] + TC4["L"]), (TC4["fl"] / 2, LID["t"] + TC4["L"]), 30, f"4 in TC Ø{mmi(TC4['fl'])} (BPE)", "h")
    vs.dim((TC4["fl"] / 2 + 10, 0), (TC4["fl"] / 2 + 10, LID["t"] + TC4["L"]), -40, None, "v")
    vs.dim((xpad + PAD["d"] / 2 + 2, 0), (xpad + PAD["d"] / 2 + 2, -PAD["steel"] - 3), -40, f"{mmi(PAD['h'])} FREE", "v")
    vs.dim((LID["od"] / 2 + KTAB["t"], LID["t"]), (LID["od"] / 2 + KTAB["t"], LID["t"] - KTAB["h"]), -40, None, "v")
    vs.weld((TC4["od"] / 2, LID["t"]), (TC4["od"] / 2 + 80, 70), "fillet", "1.5", other="sq", tail="W1 ferrules: seal under, flush")
    vs.weld((xpad, 0), (xpad - 30, -90), "fillet", "2", allround=True, tail="W2 pads")
    vs.weld((LID["od"] / 2, LID["t"]), (LID["od"] / 2 - 60, 80), "fillet", "2", tail="W3 tabs")
    # pad + cap 1:1
    s1 = SC(1)
    vp = S.view(2950, 760, s1, "P1-304-303 PAD x3 + 503 CAP (1:1)", (2700, 330))
    vp.hatch([(-15, 0), (-13, 0), (-13, -PAD["steel"] + 3), (-15, -PAD["steel"] + 3)], "hC"); vp.hatch([(13, 0), (15, 0), (15, -PAD["steel"] + 3), (13, -PAD["steel"] + 3)], "hC")
    vp.hatch([(-15, -PAD["steel"] + 3), (15, -PAD["steel"] + 3), (15, -PAD["steel"]), (-15, -PAD["steel"])], "hA")
    vp.rect(-17, -PAD["steel"] - 3, 34, 13, "vis", "#cfd8dc")
    vp.dim((-15, 0), (15, 0), 30, "Ø30 x 2 TUBE + 3 DISC", "h"); vp.dim((17, 0), (17, -PAD["steel"]), -40, f"{mmi(PAD['steel'])}", "v")
    vp.dim((-17, -PAD["steel"] - 3), (17, -PAD["steel"] - 3), -30, "CAP Ø34 x 13, Ø30 bore x 10", "h")
    vp.note(-40, -80, ["cap: FDA silicone 60 Sh, push fit", "tube end sealed by the disc (W2 all round)"], 12)
    # gaskets 1:4
    vg = S.view(700, 1750, s4, "P1-304-501 LID GASKET (1:4) · FDA silicone 3 mm", (150, 1360))
    vg.circle(0, 0, TOPFL["od"] / 2, fill="#cfd8dc"); vg.circle(0, 0, TOPFL["id"] / 2 + 2, fill="#fff")
    vg.dia(0, 0, TOPFL["od"] / 2, 45, (330, 300), f"Ø{mmi(TOPFL['od'])}"); vg.dia(0, 0, TOPFL["id"] / 2 + 2, 225, (-330, -300), f"Ø{mmi(TOPFL['id'] + 4)}")
    dxf_profile(str(DXF / "P1-304-501_lid_gasket"), [circ(TOPFL["od"] / 2), circ(TOPFL["id"] / 2 + 2)], text="P1-304-501 LID GASKET 3mm FDA silicone")
    dxf_profile(str(DXF / "P1-304-301_lid_disc"), [circ(LID["od"] / 2)], holes=[(0, 0, TC4["id"] / 2), (xd, yd, TC3["id"] / 2)], text="P1-304-301 LID 2mm 316L")
    dxf_profile(str(DXF / "P1-304-304_keeper_tab"), rect_pts(KTAB["w"], KTAB["h"]), holes=[(-10, -5, 2.75), (10, -5, 2.75)], text="P1-304-304 KEEPER TAB x4 3mm 304")
    S.table(1500, 1400, [("PART", 120), ("DESCRIPTION", 380), ("QTY", 40), ("STOCK", 520), ("FILE", 300)], [
        ("P1-304-301", "Lid disc", 1, f"316L 2 mm Ø{LID['od']:.0f}, 2 holes", "dxf/P1-304-301_lid_disc"),
        ("P1-304-302a", "4 in BPE short weld ferrule", 1, "14WMP-4 316L (bought, welded in)", "-"),
        ("P1-304-302b", "3 in BPE short weld ferrule", 1, "14WMP-3 316L (bought, welded in)", "-"),
        ("P1-304-303", "Hold-down pad", 3, f"316L tube Ø30 x 2 x {PAD['steel'] - 3:.0f} + disc Ø30 x 3", "-"),
        ("P1-304-304", "Keeper tab", 4, f"304 3 mm {KTAB['w']:.0f} x {KTAB['h']:.0f}, 2 x Ø5.5", "dxf/P1-304-304_keeper_tab"),
        ("P1-304-501", "Lid gasket", 1, "FDA silicone 3 mm 60 Sh", "dxf/P1-304-501_lid_gasket"),
        ("P1-304-503", "Pad cap", 3, "FDA silicone 60 Sh, moulded or cut from Ø34 rod", "-"),
    ], "PARTS", 13, 22)
    S.notes(1500, 1640, 1100, [
        "Weld ferrules from the underside first (seal, ground flush to the bore), then fillet on top; lid flat 1.0 after welding (planish if needed).",
        "Pads: square to the lid 0.5; all three pad faces coplanar 0.5 (the deck must be pressed evenly).",
        "Keeper tabs: fit with the lid on the body and the gasket in place, so the latches pull 2 mm over centre.",
    ], "FABRICATION", 13)
    S.save(DWG / "P1-304-300_lid.svg")


# ================================================================== 400 screen deck
def deck():
    S = sheet("P1-304-400", "SCREEN DECK 12 MESH (MAKE 2)", scale="1:2 · 2:1", material="316L flat bar 3 mm; 316 cloth 12 mesh", finish=FIN_PC,
              mass=kg("P1-304-401", "P1-304-402", "P1-304-403"), qty="1 + 1 spare")
    s4 = SC(2)
    v = S.view(800, 930, s4, "PLAN (1:2)", (150, 330))
    v.circle(0, 0, DECK["od"] / 2, fill=SS); v.circle(0, 0, DECK["od"] / 2 - DECK["t"], fill="#fff")
    for i in range(-15, 16):
        x = i * 15
        h = math.sqrt(max(0, (DECK["od"] / 2 - 3) ** 2 - x ** 2))
        v.line(x, -h, x, h, "thin"); v.line(-h, x, h, x, "thin")
    for k in range(24):
        x, y = P(DECK["od"] / 2 - 1.5, 15 * k); v.circle(x, y, 3, "vis", "#b0bec5")
    v.cmark(0, 0, DECK["od"] / 2 + 15)
    v.dia(0, 0, DECK["od"] / 2, 45, (330, 300), f"Ø{mmi(DECK['od'])} -0/-1 (fits Ø480 shell, 2 radial)")
    v.leader(P(DECK["od"] / 2 - 1.5, 15), (380, 120), ["24 TIG TACKS through cloth and both rings", "every 15°, 4 mm long, ground"])
    v.note(0, -DECK["od"] / 2 - 60, "cloth shown at 15 mm pitch for clarity (actual 2.12 mm pitch)", 12, "middle")
    s2 = SC(0.5)
    ro = DECK["od"] / 2
    vs = S.view(2500 - ro * s2, 900, s2, "SECTION AT THE RIM (2:1)", (1950, 480))
    vs.hatch([(ro - DECK["t"], 0), (ro, 0), (ro, DECK["h_lo"]), (ro - DECK["t"], DECK["h_lo"])], "hB")
    vs.hatch([(ro - DECK["t"], DECK["h_lo"] + 0.6), (ro, DECK["h_lo"] + 0.6), (ro, DECK["h_lo"] + 0.6 + DECK["h_up"]), (ro - DECK["t"], DECK["h_lo"] + 0.6 + DECK["h_up"])], "hB")
    vs.line(ro - 60, DECK["h_lo"] + 0.3, ro, DECK["h_lo"] + 0.3, "vis")
    vs.dim((ro, 0), (ro, DECK["h_lo"]), -40, None, "v"); vs.dim((ro, DECK["h_lo"]), (ro, DECK["h_lo"] + DECK["h_up"] + 0.6), -40, None, "v")
    vs.dim((ro - DECK["t"], 0), (ro, 0), -30, None, "h")
    vs.leader((ro - 40, DECK["h_lo"] + 0.3), (ro - 60, -15), ["CLOTH P1-305 12 x 12 mesh 0.58 wire 316", "tension 20-25 N/cm before tacking"], anchor="end")
    vs.weld((ro, DECK["h_lo"]), (ro + 25, DECK["h_lo"] + 25), "sq", "", tail="W2 24 tacks x 4, ground")
    S.table(1650, 1450, [("PART", 120), ("DESCRIPTION", 380), ("QTY", 50), ("BLANK", 520)], [
        ("P1-304-401", "Upper ring", 1, f"316L flat 25 x 3 x {L_DK:.0f}, roll easy way to Ø{DECK['od']:.0f} OD, butt weld W1"),
        ("P1-304-402", "Lower ring", 1, f"316L flat 10 x 3 x {L_DK:.0f}, roll to Ø{DECK['od']:.0f} OD, butt weld W1"),
        ("P1-304-403", "Cloth", 1, "P1-305 12 mesh cut Ø500, trim flush after tacking"),
        ("P1-304-502", "Deck gasket", 1, f"FDA silicone 2 mm Ø{DECK['od']:.0f} / Ø{LEDGE['id']:.0f} (dxf)"),
    ], "PARTS", 13, 22)
    S.notes(1650, 1620, 1200, [
        "Make both rings first (round ±0.5, butt seams ground flush), then stretch the cloth on a tensioning frame, sandwich it between the rings in a jig.",
        "Tack 24 places through cloth and both rings, trim the cloth to the ring OD, grind the tacks and the OD smooth, passivate.",
        "Check on a light table: no torn or distorted openings; mark the deck S1 / S2 with an etch pen (never stamp the product side).",
        "Inspect every batch (ITP T18); a torn deck is swapped for the spare and the batch is held for QA.",
    ], "FABRICATION AND CARE", 13)
    dxf_profile(str(DXF / "P1-304-502_deck_gasket"), [circ(DECK["od"] / 2), circ(LEDGE["id"] / 2)], text="P1-304-502 DECK GASKET 2mm FDA silicone")
    dxf_profile(str(DXF / "P1-304-403_cloth"), [circ(250.0)], text="P1-304-403 CLOTH Ø500 12 mesh 316 (trim after tacking)")
    S.save(DWG / "P1-304-400_screen_deck.svg")
