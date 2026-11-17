"""Phase 1 plant: one full 3D assembly of every machine, placed from the layout (design/layout.json).

Fabricated parts come from their own STEP models (cad/step, made by p1_parts.py).
Machines built in house (blender, feeders, filler, detector conveyor, capper, labeler) come from p1_machines.py:
our parts as designed plus envelope models of their bought motors, valves and heads.
Other bought machines are modelled here at catalog size (design/equipment.json footprint_mm and specs) with their
main features and connection points; they are envelope models, not the makers' own CAD.
Heights follow the stack-up on ASM-P1-001 / 002 / 003.

Usage: python3 plant_3d.py  ->  plant/DH-P1-plant.step, plant/DH-P1-plant.glb, plant/anchors.json
"""
import json
import math
import pathlib
import sys

import cadquery as cq
from cadquery import Location, Solid, Vector

HERE = pathlib.Path(__file__).parent
P1 = HERE.parent
LAY = json.loads((P1 / "design" / "layout.json").read_text())
EQ = {e["tag"]: e for e in json.loads((P1 / "design" / "equipment.json").read_text())}
DOS = json.loads((P1 / "design" / "out" / "dosing-plan.json").read_text())
OUT = HERE / "plant"
OUT.mkdir(exist_ok=True)

# ---- colours ------------------------------------------------------------------------------------
SS = (0.80, 0.82, 0.84)          # fabricated stainless (ours)
SSB = (0.70, 0.73, 0.76)         # bought stainless machines
MOTOR = (0.20, 0.33, 0.50)
DARK = (0.18, 0.19, 0.21)
WHITE = (0.95, 0.95, 0.95)
CAB = (0.86, 0.87, 0.88)
DRUM = (0.16, 0.40, 0.75)
LINER = (0.92, 0.95, 0.98)
YEL = (0.98, 0.78, 0.10)
RED = (0.85, 0.20, 0.18)
GRN = (0.30, 0.70, 0.35)
BELT = (0.12, 0.45, 0.70)
WOOD = (0.72, 0.56, 0.36)
KRAFT = (0.78, 0.66, 0.48)
WRAP = (0.80, 0.86, 0.90)
FLOOR = {"Z3": (0.83, 0.88, 0.80), "Z1": (0.78, 0.78, 0.76), "support": (0.85, 0.83, 0.78), "Z0": (0.62, 0.62, 0.60)}
WALL = (0.93, 0.93, 0.91)
DUCT = (0.55, 0.58, 0.62)
PLAST = (0.25, 0.25, 0.27)

ASSY = cq.Assembly(name="DH-P1-plant")
ANCH = []          # label anchors for the renderer: tag, name, xyz, kind
_n = [0]


def add(shape, color, name):
    _n[0] += 1
    ASSY.add(shape, name=f"{name}#{_n[0]}", color=cq.Color(*color))


def anchor(tag, name, x, y, z, kind):
    ANCH.append(dict(tag=tag, name=name, x=round(x), y=round(y), z=round(z), kind=kind))


# ---- primitives (mm, Z up, plan X/Y as on DH-LAY-P1) -----------------------------------------------
def box(x0, y0, z0, dx, dy, dz):
    return Solid.makeBox(dx, dy, dz, Vector(x0, y0, z0))


def cbox(cx, cy, z0, dx, dy, dz):
    return box(cx - dx / 2, cy - dy / 2, z0, dx, dy, dz)


def cyl(cx, cy, z0, r, h, d=(0, 0, 1)):
    return Solid.makeCylinder(r, h, Vector(cx, cy, z0), Vector(*d))


def tube(p1, p2, r):
    a, b = Vector(*p1), Vector(*p2)
    v = b - a
    return Solid.makeCylinder(r, v.Length, a, v.normalized())


def cone(cx, cy, z0, r1, r2, h):
    return Solid.makeCone(r1, r2, h, Vector(cx, cy, z0), Vector(0, 0, 1))


def hollow_cyl(cx, cy, z0, r, h, t=3):
    return cyl(cx, cy, z0, r, h).cut(cyl(cx, cy, z0 + t, r - t, h))


_step_cache = {}


def step(pid, cx, cy, z0, rot=0.0):
    """place a fabricated part's STEP model: centred on cx, cy, bottom at z0, rotated about Z."""
    if pid not in _step_cache:
        _step_cache[pid] = cq.importers.importStep(str(HERE / "step" / f"{pid}.step")).val()
    s = _step_cache[pid].copy()
    if rot:
        s = s.rotate(Vector(0, 0, 0), Vector(0, 0, 1), rot)
    return s.move(Location(Vector(cx, cy, z0)))


def lay(tag):
    for e in LAY["equipment"]:
        if e["tag"] == tag:
            return e
    raise KeyError(tag)


def lay_box(tag):
    """layout footprint -> (x0, y0, w, h, cx, cy); size from the layout, else equipment.json footprint."""
    e = lay(tag)
    w, h = e.get("size") or EQ[tag]["footprint_mm"][:2]
    if e.get("rot") in (90, 270):
        w, h = h, w
    return e["x"], e["y"], w, h, e["x"] + w / 2, e["y"] + h / 2


# ---- building -----------------------------------------------------------------------------------
WALL_H, WALL_T = 1100.0, 150.0     # cut-away walls so the equipment shows; real walls run to 3,658 [144]


def building():
    for r in LAY["rooms"]:
        z = r["zone"].split()[0]
        col = FLOOR.get(z, FLOOR["support"])
        add(box(r["x"], r["y"], -60, r["w"], r["h"], 60), col, f"floor {r['name']}")
    W, H = LAY["building"]["w"], LAY["building"]["h"]
    doors = LAY["doors"]

    def wall_run(x0, y0, x1, y1):
        horiz = y0 == y1
        cuts = []
        for d in doors:
            if horiz and d["side"] in ("S", "N") and abs(d["y"] - y0) < 1 and x0 <= d["x"] < x1:
                cuts.append((d["x"], d["x"] + d["w"]))
            if not horiz and d["side"] in ("E", "W") and abs(d["x"] - x0) < 1 and y0 <= d["y"] < y1:
                cuts.append((d["y"], d["y"] + d["w"]))
        a, b = (x0, x1) if horiz else (y0, y1)
        segs, cur = [], a
        for c0, c1 in sorted(cuts):
            if c0 > cur:
                segs.append((cur, c0))
            cur = max(cur, c1)
        if cur < b:
            segs.append((cur, b))
        for s0, s1 in segs:
            if horiz:
                add(box(s0, y0 - WALL_T / 2, 0, s1 - s0, WALL_T, WALL_H), WALL, "wall")
            else:
                add(box(x0 - WALL_T / 2, s0, 0, WALL_T, s1 - s0, WALL_H), WALL, "wall")

    # exterior and the interior partitions that the layout's rooms define
    wall_run(0, 0, W, 0); wall_run(0, H, W, H); wall_run(0, 0, 0, H); wall_run(W, 0, W, H)
    wall_run(0, 4000, W, 4000)            # warehouse / process line
    wall_run(9000, 0, 9000, 4000)         # receiving / shipping
    wall_run(2000, 4000, 2000, H)         # support / dosing
    wall_run(0, 7000, 2000, 7000)         # vestibule / office
    wall_run(8800, 4000, 8800, H)         # dosing / pack
    # outside dust collector pad
    add(box(600, H + 400, -60, 2000, 1600, 60), FLOOR["Z0"], "collector pad")


# ---- receiving, storage, shipping ---------------------------------------------------------------------
def bag(x, y, z, w=400, d=600, h=150, col=KRAFT):
    add(box(x, y, z, w, d, h), col, "bag")


def pallet(x, y, z=0, w=1219, d=1016):
    for i in range(5):
        add(box(x, y + i * (d - 90) / 4, z + 100, w, 90, 20), WOOD, "pallet deck")
    for i in range(3):
        add(box(x, y + i * (d - 90) / 2, z, w, 90, 100), WOOD, "pallet stringer")
    return z + 120


def bag_stack(x, y, z, layers, col=KRAFT):
    for k in range(layers):
        for i in range(3):
            for j in range(2):
                bag(x + 10 + i * 400, y + 10 + j * 500, z + k * 155, 390, 490, 150, col)


def receiving():
    x0, y0, w, h, cx, cy = lay_box("P1-101")
    add(box(x0, y0, 0, w, h, 90), DARK, "floor scale")
    add(box(x0 + w, y0 + 200, 0, 600, w - 400, 40), DARK, "floor scale ramp")
    add(box(x0 + w + 80, y0 + h - 100, 0, 60, 60, 1100), SSB, "indicator post")
    add(box(x0 + w + 20, y0 + h - 130, 1100, 180, 120, 160), CAB, "indicator")
    anchor("P1-101", "Floor scale 1,000 lb", cx, cy, 120, "buy")
    for t in ("SH-1", "SH-2", "SH-3", "SH-4", "SH-5"):
        x0, y0, w, h, cx, cy = lay_box(t)
        for px in (x0, x0 + w - 25):
            for py in (y0, y0 + h - 25):
                add(box(px, py, 0, 25, 25, 1880), SSB, "shelf post")
        for k, z in enumerate((150, 600, 1100, 1600)):
            add(box(x0, y0, z, w, h, 20), SSB, "wire shelf")
            for i in range(3):
                bag(x0 + 40 + i * 490, y0 + 60, z + 20, 450, h - 120, 220 if k < 3 else 160, KRAFT if (i + k) % 2 else (0.85, 0.75, 0.55))
    anchor("P1-102", "NSF shelving (6)", lay_box("SH-3")[4], lay_box("SH-3")[5], 1900, "buy")
    x0, y0, w, h, _, _ = lay_box("PAL-RM")
    for i in range(2):
        z = pallet(x0 + i * 1260, y0 + 90)
        bag_stack(x0 + i * 1260, y0 + 90, z, 6, (0.88, 0.86, 0.80) if i == 0 else (0.70, 0.25, 0.18))
    anchor("PAL-RM", "Salt, garlic, paprika pallets", x0 + 1250, y0 + 600, 1100, "stock")
    x0, y0, w, h, cx, cy = lay_box("P1-103")
    add(box(x0, y0 + 120, 0, 1150, 160, 80), RED, "pallet truck fork")
    add(box(x0, y0 + 410, 0, 1150, 160, 80), RED, "pallet truck fork")
    add(box(x0 + 1150, y0 + 100, 0, 300, 490, 300), RED, "pallet truck pump")
    add(tube((x0 + 1300, cy, 300), (x0 + 1550, cy, 1220), 18), DARK, "pallet truck handle")
    anchor("P1-103", "Pallet truck", cx, cy, 400, "buy")
    x0, y0, w, h, _, _ = lay_box("FG-1")
    for i in range(3):
        z = pallet(x0 + i * 1240, y0 + 140)
        add(box(x0 + i * 1240 + 20, y0 + 160, z, 1180, 980, 1100), WRAP, "wrapped cases")
    anchor("FG-1", "Finished goods (3 days)", x0 + 1850, y0 + 650, 1300, "stock")


# ---- dosing station: ring, bins, feeders, hopper, valve ------------------------------------------------
H_RING, Y_BIN, Y_FEED, Y_LID, Y_HOP, Y_VALVE = 2210, 1730, 1380, 1231, 650, 550
R_BIN, R_INLET = 1250.0, 280.0
FA = Y_BIN - 204.0                # built feeder barrel axis (bin outlet flange on the transition top)


def dosing():
    x0, y0, w, h, XC, YC = lay_box("P1-210")
    add(step("P1-210", XC, YC, 0), SS, "P1-210 ring frame")
    anchor("P1-210", "Bin ring frame (12 positions)", XC + 1600, YC, 2235, "build")
    names = {b["bin"]: b["name"] for b in DOS["bins"]}
    for k in range(12):
        a = math.radians(90 - 30 * k)          # B01 north, clockwise as on the ring plan
        bx, by = XC + R_BIN * math.cos(a), YC + R_BIN * math.sin(a)
        bid = f"B{k + 1:02d}"
        used = bid in names
        if used:
            add(step("P1-211", bx, by, Y_BIN, rot=math.degrees(a)), SS, f"P1-211 bin {bid}")
            add(cyl(bx, by, Y_BIN + 662, 120, 4), (0.95, 0.95, 0.95), "bin label")
            # feeder: body tube from under the bin outlet inward, motor outboard, spout to the hopper
            # built feeder P1-212: inlet flange under the bin outlet, screw runs inward, gearmotor outboard (P1-212-GA)
            ux, uy = math.cos(a), math.sin(a)
            machine("P1-212", bx, by, FA, rot=math.degrees(a) + 180)
            p_out = (XC + (R_BIN + 410) * ux, YC + (R_BIN + 410) * uy, FA)
            sx, sy = XC + (R_BIN - 580) * ux, YC + (R_BIN - 580) * uy
            hx, hy = XC + (R_INLET + 10) * ux, YC + (R_INLET + 10) * uy
            add(tube((sx, sy, FA - 132), (hx, hy, Y_LID + 4), 50), (0.85, 0.93, 0.98), "P1-214 BFM boot")
            add(cbox(bx + 330 * ux, by + 330 * uy, Y_BIN + 80, 40, 40, 120), (0.15, 0.55, 0.85), "P1-213 level fork")
            if k in (0, 6):
                anchor("P1-212" if k == 0 else "P1-211", "Screw feeder, built (9)" if k == 0 else "Ingredient bin 5 cu ft (9 used)",
                       *(p_out[:2] if k == 0 else (bx, by)), FA + 200 if k == 0 else Y_BIN + 700, "build")
        else:
            add(cyl(bx, by, Y_BIN + 300, 200, 6), SS, f"blank plate {bid}")
    # weigh hopper on 3 load cells, valve under it
    add(step("P1-220", XC, YC, Y_HOP), SS, "P1-220 weigh hopper")
    anchor("P1-220", "Weigh hopper on 3 load cells", XC + 420, YC, Y_LID, "build")
    for k in range(3):
        a = math.radians(90 + 120 * k)
        add(cbox(XC + 470 * math.cos(a), YC + 470 * math.sin(a), Y_HOP + 330, 90, 90, 70), SSB, "P1-221 load cell mount")
    add(cyl(XC, YC, Y_VALVE, 70, 100), SSB, "P1-223 butterfly valve body")
    add(cbox(XC + 150, YC, Y_VALVE + 10, 180, 110, 110), (0.25, 0.25, 0.30), "P1-223 actuator")
    anchor("P1-223", "Butterfly valve, 24 V actuator", XC + 200, YC, Y_VALVE + 60, "buy")
    # 4-step platform
    x0, y0, w, h, cx, cy = lay_box("P1-227")      # 800 wide (x), 1300 long (y); climbs north toward the ring
    w, h = min(w, h), max(w, h)
    x0, y0 = cx - w / 2, cy - h / 2
    for i in range(4):
        add(box(x0, y0 + i * 230, 254 * (i + 1) - 30, w, 300, 30), (0.75, 0.77, 0.80), "platform step")
    add(box(x0, y0 + 690, 1016 - 30, w, h - 690, 30), (0.75, 0.77, 0.80), "platform top")
    for px in (x0, x0 + w - 30):
        add(box(px, y0, 0, 30, 30, 260), YEL, "platform leg")
        add(box(px, y0 + h - 30, 0, 30, 30, 1016), YEL, "platform leg")
        add(tube((px + 15, y0 + 60, 900), (px + 15, y0 + 700, 1900), 16), YEL, "handrail")
        add(tube((px + 15, y0 + 700, 1900), (px + 15, y0 + h - 15, 1900), 16), YEL, "handrail")
        add(tube((px + 15, y0 + h - 15, 1016), (px + 15, y0 + h - 15, 1900), 16), YEL, "handrail post")
    anchor("P1-227", "4-step platform", cx, cy, 1950, "buy")
    # controller and drives on the wall
    x0, y0, w, h, cx, cy = lay_box("P1-225")
    add(box(x0, y0 - 150, 800, w, h, 900), CAB, "P1-225 panel")
    add(box(x0 + 20, y0 - 150 + h, 820, w - 40, 6, 860), (0.80, 0.81, 0.82), "panel door")
    add(cyl(x0 + 80, y0 - 150 + h + 6, 1600, 25, 30, (0, 1, 0)), RED, "e-stop")
    anchor("P1-225", "PLC panel + 9 drives", cx, y0, 1750, "buy")
    return XC, YC


# ---- flexible screw, blender on riser, sieve, drum ------------------------------------------------------
def blending(XC, YC):
    x0, y0, w, h, BCX, BCY = lay_box("P1-301")      # rotated 90: long axis along Y, gearmotor north, drum rolls in from the south
    machine("P1-301", BCX, BCY, 0, rot=90)
    add(step("P1-302", BCX, BCY - 110, PM.Z_FL + 3, rot=90), SS, "P1-302 grate and hood")
    anchor("P1-302", "Bag-dump grate + dust hood", BCX, BCY - 110, PM.Z_FL + 330, "build")
    anchor("P1-301", "Ribbon blender 6 cu ft, built", BCX - 450, BCY, PM.Z_AX + 200, "build")
    # drum on its dolly under the valve, drum-top sifter on the rim (seat 1,054, inlet 1,235)
    add(step("P1-309", BCX, BCY, 80), SS, "P1-309 dolly")
    for k in range(4):
        a = math.radians(45 + 90 * k)
        add(cyl(BCX + 250 * math.cos(a), BCY + 250 * math.sin(a), 0, 40, 80), DARK, "caster")
    add(hollow_cyl(BCX, BCY, 140, 292, 914, 6), DRUM, "P1-308 55 gal drum")
    add(hollow_cyl(BCX, BCY, 150, 284, 900, 1), LINER, "drum liner")
    anchor("P1-308", "55 gal drum on dolly", BCX - 350, BCY - 350, 700, "buy")
    add(step("P1-304", BCX, BCY, 994, rot=90), SS, "P1-304 drum-top sifter")
    add(cyl(BCX, BCY, 1094, 228, 30), (0.60, 0.62, 0.64), "P1-305 screen frame")
    add(cbox(BCX + 350, BCY, 1074, 200, 140, 120), MOTOR, "P1-306 vibrator")
    add(cyl(BCX, BCY, 1235, 50, PM.Z_TB - 28.6 - 110 - 1235), (0.97, 0.95, 0.88), "cotton sock")
    anchor("P1-304", "Drum-top sifter 12 mesh + magnet", BCX + 420, BCY - 300, 1250, "build")
    L, Wt = 1000.0, 560.0
    # flexible screw from the intake under the hopper valve up to the blender inlet
    ix, iy = XC + 0, YC - 0
    intake = cone(ix, iy, 120, 180, 380, Y_VALVE - 120).cut(cone(ix, iy, 125, 175, 375, Y_VALVE - 120))
    add(intake, SSB, "P1-224 intake hopper")
    add(cbox(ix, iy, 0, 520, 520, 120), SSB, "intake base")
    add(cyl(ix, iy, Y_VALVE - 6, 380, 6), (0.55, 0.56, 0.58), "intake grate")
    top = (BCX, BCY + 330, PM.Z_FL + 170)          # cover inlet at local x +330 (rotated 90 = +Y)
    add(tube((ix, iy, 300), top, 45), (0.80, 0.82, 0.84), "P1-224 flexible screw tube")
    add(tube(top, (top[0], top[1], PM.Z_FL + 25), 60), SSB, "screw discharge")
    add(cbox(top[0], top[1] - 80, top[2] + 20, 260, 260, 220), MOTOR, "P1-224 screw drive 1 HP")
    mid = [(ix + top[0]) / 2, (iy + top[1]) / 2, (300 + top[2]) / 2]
    add(tube((mid[0], mid[1], 0), (mid[0], mid[1], mid[2]), 30), SSB, "screw mid support")
    anchor("P1-224", "Flexible screw (hand adds at the intake)", mid[0], mid[1], mid[2] + 150, "buy")
    return BCX, BCY, top


# ---- weigh bench, tumbler, mill, QC hold -------------------------------------------------------------
def bench_side():
    x0, y0, w, h, cx, cy = lay_box("P1-206")
    add(step("P1-206", cx, cy, 0), SS, "P1-206 weigh bench")
    add(step("P1-207", cx, y0 + 125, 914), SS, "P1-207 backdraft hood")
    anchor("P1-206", "Weigh bench + backdraft hood", cx, cy, 1650, "build")
    add(cbox(cx - 350, cy + 60, 914, 500, 400, 100), WHITE, "P1-201 bench scale 60 kg")
    add(cbox(cx - 350, cy - 190, 1014, 260, 40, 160), DARK, "scale terminal")
    add(cbox(cx + 200, cy + 80, 914, 350, 300, 110), WHITE, "P1-202 precision scale")
    add(cyl(cx + 200, cy + 80, 1024, 120, 140), (0.85, 0.92, 0.98), "draft shield")
    add(cbox(cx + 560, cy + 60, 914, 230, 200, 180), DARK, "P1-204 label printer")
    anchor("P1-201", "Scales 60 kg + 6 kg x 0.1 g", cx - 100, cy + 100, 1080, "buy")
    # MES PC on the bench end
    add(cbox(cx + 560, cy - 200, 914, 60, 200, 30), DARK, "monitor foot")
    add(cbox(cx + 560, cy - 200, 960, 30, 540, 330), DARK, "P1-205 touch monitor")
    anchor("P1-205", "MES PC + touch screen", cx + 560, cy - 200, 1300, "buy")
    # tumbler on a small stand
    x0, y0, w, h, cx, cy = lay_box("P1-208")
    for px in (x0 + 20, x0 + w - 60):
        for py in (y0 + 20, y0 + h - 60):
            add(box(px, py, 0, 40, 40, 760), SS, "tumbler stand leg")
    add(box(x0, y0, 760, w, h, 20), SS, "tumbler stand top")
    add(step("P1-208", cx, cy, 780), SS, "P1-208 premix tumbler")
    add(tube((cx - 150, cy, 780 + 150), (cx + 150, cy, 780 + 150), 110), SSB, "5 qt pail")
    anchor("P1-208", "Premix pail tumbler", cx, cy, 1100, "build")
    # hammer mill on its stand, feed hopper with magnet, pail under
    x0, y0, w, h, MX, MY = lay_box("P1-320")
    for px in (MX - 350, MX + 300):
        for py in (MY - 250, MY + 200):
            add(box(px, py, 0, 50, 50, 900), SSB, "mill stand leg")
    add(cbox(MX, MY, 850, 700, 500, 50), SSB, "mill stand top")
    add(cbox(MX, MY, 250, 700, 500, 40), SSB, "mill stand shelf")
    add(tube((MX - 250, MY, 1125), (MX + 250, MY, 1125), 230), SSB, "P1-320 mill housing")
    add(cbox(MX, MY, 900, 500, 420, 180), SSB, "mill base")
    add(tube((MX + 250, MY, 1125), (MX + 670, MY, 1125), 140), MOTOR, "mill motor 2 HP")
    add(cbox(MX + 700, MY - 350, 600, 200, 120, 260), CAB, "mill starter")
    add(cone(MX, MY, 1350, 55, 150, 200), SS, "P1-322 feed hopper")
    add(cbox(MX, MY, 1430, 320, 320, 40), (0.70, 0.20, 0.20), "P1-321 grate magnet")
    add(cone(MX, MY, 744, 52, 55, 150), SS, "P1-322 discharge transition")
    add(hollow_cyl(MX, MY, 290, 150, 360, 3), WHITE, "5 gal pail")
    anchor("P1-320", "Hammer mill (whole spices)", MX - 100, MY, 1450, "buy")
    anchor("P1-321", "Feed magnet + hopper P1-322", MX, MY, 1600, "build")
    # QC hold: 6 drums on dollies
    x0, y0, w, h, cx, cy = lay_box("HOLD-1")
    for i in range(2):
        for j in range(3):
            dx, dy = x0 + 330 + i * 640, y0 + 330 + j * 620
            add(step("P1-309", dx, dy, 80), SS, "dolly")
            add(cyl(dx, dy, 105, 292, 914), DRUM, "drum")
            add(cyl(dx, dy, 1019, 300, 25), DRUM, "drum lid")
            add(cbox(dx, dy - 292, 600, 160, 4, 120), YEL, "HOLD tag")
    anchor("HOLD-1", "QC hold: drums on dollies", cx, cy, 1150, "stock")
    # dust-rated vacuum and hand sink
    add(cyl(8300, 11500, 0, 300, 900), (0.20, 0.45, 0.25), "P1-702 dust vacuum")
    anchor("P1-702", "Dust-rated vacuum", 8300, 11500, 950, "buy")
    add(cbox(1700, 5900, 750, 400, 400, 250), SSB, "P1-704 hand sink")
    add(cbox(1700, 5900, 0, 200, 200, 750), SSB, "sink pedestal")
    anchor("P1-704", "Hands-free sink", 1700, 5900, 1050, "buy")


# ---- pack bench ------------------------------------------------------------------------------------
def jar(x, y, z, cap=True, label=False):
    add(cyl(x, y, z, 44, 120), (0.93, 0.93, 0.90), "jar")
    if label:
        add(cyl(x, y, z + 25, 45, 70), (0.80, 0.25, 0.15), "jar label")
    if cap:
        add(cyl(x, y, z + 120, 46, 20), RED, "cap")


# ---- machines built in house (p1_machines.py) ---------------------------------------------------------
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import p1_machines as PM  # noqa: E402

_mcache = {}
BCOL = {"belt": BELT, "detector_head": SSB, "valve": SSB, "screw": SS, "label_rolls": WHITE, "auger_tooling": SS, "pulleys": SSB,
        "rollers": DARK, "chuck": GRN, "bearings": SSB}


def _solid(wp):
    v = [o for o in wp.vals() if isinstance(o, cq.Shape)]
    return v[0] if len(v) == 1 else cq.Compound.makeCompound(v)


def machine(mid, cx, cy, z0=0.0, rot=0.0):
    """place a built machine: our parts (stainless) and its bought parts, machine origin at cx, cy, z0, rotated about Z."""
    if mid not in _mcache:
        m = next(m for m in PM.MACHINES if m["id"] == mid)
        sh = [(p["id"], _solid(PM.placed(p["fn"](), p.get("place"))), SS) for p in m["parts"]]
        sh += [(f"{mid} {k}", _solid(v), BCOL.get(k, MOTOR)) for k, v in PM.BOUGHT_FN[mid]().items()]
        _mcache[mid] = sh
    for name, s, col in _mcache[mid]:
        c = s.copy()
        if rot:
            c = c.rotate(Vector(0, 0, 0), Vector(0, 0, 1), rot)
        add(c.move(Location(Vector(cx, cy, z0))), col, name)


def table(tag):
    x0, y0, w, h, cx, cy = lay_box(tag)
    add(step("P1-206", cx, cy, 0), SS, f"P1-409 table {tag}")
    return x0, y0, w, h, cx, cy, 914


def pack():
    # built servo auger filler P1-401 (P1-401-GA): column at the back (+y), foot switch at the front
    x0, y0, w, h, cx, cy = lay_box("P1-401")
    machine("P1-401", cx, cy)
    add(cbox(cx, cy - 60, PM.Z_NEST + 3, 120, 120, 15), (0.95, 0.95, 0.95), "P1-410 printed nest")
    jar(cx, cy - 60, PM.Z_NEST + 18, cap=False)
    anchor("P1-401", "Servo auger filler, built", cx + 300, cy, 1900, "build")
    # capping + seal table: built spindle capper P1-412, induction sealer
    x0, y0, w, h, cx, cy, z = table("TBL-1")
    machine("P1-412", cx - 450, cy, z)
    jar(cx - 450, cy - 40, z + 12)
    add(cbox(cx + 250, cy, z, 220, 120, 280), (0.25, 0.30, 0.38), "P1-403 induction sealer")
    add(tube((cx + 250, cy - 60, z + 200), (cx + 250, cy - 260, z + 200), 40), DARK, "sealer head")
    for i in range(5):
        jar(cx - 150 + i * 110, cy + 250, z, cap=i < 3)
    anchor("P1-412", "Spindle capper, built", cx - 450, cy, z + 800, "build")
    anchor("P1-403", "Induction cap sealer", cx + 250, cy, z + 350, "buy")
    # label table: LX910 printer, built wrap labeler P1-404
    x0, y0, w, h, cx, cy, z = table("TBL-2")
    add(cbox(cx - 380, cy, z, 500, 450, 270), WHITE, "P1-405 LX910 printer")
    machine("P1-404", cx + 330, cy, z)
    for i in range(4):
        jar(cx - 100 + i * 110, cy + 280, z, label=True)
    anchor("P1-405", "Colour label printer", cx - 380, cy, z + 330, "buy")
    anchor("P1-404", "Wrap labeler, built", cx + 330, cy, z + 330, "build")
    # built detector conveyor P1-406 with the used detector head P1-418
    x0, y0, w, h, cx, cy = lay_box("P1-406")
    machine("P1-406", cx, cy)
    add(cbox(cx + 400, cy - 330, 0, 400, 300, 550), RED, "locked reject bin")
    add(cyl(cx - 300, cy - 230, 760, 25, 600), DARK, "beacon post")
    add(cyl(cx - 300, cy - 230, 1360, 50, 120), YEL, "beacon")
    for i in range(3):
        jar(cx - 650 + i * 150, cy, PM.Z_BELT, label=True)
    anchor("P1-406", "Detector conveyor, built (used head, CCP-1)", cx, cy, 1500, "build")
    # turntable, checkweigh, case pack
    x0, y0, w, h, cx, cy = lay_box("P1-408")
    add(cyl(cx, cy, 0, 300, 40), SS, "turntable base")
    add(cyl(cx, cy, 40, 60, 830), SS, "turntable column")
    add(step("P1-408", cx, cy, 870), SS, "P1-408 turntable disc")
    for k in range(8):
        a = 2 * math.pi * k / 8
        jar(cx + 290 * math.cos(a), cy + 290 * math.sin(a), 895, label=True)
    anchor("P1-408", "Accumulation turntable", cx, cy, 1150, "build")
    x0, y0, w, h, cx, cy, z = table("TBL-3")
    add(cbox(cx - 250, cy, z, 350, 300, 80), WHITE, "P1-407 checkweigh scale")
    add(cbox(cx - 250, cy - 200, z, 40, 40, 400), DARK, "light post")
    add(cyl(cx - 250, cy - 200, z + 400, 35, 40), GRN, "OK light")
    add(cyl(cx - 250, cy - 200, z + 440, 35, 40), RED, "under light")
    add(cbox(cx + 350, cy, z, 400, 300, 300), (0.95, 0.65, 0.65), "short units bin")
    jar(cx - 250, cy, z + 80, label=True)
    anchor("P1-407", "Checkweigh, every unit", cx - 250, cy, z + 550, "buy")
    x0, y0, w, h, cx, cy, z = table("TBL-4")
    add(cbox(cx - 200, cy, z, 400, 300, 160), KRAFT, "12-ct case")
    add(cbox(cx + 350, cy, z, 300, 250, 200), KRAFT, "case")
    add(cbox(cx + 600, cy - 200, z, 120, 80, 150), DARK, "tape gun")
    anchor("P1-411", "Case pack: tape + case label", cx, cy, z + 300, "buy")
    # packaging stock and pallet being built
    x0, y0, w, h, _, _ = lay_box("PKG")
    z = pallet(x0 + 50, y0 + 100)
    add(box(x0 + 70, y0 + 120, z, 1180, 980, 900), (0.92, 0.92, 0.88), "empty jars (cased)")
    z = pallet(x0 + 1300, y0 + 100)
    add(box(x0 + 1320, y0 + 120, z, 1000, 900, 600), KRAFT, "caps, labels, cases")
    anchor("PKG", "Empty containers, caps, labels", x0 + 1200, y0 + 600, 1200, "stock")
    x0, y0, w, h, _, _ = lay_box("PAL-FG")
    z = pallet(x0, y0)
    for i in range(3):
        for j in range(3):
            add(box(x0 + 20 + i * 400, y0 + 20 + j * 330, z, 390, 320, 200), KRAFT, "case")
    anchor("PAL-FG", "Pallet being built", x0 + 600, y0 + 500, 500, "stock")


# ---- dust collection --------------------------------------------------------------------------------
def dust(XC, YC, BCX, BCY):
    x0, y0, w, h, cx, cy = lay_box("P1-310")
    add(cbox(cx, cy, 0, w, h, 900), (0.40, 0.45, 0.52), "P1-310 hopper stand")
    add(cbox(cx, cy, 900, w, h, 1300), (0.40, 0.45, 0.52), "P1-310 cartridge housing")
    add(tube((cx, cy, 2200), (cx, cy, 2500), 250), MOTOR, "P1-310 fan")
    add(cyl(cx, cy, 0, 280, 150), (0.25, 0.25, 0.27), "dust bin")
    anchor("P1-310", "Cartridge dust collector 1,400 cfm", cx, cy, 2600, "buy")
    ZD = 3150.0
    bench = lay_box("P1-206")
    mill = lay_box("P1-320")
    pick = [("weigh hood 300 cfm", (bench[4], bench[1] + 125, 914 + 680)),
            ("hopper vent 150 cfm", (XC + 200, YC + 200, Y_LID + 40)),
            ("blender grate 250 cfm", (BCX, BCY - 110, PM.Z_FL + 330)),
            ("sifter drum vent 200 cfm", (BCX - 250, BCY - 250, 1180)),
            ("mill 150 cfm", (mill[4], mill[5] + 200, 1500))]
    HY = 11600.0                   # header run along the north side of the dosing room, out to the pad
    # the sifter vent sits under the trough: its pickup leaves sideways, clear of the blender frame, then rises
    sx, sy, sz = pick[3][1]
    add(tube((sx, sy, sz), (BCX - 700, sy, sz), 50), DUCT, "duct sifter vent")
    pick[3] = (pick[3][0], (BCX - 700, sy, sz))
    for nm, (px, py, pz) in pick:
        add(tube((px, py, pz), (px, py, ZD), 50), DUCT, f"duct riser {nm}")
        add(tube((px, py, ZD), (px, HY, ZD), 50), DUCT, f"duct branch {nm}")
        add(cyl(px, py, ZD - 150, 60, 60), (0.90, 0.30, 0.20), "blast gate")
    xs = [p[1][0] for p in pick] + [cx]
    add(tube((max(xs), HY, ZD), (cx, HY, ZD), 100), DUCT, "duct header 8 in")
    add(tube((cx, HY, ZD), (cx, cy, ZD), 100), DUCT, "duct to collector")
    add(tube((cx, cy, ZD), (cx, cy, 2200), 100), DUCT, "duct drop")


def main():
    building()
    receiving()
    XC, YC = dosing()
    BCX, BCY, _ = blending(XC, YC)
    bench_side()
    pack()
    dust(XC, YC, BCX, BCY)
    ASSY.save(str(OUT / "DH-P1-plant.step"))
    ASSY.save(str(OUT / "DH-P1-plant.glb"), exportType="GLTF", tolerance=2.0, angularTolerance=0.3)
    (OUT / "anchors.json").write_text(json.dumps(ANCH, indent=1))
    print(f"{_n[0]} solids, {len(ANCH)} labels")


if __name__ == "__main__":
    main()
