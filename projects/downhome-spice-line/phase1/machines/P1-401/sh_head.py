"""P1-401-300 drive head assembly, -301 machined parts (head plate, housing, spindle, hub, bridge, cap, spacers), -600 auger tooling spec."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
from mechsheet import dxf_profile
from sh_parts import P, circ, arc_pts, rect_pts, rr, SS, BLU, BD

C = calcs()
BR_PTS = [(SERVO_X + sx * 55, sy * 55) for sx in (-1, 1) for sy in (-1, 1)]
HOUS_PTS = [P(HOUS["pcd"] / 2, 45 + 90 * k) for k in range(4)]
GM_PTS = [(GM_X + sx * 45, sy * 45) for sx in (-1, 1) for sy in (-1, 1)]
CAP_PTS = [(sx * 60, COL["y"] + sy * 60) for sx in (-1, 1) for sy in (-1, 1)]
GUARD_PTS = [(-60.0, -78.0), (-60.0, 78.0), (200.0, -78.0), (200.0, 78.0)]
SPR_PTS = [P(HUB["spr_pcd"] / 2, 45 + 90 * k) for k in range(4)]
ZB = Z_HPT + BRIDGE["h"]                  # bridge flange underside
BG = dict(x0=SERVO_X - 45, x1=50.0, y0=-50.0, y1=50.0, z0=HOUS["z_top"] + HOUS["cap_t"], z1=ZB - 1)
CG = dict(x0=-75.0, x1=GM_X + 45, y0=-70.0, y1=70.0, d=32.0)


def slot(v, x, y, L, w, k="vis"):
    """slot along x, overall L x w"""
    r = w / 2
    v.line(x - L / 2 + r, y - r, x + L / 2 - r, y - r, k); v.line(x - L / 2 + r, y + r, x + L / 2 - r, y + r, k)
    v.arc(x - L / 2 + r, y, r, 90, 270, k); v.arc(x + L / 2 - r, y, r, -90, 90, k)


def slot_dxf(x, y, L, w):
    r = w / 2
    return [(x - L / 2 + r, y - r), (x + L / 2 - r, y - r)] + arc_pts(r, -90, 90, 16, x + L / 2 - r, y)[1:-1] + \
        [(x + L / 2 - r, y + r), (x - L / 2 + r, y + r)] + arc_pts(r, 90, 270, 16, x - L / 2 + r, y)[1:-1]


# ================================================================== 300 drive head assembly
def head_asm():
    S = sheet("P1-401-300", "DRIVE HEAD ASSEMBLY", scale="1:2", material="see parts", finish="see parts",
              mass=kg(*[f"P1-401-30{i}" for i in range(1, 10)], "P1-401-310"))
    s2 = SC(2)
    v = S.view(170 + 235 * s2 + 40, 300 + 385 * s2, s2, "PLAN FROM ABOVE (1:2): SERVO, BRIDGE, GEARMOTOR ON HEAD PLATE 301", (170, 250))
    rr(v, HPL["x0"], HPL["y0"], HPL["x1"], HPL["y1"], "vis", SS)
    rr(v, -CAP["a"] / 2, COL["y"] - CAP["a"] / 2, CAP["a"] / 2, COL["y"] + CAP["a"] / 2, "hid")
    v.circle(0, COL["y"], 20)
    v.circle(0, 0, HUB["fl_d"] / 2, "hid"); v.circle(GM_X, 0, 30.5, "hid")
    v.poly([(CG["x0"], CG["y0"]), (CG["x1"], CG["y0"]), (CG["x1"], CG["y1"]), (CG["x0"], CG["y1"])], "hid")
    for x, y in CAP_PTS + GUARD_PTS:
        v.circle(x, y, 5.5 if (x, y) in CAP_PTS else 3, "vis" if (x, y) in CAP_PTS else "hid")
    v.circle(0, 0, HOUS["fl_d"] / 2, "vis", "#eceff1"); v.circle(0, 0, HOUS["body_d"] / 2, "vis", "#eceff1")
    for x, y in HOUS_PTS:
        v.circle(x, y, 6.5)
    rr(v, BG["x0"], BG["y0"], BG["x1"], BG["y1"], "phan")
    v.circle(0, 0, PD2 / 2 + 2, "vis", BLU); v.circle(SERVO_X, 0, PD1 / 2 + 2, "vis", BLU)
    v.line(SERVO_X, PD1 / 2 + 3, 0, PD2 / 2 + 3, "thin"); v.line(SERVO_X, -PD1 / 2 - 3, 0, -PD2 / 2 - 3, "thin")
    v.circle(0, 0, 15, "vis", "#cfd8dc")
    rr(v, SERVO_X - BRIDGE["a"] / 2, -BRIDGE["a"] / 2, SERVO_X + BRIDGE["a"] / 2, BRIDGE["a"] / 2, "vis", SS)
    rr(v, SERVO_X - 40, -40, SERVO_X + 40, 40, "vis", "#37474f"); v.text(SERVO_X, 5, "SERVO", 11, color="#fff")
    for x, y in BR_PTS:
        v.circle(x, y, 12.5, "hid")
    rr(v, GM_X - 55, -55, GM_X + 55, 55, "vis", BLU); v.text(GM_X, 5, "GEARMOTOR", 11)
    v.cmark(0, 0, 60); v.cmark(SERVO_X, 0, 50); v.cmark(GM_X, 0, 70)
    tags = [(1, (HPL["x0"] + 20, HPL["y1"] - 40), (HPL["x0"] - 30, HPL["y1"] - 70), "301"), (2, (40, -40), (60, -170), "302"), (3, (0, 0), (-60, -190), "303"),
            (4, (-50, -50), (-110, -180), "304"), (5, (BG["x1"] - 5, BG["y1"] - 5), (40, 120), "305"), (6, (CG["x1"] - 10, CG["y0"] + 4), (GM_X + 40, -140), "306"),
            (7, (SERVO_X - 70, 60), (SERVO_X - 120, 130), "307"), (8, (20, 20), (90, 110), "308"), (9, (SERVO_X + 20, -30), (SERVO_X - 40, -170), "P1-413"),
            (10, (GM_X + 40, 40), (GM_X + 40, 130), "P1-414"), (11, (-PD2 / 2, 10), (-70, 160), "P1-431"), (12, (0, COL["y"]), (100, COL["y"] + 40), "cable")]
    for n, at, to, _ in tags:
        v.tag(*to, n, at)
    v.dim((SERVO_X, -BRIDGE["a"] / 2 - 10), (0, -BRIDGE["a"] / 2 - 10), -40, f"{mmi(BELT['C'])} BELT C-C (slots ±8)", "h") if False else None
    v.dim((SERVO_X, HPL["y0"]), (0, HPL["y0"]), -30, f"{mmi(BELT['C'])} (±8 slots)", "h")
    v.dim((0, HPL["y0"]), (GM_X, HPL["y0"]), -30, f"{mmi(CHAIN['C'])} (±5 slots)", "h")
    v.dim((0, 0), (0, COL["y"]), -260 if False else 0, None, "v") if False else None
    v.dim((HPL["x1"], 0), (HPL["x1"], COL["y"]), -40, f"{mmi(COL['y'])}", "v")
    S.table(1300, 290, [("ITEM", 50), ("PART", 120), ("DESCRIPTION", 400), ("QTY", 40)], [
        (1, "P1-401-301", "Head plate 304 10 mm", 1), (2, "P1-401-302", "Spindle housing 304", 1), (3, "P1-401-303", "Spindle 316 Ø25", 1),
        (4, "P1-401-304", "Agitator hub 304 + 2.5 in TC ferrule 316L", 1), (5, "P1-401-305", "Belt guard 1.5 mm 304", 1), (6, "P1-401-306", "Chain guard tray 1.5 mm 304", 1),
        (7, "P1-401-307", "Servo bridge weldment 304", 1), (8, "P1-401-308", "Bearing cap 304", 1), ("-", "P1-401-309/310", "Outer + inner spacers 30 long", 1),
        (9, "P1-413", "Servo 750 W (SureServo2)", 1), (10, "P1-414", "Gearmotor 1/4 HP 60 rpm + 15T", 1), (11, "P1-431", "HTD 5M 20T / 40T + belt 450-5M-15", 1),
        ("-", "P1-430", "6205-2RS x 2 + 6008-2RS x 2", 1), ("-", "P1-432", "#40 SS chain 52 L + 30T plate", 1), ("-", "P1-433", "Lip seal 25 x 40 x 7 x 2", 1),
        (12, "-", "Cables up the column, Ø40 pass in 301", "-"),
    ], "ITEMS", 13, 22)
    steps = [
        "Spindle cartridge (bench): DIN 471 Ø25 in the lower groove; press the lower 6205 onto the spindle (press the inner ring only) against it.",
        "Inner spacer 310, then the upper 6205, then the upper DIN 471 Ø25. Spindle must turn freely with both bearings.",
        "Housing 302 flange-up on the bench: drop the cartridge in from the top (Ø52 H7 straight bore) with outer spacer 309 between the outer rings.",
        "Seal 25x40x7 into cap 308 (lip up, grease); cap over the spindle onto the housing, 4 x M4 x 16 (H11) 3 N·m: clamps the outer stack.",
        "Housing into the head plate pilot Ø50 from above, 4 x M8 x 25 (H3) 20 N·m, Loctite 243.",
        "Hub 304: seal 25x40x7 in its bottom pocket (lip down), 2 x 6008 pressed into Ø68 H7 with Loctite 641; press the hub onto the spigot from below, DIN 471 Ø40 under.",
        "30T sprocket plate to the hub flange, 4 x M6 x 16 (H7) 8 N·m. Gearmotor with the 15T on top, shaft down through slot E; chain 52 L; tension 4 mm deflection mid-span; 4 x 1/4-20 (H6).",
        "Chain guard 306 from below, 4 x M6 (H12). Bridge 307 on the plate, 4 x M10 x 25 from below (H5). Servo into the Ø70 pilot, 4 x M6 (H4) 8 N·m.",
        "Pulleys: 20T on the servo, 40T on the spindle key, M10 end bolt + Ø30 washer (H8) 35 N·m. Belt 450-5M-15: slide the bridge to 4 mm deflection at ~15 N mid-span, then H5 45 N·m.",
        "Belt guard 305 to the bridge (2 x M6, H12). Head onto the column cap: 4 x M10 x 30 (H2) 45 N·m. Check runout at the coupling face ≤ 0.05 TIR and the hub TC face ≤ 0.10 TIR.",
    ]
    S.notes(1300, 760, 1950, steps, "ASSEMBLY SEQUENCE (section: P1-401-002 DETAIL H)", 13)
    # guards: flat patterns
    s4 = SC(4)
    gw, gl, gh = BG["x1"] - BG["x0"], BG["y1"] - BG["y0"], BG["z1"] - BG["z0"]
    vg = S.view(300, 1830, s4, f"305 BELT GUARD FLAT (1:4): {mmi(gw + 2 * gh - 2 * BD, 1)} x {mmi(gl + 2 * gh - 2 * BD, 1)}", (170, 1480))
    FW, FL = gw + 2 * gh - 2 * BD, gl + 2 * gh - 2 * BD
    g_out = [(0, gh), (gh, gh), (gh, 0), (gh + gw - 2 * BD, 0), (gh + gw - 2 * BD, gh), (FW, gh), (FW, gh + gl - 2 * BD), (gh + gw - 2 * BD, gh + gl - 2 * BD),
             (gh + gw - 2 * BD, FL), (gh, FL), (gh, gh + gl - 2 * BD), (0, gh + gl - 2 * BD)]
    vg.poly(g_out, "vis", True, SS)
    g_holes = [(gh + 45 + 0, gh + (gl - 2 * BD) / 2, 37.0)]
    vg.circle(*g_holes[0]); vg.dim((0, 0), (FW, 0), -30, None, "h"); vg.dim((FW, 0), (FW, FL), -30, None, "v")
    vg.note(0, -40, ["open-bottom tray: 4 sides up 90°, corners welded + ground; Ø74 for the housing body", "2 tabs to the bridge (M6) welded on"], 11)
    dxf_profile(str(DXF / "P1-401-305_belt_guard"), g_out, holes=g_holes, text="P1-401-305 BELT GUARD 1.5mm 304, sides up 90")
    cw, cl, cd = CG["x1"] - CG["x0"], CG["y1"] - CG["y0"], CG["d"]
    CW, CL = cw + 2 * cd - 2 * BD, cl + 2 * cd - 2 * BD
    vc = S.view(1050, 1830, s4, f"306 CHAIN GUARD FLAT (1:4): {mmi(CW, 1)} x {mmi(CL, 1)}", (900, 1480))
    c_out = [(0, cd), (cd, cd), (cd, 0), (cd + cw - 2 * BD, 0), (cd + cw - 2 * BD, cd), (CW, cd), (CW, cd + cl - 2 * BD), (cd + cw - 2 * BD, cd + cl - 2 * BD),
             (cd + cw - 2 * BD, CL), (cd, CL), (cd, cd + cl - 2 * BD), (0, cd + cl - 2 * BD)]
    vc.poly(c_out, "vis", True, SS)
    c_holes = [(cd + 75, cd + (cl - 2 * BD) / 2, HUB["od"] / 2 + 3)]
    vc.circle(*c_holes[0]); vc.dim((0, 0), (CW, 0), -30, None, "h"); vc.dim((CW, 0), (CW, CL), -30, None, "v")
    vc.note(0, -40, ["tray: 4 sides up 90°, corners welded; 4 tabs 30 x 16 with Ø6.6 at the top edge", "(at x -60 / +200, y ±78); Ø86 hole for the hub"], 11)
    dxf_profile(str(DXF / "P1-401-306_chain_guard"), c_out, holes=c_holes, text="P1-401-306 CHAIN GUARD 1.5mm 304, sides up 90")
    S.table(1950, 1430, [("CHECK", 330), ("VALUE", 200), ("HOW", 300)], [
        ("Belt tension (HTD 5M 15)", "4 mm @ 15 N mid-span", "Gates tension gauge"),
        ("Chain sag (#40, C 184)", "4 mm mid-span", "rule"),
        ("Spindle end float", "≤ 0.05", "dial on the end bolt"),
        ("Coupling face runout", "≤ 0.05 TIR", "dial, turn by hand"),
        ("Hub TC face runout", "≤ 0.10 TIR", "dial"),
        ("Servo / spindle pulley align", "≤ 0.5 offset", "straight edge"),
    ], "SET-UP CHECKS", 13, 22)
    S.save(DWG / "P1-401-300_drive_head_assembly.svg")


# ================================================================== 301 machined parts
def machined():
    S = sheet("P1-401-301", "DRIVE HEAD MACHINED PARTS", scale="1:4 · 1:2 · 1:1",
              material="304 (301, 302, 304, 307, 308, 309, 310); 316 (303)", finish="machined Ra 1.6 unless noted; passivate", mass=kg("P1-401-301", "P1-401-302", "P1-401-303",
                                                                                                                                         "P1-401-304", "P1-401-307", "P1-401-308"))
    K1 = SC(1)
    # ---- 301 head plate (1:3)
    s3 = SC(4)
    v = S.view(170 + 235 * s3 + 20, 380 + 385 * s3, s3, "301 HEAD PLATE (1:4), 304 PLATE 10 mm, FROM ABOVE", (170, 250))
    rr(v, HPL["x0"], HPL["y0"], HPL["x1"], HPL["y1"], "vis", SS)
    v.circle(0, 0, HOUS["pilot_d"] / 2); v.cmark(0, 0, 32)
    for x, y in HOUS_PTS:
        v.circle(x, y, 4); v.circle(x, y, 3.4, "thin")
    for x, y in BR_PTS:
        slot(v, x, y, 21, 11)
    for x, y in GM_PTS:
        slot(v, x, y, 19, 9)
    slot(v, GM_X, 0, 50, 36)
    for x, y in CAP_PTS:
        v.circle(x, y, 5.5)
    v.circle(0, COL["y"], 20)
    for x, y in GUARD_PTS:
        v.circle(x, y, 3, "hid")
    v.dim((HPL["x0"], HPL["y0"]), (HPL["x1"], HPL["y0"]), -50, f"{mmi(HPL['x1'] - HPL['x0'])}", "h")
    v.dim((HPL["x1"], HPL["y0"]), (HPL["x1"], HPL["y1"]), -50, f"{mmi(HPL['y1'] - HPL['y0'])}", "v")
    v.dim((HPL["x0"], HPL["y1"]), (0, HPL["y1"]), 40, f"{mmi(-HPL['x0'])}", "h")
    v.dim((HPL["x0"], HPL["y0"]), (HPL["x0"], 0), 40, f"{mmi(-HPL['y0'])}", "v")
    v.datum((HPL["x0"] + 40, HPL["y0"]), "B", (0, -1)) if False else None
    rows = [("A", "Ø50 H8 THRU", "0", "0", "housing pilot (f7)"),
            ("B1-4", "M8 THRU", "±31.82", "±31.82", "housing, on Ø90 at 45°"),
            ("C1-4", "slot 11 x 21 (x)", f"{SERVO_X - 55:.0f} / {SERVO_X + 55:.0f}", "±55", "bridge posts, belt tension"),
            ("D1-4", "slot 9 x 19 (x)", f"{GM_X - 45:.0f} / {GM_X + 45:.0f}", "±45", "gearmotor flange, chain"),
            ("E", "slot 36 x 50 (x)", f"{GM_X:.0f}", "0", "gearmotor shaft + 15T"),
            ("F1-4", "Ø11 THRU", "±60", "240 / 360", "to column cap 203 (H2)"),
            ("G", "Ø40 THRU", "0", f"{COL['y']:.0f}", "cable pass"),
            ("H1-4", "M6 x 8 deep, from below", "-60 / 200", "±78", "chain guard 306 tabs")]
    S.table(130, 1000, [("HOLE", 60), ("SIZE", 190), ("X", 110), ("Y", 90), ("FOR", 230)], rows, "301 HOLE TABLE (from the auger axis, ±0.1)", 12, 21)
    hp = [rect_pts(HPL["x1"] - HPL["x0"], HPL["y1"] - HPL["y0"], (HPL["x0"] + HPL["x1"]) / 2, (HPL["y0"] + HPL["y1"]) / 2)]
    hp += [slot_dxf(x, y, 21, 11) for x, y in BR_PTS] + [slot_dxf(x, y, 19, 9) for x, y in GM_PTS] + [slot_dxf(GM_X, 0, 50, 36)]
    dxf_profile(str(DXF / "P1-401-301_head_plate"), hp, holes=[(0, 0, 24.0)] + [(x, y, 3.4) for x, y in HOUS_PTS] + [(x, y, 5.5) for x, y in CAP_PTS] + [(0, COL["y"], 20.0)],
                text="P1-401-301 HEAD PLATE 10mm 304: laser, then bore Ø50 H8, tap M8 x4, M6 x4 blind from below")
    # ---- 302 housing (1:1), section
    zt = HOUS["z_top"]; zs0 = Z_HP - (HOUS["spig_L"] - HPL["t"])
    vh = S.view(1350, 400 + zt * K1, K1, "302 SPINDLE HOUSING (1:1), SECTION", (1150, 290))
    prof = [(14, zs0), (HOUS["spig_d"] / 2, zs0), (HOUS["spig_d"] / 2, Z_HP), (HOUS["pilot_d"] / 2, Z_HP), (HOUS["pilot_d"] / 2, Z_HPT), (HOUS["fl_d"] / 2, Z_HPT),
            (HOUS["fl_d"] / 2, Z_HPT + HOUS["fl_t"]), (HOUS["body_d"] / 2, Z_HPT + HOUS["fl_t"]), (HOUS["body_d"] / 2, zt), (26, zt), (26, HOUS["brg_lo"]), (19, HOUS["brg_lo"]),
            (19, Z_HPT), (14, Z_HPT)]
    for sg in (-1, 1):
        vh.hatch([(sg * x, z) for x, z in prof], "hA")
        vh.rect(min(sg * 20, sg * 18.75), HUB["z_brg"] - 1.85, 1.25, 1.85, "vis", "#fff")
        vh.rect(min(sg * 31, sg * 35), zt - 10, 4, 10, "hid"); vh.rect(min(sg * 45 - 4.5 * sg, sg * 45 + 4.5 * sg), Z_HPT, 9, HOUS["fl_t"], "hid")
    vh.centre(0, zs0 - 15, 0, zt + 20)
    vh.dim((-HOUS["fl_d"] / 2, Z_HPT), (HOUS["fl_d"] / 2, Z_HPT), -40, f"Ø{mmi(HOUS['fl_d'])}", "h")
    vh.dim((-HOUS["body_d"] / 2, zt), (HOUS["body_d"] / 2, zt), 40, f"Ø{mmi(HOUS['body_d'])}", "h")
    vh.dim((-26, zt), (26, zt), 80, "Ø52 H7 [2.0472/2.0480] Ra 0.8", "h")
    vh.dim((-HOUS["pilot_d"] / 2, Z_HP), (HOUS["pilot_d"] / 2, Z_HP), -10, None, "h") if False else None
    vh.leader((-HOUS["pilot_d"] / 2, Z_HP + 5), (-95, Z_HP + 20), ["Ø50 f7 [1.9675/1.9665] PILOT"], anchor="end")
    vh.leader((-HOUS["spig_d"] / 2, zs0 + 20), (-95, zs0 + 5), ["Ø40 k6 [1.5754/1.5749] SPIGOT", "DIN 471 groove Ø37.5 x 1.85"], anchor="end")
    vh.leader((-19, Z_HPT + 6), (-95, Z_HPT + 50), ["Ø38 shoulder (lower bearing seat face)"], anchor="end")
    vh.leader((-14, zs0 + 10), (-30, zs0 - 30) if False else (110, zs0 - 20), ["Ø28 THRU"])
    vh.leader((33, zt), (110, zt + 30), ["4 x M4 x 10 deep on Ø62 at 45° (cap)"])
    vh.leader((45, Z_HPT + 6), (110, Z_HPT - 20), ["4 x Ø9 THRU on Ø90 at 45° (H3)"])
    vh.dim((HOUS["fl_d"] / 2, zs0), (HOUS["fl_d"] / 2, zt), -120, f"{mmi(zt - zs0)}", "v")
    vh.dim((HOUS["fl_d"] / 2, zs0), (HOUS["fl_d"] / 2, Z_HP), -60, f"{mmi(Z_HP - zs0)}", "v")
    vh.dim((HOUS["body_d"] / 2, HOUS["brg_lo"]), (HOUS["body_d"] / 2, zt), -20, f"{mmi(zt - HOUS['brg_lo'])} +0.05/-0", "v")
    vh.datum((0, Z_HP), "A", (0, -1)) if False else None
    vh.fcf(25, zs0 + 25, ["◎", "Ø0.02", "Ø50 f7"]); vh.note(25, zs0 + 5, ["bore and spigot", "to the pilot, one set-up"], 11)
    # ---- 304 hub (1:1), section
    z1 = HUB["z1"]; zf = z1 - HUB["fl_t"]
    vb = S.view(2500, 330 + z1 * K1 + 60, K1, "304 AGITATOR HUB (1:1), SECTION", (2300, 290))
    hpro = [(20, HUB["z_seal"]), (HUB["od"] / 2, HUB["z_seal"]), (HUB["od"] / 2, zf), (HUB["fl_d"] / 2, zf), (HUB["fl_d"] / 2, z1), (34, z1), (34, HUB["z_brg"]),
            (24, HUB["z_brg"]), (24, HUB["z_seal"] + 7), (20, HUB["z_seal"] + 7)]
    fer = [(30.1, Z_AGTC), (38.75, Z_AGTC), (38.75, Z_AGTC + 6), (31.75, Z_AGTC + 6), (31.75, HUB["z_seal"]), (30.1, HUB["z_seal"])]
    for sg in (-1, 1):
        vb.hatch([(sg * x, z) for x, z in hpro], "hA"); vb.hatch([(sg * x, z) for x, z in fer], "hC")
        vb.rect(min(sg * 47, sg * 53), zf, 6, HUB["fl_t"], "hid")
    vb.centre(0, Z_AGTC - 10, 0, z1 + 15)
    vb.dim((-HUB["fl_d"] / 2, z1), (HUB["fl_d"] / 2, z1), 50, f"Ø{mmi(HUB['fl_d'])}", "h")
    vb.dim((-34, z1), (34, z1), 20, "Ø68 H7 [2.6772/2.6784]", "h")
    vb.dim((-HUB["od"] / 2, HUB["z_seal"]), (HUB["od"] / 2, HUB["z_seal"]), -50, f"Ø{mmi(HUB['od'])}", "h")
    vb.dim((-HUB["fl_d"] / 2, Z_AGTC), (-HUB["fl_d"] / 2, z1), 40, f"{mmi(z1 - Z_AGTC)}", "v")
    vb.dim((-HUB["fl_d"] / 2, HUB["z_brg"]), (-HUB["fl_d"] / 2, z1), 110, f"{mmi(z1 - HUB['z_brg'])} +0.05/-0", "v")
    vb.leader((20, HUB["z_seal"] + 3), (90, HUB["z_seal"] - 25), ["Ø40 H8 x 7 seal pocket", "Ø48 x 4 ring relief above"])
    vb.leader((50, z1), (90, z1 + 40), ["4 x M6 x 8 on Ø100 at 45° (30T plate)"])
    vb.leader((38, Z_AGTC + 3), (90, Z_AGTC - 20), ["2.5 in BPE FERRULE 14WMP 316L,", "butt weld, ID ground; face ⟂ bore 0.05"])
    # ---- 303 spindle (1:2), drawn horizontal: x = z - Z_cpl
    s2 = SC(2)
    zc = SPN["Z_cpl"]
    vsp = S.view(1100, 1130, s2, f"303 SPINDLE (1:2), 316 Ø30 BAR, L {mmi(SPN['top'] - zc)}: COUPLING END AT THE LEFT", (1050, 1000))
    segs = [(zc, HOUS["brg_lo"] - 1.6, SPN["d"]), (HOUS["brg_lo"] - 1.6, Z_PUL, SPN["d"]), (Z_PUL, SPN["top"], SPN["seat"])]
    for a, b, d in segs:
        rr(vsp, a - zc, -d / 2, b - zc, d / 2, "vis", "#eceff1")
    for zr in (HOUS["brg_lo"] - 1.6, HOUS["z_top"] + 0.2):
        rr(vsp, zr - zc, -12.5, zr - zc + 1.3, -11.95, "vis", "#fff"); rr(vsp, zr - zc, 11.95, zr - zc + 1.3, 12.5, "vis", "#fff")
    rr(vsp, 0, -7.25, 30, 7.25, "hid"); rr(vsp, SPN["top"] - zc - 22, -4.25, SPN["top"] - zc, 4.25, "hid")
    rr(vsp, Z_PUL - zc + 3, 10 - 3.5, SPN["top"] - zc - 3, 10, "vis", "#fff")
    vsp.line(-10, 0, SPN["top"] - zc + 10, 0, "cen")
    vsp.dim((0, -12.5), (SPN["top"] - zc, -12.5), -60, f"{mmi(SPN['top'] - zc)} ±0.1", "h")
    vsp.dim((0, 12.5), (HOUS["brg_lo"] - zc, 12.5), 50, f"{mmi(HOUS['brg_lo'] - zc)}", "h")
    vsp.dim((HOUS["brg_lo"] - zc, 12.5), (HOUS["z_top"] - zc, 12.5), 50, f"{mmi(HOUS['z_top'] - HOUS['brg_lo'])} (2 x 6205 + 30)", "h")
    vsp.dim((Z_PUL - zc, 10), (SPN["top"] - zc, 10), 90, f"{mmi(SPN['top'] - Z_PUL)}", "h")
    vsp.leader((20, -7.25), (-20, -60), ["M16 x 1.5 LH x 30 deep (auger)", "face ⟂ axis 0.02, Ra 0.8"], anchor="end")
    vsp.leader((HOUS["brg_lo"] - zc + 5, -12.5), (HOUS["brg_lo"] - zc - 40, -70), ["Ø25 k6 [.9844/.9849] bearing seats 1742-1757,", "1787-1802; Ø25 h9 Ra 0.4 at both seals"], anchor="end")
    vsp.leader((HOUS["brg_lo"] - 1 - zc, -12), (HOUS["brg_lo"] - zc + 40, -60) if False else (HOUS["z_top"] - zc, -70), ["2 x DIN 471 grooves Ø23.9 x 1.3"])
    vsp.leader((SPN["top"] - zc - 12, 8), (SPN["top"] - zc + 30, 50), ["Ø20 h6 seat, key 6 x 6 x 24", "M10 x 22 deep end"])
    vsp.fcf(SPN["top"] - zc + 20, -30, ["↗", "0.01", "A-B"]); vsp.note(SPN["top"] - zc + 20, -55, ["seats + coupling face to", "the bearing seats A-B"], 11)
    # ---- 307 bridge (1:2) plan + elevation
    vbp = S.view(2850, 1080, s2, "307 SERVO BRIDGE (1:2): PLAN", (2650, 870))
    rr(vbp, -70, -70, 70, 70, "vis", SS); vbp.circle(0, 0, 35); vbp.cmark(0, 0, 45)
    for x, y in [P(45, 45 + 90 * k) for k in range(4)]:
        vbp.circle(x, y, 3.3)
    for x, y in [(sx * 55, sy * 55) for sx in (-1, 1) for sy in (-1, 1)]:
        vbp.circle(x, y, 12.5, "hid")
    for y in (-30, 30):
        vbp.circle(62, y, 2.5, "hid")
    vbp.dim((-70, -70), (70, -70), -30, f"{mmi(140)}", "h"); vbp.dim((-55, 70), (55, 70), 30, f"{mmi(110)} POSTS", "h")
    vbp.leader((-25, -25), (-100, -110), ["Ø70 H8 THRU (servo pilot)", "4 x Ø6.6 on Ø90 at 45°"], anchor="end")
    vbp.leader((62, 30), (90, 100), ["2 x M6 x 8 from below", "(belt guard)"])
    S.notes(2560, 1330, 700, ["Posts Ø25 x 110 304 bar, M10 x 20 tapped one end, plug-welded into the flange (Ø25 H11 holes) + fillet 4 under; face the flange after welding, ⟂ posts 0.05."],
            "307 POSTS", 12)
    # ---- 308 cap, 309/310 spacers (1:1)
    vcp = S.view(2400, 1200 + (zt + HOUS["cap_t"]) * K1, K1, "308 CAP (1:1)", (2250, 1120))
    cp = [(13, zt + HOUS["cap_t"]), (36, zt + HOUS["cap_t"]), (36, zt), (18, zt), (18, zt + 3), (20, zt + 3), (20, zt + 10), (13, zt + 10)]
    for sg in (-1, 1):
        vcp.hatch([(sg * x, z) for x, z in cp], "hA")
    vcp.centre(0, zt - 10, 0, zt + 25)
    vcp.dim((-36, zt + HOUS["cap_t"]), (36, zt + HOUS["cap_t"]), 40, "Ø72", "h")
    vcp.dim((36, zt), (36, zt + HOUS["cap_t"]), -30, None, "v")
    vcp.leader((-20, zt + 6), (-50, zt - 30), ["Ø40 H8 x 7 seal pocket; Ø36 x 3 ring recess", "Ø26 THRU; 4 x Ø4.5 csk on Ø62 at 45°"], anchor="end")
    vspc = S.view(2450, 1700, K1, "309 / 310 SPACERS (1:1), 304", (2300, 1500))
    for sg in (-1, 1):
        vspc.hatch([(sg * 23, 0), (sg * 26, 0), (sg * 26, 30), (sg * 23, 30)], "hA"); vspc.hatch([(sg * 12.55, 0), (sg * 15, 0), (sg * 15, 30), (sg * 12.55, 30)], "hB")
    vspc.dim((-26, 30), (26, 30), 30, "309: Ø52 g6 / Ø46", "h"); vspc.dim((-15, 0), (15, 0), -30, "310: Ø30 / Ø25.1", "h")
    vspc.dim((26, 0), (26, 30), -30, "30.00 ±0.01 (both, ground as a pair)", "v")
    S.table(1250, 1450, [("PART", 110), ("MATERIAL / STOCK", 330), ("KEY TOLERANCES", 520)], [
        ("301", "304 plate 10 mm, laser + mill", "Ø50 H8; flatness 0.1; holes ±0.1 true position Ø0.2"),
        ("302", "304 bar Ø115 x 125", "Ø52 H7 + Ø40 k6 + Ø50 f7 in one set-up, ◎ 0.02"),
        ("303", "316 bar Ø30 x 355, ground", "k6 seats, ↗ 0.01 A-B, M16 x 1.5 LH face ⟂ 0.02"),
        ("304", "304 bar Ø145 x 45 + 14WMP ferrule", "Ø68 H7, depth 30 +0.05, TC face ⟂ 0.05 after welding"),
        ("307", "304 plate 10 + bar Ø25", "Ø70 H8 ⟂ post ends 0.05 (face after welding)"),
        ("308-310", "304 bar", "Ø40 H8 pocket; spacers 30 ±0.01 matched"),
    ], "MACHINING SUMMARY", 12, 21)
    S.save(DWG / "P1-401-301_machined_parts.svg")


# ================================================================== 600 auger tooling (bought to this spec)
def tooling():
    S = sheet("P1-401-600", "AUGER TOOLING SPECIFICATION", scale="1:1 · 1:2", material="316 / 316L (product contact)", finish=FIN_PC, mass="-")
    s1 = SC(1)
    zt = Z_TC
    TJ, TS = TOOL["J"], TOOL["S"]
    # J set, vertical, 1:1 would be 515 mm tall: use 1:2
    s2 = SC(2)
    zo = Z_OUT
    v = S.view(600, 300 + SPN["Z_cpl"] * s2 + 40, s2, "SET J: AUGER IN TUBE (1:2), JAR / POUCH / TUB", (200, 250))
    for sg in (-1, 1):
        v.hatch([(sg * TJ["tube_id"] / 2, zo), (sg * TJ["tube_od"] / 2, zo), (sg * TJ["tube_od"] / 2, zt - 25), (sg * TC25["od"] / 2, zt - 6), (sg * TC25["fl"] / 2, zt - 6),
                 (sg * TC25["fl"] / 2, zt), (sg * TC25["id"] / 2, zt), (sg * TJ["tube_id"] / 2, zt - 25)], "hC")
    rr(v, -8, zo + 5, 8, SPN["Z_cpl"], "vis", "#eceff1")
    rr(v, -8, SPN["Z_cpl"] - 25, 8, SPN["Z_cpl"], "vis", "#cfd8dc")
    zf0, zf1 = zo + 5, zt + 30
    n = int((zf1 - zf0) / TJ["pitch"])
    for i in range(n + 1):
        z = zf0 + i * TJ["pitch"]
        if z + TJ["pitch"] / 2 > zf1:
            break
        v.line(-TJ["auger_od"] / 2, z, TJ["auger_od"] / 2, z + TJ["pitch"] / 2, "vis"); v.line(-TJ["auger_od"] / 2, z + TJ["pitch"], TJ["auger_od"] / 2, z + TJ["pitch"] / 2, "thin")
    v.centre(0, zo - 20, 0, SPN["Z_cpl"] + 20)
    v.dim((-TJ["tube_od"] / 2, zo), (TJ["tube_od"] / 2, zo), -30, f"Ø{mmi(TJ['tube_od'])} x 1.65 TUBE", "h")
    v.dim((TC25["fl"] / 2, zo), (TC25["fl"] / 2, zt), -60, f"{mmi(zt - zo)} TUBE ±0.5", "v")
    v.dim((TC25["fl"] / 2, zt), (TC25["fl"] / 2, SPN["Z_cpl"]), -60, f"{mmi(SPN['Z_cpl'] - zt)} TC FACE TO COUPLING", "v")
    v.dim((-TJ["auger_od"] / 2, zo + 5), (-TJ["auger_od"] / 2, zf1), 60, f"{mmi(zf1 - zo - 5)} FLIGHTED", "v")
    v.dim((-TJ["auger_od"] / 2, zo + 5), (-TJ["auger_od"] / 2, zo), 120, "5 BELOW OUTLET" if False else None, "v") if False else None
    v.leader((TJ["auger_od"] / 2, zo + 50), (90, zo + 80), [f"FLIGHT Ø{TJ['auger_od']:.0f} -0.1, pitch {TJ['pitch']:.0f}, RH", f"shaft Ø{TJ['shaft']:.0f}; clearance {C['clr_J']:.2f} radial"])
    v.leader((0, SPN["Z_cpl"] - 12), (60, SPN["Z_cpl"] + 30), ["M16 x 1.5 LH MALE x 25, shoulder Ø24", "face ⟂ 0.02 (screws into spindle 303)"])
    v.leader((TC25["fl"] / 2, zt - 3), (90, zt - 40), ["2.5 in TC ferrule face (to hopper 403)"])
    v.leader((TJ["tube_od"] / 2, zo + 2), (90, zo - 30), ["outlet: square cut, deburr, no lip"])
    # S set
    vs = S.view(1450, 300 + SPN["Z_cpl"] * s2 + 40, s2, "SET S: SHAKER (1:2)", (1200, 250))
    for sg in (-1, 1):
        vs.hatch([(sg * TS["tube_id"] / 2, zo), (sg * TS["tube_od"] / 2, zo), (sg * TS["tube_od"] / 2, zt - 25), (sg * TC25["od"] / 2, zt - 6), (sg * TC25["fl"] / 2, zt - 6),
                  (sg * TC25["fl"] / 2, zt), (sg * TC25["id"] / 2, zt), (sg * TS["tube_id"] / 2, zt - 25)], "hC")
    rr(vs, -5, zo + 5, 5, SPN["Z_cpl"] - 25, "vis", "#eceff1"); rr(vs, -8, SPN["Z_cpl"] - 25, 8, SPN["Z_cpl"], "vis", "#cfd8dc")
    for i in range(40):
        z = zo + 5 + i * TS["pitch"]
        if z + TS["pitch"] / 2 > zt + 30:
            break
        vs.line(-TS["auger_od"] / 2, z, TS["auger_od"] / 2, z + TS["pitch"] / 2); vs.line(-TS["auger_od"] / 2, z + TS["pitch"], TS["auger_od"] / 2, z + TS["pitch"] / 2, "thin")
    vs.centre(0, zo - 20, 0, SPN["Z_cpl"] + 20)
    vs.dim((-TS["tube_od"] / 2, zo), (TS["tube_od"] / 2, zo), -30, f"Ø{mmi(TS['tube_od'])} x 1.65", "h")
    vs.leader((TS["auger_od"] / 2, zo + 40), (70, zo + 80), [f"FLIGHT Ø{TS['auger_od']:.0f}, pitch {TS['pitch']:.0f}, shaft Ø{TS['shaft']:.0f}", f"clearance {C['clr_S']:.2f}; 25 cone tube to 2.5 TC"])
    # detail: top end and outlet (1:1)
    K1 = SC(1)
    vt = S.view(600, 1640, K1, "DETAIL U (1:1): AUGER TOP END, SET J", (200, 1390))
    rr(vt, -8, -80, 8, 0, "vis", "#eceff1"); rr(vt, -12, 0, 12, 6, "vis", "#cfd8dc"); rr(vt, -8, 6, 8, 31, "vis", "#cfd8dc")
    for i in range(16):
        vt.line(-8, 7 + i * 1.5, -7.2, 7.75 + i * 1.5, "thin"); vt.line(8, 7 + i * 1.5, 7.2, 7.75 + i * 1.5, "thin")
    vt.centre(0, -85, 0, 40)
    vt.dim((-12, 0), (12, 0), -30, "Ø24 SHOULDER", "h"); vt.dim((8, 6), (8, 31), -40, "25", "v"); vt.dim((12, 0), (12, 6), -100, "6", "v")
    vt.dim((-8, -60), (8, -60), -20, f"Ø{TJ['shaft']:.0f} SHAFT", "h")
    vt.leader((-8, 20), (-40, 45), ["M16 x 1.5 LH - 6g, chamfer 1 x 45°", "undercut 2 x 0.8 at the shoulder"], anchor="end")
    vt.fcf(20, -30, ["⊥", "0.02", "AXIS"]); vt.note(20, -45, ["shoulder face"], 11)
    vo = S.view(1400, 1780, K1, "DETAIL O (1:1): OUTLET, SET J", (1150, 1390))
    for sg in (-1, 1):
        vo.hatch([(sg * TJ["tube_id"] / 2, 0), (sg * TJ["tube_od"] / 2, 0), (sg * TJ["tube_od"] / 2, 80), (sg * TJ["tube_id"] / 2, 80)], "hC")
    rr(vo, -TJ["shaft"] / 2, 5, TJ["shaft"] / 2, 80, "vis", "#eceff1")
    for i in range(3):
        z = 5 + i * TJ["pitch"]
        vo.poly([(-TJ["auger_od"] / 2, z), (TJ["auger_od"] / 2, z + TJ["pitch"] / 2), (TJ["auger_od"] / 2, z + TJ["pitch"] / 2 + 2.5), (-TJ["auger_od"] / 2, z + 2.5)], "vis", True, "#cfd8dc")
    vo.dim((TJ["auger_od"] / 2, 5), (TJ["tube_od"] / 2, 5), 0, None, "h") if False else None
    vo.dim((TJ["tube_od"] / 2, 0), (TJ["tube_od"] / 2, 5), -40, "5", "v")
    vo.leader((TJ["auger_od"] / 2, 30), (60, 60), [f"radial clearance {C['clr_J']:.2f} [.030]", "flight edge square, Ra ≤ 0.8"])
    vo.leader((0, 0), (60, -25), ["optional: wire screen or spinner disc", "if the blend drips (trial)"])
    rows = []
    for k, c in CONT.items():
        r = C[k]
        rows.append((k, c["tool"], f"{c['g']:.1f}", f"{r['mL']:.0f}", f"{r['g_rev']:.2f}", f"{r['rev']:.1f}", f"{RPM[c['tool']]:.0f}", f"{r['t_dose']:.2f}", f"{r['stage']:.0f}"))
    S.table(2050, 300, [("CONTAINER", 130), ("SET", 50), ("NET g", 80), ("mL", 70), ("g / REV", 80), ("REVS", 70), ("RPM", 70), ("DOSE s", 80), ("STAGE", 70)], rows,
            f"DOSE TABLE (blend {RHO} g/mL, fill efficiency {FILL_EFF}; trim in calibration)", 13, 22)
    S.table(2050, 520, [("ITEM", 260), ("SET S", 180), ("SET J", 180)], [
        ("Tube OD x wall", f"{TS['tube_od']} x 1.65", f"{TJ['tube_od']} x 1.65"), ("Tube ID", f"{TS['tube_id']}", f"{TJ['tube_id']}"),
        ("Flight OD", f"{TS['auger_od']} -0.1", f"{TJ['auger_od']} -0.1"), ("Pitch", f"{TS['pitch']}", f"{TJ['pitch']}"), ("Shaft", f"{TS['shaft']}", f"{TJ['shaft']}"),
        ("Radial clearance", f"{C['clr_S']:.2f}", f"{C['clr_J']:.2f}"), ("Flight thickness", "2.5", "2.5"), ("Flight start above outlet", "5", "5"),
        ("Top thread", "M16 x 1.5 LH male", "M16 x 1.5 LH male"), ("Runout of flight OD", "≤ 0.15 TIR", "≤ 0.15 TIR"),
    ], "TOOLING DATA", 13, 22)
    S.notes(2050, 830, 1250, [
        "Supplier (All-Fill or equal) to quote with blend samples; confirm the fill efficiency and the clearance for a 0.54 g/mL free-flowing spice blend.",
        "All product-contact surfaces Ra ≤ 0.8 µm, flights continuously welded and polished, no crevices; 316 / 316L with material certs (3.1).",
        "Rotation when dosing: counter-clockwise seen from above. The RH flight then conveys down and the LH top thread self-tightens under load. Shoulder face seats on the spindle end.",
        "The tube is a separate part with the 2.5 in TC ferrule; it fits the hopper outlet 403 with clamp P1-445. Mark set S / J on the ferrule.",
        "Change-over: stop, lock out (Q1), clamp off, unscrew the auger (LH thread), tube down, fit the other set, set the stage stop (P1-401-700).",
    ], "REQUIREMENTS", 13)
    S.save(DWG / "P1-401-600_tooling_spec.svg")


if __name__ == "__main__":
    head_asm(); machined(); tooling()
    print("ok")
