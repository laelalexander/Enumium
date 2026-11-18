"""P1-404-100 frame, -200 drive parts, -300 web path parts, -400 peel plate and idler arm parts (+ DXF cut files)."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
import model as M

C = calcs()
SS = "#f4f6f8"
UH = "#fbfbf6"
XL0, XL1, XR0, XR1 = M.XL0, M.XL1, M.XR0, M.XR1


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


def turned(v, segs, fill=SS):
    """axis horizontal along view x; segs = [(x0, x1, d)]"""
    for x0, x1, d in segs:
        R(v, x0, x1, -d / 2, d / 2, fill=fill)
    v.centre(segs[0][0] - 8, 0, segs[-1][1] + 8, 0)


# ====================================================================== 100 frame
def frame():
    S = sheet("P1-404-100", "FRAME PARTS", scale="1:3 · 1:2", material=SS304, finish=FIN_NPC,
              mass=kg("P1-404-101", "P1-404-102", "P1-404-103", "P1-404-104", "P1-404-105"))
    s3, s2 = SC(3), SC(2)
    # base plate
    vb = S.view(520, 560, s3, "BASE PLATE 101 (1:3), 304 8 [.315], FROM ABOVE", (520, 150))
    outer = rounded(-BASE["w"] / 2, BASE["w"] / 2, BASE["y0"], BASE["y0"] + BASE["d"], 10.0)
    vb.poly(outer, fill=SS)
    rows = []
    groups = [("A", BASE["hole"], M.BASE_HOLES, "Ø7 THRU (BENCH M6)"),
              ("B", 5.5, [(sx * SP["x"], y) for sx in (-1, 1) for y in M.SP_SCREWS], "Ø5.5 THRU, CBORE Ø10 x 5.5 FROM BELOW (SIDE PLATES)"),
              ("C", 4.2, M.FENCE_HOLES["shaker-250"] + M.FENCE_HOLES["jar-12"], "M5 THRU (FENCE S / J)"),
              ("D", 5.0, M.ENC_HOLES, "M6 THRU (ENCLOSURE)")]
    dxf_holes = []
    for g, d, pts, use in groups:
        for i, (x, y) in enumerate(pts):
            vb.circle(x, y, d / 2, "vis", "#fff"); vb.text(x + 6, y + 6, f"{g}{i + 1}", 8, "start")
            rows.append((f"{g}{i + 1}", f"{x:.1f}", f"{y:.1f}", use)); dxf_holes.append((x, y, d / 2))
    vb.cmark(0, 0, 14); vb.text(0, -18, "LABEL CENTRE x 0 / ROLLER MID y 0", 9, color=ms.CEN)
    vb.dim((-BASE["w"] / 2, BASE["y0"]), (BASE["w"] / 2, BASE["y0"]), -40, None, "h")
    vb.dim((BASE["w"] / 2, BASE["y0"]), (BASE["w"] / 2, BASE["y0"] + BASE["d"]), -40, None, "v")
    S.table(1100, 160, [("HOLE", 55), ("X", 70), ("Y", 70), ("SIZE / USE", 420)], rows, "BASE HOLES (from the label centre)", 11, 19)
    dxf_profile(str(DXF / "P1-404-101_base"), outer, holes=dxf_holes, text="P1-404-101 BASE 8 304 (TAP C M5, D M6)")
    # -x side plate
    vl = S.view(2100, 1120, s3, "SIDE PLATE 102 (1:3), 304 10 [.394], SEEN FROM +X", (2150, 150))
    vl.poly(M.SPL_PTS, fill=SS)
    pl_rows = []
    feats = [("R", 28.0, [(-ROL["y"], ROL["z"]), (ROL["y"], ROL["z"])], "Ø28 H7 THRU (6001, ROLLERS)"),
             ("M", 38.5, [(MOT["y"], MOT["z"])], "Ø38.5 THRU (MOTOR PILOT, ±3 SLIDE)"),
             ("MS", 5.5, M.MOT_SLOTS, "SLOT 5.5 x 11.5 VERTICAL (MOTOR M5)"),
             ("H", 40.0, [(LD["y"], LD["z"]), (REW["y"], REW["z"])], "Ø40 H8 THRU (HOUSING SPIGOTS)"),
             ("HS", 5.5, M.ldh_holes(LD["y"], LD["z"]) + M.ldh_holes(REW["y"], REW["z"]), "SLOT 5.5 x 8 RADIAL (HOUSING M5)"),
             ("U", 25.0, [(UNW["y"], UNW["z"])], "Ø25 H8 THRU (UNWIND SPINDLE)"),
             ("UT", 4.2, M.UNW_HOLES, "M4 THRU ON PCD 44 (SPINDLE FLANGE)"),
             ("P", 16.0, [(IDL["piv_y"], IDL["piv_z"])], "Ø16 H9 THRU (ARM PIVOT SHAFT, M8 END)"),
             ("G", 8.5, [(G1["y"], G1["z"])], "Ø8.5 THRU (GUIDE SHAFT M8)"),
             ("L", 8.0, [(PINCH["piv_y"], PINCH["piv_z"])], "Ø8 H8 THRU (PINCH PIVOT)"),
             ("T", 8.5, [(M.TIE["y"], M.TIE["z"])], "Ø8.5 THRU (TIE M8)"),
             ("PS", 4.2, M.PEEL_HOLES["S"], "M5 THRU (PEEL BRACKET, SETTING S)"),
             ("PJ", 4.2, M.PEEL_HOLES["J"], "M5 THRU (PEEL BRACKET, SETTING J)"),
             ("E", 4.2, [(y, BASE["t"]) for y in M.SP_SCREWS], "M5 x 15 DEEP IN THE BOTTOM EDGE")]
    dl = []
    for g, d, pts, use in feats:
        for i, (y, z) in enumerate(pts):
            if g != "E":
                vl.circle(y, z, d / 2, "vis", "#fff"); dl.append((y, z, d / 2))
            else:
                vl.line(y - 2.1, z, y - 2.1, z + 15, "hid"); vl.line(y + 2.1, z, y + 2.1, z + 15, "hid")
            pl_rows.append((f"{g}{i + 1}", f"{y:.1f}", f"{z:.1f}", use))
    vl.dim((SPL["y0"], BASE["t"]), (SPL["y1"], BASE["t"]), -40, None, "h"); vl.dim((SPL["y1"], BASE["t"]), (SPL["y1"], SPL["z1"]), -40, None, "v")
    vl.dim((110.0, SPL["z1"]), (SPL["y1"], SPL["z1"]), 25, None, "h"); vl.dim((SPL["y0"], BASE["t"]), (SPL["y0"], 200.0), 40, None, "v")
    S.table(1100, 700, [("HOLE", 55), ("Y", 70), ("Z", 70), ("SIZE / USE (y from the roller mid, z from the bench top)", 520)], pl_rows, "SIDE PLATE 102 HOLES", 11, 19)
    dxf_profile(str(DXF / "P1-404-102_sideplate_drive"), M.SPL_PTS, holes=dl, text="P1-404-102 SIDE PLATE 10 304 (REAM H7/H8 AFTER CUT)")
    # +x side plate
    vr = S.view(180 + 100 * s3, 1880, s3, "SIDE PLATE 103 (1:3), 304 10", (330, 1380))
    vr.poly(M.SPR_PTS, fill=SS)
    dr = [(-ROL["y"], ROL["z"], 14.0), (ROL["y"], ROL["z"], 14.0), (IDL["piv_y"], IDL["piv_z"], 8.0), (M.TIE["y"], M.TIE["z"], 4.25),
          (IDL["piv_y"] - 50.0, IDL["piv_z"] - 12.0, 6.1)]
    for y, z, r in dr:
        vr.circle(y, z, r, "vis", "#fff")
    vr.dim((SPR["y0"], BASE["t"]), (SPR["y1"], BASE["t"]), -40, None, "h"); vr.dim((SPR["y1"], BASE["t"]), (SPR["y1"], SPR["z1"]), -40, None, "v")
    vr.note(SPR["y0"], -80, ["Same hole positions as 102 for R, P, T; M12 x 1 hole for the start sensor at (70, 233);", "3 x M5 x 15 in the bottom edge."], 11)
    dxf_profile(str(DXF / "P1-404-103_sideplate_free"), M.SPR_PTS, holes=dr, text="P1-404-103 SIDE PLATE 10 304")
    # tie + fence
    vt = S.view(820, 1950, s2, "TIE ROD 104 (1:2), 304 Ø16", (900, 1700))
    L = XR0 - XL1
    turned(vt, [(0, L, M.TIE["d"])])
    for x in (0, L):
        vt.line(x + (12 if x == 0 else -12), -4, x + (12 if x == 0 else -12), 4, "hid")
    vt.dim((0, -8), (L, -8), -40, None, "h"); vt.note(0, 20, ["M8 x 12 DEEP BOTH ENDS; ends square 0.05 (sets the plate spacing)"], 11)
    vf = S.view(1550, 1950, s2, "END FENCE 105 (1:2), UHMW 8", (1600, 1700))
    vf.poly([(0, 0), (40, 0), (40, 8), (8, 8), (8, FENCE["h"]), (0, FENCE["h"])], fill=UH)
    vf.dim((0, 0), (40, 0), -30, None, "h"); vf.dim((0, 0), (0, FENCE["h"]), 30, None, "v")
    vf.note(50, 30, [f"30 wide; 2 x Ø5.5 in the foot at 8 / 20 from the toe; S x {fence_x('shaker-250'):.1f}, J x {fence_x('jar-12'):.1f} (face)"], 11)
    S.notes(120, 1080, 900, [
        "Base: laser cut, deburr; tap C (M5) and D (M6); counterbore B from below so the base sits flat on the bench.",
        "Side plates: laser cut 0.3 under, then bore the R, H, U, P holes together on a mill from one datum (y 0 = roller mid, z 0 = base underside): positional Ø0.05.",
        "Both side plates must give parallel roller axes: 0.05 over 320 (ITP T3); the tie rod and the pivot shaft set the 310 spacing.",
        "Break edges 0.5; #4 brush; passivate.",
    ], "NOTES", fs=12)
    S.save(DWG / "P1-404-100_frame.svg")


# ====================================================================== 200 drive
def drive():
    S = sheet("P1-404-200", "DRIVE PARTS", scale="1:1 · 1:2", material="304 bar / sheet; UHMW pinch roller", finish="machined Ra 1.6",
              mass=kg("P1-404-201", "P1-404-202", "P1-404-203", "P1-404-204"))
    s1, s2 = SC(1), SC(2)
    vh = S.view(380, 520, s1, "BEARING HOUSING 201 x 2 (1:1), SECTION, 304 Ø75 BAR", (480, 150))
    for sg in (-1, 1):
        vh.poly([(0, sg * 14), (40, sg * 14), (40, sg * 20), (6, sg * 20), (6, sg * 35), (-10, sg * 35), (-10, sg * 20), (-10, sg * 14)], fill="url(#hA)")
    vh.line(-10, -20, -10, 20, "vis"); vh.line(40, -14, 40, 14, "vis"); vh.centre(-20, 0, 50, 0)
    vh.dim((-10, -35), (6, -35), -40, None, "h"); vh.dim((-10, -20), (40, -20), -80, None, "h")
    vh.dim((40, -20), (40, 20), -40, "Ø40 g6", "v"); vh.dim((-10, -14), (-10, 14), 40, "Ø28 H7", "v"); vh.dim((6, -35), (6, 35), -60, "Ø70", "v")
    vh.note(-10, 60, ["2 x 6001-2RS back to back, DIN 472 Ø28 each end; spigot Ø40 g6 x 10 into the plate (H8);", "3 x Ø5.5 on PCD 58 at 90 / 210 / 330°"], 11)
    ve = S.view(380, 1000 - 400 + 300, s1, "HOUSING 201 END VIEW (1:1)", (480, 780))
    ve.circle(0, 0, 35, "vis", SS); ve.circle(0, 0, 20, "hid"); ve.circle(0, 0, 14, "vis", "#fff"); ve.circle(0, 0, 29, "cen")
    for a in (90, 210, 330):
        ve.circle(29 * math.cos(math.radians(a)), 29 * math.sin(math.radians(a)), 2.75, "vis", "#fff")
    ve.cmark(0, 0, 40)
    ve.leader((29 * math.cos(math.radians(330)), 29 * math.sin(math.radians(330))), (60, -50), ["3 x Ø5.5 THRU on PCD 58, 90 / 210 / 330°"], 11)
    vr = S.view(1150, 520, s1, "LINER DRIVE ROLLER 202 (1:1), 304 Ø35 BAR", (1350, 150))
    segs = [(0, 12.0, 12.0), (12.0, 22.0, 11.0), (22.0, 70.0, 12.0), (70.0, 70.0 + LD["x1"] - LD["x0"], LD["d"])]
    turned(vr, segs)
    for x0, x1, d in segs[:-1]:
        vr.dim((x0, -d / 2), (x1, -d / 2), -35 - (x0 > 0) * 25, None, "h")
    vr.dim((70, -LD["d"] / 2), (70 + LD["x1"] - LD["x0"], -LD["d"] / 2), -50, None, "h")
    vr.dim((70 + LD["x1"] - LD["x0"], -LD["d"] / 2), (70 + LD["x1"] - LD["x0"], LD["d"] / 2), -40, f"Ø{LD['d']:.0f} h8, DIAMOND KNURL 0.8", "v")
    vr.leader((6, 6), (-20, 40), ["Ø12 h6: O-RING PULLEY + 18T PULLEY, FLAT 0.5 FOR SET SCREWS"], 11)
    vr.leader((46, 6), (60, 40), ["Ø12 h6 IN THE HOUSING BEARINGS, DIN 471 GROOVES"], 11)
    vp = S.view(500, 1500, SC(0.5), "PINCH LEVER 203 (2:1), 304 6 + Ø8 SHAFT + UHMW ROLLER Ø20", (500, 1180))
    py, pz = PINCH["piv_y"], PINCH["piv_z"]; ry, rz = LD["y"], LD["z"] + LD["d"] / 2 + PINCH["d"] / 2 + 0.2
    lp = [(py + 8 - py, pz + 8 - pz), (ry - 8 - py, rz + 8 - pz), (ry - 8 - py, rz - 8 - pz), (py + 8 - py, pz - 8 - pz)]
    lp = [(-a, b) for a, b in lp]
    vp.poly(lp, fill=SS); vp.circle(0, 0, 4, "vis", "#fff"); vp.circle(-(ry - py), rz - pz, 4, "vis", "#fff"); vp.circle(-(ry - py), rz - pz, PINCH["d"] / 2, "phan")
    vp.circle(-(ry - py) / 2, (rz - pz) / 2, 2.6, "vis", "#fff")
    vp.dim((0, -12), (-(ry - py), -12), -25, None, "h")
    vp.leader((-3, -3), (-25, -30), ["Ø8 H8 PIVOT"], 11); vp.leader((-(ry - py) + 3, rz - pz - 3), (-(ry - py) + 20, -30), ["Ø8 H7, SHAFT PRESSED"], 11)
    vp.leader((-(ry - py) / 2, (rz - pz) / 2 + 2.6), (-(ry - py) / 2 + 20, 30), ["Ø5.2 SPRING EYE"], 11)
    vp.note(-20, -48, ["Ø8 H8 pivot on a shoulder screw; Ø5.2 eye for the 20 N spring (P1-458) to the plate pin;", f"roller centre {abs(rz - pz):.1f} below the pivot; Ø8 shaft 140 long pressed in, UHMW roller Ø20 x 120 free on it, DIN 471 Ø8"], 11)
    dxf_profile(str(DXF / "P1-404-203_pinch_lever"), lp, holes=[(0, 0, 4.0), (-(ry - py), rz - pz, 4.0), (-(ry - py) / 2, (rz - pz) / 2, 2.6)], text="P1-404-203 PINCH LEVER 6 304")
    # belt guard flat
    vg = S.view(1300, 1400, s2, "BELT GUARD 204 (1:2), 304 1.5, FLAT PATTERN", (1500, 860))
    W_, H_, D_ = 255.0, 150.0, 55.0
    fp = [(0, D_), (W_, D_), (W_, D_ + H_), (0, D_ + H_)]
    flat = [(0, 0), (W_, 0), (W_, D_), (W_ + D_, D_), (W_ + D_, D_ + H_), (W_, D_ + H_), (W_, 2 * D_ + H_), (0, 2 * D_ + H_), (0, D_ + H_), (-D_, D_ + H_), (-D_, D_), (0, D_)]
    vg.poly(flat, fill=SS)
    for a, b in (((0, D_), (W_, D_)), ((0, D_ + H_), (W_, D_ + H_)), ((0, D_), (0, D_ + H_)), ((W_, D_), (W_, D_ + H_))):
        vg.line(*a, *b, "bend")
    for (x, y) in ((20, 10), (W_ - 20, 10), (W_ / 2, 2 * D_ + H_ - 10)):
        vg.circle(x, y, 2.25, "vis", "#fff")
    vg.dim((0, 0), (W_, 0), -30, None, "h"); vg.dim((W_ + D_, D_), (W_ + D_, D_ + H_), -30, None, "v"); vg.dim((-D_, D_), (0, D_), 30, None, "h")
    vg.note(-D_, -50, ["4 bends 90° up, IR 1.5; corners closed by the flanges; 3 x Ø4.5 tabs to standoffs on the plate (H12)"], 11)
    dxf_profile(str(DXF / "P1-404-204_guard_flat"), flat, holes=[(20, 10, 2.25), (W_ - 20, 10, 2.25), (W_ / 2, 2 * D_ + H_ - 10, 2.25)],
                bends=[((0, D_), (W_, D_)), ((0, D_ + H_), (W_, D_ + H_)), ((0, D_), (0, D_ + H_)), ((W_, D_), (W_, D_ + H_))], text="P1-404-204 GUARD 1.5 304")
    # roller spec (bought, to this drawing)
    vR = S.view(2200, 520, SC(2), "VIEW R: DRIVE ROLLER P1-425 (1:2), BOUGHT TO THIS DRAWING", (2400, 150))
    segs = [(0, 45.0, 12.0), (45.0, 45.0 + ROL["face"], ROL["d"]), (45.0 + ROL["face"], 45.0 + ROL["face"] + 20.0, 12.0)]
    turned(vR, segs, "#ffe0b2")
    vR.dim((0, -6), (45, -6), -60, None, "h"); vR.dim((45, -25), (45 + ROL["face"], -25), -40, None, "h"); vR.dim((45 + ROL["face"], -6), (65 + ROL["face"], -6), -60, None, "h")
    vR.dim((65 + ROL["face"], -6), (65 + ROL["face"], 6), -30, "Ø12 h6", "v"); vR.dim((45, -25), (45, 25), 60, "Ø50 ±0.05", "v")
    vR.note(0, 50, ["Urethane 70A 6 thick on a 304 tube, ground; run-out 0.05 TIR; drive end (-x) 45 long with 3 x 0.5 flat;", "both rollers matched to ±0.05 on Ø so the container does not walk"], 11)
    S.table(1900, 1500, [("PART", 120), ("STOCK", 300), ("OPERATIONS", 600)], [
        ("P1-404-201", "304 round Ø75 x 52 (x2)", "turn spigot Ø40 g6, bore Ø28 H7 + 2 ring grooves, drill 3 x Ø5.5"),
        ("P1-404-202", "304 round Ø35 x 260", "turn Ø30 h8 face 180, Ø12 h6 journals, knurl, mill 2 flats"),
        ("P1-404-203", "304 plate 6 + Ø8 rod 140 + UHMW Ø25", "laser lever, press shaft, turn roller Ø20 x 120 bore Ø8.2"),
        ("P1-404-204", "304 sheet 1.5", "laser flat, 4 bends, #4"),
    ], "CUT LIST AND OPERATIONS", 12, 22)
    S.save(DWG / "P1-404-200_drive.svg")


# ====================================================================== 300 web path
def web():
    S = sheet("P1-404-300", "WEB PATH PARTS", scale="1:2 · 1:1", material="304 bar; UHMW-PE", finish="machined",
              mass=kg("P1-404-301", "P1-404-302", "P1-404-303", "P1-404-304", "P1-404-305", "P1-404-306", "P1-404-307"))
    s1, s2 = SC(1), SC(2)
    vs = S.view(200, 520, s2, "UNWIND SPINDLE 301 (1:2), 304 Ø65 + Ø25", (450, 150))
    Lsp = 85.0 - XL1
    turned(vs, [(0, 8.0, 60.0), (8.0, Lsp, 25.0)])
    vs.line(-SP["t"], -12.5, 0, -12.5, "phan"); vs.line(-SP["t"], 12.5, 0, 12.5, "phan")
    vs.dim((0, -30), (8, -30), -30, None, "h"); vs.dim((8, -12.5), (Lsp, -12.5), -70, None, "h"); vs.dim((Lsp, -12.5), (Lsp, 12.5), -40, "Ø25 g6", "v")
    vs.dim((0, -30), (0, 30), 40, "Ø60", "v")
    vs.note(0, 60, [f"spigot Ø25 g6 x 10 into the plate (U hole); flange 3 x Ø4.5 on PCD 44; spindle end M8 x 15 (collar stop)"], 11)
    vh = S.view(200, 1200, s2, "CORE HUB 302 (1:2), UHMW, UNWIND / REWIND", (400, 820))
    R(vh, -6, 0, -UNW["flange_d"] / 2, UNW["flange_d"] / 2, fill=UH)
    R(vh, 0, 140, -(UNW["hub_d"] / 2 - 0.4), UNW["hub_d"] / 2 - 0.4, fill=UH)
    vh.line(-6, -12.6, 140, -12.6, "hid"); vh.line(-6, 12.6, 140, 12.6, "hid"); vh.centre(-14, 0, 150, 0)
    vh.dim((0, -UNW["hub_d"] / 2), (140, -UNW["hub_d"] / 2), -40, None, "h"); vh.dim((140, -37.6), (140, 37.6), -40, "Ø75.2 (3 in CORE, SLIP FIT)", "v")
    vh.dim((-6, -UNW["flange_d"] / 2), (-6, UNW["flange_d"] / 2), 40, None, "v")
    vh.note(0, -130, ["Unwind: bore Ø25.2 runs free on the spindle; flange Ø220 x 6 faces the felt brake.",
                      "Rewind: no flange, bore Ø12 H8 + M5 set screw on the shaft flat; 2 x 3 slot 40 long to tuck the liner end."], 11)
    vc = S.view(1000, 520, s1, "CORE COLLAR 303 x 2 (1:1), UHMW Ø50", (1100, 150))
    R(vc, 0, 20, -25, 25, fill=UH); vc.line(0, -12.6, 20, -12.6, "hid"); vc.line(0, 12.6, 20, 12.6, "hid")
    vc.dim((0, -25), (20, -25), -30, None, "h"); vc.dim((20, -25), (20, 25), -40, "Ø50", "v")
    vc.note(0, 45, ["bore Ø25.2 (unwind) / Ø12.2 (rewind) + M5 radial thumb screw; knurled OD"], 11)
    vb = S.view(1080, 1250, s1, "BRAKE LEAF 304 (1:1), 304 SPRING 0.8 + FELT", (1150, 820))
    lp = [(0, 0), (30, 0), (30, 70), (0, 70)]
    vb.poly(lp, fill=SS); R(vb, 0, 30, 0, 30, "thin", "#d7ccc8"); vb.circle(15, 60, 2.25, "vis", "#fff")
    vb.dim((0, 0), (30, 0), -30, None, "h"); vb.dim((30, 0), (30, 70), -30, None, "v")
    vb.note(-10, -45, ["bent 15° at 40; felt 30 x 30 x 5 bonded; drag set by the bend: label roll must not overrun on stop"], 11)
    dxf_profile(str(DXF / "P1-404-304_brake_leaf"), lp, holes=[(15, 60, 2.25)], text="P1-404-304 BRAKE 0.8 304 SPRING")
    vw = S.view(1700, 520, s1, "REWIND SHAFT 305 (1:1), 304 Ø16", (1850, 150))
    Lr = 75.0 - (X_ORING - 8.0)
    turned(vw, [(0, 12.0, 12.0), (12.0, 70.0, 12.0), (70.0, Lr, 12.0)])
    vw.dim((0, -6), (Lr, -6), -40, None, "h"); vw.dim((Lr, -6), (Lr, 6), -30, "Ø12 h6", "v")
    vw.note(0, 25, ["O-ring pulley at 0-12, bearings in housing 201 at 22-62, hub from 70; 2 flats 0.5; 2 DIN 471 grooves"], 11)
    vo = S.view(1800, 1200, SC(0.5), "O-RING PULLEY 306 x 2 (2:1), UHMW Ø45, SECTION", (1850, 820))
    for sg in (-1, 1):
        vo.poly([(0, sg * 6), (12, sg * 6), (12, sg * 22.5), (8.6, sg * 22.5), (6, sg * 17.4), (3.4, sg * 22.5), (0, sg * 22.5)], fill="url(#hA)")
    vo.centre(-6, 0, 18, 0); vo.line(0, -6, 0, 6, "vis"); vo.line(12, -6, 12, 6, "vis")
    vo.dim((0, 22.5), (12, 22.5), 25, None, "h"); vo.dim((12, -22.5), (12, 22.5), -25, "Ø45", "v"); vo.dim((0, -17.4), (0, 17.4), 20, "Ø34.8 GROOVE ROOT", "v")
    vo.dim((0, -6), (0, 6), 45, "Ø12 H8", "v")
    vo.leader((6, 17.6), (30, 30), ["R2.6 GROOVE, PITCH Ø40, FOR Ø5 PU BELT"], 11)
    vo.note(-10, -32, ["bore Ø12 H8 + M4 set screw; 1:1 ratio: rewind overspeeds and slips on the round belt"], 11)
    vg = S.view(2500, 520, s1, "GUIDE ROLLER + SHAFT 307 (1:1)", (2600, 150))
    turned(vg, [(0, 12.0, 8.0), (12.0, 22.0, 16.0), (22.0, 22.0 + 130.0 + 5.0, 10.0)])
    R(vg, 27.0, 157.0, -G1["d"] / 2, G1["d"] / 2, "thin", UH)
    vg.dim((0, -4), (12, -4), -40, "M8", "h"); vg.dim((27, -10), (157, -10), -40, None, "h"); vg.dim((157, -10), (157, 10), -30, "Ø20 UHMW", "v")
    vg.note(0, 30, ["304 shaft Ø10, collar Ø16 against the plate, M8 nut behind (H11); UHMW sleeve Ø20 x 130 bore Ø10.3 free; DIN 471 Ø10"], 11)
    S.table(1900, 1550, [("PART", 120), ("STOCK", 320), ("OPERATIONS", 600)], [
        ("P1-404-301", "304 round Ø65 x 250", "turn flange Ø60 x 8, spindle Ø25 g6, spigot; drill 3 x Ø4.5; tap M8"),
        ("P1-404-302", "UHMW round Ø80 x 150 (x2) + plate 6 (flange)", "turn Ø75.2, bore; bond + screw the flange (unwind)"),
        ("P1-404-303", "UHMW round Ø55 x 25 (x2)", "turn, bore, tap M5 radial"),
        ("P1-404-304", "304 spring strip 0.8 + felt", "cut, drill, bend 15°, bond felt"),
        ("P1-404-305", "304 round Ø16 x 300", "turn Ø12 h6, 2 flats, 2 grooves"),
        ("P1-404-306", "UHMW round Ø45 x 12 (x2)", "turn, groove R2.6, bore, tap M4"),
        ("P1-404-307", "304 Ø16 x 160 + UHMW Ø25 x 130", "turn shaft, thread M8; turn sleeve"),
    ], "CUT LIST AND OPERATIONS", 12, 22)
    S.notes(120, 1720, 1600, [
        "Web path order: unwind 301/302 → guide 307 → gap sensor P1-427 → peel plate 401 → tip → liner back under the plate → liner drive 202 with pinch 203 → rewind 305/302.",
        "Thread-up card: keep a copy inside the belt guard. The liner end tucks into the rewind hub slot; wind 2 turns by hand before running.",
        f"Label roll: 3 in core, ≤ {LAB['od_max']:.0f} OD: about {C['shaker-250']['labels_roll']:.0f} shaker or {C['jar-12']['labels_roll']:.0f} jar labels per roll.",
    ], "NOTES", fs=12)
    S.save(DWG / "P1-404-300_web_path.svg")


# ====================================================================== 400 peel + idler
def peel():
    S = sheet("P1-404-400", "PEEL PLATE AND IDLER ARM", scale="1:1 · 1:2", material=SS304, finish=FIN_NPC,
              mass=kg("P1-404-401", "P1-404-402", "P1-404-403", "P1-404-404", "P1-404-405", "P1-404-406"))
    s1, s2 = SC(1), SC(2)
    vp = S.view(300, 560, s1, "PEEL PLATE 401 (1:1), 304 2 [.079], FLAT PATTERN", (500, 150))
    Lf = PEEL["L"] + 30.0
    flat = rect_pts(0, PEEL["w"], 0, Lf)
    vp.poly(flat, fill=SS); vp.line(0, PEEL["L"], PEEL["w"], PEEL["L"], "bend")
    win = (100.0, 116.0, 30.0, 55.0)
    R(vp, win[0], win[1], win[2], win[3], "vis", "#fff")
    for x in (20.0, PEEL["w"] - 20.0):
        vp.circle(x, PEEL["L"] + 15, 2.75, "vis", "#fff")
    vp.dim((0, 0), (PEEL["w"], 0), -30, None, "h"); vp.dim((PEEL["w"], 0), (PEEL["w"], Lf), -40, None, "v"); vp.dim((0, 0), (0, PEEL["L"]), 40, None, "v")
    vp.leader((60, 0), (90, -40), ["TIP EDGE: R1 [.04], POLISHED, STRAIGHT 0.05; BEND DOWN 90° + 8° AT THE BEND LINE"], 11)
    vp.leader((116, 42), (125, -15), ["WINDOW 16 x 25 UNDER THE WEB EDGE FOR THE GAP FORK"], 11)
    dxf_profile(str(DXF / "P1-404-401_peel_flat"), flat, holes=[(20.0, PEEL["L"] + 15, 2.75), (PEEL["w"] - 20.0, PEEL["L"] + 15, 2.75)],
                bends=[((0, PEEL["L"]), (PEEL["w"], PEEL["L"]))], text="P1-404-401 PEEL PLATE 2 304")
    (y0, z0), (y1, z1) = M.peel_pts("J")
    zc = z_top(CONT["jar-12"]["d"]) - 15.0
    yb, zb = 25.0, zc - 12.0                                          # bracket datum: foot rear-bottom corner
    Hb, Lb, Ya = z1 - zb, PEEL["w"] / 2 - 5.0 - XL1, y1 - yb
    vb = S.view(950, 560, s1, "PEEL BRACKET 402 (1:1), 304 6, WELDED · FRONT (FROM -Y)", (1300, 150))
    R(vb, 0, 6, 0, Hb, fill=SS); R(vb, 6, Lb, Hb - 30, Hb, fill=SS)
    for xh in (-40.0, 40.0):
        vb.circle(xh - XL1, Hb - 15, 2.5, "vis", "#fff"); vb.circle(xh - XL1, Hb - 15, 2.1, "thin")
    vb.dim((0, 0), (Lb, 0), -35, None, "h"); vb.dim((0, Hb), (-40 - XL1, Hb), 30, None, "h"); vb.dim((-40 - XL1, Hb), (40 - XL1, Hb), 30, None, "h")
    vb.dim((Lb, Hb - 30), (Lb, Hb), -30, None, "v"); vb.dim((0, 0), (0, Hb), 40, None, "v")
    vb.leader((40 - XL1, Hb - 15), (40 - XL1 + 25, Hb - 55), ["2 x M5 THRU (peel plate flange, H9)"], 11)
    vb.leader((6, Hb - 30), (30, Hb - 70), ["3 fillet both sides, flat 0.1 after welding"], 11)
    vbs = S.view(2000, 560, s1, "SIDE (FROM +X)", (2080, 150))
    foot = [(0, 0), (Ya + 6, 0), (Ya + 6, Hb), (Ya, Hb), (Ya, 24), (0, 24)]
    vbs.poly(foot, fill=SS); vbs.poly(rect_pts(Ya, Ya + 6, Hb - 30, Hb), fill="url(#hA)")
    for yh in (40.0, 70.0):
        vbs.circle(yh - yb, 12, 2.75, "vis", "#fff")
    vbs.dim((0, 0), (Ya + 6, 0), -35, None, "h"); vbs.dim((0, 24), (15, 24), 25, None, "h"); vbs.dim((15, 24), (45, 24), 25, None, "h")
    vbs.dim((Ya + 6, 0), (Ya + 6, Hb), -30, None, "v"); vbs.dim((0, 0), (0, 12), 30, None, "v")
    vbs.leader((45, 12), (60, -30), ["2 x Ø5.5 THRU to 102 holes PS (S) or PJ (J), H9"], 11)
    vbs.note(-10, -60, [f"Arm is welded square to the foot; the peel tip then sits {PEEL['tip_y']:.0f} behind container TDC, 1 above it.",
                        "One bracket serves both settings: move it between the PS and PJ hole pairs (Δz 24.9)."], 11)
    vpv = S.view(2450, 560, s2, "PIVOT SHAFT 403 (1:2), 304 Ø16", (2700, 150))
    L = XR0 - XL1
    turned(vpv, [(0, L, 16.0)])
    vpv.dim((0, -8), (L, -8), -40, None, "h"); vpv.note(0, 25, ["Ø16 f8; M8 x 12 both ends (tie between the plates); arms turn on it with nylon washers"], 11)
    va = S.view(250, 1450, s1, "IDLER ARM 404 x 2 (1:1), 304 FLAT 25 x 8", (650, 1080))
    (py, pz), (yc, zc2) = M.arm_pts()
    La = math.hypot(yc - py, zc2 - pz)
    ap = rounded(-12.5, La + 12.5 + 55, -12.5, 12.5, 12.4, 6)
    va.poly(ap, fill=SS)
    va.circle(0, 0, 8.05, "vis", "#fff"); va.circle(La, 0, 6.0, "vis", "#fff"); va.circle(La + 55, 0, 4.25, "hid")
    va.dim((0, -12.5), (La, -12.5), -40, f"{mmi(La, 1)} PIVOT TO IDLER", "h"); va.dim((La, -12.5), (La + 55, -12.5), -70, None, "h")
    va.note(0, 40, ["Ø16.1 pivot, Ø12 H8 idler shaft + M5 set screw (H14); +x arm only: M8 x 15 at the end for the knob P1-458;",
                    "-x arm without the knob hole. Arm weight + idler presses the label at ≈ 15 N; lift stop at 40° on the sensor bracket."], 11)
    dxf_profile(str(DXF / "P1-404-404_idler_arm"), ap, holes=[(0, 0, 8.05), (La, 0, 6.0)], text="P1-404-404 IDLER ARM 8 304 x2")
    vi = S.view(1450, 1500, s2, "IDLER SHAFT 405 (1:2), 304 Ø12", (1700, 1080))
    Li = (XR0 - 4.0) - (XL1 + 4.0)
    turned(vi, [(0, Li, 12.0)]); vi.dim((0, -6), (Li, -6), -40, None, "h")
    vi.note(0, 20, ["Ø12 h6; 2 flats 0.5 for the arm set screws; DIN 471 each side of the idler P1-455"], 11)
    vs = S.view(2450, 1500, SC(0.5), "SENSOR BRACKET 406 (2:1), 304 3", (2550, 1080))
    R(vs, 0, 30, 0, 3, fill=SS); R(vs, 27, 30, 0, 25, fill=SS)
    vs.circle(13, 1.5, 2.75, "hid"); vs.dim((0, 0), (30, 0), -30, None, "h"); vs.dim((30, 0), (30, 25), -30, None, "v")
    vs.note(-10, -40, ["M12 x 1 sensor P1-457 in the 103 plate; bracket is the arm's down stop and lift stop (40°)"], 11)
    S.table(120, 1750, [("PART", 120), ("STOCK", 300), ("SIZE", 360)], [
        ("P1-404-401", "304 sheet 2", f"{PEEL['w']:.0f} x {Lf:.0f} flat, 1 bend"),
        ("P1-404-402", "304 plate 6", "foot 65 x 24 + riser, arm 210 x 30; welded"),
        ("P1-404-403", "304 round Ø16", f"{L:.0f} long"),
        ("P1-404-404", "304 flat 25 x 8", f"{La + 80:.0f} long x 2"),
        ("P1-404-405", "304 round Ø12", f"{Li:.0f} long"),
        ("P1-404-406", "304 sheet 3", "30 x 25 bent"),
    ], "CUT LIST", 12, 22)
    S.save(DWG / "P1-404-400_peel_idler.svg")


if __name__ == "__main__":
    frame(); drive(); web(); peel()
