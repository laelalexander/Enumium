"""P1-304-001 general arrangement, -002 section A-A and details."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

C = calcs()
SS = "#f4f6f8"
VX = VBR["x"] + VBR["t"]              # vibrator foot face
VR = 70.0                             # vibrator body radius (envelope, confirm)


def P(r, a):
    return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))


def elev(v, section=False, interfaces=True, vib=True):
    """elevation looking north (x right, z up). section: right half cut on y = 0 (half section), left half outside view."""
    hz = "url(#hA)" if section else SS
    # ---- base: seat ring, upstand, skirt
    for sg in (-1, 1):
        cut = section and sg > 0
        x0, x1 = sg * SEAT["id"] / 2, sg * SEAT["od"] / 2
        v.rect(min(x0, x1), 0, abs(x1 - x0), SEAT["t"], fill="url(#hA)" if cut else SS)
        v.rect(sg * R_I if sg > 0 else -R_O, UPST["z0"], T14, UPST["h"], fill="url(#hC)" if cut else SS)
        v.rect(sg * (SKIRT["od"] / 2 - SKIRT["t"]) if sg > 0 else -SKIRT["od"] / 2, -SKIRT["h"], SKIRT["t"], SKIRT["h"], fill="url(#hC)" if cut else SS)
    if not section:
        v.line(-SEAT["id"] / 2, 0, SEAT["id"] / 2, 0, "hid")
    # centring tab at 270 deg lies on y < 0: seen in front (outside view) at x = 0 -> show the one at 150 deg and 30 deg projected
    for a in (30.0, 150.0):
        x = TAB["r"] * math.cos(math.radians(a))
        v.rect(x - TAB["w"] / 2 * abs(math.sin(math.radians(a))) - (TAB["t"] if x < 0 else 0), -TAB["h"], TAB["w"] * abs(math.sin(math.radians(a))) * 0.6 + TAB["t"], TAB["h"], "vis", SS)
    # ---- isolators at 90 (on y axis: hidden behind), 210 and 330 (front)
    for a in (210.0, 330.0):
        x = R_ISO * math.cos(math.radians(a))
        v.rect(x - ISO["d"] / 2, SEAT["t"], ISO["d"], ISO["h"], fill="#37474f")
        v.rect(x - 8, -8, 16, 8, fill="#cfd8dc"); v.line(x - 4, -14, x - 4, -8, "thin"); v.line(x + 4, -14, x + 4, -8, "thin")   # nut + stud under the seat
        v.rect(x - 8, Z_ISO_TOP + BRK["t"], 16, 8, fill="#cfd8dc")
    # ---- body
    for sg in (-1, 1):
        cut = section and sg > 0
        v.rect(R_I if sg > 0 else -R_O, Z_B0, T14, Z_B1 - Z_B0, fill="url(#hC)" if cut else SS)
        v.rect(R_I if sg > 0 else -TOPFL["od"] / 2, Z_B1, TOPFL["od"] / 2 - R_I, TOPFL["t"], fill="url(#hA)" if cut else SS)
        if cut:
            v.rect(LEDGE["id"] / 2, LEDGE["z"], LEDGE["w"], LEDGE["t"], fill="url(#hA)")
    if section:
        # magnet bars (beyond the cut, y = +-110), magnet, screen deck
        v.rect(-math.sqrt(R_I ** 2 - 122.5 ** 2), BAR["z"], 2 * math.sqrt(R_I ** 2 - 122.5 ** 2), BAR["t"], "vis", "#eceff1")
        v.rect(-MAG["sq"] / 2, BAR["z"] + BAR["t"], MAG["sq"], 6, "vis", "#ffcdd2")
        for k in range(5):
            v.circle(-MAG["sq"] / 2 + 30 + k * 61, BAR["z"] + BAR["t"] + 18, 12.7, "vis", "#ef9a9a")
        for sg in (-1, 1):
            xo = sg * DECK["od"] / 2; xi = sg * (DECK["od"] / 2 - DECK["t"])
            v.rect(min(xo, xi), Z_DECK0, DECK["t"], DECK["h_lo"], fill="url(#hB)")
            v.rect(min(xo, xi), Z_DECK0 + DECK["h_lo"], DECK["t"], DECK["h_up"], fill="url(#hB)")
            v.rect(sg * LEDGE["id"] / 2 if sg < 0 else LEDGE["id"] / 2, Z_DECK0 - DECK["gasket"], DECK["od"] / 2 - LEDGE["id"] / 2, DECK["gasket"], "thin", "#90a4ae") if sg > 0 else None
        v.line(-DECK["od"] / 2 + DECK["t"], Z_DECK0 + DECK["h_lo"], DECK["od"] / 2 - DECK["t"], Z_DECK0 + DECK["h_lo"], "phan")
        # hold-down pad at 270 deg (x = 0) beyond: hidden
        v.rect(-PAD["d"] / 2, Z_DECK1, PAD["d"], PAD["h"] - 2, "hid")
    else:
        v.line(-R_I, LEDGE["z"] + LEDGE["t"], R_I, LEDGE["z"] + LEDGE["t"], "hid")
        v.line(-R_I, BAR["z"], R_I, BAR["z"], "hid")
    # ---- isolator brackets (210 front-left, 330 front-right)
    for a in (210.0, 330.0):
        sg = 1 if math.cos(math.radians(a)) > 0 else -1
        x_in, x_out = sg * R_O, sg * (R_ISO + 25) * abs(math.cos(math.radians(a))) / abs(math.cos(math.radians(a)))
        xc = R_ISO * math.cos(math.radians(a))
        v.rect(min(sg * R_O, xc + sg * 25), Z_ISO_TOP, abs(xc + sg * 25 - sg * R_O), BRK["t"], fill=SS)
        v.rect(sg * R_O if sg > 0 else -R_O - BRK["t"], Z_ISO_TOP, BRK["t"], 40, fill=SS)
    # ---- flex band and clamps
    for sg in (-1, 1):
        x = R_O if sg > 0 else -R_O - 2
        v.rect(x, Z_ISO_TOP - 26, 2, 60, "vis", "#fffde7")
        for zc in (Z_ISO_TOP - 16, Z_ISO_TOP + 24):
            v.rect(x + (2 if sg > 0 else -3), zc - 6, 3, 12, "vis", "#b0bec5")
    # ---- lid, gasket, ferrules
    v.rect(-TOPFL["od"] / 2, Z_TOP, TOPFL["od"], LID["gasket"], "thin", "#90a4ae")
    if section:
        v.rect(-LID["od"] / 2, Z_LID0, LID["od"] / 2 - TC4["id"] / 2, LID["t"], fill=SS)
        v.rect(TC4["id"] / 2, Z_LID0, LID["od"] / 2 - TC4["id"] / 2, LID["t"], fill="url(#hA)")
    else:
        v.rect(-LID["od"] / 2, Z_LID0, LID["od"], LID["t"], fill=SS)
    zf = Z_FER0
    for sg in (-1, 1):
        cut = section and sg > 0
        v.rect(sg * TC4["id"] / 2 if sg > 0 else -TC4["od"] / 2, zf, (TC4["od"] - TC4["id"]) / 2, TC4["L"] - 8, fill="url(#hA)" if cut else SS)
        v.rect(sg * TC4["id"] / 2 if sg > 0 else -TC4["fl"] / 2, zf + TC4["L"] - 8, (TC4["fl"] - TC4["id"]) / 2, 8, fill="url(#hA)" if cut else SS)
    xd = TC3["r"] * math.cos(math.radians(TC3["a"]))
    v.rect(xd - TC3["od"] / 2, zf, TC3["od"], TC3["L"] - 8, fill=SS); v.rect(xd - TC3["fl"] / 2, zf + TC3["L"] - 8, TC3["fl"], 8, fill=SS)
    # ---- latches (45, 135 front; shown at their projected x)
    for a in ((225.0,) if section else (225.0, 315.0)):          # front latches (45/135 are behind); right half is cut away in section
        x = (LATCH["r"] + 10) * math.cos(math.radians(a))
        v.rect(x - 15, Z_B1 - 55, 30, 60, "vis", "#cfd8dc"); v.rect(x - 12, Z_LID0 + LID["t"], 24, 5, "vis", "#cfd8dc")
    # ---- vibrator bracket and vibrator
    v.rect(VBR["x"], VBR["z0"], VBR["t"], VBR["z1"] - VBR["z0"], fill="url(#hA)" if section else SS)
    v.poly([(R_O, VBR["z0"]), (VBR["x"], VBR["z0"]), (VBR["x"], VBR["z1"]), (TOPFL["od"] / 2 + 1, VBR["z1"] - 60), (TOPFL["od"] / 2 + 1, Z_TOP), (R_O, Z_B1)], fill=SS)
    if vib:
        v.rect(VX, Z_VIB - 85, 20, 170, "vis", "#c5cae9")
        v.rect(VX + 15, Z_VIB - 130, 2 * VR, 260, "vis", "#c5cae9")
        v.text(VX + 15 + VR, Z_VIB + 20, "P1-306", 15, color="#283593", bold=True)
        v.text(VX + 15 + VR, Z_VIB - 4, "VIBRATOR", 13, color="#283593")
        v.text(VX + 15 + VR, Z_VIB - 24, "axis vertical", 12, color="#283593")
    # ---- centre lines
    v.centre(0, -SKIRT["h"] - 30, 0, zf + TC4["L"] + 40)
    v.centre(VX + 15 + VR, Z_VIB - 150, VX + 15 + VR, Z_VIB + 150) if vib else None
    if interfaces:
        # drum rim and liner (phantom), valve outlet + sock
        for sg in (-1, 1):
            v.poly([(sg * DRUM["od"] / 2, -200), (sg * DRUM["od"] / 2, 0), (sg * DRUM["id"] / 2, 0), (sg * DRUM["id"] / 2, -200)], "phan", closed=False)
        v.text(-DRUM["od"] / 2 + 40, -150, "55 gal DRUM P1-308 + liner (phantom)", 13, anchor="start", color="#607d8b")
        v.rect(-55, Z_VALVE, 110, 40, "phan")
        v.text(70, Z_VALVE + 46, "BLENDER VALVE P1-331 OUTLET (phantom)", 13, anchor="start", color="#607d8b")
        v.poly([(-50, Z_VALVE), (-52, zf + TC4["L"] - 2), (52, zf + TC4["L"] - 2), (50, Z_VALVE)], "phan", closed=False)


def plan(v):
    """plan looking down, lid removed on the right half? (full lid shown)."""
    v.circle(0, 0, SEAT["od"] / 2, fill=SS); v.circle(0, 0, SEAT["id"] / 2, "hid")
    v.circle(0, 0, TOPFL["od"] / 2, fill=SS)
    v.circle(0, 0, LID["od"] / 2, fill="#fafafa")
    v.circle(0, 0, TC4["fl"] / 2); v.circle(0, 0, TC4["id"] / 2)
    xd, yd = P(TC3["r"], TC3["a"]); v.circle(xd, yd, TC3["fl"] / 2); v.circle(xd, yd, TC3["id"] / 2)
    for a in A_ISO:
        x, y = P(R_ISO, a); v.circle(x, y, ISO["d"] / 2, "hid"); v.cmark(x, y, 6)
        # bracket outline
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = [(R_O, -BRK["w"] / 2), (R_ISO + 25, -BRK["w"] / 2), (R_ISO + 25, BRK["w"] / 2), (R_O, BRK["w"] / 2)]
        v.poly([(px * c - py * s, px * s + py * c) for px, py in pts], "vis", True, SS)
    for a in (30.0, 150.0, 270.0):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = [(TAB["r"], -TAB["w"] / 2), (TAB["r"] + TAB["t"], -TAB["w"] / 2), (TAB["r"] + TAB["t"], TAB["w"] / 2), (TAB["r"], TAB["w"] / 2)]
        v.poly([(px * c - py * s, px * s + py * c) for px, py in pts], "hid")
    for k in range(LATCH["n"]):
        a = LATCH["a0"] + 90 * k; c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = [(LATCH["r"] - 25, -20), (LATCH["r"] + 25, -20), (LATCH["r"] + 25, 20), (LATCH["r"] - 25, 20)]
        v.poly([(px * c - py * s, px * s + py * c) for px, py in pts], "vis", True, "#cfd8dc")
    v.rect(VBR["x"], -VBR["w"] / 2, VBR["t"], VBR["w"], fill=SS)
    for y in (-VBR["w"] / 2 + 14, VBR["w"] / 2 - 14):
        v.rect(R_O, y - VBR["gus_t"] / 2, VBR["x"] - R_O, VBR["gus_t"], fill=SS)
    v.circle(VX + 15 + VR, 0, VR, "vis", "#c5cae9"); v.rect(VX, -60, 20, 120, "vis", "#c5cae9")
    v.circle(0, 0, DRUM["od"] / 2, "phan")
    v.cmark(0, 0, SEAT["od"] / 2 + 20)


def ga():
    S = sheet("P1-304-001", "DRUM-TOP SIFTER GENERAL ARRANGEMENT", scale="1:2 · 1:4", material="see item list", finish="see parts",
              mass=f"{C['M']:.0f} kg [{C['M'] * 2.2046:.0f} lb] vibrating + base {MASS.get('P1-304-101', 0) + MASS.get('P1-304-102', 0) + MASS.get('P1-304-103', 0):.0f} kg")
    s = SC(2)
    v = S.view(1000, 1060, s, "ELEVATION LOOKING NORTH (1:2), RIGHT HALF IN SECTION ON Y = 0", (120, 360))
    elev(v, section=True)
    # balloons
    v.tag(-420, -60, 1, (-SEAT["od"] / 2 + 20, 3)); v.tag(-470, 110, 2, (-R_O, 110)); v.tag(-330, 240, 3, (-200, Z_LID0 + 1)); v.tag(380, 120, 4, (DECK["od"] / 2 - 2, Z_DECK1 - 5))
    v.tag(-120, 260, 13, (xd := TC3["r"] * math.cos(math.radians(TC3["a"])), Z_FER0 + 10))
    v.tag(-420, 30, 10, (R_ISO * math.cos(math.radians(210)), 20)); v.tag(-460, -10, 12, (-R_O - 2, 15))
    v.tag(80, 30, 9, (60, BAR["z"] + 20)); v.tag(-470, 180, 11, (-(LATCH["r"] + 10) * 0.7071, Z_B1 - 20))
    v.tag(560, 300, 8, (VX + 15 + VR, Z_VIB + 90))
    # dimensions
    v.dim((-SEAT["od"] / 2, 0), (SEAT["od"] / 2, 0), -120, f"SEAT RING Ø{mmi(SEAT['od'])}", "h")
    v.dim((-DRUM["od"] / 2, -200), (DRUM["od"] / 2, -200), 30, f"DRUM RIM Ø{mmi(DRUM['od'])} (ref)", "h")
    v.dim((-TOPFL["od"] / 2, Z_TOP), (TOPFL["od"] / 2, Z_TOP), 150, f"LID / FLANGE Ø{mmi(TOPFL['od'])}", "h")
    v.dim((-R_O, Z_B0), (R_O, Z_B0), -30, f"BODY Ø{mmi(2 * R_I)} ID", "h") if False else None
    xl = -SEAT["od"] / 2
    v.dim((xl, 0), (xl, C["z_inlet"]), 150, f"{mmi(C['z_inlet'])} INLET (= 1,235 [48.62] AFF)", "v")
    v.dim((xl, 0), (xl, Z_TOP), 90, None, "v")
    v.dim((xl, -SKIRT["h"]), (xl, 0), 90, None, "v")
    v.dim((VX + 15 + VR, 0), (VX + 15 + VR, Z_VIB), 120 + 0, f"{mmi(Z_VIB)}", "v")
    v.dim((0, Z_VIB + 160), (VX + 15 + VR, Z_VIB + 160), 20, None, "h")
    v.dim((0, Z_VALVE + 40), (0, Z_VALVE), -170, f"VALVE {mmi(Z_VALVE)}", "v") if False else None
    v.leader((40, Z_VALVE), (160, Z_VALVE + 80), [f"valve outlet {mmi(Z_VALVE)} above rim = 1,261 [49.65] AFF", f"sock P1-346 over {mmi(C['gap_valve'])} gap"])
    # plan
    sp = SC(4)
    vp = S.view(2560, 700, sp, "PLAN (1:4), LID ON", (2050, 330))
    plan(vp)
    vp.dim((-SEAT["od"] / 2, -SEAT["od"] / 2 - 30), (SEAT["od"] / 2, -SEAT["od"] / 2 - 30), -10, None, "h")
    vp.leader(P(R_ISO, 90), (120, 420), ["3 ISOLATORS P1-341 on R" + mmi(R_ISO), "at 90°, 210°, 330°"])
    vp.leader(P(TAB["r"], 150), (-470, 330), ["3 CENTRING TABS at 30°, 150°, 270°", "(hidden: outside the drum rim)"], anchor="end")
    vp.leader(P(LATCH["r"] + 25, 135), (-480, 230), ["4 DRAW LATCHES P1-342 at 45° + 90°"], anchor="end")
    vp.leader(P(TC3["r"], TC3["a"]), (-480, -200), ["3 in TC DUST PORT on R" + mmi(TC3["r"]) + " at 200°"], anchor="end")
    vp.leader((0, TC4["fl"] / 2), (-150, 380), ["4 in TC INLET on axis"], anchor="end")
    vp.text(0, -SEAT["od"] / 2 - 110, "NORTH ↑ (+y) · VIBRATOR EAST (+x)", 14)
    # item list
    S.table(2050, 1200, [("ITEM", 50), ("PART", 120), ("DESCRIPTION", 560), ("QTY", 45), ("SOURCE / DRAWING", 280)],
            [(a, b, c, d, e) for a, b, c, d, e in ITEMS], "ITEM LIST", 13, 22)
    S.table(120, 1600, [("INTERFACE", 300), ("VALUE", 420), ("SET BY", 420)], [
        ("Drum rim (top)", "1,054 [41.50] AFF, Ø584 [23.0]", "drum P1-308 on dolly P1-309"),
        ("Seat ring on the rim", "rests by weight; 3 tabs centre it ±2", "liner folded over the rim under the seat"),
        ("Inlet ferrule top", f"{mmi(C['z_inlet'])} above rim = 1,235 AFF", "blender valve P1-331 outlet 1,261 AFF"),
        ("Dust port", "3 in TC on R170 at 200°", "hose to P1-310, blast gate ≈ 100 cfm"),
        ("Vibrator supply", "115 V 1-ph, 15 A circuit, KM-306", "panel MS-P1 (E01)"),
        ("Bonding", "body to base braid P1-347; base to drum ground clip", "NFPA 77 / 652"),
    ], "PLANT INTERFACES", 13, 22)
    S.notes(1250, 1600, 750, [
        "Vibrating parts: body 200, lid 300, deck 400, magnet, vibrator. Fixed: base 100 on the drum.",
        f"Vibrator weights set to about {C['setting'] * 100:.0f} % for ±{AMP_TARGET} mm at the deck ({C['acc_g']:.1f} g); see P1-304-900.",
        f"Isolators give {C['fn']:.1f} Hz on {ISO['k']:.0f} N/mm each: {C['T'] * 100:.1f} % of the force reaches the drum.",
        "Lift-off: drum rolls out on its dolly with the sifter removed (2 people, ≈ 45 kg [100 lb] with base).",
        "All dimensions mm [in]. Third-angle projection.",
    ], "NOTES", 13)
    S.save(DWG / "P1-304-001_general_arrangement.svg")


def section():
    S = sheet("P1-304-002", "SECTION A-A AND DETAILS", scale="1:1 · 2:1", material="see item list", finish="see parts", mass="-")
    s = SC(1)
    # detail B: isolator stack (1:1) at 330 deg cut radially
    v = S.view(300 - (R_I - 40) * s, 760, s, "DETAIL B (1:1): ISOLATOR STACK, RADIAL SECTION AT 330°", (120, 330))
    x0 = R_ISO
    v.rect(SEAT["id"] / 2 - 200 + 200 - 20 + 0 + 0, 0, 0, 0) if False else None
    v.hatch([(R_I - 40, 0), (SEAT["od"] / 2, 0), (SEAT["od"] / 2, SEAT["t"]), (R_I - 40, SEAT["t"])], "hA")
    v.rect(x0 - 4.25, 0, 8.5, SEAT["t"], "vis", "#fff")
    v.rect(x0 - ISO["d"] / 2, SEAT["t"], ISO["d"], ISO["h"], "vis", "#37474f")
    v.rect(x0 - 4, -16, 8, 16 + SEAT["t"], "thin"); v.rect(x0 - 4, Z_ISO_TOP, 8, 18, "thin")
    v.rect(x0 - 8, -14, 16, 8, "vis", "#cfd8dc"); v.rect(x0 - 8, Z_ISO_TOP + BRK["t"], 16, 8, "vis", "#cfd8dc")
    v.hatch([(R_O, Z_ISO_TOP), (R_ISO + 25, Z_ISO_TOP), (R_ISO + 25, Z_ISO_TOP + BRK["t"]), (R_O, Z_ISO_TOP + BRK["t"])], "hB")
    v.rect(x0 - 4.5, Z_ISO_TOP, 9, BRK["t"], "vis", "#fff")
    v.hatch([(R_O, Z_ISO_TOP), (R_O + BRK["t"], Z_ISO_TOP), (R_O + BRK["t"], Z_ISO_TOP + 40), (R_O, Z_ISO_TOP + 40)], "hB")
    v.hatch([(R_I, Z_B0), (R_O, Z_B0), (R_O, Z_B0 + 60), (R_I, Z_B0 + 60)], "hC")
    v.hatch([(R_I, UPST["z0"]), (R_O, UPST["z0"]), (R_O, UPST["z0"] + UPST["h"]), (R_I, UPST["z0"] + UPST["h"])], "hC")
    v.rect(R_O, Z_ISO_TOP - 26, 2, 60, "vis", "#fffde7")
    v.poly([(DRUM["id"] / 2, -40), (DRUM["id"] / 2, 0), (DRUM["od"] / 2, 0), (DRUM["od"] / 2, -40)], "phan", closed=False)
    v.dim((x0, SEAT["t"]), (x0, Z_ISO_TOP), 70, None, "v") if False else None
    v.dim((x0 + ISO["d"] / 2, SEAT["t"]), (x0 + ISO["d"] / 2, Z_ISO_TOP), -40, f"{mmi(ISO['h'])} free", "v")
    v.dim((R_I, Z_ISO_TOP), (R_I, Z_B0), 40, f"{mmi(Z_B0 - Z_ISO_TOP)} GAP", "v")
    v.dim((0 + R_I - 40, 0), (R_ISO, 0), 0, None, "h") if False else None
    v.dim((DRUM["od"] / 2, 0), (R_ISO, 0), -40, f"{mmi(R_ISO - DRUM['od'] / 2)}", "h")
    v.leader((R_O + 1, Z_ISO_TOP + 10), (R_O + 140, Z_ISO_TOP + 140), ["FLEX BAND P1-344, 10 slack", "2 worm clamps, 3 N·m"])
    v.leader((x0, -10), (x0 + 80, -70), ["H1 M8 nyloc + washer 12 N·m", "nut clears the drum rim"])
    v.leader((x0, Z_ISO_TOP + BRK["t"] + 4), (x0 + 120, Z_ISO_TOP + 90), ["H2 M8 nyloc + washer 12 N·m"])
    v.text(DRUM["od"] / 2 - 10, -55, "DRUM RIM", 12, color="#607d8b")
    # detail C: deck on ledge under lid pad (2:1)
    s2 = SC(0.5)
    vc = S.view(1700 - (LEDGE["id"] / 2 - 15) * s2, 450 + 165 * s2, s2, "DETAIL C (2:1): SCREEN DECK, LEDGE, LID PAD", (1500, 380))
    ox = DECK["od"] / 2
    vc.hatch([(R_I, LEDGE["z"] - 25), (R_O, LEDGE["z"] - 25), (R_O, Z_TOP + 0), (R_I, Z_TOP + 0)], "hC")
    vc.hatch([(R_I, Z_B1), (R_I + 35, Z_B1), (R_I + 35, Z_TOP), (R_I, Z_TOP)], "hA")
    vc.hatch([(LEDGE["id"] / 2, LEDGE["z"]), (R_I, LEDGE["z"]), (R_I, LEDGE["z"] + LEDGE["t"]), (LEDGE["id"] / 2, LEDGE["z"] + LEDGE["t"])], "hA")
    vc.rect(LEDGE["id"] / 2, Z_DECK0 - DECK["gasket"], ox - LEDGE["id"] / 2, DECK["gasket"], "vis", "#90a4ae")
    vc.hatch([(ox - DECK["t"], Z_DECK0), (ox, Z_DECK0), (ox, Z_DECK0 + DECK["h_lo"]), (ox - DECK["t"], Z_DECK0 + DECK["h_lo"])], "hB")
    vc.hatch([(ox - DECK["t"], Z_DECK0 + DECK["h_lo"] + 0.6), (ox, Z_DECK0 + DECK["h_lo"] + 0.6), (ox, Z_DECK1), (ox - DECK["t"], Z_DECK1)], "hB")
    vc.line(LEDGE["id"] / 2 - 15, Z_DECK0 + DECK["h_lo"] + 0.3, ox, Z_DECK0 + DECK["h_lo"] + 0.3, "vis")
    vc.rect(R_I - 15 - 30, Z_LID0, 60, LID["t"], "vis", SS) if False else None
    vc.hatch([(LEDGE["id"] / 2 - 15, Z_LID0), (R_I + 35, Z_LID0), (R_I + 35, Z_LID0 + LID["t"]), (LEDGE["id"] / 2 - 15, Z_LID0 + LID["t"])], "hA")
    vc.rect(R_I, Z_TOP, 35, LID["gasket"], "vis", "#90a4ae")
    vc.dim((ox, Z_DECK0), (ox, Z_DECK1), -60, None, "v")
    vc.dim((LEDGE["id"] / 2, LEDGE["z"]), (LEDGE["id"] / 2, LEDGE["z"] + LEDGE["t"]), 40, None, "v")
    vc.dim((ox, Z_DECK1), (ox, Z_LID0), -60, f"{mmi(Z_LID0 - Z_DECK1)}: pad {mmi(PAD['h'])} free, squeezed 2", "v")
    vc.dim((LEDGE["id"] / 2, LEDGE["z"] - 10), (R_I, LEDGE["z"] - 10), -10, None, "h")
    vc.dim((ox, Z_DECK0 - 12), (R_I, Z_DECK0 - 12), -10, f"{mmi(R_I - ox)} radial", "h")
    vc.leader((ox - DECK["t"] / 2, Z_DECK0 + DECK["h_lo"] + 0.3), (ox - 60, Z_DECK0 + 55), ["12 MESH CLOTH P1-305 clamped between the rings,", "rings TIG tacked through the cloth (P1-304-400)"], anchor="end")
    vc.leader((R_I - 10, Z_DECK0 - 1), (R_I - 80, Z_DECK0 - 25), ["DECK GASKET P1-304-502 2 mm"], anchor="end")
    vc.leader((R_I + 20, Z_TOP + 1.5), (R_I + 60, Z_TOP + 30), ["LID GASKET P1-304-501 3 mm"])
    vc.leader((LEDGE["id"] / 2 + 5, LEDGE["z"] + 3), (LEDGE["id"] / 2 - 40, LEDGE["z"] - 30), ["LEDGE P1-304-204", "fillet weld W4 top, seal weld under"], anchor="end")
    # section A-A full at 1:2 (bottom left)
    s3 = SC(2)
    va = S.view(820, 1850, s3, "SECTION A-A (1:2) ON Y = 0", (120, 1470))
    elev(va, section=True, interfaces=False, vib=False)
    S.notes(2250, 1450, 1100, [
        "Product path: valve sock > 4 in inlet > screen deck (overs stay on the deck, cleared each batch) > grate magnet > drum liner.",
        "No ledges or threads in the product zone: bars and ledge are fully seal-welded and ground; deck and magnet lift out.",
        f"Screen open area {C['open_area'] * 100:.0f} %, {C['area_dm2']:.1f} dm² of 12 mesh: rated about {C['cap']:.0f} kg/min against {RATE_KGMIN} kg/min target.",
        "Gaskets FDA silicone; deck sits on the ledge gasket and is held by 3 lid pads (no screws).",
    ], "NOTES", 13)
    S.save(DWG / "P1-304-002_sections.svg")
