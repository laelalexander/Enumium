"""P1-301 trough: weldment 100, shell flat pattern 101, plates 102/103/105 (+ DXF), stuffing box 104 and gland follower 501."""
import math

import design as D
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403

s5, s2, s1, s4, s8 = SC(5), SC(2), SC(1), SC(4), SC(8)
R_O = R_IN + T_SH
R_EP = R_O + EP_OFF                          # end plate profile radius 298
Y_LUG0 = R_O
NEUTRAL = R_IN + T_SH / 2
ARC = math.pi * NEUTRAL
DEV_W = ARC + 2 * H_SIDE                     # developed width of the U shell
PROBE = dict(x=-300.0, z=Z_AX + 200.0, d=38.6)


def u_outline(r, top, cx=0.0, cz=Z_AX, n=60):
    """U profile in an end view (y, z): flat top at cz + top."""
    pts = [(-r, cz + top)] + [(r * math.cos(math.radians(a)), cz + r * math.sin(math.radians(a))) for a in [180 + 180 * i / n for i in range(n + 1)]] + [(r, cz + top)]
    return [(cx + y, z) for y, z in pts]


# ================================================================== 100 trough weldment
def weldment():
    S = sheet("P1-301-100", "TROUGH WELDMENT", scale="1:5, 1:2", material=SS316L, finish=FIN_PC + " inside; outside " + "#4 / bead blast",
              mass=kg("P1-301-101", "P1-301-102", "P1-301-103", "P1-301-104", "P1-301-105", "P1-301-106", "P1-301-107"))
    # ---------- plan (x, y), looking down: screen up = +y (back)
    P = S.view(700, 480, s5, "PLAN (cover removed)  1:5", (120, 70))
    P.rect(-FL_OUT_X / 2, -FL_OUT_Y / 2, FL_OUT_X, FL_OUT_Y)
    P.rect(-L_IN / 2, -W_IN / 2, L_IN, W_IN, "thin")
    for sx in (-1, 1):
        x0 = L_IN / 2 if sx > 0 else -L_IN / 2 - T_EP
        P.rect(x0, -R_EP, T_EP, 2 * R_EP, "hid")
        xb = L_IN / 2 + T_EP if sx > 0 else -L_IN / 2 - BOX["x_face"]
        P.rect(xb, -BOX["od"] / 2, BOX["x_face"] - T_EP, BOX["od"], "vis")
        for x in LUG["x"]:
            for sy in (-1, 1):
                y0, y1 = sorted((sy * FL_OUT_Y / 2, sy * 430))
                P.rect(x - LUG["w"] / 2, y0, LUG["w"], y1 - y0, "vis")
                P.circle(x, sy * Y_LEG, 7, "vis")
    P.circle(0, 0, TC4_OD / 2 - 1.65, "hid"); P.cmark(0, 0, 50)
    P.centre(-560, 0, 560, 0)
    for x in LUG["x"]:
        P.centre(x, -470, x, 470)
    P.dim((-FL_OUT_X / 2, FL_OUT_Y / 2), (FL_OUT_X / 2, FL_OUT_Y / 2), 70, f"FLANGE {mmi(FL_OUT_X)}", "h")
    P.dim((-L_IN / 2, -W_IN / 2), (L_IN / 2, -W_IN / 2), -150, f"INSIDE {mmi(L_IN)}", "h")
    P.dim((LUG["x"][0], -430), (LUG["x"][1], -430), -60, f"LUGS {mmi(600)}", "h")
    P.dim((FL_OUT_X / 2, -FL_OUT_Y / 2), (FL_OUT_X / 2, FL_OUT_Y / 2), -70, f"{mmi(FL_OUT_Y)}", "v")
    P.dim((-FL_OUT_X / 2, -W_IN / 2), (-FL_OUT_X / 2, W_IN / 2), 50, f"INSIDE {mmi(W_IN)}", "v")
    P.tag(-640, 380, 3, (-500, 300)); P.tag(-470, 380, 5, (-330, 400)); P.tag(600, 230, 4, (490, 60))
    P.note(-640, -380, ["FRONT", "(y-)"], 13); P.note(-640, 300, ["BACK (y+)", "hinge side"], 13)

    # ---------- front elevation (x, z), seen from the front: screen right = +x
    F = S.view(700, 1170 + Z_AX * s5, s5, "FRONT ELEVATION  1:5", (120, 905))

    def fz(z):
        return z
    F.rect(-L_IN / 2, Z_TB, L_IN, Z_AX + H_SIDE - Z_TB)                          # shell silhouette
    F.line(-L_IN / 2, Z_AX, L_IN / 2, Z_AX, "hid")                              # tangent line (start of the radius)
    F.rect(-FL_OUT_X / 2, Z_AX + H_SIDE, FL_OUT_X, T_FL)                          # flange
    for sx in (-1, 1):
        x0 = L_IN / 2 if sx > 0 else -L_IN / 2 - T_EP
        re = R_EP if sx > 0 else RING["r_out"]
        F.rect(x0, Z_AX - re, T_EP, re + H_SIDE, "vis" if sx > 0 else "phan")
        if sx < 0:
            F.rect(-L_IN / 2, Z_AX - RING["r_out"], RING["t"], RING["r_out"] + H_SIDE)
        xb = L_IN / 2 + T_EP if sx > 0 else -L_IN / 2 - BOX["x_face"]
        F.rect(xb, Z_AX - BOX["od"] / 2, BOX["x_face"] - T_EP, BOX["od"])
        F.line(min(xb, xb + (BOX["x_face"] - T_EP)), Z_AX - BOX["bore"] / 2, max(xb, xb + BOX["x_face"] - T_EP), Z_AX - BOX["bore"] / 2, "hid")
        for x in LUG["x"]:
            pass
    for x in LUG["x"]:
        F.rect(x - LUG["w"] / 2, Z_RAIL, LUG["w"], LUG["t"])
        F.poly([(x - 5, Z_RAIL), (x + 5, Z_RAIL), (x + 5, Z_RAIL - 100), (x - 5, Z_RAIL - 100)], "vis")
    F.rect(-TC4_OD / 2, Z_TB - TC4_FER_L, TC4_OD, TC4_FER_L - 4); F.rect(-TC4_FER_OD / 2, Z_TB - TC4_FER_L, TC4_FER_OD, 4)
    F.circle(PROBE["x"], PROBE["z"], 25.25); F.circle(PROBE["x"], PROBE["z"], 17.4); F.cmark(PROBE["x"], PROBE["z"], 25)
    F.centre(-600, Z_AX, 600, Z_AX); F.centre(0, Z_TB - 60, 0, Z_FLTOP + 40)
    F.dim((L_IN / 2 + BOX["x_face"], Z_AX), (L_IN / 2 + BOX["x_face"], Z_FLTOP), -120, f"{mmi(H_SIDE + T_FL)}", "v")
    F.dim((L_IN / 2 + BOX["x_face"], Z_TB), (L_IN / 2 + BOX["x_face"], Z_AX), -120, f"{mmi(R_O)}", "v")
    F.dim((-L_IN / 2 - BOX["x_face"], Z_AX - 75), (L_IN / 2 + BOX["x_face"], Z_AX - 75), -330, f"BOX FACE TO BOX FACE {mmi(L_IN + 2 * BOX['x_face'])}  ±0.5", "h")
    F.dim((L_IN / 2, Z_AX - R_EP), (L_IN / 2 + T_EP, Z_AX - R_EP), -40, f"{mmi(T_EP)}", "h")
    F.dim((PROBE["x"], PROBE["z"]), (-L_IN / 2, PROBE["z"]), 0, f"{mmi(150)}", "h", ext=False)
    F.dim((PROBE["x"] - 60, PROBE["z"]), (PROBE["x"] - 60, Z_AX), 0, f"{mmi(200)}", "v", ext=False)
    F.dim((x - 60, Z_RAIL), (x - 60, Z_AX), 0, None, "v") if False else None
    F.dim((LUG["x"][1] + 60, Z_RAIL), (LUG["x"][1] + 60, Z_RAIL + LUG["t"]), -40, f"{mmi(LUG['t'])}", "v")
    F.dim((LUG["x"][0] + 60, Z_AX), (LUG["x"][0] + 60, Z_RAIL), -30, f"LUG SEAT {mmi(Z_RAIL - Z_AX)} ABOVE AXIS", "v")
    F.leader((PROBE["x"] + 18, PROBE["z"] - 18), (-140, Z_AX - 60), ["1-1/2 in TC FERRULE (item 7), level switch P1-337", "hole Ø38.6 [1.520] in the front wall"])
    F.leader((TC4_FER_OD / 2, Z_TB - TC4_FER_L + 2), (150, Z_TB - 160), ["4 in TC FERRULE (item 6) on Ø98.3 [3.870] hole", "valve P1-331 hangs here"])
    F.tag(-570, Z_TB + 30, 1, (-440, Z_TB + 60)); F.tag(-570, Z_AX - 150, 2, (-454, Z_AX - 200)); F.tag(-560, Z_AX + 80, 4, (-475, Z_AX + 50))
    F.tag(110, Z_TB - 60, 6, (45, Z_TB - 15)); F.tag(-380, PROBE["z"] - 60, 7, (PROBE["x"] - 18, PROBE["z"] - 18))
    # welds (front view)
    F.weld((-L_IN / 2, Z_AX - 200), (-420, Z_TB - 110), "fillet", "3", other="fillet", tail="W1 inside: R3 cove")
    F.weld((L_IN / 2 + T_EP, Z_AX + 75), (680, Z_AX + 150), "fillet", "6", allround=True, tail="W3 outside")
    F.weld((LUG["x"][1] + 5, Z_RAIL - 50), (380, Z_FLTOP + 90), "fillet", "4", other="fillet", tail="W5 lugs")
    F.weld((-FL_OUT_X / 2 + 60, Z_AX + H_SIDE), (-400, Z_FLTOP + 90), "fillet", "3", length="25-150", tail="W2 outside")

    # ---------- end view (y, z) from the drive end: screen right = +y (back)
    E = S.view(1840, 1170 + Z_AX * s5, s5, "END VIEW (from the drive end)  1:5", (1560, 905))
    E.poly(u_outline(R_EP, H_SIDE))
    E.poly(u_outline(R_O, H_SIDE), "hid", False)
    E.rect(-FL_OUT_Y / 2, Z_AX + H_SIDE, FL_OUT_Y, T_FL)
    E.circle(0, Z_AX, BOX["od"] / 2); E.circle(0, Z_AX, BOX["bore"] / 2, "thin"); E.circle(0, Z_AX, BOX["throat"] / 2, "thin")
    for k in range(4):
        a = math.radians(45 + 90 * k); E.circle(BOX["pcd"] / 2 * math.cos(a), Z_AX + BOX["pcd"] / 2 * math.sin(a), 4.25)
    for sy in (-1, 1):
        E.poly([(sy * R_O, Z_RAIL + LUG["t"]), (sy * 430, Z_RAIL + LUG["t"]), (sy * 430, Z_RAIL), (sy * 355, Z_RAIL), (sy * 355, Z_RAIL - 20), (sy * R_O, Z_RAIL - 100)])
    E.rect(-TC4_FER_OD / 2, Z_TB - TC4_FER_L, TC4_FER_OD, 4); E.rect(-TC4_OD / 2, Z_TB - TC4_FER_L + 4, TC4_OD, TC4_FER_L - 4 - 3)
    E.rect(-R_O - 21.5, PROBE["z"] - 19, 21.5, 38)
    E.centre(-470, Z_AX, 470, Z_AX); E.centre(0, Z_TB - 60, 0, Z_FLTOP + 40)
    E.dim((-R_EP, Z_AX - 30), (R_EP, Z_AX - 30), -300 * s5 - 60, f"END PLATE {mmi(2 * R_EP)}", "h")
    E.dim((-430, Z_RAIL + LUG["t"]), (430, Z_RAIL + LUG["t"]), 95, f"LUG TIPS {mmi(860)}", "h")
    E.dim((-FL_OUT_Y / 2, Z_FLTOP), (FL_OUT_Y / 2, Z_FLTOP), 40, f"{mmi(FL_OUT_Y)}", "h")
    E.rad(0, Z_AX, R_EP, -40, (380, Z_AX - 330), f"R{mmi(R_EP)} END PLATE (15 [.59] proud of the shell)")
    E.rad(0, Z_AX, R_O, -130, (-430, Z_AX - 340), f"R{mmi(R_IN)} INSIDE, 3 [.118] SHELL")
    E.dim((-Y_LEG, Z_RAIL + LUG["t"]), (Y_LEG, Z_RAIL + LUG["t"]), 45, f"LUG HOLES Ø14 AT {mmi(2 * Y_LEG)}", "h")
    E.leader((BOX["pcd"] / 2 * 0.7071, Z_AX - BOX["pcd"] / 2 * 0.7071), (150, Z_AX - 150), ["4 x M10 x 20 DEEP on PCD 115 [4.528], 45°"])
    E.tag(-470, Z_AX + 120, 2, (-R_EP + 5, Z_AX + 100)); E.tag(470, Z_RAIL + 70, 5, (430, Z_RAIL + 5))

    # ---------- detail C: inside corner weld at the end plate (2:1)
    C = S.view(520, 1990, SC(0.5), "DETAIL C  SHELL TO END PLATE, TYPICAL ALL ROUND  2:1", (120, 1700))
    C.hatch([(-45, 0), (0, 0), (0, 3), (-45, 3)], "hA")
    C.hatch([(0, -18), (8, -18), (8, 40), (0, 40)], "hB")
    C.poly([(-3, 3), (0, 3), (0, 6)], "vis", True, "#444")
    C.poly([(0, -3), (-3, 0), (0, 0)], "vis", True, "#444")
    C.note(-44, 28, ["PRODUCT SIDE"], 13)
    C.note(-44, -12, ["OUTSIDE"], 13)
    C.leader((-1.5, 4.5), (20, 30), ["INSIDE: fillet 3 [.12] continuous, ground", "to R3 [.12] cove, no undercut, #4"])
    C.leader((-1.5, -1.5), (20, -12), ["OUTSIDE: fillet 3 [.12] continuous"])
    C.dim((0, 40), (8, 40), 20, "8 [.315]", "h"); C.dim((-45, 0), (-45, 3), 20, "3", "v")
    C.dim((0, -18), (0, 0), -20, "15 [.59] land", "v")

    # ---------- tables
    items = [(1, "P1-301-101", "Shell, U formed (sheet P1-301-101)", 1, "3 [.118] 316L, 1472.4 x 900", kg("P1-301-101")),
             (2, "P1-301-102", "End plate, drive end (sheet P1-301-102)", 1, "8 [.315] 316L laser", kg("P1-301-102")),
             (9, "P1-301-108", "Shell end ring, free end (sheet P1-301-108)", 1, "8 [.315] 316L laser", kg("P1-301-108")),
             (3, "P1-301-103", "Top flange frame (sheet P1-301-102)", 1, "6 [.236] 316L laser", kg("P1-301-103")),
             (4, "P1-301-104", "Stuffing box (sheet P1-301-104)", 2, "Ø160 316L bar", kg("P1-301-104")),
             (5, "P1-301-105", "Lug: seat + gusset (sheet P1-301-102)", 4, "10 [.394] 316L laser", kg("P1-301-105")),
             (6, "P1-301-106", "4 in BPE short weld ferrule 14WMP", 1, "bought 316L", kg("P1-301-106")),
             (7, "P1-301-107", "1-1/2 in BPE short weld ferrule 14WMP", 1, "bought 316L", kg("P1-301-107")),
             (8, "P1-301-109", "Hinge knuckle Ø20 x 38, bore Ø10.2", 2, "316 bar (sheet P1-301-300)", "0.1 kg")]
    S.table(2140, 140, [("ITEM", 50), ("PART NO.", 120), ("DESCRIPTION", 400), ("QTY", 45), ("STOCK", 270), ("MASS", 170)], items, "ITEM LIST", 14, 25)
    welds = [("W1", "Shell to end plates", "fillet 3 both sides, continuous", "inside ground to R3 cove"),
             ("W2", "Shell + end plates to flange", "inside fillet 3 continuous; outside 3, 25 @ 150", "inside ground flush to the wall"),
             ("W3", "Box spigot to end plate", "fillet 6 all round outside; inside fillet 3", "inside ground flush, R3"),
             ("W4", "Ferrules to shell", "full penetration, purged", "inside ground flush, no ledge"),
             ("W5", "Lug gusset + seat to shell", "fillet 4 both sides", "outside only; seat flat after weld 0.5"),
             ("W6", "Hinge knuckles to flange (back)", "fillet 4 both sides", "jig: both pins on one axis 0.3")]
    S.table(2140, 420, [("WELD", 60), ("JOINT", 330), ("SIZE", 400), ("FINISH / CHECK", 265)], welds, "WELD SCHEDULE (GTAW, ER316L, argon; AWS D1.6)", 14, 25)
    S.notes(2140, 640, 1055, [
        "FREE END IS BOLTED: the ring (item 9) is welded to the shell; the free-end plate P1-301-110 with its stuffing box (phantom here) bolts on with gasket P1-301-111 and 15 x H13. The agitator slides in from the free end (P1-301-003 step 4).",
        "Weld sequence: (1) bolt the free-end plate to the ring with the gasket, tack the shell into the drive end plate and the ring on a flat table with the alignment bar Ø63.8 x 1100 through both stuffing-box throats; (2) tack the boxes, check bar turns free; (3) weld W1 and W3 in short balanced runs, inside first; (4) fit flange, check flat 1.5 [.06], weld W2; (5) lugs and ferrules last.",
        "Box faces must be parallel and square to the bar within 0.2 [.008] and concentric to it within 0.25 [.010] after welding. If not, face and bore the boxes in place on a boring bar before passivating.",
        "Flange top flat within 1.5 [.06] over the full frame; no weld spatter on the gasket land.",
        "All inside welds ground flush, blended, no pits, cracks or crevices. Inside surface #4, Ra ≤ 0.8 µm [32 µin]. Passivate the finished weldment to ASTM A967 (citric).",
        "Lug seats bear on the frame rails: grind the four seats coplanar within 1 [.04] with the trough on its flange (upside down) on the table.",
        "Inspect per P1-301-900 items T1..T6 before passivation. Mark part no. and heat no. on the outside of an end plate (vibro-etch).",
    ], fs=14)
    S.save(DWG / "P1-301-100_trough.svg")


# ================================================================== 101 shell flat pattern
def shell_flat():
    S = sheet("P1-301-101", "SHELL FLAT PATTERN AND FORMING", scale="1:5, 1:10", material="SS 316L sheet 3 [.118] (11 ga), ASTM A240, 2B, PVC-coated one side",
              finish="Inside (coated side) #4 after forming", mass=kg("P1-301-101"))
    v = S.view(220, 980, s5, "FLAT PATTERN  1:5  (coated side up = product side; dimensions on the neutral line, K 0.5)", (120, 120))
    W_, Hh = DEV_W, L_IN
    # developed: u (sheet x) across the width 0..1472.4 from the FRONT top edge, w (sheet y) along the trough length 0..900 from the free end
    v.rect(0, 0, W_, Hh)
    v.line(H_SIDE, -20, H_SIDE, Hh + 20, "bend"); v.line(H_SIDE + ARC, -20, H_SIDE + ARC, Hh + 20, "bend")
    v.circle(W_ / 2, Hh / 2, 98.3 / 2); v.cmark(W_ / 2, Hh / 2, 49)
    pu = H_SIDE - (PROBE["z"] - Z_AX); pw = PROBE["x"] + L_IN / 2
    v.circle(pu, pw, PROBE["d"] / 2); v.cmark(pu, pw, 20)
    v.dim((0, Hh), (W_, Hh), 70, f"{mmi(W_, 1)}  (= 294 + 884.4 + 294)", "h")
    v.dim((0, 0), (H_SIDE, 0), -50, f"{mmi(H_SIDE)}", "h"); v.dim((H_SIDE, 0), (H_SIDE + ARC, 0), -50, f"ROLLED ZONE {mmi(ARC, 1)} = π x 281.5", "h")
    v.dim((H_SIDE + ARC, 0), (W_, 0), -50, f"{mmi(H_SIDE)}", "h")
    v.dim((0, 0), (W_ / 2, 0), -110, f"{mmi(W_ / 2, 1)}", "h")
    v.dim((W_, 0), (W_, Hh), -60, f"{mmi(Hh)} (trough length, grain this way)", "v")
    v.dim((W_ / 2 + 120, 0), (W_ / 2 + 120, Hh / 2), 0, f"{mmi(Hh / 2)}", "v", ext=False)
    v.dim((0, pw), (pu, pw), 30, f"{mmi(pu)}", "h"); v.dim((pu + 40, 0), (pu + 40, pw), 0, f"{mmi(pw)}", "v", ext=False)
    v.leader((W_ / 2 + 35, Hh / 2 + 35), (W_ / 2 + 160, Hh / 2 + 200), ["Ø98.3 [3.870] (4 in tube ID) for ferrule item 6", "cut AFTER forming (laser the pilot Ø20 only)"])
    v.leader((pu + 14, pw + 14), (pu + 140, pw + 160), ["Ø38.6 [1.520] for 1-1/2 in ferrule item 7"])
    v.note(H_SIDE + 8, Hh + 25, ["BEND LINE (start of R)"], 12, "start", "#b00020")
    v.note(20, -200, ["FRONT top edge (y-)", "welds to flange"], 13)
    v.note(W_ - 20, -200, ["BACK top edge (y+)", "welds to flange"], 13, "end")
    ms.dxf_profile(str(DXF / "P1-301-101_shell_flat"), [(0, 0), (W_, 0), (W_, Hh), (0, Hh)], holes=[(W_ / 2, Hh / 2, 10), (pu, pw, PROBE["d"] / 2)],
                   bends=[((H_SIDE, 0), (H_SIDE, Hh)), ((H_SIDE + ARC, 0), (H_SIDE + ARC, Hh))], text="P1-301-101 3mm 316L - pilot hole only at the 4in port")
    # forming end view 1:10
    s10 = SC(10)
    f = S.view(2650, 640, s10, "FORMED SHAPE  1:10  (end view)", (2300, 120))
    f.poly(u_outline(R_O, H_SIDE, 0, 0)); f.poly(u_outline(R_IN, H_SIDE, 0, 0), "thin", False)
    f.dim((-R_O, H_SIDE), (R_O, H_SIDE), 30, f"OUTSIDE {mmi(2 * R_O)} +1/-0", "h")
    f.dim((R_O, 0), (R_O, H_SIDE), -30, f"{mmi(H_SIDE)}", "v")
    f.rad(0, 0, R_IN, -60, (300, -330), f"R{mmi(R_IN)} INSIDE ±1")
    f.centre(-320, 0, 320, 0); f.centre(0, -320, 0, 330)
    # template
    t = S.view(2650, 1000, s10, "CHECK TEMPLATE  1:10  (3 mm plate or 6 mm ply, cut from the DXF)", (2300, 860))
    t.arc(0, 0, R_IN, 180, 360); t.line(-R_IN, 0, -R_IN - 60, 0); t.line(R_IN, 0, R_IN + 60, 0)
    t.poly([(-R_IN - 60, 0), (-R_IN - 60, -R_IN - 60), (R_IN + 60, -R_IN - 60), (R_IN + 60, 0)], "thin", False)
    t.note(0, -R_IN - 30, ["gap ≤ 1 [.04] anywhere"], 13, "middle")
    ang = [(math.cos(math.radians(a)) * R_IN, math.sin(math.radians(a)) * R_IN) for a in range(180, 361, 3)]
    ms.dxf_profile(str(DXF / "P1-301-101_template_R280"), [(-R_IN - 60, 0)] + ang + [(R_IN + 60, 0), (R_IN + 60, -R_IN - 60), (-R_IN - 60, -R_IN - 60)], text="P1-301-101 template R280")
    S.notes(120, 1420, 1500, [
        "Blank: laser from 1524 x 3048 [60 x 120] 3 mm 316L 2B PVC-coated sheet; 1472.4 runs across the 1524 width, the 900 along the length. Remove burrs; keep the PVC on through forming.",
        "Form the 884.4 [34.82] centre zone to R280 inside on plate rolls with pre-bent ends, OR by bump forming on the press brake: 74 hits at 12 [.47] pitch, 2.4° each, with a radius punch R≤ 100 and a 50 V-die. Leave the two 294 [11.57] flats straight (no flat spot or kink at the bend lines).",
        "Check with the template every 150 [6] along the length: gap ≤ 1 [.04]. Outside width at the top 566 +1/-0 before welding; spring back is taken out by the end plates.",
        "Cut the 4 in port Ø98.3 after forming (pilot Ø20 in the blank), deburr inside to a sharp, clean edge for the ferrule weld.",
        "Ends must be square to the axis within 0.5 [.02] across 566 so the shell seats flat on the end plates: trim after forming if needed.",
    ], fs=14)
    S.table(120, 1250, [("FILE", 380), ("CONTENTS", 520), ("UNITS", 140)],
            [("P1-301-101_shell_flat_mm.dxf / _in.dxf", "blank, pilot Ø20, probe hole, 2 bend lines (layer BEND)", "mm / in"),
             ("P1-301-101_template_R280_mm.dxf / _in.dxf", "R280 check template", "mm / in")], "CUT FILES", 14, 25)
    S.save(DWG / "P1-301-101_shell_flat.svg")


# ================================================================== 102 plates
def endplate_pts():
    r = R_EP
    pts = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in [180 + i * 3 for i in range(61)]]
    return [(-r, H_SIDE)] + pts + [(r, H_SIDE)]


def plates():
    S = sheet("P1-301-102", "END PLATE, TOP FLANGE, LUG", scale="1:5, 1:2", material="SS 316L plate (ASTM A240): 8, 6 and 10 [.315, .236, .394]",
              finish="Laser cut, deburr; product side #4", mass=kg("P1-301-102", "P1-301-103", "P1-301-105"))
    # ---- end plate (y, z about the axis), 2 off: drive end and free end are the same
    e = S.view(480, 700, s4, "P1-301-102  END PLATE, DRIVE END (welded)  8 [.315] 316L  QTY 1  1:4", (120, 120))
    e.poly(endplate_pts())
    e.circle(0, 0, 50.0); e.cmark(0, 0, 50)
    e.poly(u_outline(R_O, H_SIDE, 0, 0), "phan", False)
    e.dim((-R_EP, H_SIDE), (R_EP, H_SIDE), 40, f"{mmi(2 * R_EP)}", "h")
    e.dim((R_EP, 0), (R_EP, H_SIDE), -40, f"{mmi(H_SIDE)}", "v")
    e.dim((R_EP, -R_EP), (R_EP, 0), -40, f"{mmi(R_EP)}", "v")
    e.dim((-R_EP, -R_EP), (-R_EP, H_SIDE), 60, f"OVERALL {mmi(R_EP + H_SIDE)}", "v")
    e.rad(0, 0, R_EP, -50, (260, -340), f"R{mmi(R_EP)}")
    e.dia(0, 0, 50, 45, (150, 150), "Ø100 H9 [3.9370/3.9404] (+0.087/0)", None)
    e.note(0, -R_O + 20, ["phantom: shell outside R283 (15 [.59] land all round)"], 12, "middle", "#607d8b")
    e.note(-R_EP + 10, H_SIDE - 25, ["TOP EDGE: under the flange"], 12)
    e.text(0, -150, "ETCH P1-301-102 OUTSIDE", 12, color="#607d8b")
    ms.dxf_profile(str(DXF / "P1-301-102_endplate"), endplate_pts(), holes=[(0, 0, 49.5)], text="P1-301-102 8mm 316L x1 drive end - bore hole to Ø100 H9")
    S.text(120, 1210, "Laser the centre hole to Ø99 [3.898], then bore to Ø100 H9 so the stuffing-box spigot (f8) is a slide fit.", 13)

    # ---- flange frame (x, y)
    f = S.view(1700, 520, s5, "P1-301-103  TOP FLANGE FRAME  6 [.236] 316L  QTY 1  1:5", (1180, 120))
    f.rect(-FL_OUT_X / 2, -FL_OUT_Y / 2, FL_OUT_X, FL_OUT_Y); f.rect(-L_IN / 2, -W_IN / 2, L_IN, W_IN)
    f.centre(-540, 0, 540, 0); f.centre(0, -360, 0, 360)
    f.dim((-FL_OUT_X / 2, FL_OUT_Y / 2), (FL_OUT_X / 2, FL_OUT_Y / 2), 40, f"{mmi(FL_OUT_X)}", "h")
    f.dim((-L_IN / 2, -W_IN / 2), (L_IN / 2, -W_IN / 2), -80, f"CUTOUT {mmi(L_IN)} +1/-0", "h")
    f.dim((FL_OUT_X / 2, -FL_OUT_Y / 2), (FL_OUT_X / 2, FL_OUT_Y / 2), -40, f"{mmi(FL_OUT_Y)}", "v")
    f.dim((-L_IN / 2, -W_IN / 2), (-L_IN / 2, W_IN / 2), -40, f"CUTOUT {mmi(W_IN)} +1/-0", "v")
    f.dim((-FL_OUT_X / 2, 0), (-L_IN / 2, 0), 0, f"{mmi(50)}", "h", ext=False)
    f.dim((250, W_IN / 2), (250, FL_OUT_Y / 2), 0, f"{mmi(43)}", "v", ext=False)
    f.note(0, -FL_OUT_Y / 2 - 75, ["inside corners sharp (cutout matches the shell and end plates); outside corners R5"], 12, "middle")
    f.note(-FL_OUT_X / 2, FL_OUT_Y / 2 + 110, ["BACK (hinge side) up"], 12)
    flp = [(-FL_OUT_X / 2, -FL_OUT_Y / 2), (FL_OUT_X / 2, -FL_OUT_Y / 2), (FL_OUT_X / 2, FL_OUT_Y / 2), (-FL_OUT_X / 2, FL_OUT_Y / 2)]
    cut = [(-L_IN / 2, -W_IN / 2), (L_IN / 2, -W_IN / 2), (L_IN / 2, W_IN / 2), (-L_IN / 2, W_IN / 2)]
    ms.dxf_profile(str(DXF / "P1-301-103_flange"), [flp, cut], text="P1-301-103 6mm 316L x1")
    S.text(1180, 920, "Laser one piece (no joints). Latch keepers and interlock bracket holes are drilled on assembly (P1-301-003 step 9).", 13)

    # ---- lug seat and gusset (1:2)
    l = S.view(500, 1700, s2, "P1-301-105  LUG SEAT  10 [.394] 316L  QTY 4  1:2", (120, 1330))
    l.rect(0, 0, 147, LUG["w"]); l.circle(Y_LEG - Y_LUG0, LUG["w"] / 2, 7); l.cmark(Y_LEG - Y_LUG0, LUG["w"] / 2, 7)
    l.dim((0, LUG["w"]), (147, LUG["w"]), 30, f"{mmi(147)}", "h"); l.dim((147, 0), (147, LUG["w"]), -30, f"{mmi(LUG['w'])}", "v")
    l.dim((0, LUG["w"] / 2), (Y_LEG - Y_LUG0, LUG["w"] / 2), 0, f"{mmi(Y_LEG - Y_LUG0)}", "h", ext=False)
    l.dia(Y_LEG - Y_LUG0, LUG["w"] / 2, 7, -45, (180, -40), "Ø14 [.551] for M12 (H3)")
    l.note(0, -20, ["shell end (y = 283): weld edge, cope to R283 if the seat sits low"], 12)
    ms.dxf_profile(str(DXF / "P1-301-105_lug_seat"), [(0, 0), (147, 0), (147, LUG["w"]), (0, LUG["w"])], holes=[(Y_LEG - Y_LUG0, LUG["w"] / 2, 7)], text="P1-301-105 seat 10mm 316L x4")
    g = S.view(1200, 1820, s2, "P1-301-105  LUG GUSSET  10 [.394] 316L  QTY 4  1:2", (1000, 1330))
    gp = [(0, 100), (72, 100), (72, 80), (0, 0)]
    g.poly(gp)
    g.dim((0, 100), (72, 100), 30, f"{mmi(72)}", "h"); g.dim((72, 80), (72, 100), -30, "20", "v")
    g.dim((0, 0), (0, 100), 30, f"{mmi(100)}", "v")
    g.note(5, -25, ["edge at y = 283: fits the shell side wall (flat zone)"], 12)
    ms.dxf_profile(str(DXF / "P1-301-105_lug_gusset"), gp, text="P1-301-105 gusset 10mm 316L x4")
    S.notes(2140, 1330, 1060, [
        "Lugs: gusset centred under the seat, square to the shell; seat top at 100 [3.94] above the shaft axis (P1-301-100). The gusset stops 7 [.28] short of the rail so the seat sits flat and the M12 clears it.",
        "All plates: laser to the DXF (mm or inch files identical), remove dross, break edges 0.5. Keep PVC on product sides until welding.",
        "Stock: end plates and lugs from one 1219 x 2438 [48 x 96] plate each thickness; the flange from 1219 x 2438 x 6.",
    ], fs=14)
    S.table(2140, 1610, [("FILE", 400), ("PART", 340), ("QTY", 60)],
            [("P1-301-102_endplate_mm/_in.dxf", "end plate 8 mm, drive end", 1), ("P1-301-103_flange_mm/_in.dxf", "flange frame 6 mm", 1),
             ("P1-301-105_lug_seat_mm/_in.dxf", "lug seat 10 mm", 4), ("P1-301-105_lug_gusset_mm/_in.dxf", "lug gusset 10 mm", 4)], "CUT FILES", 14, 25)
    S.save(DWG / "P1-301-102_plates.svg")


# ================================================================== 108 free-end ring, bolted plate 110, gasket 111
def u_pts(r, top=H_SIDE, n=60):
    return [(-r, top)] + [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in [180 + 180 * i / n for i in range(n + 1)]] + [(r, top)]


def free_end():
    S = sheet("P1-301-108", "FREE END: SHELL RING, BOLTED END PLATE, GASKET", scale="1:4, 1:1", material="SS 316L plate 8 [.315]; gasket FDA silicone 3 [.118]",
              finish="Ring face and plate land flat 0.2 [.008], Ra 1.6; product side #4", mass=kg("P1-301-108") + " ring")
    rr, rb = RING["r_out"], RING["r_bolt"]
    bolts = D.ring_bolts()
    # ring
    g = S.view(240 + rr * s4 + 40, 200 + (rr + H_SIDE) * s4 - (rr) * s4 + H_SIDE * s4 * 0 + 60 + rr * s4 * 0, s4, "P1-301-108  SHELL END RING  8 [.315] 316L  QTY 1  1:4", (120, 120))
    g.oy = 200 + H_SIDE * s4 + 30
    g.poly(u_pts(rr)); g.poly(u_pts(R_O), "vis", False); g.line(-rr, H_SIDE, -R_O, H_SIDE); g.line(rr, H_SIDE, R_O, H_SIDE)
    for y, z in bolts:
        g.circle(y, z, RING["hole"] / 2)
    g.cmark(0, 0, 30)
    g.dim((-rr, H_SIDE), (rr, H_SIDE), 40, f"{mmi(2 * rr)}", "h"); g.dim((-R_O, H_SIDE), (R_O, H_SIDE), 15, f"{mmi(2 * R_O)} (shell OD)", "h")
    g.rad(0, 0, rr, -60, (260, -380), f"R{mmi(rr)}"); g.rad(0, 0, R_O, -120, (-200, -400), f"R{mmi(R_O)} fits the shell outside")
    g.leader((bolts[4][0] + 4, bolts[4][1] - 4), (60, -200), [f"15 x Ø{RING['hole']:.0f} [{fin(RING['hole'])}] on R{rb:.0f} [{fin(rb)}]:", "9 at 22.5° on the radius, 3 up each side at 85 / 175 / 265 above the axis"])
    g.dim((rr, 0), (rr, H_SIDE), -40, f"{mmi(H_SIDE)}", "v")
    ms.dxf_profile(str(DXF / "P1-301-108_ring"), [u_pts(rr), list(reversed(u_pts(R_O)))], holes=[(y, z, RING["hole"] / 2) for y, z in bolts], text="P1-301-108 8mm 316L x1 (inner = shell OD)")
    # bolted plate
    p = S.view(1750, 200 + H_SIDE * s4 + 30, s4, "P1-301-110  FREE-END PLATE (bolted, carries stuffing box 104)  8 [.315] 316L  QTY 1  1:4", (1250, 120))
    p.poly(u_pts(rr))
    for y, z in bolts:
        p.circle(y, z, RING["hole"] / 2)
    p.circle(0, 0, 50); p.cmark(0, 0, 50); p.poly(u_pts(R_IN), "phan", False)
    p.dim((-rr, H_SIDE), (rr, H_SIDE), 40, f"{mmi(2 * rr)}", "h"); p.dim((rr, -rr), (rr, H_SIDE), -40, f"{mmi(rr + H_SIDE)}", "v")
    p.dia(0, 0, 50, 45, (150, 150), "Ø100 H9 [3.9370/3.9404] for the box spigot")
    p.note(0, -R_IN + 30, ["phantom: product edge R280 (gasket inside edge)"], 12, "middle", "#607d8b")
    p.text(0, -150, "2 x M10 jacking holes may be added at 3 and 9 o'clock", 12, color="#607d8b")
    ms.dxf_profile(str(DXF / "P1-301-110_free_end_plate"), u_pts(rr), holes=[(0, 0, 49.5)] + [(y, z, RING["hole"] / 2) for y, z in bolts], text="P1-301-110 8mm 316L x1 - bore Ø100 H9")
    # gasket
    k = S.view(240 + rr * s4 + 40, 1250 + H_SIDE * s4, s4, "P1-301-111  END GASKET  FDA SILICONE 3 [.118]  QTY 1 (+1 spare)  1:4", (120, 1150))
    k.poly(u_pts(rr)); k.poly(u_pts(R_IN), "vis", False); k.line(-rr, H_SIDE, -R_IN, H_SIDE); k.line(rr, H_SIDE, R_IN, H_SIDE)
    for y, z in bolts:
        k.circle(y, z, RING["hole"] / 2)
    k.rad(0, 0, R_IN, -120, (-150, -400), f"R{mmi(R_IN)} INSIDE = product edge, flush ±0.5")
    ms.dxf_profile(str(DXF / "P1-301-111_end_gasket"), [u_pts(rr), list(reversed(u_pts(R_IN)))], holes=[(y, z, RING["hole"] / 2) for y, z in bolts], text="P1-301-111 3mm FDA silicone")
    # joint section 1:1
    j = S.view(1500, 1900, s1, "SECTION J  BOLTED JOINT AT THE FREE END  1:1", (1250, 1620))
    j.hatch([(-60, 0), (0, 0), (0, 3), (-60, 3)], "hA")                               # shell (x along, z radial)
    j.hatch([(-8, 3), (0, 3), (0, rr - R_O + 3), (-8, rr - R_O + 3)], "hB")            # ring
    j.hatch([(0, -3), (2.5, -3), (2.5, rr - R_O + 3), (0, rr - R_O + 3)], "hS", "thin")   # gasket (compressed 3 -> 2.5)
    j.hatch([(2.5, -40), (10.5, -40), (10.5, rr - R_O + 3), (2.5, rr - R_O + 3)], "hA")  # plate
    zb = rb - R_O
    j.rect(-8 - 9, zb - 5, 10.5 + 8 + 9 + 12, 10, "thin", "#fff"); j.rect(-8 - 9 - 8, zb - 8.5, 8, 17, "vis"); j.rect(10.5, zb - 8.5, 7, 17, "vis")
    j.note(-58, -14, ["PRODUCT SIDE (inside)"], 13)
    j.leader((1.2, -1.5), (30, -30), ["gasket inside edge flush with R280, no step > 0.3"])
    j.leader((-4, 10), (-60, 50), ["ring 108: fillet 4 all round to the shell outside,", "face machined flat after welding (0.2)"])
    j.leader((14, zb), (40, zb + 30), ["H13 M10 x 35 A4-70, 25 N·m"])
    j.dim((2.5, rr - R_O + 3), (10.5, rr - R_O + 3), 25, "8", "h"); j.dim((0, rr - R_O + 3), (2.5, rr - R_O + 3), 55, "2.5 compressed", "h")
    S.notes(2200, 1150, 1000, [
        "Why bolted: both shaft ends pass through the end plates and the ribbons run 15 [.59] from the plates, so a welded-both-ends trough could not take the agitator. With 110 off, the agitator slides in from the free end.",
        "Ring 108 is welded to the shell outside with its face flush with the shell end, then the face is skimmed flat (0.2) on the mill or with a flange facer.",
        "The free-end plate and its box (104) are welded as a sub-weldment (W3) before the trough weldment is aligned with the bar.",
        "Gasket: cut from 3 mm FDA silicone with the DXF; replace at every agitator removal. Torque H13 in a cross pattern 10 then 25 N·m.",
        "Dowel option: 2 x Ø8 dowels at 3 and 9 o'clock (ring + plate drilled together) to keep the box concentric after removal.",
    ], fs=13)
    S.table(2200, 1550, [("FILE", 380), ("QTY", 60)], [("P1-301-108_ring_mm/_in.dxf", 1), ("P1-301-110_free_end_plate_mm/_in.dxf", 1), ("P1-301-111_end_gasket_mm/_in.dxf", 1)], "CUT FILES", 13, 23)
    S.save(DWG / "P1-301-108_free_end.svg")


# ================================================================== 104 stuffing box + 501 follower (machined)
def machined():
    S = sheet("P1-301-104", "STUFFING BOX AND GLAND FOLLOWER", scale="1:1", material="SS 316L bar (ASTM A276), Ø160 [6.30] and Ø155 [6.10]",
              finish="Bore and spigots Ra 1.6 [63 µin]; rest Ra 3.2", mass=kg("P1-301-104") + " (2 boxes)", qty="2 + 2")
    v = S.view(520, 640, s1, "P1-301-104  STUFFING BOX  QTY 2  -  SECTION ON THE AXIS  1:1", (120, 120))
    # axial coordinate x from the spigot end (product side) 0 .. 58; radial r
    L1, L2 = BOX["spig_l"], BOX["x_face"]
    r_sp, r_od, r_th, r_bo = BOX["spig_d"] / 2, BOX["od"] / 2, BOX["throat"] / 2, BOX["bore"] / 2
    for sg in (1, -1):
        v.hatch([(0, sg * r_th), (0, sg * r_sp), (L1, sg * r_sp), (L1, sg * r_od), (L2, sg * r_od), (L2, sg * r_bo), (10, sg * r_bo), (10, sg * r_th)], "hA")
        q = BOX["pcd"] / 2
        v.rect(L2 - 20, sg * q - 4.25, 20, 8.5, "thin", "#fff"); v.line(L2 - 20, sg * q - 5, L2, sg * q - 5, "thin"); v.line(L2 - 20, sg * q + 5, L2, sg * q + 5, "thin")
    v.centre(-20, 0, L2 + 20, 0)
    v.dim((0, r_sp), (L1, r_sp), 30, "8 [.315]", "h"); v.dim((0, r_od), (L2, r_od), 50, f"{mmi(L2)} ±0.1", "h")
    v.dim((10, r_bo), (L2, r_bo), 20, f"BORE DEPTH {mmi(L2 - 10)}", "h")
    v.dim((0, -r_sp), (0, r_sp), 60, "Ø100 f8 [3.9386/3.9365]", "v")
    v.dim((L2, -r_od), (L2, r_od), -70, "Ø150 [5.906]", "v")
    v.dim((L2 - 5, -r_bo), (L2 - 5, r_bo), -20, "Ø80 H8 [3.1496/3.1514]", "v")
    v.dim((5, -r_th), (5, r_th), -30, "Ø64 [2.520]", "v")
    v.leader((L2 - 10, BOX["pcd"] / 2 + 4), (L2 + 60, 110), ["4 x M10 - 6H, 20 [.79] full thread,", "drill Ø8.5 x 25, on PCD 115 [4.528] at 45°"])
    v.leader((10, -r_bo), (-60, -110), ["bore bottom: flat, R0.5 corner,", "packing seats here"])
    v.leader((0, r_th + 5), (-60, 100), ["C1 x 45° throat entry (product side)"])
    v.finish((L2 - 25, r_bo), "1.6"); v.finish((4, r_sp), "1.6")
    v.datum((0, -r_sp - 18), "A", (0, -1))
    v.fcf(20, -112, ["◎", "Ø0.05", "A"]); v.note(62, -114, ["Ø80 bore to spigot A"], 13)
    v.fcf(20, -128, ["⊥", "0.05", "A"]); v.note(62, -130, ["packing face to spigot A"], 13)
    # end view of the box
    e = S.view(1260, 640, s1, "VIEW ON THE PACKING FACE  1:1", (1000, 120))
    e.circle(0, 0, r_od); e.circle(0, 0, r_bo); e.circle(0, 0, r_th, "hid")
    e.circle(0, 0, BOX["pcd"] / 2, "cen")
    for k in range(4):
        a = math.radians(45 + 90 * k); e.circle(BOX["pcd"] / 2 * math.cos(a), BOX["pcd"] / 2 * math.sin(a), 5); e.circle(BOX["pcd"] / 2 * math.cos(a), BOX["pcd"] / 2 * math.sin(a), 4.25, "thin")
    e.cmark(0, 0, r_od)
    e.angle((0, 0), 30, 0, 45, "45°")
    # follower
    L3, L4 = FOLLOW["spig_l"], FOLLOW["spig_l"] + FOLLOW["t"]
    f = S.view(520, 1580, s1, "P1-301-501  GLAND FOLLOWER  QTY 2  -  SECTION  1:1", (120, 1240))
    for sg in (1, -1):
        f.hatch([(0, sg * FOLLOW["bore"] / 2), (0, sg * FOLLOW["spig_d"] / 2), (L3, sg * FOLLOW["spig_d"] / 2), (L3, sg * FOLLOW["od"] / 2), (L4, sg * FOLLOW["od"] / 2), (L4, sg * FOLLOW["bore"] / 2)], "hA")
        f.rect(L3, sg * BOX["pcd"] / 2 - 5.5, FOLLOW["t"], 11, "thin", "#fff")
    f.centre(-20, 0, L4 + 20, 0)
    f.dim((0, FOLLOW["spig_d"] / 2), (L3, FOLLOW["spig_d"] / 2), 25, "18 [.709]", "h"); f.dim((L3, FOLLOW["od"] / 2), (L4, FOLLOW["od"] / 2), 30, "12 [.472]", "h")
    f.dim((0, -FOLLOW["spig_d"] / 2), (0, FOLLOW["spig_d"] / 2), 50, "Ø80 f8 [3.1484/3.1466]", "v")
    f.dim((L4, -FOLLOW["od"] / 2), (L4, FOLLOW["od"] / 2), -60, "Ø150 [5.906]", "v")
    f.dim((L4 - 4, -FOLLOW["bore"] / 2), (L4 - 4, FOLLOW["bore"] / 2), -20, "Ø62 [2.441] +0.2/0", "v")
    f.leader((L3 + 6, BOX["pcd"] / 2 + 5.5), (L4 + 60, 40), ["4 x Ø11 [.433] THRU on PCD 115 [4.528] at 45°", "(match the box studs)"])
    f.leader((0, FOLLOW["bore"] / 2 + 3), (-60, 60), ["C0.5 both ends of the bore"])
    f.finish((8, FOLLOW["spig_d"] / 2), "1.6")
    g = S.view(1260, 1580, s1, "FOLLOWER: VIEW ON THE FLANGE  1:1", (1000, 1240))
    g.circle(0, 0, FOLLOW["od"] / 2); g.circle(0, 0, FOLLOW["bore"] / 2); g.circle(0, 0, BOX["pcd"] / 2, "cen")
    for k in range(4):
        a = math.radians(45 + 90 * k); g.circle(BOX["pcd"] / 2 * math.cos(a), BOX["pcd"] / 2 * math.sin(a), 5.5)
    g.cmark(0, 0, FOLLOW["od"] / 2)
    # tables / notes
    S.table(1700, 140, [("FEATURE", 300), ("SIZE", 220), ("LIMITS mm", 230), ("LIMITS in", 230)], [
        ("Box spigot", "Ø100 f8", "99.964 / 99.910", "3.9356 / 3.9335"),
        ("End plate hole (102)", "Ø100 H9", "100.087 / 100.000", "3.9404 / 3.9370"),
        ("Box packing bore", "Ø80 H8", "80.046 / 80.000", "3.1514 / 3.1496"),
        ("Follower spigot", "Ø80 f8", "79.970 / 79.924", "3.1484 / 3.1466"),
        ("Shaft at the box (201)", "Ø60 h7", "60.000 / 59.970", "2.3622 / 2.3610"),
        ("Packing cross-section", "10 sq", "(80 - 60) / 2 = 10", ".394"),
    ], "LIMITS OF SIZE", 14, 25)
    S.notes(1700, 360, 1000, [
        "Box: saw Ø160 bar to 62, face, turn OD Ø150 and spigot Ø100 f8 in one setting with the bore Ø80 H8 and throat Ø64 so the spigot (datum A) and bore run true within 0.05.",
        "Drill and tap 4 x M10 on PCD 115 at 45° to the vertical (two studs above, two below the shaft when fitted). Use a drill jig or the mill DRO.",
        "Follower: saw Ø155 bar to 34, turn spigot Ø80 f8 and bore Ø62 in one setting. 4 x Ø11 on PCD 115.",
        "Mark part no. on the Ø150 OD. Fit-check: follower slides into the box bore by hand with no shake; spigot slides into the end plate hole.",
        "No sharp edges in the throat (product side): C1 and polish Ra 0.8.",
    ], fs=14)
    S.table(1700, 760, [("PART", 200), ("STOCK", 300), ("OPS", 480)], [
        ("P1-301-104 x2", "Ø160 x 62 316L bar", "lathe 1 setting + flip face, mill/drill PCD, tap"),
        ("P1-301-501 x2", "Ø155 x 34 316L bar", "lathe 1 setting + flip face, drill PCD"),
    ], "STOCK AND OPERATIONS", 14, 25)
    S.save(DWG / "P1-301-104_box_follower.svg")


if __name__ == "__main__":
    weldment(); shell_flat(); plates(); free_end(); machined()
