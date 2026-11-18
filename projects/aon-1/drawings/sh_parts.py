"""AON-1 detail drawings: rails (tabulated -101/-102), the three frames, switch bracket, stack spacers and rods, board outlines."""
import math

from common import *  # noqa: F401,F403
from mechsheet import dxf_profile

E, FR = D.ENV, D.FR
RAIL, H, RI, L = E["rail"], D.HALF, D.RI, E["L"]
X0, X1, B0, T = FR["bar_x0"], FR["bar_x1"], FR["blk0"], FR["t"]
HP = D.BRD["hp"]
RS = D.RAIL_SCREW
U_HOLE = RS["bar_mid"] - RI            # 3.5 from the rail's inner edge
CSK_D = RS["csk_d"]
CL = RS["d"] + 0.15 * 2                # 2.80 clearance
AL_FILL = "#f2f4f6"


def zscrew(i):
    zm = FR["z"][i] + T / 2
    return zm - FR["dz_screw"], zm + FR["dz_screw"]


ZA = [zscrew(i)[0] for i in range(3)]  # face A (normal to Y): screws along Y into the X bars
ZB = [zscrew(i)[1] for i in range(3)]  # face B (normal to X)


def rr(v, x, y, w, h, r, k="vis", fill="none"):
    """rounded rectangle in model mm."""
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        pts += [(cx + r * math.cos(math.radians(a0 + 90 * t / 6)), cy + r * math.sin(math.radians(a0 + 90 * t / 6))) for t in range(7)]
    v.poly(pts, k, True, fill)


# ================================================================== AON-101 / -102 rails
def rails():
    S = sheet("AON-101", "RAIL, TABULATED: -101 (SWITCH NOTCH) AND -102 (SPRING BORE)", scale="1:1 · 5:1", material=AL6061 + ", 10 mm [.394] square bar",
              finish=ANOD, mass=f"-101 {kg('AON-101')} · -102 {kg('AON-102')}", qty="-101: 2 · -102: 2")
    s1 = SC(1)
    for k, (title, zs, oy) in enumerate((("FACE A: OUTER FACE NORMAL TO ±Y (1:1) · lower edge = inner edge", ZA, 560), ("FACE B: OUTER FACE NORMAL TO ±X (1:1) · lower edge = inner edge", ZB, 1060))):
        v = S.view(220, oy, s1, title, (220, oy - 190))
        v.rect(0, 0, L, RAIL, fill=AL_FILL)
        v.line(0, 1.0, L, 1.0, "thin"); v.line(0, RAIL - 1.0, L, RAIL - 1.0, "thin")
        for z in zs:
            v.circle(z, U_HOLE, CSK_D / 2); v.circle(z, U_HOLE, CL / 2); v.cmark(z, U_HOLE, CSK_D / 2)
        if k == 0:   # notch on the inner face, seen hidden from face A (-101 only)
            v.rect(0, 1.5, D.SWITCH["notch_h"], D.SWITCH["notch_w"], "hid")
            v.leader((D.SWITCH["notch_h"] / 2, 2.5), (40, -24), ["NOTCH (-101 ONLY), SEE END VIEW D"], 12)
        else:        # spring bore (-102 only), hidden
            v.rect(L - D.SPRING["depth"], RAIL / 2 - 1.25, D.SPRING["depth"], 2.5, "hid")
            v.leader((L - 4, RAIL / 2), (L - 10, -38), ["M3 BORE (-102 ONLY), SEE END VIEW E"], 12, anchor="end")
        # baseline dimensions from datum B (the -Z end)
        for j, z in enumerate(zs):
            v.dim((0, RAIL), (z, U_HOLE), 28 + 30 * j if j < 2 else 28 + 30 * j, mmi(z, 2), "h")
        v.dim((0, 0), (L, 0), -40, mmi(L, 1), "h", tol="±0.1 [±.004]")
        v.dim((L, 0), (L, RAIL), -36, mmi(RAIL, 2), "v", tol="±0.02")
        v.dim((zs[1], 0), (zs[1], U_HOLE), 36, mmi(U_HOLE, 2), "v")
        v.leader((zs[1], U_HOLE), (zs[1] + 30, -24),
                 [f"3 x Ø{mmi(CL, 2)} THRU, ⌵ Ø{mmi(CSK_D, 1)} +0.1/-0 x 90°", "for H1 M2.5 ISO 14581; head flush to 0.05 below the face"], 12)
        v.datum((0, RAIL / 2), "B", (-1, 0))
    # ---- end views 5:1
    s5 = SC(5)
    for (title, ox, kind) in (("END VIEW D: -Z END, -101 (5:1)", 300, "notch"), ("END VIEW E: +Z END, -102 (5:1)", 800, "bore"), ("-Z END -102 / +Z END -101: PLAIN (5:1)", 1300, "plain")):
        v = S.view(ox, 1650, s5, title, (ox - 60, 1650 - RAIL * s5 - 90))
        rr(v, 0, 0, RAIL, RAIL, 1.0, fill=AL_FILL)
        v.note(-0.2, -3.6, "● = INNER EDGE (corner toward the satellite axis)", 11)
        v.circle(0, 0, 0.35, fill="#111")
        if kind == "notch":
            v.rect(1.5, 0, D.SWITCH["notch_w"], D.SWITCH["notch_d"], fill="#fff")
            v.dim((1.5, D.SWITCH["notch_d"]), (3.5, D.SWITCH["notch_d"]), 30, mmi(2.0, 1), "h", tol="+0.1/-0")
            v.dim((0, D.SWITCH["notch_d"]), (1.5, D.SWITCH["notch_d"]), 62, mmi(1.5, 1), "h")
            v.dim((3.5, 0), (3.5, D.SWITCH["notch_d"]), -50, mmi(4.5, 1), "v", tol="±0.1")
            v.note(-0.4, -4.6, f"NOTCH DEPTH ALONG THE RAIL {mmi(D.SWITCH['notch_h'], 1)} FROM THE -Z END (FACE A VIEW). Ø0.5 tool corner radius allowed.", 11)
            v.note(-0.4, -5.4, "Notch is on the inner face that FACE A's holes exit into (the Y-facing inner face).", 11)
        elif kind == "bore":
            v.circle(RAIL / 2, RAIL / 2, 1.25); v.circle(RAIL / 2, RAIL / 2, 1.5, "thin"); v.cmark(RAIL / 2, RAIL / 2, 1.5)
            v.leader((RAIL / 2 + 1.06, RAIL / 2 + 1.06), (RAIL + 2.2, RAIL + 1.0), ["M3 x 0.5 - 6H ▽ 7 [.276]", "Ø2.5 [.098] DRILL ▽ 9 [.354]", "on the rail axis ±0.1", "mask during anodise"], 12)
            v.dim((0, RAIL), (RAIL / 2, RAIL / 2), 30, mmi(RAIL / 2, 2), "h")
        v.dim((0, 0), (RAIL, 0), -30, mmi(RAIL, 2), "h", tol="±0.02")
        v.rad(RAIL, RAIL, 1.0, 45, (RAIL + 1.5, RAIL + 2.6), "R1.0 [.039] MIN, 4 LONG EDGES")
    # ---- section C-C 5:1 through a face A hole
    v = S.view(1850, 1650, s5, "SECTION C-C THROUGH A FACE A HOLE (5:1)", (1780, 1650 - RAIL * s5 - 90))
    v.hatch([(0, 0), (U_HOLE - CL / 2, 0), (U_HOLE - CL / 2, RAIL - (CSK_D - CL) / 2), (U_HOLE - CSK_D / 2, RAIL), (0, RAIL)], "hA")
    v.hatch([(U_HOLE + CL / 2, 0), (RAIL, 0), (RAIL, RAIL), (U_HOLE + CSK_D / 2, RAIL), (U_HOLE + CL / 2, RAIL - (CSK_D - CL) / 2)], "hA")
    v.centre(U_HOLE, -1.5, U_HOLE, RAIL + 1.5)
    v.dim((U_HOLE - CSK_D / 2, RAIL), (U_HOLE + CSK_D / 2, RAIL), 36, f"⌵ Ø{mmi(CSK_D, 1)}", "h")
    v.dim((U_HOLE - CL / 2, 0), (U_HOLE + CL / 2, 0), -30, f"Ø{mmi(CL, 2)}", "h")
    v.dim((0, 0), (U_HOLE, 0), -62, mmi(U_HOLE, 2), "h")
    v.angle((U_HOLE, RAIL - CSK_D / 2), 2.2, 45, 135, "90°")
    v.note(RAIL + 0.6, RAIL - 0.3, ["OUTER (CONTACT) FACE", "", "INNER FACE: screw enters", "the frame bar end here"], 12)
    # ---- hole table
    rows = []
    for j in range(3):
        rows.append((f"A{j + 1}", "A (±Y)", mmi(ZA[j], 2), mmi(U_HOLE, 2), f"Ø{CL:.2f} THRU + ⌵ Ø{CSK_D} x 90°", ["-Z", "MID", "+Z"][j] + " frame, X bar end"))
    for j in range(3):
        rows.append((f"B{j + 1}", "B (±X)", mmi(ZB[j], 2), mmi(U_HOLE, 2), f"Ø{CL:.2f} THRU + ⌵ Ø{CSK_D} x 90°", ["-Z", "MID", "+Z"][j] + " frame, Y bar end"))
    rows.append(("D", "-Z end (-101)", "0 to 6.5", "1.5 to 3.5", "notch 2.0 x 4.5 deep", "switch lever SW1/SW2"))
    rows.append(("E", "+Z end (-102)", "340.5 to 331.5", "on axis", "M3 x 0.5-6H ▽7, drill Ø2.5 ▽9", "spring plunger BP-04"))
    S.table(2330, 260, [("HOLE", 60), ("FACE", 130), ("Z FROM -Z END", 170), ("FROM INNER EDGE", 170), ("SIZE", 330), ("MATES", 210)], rows, "HOLE TABLE (both variants unless noted)", 13, 26)
    S.table(2330, 700, [("VARIANT", 110), ("END FEATURE", 380), ("POSITION IN THE SATELLITE", 400), ("QTY", 60)],
            [("-101", "-Z switch notch D", "+X+Y and -X-Y corners", "2"), ("-102", "+Z spring bore E", "+X-Y and -X+Y corners", "2")], "TABULATION", 13, 26)
    S.notes(2330, 860, 1070, [
        "Datum A: face A. Datum B: -Z end face. Datum C: face B. Make from 10 mm square 6061-T6 bar; finish all four faces to 8.50 ±0.02 [.3346 ±.0008] AFTER hard anodise (machine to 8.45-8.47 before anodise; confirm the build-up with the anodiser).",
        "Straightness of each face 0.05 [.002] over the full length; ends square to the axis within 0.05; length 340.50 ±0.10 [13.406 ±.004].",
        "All four long edges R1.0 [.039] minimum (CubeSat Design Specification rev 14.1, rail edge requirement). Break other edges 0.2 max.",
        "Contact faces (both outer faces and both ends): Ra 0.8 µm [32 µin] before anodise, no scratches across the length, no marking. Identify the part on a bag tag only.",
        "Hard anodise all over, Type III Class 1 (undyed), 25-50 µm. Mask the M3 thread (-102). Holes may anodise.",
        "Countersinks: H1 head must sit flush to 0.05 [.002] BELOW the face; check every hole with the screw before anodise and re-check after.",
        "Deburr all holes inside the rail; no burr may protrude past the inner faces (the frame bar ends seat on them).",
        "Inspect per AON-900 T3; record serial, length, 4 faces, straightness on the traveller.",
        VAC,
    ], "NOTES", 13)
    S.save(DWG / "AON-101_rails.svg")


# ================================================================== frames
def frame_outline(v, fill=AL_FILL):
    """plan outline of a frame (top view), model x right / y up."""
    R = FR["relief"]
    q = []    # outer boundary going CCW, built per quadrant
    o = [(X1, -RI), (X1, RI), (X0, RI), (X0, X0 - R), (X0 - R, X0 - R), (X0 - R, X0), (RI, X0), (RI, X1), (-RI, X1), (-RI, X0), (-(X0 - R), X0),
         (-(X0 - R), X0 - R), (-X0, X0 - R), (-X0, RI), (-X1, RI), (-X1, -RI), (-X0, -RI), (-X0, -(X0 - R)), (-(X0 - R), -(X0 - R)), (-(X0 - R), -X0),
         (-RI, -X0), (-RI, -X1), (RI, -X1), (RI, -X0), (X0 - R, -X0), (X0 - R, -(X0 - R)), (X0, -(X0 - R)), (X0, -RI)]
    inner = [(X0, -B0), (X0, B0), (B0, B0), (B0, X0), (-B0, X0), (-B0, B0), (-X0, B0), (-X0, -B0), (-B0, -B0), (-B0, -X0), (B0, -X0), (B0, -B0)]
    v.poly(o, fill=fill)
    v.poly(inner, fill="#fff")
    return o, inner


def frame_sheet(i):
    num = ["AON-103", "AON-104", "AON-105"][i]
    name = ["-Z FRAME", "MID FRAME", "+Z FRAME"][i]
    S = sheet(num, f"{name} (MACHINED 6061-T6)", scale="3:1 · 4:1", material=AL6061 + ", 10 mm [.394] plate", finish=CHEM, mass=kg(num))
    s2 = SC(3)
    v = S.view(800, 1080, s2, f"PLAN, VIEWED FROM +Z (3:1)", (260, 440))
    o, inner = frame_outline(v)
    v.centre(-60, 0, 60, 0); v.centre(0, -60, 0, 60)
    v.text(58, 2, "+X", 14, "start"); v.text(2, 58, "+Y", 14, "start")
    # stack holes
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        if i == 0:
            v.circle(sx * HP, sy * HP, 1.25); v.circle(sx * HP, sy * HP, 1.5, "thin")
        else:
            v.circle(sx * HP, sy * HP, 1.7)
        v.cmark(sx * HP, sy * HP, 1.7)
    stack_txt = "4 x M3 x 0.5-6H THRU (Ø2.5 drill)" if i == 0 else "4 x Ø3.4 [.134] THRU"
    v.leader((HP + 1.2, HP + 1.2), (62, 62), [stack_txt, f"on a {mmi(2 * HP, 1)} square, ⌖ Ø0.1 A B C"], 13)
    # rail screw taps seen hidden in plan (they run in the bar ends)
    zy, zx = zscrew(i)
    for s in (1, -1):
        for e in (1, -1):
            v.line(s * RS["bar_mid"], e * (RI - RS["tap_depth"]), s * RS["bar_mid"], e * RI, "hid")
            v.line(e * (RI - RS["tap_depth"]), s * RS["bar_mid"], e * RI, s * RS["bar_mid"], "hid")
    v.leader((RS["bar_mid"], RI - 2), (66, 30), ["8 x M2.5 x 0.45-6H ▽ 8 [.315] in the bar ends", "(Ø2.05 drill ▽ 10), see VIEW F and table"], 13)
    if i == 0:
        for sx, sy in ((1, 1), (-1, -1)):
            for yy in D.SWITCH["tap_y"]:
                v.circle(sx * RS["bar_mid"], sy * yy, 0.8, "hid")
        v.leader((RS["bar_mid"], D.SWITCH["tap_y"][0]), (66, 10), ["4 x M2 x 0.4-6H ▽ 5 FROM -Z FACE (Ø1.6 drill ▽ 6)", "switch brackets AON-106, +X bar and -X bar"], 13)
    # dims
    v.dim((-X1, -RI), (X1, -RI), -70, mmi(2 * X1, 1), "h")
    v.dim((-RI, -X1), (RI, -X1), -110, mmi(2 * RI, 2), "h", tol="+0/-0.05")
    v.dim((-X1, RI), (-X1, -RI), 70, mmi(2 * RI, 2), "v", tol="+0/-0.05")
    v.dim((X0, -RI), (X1, -RI), -40, mmi(X1 - X0, 1), "h")
    v.dim((B0, -X0), (X0, -X0), 50, None, "h") if False else None
    v.dim((-X0, -B0 - 0), (-B0, -B0), 0, None, "h") if False else None
    v.dim((-HP, HP), (-HP, -HP), 150, mmi(2 * HP, 1), "v")
    v.dim((-HP, HP), (HP, HP), 160, mmi(2 * HP, 1), "h")
    v.dim((B0, X0), (B0, B0), 0, None, "v") if False else None
    v.dim((-X0, X0), (-B0, X0), 50, mmi(X0 - B0, 1), "h")
    v.dim((-B0, X0), (-B0, B0), 40, mmi(X0 - B0, 1), "v") if False else None
    v.datum((X1, -20), "A", (1, 0)); v.datum((20, -X1), "B", (0, -1))
    v.fcf(-X1, -X1 - 26, ["⏥", "0.05"]); v.note(-X1, -X1 - 31, "BOTH Z FACES, AND ∥ 0.05 TO EACH OTHER", 12)
    # ---- detail F (4:1): bar end with the 2 crossing screws, viewed on the bar's outer face
    s4 = SC(4)
    v2 = S.view(1500, 900, s4, "VIEW F: +X BAR, OUTER FACE AT THE +Y END (4:1)", (1500, 640))
    # model: horizontal = y (20 .. 41.5), vertical = z (0 .. T) local
    v2.rect(20, 0, RI - 20, T, fill=AL_FILL)
    v2.line(B0, 0, B0, T, "hid")
    v2.circle(RI - 0.0, zy - FR["z"][i], 0.0)
    v2.line(RI - RS["tap_depth"], zy - FR["z"][i] - 1.025, RI, zy - FR["z"][i] - 1.025, "hid"); v2.line(RI - RS["tap_depth"], zy - FR["z"][i] + 1.025, RI, zy - FR["z"][i] + 1.025, "hid")
    v2.centre(RI - RS["tap_depth"] - 2, zy - FR["z"][i], RI + 2, zy - FR["z"][i])
    v2.circle(RS["bar_mid"] - X0 + 33.0, 0, 0) if False else None
    v2.dim((RI, 0), (RI, zy - FR["z"][i]), -40, mmi(zy - FR["z"][i], 2), "v")
    v2.dim((RI, 0), (RI, T), -100, mmi(T, 1), "v", tol="±0.05")
    v2.dim((RI - RS["tap_depth"], T), (RI, T), 30, mmi(RS["tap_depth"], 1) + " THREAD", "h")
    v2.note(20.5, -2.0, [f"M2.5 tap in the bar END at Z {mmi(zy - FR['z'][i], 2)} from the -Z face (screws along Y, from rail face A)",
                         f"the Y bars' end taps sit at Z {mmi(zx - FR['z'][i], 2)} (screws along X, from rail face B): the two never cross",
                         f"tap position across the bar: {mmi(RS['bar_mid'] - X0, 1)} from the inner face, ±0.05"], 12)
    if i in (0, 2):
        zc = T / 2
        v2.circle(D.PANEL["hole_y"], zc, 0.8); v2.circle(D.PANEL["hole_y"], zc, 1.0, "thin"); v2.cmark(D.PANEL["hole_y"], zc, 1.0)
        v2.dim((20, zc), (D.PANEL["hole_y"], zc), 0, None, "h") if False else None
        v2.leader((D.PANEL["hole_y"] + 0.7, zc + 0.7), (22, T + 5), ["2 x M2 x 0.4-6H ▽ 6 per bar outer face (8 total)",
                                                                                     f"at Y ±{mmi(D.PANEL['hole_y'], 1)}, Z {mmi(zc, 1)} (mid-thickness)", "solar panel screws H2"], 12)
    # ---- section G-G through a corner block (4:1) showing the stack hole
    v3 = S.view(1500, 1500, s4, "SECTION G-G THROUGH THE STACK HOLE (4:1)", (1500, 1290))
    v3.hatch([(B0, 0), (HP - (1.25 if i == 0 else 1.7), 0), (HP - (1.25 if i == 0 else 1.7), T), (B0, T)], "hA")
    v3.hatch([(HP + (1.25 if i == 0 else 1.7), 0), (X0, 0), (X0, T), (HP + (1.25 if i == 0 else 1.7), T)], "hA")
    v3.hatch([(X0, 0), (X1, 0), (X1, T), (X0, T)], "hB")
    v3.centre(HP, -2, HP, T + 2)
    v3.dim((B0, T), (X1, T), 40, mmi(X1 - B0, 1), "h")
    v3.dim((B0, 0), (HP, 0), -36, mmi(HP - B0, 1), "h")
    v3.note(X1 + 1, T / 2, ["block + X bar,", "one piece"], 12)
    # ---- hole table
    rows = []
    for s in (1, -1):
        sg = "+" if s > 0 else "-"
        rows.append((f"T{1 if s > 0 else 2}", f"{sg}X bar, both end faces", f"X {s * RS['bar_mid']:+.1f}", f"Y ±{RI:.1f} (end faces)", f"{zy - FR['z'][i]:.2f}", "M2.5-6H ▽8, along Y"))
        rows.append((f"T{3 if s > 0 else 4}", f"{sg}Y bar, both end faces", f"X ±{RI:.1f} (end faces)", f"Y {s * RS['bar_mid']:+.1f}", f"{zx - FR['z'][i]:.2f}", "M2.5-6H ▽8, along X"))
    rows.append(("S", "corner blocks", f"X ±{HP:.1f}", f"Y ±{HP:.1f}", "thru", "M3-6H THRU" if i == 0 else "Ø3.4 THRU"))
    if i in (0, 2):
        rows.append(("P", "4 bar outer faces", "X ±48.0 / Y ±48.0", f"±{D.PANEL['hole_y']:.1f} along the bar", f"{T / 2:.1f}", "M2-6H ▽6, normal to the face"))
    if i == 0:
        rows.append(("W", "+X and -X bars, -Z face", f"X ±{RS['bar_mid']:.1f}", "Y +17.0, +23.0 (+X) / -17.0, -23.0 (-X)", "from -Z face", "M2-6H ▽5"))
    S.table(2400, 260, [("ID", 40), ("WHERE", 210), ("X", 160), ("Y", 260), ("Z FROM -Z FACE", 130), ("SIZE", 230)], rows,
            f"HOLE TABLE {num} (frame -Z face at satellite Z = {mmi(FR['z'][i], 2)})", 12, 24)
    S.notes(2400, 260 + 24 * (len(rows) + 1) + 40, 1030, [
        f"Datums: A = +X bar outer face, B = -Y bar outer face, C = the -Z face. All features ⌖ Ø0.1 A B C unless noted.",
        f"Bar end faces (Y ±{RI:.1f}, X ±{RI:.1f}) are the rail seats: overall {2 * RI:.2f} +0/-0.05 [{2 * RI / 25.4:.4f} +0/-.002] so the rails pull in to a 100.0 ±0.1 envelope. Square to A/B within 0.03.",
        f"Thickness {T:.2f} ±0.05; both Z faces flat 0.05 and parallel 0.05 (they set the board stack length).",
        "Taps: form-tap or cut, class 6H; blow out chips; check with go/no-go gauges; no helicoils needed (assembly torques on AON-002 are below the 6061 strip torque with 2 x D engagement).",
        "Inside corners: R0.5 max tool radius at the block/bar junctions; the relief square at each outer corner (1.5 x 1.5) clears the rail edge radius.",
        "Chromate-free conversion coat all over after machining (bonding path rail-frame-panel ground < 10 mΩ, AON-900 T11). No anodise on frames.",
        VAC,
    ], "NOTES", 13)
    S.save(DWG / f"{num}_{['zminus', 'mid', 'zplus'][i]}_frame.svg")


# ================================================================== AON-106 switch bracket (sheet metal)
def bracket_sheet():
    S = sheet("AON-106", "DEPLOYMENT SWITCH BRACKET (SHEET METAL)", scale="10:1", material="5052-H32 aluminium sheet 1.0 mm [.040], ASTM B209", finish=CHEM,
              mass=kg("AON-106"), qty="2")
    Sw = D.SWITCH
    t = Sw["t"]
    s5 = SC(10)
    z_top = FR["z"][0]
    leg_h = z_top - 0.3                        # 6.2
    fl_w = X1 - (Sw["leg_x"] + t)              # 5.9
    # flat pattern: leg (y 14..40, h leg_h) + flange (y 14..26, w fl_w) along the bend line, bend allowance for 90°, R1.0 inside, K 0.4
    ri = 1.0
    ba = math.pi / 2 * (ri + 0.4 * t)
    leg_flat = leg_h - (ri + t)
    fl_flat = fl_w - (ri + t) + t
    v = S.view(300, 1250, s5, "FLAT PATTERN (10:1) · cut file AON-106_flat_mm/_in.dxf", (300, 600))
    pts = [(0, 0), (26.0, 0), (26.0, leg_flat), (12.0, leg_flat), (12.0, leg_flat + ba + fl_flat), (0, leg_flat + ba + fl_flat)]
    v.poly(pts, fill=AL_FILL)
    v.line(0, leg_flat + ba / 2, 12.0, leg_flat + ba / 2, "bend")
    holes_leg = [(30.0 - 14.0, 3.0 - 0.3), (36.5 - 14.0, 3.0 - 0.3)]
    holes_fl = [(17.0 - 14.0, leg_flat + ba + fl_flat - (X1 - RS["bar_mid"])), (23.0 - 14.0, leg_flat + ba + fl_flat - (X1 - RS["bar_mid"]))]
    for x, y in holes_leg + holes_fl:
        v.circle(x, y, 1.1); v.cmark(x, y, 1.1)
    v.dim((0, 0), (26.0, 0), -40, mmi(26.0, 1), "h")
    v.dim((0, leg_flat + ba + fl_flat), (12.0, leg_flat + ba + fl_flat), 40, mmi(12.0, 1), "h")
    v.dim((26.0, 0), (26.0, leg_flat), -40, mmi(leg_flat, 2), "v")
    v.dim((0, 0), (0, leg_flat + ba + fl_flat), 60, mmi(leg_flat + ba + fl_flat, 2), "v")
    v.dim((0, holes_leg[0][1]), holes_leg[0], 0, None, "h") if False else None
    v.dim((0, 0), (holes_leg[0][0], holes_leg[0][1]), -80, mmi(holes_leg[0][0], 1), "h")
    v.dim((holes_leg[0][0], holes_leg[0][1]), (holes_leg[1][0], holes_leg[1][1]), 30, mmi(6.5, 1), "h", tol="±0.05")
    v.dim((26.0, 0), holes_leg[1], 0, None, "v") if False else None
    v.dim((0, leg_flat + ba + fl_flat), holes_fl[0], 0, None, "h") if False else None
    v.dim(holes_fl[0], holes_fl[1], -30, mmi(6.0, 1), "h", tol="±0.05")
    v.leader(holes_leg[1], (30, 3), ["2 x Ø2.2 [.087] for H5 M2 (switch)", "D2F mounting holes Ø2.1 at 6.5 pitch [ds: confirm]"], 12)
    v.leader(holes_fl[1], (16, leg_flat + ba + fl_flat + 4), ["2 x Ø2.2 [.087] for H4 M2 (to the -Z frame W taps)"], 12)
    v.note(13, leg_flat + ba / 2 + 0.6, f"BEND UP 90° R{ri:.1f} INSIDE", 12, color="#b00020")
    # formed views
    v2 = S.view(1900, 1250, s5, "FORMED, VIEWED ALONG -Y (10:1), AS FITTED ON THE +X BAR", (1800, 600))
    v2.rect(0, 0, t, leg_h, fill=AL_FILL)
    v2.rect(t, leg_h - t, fl_w, t, fill=AL_FILL)
    v2.rect(t, 0.0, Sw["body"][2], Sw["body"][0], "phan")
    v2.note(t + 0.4, 2.6, "D2F body (phantom)", 11)
    v2.rect(0, leg_h, fl_w + t + 0.1, 4.0, "phan"); v2.note(1, leg_h + 2.0, "-Z frame +X bar (phantom)", 11)
    v2.dim((0, 0), (t, 0), -30, mmi(t, 1), "h")
    v2.dim((0, leg_h), (fl_w + t, leg_h), 70, mmi(fl_w + t, 1), "h")
    v2.dim((0, 0), (0, leg_h), 40, mmi(leg_h, 1), "v")
    v2.angle((t, leg_h - t), 2.0, 180, 270, "90° ±1°")
    S.notes(1800, 1500, 1500, [
        "Cut from DXF (laser or turret punch), deburr, form one 90° bend, inside R1.0, bend allowance per the flat (K = 0.40). Check the formed leg 6.2 ±0.1 and squareness ±1°.",
        "Make 2; the -X bracket is the same part turned 180° about Z (no mirror).",
        "Switch lever must reach through the rail notch and stand 1.5 ±0.3 [.059 ±.012] past the -Z rail end when free; bend the D2F hinge lever only with the switch's own lever spec; adjust by the slotted fit of H5 if needed (AON-900 T6).",
        "Conversion coat MIL-DTL-5541 Type II after forming.",
    ], "NOTES", 13)
    flat = pts
    dxf_profile(str(DXF / "AON-106_flat"), flat, holes=[(x, y, 1.1) for x, y in holes_leg + holes_fl], bends=[((0, leg_flat + ba / 2), (12.0, leg_flat + ba / 2))], text="AON-106 rev A 5052-H32 1.0 mm QTY 2")
    S.save(DWG / "AON-106_switch_bracket.svg")


# ================================================================== AON-107 stack spacers and rods
def stack_sheet():
    S = sheet("AON-107", "STACK SPACERS AND RODS (TABULATED)", scale="2:1 · 1:2", material="spacers 6061-T6 Ø6 bar; rods Ti-6Al-4V M3", finish=CHEM + " (spacers)",
              mass="spacers 4 x 6 sets ≈ 31 g; rods 4 x 4.7 g", qty="see table")
    solids = sorted([(FR["z"][i], FR["z"][i] + T, ["-Z frame", "mid frame", "+Z frame"][i]) for i in range(3)] +
                    [(z, z + D.BRD["t"], bid) for bid, _, z, _ in D.STACK])
    rows = []
    for k, (a, b) in enumerate(zip(solids, solids[1:])):
        Lg = b[0] - a[1]
        trim = b[2] in ("mid frame", "+Z frame")
        rows.append((f"AON-107-{k + 1:02d}", f"{a[2]} → {b[2]}", mmi(Lg, 2), "-0.05/-0.10 TRIM AT ASSEMBLY" if trim else "±0.05", "4", f"{a[1]:.2f} – {b[0]:.2f}"))
    rod_L = D.ROD["z1"] - D.ROD["z0"]
    rows.append(("AON-107-R", "stack rod, Ti-6Al-4V, M3 x 0.5 full thread", mmi(rod_L, 1), "±0.5", "4", f"{D.ROD['z0']:.1f} – {D.ROD['z1']:.1f}"))
    S.table(160, 260, [("PART", 190), ("BETWEEN", 520), ("LENGTH", 230), ("TOL", 380), ("QTY", 60), ("SATELLITE Z", 230)], rows, "TABULATION", 15, 34)
    s2 = SC(10)
    v = S.view(400, 1150, s2, "SPACER, TYPICAL (10:1)", (300, 980))
    Lx = 20.0
    v.hatch([(0, 1.6), (Lx, 1.6), (Lx, 2.75), (0, 2.75)], "hA"); v.hatch([(0, -2.75), (Lx, -2.75), (Lx, -1.6), (0, -1.6)], "hA")
    v.centre(-2, 0, Lx + 2, 0)
    v.dim((Lx, -2.75), (Lx, 2.75), -40, "Ø" + mmi(5.5, 1), "v", tol="±0.05")
    v.dim((0, -1.6), (0, 1.6), 40, "Ø" + mmi(3.2, 1), "v", tol="+0.1/-0")
    v.dim((0, 2.75), (Lx, 2.75), 30, "L (TABLE)", "h")
    v.note(0, -5.5, ["ENDS SQUARE TO THE BORE 0.02, ∥ 0.02, CHAMFER 0.2 x 45° BOTH ENDS", "Ra 1.6 µm on the end faces (they carry the stack preload)"], 12)
    S.notes(160, 1450, 2200, [
        "The stack is a clamped column on each rod: -Z frame (rod tapped through it) / spacers / boards / mid frame / spacers / board / +Z frame, preloaded by the hex standoff H7 on the rod above the +Z frame.",
        "Frames are located by the rails, so the last spacer under the mid frame (-04) and under the +Z frame (-06) is cut to fit: build the bay, measure the gap at each rod with gauge blocks, face the spacer to the gap minus 0.05-0.10, so the H7 preload compresses the column, not the rails.",
        "Rod preload: torque H7 to 0.6 N·m [5.3 lbf·in] against the +Z frame. Rod stress ≈ 190 MPa at 0.6 N·m (K = 0.2) on the M3 stress area 5.03 mm², 23 % of Ti-6Al-4V yield.",
        "Rod ends: deburr the cut ends, start the thread with a die; thin nut H3 under the -Z end board, standoff H7 at the +Z end; stake both with 2216 (no thread locker).",
        "Spacers: lathe from Ø6 6061-T6 bar; drill and ream Ø3.2; part off, then face to length in a collet stop; mark the dash number on the bag tag.",
        "First natural frequency target > 100 Hz for the stack (verify in the sine survey, AON-900 T15).",
    ], "NOTES", 13)
    S.save(DWG / "AON-107_stack.svg")


# ================================================================== AON-B00 board outlines (DXF for KiCad Edge.Cuts)
def boards_sheet():
    S = sheet("AON-B00", "BOARD OUTLINES AND MOUNTING (KICAD EDGE.CUTS SOURCE)", scale="3:1 · 1:1", material="FR4 per board (see AON-600 / board fab notes)", finish="ENIG, LPI mask",
              mass="-", qty="see table")
    w, ch, hp, hd = D.BRD["w"], D.BRD["corner_ch"], HP, D.BRD["hole"]
    h = w / 2
    octo = [(-h + ch, -h), (h - ch, -h), (h, -h + ch), (h, h - ch), (h - ch, h), (-h + ch, h), (-h, h - ch), (-h, -h + ch)]
    s1 = SC(3)
    v = S.view(720, 1000, s1, "STACK BOARD OUTLINE E01-E05, E07 (3:1)", (240, 380))
    v.poly(octo, fill="#e8f5e9")
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        v.circle(sx * hp, sy * hp, hd / 2); v.cmark(sx * hp, sy * hp, hd / 2)
        v.circle(sx * hp, sy * hp, 3.25, "phan")
    v.dim((-h, -h), (h, -h), -50, mmi(w, 1), "h", tol="±0.1")
    v.dim((h, -h), (h, h), -50, mmi(w, 1), "v", tol="±0.1")
    v.dim((-hp, hp), (hp, hp), 70, mmi(2 * hp, 1), "h", tol="±0.05")
    v.dim((-h, hp), (-hp, hp), 30, mmi(h - hp, 1), "h")
    v.leader((hp + 1.1, hp + 1.1), (52, 56), [f"4 x Ø{mmi(hd, 1)} PTH-free NPTH, keep-out Ø6.5 both sides (phantom)", "copper ground ring Ø6.5 on the mounting face (chassis bond)"], 12)
    v.leader((h - ch / 2, h - ch / 2), (50, 46), [f"4 x CHAMFER {mmi(ch, 1)} x 45°: clears the rails"], 12)
    v.note(-h, -h - 14, [f"Rails start at ±41.5: board edge ±{h:.1f} leaves 1.0 [.039] each side. Stack connector BP-05 ESQ-126 centred on Y = -29.0 (2 rows along X).",
                         "Component height limits by bay: see AON-002 (max top-side height = gap to the next board - 2.0)."], 12)
    # solar panel E06
    P = D.PANEL
    s2 = SC(1)
    v2 = S.view(1650, 2000, s2, "SOLAR PANEL E06 OUTLINE AND CELL LAYOUT (1:1) · panel width = satellite Y, Z up", (1450, 2000 - P["z1"] * s2 - 40))
    v2.rect(-P["w"] / 2, P["z0"], P["w"], P["L"], fill="#e8f5e9")
    C = D.CELL
    for k in range(C["n_per_face"]):
        z = D.CELL_Z0 + k * (C["w"] + D.GAP_CELL)
        v2.rect(-C["l"] / 2, z, C["l"], C["w"], fill="#c5cae9")
    for zz in (FR["z"][0] + T / 2, FR["z"][2] + T / 2):
        for yy in (-P["hole_y"], P["hole_y"]):
            v2.circle(yy, zz, P["hole_d"] / 2)
    v2.rect(-P["w"] / 2, Z_MID - 4, P["w"], 8, "phan")
    v2.dim((-P["w"] / 2, P["z0"]), (P["w"] / 2, P["z0"]), -40, mmi(P["w"], 1), "h", tol="±0.1")
    v2.dim((P["w"] / 2, P["z0"]), (P["w"] / 2, P["z1"]), -40, mmi(P["L"], 1), "v", tol="±0.1")
    v2.dim((-P["w"] / 2, P["z0"]), (-P["w"] / 2, D.CELL_Z0), 40, mmi(D.CELL_Z0 - P["z0"], 1), "v")
    v2.dim((-P["w"] / 2, D.CELL_Z0 + 6 * (C["w"] + D.GAP_CELL) + C["w"]), (-P["w"] / 2, P["z1"]), 40, None, "v")
    v2.leader((P["hole_y"], FR["z"][2] + T / 2), (60, P["z1"] + 10), [f"4 x Ø{mmi(P['hole_d'], 1)} for H2 M2, at Y ±{mmi(P['hole_y'], 1)}",
                                                                       f"Z {mmi(FR['z'][0] + T / 2 - P['z0'], 1)} and {mmi(FR['z'][2] + T / 2 - P['z0'], 1)} from the panel's -Z edge"], 12)
    v2.leader((0, Z_MID), (60, Z_MID + 20), ["silicone pad H9 bears on the PCB back at the mid frame (phantom band)"], 12)
    v2.leader((0, D.CELL_Z0 + 20), (60, D.CELL_Z0 + 40), [f"7 x {C['l']:.0f} x {C['w']:.0f} CIC, {D.GAP_CELL} gaps, series string, bypass diode per cell (in CIC)"], 12)
    v2.leader((0, 312), (60, 330), ["sensor zone: -/+ face sun sensor photodiode, NTC, E06A: RBF port + umbilical (window 14 x 8)"], 12)
    rows = [("E01-E04", "stack board", "81 x 81, chamfer 3", "4 x Ø3.2 on 73.0 sq", "E01, E02, E03 lower bay; E04 upper bay"),
            ("E05", "+Z antenna board", "81 x 81, chamfer 3", "4 x Ø3.2 (on H7 standoffs)", "elements wound on the top face, restraint across"),
            ("E07", "-Z end board", "81 x 81, chamfer 3", "4 x Ø3.2 (on the rod ends, thin nuts H3)", "Z coil bonded under it, -Z sun sensor"),
            ("E06A/B", "solar panel", f"{P['w']:.0f} x {P['L']:.1f}", "4 x Ø2.2", "4-layer: L2/L3 embedded spiral coil 2 x 40 turns, 0.2 mm track")]
    S.table(2320, 260, [("BOARD", 120), ("ROLE", 170), ("OUTLINE", 190), ("HOLES", 260), ("NOTE", 330)], rows, "BOARD FAMILY", 12, 26)
    S.notes(2320, 440, 1080, [
        "DXF outlines aon_board_81_mm/_in.dxf and aon_panel_E06_mm/_in.dxf in dxf/ import straight into KiCad Edge.Cuts (origin = satellite axis for the 81 board, panel centre-bottom for E06).",
        "Board fab (all): IPC-6012 Class 3 (space addendum IPC-6012DS where the vendor supports it), Tg ≥ 170 °C, ENIG, no via-in-pad unfilled, 1 oz outer / 1 oz inner minimum, coupons kept.",
        "Assembly: IPC J-STD-001 with space addendum (J-STD-001xS), no-clean flux removed, conformal coat Arathane 5750 / CV-1152 except connectors and the torquer test pads.",
        "Mounting holes are not plated; the chassis ground ring on the mounting face bonds board ground to the frame through the spacer (one-point ground at E01).",
        "Stack bus: ESQ-126-39-G-D (BP-05) at the same X/Y on every stack board; pin allocation in AON-E01.",
    ], "NOTES", 12)
    dxf_profile(str(DXF / "aon_board_81"), octo, holes=[(sx * hp, sy * hp, hd / 2) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))], text="AON 81 board rev A")
    pan = [(-P["w"] / 2, 0), (P["w"] / 2, 0), (P["w"] / 2, P["L"]), (-P["w"] / 2, P["L"])]
    dxf_profile(str(DXF / "aon_panel_E06"), pan, holes=[(yy, zz - P["z0"], P["hole_d"] / 2) for zz in (FR["z"][0] + T / 2, FR["z"][2] + T / 2) for yy in (-P["hole_y"], P["hole_y"])],
                text="AON E06 solar panel rev A")
    S.save(DWG / "AON-B00_boards.svg")


Z_MID = D.Z_MID


def all_parts():
    rails()
    for i in range(3):
        frame_sheet(i)
    bracket_sheet()
    stack_sheet()
    boards_sheet()
