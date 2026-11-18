"""P1-406-100 frame, -200 belt run, -300 reject, -400 drive and controls brackets (+ DXF cut files)."""
import math
from common import *  # noqa: F401,F403
from design import *  # noqa: F401,F403
import model as M

C = calcs()
SS = "#f4f6f8"
UH = "#fbfbf6"
FRPC = "#f3e5ab"
YI, YO = M.YI, M.YO
U0, V0 = SIDE["x0"], Z_SIDE0               # side plate local datum: u = |x| - 475 (MFZ end), v = z - 763 (bottom edge)
UP, VP = PUL["x"] - U0, Z_PUL - V0         # pulley centre in plate coordinates
LP, HP = SIDE["x1"] - SIDE["x0"], SIDE["h"]


def R(v, x0, x1, y0, y1, k="vis", fill="none"):
    v.rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0), k, fill)


def rect_pts(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def turned(v, segs, fill=SS):
    for x0, x1, d in segs:
        R(v, x0, x1, -d / 2, d / 2, fill=fill)
    v.centre(segs[0][0] - 8, 0, segs[-1][1] + 8, 0)


def plate_outline():
    e0, e1, et = UP - M.EAR / 2, UP + M.EAR / 2, VP + M.EAR / 2
    return [(0, 0), (LP, 0), (LP, HP), (e1, HP), (e1, et), (e0, et), (e0, HP), (0, HP)]


def plate_feats(drive, side):
    """(tag, dia, [(u, v)], use, slot_len) for one side plate. side -1 = operator side."""
    f = []
    if drive:
        f.append(("S", 26.0, [(UP, VP)], "Ø26 THRU (SHAFT CLEARANCE)", 0))
        f.append(("B", 11.0, [(UP + dx, VP + dz) for dx, dz in M.BRG_HOLES], "Ø11 THRU (UCFL204, M10)", 0))
    else:
        f.append(("S", 22.0, [(UP, VP)], f"SLOT 22 x {22 + TAKEUP:.0f} ALONG x (SHAFT, TAKE-UP)", TAKEUP))
        f.append(("B", 11.0, [(UP + dx, VP + dz) for dx, dz in M.BRG_HOLES], f"SLOT 11 x {11 + TAKEUP:.0f} ALONG x (UCFL204, M10)", TAKEUP))
    f.append(("C", 6.6, [(cx - U0, Z_BELT - 22.0 - V0) for cx in M.CLIP_X], "Ø6.6 THRU (RAIL CLIP M6)", 0))
    gx = M.GUIDE_BKT_X[+1 if drive else -1]
    f.append(("G", 4.2, [(cx - U0, vv) for cx in gx for vv in (122.0, 136.0)], "M5 THRU (GUIDE BRACKET)", 0))
    if drive and side < 0:
        f.append(("P", 6.6, [(REJ["x"] + dx - U0, vv) for dx in (-25.0, 25.0) for vv in (95.0, 122.0)], "Ø6.6 THRU (PUSHER BRACKET, M6 H8)", 0))
        f.append(("E", 4.2, [(B1_X - U0, vv) for vv in (118.0, 134.0)], "M5 THRU (B1 EYE BRACKET)", 0))
    if drive and side > 0:
        f.append(("E", 4.2, [(B1_X - U0, vv) for vv in (118.0, 134.0)], "M5 THRU (B1 REFLECTOR)", 0))
        f.append(("K", 6.6, [(x - U0, HP - 25.0) for x in M.BIN_HOOKS], "Ø6.6 THRU (BIN HOOK STOP SCREWS H8)", 0))
    return f


def draw_plate(v, feats, ox=0.0):
    v.poly([(ox + u, vv) for u, vv in plate_outline()], fill=SS)
    holes, rows = [], []
    for tag, d, pts, use, sl in feats:
        for i, (u, vv) in enumerate(pts):
            if sl:
                v.poly([(ox + a, b) for a, b in slot_pts(u, vv, d, sl)], "vis", fill="#fff")
            else:
                v.circle(ox + u, vv, d / 2, "vis", "#fff")
            v.text(ox + u + d / 2 + 3, vv + d / 2 + 2, f"{tag}{i + 1}", 7, "start")
            rows.append((f"{tag}{i + 1}", f"{u:.1f}", f"{vv:.1f}", use)); holes.append((u, vv, d / 2, sl))
    return holes, rows


def slot_pts(u, v, d, sl, n=8):
    r = d / 2; pts = []
    for cx, a0 in ((u + sl / 2, -90), (u - sl / 2, 90)):
        for i in range(n + 1):
            a = math.radians(a0 + 180 * i / n); pts.append((cx + r * math.cos(a), v + r * math.sin(a)))
    return pts


# ====================================================================== 100 frame
def frame():
    S = sheet("P1-406-100", "FRAME: END FRAMES, SPINE, HEAD STAND", scale="1:2 · 1:4 · 1:8", material=SS304, finish=FIN_NPC,
              mass=kg("P1-406-101", "P1-406-102", "P1-406-103", "P1-406-104"))
    s2, s4, s8 = SC(2), SC(2), SC(8)
    s2 = SC(2); s4 = SC(4)
    # side plates flat (1:2): drive (outfeed -y), tail (infeed)
    vd = S.view(150, 560, s2, "SIDE PLATE, OUTFEED -Y (1:2), 304 4 [.157], FROM OUTSIDE", (430, 130))
    hd, rd = draw_plate(vd, plate_feats(True, -1))
    vd.dim((0, 0), (LP, 0), -40, None, "h"); vd.dim((LP, 0), (LP, HP), -40, None, "v"); vd.dim((0, 0), (UP, 0), -70, None, "h")
    vd.dim((0, 0), (0, VP), 40, None, "v"); vd.dim((UP - M.EAR / 2, VP + M.EAR / 2), (UP + M.EAR / 2, VP + M.EAR / 2), 25, None, "h")
    vd.dim((LP, HP), (LP, VP + M.EAR / 2), -40, None, "v")
    vd.note(0, -95, ["u from the MFZ end (|x| 475), v from the bottom edge (z 763). Outfeed +y plate: same without P, with K; infeed plates: S and B as slots."], 10)
    for nm, drive, side in (("P1-406-102_plate_out_opside", True, -1), ("P1-406-102_plate_out_back", True, 1), ("P1-406-101_plate_in_opside", False, -1), ("P1-406-101_plate_in_back", False, 1)):
        fe = plate_feats(drive, side)
        hs = [(u, vv, d / 2) for t, d, pts, use, sl in fe if not sl for u, vv in pts]
        sl = [slot_pts(u, vv, d, s_) for t, d, pts, use, s_ in fe if s_ for u, vv in pts]
        dxf_profile(str(DXF / nm), [plate_outline()] + sl, holes=hs, text=f"{nm.split('_')[0]} SIDE PLATE 4 304 " + ("OP SIDE" if side < 0 else "BACK"))
    vt = S.view(150, 1000, s2, "SIDE PLATE, INFEED (1:2): TAKE-UP SLOTS", (430, 640))
    ht, rt = draw_plate(vt, plate_feats(False, -1))
    vt.dim((UP - TAKEUP / 2 - 11, VP), (UP + TAKEUP / 2 + 11, VP), -80, None, "h")
    S.table(1750, 140, [("HOLE", 50), ("u", 60), ("v", 60), ("SIZE / USE (infeed, operator side)", 380)], rt, "PLATE HOLES (INFEED -Y)", 10, 17)
    S.table(1150, 140, [("HOLE", 50), ("u", 60), ("v", 60), ("SIZE / USE (outfeed, operator side)", 380)], rd, "PLATE HOLES (OUTFEED -Y)", 10, 17)
    # end frame weldment elevation (1:4) from -y and end view
    ve = S.view(150, 2000, s4, "END FRAME 102 WELDMENT (1:4), FROM -Y (101: SLOTS + TAKE-UP LUGS)", (150, 1100))
    R(ve, 0, LP, V0, V0 + HP, fill=SS); R(ve, UP - M.EAR / 2, UP + M.EAR / 2, V0 + HP, Z_PUL + M.EAR / 2, fill=SS)
    lx = LEG["x"] - U0
    R(ve, lx - 20, lx + 20, LEG["z_foot"], V0 + 60, fill=SS); R(ve, lx - 30, lx + 30, LEG["z_foot"] - 8, LEG["z_foot"], fill=SS)
    R(ve, lx - 20, lx + 20, BRACE_Z - 20, BRACE_Z + 20, "hid")
    for cx in (560.0, 660.0):
        R(ve, cx - U0 - 20, cx - U0 + 20, V0, V0 + 40, "hid")
    R(ve, 5, PUL["x"] - PUL["d"] / 2 - 8 - U0, V0 + HP - BED_SS["t"], V0 + HP, "hid")
    ve.line(-20, 0, LP + 40, 0, "phan")
    ve.dim((lx, 0), (lx, LEG["z_foot"]), 40, "FOOT", "v"); ve.dim((LP, 0), (LP, V0 + HP), -50, None, "v"); ve.dim((0, V0 - 30), (lx, V0 - 30), 0, None, "h")
    ve.dim((lx + 20, BRACE_Z), (lx + 20, 0), -30, None, "v")
    ve.note(-10, -60, ["Leg 40 x 40 x 2 welded to the plate outside face (3 fillet, 60 overlap); 2 cross tubes 40 x 40 x 2 at u 85 / 185 under the bed,",
                       "brace 40 x 40 x 2 between the legs at z 300; bed 3 mm on top, welded intermittent 3-25-100; foot pad 60 x 60 x 8 tapped M16."], 10)
    vend = S.view(1300, 2000, s4, "END VIEW (1:4), FROM +X", (1170, 2075))
    for sy in (-1, 1):
        R(vend, sy * YI, sy * YO, V0, V0 + HP, fill=SS); R(vend, sy * LEG["y"] - 20, sy * LEG["y"] + 20, LEG["z_foot"], V0 + 60, fill=SS)
        R(vend, sy * LEG["y"] - 30, sy * LEG["y"] + 30, LEG["z_foot"] - 8, LEG["z_foot"], fill=SS)
    R(vend, -YI, YI, V0 + HP - BED_SS["t"], V0 + HP, fill=SS); R(vend, -LEG["y"] + 20, LEG["y"] - 20, BRACE_Z - 20, BRACE_Z + 20, fill=SS)
    R(vend, -YI, YI, V0, V0 + 40, "hid")
    vend.dim((-YO, V0 + HP + 20), (YO, V0 + HP + 20), 30, None, "h"); vend.dim((-LEG["y"], 0), (LEG["y"], 0), -40, f"LEGS {LEG['y'] * 2:.0f} CTRS", "h")
    vend.dim((-YI, V0 + HP), (YI, V0 + HP), 60, "200 INSIDE ±0.5", "h")
    # spine and head stand (1:8)
    vs = S.view(1800, 1250, s8, "SPINE 103 (1:8), 304 TUBE 80 x 40 x 3", (1470, 1170))
    L = 2 * LEG["x"] + 40
    R(vs, -L / 2, L / 2, -SPINE["h"] / 2, SPINE["h"] / 2, fill=SS)
    for sx in (-1, 1):
        R(vs, sx * LEG["x"] - 30, sx * LEG["x"] + 30, SPINE["h"] / 2, SPINE["h"] / 2 + 8, fill=SS)
    vs.dim((-L / 2, -SPINE["h"] / 2), (L / 2, -SPINE["h"] / 2), -30, None, "h"); vs.dim((-LEG["x"], SPINE["h"] / 2 + 8), (LEG["x"], SPINE["h"] / 2 + 8), 30, None, "h")
    vs.note(-L / 2, -70, ["Top plates 60 x 80 x 8 welded at the leg brace positions, 2 x Ø9 each (H1 M8 to the braces); stand beam bolts on at x 0 (4 x Ø9)."], 10)
    vh = S.view(2050, 1850, s4, "HEAD STAND 104 (1:4), WELDED; CONFIRM LUGS ON THE ACTUAL HEAD", (1740, 1320))
    zb = 0.0; hp = HEAD["lug_z"] - (M.SPINE_Z + SPINE["h"] / 2) - 40
    R(vh, -STAND["beam_y"], STAND["beam_y"], 0, 40, fill=SS)
    for sy in (-1, 1):
        R(vh, sy * HEAD["lug_y"] - 25, sy * HEAD["lug_y"] + 25, 40, 40 + hp - 8, fill=SS); R(vh, sy * HEAD["lug_y"] - 35, sy * HEAD["lug_y"] + 35, 40 + hp - 8, 40 + hp, fill=SS)
        R(vh, sy * HEAD["lug_y"] - 6, sy * HEAD["lug_y"] + 6, 40 + hp - 8, 40 + hp, "hid")
    vh.dim((-STAND["beam_y"], 0), (STAND["beam_y"], 0), -30, None, "h"); vh.dim((-HEAD["lug_y"], 40 + hp), (HEAD["lug_y"], 40 + hp), 30, "LUG CTRS (CONFIRM)", "h")
    vh.dim((STAND["beam_y"], 0), (STAND["beam_y"], 40 + hp), -40, None, "v")
    vh.note(-STAND["beam_y"], -60, ["Beam 80 x 40 x 3, posts 50 x 50 x 3, top plates 70 x 120 x 8 with slots 9 x 30 along y; +y top plate gets the G10 pad and nylon bushes (H7)."], 10)
    S.notes(1150, 820, 1300, [
        "Laser cut the side plates as a set of 4; mark u/v datum; deburr. Weld the end frames on a table jig: plates 200 ±0.5 apart inside, square to the bed 0.5.",
        f"After welding, line-bore is not needed: the flange bearings self-align; check the two pulley axes parallel 0.5 over 1,420 at assembly (ITP T3).",
        f"No steel inside |x| < {X_STATIC:.0f}: the end frames stop at u 0. Spine and stand are {HEAD['ap_z0'] - (M.SPINE_Z + SPINE['h'] / 2):.0f} below the aperture (> {MFZ['static']:.0f}).",
        "Break edges 0.5; #4 brush; passivate ASTM A967.",
    ], "NOTES", fs=12)
    S.save(DWG / "P1-406-100_frame.svg")


# ====================================================================== 200 belt run
def belt():
    S = sheet("P1-406-200", "BELT RUN: PULLEYS, TAKE-UP, FRP RAILS, BED, GUIDES", scale="1:1 · 1:2 · 1:5", material="304 pipe + bar; FRP; UHMW-PE", finish="machined / as supplied",
              mass=kg("P1-406-201", "P1-406-202", "P1-406-203", "P1-406-204", "P1-406-205", "P1-406-206", "P1-406-207", "P1-406-208"))
    s1, s2, s5 = SC(1), SC(2), SC(5)
    vp = S.view(250, 520, s2, "DRIVE PULLEY 201 (1:2), SECTION; TAIL 202 THE SAME WITH A SHORT SHAFT", (150, 360))
    yl0 = YO + PUL["brg_t"] + 95.0; yl1 = YO + PUL["brg_t"] + 8.0
    R(vp, 0, yl0 + yl1, -PUL["shaft"] / 2, PUL["shaft"] / 2, fill=SS)
    a = yl0 - PUL["face"] / 2; b = yl0 + PUL["face"] / 2
    for sg in (-1, 1):
        R(vp, a, b, sg * (PUL["d"] / 2 - 4), sg * PUL["d"] / 2, fill="url(#hA)")
        R(vp, a, a + 8, sg * PUL["shaft"] / 2, sg * (PUL["d"] / 2 - 4), fill="url(#hA)"); R(vp, b - 8, b, sg * PUL["shaft"] / 2, sg * (PUL["d"] / 2 - 4), fill="url(#hA)")
    vp.centre(-10, 0, yl0 + yl1 + 10, 0)
    vp.dim((0, -PUL["shaft"] / 2), (yl0 + yl1, -PUL["shaft"] / 2), -60, None, "h"); vp.dim((a, PUL["d"] / 2), (b, PUL["d"] / 2), 30, None, "h")
    vp.dim((b, -PUL["d"] / 2), (b, PUL["d"] / 2), -40, "Ø60 CROWN 0.5", "v"); vp.dim((0, -PUL["shaft"] / 2), (0, PUL["shaft"] / 2), 30, "Ø20 h7 + KEY 6", "v")
    vp.dim((0, PUL["shaft"] / 2), (a, PUL["shaft"] / 2), 45, None, "h")
    vp.leader((yl0 - 40, PUL["d"] / 2 - 2), (yl0 - 30, 60), ["2 in SCH 40 304 PIPE (60.3 x 3.9) TURNED Ø60, CROWN 0.5 ON Ø; END DISCS 8, BORE Ø20 H7, WELDED TO THE SHAFT"], 10)
    vp.leader((yl0 + yl1 - 60, PUL["shaft"] / 2), (yl0 + yl1 - 20, 45), ["JOURNALS Ø20 k6 IN UCFL204 (SET SCREWS)"], 10)
    vp.note(0, -55, ["Drive shaft: -y end 95 long beyond the bearing, key 6 x 6 x 30 for the hollow-shaft gearmotor (P1-420). Tail: 8 beyond the bearings both ends."], 10)
    # take-up screw
    vtk = S.view(250, 820, s1, "TAKE-UP SCREW 203 x 2 (1:1)", (250, 700))
    R(vtk, 0, 60, -5, 5, fill=SS); R(vtk, 0, 7, -8.5, 8.5, fill=SS); R(vtk, 30, 38, -8.5, 8.5, "phan")
    vtk.dim((0, -8.5), (60, -8.5), -25, None, "h"); vtk.note(0, 15, ["H3: M10 x 60 hex screw + 2 nuts through the lug; pushes the tail bearing flange; lock with the nut."], 10)
    # FRP rail
    vf = S.view(150, 1150, s5, "FRP RAIL 204 x 2 (1:5), PULTRUDED RECT TUBE 38.1 x 19.05 x 3.2 [1-1/2 x 3/4 x 1/8 in], ON EDGE", (150, 1080))
    Lr = 2 * FRP["x"]
    R(vf, 0, Lr, 0, FRP["h"], fill=FRPC)
    hx = [40.0 + i * (Lr - 80.0) / 8 for i in range(9)]
    for x in hx:
        vf.line(x, FRP["h"] - 6, x, FRP["h"], "hid")
    for x in (15.0, 30.0, Lr - 30.0, Lr - 15.0):
        vf.circle(x, FRP["h"] / 2, 2.75, "vis", "#fff")
    vf.dim((0, 0), (Lr, 0), -30, None, "h"); vf.dim((Lr, 0), (Lr, FRP["h"]), -30, None, "v")
    vf.note(0, -60, [f"9 x Ø5.5 down through the top wall at {(Lr - 80) / 8:.0f} pitch for nylon screws to the bed; 2 x Ø5.5 across each end for the clips (nylon, H5).",
                     "Cut with a diamond blade, seal the cut ends with resin; no metal fasteners."], 10)
    # clip
    vc = S.view(1500, 820, s1, "RAIL CLIP 205 x 4 (1:1), 304 4, FLAT + 1 BEND", (1500, 585))
    zr0 = Z_BELT - BELT["t"] - UBED["t"] - FRP["h"]
    up = (Z_BELT - 12.0) - (zr0 - 4.0); sh = YI - (FRP["y"] + FRP["w"] / 2)
    clip = rect_pts(0, 50, 0, up + sh)
    vc.poly(clip, fill=SS); vc.line(0, sh, 50, sh, "bend")
    for x in (15.0, 35.0):
        vc.circle(x, sh + up - 12, 3.3, "vis", "#fff"); vc.circle(x, sh / 2, 2.75, "vis", "#fff")
    vc.dim((0, 0), (50, 0), -25, None, "h"); vc.dim((50, 0), (50, up + sh), -30, None, "v"); vc.dim((0, 0), (0, sh), 25, None, "v")
    vc.note(0, -45, ["Bend 90° at the line (IR 4): short leg is the shelf under the rail; 2 x Ø6.6 to the plate (H4), 2 x Ø5.5 to the rail (nylon)."], 10)
    dxf_profile(str(DXF / "P1-406-205_rail_clip"), clip, holes=[(15.0, sh + up - 12, 3.3), (35.0, sh + up - 12, 3.3), (15.0, sh / 2, 2.75), (35.0, sh / 2, 2.75)],
                bends=[((0, sh), (50, sh))], text="P1-406-205 CLIP 4 304 x4")
    # bed
    vb = S.view(150, 1560, s5, f"UHMW BED 206 (1:5), {UBED['t']:.0f} THICK", (150, 1340))
    Lb = 2 * UBED["x"]
    bed = rect_pts(0, Lb, 0, UBED["w"])
    vb.poly(bed, fill=UH)
    bh = [(x, UBED["w"] / 2 + sy * FRP["y"], 2.75) for x in hx[:] for sy in (-1, 1) if x - (FRP["x"] - UBED["x"]) > 5 and x - (FRP["x"] - UBED["x"]) < Lb - 5]
    bh = [(x - (FRP["x"] - UBED["x"]), y, r) for x, y, r in bh]
    for x, y, r in bh:
        vb.circle(x, y, r, "vis", "#fff")
    vb.dim((0, 0), (Lb, 0), -30, None, "h"); vb.dim((Lb, 0), (Lb, UBED["w"]), -30, None, "v")
    vb.note(0, -60, ["Ø5.5 c'sunk 90° from the top for nylon flat-head M5 (flush, under the belt); ends chamfered 3 x 30° so the belt cannot catch."], 10)
    dxf_profile(str(DXF / "P1-406-206_uhmw_bed"), bed, holes=bh, text="P1-406-206 BED UHMW 10")
    # guide strip + bracket
    vg = S.view(1500, 1180, s2, "GUIDE STRIPS 207 (1:2), UHMW 10 x 40", (1500, 1050))
    for L_, y0 in ((SIDE["x1"] - UBED["x"], 0.0), (REJ["x"] - 70 - UBED["x"], -90.0)):
        R(vg, 0, L_, y0, y0 + GUIDE["h"], fill=UH); vg.dim((0, y0), (L_, y0), -20, None, "h")
    vg.note(0, -150, ["Infeed pair 280 long, outfeed pair 70 long (stop at the reject); ends radiused R20 at the infeed; 2 x M5 tapped per bracket."], 10)
    vgb = S.view(2500, 1180, s1, "GUIDE BRACKET 208 x 6 (1:1), 304 3", (2420, 1050))
    arm = (GUIDE["gap"]["S"] / 2 + GUIDE["t"], YO)
    gb = [(0, 0), (YO - arm[0] + 30, 0), (YO - arm[0] + 30, 5), (0, 5)]
    R(vgb, 0, YO - arm[0], 0, 5, fill=SS); R(vgb, YO - arm[0], YO - arm[0] + 3, -50, 5, fill=SS)
    R(vgb, 8, 8 + (GUIDE["gap"]["S"] - GUIDE["gap"]["J"]) / 2 + 6, 1, 4, "vis", "#fff")
    vgb.dim((0, 5), (YO - arm[0] + 3, 5), 20, None, "h"); vgb.dim((YO - arm[0] + 3, -50), (YO - arm[0] + 3, 5), -25, None, "v")
    Ls = (GUIDE["gap"]["S"] - GUIDE["gap"]["J"]) / 2 + 6
    dxf_profile(str(DXF / "P1-406-208_guide_bracket"), [rect_pts(0, YO - arm[0] + 53, 0, 20), slot_pts(8 + Ls / 2, 10, 5.5, Ls - 5.5)], holes=[(YO - arm[0] + 40, 10, 2.75), (YO - arm[0] + 30, 10, 2.75)],
                bends=[((YO - arm[0], 0), (YO - arm[0], 20))], text="P1-406-208 GUIDE BKT 3 304 x6")
    vgb.note(0, -75, [f"SLOT 5.5 x {(GUIDE['gap']['S'] - GUIDE['gap']['J']) / 2 + 6:.0f}: S / J guide positions; 2 x Ø5.5 in the leg to the plate G holes"], 10)
    S.table(1500, 1560, [("PART", 120), ("STOCK", 330), ("OPERATIONS", 520)], [
        ("P1-406-201/202", "2 in sch 40 304 pipe x 175 + Ø80 x 8 discs + Ø25 bar", "weld discs, turn Ø60 crown, journals Ø20 k6, keyway (201)"),
        ("P1-406-203", "M10 x 60 A2 hex screw + 2 nuts", "bought (H3)"),
        ("P1-406-204", "FRP rect tube 38.1 x 19.05 x 3.2 x 1,070 (x2)", "saw, drill, seal ends"),
        ("P1-406-205", "304 sheet 4", "laser flat, 1 bend"),
        ("P1-406-206", "UHMW 10 sheet 960 x 196", "saw, drill + c'sink, chamfer ends"),
        ("P1-406-207", "UHMW 10 x 40 bar", "saw 2 x 280, 2 x 70, radius"),
        ("P1-406-208", "304 sheet 3", "laser, bend, tap"),
    ], "CUT LIST AND OPERATIONS", 11, 20)
    S.save(DWG / "P1-406-200_belt_run.svg")


# ====================================================================== 300 reject
def reject():
    S = sheet("P1-406-300", "REJECT: PUSHER, PADDLE, LOCKED BIN, EYE BRACKETS", scale="1:2 · 1:4", material=SS304 + "; UHMW paddle", finish=FIN_NPC,
              mass=kg("P1-406-301", "P1-406-302", "P1-406-303", "P1-406-304"))
    s2, s4 = SC(2), SC(4)
    vb = S.view(300, 700, s2, "PUSHER BRACKET 301 (1:2), 304 6, WELDED · FROM +X", (250, 600))
    zt = REJ["z"]
    R(vb, 0, 6, Z_SIDE1 - 60 - zt, 25, fill=SS); R(vb, 6, 260, -35, -29, fill=SS); R(vb, 254, 260, -35, 15, fill=SS)
    vb.circle(257, 0, 3.1, "vis", "#fff"); vb.circle(150, 0, 18, "phan")
    for vv in (95.0, 122.0):
        vb.circle(3, vv + V0 - zt, 3.0, "hid")
    vb.dim((0, -35), (260, -35), -40, None, "h"); vb.dim((260, -35), (260, 15), -30, None, "v"); vb.dim((0, Z_SIDE1 - 60 - zt), (0, 25), 40, None, "v")
    vb.note(0, -110, ["Plate 80 x 132 on the -y side plate (4 x Ø6.6 to P1-P4), shelf 80 x 254 carries the actuator body, rear plate holds the clevis pin Ø6 (H9).",
                      "Weld 3 fillet both sides; actuator axis along y at z 950, x 620."], 10)
    vpd = S.view(1250, 700, s2, "PADDLE 302 (1:2), UHMW 20 + 304 CLEVIS", (1130, 505))
    R(vpd, -REJ["paddle_w"] / 2, REJ["paddle_w"] / 2, 0, REJ["paddle_h"], fill=UH); R(vpd, -12, 12, 25, 55, "hid")
    vpd.dim((-REJ["paddle_w"] / 2, 0), (REJ["paddle_w"] / 2, 0), -30, None, "h"); vpd.dim((REJ["paddle_w"] / 2, 0), (REJ["paddle_w"] / 2, REJ["paddle_h"]), -30, None, "v")
    vpd.note(-REJ["paddle_w"] / 2, -60, ["Face 120 x 80 (pushes below the jar shoulder), edges R5; clevis block 24 x 30 x 20 with 2 nylon screws; pin Ø6 to the rod end."], 10)
    vbin = S.view(150 + 0, 1850, s4, "BIN 303 (1:4), 304 1.5, WELDED · FROM -X", (150, 1320))
    R(vbin, BIN["y0"], BIN["y1"], BIN["z0"] - BIN["z0"], BIN["z1"] - BIN["z0"], fill=SS)
    R(vbin, BIN["y0"] - 2, BIN["y1"] + 20, BIN["z1"] - BIN["z0"], BIN["z1"] - BIN["z0"] + 2, fill=SS)
    R(vbin, BIN["y0"] - 1, BIN["y0"] + 1.5, Z_BELT - 5 - BIN["z0"], Z_BELT - 5 - BIN["z0"] + BIN["slot_h"], fill="#fff")
    R(vbin, YO, BIN["y0"], Z_SIDE1 - 40 - BIN["z0"], Z_SIDE1 - 36 - BIN["z0"], fill=SS)
    vbin.dim((BIN["y0"], 0), (BIN["y1"], 0), -30, None, "h"); vbin.dim((BIN["y1"], 0), (BIN["y1"], BIN["z1"] - BIN["z0"]), -50, None, "v")
    vbin.dim((BIN["y0"], Z_BELT - 5 - BIN["z0"]), (BIN["y0"], Z_BELT - 5 - BIN["z0"] + BIN["slot_h"]), 40, "SLOT H", "v")
    vbin.note(BIN["y0"], -60, [f"Body {BIN['x1'] - BIN['x0']:.0f} (x) x {BIN['y1'] - BIN['y0']:.0f} (y) x {BIN['z1'] - BIN['z0']:.0f}; slot {BIN['slot_w']:.0f} x {BIN['slot_h']:.0f} in the -y wall centred on x {REJ['x']:.0f};",
                                "lid hinged on the +y edge (piano hinge 304), hasp + padlock (P1-462), reed switch B3; 2 hooks 30 wide onto the +y plate top; drain hole Ø6."], 10)
    # bin flat pattern (body wrap: 4 walls + bottom as one blank, corners welded)
    Wb, Db, Hb = BIN["x1"] - BIN["x0"], BIN["y1"] - BIN["y0"], BIN["z1"] - BIN["z0"]
    flat = [(0, Hb), (0, Hb + Db), (Wb, Hb + Db), (Wb, Hb), (Wb + Hb, Hb), (Wb + Hb, Hb + Db), (Wb, Hb + Db), (Wb, 2 * Hb + Db), (0, 2 * Hb + Db), (0, Hb + Db),
            (-Hb, Hb + Db), (-Hb, Hb), (0, Hb), (0, 0), (Wb, 0), (Wb, Hb)]
    flat = [(0, 0), (Wb, 0), (Wb, Hb), (Wb + Hb, Hb), (Wb + Hb, Hb + Db), (Wb, Hb + Db), (Wb, 2 * Hb + Db), (0, 2 * Hb + Db), (0, Hb + Db), (-Hb, Hb + Db), (-Hb, Hb), (0, Hb)]
    vfl = S.view(1400 + 0, 1900, SC(8), "BIN 303 FLAT PATTERN (1:8), 304 1.5: BOTTOM + 4 WALLS", (1150, 1250))
    vfl.poly(flat, fill=SS)
    for a, b in (((0, Hb), (Wb, Hb)), ((0, Hb + Db), (Wb, Hb + Db)), ((0, Hb), (0, Hb + Db)), ((Wb, Hb), (Wb, Hb + Db))):
        vfl.line(*a, *b, "bend")
    sx0 = (REJ["x"] - BIN["x0"]) - BIN["slot_w"] / 2
    slot = rect_pts(sx0, sx0 + BIN["slot_w"], Hb - (Z_BELT - 5 - BIN["z0"]) - BIN["slot_h"], Hb - (Z_BELT - 5 - BIN["z0"]))
    vfl.poly(slot, "vis", fill="#fff")
    vfl.dim((0, 0), (Wb, 0), -25, None, "h"); vfl.dim((-Hb, Hb), (-Hb, Hb + Db), 25, None, "v"); vfl.dim((Wb + Hb, Hb), (Wb + Hb, Hb + Db), -25, None, "v")
    vfl.note(-Hb, -75, ["Bottom in the middle; bend the 4 walls up 90° (IR 1.5); TIG the 4 corners and grind flush. Slot cut in the -y wall (lower panel)."], 10)
    dxf_profile(str(DXF / "P1-406-303_bin_flat"), [flat, slot], holes=[(Wb / 2, Hb + Db / 2, 3.0)], bends=[((0, Hb), (Wb, Hb)), ((0, Hb + Db), (Wb, Hb + Db)), ((0, Hb), (0, Hb + Db)), ((Wb, Hb), (Wb, Hb + Db))],
                text="P1-406-303 BIN 1.5 304")
    vsy = S.view(800, 1850, s4, "BIN FROM -Y: SLOT (1:4)", (750, 1320))
    R(vsy, 0, Wb, 0, Hb, fill=SS); R(vsy, -2, Wb + 2, Hb, Hb + 2, fill=SS)
    zs = Z_BELT - 5 - BIN["z0"]
    R(vsy, sx0, sx0 + BIN["slot_w"], zs, zs + BIN["slot_h"], "vis", "#fff")
    vsy.dim((0, 0), (Wb, 0), -30, None, "h"); vsy.dim((0, zs), (sx0, zs), 0, None, "h"); vsy.dim((sx0, zs), (sx0 + BIN["slot_w"], zs), -20, None, "h")
    vsy.dim((Wb, 0), (Wb, zs), -30, None, "v"); vsy.dim((Wb, zs), (Wb, zs + BIN["slot_h"]), -30, None, "v")
    vsy.note(0, -60, [f"x from the bin -x wall (x {BIN['x0']:.0f})"], 10)
    vsb = S.view(2600, 700, SC(1), "EYE BRACKET 304 x 2 (1:1), 304 3", (2500, 310))
    R(vsb, 0, 30, 0, 92, fill=SS)
    for vv in (10.0, 26.0):
        vsb.circle(15, vv, 2.75, "vis", "#fff")
    vsb.circle(15, 70, 9.25, "vis", "#fff")
    vsb.dim((0, 0), (30, 0), -25, None, "h"); vsb.dim((30, 0), (30, 92), -30, None, "v"); vsb.dim((0, 0), (0, 70), 25, None, "v")
    vsb.note(-10, -45, ["Ø18.5 for the M18 eye (B1) or the reflector stud; 2 x Ø5.5 to the plate E holes"], 10)
    dxf_profile(str(DXF / "P1-406-304_eye_bracket"), rect_pts(0, 30, 0, 92), holes=[(15, 10, 2.75), (15, 26, 2.75), (15, 70, 9.25)], text="P1-406-304 EYE BKT 3 304 x2")
    S.table(1950, 1300, [("PART", 120), ("STOCK", 300), ("OPERATIONS", 420)], [
        ("P1-406-301", "304 plate 6", "laser 3 pieces, weld, drill Ø6.2 clevis"),
        ("P1-406-302", "UHMW 20 + 304 block 24 x 30 x 20", "saw, radius, drill; clevis drill Ø6.2"),
        ("P1-406-303", f"304 sheet 1.5, {Wb + 2 * Hb:.0f} x {2 * Hb + Db:.0f} blank + lid + hooks", "laser, bend, TIG, grind, hinge, hasp"),
        ("P1-406-304", "304 sheet 3", "laser x 2"),
    ], "CUT LIST", 11, 20)
    S.notes(1950, 1440, 840, [
        "Bin is part of CCP-1: it must be locked whenever the line runs (B3 lid switch stops the belt when open).",
        "Pusher retracted: paddle face 8 outside the J guide line; extended: pack lands in the bin through the slot (ITP T10).",
    ], "NOTES", fs=12)
    S.save(DWG / "P1-406-300_reject.svg")


# ====================================================================== 400 drive + controls
def drive():
    S = sheet("P1-406-400", "DRIVE AND CONTROLS BRACKETS", scale="1:2 · 1:4", material=SS304, finish=FIN_NPC, mass=kg("P1-406-401", "P1-406-402", "P1-406-403"))
    s2, s4 = SC(2), SC(4)
    va = S.view(300, 900, s2, "TORQUE ARM 401 (1:2), 304 6 · FROM -Y", (250, 380))
    z0 = LEG["z_foot"] + 500; z1 = Z_PUL - 60
    arm = [(LEG["x"] - 20, z0), (PUL["x"] + 5, z0), (PUL["x"] + 5, z1), (PUL["x"] - 15, z1), (PUL["x"] - 15, z0 + 30), (LEG["x"] - 20, z0 + 30)]
    arm = [(x - LEG["x"] + 20, z - z0) for x, z in arm]
    h1, h2 = (10, 15, 4.5), (arm[2][0] - 10, z1 - z0 - 12, 5.5)
    va.poly(arm, fill=SS)
    va.circle(*h1, "vis", "#fff"); va.circle(*h2, "vis", "#fff"); va.cmark(h1[0], h1[1], 8); va.cmark(h2[0], h2[1], 8)
    va.dim((0, 0), (arm[1][0], 0), -30, None, "h"); va.dim((arm[1][0], 0), (arm[1][0], z1 - z0), -30, None, "v")
    va.dim((0, 0), (0, 30), 30, None, "v"); va.dim((arm[3][0], z1 - z0), (arm[2][0], z1 - z0), 20, None, "h")
    va.dim((0, 0), (h1[0], 0), -55, None, "h"); va.dim((arm[1][0], 0), (arm[1][0], h2[1]), -60, None, "v")
    va.leader((h1[0] + 3, h1[1] + 3), (h1[0] + 60, h1[1] + 60), ["Ø9 THRU (H13 M8 + RUBBER BUSH)"], 10)
    va.leader((h2[0] + 3, h2[1]), (h2[0] + 70, h2[1] - 40), ["Ø11 THRU (GEARMOTOR LUG, CONFIRM ON P1-420)"], 10)
    va.note(0, -95, ["The arm takes reaction torque only (≈ 9 N·m); the rubber bush lets the hollow shaft float."], 10)
    dxf_profile(str(DXF / "P1-406-401_torque_arm"), arm, holes=[h1, h2], text="P1-406-401 TORQUE ARM 6 304")
    # drive arrangement elevation (1:4) from -y, outfeed end
    s4_ = s4; xa = 560.0
    vdr = S.view(300 - xa * s4_, 2180, s4_, "DRIVE ARRANGEMENT, OUTFEED END (1:4), FROM -Y", (150, 1170))
    R(vdr, xa, SIDE["x1"], Z_SIDE0, Z_SIDE1, fill=SS); R(vdr, PUL["x"] - M.EAR / 2, PUL["x"] + M.EAR / 2, Z_SIDE1, Z_PUL + M.EAR / 2, fill=SS)
    R(vdr, LEG["x"] - 20, LEG["x"] + 20, LEG["z_foot"], Z_SIDE0 + 60, fill=SS); R(vdr, LEG["x"] - 30, LEG["x"] + 30, LEG["z_foot"] - 8, LEG["z_foot"], fill=SS)
    vdr.line(xa - 20, 0, SIDE["x1"] + 40, 0, "phan")
    R(vdr, PUL["x"] - PUL["brg_sq"] / 2, PUL["x"] + PUL["brg_sq"] / 2, Z_PUL - PUL["brg_sq"] / 2, Z_PUL + PUL["brg_sq"] / 2, "hid")
    vdr.circle(PUL["x"], Z_PUL, PUL["shaft"] / 2, "vis", "#fff"); vdr.circle(PUL["x"], Z_PUL, PUL["d"] / 2, "hid")
    R(vdr, PUL["x"] - 75, PUL["x"] + 75, Z_PUL - 210, Z_PUL + 55, "phan")
    vdr.poly([(x + LEG["x"] - 20, z + z0) for x, z in arm], fill="#dde3ea")
    vdr.cmark(PUL["x"], Z_PUL, 30)
    vdr.dim((SIDE["x1"], 0), (SIDE["x1"], Z_PUL), -50, None, "v"); vdr.dim((LEG["x"], 0), (LEG["x"], z0 + 15), 50, None, "v")
    vdr.dim((LEG["x"], 0), (PUL["x"], 0), -30, None, "h")
    vdr.leader((PUL["x"] + 60, Z_PUL - 150), (PUL["x"] + 160, Z_PUL - 230), ["GEARMOTOR P1-420 (PHANTOM, CONFIRM SIZE)", "ON THE SHAFT, KEY 6 + 2 SET SCREWS H12"], 10)
    vdr.leader((LEG["x"], z0 + 15), (LEG["x"] - 120, z0 - 80), ["TORQUE ARM 401 TO THE LEG, H13"], 10)
    vdr.leader((PUL["x"] - 30, Z_PUL + 30), (PUL["x"] - 150, Z_PUL + 120), ["UCFL204 ON THE INSIDE OF THE EAR (HIDDEN)"], 10)
    vbx = S.view(1300, 1100, s2, "CONTROLS BOX BRACKET 402 (1:2), 304 3 · FROM -Y", (1300, 650))
    Wb, Hb = ENC["x1"] - ENC["x0"] - 40, ENC["h"] - 40
    R(vbx, 0, Wb, 0, Hb, fill=SS)
    for x, z in ((20, 20), (Wb - 20, 20), (20, Hb - 20), (Wb - 20, Hb - 20)):
        vbx.circle(x, z, 3.3, "vis", "#fff")
    lx = -LEG["x"] - (ENC["x0"] + 20)
    R(vbx, lx - 20, lx + 20, 20, 40, "hid"); vbx.circle(lx, 30, 4.5, "vis", "#fff")
    vbx.dim((0, 0), (Wb, 0), -30, None, "h"); vbx.dim((Wb, 0), (Wb, Hb), -30, None, "v")
    vbx.note(0, -60, ["Plate 160 x 210 with 4 x Ø6.6 for the box (H10); welded tab 40 x 20 x 16 standoff to the -y infeed leg, Ø9 (M8)."], 10)
    dxf_profile(str(DXF / "P1-406-402_box_bracket"), rect_pts(0, Wb, 0, Hb), holes=[(20, 20, 3.3), (Wb - 20, 20, 3.3), (20, Hb - 20, 3.3), (Wb - 20, Hb - 20, 3.3), (lx, 30, 4.5)],
                text="P1-406-402 BOX BKT 3 304")
    vpo = S.view(2300, 1700, s4, "BEACON POLE 403 (1:4), 304 TUBE Ø25.4 x 1.65", (2200, 940))
    Lp = POLE["h"] + (Z_BELT - Z_SIDE0) + 120
    R(vpo, -12.7, 12.7, 0, Lp, fill=SS)
    for zz in (0.0, 220.0):
        R(vpo, 12.7, 12.7 + (POLE["y"] - LEG["y"] - LEG["sq"] / 2 - 12.7), zz, zz + 20, fill=SS)
    vpo.dim((-12.7, 0), (-12.7, Lp), 40, None, "v"); vpo.dim((12.7, 0), (12.7, 220), -60, None, "v")
    vpo.note(-20, -50, ["2 clamp brackets (U-bolts H11) to the infeed +y leg; top: stack light P1-461 base; cable inside the tube, grommet at the bottom."], 10)
    S.table(1300, 1500, [("PART", 120), ("STOCK", 300), ("OPERATIONS", 420)], [
        ("P1-406-401", "304 plate 6", "laser, deburr"),
        ("P1-406-402", "304 sheet 3 + 40 x 20 x 16 block", "laser, weld tab"),
        ("P1-406-403", f"304 tube Ø25.4 x 1.65 x {Lp:.0f} + 2 brackets", "saw, weld brackets, grommet"),
    ], "CUT LIST", 11, 20)
    S.notes(1300, 1680, 900, [
        "Gearmotor: clean the shaft, anti-seize on the bore, slide on with the key 6 x 6 x 30; set screws H12 with Loctite 243, 4 N·m.",
        "Torque arm: bolt to the leg with the rubber bush; the bush must not be crushed (8 N·m). The arm must never carry the motor weight.",
        "Controls box: fit the bracket to the -y infeed leg before mounting the box; glands face down; lid toward the operator.",
        "Beacon pole: cable inside the tube, grommet at the bottom; light top at z ≈ 1,450, seen from the whole bench.",
    ], "NOTES", fs=12)
    S.save(DWG / "P1-406-400_drive_controls.svg")


if __name__ == "__main__":
    frame(); belt(); reject(); drive()
