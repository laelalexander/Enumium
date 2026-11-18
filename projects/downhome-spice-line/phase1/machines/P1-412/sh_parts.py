"""P1-412-100 base weldment, -200 carriage weldment, -300 spindle parts, -400 nest and clamp, -500 lever, link, stop."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
import model as M

SS = "#f4f6f8"
UH = "#fbfbf6"
PC = "#e3f2fd"
ZS = Z_SHELF_UP
ZD = z_shelf_down("shaker-250")


def R(v, x0, x1, y0, y1, k="vis", fill="none"):
    v.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0), k, fill)


def rect_pts(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rounded(x0, x1, y0, y1, r, n=8):
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# ====================================================================== 100 base weldment
def base():
    S = sheet("P1-412-100", "BASE WELDMENT", scale="1:3 · 1:2", material=SS304, finish=FIN_NPC,
              mass=kg("P1-412-101", "P1-412-102", "P1-412-103", "P1-412-104", "P1-412-105", "P1-412-106"))
    s3, s2 = SC(3), SC(2)
    # ---- front view of the weldment (1:3)
    v = S.view(530, 1250, s3, "FRONT (1:3)", (380, 230))
    R(v, -BASE["w"] / 2, BASE["w"] / 2, 0, BASE["t"], fill=SS)
    for sx in (-1, 1):
        v.poly([(sx * COL["a"] / 2, Z_COL0), (sx * (COL["a"] / 2 + GUS["a"]), Z_COL0), (sx * COL["a"] / 2, Z_COL0 + GUS["a"])], fill=SS)
    R(v, -COL["a"] / 2, COL["a"] / 2, Z_COL0, Z_COL1, fill=SS)
    R(v, -RSB["w"] / 2, RSB["w"] / 2, RSB["z0"], RSB["z0"] + RSB["L"], fill=SS)
    R(v, CAPPL["x0"], CAPPL["x1"], Z_COL1, Z_CAP, fill=SS)
    R(v, CLEV["x"], CLEV["x"] + CLEV["t"], Z_CAP, Z_CAP + CLEV["h"], fill=SS)
    for x, _ in M.BASE_HOLES[:2]:
        R(v, x - 4.5, x + 4.5, 0, BASE["t"], "hid")
    v.centre(0, -15, 0, Z_CAP + 20)
    v.dim((-BASE["w"] / 2, 0), (BASE["w"] / 2, 0), -40, None, "h")
    v.dim((-COL["a"] / 2 - GUS["a"], 0), (COL["a"] / 2 + GUS["a"], 0), -80, None, "h")
    v.dim((-BASE["w"] / 2, 0), (-BASE["w"] / 2, Z_COL1), 60, None, "v")
    v.dim((-BASE["w"] / 2, 0), (-BASE["w"] / 2, Z_CAP), 110, None, "v")
    v.dim((BASE["w"] / 2, 0), (BASE["w"] / 2, BASE["t"]), -30, None, "v")
    v.dim((RSB["w"] / 2, RSB["z0"]), (RSB["w"] / 2, RSB["z0"] + RSB["L"]), -150, f"SEAT BAR {mmi(RSB['L'])} FROM Z {mmi(RSB['z0'])}", "v")
    v.dim((CLEV["x"] + CLEV["t"], Z_CAP), (CLEV["x"] + CLEV["t"], PIV["z"]), -40, None, "v")
    v.dim((0, Z_CAP + 30), (PIV["x"], Z_CAP + 30), 40, None, "h")
    v.weld((COL["a"] / 2 + 30, Z_COL0 + 30), (180, 160), "fillet", "5", other="fillet", tail="W1 GUSSETS 2 SIDES")
    v.weld((-COL["a"] / 2, Z_COL0 + 2), (-180, 90), "fillet", "5", allround=True, tail="W2 COLUMN TO BASE")
    v.weld((RSB["w"] / 2, 400), (160, 420), "fillet", "4", length="25-100", tail="W3 SEAT BAR STITCH BOTH SIDES")
    v.weld((-COL["a"] / 2, Z_COL1 + 2), (-180, 700), "fillet", "4", allround=True, tail="W4 CAP")
    v.weld((CLEV["x"], Z_CAP + 3), (150, 760), "fillet", "5", other="fillet", tail="W5 CLEVIS")
    v.tag(-180, 360, 102, (-COL["a"] / 2, 360)); v.tag(170, 40, 101, (150, 6)); v.tag(-180, 160, 103, (-60, 40))
    v.tag(-120, 760, 104, (-20, Z_CAP)); v.tag(170, 700, 105, (CLEV["x"] + 4, Z_CAP + 30)); v.tag(170, 300, 106, (RSB["w"] / 2, 300))
    # ---- side view (1:3)
    vs = S.view(1130, 1250, s3, "SIDE (1:3), SEAT BAR FACE", (1000, 230))
    R(vs, BASE["y0"], BASE["y0"] + BASE["d"], 0, BASE["t"], fill=SS)
    R(vs, COL["y"] - COL["a"] / 2, COL["y"] + COL["a"] / 2, Z_COL0, Z_COL1, fill=SS)
    R(vs, COL["y"] - 3, COL["y"] + 3, Z_COL0, Z_COL0 + GUS["a"], fill=SS)
    R(vs, Y_RSB, Y_COLF, RSB["z0"], RSB["z0"] + RSB["L"], fill=SS)
    R(vs, CAPPL["y0"], CAPPL["y1"], Z_COL1, Z_CAP, fill=SS)
    vs.poly([(CLEV["y0"], Z_CAP), (CLEV["y1"], Z_CAP), (CLEV["y1"], Z_CAP + CLEV["h"] - 20), (CLEV["y1"] - 20, Z_CAP + CLEV["h"]), (CLEV["y0"] + 20, Z_CAP + CLEV["h"]),
             (CLEV["y0"], Z_CAP + CLEV["h"] - 20)], fill=SS)
    vs.circle(PIV["y"], PIV["z"], 5.1, "vis", "#fff")
    for k in range(int(RAIL["L"] // RAIL["pitch"])):
        z = RAIL["z0"] + RAIL["e"] + k * RAIL["pitch"]
        vs.line(Y_RSB, z, Y_RSB + 8, z, "hid")
    vs.dim((BASE["y0"], 0), (BASE["y0"] + BASE["d"], 0), -40, None, "h")
    vs.dim((BASE["y0"], 0), (Y_RSB, 0), -80, f"{mmi(Y_RSB - BASE['y0'], 1)} TO SEAT FACE (AXIS {mmi(-BASE['y0'])})", "h")
    vs.dim((CLEV["y0"], Z_CAP + CLEV["h"]), (PIV["y"], Z_CAP + CLEV["h"]), 30, None, "h")
    vs.dim((Y_RSB, RAIL["z0"]), (Y_RSB, RAIL["z0"] + RAIL["e"]), 60, None, "v")
    vs.leader((Y_RSB + 4, RAIL["z0"] + RAIL["e"] + 40), (-140, 520), ["12 x M3 x 8 DEEP AT 40 PITCH ON CL,", "DRILL AFTER FACING (RAIL AS JIG)"], 13)
    vs.finish((Y_RSB, 600), "1.6")
    vs.datum((Y_RSB, 200), "A", (-1, 0))
    vs.fcf(-140, 300, ["⏥", "0.05", ""])
    vs.text(-140, 280, "seat face A flat over 500 after welding", 11, "start")
    vs.fcf(-140, 240, ["//", "0.1", "C"]); vs.text(-140, 220, "A parallel to column side C", 11, "start")
    # ---- plan of the base plate (1:3) with hole table
    vp = S.view(2010, 870, s3, "BASE PLATE 101 (1:3), FROM ABOVE", (1840, 230))
    vp.poly(rounded(-BASE["w"] / 2, BASE["w"] / 2, BASE["y0"], BASE["y0"] + BASE["d"], 10), fill=SS)
    holes = [("A", d, M.BASE_HOLES, "Ø9 THRU (BENCH BOLTS)"), ("B", 6.8, M.VB_HOLES["S"] + M.VB_HOLES["J"] + M.GAS_HOLES, "M8 THRU (V-BLOCK S/J, GAS BKT)"),
             ("C", 5.0, M.TGL_HOLES + M.ENC_HOLES, "M6 THRU (CLAMP BKT, ENCLOSURE)"), ("D", 14.5, [(STOP["x"], STOP["y"])], "M16 x 1.5 THRU (STOP ROD)")] if (d := BASE["hole"]) else []
    rows = []
    for lab, dd, pts, desc in holes:
        for i, (x, y) in enumerate(pts):
            vp.circle(x, y, dd / 2, "vis", "#fff")
            vp.text(x + 8, y + 5, f"{lab}{i + 1}", 9, "start")
            rows.append((f"{lab}{i + 1}", f"{x:.1f}", f"{y:.1f}", desc))
    R(vp, -COL["a"] / 2, COL["a"] / 2, COL["y"] - COL["a"] / 2, COL["y"] + COL["a"] / 2, "phan")
    vp.cmark(0, 0, 10)
    vp.dim((-BASE["w"] / 2, BASE["y0"]), (BASE["w"] / 2, BASE["y0"]), -40, None, "h")
    vp.dim((BASE["w"] / 2, BASE["y0"]), (BASE["w"] / 2, BASE["y0"] + BASE["d"]), -40, None, "v")
    vp.text(0, -20, "ORIGIN = SPINDLE AXIS", 11, color=ms.CEN)
    S.table(2560, 230, [("HOLE", 55), ("X", 70), ("Y", 70), ("SIZE / USE", 300)], rows, "BASE PLATE HOLES (from the spindle axis)", 11, 20)
    # ---- flat parts (1:2): gusset, cap, clevis, seat bar end
    vg = S.view(1840, 1530, s2, "GUSSET 103 x 2 (1:2), 6 [.236]", (1780, 1330))
    vg.poly([(0, 0), (GUS["a"], 0), (0, GUS["a"])], fill=SS)
    vg.dim((0, 0), (GUS["a"], 0), -30, None, "h"); vg.dim((0, 0), (0, GUS["a"]), 30, None, "v")
    vc = S.view(2300, 1560, s2, "TOP CAP 104 (1:2), 6 [.236]", (2380, 1330))
    vc.poly(rect_pts(CAPPL["x0"], CAPPL["x1"], CAPPL["y0"], CAPPL["y1"]), fill=SS)
    R(vc, -COL["a"] / 2, COL["a"] / 2, COL["y"] - COL["a"] / 2, COL["y"] + COL["a"] / 2, "phan")
    vc.dim((CAPPL["x0"], CAPPL["y0"]), (CAPPL["x1"], CAPPL["y0"]), -30, None, "h"); vc.dim((CAPPL["x1"], CAPPL["y0"]), (CAPPL["x1"], CAPPL["y1"]), -30, None, "v")
    vk = S.view(1900, 1900, s2, "CLEVIS 105 (1:2), 8 [.315]", (1860, 1720))
    kp = [(CLEV["y0"], 0), (CLEV["y1"], 0), (CLEV["y1"], CLEV["h"] - 20), (CLEV["y1"] - 20, CLEV["h"]), (CLEV["y0"] + 20, CLEV["h"]), (CLEV["y0"], CLEV["h"] - 20)]
    vk.poly([(y - CLEV["y0"], z) for y, z in kp], fill=SS)
    vk.circle(PIV["y"] - CLEV["y0"], PIV["z"] - Z_CAP, 5.1, "vis", "#fff")
    vk.dim((0, 0), (CLEV["y1"] - CLEV["y0"], 0), -30, None, "h"); vk.dim((0, 0), (0, CLEV["h"]), 30, None, "v")
    vk.dia(PIV["y"] - CLEV["y0"], PIV["z"] - Z_CAP, 5.1, 45, (PIV["y"] - CLEV["y0"] + 40, PIV["z"] - Z_CAP + 30), "Ø10.2 [.402] REAM")
    vk.dim((0, PIV["z"] - Z_CAP), (PIV["y"] - CLEV["y0"], PIV["z"] - Z_CAP), 0, None, "h") if False else None
    S.table(120, 1530, [("PART", 120), ("DESCRIPTION", 330), ("STOCK", 300), ("CUT SIZE", 260), ("DXF", 220)], [
        ("P1-412-101", "Base plate", "304 plate 12 [.472]", f"{BASE['w']:.0f} x {BASE['d']:.0f} R10 corners", "P1-412-101_base"),
        ("P1-412-102", "Column", "304 sq tube 2 x 2 in x 11 ga", f"{COL['L']:.0f} long, ends square", "saw"),
        ("P1-412-103", "Gussets (2)", "304 plate 6 [.236]", f"{GUS['a']:.0f} x {GUS['a']:.0f} triangle", "P1-412-103_gusset"),
        ("P1-412-104", "Top cap", "304 plate 6 [.236]", f"{CAPPL['x1'] - CAPPL['x0']:.0f} x {CAPPL['y1'] - CAPPL['y0']:.0f}", "P1-412-104_cap"),
        ("P1-412-105", "Clevis plate", "304 plate 8 [.315]", f"{CLEV['y1'] - CLEV['y0']:.0f} x {CLEV['h']:.0f}, Ø10.2 ream after weld", "P1-412-105_clevis"),
        ("P1-412-106", "Rail seat bar", "304 flat 30 x 12 (face to 10)", f"{RSB['L']:.0f} long", "saw + mill"),
    ], "CUT LIST", 12, 22)
    S.notes(120, 1720, 1600, [
        "Weld sequence: W2 column to base (tack 4 corners, check square to the base 0.5 / 600 both ways), W1 gussets, W4 cap, W5 clevis, W3 seat bar stitches alternating sides.",
        "After welding: mill seat face A flat 0.05 over 500 and parallel to the column side 0.1; ream the clevis Ø10.2 square to the column side; drill/tap M3 x 12 on CL using the rail.",
        "Tap base holes after welding (B M8, C M6, D M16 x 1.5); check the stop-rod hole D square to the base.",
        "Column left face (-x): 2 x M4 stainless rivnut for the limit switch P1-452, set at assembly against the carriage plate top (carriage up), see P1-412-003.",
        "Break all edges 0.5; #4 brush; passivate. Column top cap weld ground smooth (lever swings over it).",
    ], "FABRICATION NOTES", fs=13)
    dxf_profile(str(DXF / "P1-412-101_base"), rounded(-BASE["w"] / 2, BASE["w"] / 2, BASE["y0"], BASE["y0"] + BASE["d"], 10),
                holes=[(x, y, BASE["hole"] / 2) for x, y in M.BASE_HOLES] + [(x, y, 3.4) for x, y in M.VB_HOLES["S"] + M.VB_HOLES["J"] + M.GAS_HOLES]
                + [(x, y, 2.5) for x, y in M.TGL_HOLES + M.ENC_HOLES] + [(STOP["x"], STOP["y"], 7.25)], text="P1-412-101 BASE 12 304 (TAP B M8, C M6, D M16x1.5)")
    dxf_profile(str(DXF / "P1-412-103_gusset"), [(0, 0), (GUS["a"], 0), (0, GUS["a"])], text="P1-412-103 GUSSET 6 304 x2")
    dxf_profile(str(DXF / "P1-412-104_cap"), rect_pts(CAPPL["x0"], CAPPL["x1"], CAPPL["y0"], CAPPL["y1"]), text="P1-412-104 CAP 6 304")
    dxf_profile(str(DXF / "P1-412-105_clevis"), [(y - CLEV["y0"], z) for y, z in kp], holes=[(PIV["y"] - CLEV["y0"], PIV["z"] - Z_CAP, 4.5)], text="P1-412-105 CLEVIS 8 304 (REAM 10.2)")
    S.save(DWG / "P1-412-100_base_weldment.svg")


# ====================================================================== 200 carriage weldment
def carriage():
    S = sheet("P1-412-200", "CARRIAGE WELDMENT", scale="1:2 · 1:1", material=SS304, finish=FIN_NPC,
              mass=kg("P1-412-201", "P1-412-202", "P1-412-203", "P1-412-204"))
    s2 = SC(2)
    zs = 0.0                                              # drawn with the shelf underside at 0
    # ---- front view (looking +y) 1:2
    v = S.view(720, 900, s2, "FRONT (1:2)", (620, 230))
    R(v, CAR["sh_x0"], CAR["sh_x1"], 0, CAR["sh_t"], fill=SS)
    R(v, -CAR["w"] / 2, CAR["w"] / 2, CAR["sh_t"], CAR["sh_t"] + CAR["h"], "hid")
    for x in (-50, 50):
        R(v, x - 3, x + 3, CAR["sh_t"], CAR["sh_t"] + CAR["gus"], fill=SS)
    R(v, CAR["lug_x"] - 5, CAR["lug_x"] + 5, CAR["sh_t"], Z_LUGPIN + 15, fill=SS)
    v.circle(CAR["lug_x"], Z_LUGPIN, 4.1, "hid")
    R(v, -MOTOR_BORE / 2, MOTOR_BORE / 2, 0, CAR["sh_t"], "hid")
    v.centre(0, -20, 0, CAR["sh_t"] + CAR["h"] + 20)
    v.dim((CAR["sh_x0"], 0), (CAR["sh_x1"], 0), -40, None, "h")
    v.dim((0, CAR["sh_t"] + CAR["h"]), (CAR["lug_x"], CAR["sh_t"] + CAR["h"]), 30, None, "h")
    v.dim((CAR["lug_x"] + 5, 0), (CAR["lug_x"] + 5, Z_LUGPIN), -50, None, "v")
    v.dim((-50, CAR["sh_t"] + CAR["gus"]), (50, CAR["sh_t"] + CAR["gus"]), 70, None, "h")
    v.weld((-CAR["w"] / 2, CAR["sh_t"]), (-200, 120), "fillet", "4", other="fillet", tail="W1 PLATE TO SHELF")
    v.weld((-47, 40), (-200, 60), "fillet", "3", other="fillet", tail="W2 GUSSETS")
    v.weld((CAR["lug_x"] - 5, CAR["sh_t"] + 2), (190, 90), "fillet", "4", other="fillet", tail="W3 LUG")
    v.tag(-170, -40, 202, (-80, 5)); v.tag(-170, 200, 201, (-55, 150)); v.tag(170, 200, 204, (CAR["lug_x"], Z_LUGPIN + 10)); v.tag(170, -40, 203, (50, 30))
    # ---- side view (y horizontal) 1:2 with block hole pattern on the plate face
    vs = S.view(1330, 900, s2, "SIDE (1:2)", (1300, 230))
    R(vs, SHELF_Y0, Y_BLK, 0, CAR["sh_t"], fill=SS)
    R(vs, Y_BLK - CAR["t"], Y_BLK, CAR["sh_t"], CAR["sh_t"] + CAR["h"], fill=SS)
    vs.poly([(Y_BLK - CAR["t"], CAR["sh_t"]), (Y_BLK - CAR["t"] - CAR["gus"], CAR["sh_t"]), (Y_BLK - CAR["t"], CAR["sh_t"] + CAR["gus"])], fill=SS)
    vs.poly(rect_pts(CAR["lug_y"] - 15, CAR["lug_y"] + 15, CAR["sh_t"], Z_LUGPIN + 15), fill=SS)
    vs.circle(CAR["lug_y"], Z_LUGPIN, 4.1, "vis", "#fff")
    vs.centre(0, -20, 0, CAR["sh_t"] + CAR["h"] + 20)
    vs.dim((SHELF_Y0, 0), (Y_BLK, 0), -40, None, "h")
    vs.dim((0, 0), (Y_BLK, 0), -80, f"{mmi(Y_BLK)} AXIS TO FACE B", "h", tol="±0.05")
    vs.dim((Y_BLK, CAR["sh_t"]), (Y_BLK, CAR["sh_t"] + CAR["h"]), -40, None, "v")
    vs.dim((Y_BLK, 0), (Y_BLK, CAR["sh_t"] + CAR["h"] / 2), -90, f"{mmi(CAR['sh_t'] + CAR['h'] / 2)} TO BLOCK CL", "v")
    vs.datum((Y_BLK, 120), "B", (1, 0))
    vs.finish((Y_BLK, 160), "1.6")
    vs.leader((Y_BLK, CAR["sh_t"] + CAR["h"] / 2 + BLK["C"] / 2), (140, 230), [f"4 x Ø3.4 THRU ON {BLK['B']:.0f} x {BLK['C']:.0f} (MGN15H)", "CBORE Ø6.5 x 3.5 FROM THE REAR"], 13)
    vs.fcf(-120, -30, ["⊥", "0.05", "B"]); vs.text(-120, -50, "shelf top / motor bore axis to B", 11, "start")
    # ---- shelf plan 1:2 with hole table
    vp = S.view(2350, 900, s2, "SHELF 202 (1:2), FROM ABOVE", (2200, 230))
    sp = rounded(CAR["sh_x0"], CAR["sh_x1"], SHELF_Y0, Y_BLK + 15, 15)
    vp.poly([(x, min(y, Y_BLK)) for x, y in sp], fill=SS)
    rows = []
    for lab, d, pts, desc in (("M", MOTOR_BORE, [(0.0, 0.0)], "Ø30.00 H8 THRU (motor pilot)"), ("F", 5.0, M.MOT_HOLES, f"Ø5.0 THRU (10-32 motor, PCD {GM['pcd']:.0f})"),
                              ("G", 4.2, M.GRD_HOLES, "M5 THRU (guard standoffs)"), ("S", 6.8, [(GAS["x"], GAS["y"])], "M8 THRU (gas spring ball stud)")):
        for i, (x, y) in enumerate(pts):
            vp.circle(x, y, d / 2, "vis", "#fff"); vp.text(x + d / 2 + 4, y + 4, f"{lab}{i + 1}", 9, "start")
            rows.append((f"{lab}{i + 1}", f"{x:.1f}", f"{y:.1f}", desc))
    R(vp, -CAR["w"] / 2, CAR["w"] / 2, Y_BLK - CAR["t"], Y_BLK, "phan")
    vp.circle(0, 0, GM["pcd"] / 2, "cen")
    vp.dim((CAR["sh_x0"], SHELF_Y0), (CAR["sh_x1"], SHELF_Y0), -40, None, "h"); vp.dim((CAR["sh_x1"], SHELF_Y0), (CAR["sh_x1"], Y_BLK), -40, None, "v")
    S.table(1900, 1300, [("HOLE", 55), ("X", 70), ("Y", 70), ("SIZE / USE", 330)], rows, "SHELF HOLES (from the spindle axis)", 11, 20)
    # ---- vertical plate 201 (1:2), lug 204 (1:1)
    vv = S.view(400, 1700, s2, "PLATE 201 (1:2), 10 [.394], SEEN FROM THE RAIL", (420, 1330))
    vv.poly(rect_pts(-CAR["w"] / 2, CAR["w"] / 2, 0, CAR["h"]), fill=SS)
    for dx in (-BLK["B"] / 2, BLK["B"] / 2):
        for dz in (-BLK["C"] / 2, BLK["C"] / 2):
            vv.circle(dx, CAR["h"] / 2 + dz, 1.7, "vis", "#fff"); vv.circle(dx, CAR["h"] / 2 + dz, 3.25, "hid")
    vv.dim((-CAR["w"] / 2, 0), (CAR["w"] / 2, 0), -30, None, "h"); vv.dim((CAR["w"] / 2, 0), (CAR["w"] / 2, CAR["h"]), -30, None, "v")
    vv.dim((-BLK["B"] / 2, CAR["h"] / 2 + BLK["C"] / 2), (BLK["B"] / 2, CAR["h"] / 2 + BLK["C"] / 2), 40, None, "h")
    vl = S.view(950, 1720, SC(1), "LUG 204 (1:1), 10 [.394]", (950, 1330))
    vl.poly(rect_pts(-15, 15, 0, Z_LUGPIN + 15 - CAR["sh_t"]), fill=SS); vl.circle(0, Z_LUGPIN - CAR["sh_t"], 4.1, "vis", "#fff")
    vl.dim((-15, 0), (15, 0), -30, None, "h"); vl.dim((15, 0), (15, Z_LUGPIN + 15 - CAR["sh_t"]), -30, None, "v")
    vl.dim((-15, 0), (-15, Z_LUGPIN - CAR["sh_t"]), 30, None, "v")
    S.notes(1250, 1600, 600, [
        "Weld W1-W3 in a fixture; then machine: face B (block face) flat 0.02, drill/cbore the 4 block holes, then bore the motor pilot Ø30 H8 ⊥ 0.05 to B at 73.6 ±0.05 from B.",
        "Shelf top flat 0.1 under the motor face. Lug hole Ø8.2 square to B.",
        "Mass of the carriage with motor, clutch, chuck and guard ≈ 11.8 kg (116 N); gas spring 200 N lifts it with ≈ 85 N to spare.",
    ], "MACHINING", fs=12)
    S.table(1900, 1720, [("PART", 120), ("DESCRIPTION", 200), ("STOCK", 230), ("SIZE", 200)], [
        ("P1-412-201", "Plate", "304 plate 10", f"{CAR['w']:.0f} x {CAR['h']:.0f}"),
        ("P1-412-202", "Shelf", "304 plate 10", f"{CAR['sh_x1'] - CAR['sh_x0']:.0f} x {Y_BLK - SHELF_Y0:.1f}"),
        ("P1-412-203", "Gussets (2)", "304 plate 6", f"{CAR['gus']:.0f} x {CAR['gus']:.0f} triangle"),
        ("P1-412-204", "Link lug", "304 plate 10", f"30 x {Z_LUGPIN + 15 - CAR['sh_t']:.0f}"),
    ], "CUT LIST", 12, 22)
    dxf_profile(str(DXF / "P1-412-202_shelf"), [(x, min(y, Y_BLK)) for x, y in sp], holes=[(0, 0, 14.5)] + [(x, y, 2.5) for x, y in M.MOT_HOLES]
                + [(x, y, 2.1) for x, y in M.GRD_HOLES] + [(GAS["x"], GAS["y"], 3.4)], text="P1-412-202 SHELF 10 304 (BORE 30 H8 AFTER WELD; TAP G M5, S M8)")
    dxf_profile(str(DXF / "P1-412-201_plate"), rect_pts(-CAR["w"] / 2, CAR["w"] / 2, 0, CAR["h"]), text="P1-412-201 PLATE 10 304 (DRILL BLOCK HOLES AFTER WELD)")
    dxf_profile(str(DXF / "P1-412-203_gusset"), [(0, 0), (CAR["gus"], 0), (0, CAR["gus"])], text="P1-412-203 GUSSET 6 304 x2")
    dxf_profile(str(DXF / "P1-412-204_lug"), rect_pts(-15, 15, 0, Z_LUGPIN + 15 - CAR["sh_t"]), holes=[(0, Z_LUGPIN - CAR["sh_t"], 4.1)], text="P1-412-204 LUG 10 304")
    S.save(DWG / "P1-412-200_carriage_weldment.svg")


# ====================================================================== 300 spindle parts
def spindle():
    S = sheet("P1-412-300", "SPINDLE PARTS", scale="2:1 · 1:1 · 1:2", material="304 bar; PC guard", finish="machined Ra 1.6",
              mass=kg("P1-412-301", "P1-412-302", "P1-412-303", "P1-412-304"))
    s1 = SC(1)
    # stub shaft 301 (1:1), axis horizontal
    v = S.view(260, 520, SC(0.5), "STUB SHAFT 301 (2:1), 304 Ø25 BAR", (520, 230))
    L1, L2 = 30.0, STUB["spig_L"]
    R(v, 0, L1, -STUB["d"] / 2, STUB["d"] / 2, fill=SS)
    R(v, L1, L1 + STUB["collar_t"], -STUB["collar_d"] / 2, STUB["collar_d"] / 2, fill=SS)
    R(v, L1 + STUB["collar_t"], L1 + STUB["collar_t"] + L2, -STUB["spig_d"] / 2, STUB["spig_d"] / 2, fill=SS)
    v.line(0, STUB["d"] / 2 - 1.5, L1, STUB["d"] / 2 - 1.5, "thin")               # flat for the clutch set screws
    R(v, L1 + STUB["collar_t"] + 6, L1 + STUB["collar_t"] + L2 - 6, STUB["spig_d"] / 2 - 2, STUB["spig_d"] / 2, "thin")   # float flat 2 deep (set screw rides)
    v.centre(-10, 0, L1 + STUB["collar_t"] + L2 + 10, 0)
    v.dim((0, -STUB["d"] / 2), (L1, -STUB["d"] / 2), -40, None, "h")
    v.dim((L1, -STUB["collar_d"] / 2), (L1 + STUB["collar_t"], -STUB["collar_d"] / 2), -70, None, "h")
    v.dim((L1 + STUB["collar_t"], -STUB["spig_d"] / 2), (L1 + STUB["collar_t"] + L2, -STUB["spig_d"] / 2), -40, None, "h")
    v.dim((0, -STUB["d"] / 2), (0, STUB["d"] / 2), 40, "Ø12.70 h6 [.500]", "v")
    v.dim((L1 + 3, -STUB["collar_d"] / 2), (L1 + 3, STUB["collar_d"] / 2), -150, None, "v")
    v.dim((L1 + STUB["collar_t"] + L2, -STUB["spig_d"] / 2), (L1 + STUB["collar_t"] + L2, STUB["spig_d"] / 2), -30, "Ø16 g6", "v")
    v.leader((15, STUB["d"] / 2 - 1.5), (20, 30), ["FLAT 1.5 DEEP x 30 (CLUTCH SET SCREWS)"], 12)
    v.leader((L1 + 20, STUB["spig_d"] / 2 - 1), (60, 22), ["FLAT 2 DEEP x 18 (FLOAT SLOT: ADAPTER SET SCREW)"], 12)
    # chuck adapter 302 (1:1) section
    va = S.view(1300, 520, s1, "CHUCK ADAPTER 302 (1:1), SECTION, 304 Ø115 BAR", (1300, 230))
    hr = CHK["d"] / 2; ip = INSERT["J"]["id_bot"] / 2 + 4
    for sg in (-1, 1):
        va.poly([(sg * STUB["spig_d"] / 2, 20), (sg * hr, 20), (sg * hr, CHK["h"]), (sg * STUB["spig_d"] / 2, CHK["h"])], fill="url(#hA)")
        va.poly([(sg * ip, 0), (sg * hr, 0), (sg * hr, 20), (sg * ip, 20)], fill="url(#hA)")
    va.line(-STUB["spig_d"] / 2, 20, STUB["spig_d"] / 2, 20, "vis")
    va.line(-ip, 20, ip, 20, "vis")
    R(va, 8, 14, CHK["h"] - 14, CHK["h"] - 8, "vis", "#fff")
    for a in (90, 210, 330):
        pass
    va.centre(0, -10, 0, CHK["h"] + 10)
    va.dim((-hr, 0), (hr, 0), -40, f"Ø{mmi(CHK['d'])}", "h")
    va.dim((-ip, 0), (ip, 0), -80, f"Ø{mmi(2 * ip)} H9 POCKET", "h")
    va.dim((-STUB["spig_d"] / 2, CHK["h"]), (STUB["spig_d"] / 2, CHK["h"]), 30, "Ø16 H8", "h")
    va.dim((hr, 0), (hr, CHK["h"]), -40, None, "v"); va.dim((hr, 0), (hr, 20), -90, None, "v")
    va.leader((11, CHK["h"] - 11), (90, 70), ["M6 SET SCREW (H12) RADIAL AT 12 BELOW TOP,", "RIDES IN THE STUB FLOAT FLAT"], 12)
    va.leader((-hr, 10), (-90, -75), ["3 x M5 RADIAL AT 120° ON Z 10", "(INSERT SET SCREWS)"], 12)
    # guard 303 (1:2) + standoff 304 (1:1)
    s2 = SC(2)
    vg = S.view(2500, 600, s2, "GUARD 303 (1:2): PC TUBE Ø150 x 3 + PC RING 6, SOLVENT-BONDED", (2400, 230))
    for sg in (-1, 1):
        R(vg, sg * (GUARD["d"] / 2 - GUARD["t"]), sg * GUARD["d"] / 2, 0, GUARD["h"] - 16, fill=PC)
        R(vg, sg * (GUARD["d"] / 2 - GUARD["t"]), sg * (GUARD["r_bolt"] + 10), GUARD["h"] - 16, GUARD["h"] - 10, fill=PC)
    vg.dim((-GUARD["d"] / 2, 0), (GUARD["d"] / 2, 0), -40, f"Ø{mmi(GUARD['d'])} OD", "h")
    vg.dim((-GUARD["r_bolt"] - 10, GUARD["h"] - 10), (GUARD["r_bolt"] + 10, GUARD["h"] - 10), 30, f"RING Ø{mmi(2 * GUARD['r_bolt'] + 20)}", "h")
    vg.dim((GUARD["d"] / 2, 0), (GUARD["d"] / 2, GUARD["h"] - 10), -40, None, "v")
    vg.note(-120, -60, [f"3 x Ø5.5 ON R{GUARD['r_bolt']:.0f} AT -90 / 30 / 150° (Y TOWARD THE COLUMN)", "PC tube cut square, edges flame-polished"], 12)
    vso = S.view(2450, 1000, SC(0.5), "STANDOFF 304 x 3 (2:1), 304 Ø10 BAR", (2450, 840))
    R(vso, -5, 5, 0, 10, fill=SS); vso.line(-2.75, 0, -2.75, 10, "hid"); vso.line(2.75, 0, 2.75, 10, "hid")
    vso.dim((-5, 0), (5, 0), -30, "Ø10", "h"); vso.dim((5, 0), (5, 10), -30, None, "v")
    # chuck adapter end view from below: radial holes
    ve = S.view(1300, 1040, s1, "CHUCK ADAPTER 302 (1:1), VIEW FROM BELOW", (1300, 770))
    ve.circle(0, 0, hr, "vis"); ve.circle(0, 0, ip, "vis"); ve.circle(0, 0, STUB["spig_d"] / 2, "hid")
    for a in (90, 210, 330):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        ve.line(ip * ca, ip * sa, hr * ca, hr * sa, "cen")
        ve.line((ip) * ca - 2.1 * sa, ip * sa + 2.1 * ca, hr * ca - 2.1 * sa, hr * sa + 2.1 * ca, "hid")
        ve.line((ip) * ca + 2.1 * sa, ip * sa - 2.1 * ca, hr * ca + 2.1 * sa, hr * sa - 2.1 * ca, "hid")
    ve.centre(-hr - 10, 0, hr + 10, 0); ve.centre(0, -hr - 10, 0, hr + 10)
    ve.leader((hr * math.cos(math.radians(330)), hr * math.sin(math.radians(330))), (90, -40), ["3 x M5 THRU WALL AT 90 / 210 / 330°, Z 10 FROM FACE"], 12)
    # guard ring plan
    vr = S.view(2500, 1500, s2, "GUARD RING 303 (1:2), PC 6 [.236], PLAN", (2500, 1290))
    vr.circle(0, 0, GUARD["r_bolt"] + 10, "vis"); vr.circle(0, 0, GUARD["d"] / 2 - GUARD["t"], "vis")
    vr.circle(0, 0, GUARD["r_bolt"], "cen")
    for x, y in M.GRD_HOLES:
        vr.circle(x, y, 2.75, "vis")
    vr.dim((-(GUARD["r_bolt"] + 10), -GUARD["r_bolt"] - 10), (GUARD["r_bolt"] + 10, -GUARD["r_bolt"] - 10), -30, None, "h")
    vr.leader((M.GRD_HOLES[0][0], M.GRD_HOLES[0][1]), (110, -70), [f"3 x Ø5.5 [.217] THRU ON R{GUARD['r_bolt']:.0f}", f"BORE Ø{GUARD['d'] - 2 * GUARD['t']:.0f} (tube bonds inside)"], 12)
    S.table(120, 1420, [("PART", 120), ("DESCRIPTION", 260), ("STOCK", 300), ("OPERATIONS", 640)], [
        ("P1-412-301", "Stub shaft", "304 round Ø25 x 75", "turn Ø12.70 h6, collar Ø22, spigot Ø16 g6; mill 2 flats"),
        ("P1-412-302", "Chuck adapter", "304 round Ø115 x 50", "turn Ø112, pocket Ø100 H9 x 20, bore Ø16 H8; drill/tap 1 x M6 + 3 x M5 radial"),
        ("P1-412-303", "Guard", "PC tube Ø150 x 3 + PC sheet 6", "cut tube 84; laser ring Ø190 / Ø144, 3 x Ø5.5; bond"),
        ("P1-412-304", "Standoffs (3)", "304 round Ø10 x 12", "turn 10 long, drill Ø5.5 thru"),
    ], "CUT LIST AND OPERATIONS", 12, 22)
    S.notes(120, 1600, 1500, [
        "Run-out of the chuck face to the stub Ø12.70: 0.1 TIR, assembled on the clutch (ITP T7).",
        "Chuck adapter slides 12 on the spigot against the float spring (P1-423 kit); the set screw only keys rotation, so the slot must be free: no Loctite in the set screw thread tip.",
        "Urethane inserts are bought to suit the actual caps: confirm with 10 caps of each size before ordering 2 spares each.",
    ], "NOTES", fs=13)
    dxf_profile(str(DXF / "P1-412-303_guard_ring"),
                [((GUARD["r_bolt"] + 10) * math.cos(math.radians(a * 5)), (GUARD["r_bolt"] + 10) * math.sin(math.radians(a * 5))) for a in range(72)],
                holes=[(0, 0, GUARD["d"] / 2 - GUARD["t"])] + [(x, y, 2.75) for x, y in M.GRD_HOLES], text="P1-412-303 GUARD RING PC 6")
    S.save(DWG / "P1-412-300_spindle_parts.svg")


# ====================================================================== 400 nest and clamp
def nest():
    S = sheet("P1-412-400", "NEST AND CLAMP PARTS", scale="1:1", material="UHMW-PE natural FDA; 304 bracket", finish="machined; bracket #4",
              mass=kg("P1-412-401", "P1-412-402", "P1-412-403", "P1-412-404"))
    s2 = SC(1)
    vn = S.view(560, 660, s2, "NEST PLATE 401 (1:1), UHMW 8 [.315]", (560, 300))
    npts = rounded(-95, 110, -70, 70, 8)
    vn.poly(npts, fill=UH)
    rows = []
    for k in ("S", "J"):
        for i, (x, y) in enumerate(M.VB_HOLES[k]):
            vn.circle(x, y, 5, "vis", "#fff"); vn.text(x + 8, y + 4, f"{k}{i + 1}", 9, "start"); rows.append((f"{k}{i + 1}", f"{x:.1f}", f"{y:.1f}", "Ø10 THRU (V-block bolts, clearance)"))
    vn.circle(0, 0, JAR["d"] / 2 if (JAR := CONT["jar-12"]) else 0, "phan"); vn.circle(0, 0, CONT["shaker-250"]["d"] / 2, "phan"); vn.cmark(0, 0, 10)
    vn.dim((-95, -70), (110, -70), -40, None, "h"); vn.dim((110, -70), (110, 70), -40, None, "v"); vn.dim((-95, 70), (0, 70), 30, None, "h")
    S.table(120, 1060, [("HOLE", 55), ("X", 70), ("Y", 70), ("SIZE", 260)], rows, "NEST HOLES (from the axis)", 11, 20)
    # V-block
    xf = 0.0
    vv = S.view(1380, 660, s2, "V-BLOCK 402 (1:1), UHMW 60 [2.362] THICK, PLAN", (1450, 300))
    vpts = [(0, -VB["L"] / 2), (VB["t"], -VB["L"] / 2), (VB["t"], VB["L"] / 2), (0, VB["L"] / 2), (0, VB["depth"]), (VB["depth"], 0), (0, -VB["depth"])]
    vv.poly(vpts, fill=UH)
    for y in (-35.0, 35.0):
        vv.circle(VB_BOLT_DX, y, 4.5, "vis", "#fff"); vv.circle(VB_BOLT_DX, y, 7.5, "hid")
    vv.dim((0, -VB["L"] / 2), (VB["t"], -VB["L"] / 2), -40, None, "h"); vv.dim((VB["t"], -VB["L"] / 2), (VB["t"], VB["L"] / 2), -40, None, "v")
    vv.dim((0, VB["L"] / 2), (VB["depth"], VB["L"] / 2), 30, None, "h"); vv.dim((0, -VB["depth"]), (0, VB["depth"]), 30, None, "v")
    vv.dim((0, 35), (VB_BOLT_DX, 35), 70, None, "h")
    vv.angle((VB["depth"], 0), 18, 135, 225, "90°")
    vv.leader((VB_BOLT_DX + 3, 38), (110, 80), ["2 x Ø9 THRU, CSK Ø16 x 90° FOR M8 x 70 (H6)", f"HEIGHT {VB['h']:.0f} [{fin(VB['h'])}]"], 12)
    # pad
    vpd = S.view(2900, 660, s2, "CLAMP PAD 403 (1:1), UHMW 20, PLAN", (2900, 300))
    pp = [(-PAD["t"], -PAD["w"] / 2), (0, -PAD["w"] / 2), (0, -16), (-8, 0), (0, 16), (0, PAD["w"] / 2), (-PAD["t"], PAD["w"] / 2)]
    vpd.poly(pp, fill=UH)
    vpd.dim((-PAD["t"], -PAD["w"] / 2), (0, -PAD["w"] / 2), -30, None, "h"); vpd.dim((0, -PAD["w"] / 2), (0, PAD["w"] / 2), -30, None, "v")
    vpd.dim((0, -16), (0, 16), -70, None, "v")
    vpd.leader((-PAD["t"], 0), (-80, 40), ["M10 TAPPED 15 DEEP (TOGGLE SPINDLE)", f"HEIGHT {PAD['h']:.0f}"], 12)
    # bracket
    vb = S.view(1250, 1560, s2, "CLAMP BRACKET 404 (1:1), 304 6 [.236], FLAT PATTERN", (1500, 1330))
    flat = rect_pts(0, 70 + 70 - 6, -30, 30)
    vb.poly(flat, fill=SS)
    vb.line(64, -30, 64, 30, "bend")
    for x, y in M.TGL_HOLES:
        vb.circle(x + 195, y, 3.3, "vis", "#fff")
    vb.dim((0, -30), (134, -30), -40, None, "h"); vb.dim((134, -30), (134, 30), -30, None, "v")
    vb.text(70, 38, "BEND UP 90°, IR 6", 11, color=ms.DIM)
    vb.note(0, -80, ["4 x Ø6.6 to the base (C holes); toggle clamp 603-M: drill its 4 holes on the upright from the clamp (confirm)"], 12)
    # V-block elevation from the container side (x = model y, y = z)
    ve = S.view(2050, 1060, s2, "V-BLOCK 402 (1:1), VIEW ON THE V FACE", (2050, 745))
    ve.rect(-VB["L"] / 2, 0, VB["L"], VB["h"], fill=UH)
    for yy in (-VB["depth"], VB["depth"]):
        ve.line(yy, 0, yy, VB["h"], "vis")
    ve.line(0, 0, 0, VB["h"], "thin")
    for yy in (-35.0, 35.0):
        ve.line(yy - 4.5, 0, yy - 4.5, VB["h"] - 3.5, "hid"); ve.line(yy + 4.5, 0, yy + 4.5, VB["h"] - 3.5, "hid")
        ve.line(yy - 4.5, VB["h"] - 3.5, yy - 8, VB["h"], "hid"); ve.line(yy + 4.5, VB["h"] - 3.5, yy + 8, VB["h"], "hid")
        ve.centre(yy, -6, yy, VB["h"] + 6)
    ve.dim((VB["L"] / 2, 0), (VB["L"] / 2, VB["h"]), -40, None, "v"); ve.dim((-VB["L"] / 2, 0), (VB["L"] / 2, 0), -40, None, "h")
    ve.dim((-VB["depth"], VB["h"]), (VB["depth"], VB["h"]), 30, "V OPENING 80 [3.150]", "h")
    ve.note(-VB["L"] / 2, -30, ["V faces machined Ra 3.2, edges 1 x 45°; bolts from the top, heads sunk flush"], 11)
    # bracket bent, side view
    vk = S.view(2350, 1600, s2, "CLAMP BRACKET 404 BENT (1:1), SIDE", (2450, 1330))
    vk.poly([(0, 0), (70, 0), (70, 70), (64, 70), (64, 6), (0, 6)], fill=SS)
    vk.dim((0, 0), (70, 0), -40, None, "h"); vk.dim((70, 0), (70, 70), -40, None, "v"); vk.dim((0, 6), (0, 0), 30, None, "v")
    vk.note(-20, -40, ["upright faces the container: toggle spindle on Y = 0, Z 50 (set with the clamp)"], 11)
    S.table(120, 1500, [("PART", 120), ("DESCRIPTION", 200), ("STOCK", 260), ("SIZE", 300)], [
        ("P1-412-401", "Nest plate", "UHMW 8", "205 x 140, R8"),
        ("P1-412-402", "V-block", "UHMW 60", f"{VB['t']:.0f} x {VB['L']:.0f} x {VB['h']:.0f}, 90° V {VB['depth']:.0f} deep"),
        ("P1-412-403", "Clamp pad", "UHMW 20", f"{PAD['w']:.0f} x {PAD['h']:.0f}, 90° V 8 deep"),
        ("P1-412-404", "Clamp bracket", "304 sheet 6", "134 x 60 flat, 1 bend"),
    ], "CUT LIST", 12, 22)
    dxf_profile(str(DXF / "P1-412-401_nest"), npts, holes=[(x, y, 5.0) for x, y in M.VB_HOLES["S"] + M.VB_HOLES["J"]], text="P1-412-401 NEST UHMW 8")
    dxf_profile(str(DXF / "P1-412-402_vblock"), vpts, holes=[(VB_BOLT_DX, y, 4.5) for y in (-35.0, 35.0)], text="P1-412-402 V-BLOCK UHMW 60 (CSK)")
    dxf_profile(str(DXF / "P1-412-403_pad"), pp, text="P1-412-403 PAD UHMW 20")
    dxf_profile(str(DXF / "P1-412-404_bracket_flat"), flat, holes=[(x + 195, y, 3.3) for x, y in M.TGL_HOLES], bends=[((64, -30), (64, 30))], text="P1-412-404 BRACKET 6 304")
    S.save(DWG / "P1-412-400_nest_clamp.svg")


# ====================================================================== 500 lever, link, stop
def lever():
    S = sheet("P1-412-500", "LEVER, LINK AND STOP", scale="1:2 · 2:1", material=SS304, finish=FIN_NPC,
              mass=kg("P1-412-501", "P1-412-502", "P1-412-503", "P1-412-504", "P1-412-505"))
    s2, s1 = SC(2), SC(1)
    L = LEV["L"] + 25
    v = S.view(1600 - L * s2 / 2, 520, s2, "HAND LEVER 501 (1:2), 304 FLAT 25 x 10", (1600, 230))
    lp = rect_pts(0, L + 20, -LEV["w"] / 2, LEV["w"] / 2)
    v.poly(lp, fill=SS)
    for x, d, lab in ((L + 20 - 25 - LEV["L"] + LEV["L"], 0, ""),):
        pass
    xp = L + 20 - 25                                         # pivot 25 from the rear end; handle end at 0 + 20
    for x, r in ((xp, 5.1), (xp - LEV["a"], 4.1), (20.0, 4.25)):
        v.circle(x, 0, r, "vis", "#fff"); v.cmark(x, 0, r)
    v.dim((0, -LEV["w"] / 2), (L + 20, -LEV["w"] / 2), -40, None, "h")
    v.dim((xp - LEV["a"], LEV["w"] / 2), (xp, LEV["w"] / 2), 30, None, "h")
    v.dim((20, LEV["w"] / 2), (xp, LEV["w"] / 2), 70, None, "h")
    v.leader((xp + 4, 4), (xp + 60, 50), ["Ø10.2 PIVOT (H9 SHOULDER BOLT)"], 12)
    v.leader((xp - LEV["a"] + 3, 3), (xp - LEV["a"] + 40, 60), ["Ø8.2 LINK PIN"], 12)
    v.leader((20, 4), (60, 60), ["M10 x 15 TAPPED IN THE END FACE? NO: Ø8.5 THRU, TAP M10 (KNOB DIN 319)"], 12) if False else v.leader((20, 4), (60, 60), ["Ø8.5 THRU, TAP M10 (KNOB P1-453)"], 12)
    v.rad(L + 20, 0, LEV["w"] / 2, 0, (L + 40, -30), "R12.5 BOTH ENDS")
    # link rod
    vl = S.view(1600 - LINK["L"] * s2 / 2, 820, s2, f"LINK ROD 502 (1:2), 304 Ø10, ROD ENDS M8 BOTH ENDS, {mmi(LINK['L'], 1)} CENTRES", (1600, 700))
    R(vl, 18, LINK["L"] - 18, -5, 5, fill=SS)
    for x in (0.0, LINK["L"]):
        vl.circle(x, 0, 9, "vis", "#cfd8dc"); vl.circle(x, 0, 4, "thin", "#fff")
    vl.dim((0, -12), (LINK["L"], -12), -30, f"{mmi(LINK['L'], 1)} PIN CENTRES (SET WITH THE ROD ENDS)", "h")
    vl.dim((18, 5), (LINK["L"] - 18, 5), 30, None, "h")
    vl.note(20, -60, ["Thread M8 x 20 both ends (one LH + one RH so the length adjusts by turning the rod), jam nuts"], 12)
    # stop rod + flip stop + gas bracket
    vs = S.view(520, 1700, s2, "STOP ROD 503 (1:2), 304 Ø16", (560, 1110))
    Ls = ZD + 25.0
    R(vs, -8, 8, 0, Ls, fill=SS)
    vs.line(-8, 25, 8, 25, "thin")
    vs.dim((8, 0), (8, 25), -30, "M16 x 1.5 x 25", "v"); vs.dim((-8, 0), (-8, Ls), 40, None, "v")
    vs.leader((0, Ls - 10), (40, Ls - 20), ["Ø6 CROSS HOLE 10 BELOW TOP (FLIP PIN)", "TOP FACE GROUND SQUARE"], 12)
    vf = S.view(1000, 1600, SC(0.5), "FLIP STOP 504 (2:1), 304 BAR 30 x 24", (1130, 1180))
    R(vf, 0, 30, 0, STOP["flip_t"], fill=SS)
    vf.circle(15, STOP["flip_t"] - 5, 3.1, "vis", "#fff")
    vf.dim((0, 0), (30, 0), -30, None, "h"); vf.dim((30, 0), (30, STOP["flip_t"]), -30, f"{mmi(STOP['flip_t'], 1)} ±0.1", "v")
    R(vf, 45, 69, 0, STOP["flip_t"], fill=SS); vf.line(45, STOP["flip_t"] - 8.1, 69, STOP["flip_t"] - 8.1, "hid"); vf.line(45, STOP["flip_t"] - 1.9, 69, STOP["flip_t"] - 1.9, "hid")
    vf.dim((45, 0), (69, 0), -30, None, "h")
    vf.note(-10, -30, ["Ø6.2 pivot hole; swings on a Ø6 pin through the rod", "top face lands on the shelf (jar stop)"], 12)
    vgb = S.view(1800, 1450, SC(0.5), "GAS SPRING BRACKET 505 (2:1), SIDE + PLAN", (1800, 1180))
    R(vgb, -30, 30, 0, 4, fill=SS); R(vgb, -8, 8, 4, GAS["z_lo"] - BASE["t"], fill=SS)
    for x in (-20, 20):
        vgb.line(x - 4.5, 0, x - 4.5, 4, "hid"); vgb.line(x + 4.5, 0, x + 4.5, 4, "hid")
    vgb.dim((-30, 0), (30, 0), -30, None, "h"); vgb.dim((30, 0), (30, GAS["z_lo"] - BASE["t"]), -30, None, "v")
    vp5 = S.view(1800, 1700, SC(0.5))
    R(vp5, -30, 30, -12, 12, fill=SS); vp5.circle(0, 0, 8, "vis"); vp5.circle(0, 0, 3.4, "hid")
    for x in (-20, 20):
        vp5.circle(x, 0, 4.5, "vis", "#fff")
    vp5.dim((-20, -12), (20, -12), -30, "2 x Ø9 [.354] ON 40", "h"); vp5.dim((30, -12), (30, 12), -30, None, "v")
    vp5.note(-30, -32, ["plate 60 x 24 x 4 + Ø16 boss drilled/tapped M8 for the ball stud; 2 x Ø9 on 40"], 12)
    S.table(2200, 1300, [("PART", 120), ("STOCK", 230), ("SIZE", 300)], [
        ("P1-412-501", "304 flat 25 x 10", f"{L + 20:.0f} long, R12.5 ends"),
        ("P1-412-502", "304 round Ø10", f"{LINK['L'] - 36:.0f} long + 2 rod ends"),
        ("P1-412-503", "304 round Ø16", f"{Ls:.1f} long"),
        ("P1-412-504", "304 bar 30 x 24", f"{STOP['flip_t']:.1f} long"),
        ("P1-412-505", "304 plate 4 + Ø16 bar", "60 x 24 + boss 8 long, welded"),
    ], "CUT LIST", 12, 22)
    S.notes(2200, 1500, 1100, [
        f"Lever swing ±{TH0:.1f}° about horizontal gives the {STROKE_MAX:.1f} stroke; hand force ≈ {calcs()['F_hand']:.0f} N at the knob.",
        "Set the link length so the shelf just touches the stop rod with the lever 1-2° above its lowest; the gas spring holds the carriage up at its full extension.",
    ], "NOTES", fs=12)
    dxf_profile(str(DXF / "P1-412-501_lever"), lp, holes=[(xp, 0, 5.1), (xp - LEV["a"], 0, 4.1), (20.0, 0, 4.25)], text="P1-412-501 LEVER 10 304")
    S.save(DWG / "P1-412-500_lever_link_stop.svg")


if __name__ == "__main__":
    base(); carriage(); spindle(); nest(); lever()
