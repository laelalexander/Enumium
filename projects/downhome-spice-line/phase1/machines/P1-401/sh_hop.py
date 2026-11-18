"""P1-401-400 hopper weldment + lid + flap (316L), -500 agitator weldment (316L)."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
from mechsheet import dxf_profile
from sh_parts import P, circ, arc_pts, rect_pts, rr, SS, BLU, WELD_316, R_O, R_RIM, BD

# cone development on the mean surface
R1m, R2m = HOP["r"] + T14 / 2, HOP["r_lo"] + T14 / 2
SLANT = math.hypot(HOP["h_cone"], R1m - R2m)
DEV_RO = R1m * SLANT / (R1m - R2m)
DEV_RI = DEV_RO - SLANT
DEV_ANG = 360 * R1m / DEV_RO
L_CYL = math.pi * (2 * HOP["r"] + T14)
CONE_ANG = math.degrees(math.atan(HOP["h_cone"] / (HOP["r"] - HOP["r_lo"])))
# agitator
TH = math.atan((HOP["r"] - HOP["r_lo"]) / HOP["h_cone"])
RW = HOP["r"] - AGIT["clear"]
SC_Z0, SC_Z1 = AGIT["z_cone_end"], Z_CYL0
SC_R0 = HOP["r_lo"] + (HOP["r"] - HOP["r_lo"]) * (SC_Z0 - Z_CONE0) / HOP["h_cone"] - AGIT["clear"] / math.cos(TH)
SC_L = math.hypot(RW - SC_R0, SC_Z1 - SC_Z0)
SC_A = math.degrees(math.atan2(SC_Z1 - SC_Z0, RW - SC_R0))
ARM_L = AGIT["r_tip"] - AGIT["sleeve_od"] / 2 + 1
BLADE_L = AGIT["z_arm"] + AGIT["arm_t"] - Z_CYL0
SLV_L = Z_AGTC - 21.5 - AGIT["z_arm"]


def hopper():
    S = sheet("P1-401-400", "HOPPER WELDMENT 42 L, LID AND FLAP (PRODUCT CONTACT)", scale="1:3 · 1:4 · 1:6 · 1:8", material=SS316L + ", 14 ga (1.9) / 16 ga (1.5)",
              finish=FIN_PC, mass=kg(*[f"P1-401-40{i}" for i in range(1, 8)]))
    s4 = SC(3)
    v = S.view(700, 420 + (Z_RIM + LID["up"] + 20) * s4, s4, "SECTION ON Y = 0 (1:3), LID ON", (170, 250))
    for sg in (-1, 1):
        v.hatch([(sg * HOP["r_lo"], Z_CONE0), (sg * (HOP["r_lo"] + T14), Z_CONE0), (sg * R_O, Z_CYL0), (sg * HOP["r"], Z_CYL0)], "hC")
        v.hatch([(sg * HOP["r"], Z_CYL0), (sg * R_O, Z_CYL0), (sg * R_O, Z_RIM), (sg * HOP["r"], Z_RIM)], "hC")
        v.hatch([(sg * R_O, Z_RIM - RIM["t"]), (sg * R_RIM, Z_RIM - RIM["t"]), (sg * R_RIM, Z_RIM), (sg * R_O, Z_RIM)], "hA")
        v.hatch([(sg * R_O, Z_RIM - RIM["w"]), (sg * (R_O + RIM["t"]), Z_RIM - RIM["w"]), (sg * (R_O + RIM["t"]), Z_RIM), (sg * R_O, Z_RIM)], "hA")
        v.hatch([(sg * TC25["id"] / 2, Z_TC), (sg * TC25["fl"] / 2, Z_TC), (sg * TC25["fl"] / 2, Z_TC + 6), (sg * TC25["od"] / 2, Z_TC + 6),
                 (sg * TC25["od"] / 2, Z_CONE0), (sg * TC25["id"] / 2, Z_CONE0)], "hC")
        v.hatch([(sg * LID["bore"] / 2, Z_RIM), (sg * R_RIM, Z_RIM), (sg * R_RIM, Z_RIM + LID["t"]), (sg * LID["bore"] / 2, Z_RIM + LID["t"])], "hC") if sg > 0 else None
        v.rect(min(sg * R_RIM, sg * (R_RIM + LID["t"])), Z_RIM - 15, LID["t"], 15 + LID["t"], "vis", SS)
        rr(v, sg * (R_O + 0), Z_CYL0 + 70, sg * (R_O + 40), Z_CYL0 + 80, "vis", SS)
    px0, px1 = LID["port_x"] - LID["port_w"] / 2, LID["port_x"] + LID["port_w"] / 2
    v.hatch([(-R_RIM, Z_RIM), (px0, Z_RIM), (px0, Z_RIM + LID["t"]), (-R_RIM, Z_RIM + LID["t"])], "hC")
    v.hatch([(px1, Z_RIM), (-LID["bore"] / 2, Z_RIM), (-LID["bore"] / 2, Z_RIM + LID["t"]), (px1, Z_RIM + LID["t"])], "hC")
    for x in (px0 - LID["t"], px1):
        rr(v, x, Z_RIM, x + LID["t"], Z_RIM + LID["up"], "vis", SS)
    rr(v, px0 - 5, Z_RIM + LID["up"], px1 + 5, Z_RIM + LID["up"] + LID["t"], "vis", BLU)
    for sg in (-1, 1):
        rr(v, sg * LID["bore"] / 2, Z_RIM, sg * (LID["bore"] / 2 + LID["t"]), Z_RIM + 25, "vis", SS)
    v.centre(0, Z_TC - 20, 0, Z_RIM + 80)
    v.dim((-HOP["r"], Z_RIM + 60), (HOP["r"], Z_RIM + 60), 30, f"Ø{mmi(2 * HOP['r'])} ID ±1", "h")
    v.dim((-R_RIM, Z_RIM - RIM["t"]), (R_RIM, Z_RIM - RIM["t"]), -0, None, "h") if False else None
    v.dim((R_RIM, Z_TC), (R_RIM, Z_CONE0), -60, None, "v")
    v.dim((R_RIM, Z_CONE0), (R_RIM, Z_CYL0), -60, f"{mmi(HOP['h_cone'])}", "v")
    v.dim((R_RIM, Z_CYL0), (R_RIM, Z_RIM), -60, f"{mmi(HOP['h_cyl'])}", "v")
    v.dim((R_RIM, Z_TC), (R_RIM, Z_RIM), -140, f"{mmi(Z_RIM - Z_TC)} ±1 TC FACE TO RIM", "v")
    v.dim((-TC25["fl"] / 2, Z_TC), (TC25["fl"] / 2, Z_TC), -40, "2.5 in TC (Ø77.5)", "h")
    v.angle((HOP["r_lo"] + T14, Z_CONE0), 90, 0, CONE_ANG, f"{CONE_ANG:.0f}° from horizontal")
    v.datum((60, Z_TC), "A", (0, -1))
    v.fcf(-R_RIM - 110, Z_RIM + 70, ["⊥", "1.0", "A"]); v.note(-R_RIM - 110, Z_RIM + 45, ["rim top ⊥ ferrule axis"], 11)
    v.fcf(-R_RIM - 110, Z_CONE0 + 40, ["◎", "0.8", "A"]); v.note(-R_RIM - 110, Z_CONE0 + 15, ["cylinder ID to the ferrule"], 11)
    v.weld((-R_O, Z_CYL0), (-R_RIM - 20, Z_CYL0 - 100), "sq", "", allround=True, tail="W1 full pen., ground in")
    v.weld((TC25["od"] / 2, Z_CONE0), (150, Z_CONE0 - 70), "sq", "", allround=True, tail="W3 ferrule, full pen., ground")
    v.weld((R_O + RIM["t"], Z_RIM - RIM["w"]), (R_RIM + 90, Z_RIM - 120), "fillet", "2", allround=True, tail="W4 outside + seal top inside")
    v.leader((px0, Z_RIM + LID["up"]), (-150, Z_RIM + 150), ["SCOOP PORT 170 x 280, 40 upstand,", "FLAP 406 + interlock P1-438"], anchor="end")
    v.leader((LID["bore"] / 2 + 1.5, Z_RIM + 20), (160, Z_RIM + 140), ["Ø80 bore + collar 25 (agitator sleeve)"])
    v.leader((R_O + 30, Z_CYL0 + 75), (R_RIM + 60, Z_CYL0 + 160), ["HANDLE 407 x 2 (10 sq bar U)"])
    # ---- lid plan
    vl = S.view(1650, 720, SC(4), "405 LID PLAN (1:4): 2 HALVES, SPLIT ON X = 0", (1290, 250))
    vl.circle(0, 0, R_RIM + LID["t"], "vis", SS); vl.circle(0, 0, LID["bore"] / 2, "vis", "#fff")
    rr(vl, px0, -LID["port_l"] / 2, px1, LID["port_l"] / 2, "vis", "#fff")
    vl.line(0, -R_RIM - 20, 0, R_RIM + 20, "cen"); rr(vl, 0, -R_RIM + 10, 20, R_RIM - 10, "hid")
    for a in HSH["pin_a"]:
        x, y = P(HSH["ri"] + 12, a); vl.circle(x, y, 4.5, "hid")
    rr(vl, px1 + 8, 60, px1 + 38, 100, "vis", BLU)
    vl.dim((px0, -LID["port_l"] / 2), (px1, -LID["port_l"] / 2), -40, None, "h")
    vl.dim((px0, -LID["port_l"] / 2), (px0, LID["port_l"] / 2), 40, None, "v")
    vl.dim((0, -LID["port_l"] / 2), (LID["port_x"], -LID["port_l"] / 2), -90, f"{mmi(-LID['port_x'])}", "h")
    vl.dia(0, 0, R_RIM + LID["t"], 40, (300, 260), f"Ø{mmi(2 * (R_RIM + LID['t']))} OD, skirt 15 down")
    vl.leader((px1 + 23, 100), (200, 330) if False else (330, 160), ["INTERLOCK BNS 260 (P1-438) on 2 x M4", "weld studs; actuator on the flap"])
    vl.leader((10, -150), (180, -310), ["LAP STRIP 20 x 1.5 on the right half", "(hidden), stitch 15 @ 60 outside"])
    vl.text(0, -R_RIM - 60, "operator (-y)", 12)
    # ---- cone development + cylinder blank (1:8)
    s8 = SC(8)
    vd = S.view(2750, 900, SC(6), f"402 CONE BLANK (1:6): R{DEV_RO:.1f} / R{DEV_RI:.1f}, {DEV_ANG:.2f}°", (2280, 250))
    a0, a1 = 90 - DEV_ANG / 2, 90 + DEV_ANG / 2
    cone = arc_pts(DEV_RO, a0, a1, 120) + arc_pts(DEV_RI, a1, a0, 60)
    vd.poly(cone, "vis", True, SS); vd.cmark(0, 0, 20)
    vd.dim(P(DEV_RO, a0), (0, 0), 0, None) if False else None
    vd.rad(0, 0, DEV_RO, 60, (330, 520), f"R{mmi(DEV_RO, 1)} (mean surface)")
    vd.rad(0, 0, DEV_RI, 120, (-330, 330), f"R{mmi(DEV_RI, 1)}")
    vd.angle((0, 0), 120, a0, a1, f"{DEV_ANG:.2f}°")
    vd.note(-DEV_RO, -DEV_RO * 0.45, [f"slant {SLANT:.1f}; roll to Ø{2 * R1m:.1f} / Ø{2 * R2m:.1f} mean", "1 seam W2 (butt, autogenous, ground)"], 12)
    vc = S.view(1750, 1320, s8, f"401 CYLINDER BLANK (1:8): {L_CYL:.1f} x {HOP['h_cyl']:.0f}", (1750, 1230))
    rr(vc, 0, 0, L_CYL, HOP["h_cyl"], "vis", SS)
    vc.dim((0, 0), (L_CYL, 0), -30, f"{mmi(L_CYL, 1)} (on mean Ø)", "h")
    vc.dim((L_CYL, 0), (L_CYL, HOP["h_cyl"]), -30, None, "v")
    dxf_profile(str(DXF / "P1-401-402_cone_blank"), cone, text="P1-401-402 CONE 14ga 316L, roll, mean-surface development")
    dxf_profile(str(DXF / "P1-401-401_cyl_blank"), rect_pts(L_CYL, HOP["h_cyl"], L_CYL / 2, HOP["h_cyl"] / 2), text="P1-401-401 CYLINDER 14ga 316L roll ID450")
    RL = R_RIM + LID["t"]
    left = [(0, -RL)] + arc_pts(RL, 270, 90, 90)[1:-1] + [(0, RL), (0, LID["bore"] / 2)] + arc_pts(LID["bore"] / 2, 90, 270, 30)[1:-1] + [(0, -LID["bore"] / 2)]
    right = [(0, -RL), (0, -LID["bore"] / 2)] + arc_pts(LID["bore"] / 2, 270, 450, 30)[1:-1] + [(0, LID["bore"] / 2), (0, RL)] + arc_pts(RL, 90, -90, 90)[1:-1]
    dxf_profile(str(DXF / "P1-401-405_lid_left"), [left, rect_pts(LID["port_w"], LID["port_l"], LID["port_x"], 0)], text="P1-401-405 LID LEFT 16ga 316L (port side)")
    dxf_profile(str(DXF / "P1-401-405_lid_right"), right, holes=[(px1 + 15, 80.0, 2.0), (px1 + 31, 80.0, 2.0)] if False else [], text="P1-401-405 LID RIGHT 16ga 316L")
    dxf_profile(str(DXF / "P1-401-406_flap"), rect_pts(LID["port_w"] + 10, LID["port_l"] + 10, LID["port_x"], 0), text="P1-401-406 FLAP 16ga 316L, 12 lip on the hinge side")
    S.table(130, 1460, [("PART", 120), ("DESCRIPTION", 300), ("QTY", 40), ("STOCK / BLANK", 470)], [
        ("P1-401-401", "Cylinder shell", 1, f"316L 14 ga (1.9), {L_CYL:.1f} x 150, roll ID 450"),
        ("P1-401-402", "Cone", 1, f"316L 14 ga, development R{DEV_RO:.1f}/R{DEV_RI:.1f} x {DEV_ANG:.1f}°"),
        ("P1-401-403", "Outlet ferrule (buy)", 1, "2.5 in BPE short weld ferrule 14WMP-2.5 316L"),
        ("P1-401-404", "Rim angle (buy rolled)", 1, "316L angle 25 x 25 x 3, rolled leg out, ID 453.8; 2 x Ø9"),
        ("P1-401-405", "Lid, 2 halves + skirt + collar", 1, "316L 16 ga (1.5); skirt 15 rolled; collar Ø83 x 25"),
        ("P1-401-406", "Flap", 1, "316L 16 ga 180 x 290, 12 lip"),
        ("P1-401-407", "Handle", 2, "316L bar 10 sq, U 40 x 90"),
    ], "PARTS", 13, 22)
    S.table(130, 1680, [("WELD", 60), ("JOINT", 330), ("PROCESS", 300), ("NOTES", 480)], [
        ("W1", "Cylinder to cone (butt)", WELD_316, "full penetration, inside ground flush Ra ≤ 0.8"),
        ("W2", "Seams of 401, 402 (butt)", "GTAW autogenous, back purge", "full penetration, ground both sides"),
        ("W3", "Ferrule 403 to cone (butt)", WELD_316, "full pen., inside ground; ⟂ A, concentric 0.5"),
        ("W4", "Rim angle 404 to cylinder", WELD_316, "outside fillet 2; top inside seal, ground (no crevice)"),
        ("W5", "Handles, skirt, collar, upstand", WELD_316, "continuous outside, ground; lid inside smooth"),
    ], "WELD SCHEDULE", 13, 22)
    S.notes(1500, 1460, 1050, [
        f"Volume 42.2 L to the rim (23 kg of blend); cone {CONE_ANG:.0f}° from horizontal for mass flow of a 0.54 g/mL blend (P1-401-900).",
        "Fit the ferrule on a mandrel through the cone so its axis is the cone axis; weld W3 before W1. Check the TC face square to the rim top (1.0).",
        "Product contact (inside, lid underside, flap underside): Ra ≤ 0.8 µm [32 µin], welds ground flush, no crevices; electropolish optional. Passivate ASTM A967.",
        "The hopper hangs on the horseshoe by the rim angle and 2 pins: lift 13 to clear the pins, slide forward through the opening with the tooling removed.",
    ], "FABRICATION", 13)
    S.save(DWG / "P1-401-400_hopper.svg")


def agitator():
    S = sheet("P1-401-500", "AGITATOR WELDMENT (PRODUCT CONTACT)", scale="1:2 · 1:4", material=SS316L, finish=FIN_PC, mass=kg("P1-401-501", "P1-401-502", "P1-401-503"))
    s4 = SC(2)
    v = S.view(1150, 330 + 1700 * s4, s4, "ELEVATION IN THE HOPPER (1:2), SECTION ON Y = 0", (400, 250))
    hp = [(-HOP["r_lo"], Z_CONE0), (-HOP["r"], Z_CYL0), (-HOP["r"], Z_RIM), (HOP["r"], Z_RIM), (HOP["r"], Z_CYL0), (HOP["r_lo"], Z_CONE0)]
    v.poly(hp, "phan", False)
    for sg in (-1, 1):
        rr(v, sg * (AGIT["sleeve_od"] / 2 - AGIT["sleeve_t"]), AGIT["z_arm"], sg * AGIT["sleeve_od"] / 2, Z_AGTC - 21.5, "vis", SS)
        v.poly([(sg * TC25["od"] / 2, Z_AGTC - 21.5), (sg * TC25["od"] / 2, Z_AGTC - 6), (sg * TC25["fl"] / 2, Z_AGTC - 6), (sg * TC25["fl"] / 2, Z_AGTC)], "vis", False)
        rr(v, sg * AGIT["sleeve_od"] / 2, AGIT["z_arm"], sg * AGIT["r_tip"], AGIT["z_arm"] + AGIT["arm_t"], "vis", SS)
        rr(v, sg * (RW - AGIT["blade_t"]), Z_CYL0, sg * RW, AGIT["z_arm"] + AGIT["arm_t"], "vis", SS)
        v.poly([(sg * SC_R0, SC_Z0), (sg * RW, SC_Z1), (sg * (RW - AGIT["blade_t"] / math.sin(math.radians(SC_A))), SC_Z1), (sg * (SC_R0 - AGIT["blade_t"] / math.sin(math.radians(SC_A))), SC_Z0)],
               "vis", True, SS)
    v.line(-TC25["fl"] / 2, Z_AGTC, TC25["fl"] / 2, Z_AGTC)
    rr(v, -SPN["d"] / 2, SPN["Z_cpl"], SPN["d"] / 2, Z_AGTC + 40, "phan")
    v.centre(0, Z_CONE0 - 30, 0, Z_AGTC + 60)
    v.dim((AGIT["r_tip"], AGIT["z_arm"] + AGIT["arm_t"]), (-AGIT["r_tip"], AGIT["z_arm"] + AGIT["arm_t"]), 190, f"Ø{mmi(2 * AGIT['r_tip'])} ARM TIPS", "h")
    v.dim((-RW, Z_CYL0), (RW, Z_CYL0), -40, f"Ø{mmi(2 * RW)} BLADES (10 [.39] off the wall)", "h")
    v.dim((RW, SC_Z0), (RW, Z_AGTC), -120, f"{mmi(Z_AGTC - SC_Z0)} ±1", "v")
    v.dim((RW, AGIT["z_arm"]), (RW, Z_AGTC), -60, f"{mmi(Z_AGTC - AGIT['z_arm'])}", "v")
    v.dim((-SC_R0, SC_Z0), (SC_R0, SC_Z0), -40, f"Ø{mmi(2 * SC_R0, 1)}", "h")
    v.angle((SC_R0, SC_Z0), 70, 0, SC_A, f"{SC_A:.1f}°")
    v.datum((-50, Z_AGTC), "A", (0, 1))
    v.leader((-AGIT["sleeve_od"] / 2, Z_AGTC - 60), (-300, Z_AGTC + 20), ["501 SLEEVE 2.5 in x 0.065 tube (63.5 x 1.65) + 14WMP ferrule", f"tube {SLV_L:.0f} long; 2.5 in TC to hub 304"], anchor="end")
    v.leader((-120, AGIT["z_arm"] + 6), (-300, AGIT["z_arm"] + 120), [f"502 ARM x 2: flat 25 x 6 x {ARM_L:.1f}", "saddle end to the sleeve"], anchor="end")
    v.leader((-RW + 3, Z_CYL0 + 50), (-300, Z_CYL0 - 40), [f"503 BLADE x 2: flat 25 x 6 x {BLADE_L:.0f} (vertical)"], anchor="end")
    v.leader((-(SC_R0 + RW) / 2, (SC_Z0 + SC_Z1) / 2), (-300, Z_CONE0 + 20), [f"503 SCRAPER x 2: flat 25 x 6 x {SC_L:.1f}", f"at {SC_A:.1f}°, 10 off the cone"], anchor="end")
    v.fcf(130, Z_CONE0 + 40, ["◎", "1.0", "A"]); v.note(130, Z_CONE0 + 10, ["blade + scraper edges", "to the TC axis"], 11)
    # plan
    vp = S.view(2650, 650, SC(4), "PLAN (1:4)", (2450, 250))
    vp.circle(0, 0, HOP["r"], "phan"); vp.circle(0, 0, AGIT["sleeve_od"] / 2, "vis", SS)
    for a in (0, 180):
        c = math.cos(math.radians(a))
        rr(vp, c * AGIT["sleeve_od"] / 2, -AGIT["arm_w"] / 2, c * AGIT["r_tip"], AGIT["arm_w"] / 2, "vis", SS)
    vp.cmark(0, 0, HOP["r"] + 15)
    vp.dim((AGIT["r_tip"], AGIT["arm_w"] / 2), (AGIT["r_tip"], -AGIT["arm_w"] / 2), -30, None, "v")
    vp.text(0, -HOP["r"] - 40, "turns CW seen from above, 30 rpm", 12)
    # cut list + DXF
    S.table(1850, 1250, [("PART", 120), ("DESCRIPTION", 260), ("QTY", 40), ("CUT SIZE", 340), ("NOTE", 260)], [
        ("P1-401-501", "Sleeve + ferrule", 1, f"2.5 in OD x 0.065 316L tube x {SLV_L:.0f}; 14WMP-2.5", "BPE, ID Ra ≤ 0.5"),
        ("P1-401-502", "Arm", 2, f"316L flat 25 x 6 x {ARM_L:.1f}", "inner end R31.75 saddle"),
        ("P1-401-503a", "Vertical blade", 2, f"316L flat 25 x 6 x {BLADE_L:.0f}", "edges R1"),
        ("P1-401-503b", "Cone scraper", 2, f"316L flat 25 x 6 x {SC_L:.1f}, ends cut {SC_A:.1f}°", "edges R1"),
    ], "CUT LIST", 13, 22)
    S.table(130, 1640, [("WELD", 60), ("JOINT", 360), ("PROCESS", 300), ("NOTES", 460)], [
        ("W1", "Ferrule to sleeve (butt)", WELD_316, "full pen., orbital or manual + purge, ID ground"),
        ("W2", "Arms to sleeve", WELD_316, "fillet 4 all round, sealed, ground R2"),
        ("W3", "Blades to arms, scrapers to blades", WELD_316, "fillet 4 all round, sealed, ground R2"),
    ], "WELD SCHEDULE", 13, 22)
    S.notes(1600, 1640, 960, [
        "Weld on a fixture that holds the ferrule face (A) square and the sleeve on the axis. After welding, spin on the TC: blade edges within 1.0 of true.",
        "Check in the hopper: 10 [.39] ±2 clearance to the wall and cone at every angle; no contact with the auger flight (tooling J top at z 1,148).",
        "All surfaces product contact: welds sealed, no crevices, Ra ≤ 0.8. Passivate. The agitator drops out with the 2.5 in TC clamp (P1-445).",
    ], "FABRICATION", 13)
    for nm, L in (("502_arm", ARM_L), ("503a_blade", BLADE_L), ("503b_scraper", SC_L)):
        dxf_profile(str(DXF / f"P1-401-{nm}"), rect_pts(L, 25, L / 2, 0), text=f"P1-401-{nm} 6mm 316L x2")
    S.save(DWG / "P1-401-500_agitator.svg")


if __name__ == "__main__":
    hopper(); agitator()
    print("ok", DEV_RO, DEV_RI, DEV_ANG, SC_L, SC_A, ARM_L, BLADE_L)
