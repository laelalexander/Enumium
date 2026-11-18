"""Phase 1 machines built in house: ribbon blender, bin feeders, auger filler, detector conveyor, spindle capper, wrap labeler.

Each machine is a set of fabricated weldments (our STEP, part sheet with every hole, DXF of the flat parts) plus bought
components (motors, bearings, seals, sensors, controls; each with maker, model class and source in machines.json).
A general-arrangement (GA) sheet per machine shows the assembly at true scale with a ballooned item list.

Design rules (references/food-safety-design.md): product contact 316L, continuous welds ground flush, #4 finish,
no threads, ledges or bearings in the product zone, tool-free strip-down. Bought precision parts stay bought:
servo, gearmotors, bearings, seals, flighting, auger tooling, belts, sensors.

Usage: python3 p1_machines.py  ->  step/<id>.step, stl/<id>.stl, ../drawings/machines/*.svg, ../dxf/*, machines.json
"""
import json
import math
import pathlib
import sys
from html import escape

import cadquery as cq
from cadquery import Vector

HERE = pathlib.Path(__file__).parent
P1 = HERE.parent
sys.path.insert(0, str(P1.parents[2] / "skills" / "anatomy" / "tools" / "plant"))
import partsheet  # noqa: E402
from p1_parts import IN, GA14, GA11, TC4_FL, TC4_TUBE, PROJECT, ferrule4, sqt, dxf  # noqa: E402

LABOR = 65.0                      # $/h shop rate (same as the BOM)
SS_KG = 7.0                       # $/kg 304/316L sheet and tube, cut-to-size estimate


def W():
    return cq.Workplane("XY")


def tube_x(x0, x1, od, t, y=0.0, z=0.0):
    return W().circle(od / 2).circle(od / 2 - t).extrude(x1 - x0).rotate((0, 0, 0), (0, 1, 0), 90).translate((x0, y, z))


def rod(p1, p2, d):
    a, b = Vector(*p1), Vector(*p2)
    v = b - a
    return cq.Workplane(obj=cq.Solid.makeCylinder(d / 2, v.Length, a, v.normalized()))


def ribbon(r_out, width, thick, pitch, length, x0, lefthand, phase=0.0):
    """Helical ribbon about the X axis: rectangle width (radial) x thick swept on a helix of mean radius r_out - width/2."""
    rm = r_out - width / 2
    helix = cq.Wire.makeHelix(pitch, length, rm, lefthand=lefthand)
    prof = cq.Workplane("XZ", origin=(rm, 0, 0)).rect(width, thick)
    s = prof.sweep(cq.Workplane(obj=helix), isFrenet=True)
    return s.rotate((0, 0, 0), (0, 0, 1), phase).rotate((0, 0, 0), (0, 1, 0), 90).translate((x0, 0, 0))


# =============================================================================================== blender P1-301
TR_R, TR_W, TR_L, TR_SIDE, TR_T = 280.0, 560.0, 900.0, 300.0, 3.0      # inside radius, width, length, side above axis, wall
Z_TB = 1400.0                     # trough bottom (outside): valve + sock into the drum-top sifter P1-304 on a drum on its dolly (rim 1,054)
Z_AX = Z_TB + TR_T + TR_R         # agitator axis 1,683
Z_FL = Z_AX + TR_SIDE             # top flange 1,983
SHAFT_D = 60.0
X_END = TR_L / 2 + 10             # outside face of an end plate


def bl_trough():
    """U-trough 316L 3 mm, 10 mm end plates with seal-gland bolt circle, 6 mm top flange, 4 in TC port at the bottom centre."""
    def u(r, w, ext):
        return W().box(TR_L + ext, w, TR_SIDE).translate((0, 0, TR_SIDE / 2)).union(
            W().circle(r).extrude(TR_L + ext).rotate((0, 0, 0), (0, 1, 0), 90).translate((-(TR_L + ext) / 2, 0, 0)))
    shell = u(TR_R + TR_T, TR_W + 2 * TR_T, 0).cut(u(TR_R, TR_W, 2))
    for sx in (-1, 1):
        plate = (W().box(10, TR_W + 2 * TR_T + 60, TR_SIDE + 30).translate((0, 0, (TR_SIDE + 30) / 2 - 15))
                 .union(W().circle(TR_R + TR_T + 30).extrude(10).rotate((0, 0, 0), (0, 1, 0), 90).translate((-5, 0, 0)))
                 .translate((sx * (TR_L / 2 + 5), 0, 0)))
        plate = plate.cut(W().circle(SHAFT_D / 2 + 4).extrude(40).rotate((0, 0, 0), (0, 1, 0), 90).translate((sx * (TR_L / 2 + 5) - 20, 0, 0)))
        for k in range(4):                                    # M10 gland studs on PCD 130
            a = math.radians(45 + 90 * k)
            plate = plate.cut(W().circle(5.5).extrude(40).rotate((0, 0, 0), (0, 1, 0), 90)
                              .translate((sx * (TR_L / 2 + 5) - 20, 65 * math.cos(a), 65 * math.sin(a))))
        for z in (-200, 150):                                 # 2 x M12 to the frame end plate
            for y in (-(TR_W / 2 + 15), TR_W / 2 + 15):
                plate = plate.cut(W().circle(6.5).extrude(40).rotate((0, 0, 0), (0, 1, 0), 90).translate((sx * (TR_L / 2 + 5) - 20, y, z)))
        shell = shell.union(plate)
    fl = (W().rect(TR_L + 100, TR_W + 2 * TR_T + 80).rect(TR_L, TR_W).extrude(6).translate((0, 0, TR_SIDE - 6)))
    for x in (-400, -133, 133, 400):                          # M8 cover clamps / hinge
        for y in (-(TR_W / 2 + 25), TR_W / 2 + 25):
            fl = fl.cut(W().circle(4.5).extrude(20).translate((x, y, TR_SIDE - 10)))
    shell = shell.union(fl)
    zb = -(TR_R + TR_T)
    shell = shell.cut(W().circle(TC4_TUBE / 2 - 1.65).extrude(60).translate((0, 0, zb - 20)))
    shell = shell.union(ferrule4().translate((0, 0, zb - 28.6)).cut(W().circle(TC4_TUBE / 2 - 1.65).extrude(40).translate((0, 0, zb - 35))))
    return shell.translate((0, 0, Z_AX))


def bl_agitator():
    """Shaft Ø60 316 with two outer ribbons (OD 550, opposed hands push to the centre) and two inner ribbons (OD 320, push out)."""
    x_drive, x_free = X_END + 330, -(X_END + 150)
    shaft = W().circle(SHAFT_D / 2).extrude(x_drive - x_free).rotate((0, 0, 0), (0, 1, 0), 90).translate((x_free, 0, 0))
    shaft = shaft.cut(W().box(80, 18, 7).translate((x_drive - 50, 0, SHAFT_D / 2 - 3)))          # 18 x 11 key for the hollow-shaft gearmotor
    half = TR_L / 2 - 15
    parts = [shaft,
             ribbon(275, 50, 8, 600, half, -half, False), ribbon(275, 50, 8, 600, half, 0, True, phase=180),
             ribbon(165, 40, 8, 450, half, -half, True, phase=90), ribbon(165, 40, 8, 450, half, 0, False, phase=270)]
    a = parts[0]
    for r in parts[1:]:
        a = a.union(r)
    # spokes Ø20 every 90 deg along each half: shaft -> inner ribbon -> outer ribbon
    for side in (-1, 1):
        for k in range(4):
            x = side * (60 + k * 120)
            ang = math.radians(k * 90 + (0 if side < 0 else 45))
            c, s = math.cos(ang), math.sin(ang)
            a = a.union(rod((x, c * 28, s * 28), (x, c * 252, s * 252), 20))
    return a.translate((0, 0, Z_AX))


def bl_cover():
    """3 mm cover: bag-dump opening 600 x 400 for grate P1-302, 4 in TC inlet for the flexible screw, hinge lugs, interlock tab, lift handles."""
    c = W().box(TR_L + 100, TR_W + 2 * TR_T + 80, 3).translate((0, 0, 1.5))
    c = c.cut(W().box(600, 400, 10).translate((-110, 0, 0)))
    c = c.cut(W().circle(TC4_TUBE / 2 - 1.65).extrude(10).translate((330, 0, -2)))
    c = c.union(ferrule4().translate((330, 0, 3)).cut(W().circle(TC4_TUBE / 2 - 1.65).extrude(40).translate((330, 0, 0))))
    c = c.union(W().rect(600 + 12, 400 + 12).rect(600, 400).extrude(25).translate((-110, 0, 3)))          # upstand: no ledge, grate drops in
    for x in (-400, -133, 133, 400):
        for y in (-(TR_W / 2 + 25), TR_W / 2 + 25):
            c = c.cut(W().circle(4.5).extrude(10).translate((x, y, -2)))
    for x in (-250, 250):                                      # hinge knuckles on the back edge
        c = c.union(W().circle(12).circle(6.5).extrude(60).rotate((0, 0, 0), (0, 1, 0), 90).translate((x - 30, TR_W / 2 + 52, 12)))
    c = c.union(W().box(40, 6, 60).translate((TR_L / 2 + 30, -(TR_W / 2 + 40), 30)))                     # interlock actuator tab
    for x in (-300, 300):                                      # lift handle
        c = c.union(rod((x, -(TR_W / 2 + 46), 3), (x, -(TR_W / 2 + 46), 60), 14)).union(rod((x - 60, -(TR_W / 2 + 46), 60), (x + 60, -(TR_W / 2 + 46), 60), 14))
    return c.translate((0, 0, Z_FL))


def bl_frame():
    """Frame: 4 legs 3 in sq 11 ga, end plates 12 mm carrying the flange bearings, saddle cross-members, foot plates, gearmotor torque arm."""
    f = W()
    lx, ly = X_END + 20, TR_W / 2 + 90          # 664 clear between legs: a drum on its dolly (640) rolls in from the free end
    for sx in (-1, 1):
        for sy in (-1, 1):
            f = f.union(sqt(76.2, 76.2, Z_AX + 150, 3.0).translate((sx * lx, sy * ly, (Z_AX + 150) / 2)))
            f = f.union(W().box(150, 150, 12).translate((sx * lx, sy * ly, 6)).faces(">Z").workplane(centerOption="CenterOfBoundBox")
                        .rect(110, 110, forConstruction=True).vertices().hole(14))
        ep = W().box(12, 2 * ly + 76, 520).translate((sx * (lx + 44), 0, Z_AX - 60))
        ep = ep.cut(W().circle(SHAFT_D / 2 + 10).extrude(40).rotate((0, 0, 0), (0, 1, 0), 90).translate((sx * (lx + 44) - 20, 0, Z_AX)))
        for k in range(4):                                     # UCFL212 bolt holes (2 bolt, 4 bolt: use 4-bolt UCF212 pattern 143 sq)
            a = math.radians(45 + 90 * k)
            ep = ep.cut(W().circle(9).extrude(40).rotate((0, 0, 0), (0, 1, 0), 90).translate((sx * (lx + 44) - 20, 101 * math.cos(a), Z_AX + 101 * math.sin(a))))
        f = f.union(ep)
        f = f.union(sqt(2 * lx, 76.2, 76.2, 3.0).translate((0, sx * ly, 320)))
    for x in (-300, 300):                                      # saddles under the trough
        f = f.union(sqt(76.2, 2 * ly, 76.2, 3.0).translate((x, 0, Z_TB - 38)))
        f = f.union(W().box(76, 2 * ly - 76, 10).translate((x, 0, Z_TB + 5)))
    f = f.union(W().box(120, 12, 260).translate((lx + 260, ly - 30, Z_AX - 40)))                       # torque-arm bracket
    return f


def bl_gland():
    """Seal gland follower: ring flange that compresses PTFE packing in the end-plate stuffing box (2 per blender)."""
    g = W().circle(90).circle(SHAFT_D / 2 + 1).extrude(12).union(W().circle(48).circle(SHAFT_D / 2 + 1).extrude(40).translate((0, 0, -28)))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        g = g.cut(W().circle(5.5).extrude(30).translate((65 * math.cos(a), 65 * math.sin(a), -5)))
    return g.rotate((0, 0, 0), (0, 1, 0), 90)


def bought_blender():
    """Envelope models of the bought parts so the GA shows them (gearmotor, bearings, valve, interlock)."""
    gm = W().box(230, 280, 330).translate((X_END + 290, 0, Z_AX - 30)).union(rod((X_END + 400, 0, Z_AX + 80), (X_END + 650, 0, Z_AX + 80), 200))
    br = W()
    for sx in (-1, 1):
        br = br.union(W().box(40, 190, 190).translate((sx * (X_END + 20 + 44 + 26), 0, Z_AX)))
    valve = W().circle(70).extrude(110).translate((0, 0, Z_TB - 28.6 - 110)).union(W().box(160, 110, 110).translate((150, 0, Z_TB - 90)))
    return dict(gearmotor=gm, bearings=br, valve=valve)


# =============================================================================================== feeder P1-212
_FD = {}


def _fd_model():
    """rev B feeder from machines/P1-212 (design.py + model.py): the full drawing set P1-212-000..900 is drawn from the same model."""
    if not _FD:
        import importlib.util
        d = P1 / "machines" / "P1-212"
        saved = sys.modules.pop("design", None)
        sys.path.insert(0, str(d))
        try:
            spec = importlib.util.spec_from_file_location("p1_212_model", d / "model.py")
            m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
            _FD["parts"], _FD["bought"] = m.build(), m.bought()
        finally:
            sys.path.remove(str(d)); sys.modules.pop("design", None)
            if saved is not None:
                sys.modules["design"] = saved
    return _FD


def fd_barrel():
    """Feeder P1-212 rev B, all made parts (barrel weldment, screw, drive cartridge, tail cap, lantern, guard) in the feeder frame:
    x along the screw, 0 under the bin outlet, +x toward the hopper; z 0 on the axis (1,526 AFF)."""
    out = None
    for pid, s in _fd_model()["parts"].items():
        out = s if out is None else out.union(s, clean=False)
    return out


def bought_feeder():
    b = _fd_model()["bought"]
    return {"gearmotor": b["P1-216"], "coupling": b["P1-244"], "bearings": b["P1-241"], "clamp": b["P1-247"], "sleeve": b["P1-214"]}


# =============================================================================================== auger filler P1-401
Z_NEST = 855.0                   # jar-12 stage top (stage plate at 89 above the 760 cabinet top + 6): container on the printed nest
Z_HOP = 1118.5                   # hopper outlet TC clamp face (machines/P1-401 design.py Z_TC)
_FL = {}


def _fl_model():
    """rev B servo auger filler from machines/P1-401 (design.py + model.py): the full drawing set P1-401-000..900 is drawn from the same model."""
    if not _FL:
        import importlib.util
        d = P1 / "machines" / "P1-401"
        saved = sys.modules.pop("design", None)
        sys.path.insert(0, str(d))
        try:
            spec = importlib.util.spec_from_file_location("p1_401_model", d / "model.py")
            m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
            _FL["parts"], _FL["bought"] = m.build(), m.bought()
        finally:
            sys.path.remove(str(d)); sys.modules.pop("design", None)
            if saved is not None:
                sys.modules["design"] = saved
    return _FL


def fl_all():
    """Filler P1-401 rev B, all made parts (cabinet, column, drive head, hopper, agitator, stage) in the filler frame:
    auger axis at x 0, y 0; column at y +300; floor z 0."""
    out = None
    for pid, s in _fl_model()["parts"].items():
        out = s if out is None else out.union(s, clean=False)
    return out


def bought_filler():
    b = _fl_model()["bought"]
    return {"servo": b["P1-413"], "belt drive": b["P1-431"], "agitator": b["P1-414"], "chain drive": b["P1-432"], "index plunger": b["P1-434"],
            "hmi": b["P1-416"], "container sensor": b["P1-435"], "pedal": b["P1-417"], "feet": b["P1-443"], "auger_tooling": b["P1-415J"].union(b["P1-415A"])}


# =============================================================================================== detector conveyor P1-406
C_L, C_W, Z_BELT = 1500.0, 160.0, 905.0


def cv_frame():
    """Conveyor weldment: 2 bent side channels 120 x 40 x 2.5, slider bed 3 mm, 4 legs 40 sq with feet, pulley bearing slots, reject-arm boss."""
    f = W()
    for sy in (-1, 1):
        ch = W().box(C_L, 2.5, 120).translate((0, sy * (C_W / 2 + 12), Z_BELT - 60))
        ch = ch.union(W().box(C_L, 40, 2.5).translate((0, sy * (C_W / 2 + 12 + 18.75), Z_BELT - 118)))
        for x in (-C_L / 2 + 40, C_L / 2 - 40):
            ch = ch.cut(W().box(50, 20, 22).translate((x, sy * (C_W / 2 + 12), Z_BELT - 30)))          # take-up slot for the pulley shaft
        f = f.union(ch)
        for x in (-C_L / 2 + 150, C_L / 2 - 150):
            f = f.union(sqt(40, 40, Z_BELT - 120, 2.0).translate((x, sy * (C_W / 2 + 12 + 20), (Z_BELT - 120) / 2)))
            f = f.union(W().box(80, 80, 8).translate((x, sy * (C_W / 2 + 32), 4)))
    f = f.union(W().box(C_L - 160, C_W + 22, 3).translate((0, 0, Z_BELT - 12)))
    for x in (-C_L / 2 + 150, C_L / 2 - 150):
        f = f.union(sqt(40, C_W + 64, 40, 2.0).translate((x, 0, 300)))
    return f


def bought_conveyor():
    belt = W().box(C_L - 60, 152, 4).translate((0, 0, Z_BELT - 2)).union(W().box(C_L - 60, 152, 4).translate((0, 0, Z_BELT - 64)))
    pul = rod((-C_L / 2 + 40, -90, Z_BELT - 32), (-C_L / 2 + 40, 90, Z_BELT - 32), 60).union(rod((C_L / 2 - 40, -90, Z_BELT - 32), (C_L / 2 - 40, 90, Z_BELT - 32), 60))
    gm = rod((C_L / 2 - 40, 100, Z_BELT - 32), (C_L / 2 - 40, 330, Z_BELT - 32), 100)
    head = W().box(420, 520, 620).translate((0, 0, Z_BELT - 150 + 310)).cut(W().box(440, 254, 152).translate((0, 0, Z_BELT + 76)))
    rej = W().box(80, 120, 80).translate((350, 170, Z_BELT + 40))
    return dict(belt=belt, pulleys=pul, gearmotor=gm, detector_head=head, reject=rej)


# =============================================================================================== spindle capper P1-412
def cp_frame():
    """Bench capper weldment: 12 mm base plate with container V-nest slot, 50 sq column, carriage plate for an MGN15 rail block,
    motor clamp, lever pivot; the chuck spins the cap down to a set slip torque."""
    base = W().box(400, 350, 12).translate((0, 0, 6)).faces(">Z").workplane(centerOption="CenterOfBoundBox").rect(340, 290, forConstruction=True).vertices().hole(9)
    base = base.cut(W().box(160, 24, 20).translate((0, -40, 6)))
    col = sqt(50.8, 50.8, 650, 3.0).translate((0, 120, 12 + 325))
    rail_plate = W().box(30, 8, 500).translate((0, 120 - 29, 12 + 380))
    car = W().box(120, 10, 140).translate((0, 120 - 60, 12 + 520)).union(W().box(140, 120, 10).translate((0, 10, 12 + 470)))
    car = car.cut(W().circle(26).extrude(20).translate((0, -20, 12 + 460)))
    lever = rod((0, 150, 12 + 640), (0, -220, 12 + 590), 20)
    return base.union(col).union(rail_plate).union(car).union(lever)


def bought_capper():
    gm = W().circle(45).extrude(220).translate((0, -20, 12 + 480))
    clutch = W().circle(40).extrude(50).translate((0, -20, 12 + 420))
    chuck = W().circle(55).circle(46).extrude(40).translate((0, -20, 12 + 375))
    gas = rod((40, 150, 12 + 120), (40, 100, 12 + 470), 22)
    return dict(gearmotor=gm, clutch=clutch, chuck=chuck, gas_spring=gas)


# =============================================================================================== wrap labeler P1-404
def lb_frame():
    """Labeler weldment: 8 mm base, 2 drive-roller bearing blocks, idler arm pivot, unwind and rewind spindle posts, peel-plate bracket."""
    b = W().box(520, 360, 8).translate((0, 0, 4)).faces(">Z").workplane(centerOption="CenterOfBoundBox").rect(460, 300, forConstruction=True).vertices().hole(7)
    for x in (-60, 60):
        for y in (-110, 110):
            b = b.union(W().box(40, 30, 60).translate((x, y, 38)).cut(rod((x, y - 30, 50), (x, y + 30, 50), 13)))
    b = b.union(W().box(20, 20, 160).translate((0, 150, 88)))                         # idler arm post
    b = b.union(W().box(16, 16, 240).translate((-200, 140, 128))).union(W().box(16, 16, 240).translate((200, 140, 128)))   # spindle posts
    peel = W().box(160, 3, 70).translate((140, 120, 140)).rotate((140, 120, 140), (0, 0, 1), -30)
    return b.union(peel)


def bought_labeler():
    rol = rod((-60, -120, 50), (-60, 120, 50), 50).union(rod((60, -120, 50), (60, 120, 50), 50))
    idl = rod((0, 130, 190), (0, -100, 190), 40)
    step = W().box(57, 57, 80).translate((-160, -150, 40))
    rolls = rod((-200, 120, 250), (-200, 40, 250), 180).union(rod((200, 120, 250), (200, 60, 250), 120))
    sens = W().box(60, 30, 40).translate((130, 160, 170))
    return dict(rollers=rol, idler=idl, stepper=step, label_rolls=rolls, gap_sensor=sens)


# =============================================================================================== registry
MACHINES = [
    dict(id="P1-301", title="Ribbon blender 6 cu ft (built)", tag_name="Ribbon blender", qty=1,
         assy_note="Valve outlet 1,260 [49.6] drops through a sock into the drum-top sifter P1-304 on a 55 gal drum (rim 1,054); cover at 1,983 [78.1]",
         parts=[
             dict(id="P1-301-01", fn=bl_trough, title="Blender trough 900 x 560, U r280", material="SS 316L #4, 3 mm; end plates 10 mm; flange 6 mm",
                  process="Laser cut, roll, TIG, ground flush, electropolish or #4", mat_kg=70, labor_h=40, flat="flange", contact=True, qty=1,
                  notes=["Working volume 170 L [6.0 cu ft] at 65 % of 262 L; a 131 L batch is 50 % full",
                         "Ribbon clearance 5 mm to the trough: check with a feeler along the full length before passivating",
                         "Bottom 4 in TC port flush with the trough skin (no dead leg); valve P1-331 clamps to it",
                         "End plates: stuffing box for PTFE packing, 4 x M10 gland studs on PCD 130"],
                  fasteners=lambda f: "M10 gland stud" if abs(f["dia"] - 11) < 1 else ("M12 x 35 A2-70 to frame end plate, 70 N·m" if abs(f["dia"] - 13) < 1 else ("M8 cover clamp" if f["dia"] < 10 else "4 in TC"))),
             dict(id="P1-301-02", fn=bl_agitator, title="Blender agitator: shaft Ø60 + double ribbons", material="SS 316 shaft Ø60 bar; ribbons 316L 8 mm flat bar; spokes Ø20",
                  process="Form ribbons on a helix jig, TIG to spokes, true to 1 mm TIR, balance, polish", mat_kg=45, labor_h=36, flat=None, contact=True, qty=1,
                  notes=["Outer ribbons OD 550 x 50, pitch 600, opposed hands push to the centre; inner OD 320 x 40, pitch 450, push out",
                         "40 rpm (tip 1.15 m/s) from a 2 HP hollow-shaft gearmotor; design torque 360 N·m, shaft stress 17 MPa at 2 x start",
                         "Key 18 x 11 x 80 at the drive end; Ø60 h7 at bearings and packing"],
                  fasteners=lambda f: "Ø60 h7 bearing / packing journal"),
             dict(id="P1-301-03", fn=bl_cover, title="Blender cover with bag-dump opening and screw inlet", material="SS 304 #4, 3 mm; 4 in BPE ferrule",
                  process="Laser cut, TIG, ground", mat_kg=18, labor_h=8, flat="cover", contact=True, qty=1,
                  notes=["Grate P1-302 drops into the 600 x 400 upstand; 4 in TC inlet takes the flexible screw P1-224 discharge",
                         "Interlock tab trips P1-332 when the cover lifts: agitator stops through SR-P1 (cannot be overridden by the PLC)",
                         "Hinged on the back edge; 8 x M8 quick clamps on the flange"],
                  fasteners=lambda f: "M8 quick clamp" if f["dia"] < 10 else ("hinge pin Ø12" if f["dia"] < 20 else "4 in TC")),
             dict(id="P1-301-04", fn=bl_frame, title="Blender frame and bearing end plates", material="SS 304 3 in sq tube 11 ga; plates 12 mm",
                  process="Saw, TIG, ground, passivated", mat_kg=95, labor_h=24, flat="foot", contact=False, qty=1,
                  notes=["Bearings UCF212 (4-bolt, 143 sq) on the 12 mm end plates, outside the product zone with 120 mm drip gap",
                         "Saddles carry the trough at 1,250 [49.2]; anchor 4 x 1/2 in wedge anchors per foot",
                         "Torque arm bracket for the hollow-shaft gearmotor on the drive side"],
                  fasteners=lambda f: "M16 x 50 A2-70 to UCF212, 120 N·m" if f["dia"] > 16 else "1/2 in wedge anchor, 3 in embed, 60 N·m"),
             dict(id="P1-301-05", fn=bl_gland, title="Packing gland follower (2 per blender)", material="SS 316, 12 mm plate + Ø96 tube",
                  process="Laser cut, turn, TIG", mat_kg=3, labor_h=3, flat=None, contact=True, qty=2,
                  place=[(X_END + 12, 0, Z_AX, 0), (-(X_END + 12), 0, Z_AX, 180)],
                  notes=["Compresses 4 rings of PTFE packing 10 mm sq (P1-335) around the Ø60 shaft", "Tighten evenly to stop dust; re-torque after the first run"],
                  fasteners=lambda f: "M10 gland nut, 15 N·m" if f["dia"] < 12 else "Ø61 shaft clearance"),
         ],
         bought=[
             ("P1-333", "Hollow-shaft helical-bevel gearmotor 2 HP, about 40 rpm, Ø60 bore, washdown paint", "NORD Drivesystems", "SK 9022.1 AZBH class, i about 43 (confirm)",
              "https://www.nord.com/", "NORD distributor", 1, 2600, "gearmotor"),
             ("P1-334", "Stainless flange bearing UCF212, Ø60 bore, food-grade grease", "NTN / Dodge (SS insert)", "UCF212 SS or Dodge ULTRA Kleen F4B-SCEZ (confirm)",
              "https://www.dodgeindustrial.com/", "Applied Industrial / Motion", 2, 380, "bearings"),
             ("P1-335", "PTFE packing 10 mm sq, FDA, 4 rings per gland", "Chesterton", "1724 PTFE packing (confirm size)", "https://chesterton.com/", "Chesterton distributor", 1, 120, None),
             ("P1-331", "Sanitary butterfly valve 4 in TC with 24 V DC electric actuator and limit switches (blender discharge)", "Valworx",
              "4 in sanitary butterfly 316L, EPDM, 24 V DC actuator (same as P1-223)", "https://www.valworx.com/", "Valworx", 1, 1400, "valve"),
             ("P1-332", "Cover interlock switch, coded magnetic, stainless", "Schmersal", "BNS 260 class + AES safety module input on SR-P1 (confirm)",
              "https://www.schmersal.com/", "Schmersal distributor", 1, 260, None),
             ("P1-336", "VFD 2 HP for the blender (soft start, 40 rpm trim)", "AutomationDirect", "GS21-22P0 (confirm)", "https://www.automationdirect.com/", "AutomationDirect", 1, 330, None),
         ]),
    dict(id="P1-212", title="Bin screw feeder 2.5 in (built, 9) rev B", tag_name="Bin screw feeder", qty=9,
         full_set="machines/P1-212/drawings/P1-212-001_general_arrangement.svg",
         assy_note="Hangs from the bin outlet flange; spout vertical over the hopper lid stub (R280) with sleeve P1-214; screw pulls out the tail end "
                   "after the hex-nut TC clamp. Full build set: machines/P1-212/drawings/P1-212-drawing-set.pdf (14 sheets)",
         parts=[
             dict(id="P1-212-01", fn=fd_barrel, title="Feeder P1-212 rev B made parts (barrel weldment, screw, drive cartridge, tail cap, lantern, guard)",
                  material="SS 316L A270 tube 2.5 in x 16 ga, 316L plate, 316 bar; 304 lantern/guard; UHMW tail bush",
                  process="Laser, brake, TIG, lathe, mill, polish (see P1-212-100..400)", mat_kg=22, labor_h=16, flat=None, contact=True, qty=9,
                  notes=["Detail drawings: P1-212-001..900 (GA, sections, weldment, flat patterns, screw, drive, tail, lantern, assembly, hardware, E01/E02, ITP)",
                         "Screw Ø56 x pitch 56 on Ø25, supported both ends: drive pin in socket, UHMW bush at the tail; no bearing in the product",
                         "0.044 L/rev at 40 % fill: 150 rpm about 398 L/h fast, 15 rpm about 6 g/s dribble; 0.25 kW i 10.25 gearmotor"],
                  fasteners=lambda f: "M10 x 30 A2-70 + FDA gasket to bin, 25 N·m" if abs(f["dia"] - 11) < 1 else "see P1-212-600"),
         ],
         bought=[
             ('P1-215', 'Formed (cold-rolled) continuous screw flight, 316, OD 56 x ID 25 x pitch 56 x 3 thick, 1,110 long (20 turns), right hand', 'Spirotech / Kase Conveyors',
              'continuous helicoid flight 56 x 25 x 56 x 3, 316 (quote; alternate: 20 sectional blanks per DXF P1-212-202)', 'https://www.mcmaster.com/', 'Spirotech', 9, 180, 'screw'),
             ('P1-216', 'Helical in-line gearmotor 0.25 kW 4-pole 230/460 V 3-ph, i ≈ 10.25 (165 rpm at 60 Hz), solid shaft Ø20 j6 x 40 keyed, B14 face flange (spigot Ø80, 4 x M6 on PCD 100), IP66 washdown', 'NORD Drivesystems',
              'SK 072.1 - 71S/4, B14 flange C120 (confirm flange code and shaft with the NORD quote drawing)', 'https://www.nord.com/', 'NORD Drivesystems', 9, 520, 'gearmotor'),
             ('P1-241', 'Deep-groove ball bearing, stainless, 20 x 42 x 12, sealed both sides, food grease', 'SKF',
              'W 6004-2RS1 (stainless)', 'https://www.skf.com/', 'SKF', 18, 38, None),
             ('P1-242', 'Rotary lip seal 20 x 35 x 7, FDA PTFE lip, stainless case, dry-running', 'Trelleborg / AHP Seals',
              'PTFE lip seal 20x35x7 FDA, SS case (confirm series)', 'https://www.mcmaster.com/', 'Trelleborg', 9, 45, None),
             ('P1-243', 'O-ring 46 x 2.5, EPDM, FDA 21 CFR 177.2600', 'generic',
              'O-ring 46 x 2.5 EPDM 70 FDA', 'https://www.mcmaster.com/', 'generic', 18, 3, None),
             ('P1-244', 'Jaw coupling, cast iron hubs, 20 mm bore 6 mm key both hubs, Hytrel spider', 'Lovejoy (Timken)',
              'L-075 hubs 20 mm x 6 kw (2) + L-075 Hytrel spider', 'https://www.lovejoy-inc.com/', 'Lovejoy (Timken)', 9, 55, None),
             ('P1-245', 'Sanitary short weld ferrule 2.5 in, 316L, A270 tube end', 'generic sanitary (14WMP)',
              '14WMP-2.5 316L', 'https://www.mcmaster.com/', 'generic sanitary (14WMP)', 9, 9, None),
             ('P1-246', 'Tri-Clamp gasket 2.5 in EPDM, FDA', 'generic sanitary',
              '40MP-2.5 EPDM', 'https://www.mcmaster.com/', 'generic sanitary', 18, 2, None),
             ('P1-247', 'Tri-Clamp clamp 2.5 in, single pin, HEX-NUT closure (tool needed: the cap guards the screw)', 'generic sanitary',
              '13MHHS-2.5 304', 'https://www.mcmaster.com/', 'generic sanitary', 9, 14, None),
             ('P1-248', 'Motor isolator, 3-pole 16 A, lockable OFF, stainless or polycarbonate IP66 enclosure, 1 early-break NO aux contact', 'ABB',
              'OTP16T3M + OA1G10 aux, IP66 (confirm enclosure code)', 'https://new.abb.com/low-voltage', 'ABB', 9, 95, None),
             ("P1-217", "Inlet agitator gearmotor kit for herb and peel bins (slow paddle)", "Bodine Electric", "1/17 HP 30 rpm gearmotor + SS paddle (confirm)",
              "https://www.bodine-electric.com/", "Bodine distributor", 3, 380, None),
         ]),
    dict(id="P1-401", title="Servo auger filler (built) rev B", tag_name="Auger filler", qty=1,
         full_set="machines/P1-401/drawings/P1-401-001_general_arrangement.svg",
         assy_note="Container on the indexed stage under the tooling outlet at 1,020 [40.2]; blend scooped into the interlocked lid port. "
                   "Full build set: machines/P1-401/drawings/P1-401-drawing-set.pdf (18 sheets)",
         parts=[
             dict(id="P1-401-01", fn=fl_all, title="Filler P1-401 rev B made parts (cabinet, column, drive head, hopper, agitator, container stage)",
                  material="SS 304 1.5 / 3 / 10 / 12 mm, 4 in sq tube; 316L 1.5 mm hopper and agitator; 17-4PH spindle",
                  process="Laser, brake, roll, TIG, lathe, mill, polish (see P1-401-100..700)", mat_kg=135, labor_h=60, flat=None, contact=True, qty=1,
                  notes=["Detail drawings: P1-401-001..900 (GA, sections, assembly, cabinet + flats, column, drive head + machined parts, hopper, agitator, tooling, stage, bought, E01-E03, ITP)",
                         "Spindle on 2 x 6205 in a top-loaded cartridge, belt 2:1 from the 750 W servo; agitator hub on 2 x 6008 around it, #40 SS chain from a 1/4 HP gearmotor",
                         "PNOZ s4 safety relay: E-stop and the lid flap switch remove servo torque (STO) and drop the agitator"],
                  fasteners=lambda f: "see P1-401-800"),
         ],
         bought=[
             ('P1-413', 'AC servo 750 W, 80 mm flange (Ø70 pilot, 4 x M6 on Ø90), Ø19 keyed shaft, 2.39 N·m rated / 7.16 peak, 3,000 rpm, with drive 200-230 V 1-ph, STO, RS-485 Modbus, 3 m motor + encoder cables', 'AutomationDirect', 'SureServo2 SV2L-207B motor + SV2A-2075 drive + SVC2 cables (confirm shaft and flange before machining the bridge)',
              'https://www.automationdirect.com/', 'AutomationDirect', 1, 1350, 'servo'),
             ('P1-414', 'Agitator gearmotor 1/4 HP 115 V 1-ph, about 60 rpm, face-mount, output shaft Ø5/8 in keyed, 4 x 1/4-20 on Ø3.75 in (confirm)', 'Bison Gear & Engineering', '011-series parallel shaft 1/4 HP 60 rpm (confirm flange; head plate slots are 9 x 19 on 90 sq)',
              'https://www.bisongear.com/', 'Bison Gear & Engineering', 1, 420, 'agitator'),
             ('P1-415', 'Auger tooling, 2 sets to drawing P1-401-600: S (shaker) 27 OD auger + 1.25 in tube, J (jar/pouch/tub) 46 OD auger + 2 in tube; 316, M16 x 1.5 LH top thread', 'All-Fill Inc.', 'custom auger + funnel tube to P1-401-600 (quote with blend samples)',
              'https://www.all-fill.com/', 'All-Fill Inc.', 2, 650, 'auger_tooling'),
             ('P1-416', 'Filler controls: CLICK PLUS PLC C2-03CPU-2 + 8 in / 8 out DC module + C-more Micro 3 in HMI', 'AutomationDirect', 'C2-03CPU-2 + C0-16CDD2 + EA3-S3ML (confirm I/O module)',
              'https://www.automationdirect.com/', 'AutomationDirect', 1, 620, 'hmi'),
             ('P1-417', 'Foot switch, guarded, 1 NO + 1 NC, IP68, 3 m cord', 'Linemaster', '632-S class (confirm)',
              'https://www.linemaster.com/', 'Linemaster', 1, 90, 'pedal'),
             ('P1-430', 'Ball bearings: 2 x 6205-2RS (spindle), 2 x 6008-2RS (agitator hub), food-grade grease', 'SKF', '6205-2RSH/C3GJN + 6008-2RS1 (H1 grease)',
              'https://www.skf.com/', 'SKF', 1, 85, None),
             ('P1-431', 'Timing drive HTD 5M 15 wide: pulley 20T bore Ø19 key 6 (servo), pulley 40T bore Ø20 key 6 (spindle), belt 450-5M-15', 'Gates / B&B Manufacturing', '20-5M-15 + 40-5M-15 (finished bore) + 450-5M-15 belt',
              'https://www.bbman.com/', 'Gates', 1, 95, None),
             ('P1-432', 'Roller chain drive #40 stainless: sprocket 15T (bore 5/8 in key), sprocket 30T plate (bored Ø81 H7, 4 x Ø6.5 on Ø100), chain #40 SS 52 links + connecting link', 'Tsubaki / Martin Sprocket', '40SS 15T B-hub + 40SS 30T A-plate (bore to drawing) + RS40-SS x 52L',
              'https://www.martinsprocket.com/', 'Tsubaki', 1, 140, None),
             ('P1-433', 'Lip seals 25 x 40 x 7, FKM or PTFE, FDA', 'SKF / Trelleborg', '25x40x7 HMSA10 V (FDA) or PTFE lip',
              'https://www.skf.com/', 'SKF', 2, 18, None),
             ('P1-434', 'Index plunger M16 x 1.5, pin Ø10, pull knob with rest position, stainless', 'Elesa-Ganter', 'GN 617-10-AK-NI (confirm)',
              'https://www.elesa-ganter.com/', 'Elesa-Ganter', 1, 38, None),
             ('P1-435', 'Container sensor: diffuse photoelectric 18 mm, 24 V DC PNP, IP69K, 2 m M12 cable', 'Banner Engineering', 'QS18VP6D + MQDEC2-506 (confirm range ≈ 100 mm)',
              'https://www.bannerengineering.com/', 'Banner Engineering', 1, 95, None),
             ('P1-436', 'Safety relay 24 V DC, dual channel, 3 NO safety + 1 NC aux, monitored manual reset', 'Pilz', 'PNOZ s4 24VDC 3 n/o 1 n/c (750104)',
              'https://www.pilz.com/', 'Pilz', 1, 230, None),
             ('P1-437', '22 mm operators: E-stop 40 mm mushroom 2 NC, blue reset 1 NO, green and red LED pilot lights 24 V', 'AutomationDirect', 'GCX1131-24 (E-stop) + GCX1102 + GCX0102 x2 (confirm)',
              'https://www.automationdirect.com/', 'AutomationDirect', 1, 85, None),
             ('P1-438', 'Coded magnetic safety switch 2 NC, M12 connector, IP69K, for the scoop flap', 'Schmersal', 'BNS 260-02z-ST + BPS 260-1 actuator (confirm)',
              'https://www.schmersal.com/', 'Schmersal', 1, 120, None),
             ('P1-439', 'Disconnect switch 25 A 2-pole, lockable OFF, side-mount handle', 'ABB', 'OT25F3 + OHB45J6 handle + OXP6X shaft (confirm)',
              'https://new.abb.com/low-voltage', 'ABB', 1, 75, None),
             ('P1-440', 'Control transformer 750 VA 208 V / 120 V', 'Hammond', 'PH750MQMJ (confirm)',
              'https://www.hammondpowersolutions.com/', 'Hammond', 1, 160, None),
             ('P1-441', 'Breakers and motor protection: F1 S202-C10 (servo drive), F2 S202-D8 (T1 primary), F3 S201-C8 (120 V), Q2 MS116-4.0 + HKF1-11 (agitator), KM1 AF09-30-10-13 24 V DC coil', 'ABB', 'S202-C10, S202-D8, S201-C8, MS116-4.0, HKF1-11, AF09-30-10-13',
              'https://new.abb.com/low-voltage', 'ABB', 1, 260, None),
             ('P1-442', 'Power supply 24 V DC 2.5 A, DIN rail', 'AutomationDirect', 'PSB24-060S (confirm)',
              'https://www.automationdirect.com/', 'AutomationDirect', 1, 45, None),
             ('P1-443', 'Levelling feet M12, Ø60 pad, stainless, 100 mm thread', 'Elesa-Ganter', 'LMT-60-M12x100 inox (confirm)',
              'https://www.elesa-ganter.com/', 'Elesa-Ganter', 4, 22, None),
             ('P1-444', 'Cabinet hardware: 2 lift-off hinges SS, 1 quarter-turn latch SS with handle, door gasket FDA silicone 2 m', 'Southco', 'C6-1-1 hinges + E3-5 latch + FDA gasket (confirm)',
              'https://www.southco.com/', 'Southco', 1, 70, None),
             ('P1-445', 'TC clamps 2.5 in heavy-duty wing nut 304 + EPDM FDA gaskets (tooling and agitator)', 'generic sanitary', '13MHHM-2.5 + 40MP-U250 (confirm)',
              'https://www.mcmaster.com/', 'generic sanitary', 2, 18, None),
             ('P1-446', 'Cable glands M25 + 2 x M20 nylon IP68, 2 m DIN rail 35, wire duct, terminals', 'Phoenix Contact', 'UT 4 terminals + glands (confirm)',
              'https://www.phoenixcontact.com/', 'Phoenix Contact', 1, 90, None),
         ]),
    dict(id="P1-406", title="Metal detector conveyor (built frame, bought head)", tag_name="Detector conveyor", qty=1,
         assy_note="Belt top 905 [35.6], level with the tables; the bought search head (CCP-1) bolts over the centre",
         parts=[
             dict(id="P1-406-01", fn=cv_frame, title="Detector conveyor frame 1,500 x 6 in belt", material="SS 304 2.5 mm channels, 3 mm bed, 40 sq legs",
                  process="Laser cut, brake, TIG", mat_kg=30, labor_h=16, flat=None, contact=False, qty=1,
                  notes=["Non-metallic zone: no frame metal within 1.5 x aperture height of the head (head maker's rule: VERIFY)",
                         "Take-up slots for the tail pulley; belt tracks on crowned pulleys", "Reject arm pushes failed packs into the locked bin"],
                  fasteners=lambda f: "pulley shaft take-up"),
         ],
         bought=[
             ("P1-418", "Metal detector search head about 10 x 6 in aperture with control (CCP-1), used, validated", "Fortress Technology",
              "Stealth search head + control only (used, Sigma Equipment) (confirm)", "https://www.sigmaequipment.com/", "Sigma Equipment", 1, 8500, "detector_head"),
             ("P1-419", "Endless belt 6 in, FDA polyurethane, plus 2 crowned SS pulleys Ø60 with bearings", "Ammeraal Beltech", "Ropanyl FDA 6 in endless + pulley set (quote)",
              "https://www.ammeraalbeltech.com/", "Ammeraal distributor", 1, 650, "belt"),
             ("P1-420", "Conveyor gearmotor 1/6 HP shaft-mount, 60 rpm", "Bodine Electric", "1/6 HP parallel-shaft (confirm)", "https://www.bodine-electric.com/", "Bodine distributor", 1, 480, "gearmotor"),
             ("P1-421", "Reject pusher: 24 V linear actuator 100 mm stroke with the head's reject output", "Progressive Automations", "PA-15 class (confirm speed)",
              "https://www.progressiveautomations.com/", "Progressive Automations", 1, 180, "reject"),
         ]),
    dict(id="P1-412", title="Bench spindle capper (built)", tag_name="Spindle capper", qty=1,
         assy_note="Operator pulls the lever: the chuck lowers onto the cap and spins it down to the clutch torque, then slips",
         parts=[
             dict(id="P1-412-01", fn=cp_frame, title="Capper frame, column and carriage", material="SS 304 12 mm plate, 2 in sq tube, 10 mm plate",
                  process="Laser cut, TIG, machine rail seat", mat_kg=14, labor_h=12, flat="base", contact=False, qty=1,
                  notes=["Rail seat machined flat 0.05 mm over 500; MGN15 rail (P1-424) bolts to it", "V-nest slot takes printed container nests (never product contact)",
                         "Clutch set to the cap torque table; checked hourly on the torque tester P1-402"],
                  fasteners=lambda f: "M8 x 20 to bench" if f["dia"] < 10 else ("Ø52 chuck bore" if f["dia"] > 40 else "lever pivot")),
         ],
         bought=[
             ("P1-422", "Gearmotor 1/8 HP 120 V, about 200 rpm", "Bodine Electric", "1/8 HP PMDC + speed control (confirm)", "https://www.bodine-electric.com/", "Bodine distributor", 1, 420, "gearmotor"),
             ("P1-423", "Adjustable slip clutch 0.5-5 N·m with capping chucks for 53 mm and 89 mm caps", "Zero-Max / Resina-style chucks",
              "Torq-Tender TT1 class + urethane chuck inserts (confirm)", "https://www.zero-max.com/", "Zero-Max distributor", 1, 520, "clutch"),
             ("P1-424", "Linear rail MGN15 500 mm with block, and a gas spring counterbalance", "HIWIN", "MGN15H rail 500 + gas spring 100 N (confirm)", "https://www.hiwin.us/", "HIWIN distributor", 1, 160, "gas_spring"),
         ]),
    dict(id="P1-404", title="Wrap labeler for round containers (built)", tag_name="Wrap labeler", qty=1,
         assy_note="Container rolls on the two drive rollers under the idler; the label peels at the plate and wraps in one turn",
         parts=[
             dict(id="P1-404-01", fn=lb_frame, title="Labeler base, roller blocks, spindle posts and peel plate", material="SS 304 8 mm plate, 3 mm peel plate, 20 sq bar",
                  process="Laser cut, TIG, machine bores", mat_kg=10, labor_h=14, flat="base", contact=False, qty=1,
                  notes=["Roller bores line-reamed Ø12 H7 for the drive roller shafts; parallel within 0.05 mm", "Peel plate at 30 deg, edge radius 1 mm, label gap sensor just upstream",
                         "Stepper advances one label per wrap at the container surface speed"],
                  fasteners=lambda f: "M6 to bench" if f["dia"] < 8 else "Ø12 H7 roller shaft"),
         ],
         bought=[
             ("P1-425", "Drive rollers 50 x 240 mm urethane-covered, with shafts, bearings and timing pulleys (set of 3)", "Misumi", "custom urethane rollers (quote)",
              "https://us.misumi-ec.com/", "Misumi", 1, 420, "rollers"),
             ("P1-426", "NEMA 23 stepper with integrated driver and controller (label feed + roller drive)", "Teknic", "ClearPath-SD or ClearCore + NEMA 23 (confirm)",
              "https://teknic.com/", "Teknic", 1, 560, "stepper"),
             ("P1-427", "Label gap sensor, fork type", "SICK", "WFS3 class (confirm)", "https://www.sick.com/", "SICK distributor", 1, 260, "gap_sensor"),
         ]),
]
BOUGHT_FN = {"P1-301": bought_blender, "P1-212": bought_feeder, "P1-401": bought_filler, "P1-406": bought_conveyor, "P1-412": bought_capper, "P1-404": bought_labeler}


def placed(s, where):
    """the part as it sits in the machine: copies at (x, y, z, rotZ) or as modelled."""
    if not where:
        return s
    out = None
    for x, y, z, r in where:
        c = s.rotate((0, 0, 0), (0, 0, 1), r).translate((x, y, z))
        out = c if out is None else out.union(c)
    return out


def anchor_pt(s):
    sol = s.val().Solids() if hasattr(s.val(), "Solids") else [s.val()]
    big = max(sol, key=lambda q: q.Volume()) if sol else s.val()
    return big.BoundingBox().center


# =============================================================================================== GA sheet
def ga_sheet(m, parts, bought_shapes):
    """General arrangement: true-scale front/top/right/iso of the whole machine, balloons, item list (built + bought)."""
    shapes = [s.val() for s in parts.values()] + [s.val() for s in bought_shapes.values() if s.val() is not None and s.vals()]
    comp = cq.Compound.makeCompound(shapes)
    views = {n: partsheet.View(comp, n) for n in ("FRONT", "TOP", "RIGHT", "ISOMETRIC")}
    F, T, R, I = views["FRONT"], views["TOP"], views["RIGHT"], views["ISOMETRIC"]
    ox, oy, gap = 90, 90, 120
    avail_w, avail_h = 980 - ox - gap, partsheet.H - 60 - oy - gap - 120
    raw = min(avail_w / (F.w + R.w), avail_h / (F.h + T.h)) / partsheet.PXMM
    steps = [1, 0.5, 0.4, 0.25, 0.2, 0.1, 0.05, 0.04, 1 / 30, 0.025, 0.02]
    sc = next((k for k in steps if k <= raw + 1e-9), 0.02)
    S = sc * partsheet.PXMM
    T.place(ox, oy, S); F.place(ox, oy + T.h * S + gap, S); R.place(ox + F.w * S + gap, F.oy, S)
    ix0 = R.ox + R.pw + 40
    si = min((1040 - ix0) / I.w, (F.oy - 60) / I.h) * 0.85
    I.place(ix0, 70, si)
    body = "".join(v.svg() for v in (T, F, R, I))
    for v, lab in ((T, "TOP"), (F, "FRONT"), (R, "RIGHT")):
        body += f'<text x="{v.ox}" y="{v.oy - 30}" font-size="13" font-weight="bold">{lab} VIEW</text>'
    body += f'<text x="{I.ox}" y="60" font-size="13" font-weight="bold">ISOMETRIC (REF.)</text>'
    bb = comp.BoundingBox()
    body += partsheet.hdim(F.ox, F.ox + F.pw, F.oy + F.ph + 30, partsheet.mm_in(bb.xlen, 0), F.oy + F.ph + 4)
    body += partsheet.vdim(F.ox - 30, F.oy, F.oy + F.ph, partsheet.mm_in(bb.zlen, 0), F.ox - 4)
    body += partsheet.hdim(R.ox, R.ox + R.pw, R.oy + R.ph + 30, partsheet.mm_in(bb.ylen, 0), R.oy + R.ph + 4)
    # balloons on the front view at each item's bbox centre
    items = []
    n = 1
    for pid, s in parts.items():
        items.append((n, pid, next(p for p in m["parts"] if p["id"] == pid)["title"], "BUILD", next(p for p in m["parts"] if p["id"] == pid)["qty"], "our drawing", s)); n += 1
    for b in m["bought"]:
        s = bought_shapes.get(b[8]) if b[8] else None
        items.append((n, b[0], b[1], "BUILD" if b[2] == "(our part)" else "BUY", b[6], f"{b[2]}: {b[3]}" + (" (listed on its own line)" if b[7] == 0 else ""), s)); n += 1
    used = []
    for num, pid, *_rest in items:
        s = _rest[-1]
        if s is None:
            continue
        c = anchor_pt(s)
        px, py = F.pt((c.x, c.y, c.z))
        cands = [(px + dx * r, py + dy * r) for r in (45, 75, 105, 135, 165) for dx, dy in ((1, -1), (-1, -1), (1, 1), (-1, 1), (0, -1.3), (1.3, 0), (-1.3, 0))]
        lo_x, hi_x, lo_y, hi_y = F.ox - 70, F.ox + F.pw + 70, F.oy - 20, F.oy + F.ph + 20
        bx, by = next(((x, y) for x, y in cands if lo_x < x < min(hi_x, R.ox - 20) and lo_y < y < hi_y
                       and not any(abs(x - ux) < 32 and abs(y - uy) < 32 for ux, uy in used)), cands[-1])
        used.append((bx, by))
        col = "#c0620c" if _rest[2] == "BUILD" else "#1f5fa8"
        body += (f'<line x1="{px}" y1="{py}" x2="{bx}" y2="{by}" stroke="{col}" stroke-width="0.9"/><circle cx="{px}" cy="{py}" r="2.5" fill="{col}"/>'
                 f'<circle cx="{bx}" cy="{by}" r="13" fill="#fff" stroke="{col}" stroke-width="1.6"/>'
                 f'<text x="{bx}" y="{by + 4.5}" font-size="12" font-weight="bold" text-anchor="middle" fill="{col}">{num}</text>')
    # item list
    tx, ty, tw = 1060, 40, 520
    t = f'<text x="{tx}" y="{ty + 12}" font-size="13" font-weight="bold">ITEM LIST</text>'
    y = ty + 20
    t += f'<rect x="{tx}" y="{y}" width="{tw}" height="16" fill="#eef1f4" stroke="#222" stroke-width="0.6"/>'
    for cx, lab in ((4, "ITEM"), (36, "PART"), (112, "DESCRIPTION / SOURCE"), (440, "MAKE"), (486, "QTY")):
        t += f'<text x="{tx + cx}" y="{y + 12}" font-size="9.5" font-weight="bold">{lab}</text>'
    y += 16
    for num, pid, title, kind, qty, src, _s in items:
        lines = partsheet._wrap(title, 58) + [x for x in partsheet._wrap(src, 62)][:2]
        h = 11 * len(lines) + 5
        col = "#c0620c" if kind == "BUILD" else "#1f5fa8"
        t += f'<rect x="{tx}" y="{y}" width="{tw}" height="{h}" fill="none" stroke="#222" stroke-width="0.4"/>'
        t += f'<text x="{tx + 10}" y="{y + 12}" font-size="10.5" font-weight="bold" fill="{col}">{num}</text><text x="{tx + 36}" y="{y + 12}" font-size="9.5" font-weight="bold">{pid}</text>'
        t += "".join(f'<text x="{tx + 112}" y="{y + 12 + 11 * i}" font-size="{9.5 if i < len(lines) - 2 or len(lines) < 3 else 8.5}" fill="{"#111" if i == 0 or i < len(partsheet._wrap(title, 58)) else "#555"}">{escape(l)}</text>' for i, l in enumerate(lines))
        t += f'<text x="{tx + 440}" y="{y + 12}" font-size="9.5" fill="{col}" font-weight="bold">{kind}</text><text x="{tx + 490}" y="{y + 12}" font-size="10">{qty}</text>'
        y += h
    cost = m["cost"]
    notes = [m["assy_note"], f"Built parts: {', '.join(p['id'] for p in m['parts'])} (part sheets with every hole and DXF in this set).",
             f"Cost per machine: material ${cost['material']:,.0f} + {cost['labor_h']} h labour (${cost['labor']:,.0f}) + bought ${cost['bought']:,.0f} = ${cost['total']:,.0f}.",
             "Bought items are catalog-size models on this sheet; dimensions marked VERIFY are set by them.",
             "Product contact 316L #4, welds ground flush, Tri-Clamp joints, tool-free strip-down."]
    tb = dict(title=m["title"], partno=m["id"] + "-GA", material="see item list", process="Assemble, align, run-in, FAT per build.json",
              qty=str(m["qty"]), mass=f"{sum(p.val().Volume() for p in parts.values()) * 8e-6:.0f} kg [fabricated parts]", scale=f"1:{round(1 / sc, 2):g}" if sc < 1 else "1:1",
              project=PROJECT, assy="Phase 1 plant", qty_label="QTY PHASE 1")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{partsheet.W}" height="{partsheet.H}" viewBox="0 0 {partsheet.W} {partsheet.H}" '
           f'font-family="Helvetica,Arial,sans-serif">{partsheet.frame()}{body}{t}{partsheet.notes_block(notes)}{partsheet.title_block(tb)}</svg>')
    return svg


def main():
    step, stl, dwg, dx = HERE / "step", HERE / "stl", P1 / "drawings" / "machines", P1 / "dxf"
    for d in (step, stl, dwg, dx):
        d.mkdir(parents=True, exist_ok=True)
    out = []
    for m in MACHINES:
        parts = {}
        mat = lab = 0.0
        for p in m["parts"]:
            s = p["fn"]()
            parts[p["id"]] = placed(s, p.get("place"))
            cq.exporters.export(s, str(step / f"{p['id']}.step"))
            cq.exporters.export(s, str(stl / f"{p['id']}.stl"), tolerance=0.3, angularTolerance=0.3)
            info = dict(title=p["title"], partno=p["id"], material=p["material"], process=p["process"], qty=str(p["qty"]), density=8.0, tol="sheet",
                        notes=p["notes"], project=PROJECT, assy=m["title"], qty_label="QTY PHASE 1")
            svg, feats = partsheet.sheet(s, info, fasteners=p["fasteners"])
            (P1 / "drawings" / "parts" / f"{p['id']}.svg").write_text(svg)
            files = []
            if p["flat"]:
                kind = p["flat"]
                try:
                    if kind == "cover":
                        bb = s.val().BoundingBox()
                        flat = cq.Workplane("XY").add(s.val()).section(bb.zmin + 1.5).val().translate(cq.Vector(0, 0, -(bb.zmin + 1.5)))
                        cq.exporters.export(cq.Workplane("XY").add(flat), str(dx / f"{p['id']}_cover_mm.dxf"), "DXF")
                        cq.exporters.export(cq.Workplane("XY").add(flat.scale(1 / IN)), str(dx / f"{p['id']}_cover_in.dxf"), "DXF")
                    elif kind == "flange":
                        bb = s.val().BoundingBox()
                        z = bb.zmax - 3
                        flat = cq.Workplane("XY").add(s.val()).section(z).val().translate(cq.Vector(0, 0, -z))
                        cq.exporters.export(cq.Workplane("XY").add(flat), str(dx / f"{p['id']}_flange_mm.dxf"), "DXF")
                        cq.exporters.export(cq.Workplane("XY").add(flat.scale(1 / IN)), str(dx / f"{p['id']}_flange_in.dxf"), "DXF")
                    else:
                        dxf(s, p["id"], kind, dx)
                    files = [f"dxf/{p['id']}_{kind}_mm.dxf", f"dxf/{p['id']}_{kind}_in.dxf"]
                except Exception as e:
                    print("  DXF failed", p["id"], e)
            mass = s.val().Volume() * 8.0e-6
            mat += p["mat_kg"] * SS_KG * p["qty"] / m["qty"] + 40          # + consumables per part
            lab += p["labor_h"] * p["qty"] / m["qty"]
            bb = s.val().BoundingBox()
            out.append(dict(machine=m["id"], id=p["id"], title=p["title"], qty=p["qty"], material=p["material"], features=len(feats), contact=p["contact"],
                            mass_kg=round(mass, 1), size_mm=[round(bb.xlen), round(bb.ylen), round(bb.zlen)], step=f"cad/step/{p['id']}.step",
                            drawing=f"drawings/parts/{p['id']}.svg", dxf=files, labor_h=p["labor_h"], mat_kg=p["mat_kg"]))
            print(p["id"], len(feats), "features", out[-1]["size_mm"], round(mass, 1), "kg", files and "dxf" or "")
        bought_shapes = BOUGHT_FN[m["id"]]()
        bsum = sum(b[6] * b[7] for b in m["bought"]) / m["qty"]
        m["cost"] = dict(material=round(mat), labor_h=round(lab, 1), labor=round(lab * LABOR), bought=round(bsum), total=round(mat + lab * LABOR + bsum))
        if m.get("full_set"):            # machine has its own full drawing set: its real GA replaces the auto GA (and the auto HLR is too slow on it)
            (dwg / f"{m['id']}-GA.svg").write_text((P1 / m["full_set"]).read_text())
        else:
            (dwg / f"{m['id']}-GA.svg").write_text(ga_sheet(m, parts, bought_shapes))
        asm = cq.Assembly(name=m["id"])
        for pid, s in parts.items():
            asm.add(s, name=pid, color=cq.Color(0.80, 0.82, 0.84))
        for k, s in bought_shapes.items():
            asm.add(s, name=k, color=cq.Color(0.25, 0.35, 0.55))
        asm.save(str(step / f"{m['id']}-ASM.step"))
        print(m["id"], "GA", m["cost"])
    summary = [dict(id=m["id"], title=m["title"], qty=m["qty"], cost=m["cost"], assy_note=m["assy_note"], parts=[p["id"] for p in m["parts"]],
                    bought=[dict(tag=b[0], name=b[1], maker=b[2], model=b[3], source=b[4], supplier=b[5], qty=b[6], usd=b[7]) for b in m["bought"]],
                    ga=f"drawings/machines/{m['id']}-GA.svg", asm_step=f"cad/step/{m['id']}-ASM.step") for m in MACHINES]
    (HERE / "machines.json").write_text(json.dumps(dict(machines=summary, parts=out), indent=1))


if __name__ == "__main__":
    main()
