"""Phase 1 fabricated parts: CAD (STEP, STL), part drawings (partsheet.py), DXF cut files (mm and inch)
and 3D-print STLs for the non-contact fixtures.

Fabricate-in-house list (equipment_p1.py kind="build"):
  P1-206  Stainless work table 60 x 30 in (weigh bench and 4 pack stations)
  P1-207  Weigh-bench backdraft dust hood, slot plate + 4 in collar
  P1-208  Premix pail tumbler frame: base plate, 4 bearing uprights, 2 roller shafts for a 5 gal pail
  P1-210  Ingredient bin ring frame, 12 positions around the weigh hopper
  P1-211  Ingredient bin 5 cu ft, square body + pyramid cone, flange for a 2 in screw feeder
  P1-220  Weigh hopper 141 L on 3 load cells, 4 in Tri-Clamp outlet
  P1-302  Blender bag-dump grate (sits in the blender cover opening)
  P1-303  Blender discharge chute, flange to 4 in Tri-Clamp
  P1-304  Sieve deck housing for an 18 in round screen, cone to 4 in Tri-Clamp
  P1-309  Drum dolly base for a 30 gal drum
  P1-408  Accumulation turntable disc 30 in with rim
  P1-410a-d  3D-printed: shaker nest, jar nest, 53 mm and 89 mm cap grips (PETG, never touch product)

Sanitary rules (references/food-safety-design.md): product-contact parts 304/316L, continuous welds ground flush,
#4 finish, no threads or ledges in the product zone, Tri-Clamp joints so everything opens without tools.
Dimensions marked VERIFY are set by a bought part (used blender flange, feeder inlet, load cell) and must be
measured on the real part before cutting.
Usage: python3 p1_parts.py
"""
import json, math, pathlib, sys

import cadquery as cq

HERE = pathlib.Path(__file__).parent
P1 = HERE.parent
sys.path.insert(0, str(P1.parents[2] / "skills" / "anatomy" / "tools" / "plant"))
import partsheet  # noqa: E402

IN = 25.4
GA14, GA11 = 1.9, 3.0
TC4_FL, TC4_TUBE = 4.684 * IN / 2 * 2, 4.0 * IN          # 4 in Tri-Clamp ferrule flange OD 119.0, tube OD 101.6
PROJECT = "Down Home Creole Phase 1 prototype"


def ferrule4(h=28.6):
    return cq.Workplane("XY").circle(TC4_FL / 2).circle(TC4_TUBE / 2 - 1.65).extrude(h)


def shell_loft(w1, d1, w2, d2, h, t, round2=False):
    """Hollow loft from a w1 x d1 rectangle at z=0 down to w2 x d2 (or a circle of dia w2) at z=-h, wall t."""
    def prof(off):
        wp = cq.Workplane("XY").rect(w1 + 2 * off, d1 + 2 * off).workplane(offset=-h)
        wp = wp.circle(w2 / 2 + off) if round2 else wp.rect(w2 + 2 * off, d2 + 2 * off)
        return wp.loft()
    outer = cq.Workplane("XY").rect(w1 + 2 * t, d1 + 2 * t).workplane(offset=-h)
    outer = (outer.circle(w2 / 2 + t) if round2 else outer.rect(w2 + 2 * t, d2 + 2 * t)).loft()
    inner = cq.Workplane("XY").workplane(offset=0.01).rect(w1, d1).workplane(offset=-h - 0.02)
    inner = (inner.circle(w2 / 2) if round2 else inner.rect(w2, d2)).loft()
    return outer.cut(inner)


# ------------------------------------------------------------------ parts
def p1_206():
    """Table: 1524 x 762 top, 40 mm turned-down edge, 4 legs 38 sq tube, under-shelf, 914 high."""
    L, W, H, e, leg = 1524.0, 762.0, 914.0, 40.0, 38.1
    top = cq.Workplane("XY").box(L, W, GA14).translate((0, 0, H - GA14 / 2))
    edge = (cq.Workplane("XY").rect(L, W).rect(L - 2 * GA14, W - 2 * GA14).extrude(e).translate((0, 0, H - e)))
    legs = cq.Workplane("XY")
    for sx in (-1, 1):
        for sy in (-1, 1):
            legs = legs.union(cq.Workplane("XY").rect(leg, leg).rect(leg - 3.2, leg - 3.2).extrude(H - e)
                              .translate((sx * (L / 2 - 60), sy * (W / 2 - 60), 0)))
    shelf = (cq.Workplane("XY").box(L - 120 + leg, W - 120 + leg, GA14).translate((0, 0, 250))
             .faces(">Z").workplane().rect(L - 120, W - 120, forConstruction=True).vertices().hole(leg + 1))
    # 4 x Ø10 holes in the top edge flange for the hood / accessory clamp
    t = top.union(edge).union(legs).union(shelf)
    t = t.faces(">Y").workplane(centerOption="CenterOfBoundBox").pushPoints([(-500, H - 20 - H / 2 - 0), (500, H - 20 - H / 2)]).hole(10, 5)
    return t


def p1_207():
    """Backdraft hood: 1400 wide, 250 deep, 600 high box; 3 slots 1300 x 25 in the front plate; 4 in collar on top."""
    w, d, h = 1400.0, 250.0, 600.0
    box = cq.Workplane("XY").box(w, d, h).faces("<Y or <Z").shell(-GA14).translate((0, 0, h / 2))
    box = box.faces("<Y").workplane(centerOption="CenterOfBoundBox").pushPoints([(0, -180), (0, 0), (0, 180)]).slot2D(1300, 25, 0).cutThruAll()
    collar = cq.Workplane("XY").circle(TC4_TUBE / 2).circle(TC4_TUBE / 2 - 1.65).extrude(80).translate((0, 0, h))
    box = box.union(collar).faces(">Z").workplane().circle(TC4_TUBE / 2 - 1.65).cutBlind(-GA14 - 1)
    # mounting flange holes at the bottom back
    box = box.faces(">Y").workplane(centerOption="CenterOfBoundBox").pushPoints([(-600, -250), (600, -250), (-600, 250), (600, 250)]).hole(7)
    return box


def p1_211():
    """Bin: 600 sq x 250 straight + pyramid to 120 sq outlet over 400, outlet flange 200 sq with 4 x Ø11 on 160 sq (VERIFY feeder)."""
    body = cq.Workplane("XY").rect(600 + 2 * GA14, 600 + 2 * GA14).rect(600, 600).extrude(250)
    cone = shell_loft(600, 600, 120, 120, 400, GA14)
    fl = (cq.Workplane("XY").rect(200, 200).rect(120, 120).extrude(6).translate((0, 0, -406))
          .faces(">Z").workplane().rect(160, 160, forConstruction=True).vertices().hole(11))
    rim = (cq.Workplane("XY").rect(680, 680).rect(600, 600).extrude(6).translate((0, 0, 250))
           .faces(">Z").workplane().rect(640, 640, forConstruction=True).vertices().hole(9))
    lugs = cq.Workplane("XY")
    for sx in (-1, 1):
        lugs = lugs.union(cq.Workplane("XY").box(8, 120, 100).translate((sx * (300 + GA14 + 4), 0, 150))
                          .faces(">X" if sx > 0 else "<X").workplane(centerOption="CenterOfBoundBox").pushPoints([(-30, 0), (30, 0)]).hole(13))
    return body.union(cone).union(fl).union(rim).union(lugs).translate((0, 0, 406))


def p1_220():
    """Weigh hopper: Ø700 x 250 cylinder + 45° cone to 4 in TC; 3 load-cell lugs at 120° on Ø800 (VERIFY load cell)."""
    R, t = 350.0, GA14
    cyl = cq.Workplane("XY").circle(R + t).circle(R).extrude(250)
    h_cone = R - TC4_TUBE / 2
    cone = (
        cq.Workplane("XY").circle(R + t).workplane(offset=-h_cone).circle(TC4_TUBE / 2 + t).loft()
        .cut(cq.Workplane("XY").workplane(offset=0.01).circle(R).workplane(offset=-h_cone - 0.02).circle(TC4_TUBE / 2).loft()))
    fer = ferrule4().translate((0, 0, -h_cone - 28.6))
    part = cyl.union(cone).union(fer)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        lug = (cq.Workplane("XY").box(110, 80, 10).translate((math.cos(a) * (R + 55), math.sin(a) * (R + 55), 150))
               .faces(">Z").workplane(centerOption="CenterOfBoundBox").pushPoints([(-25, 0), (25, 0)]).hole(13))
        part = part.union(lug.rotate((math.cos(a) * (R + 55), math.sin(a) * (R + 55), 0), (math.cos(a) * (R + 55), math.sin(a) * (R + 55), 1), math.degrees(a) - 90 + 90))
    # 12 inlet holes Ø70 in the lid ring for the feeder spouts, on Ø560
    lid = cq.Workplane("XY").circle(R + 30).extrude(3).translate((0, 0, 250))
    lid = lid.faces(">Z").workplane().polarArray(280, 0, 360, 12).hole(70)
    return part.union(lid).translate((0, 0, h_cone + 28.6))


def htube(L, s=50.8, t=3.0, axis="X"):
    """Hollow square tube along X (or Z), centred."""
    if axis == "Z":
        return cq.Workplane("XY").rect(s, s).rect(s - 2 * t, s - 2 * t).extrude(L).translate((0, 0, -L / 2))
    return cq.Workplane("YZ").rect(s, s).rect(s - 2 * t, s - 2 * t).extrude(L).translate((-L / 2, 0, 0))


def p1_210():
    """Ring frame: 12 bin positions on a dodecagon, radius 1,250 to bin centres, 50 sq tube ring at 1,250 high on 12 legs."""
    Rb, Hr, tube = 1250.0, 1250.0, 50.8
    n = 12
    pts = [(math.cos(2 * math.pi * k / n) * (Rb + 340), math.sin(2 * math.pi * k / n) * (Rb + 340)) for k in range(n)]
    frame = cq.Workplane("XY")
    for k in range(n):
        x0, y0 = pts[k]; x1, y1 = pts[(k + 1) % n]
        L = math.hypot(x1 - x0, y1 - y0); a = math.degrees(math.atan2(y1 - y0, x1 - x0))
        beam = htube(L).rotate((0, 0, 0), (0, 0, 1), a).translate(((x0 + x1) / 2, (y0 + y1) / 2, Hr))
        leg = htube(Hr, axis="Z").translate((x0, y0, Hr / 2))
        frame = frame.union(beam).union(leg)
    # inner support ring for the bin lugs (radius Rb - 340) on 12 radial arms
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        arm = htube(700).rotate((0, 0, 0), (0, 0, 1), math.degrees(a)).translate((math.cos(a) * Rb, math.sin(a) * Rb, Hr))
        frame = frame.union(arm)
    plate = cq.Workplane("XY")
    for k in range(n):                                  # foot plates with anchor holes
        x0, y0 = pts[k]
        plate = plate.union(cq.Workplane("XY").box(150, 150, 10).translate((x0, y0, 5)).faces(">Z").workplane(centerOption="CenterOfBoundBox")
                            .rect(100, 100, forConstruction=True).vertices().hole(14))
    return frame.union(plate)


def p1_302():
    """Bag-dump grate: 600 x 400 x 10 bar grid at 50 mm spacing, with a 40 mm upstand and 4 in collar at the back."""
    g = cq.Workplane("XY").box(600, 400, 10)
    xs = [-250 + 50 * i for i in range(11)]
    g = g.faces(">Z").workplane().pushPoints([(x + 25, 0) for x in xs[:-1]]).rect(40, 360).cutThruAll()
    up = cq.Workplane("XY").rect(600, 400).rect(600 - 2 * GA14, 400 - 2 * GA14).extrude(300).translate((0, 0, 5))
    up = up.faces(">Y").workplane(centerOption="CenterOfBoundBox").center(0, 60).hole(TC4_TUBE - 3.3)
    fer = ferrule4().rotate((0, 0, 0), (1, 0, 0), -90).translate((0, 200, 215))
    return g.union(up).union(fer)


def p1_303():
    """Chute: 200 sq flange (8 x Ø9 on 170 sq, VERIFY blender valve) loft 180 to 4 in TC ferrule."""
    fl = (cq.Workplane("XY").rect(200, 200).extrude(6).faces(">Z").workplane().rect(170, 170, forConstruction=True).vertices().hole(9)
          .faces(">Z").workplane().pushPoints([(0, 85), (0, -85), (85, 0), (-85, 0)]).hole(9).faces(">Z").workplane().rect(120, 120).cutThruAll())
    tr = shell_loft(120, 120, TC4_TUBE, 0, 180, GA14, round2=True)
    fer = ferrule4().translate((0, 0, -180 - 28.6))
    return fl.union(tr).union(fer).translate((0, 0, 180 + 28.6))


def p1_304():
    """Sieve deck: Ø480 x 150 housing with screen ledge, 4 clamp lugs, cone to 4 in TC, 3 legs."""
    R = 240.0
    hs = cq.Workplane("XY").circle(R + GA14).circle(R).extrude(150)
    ledge = cq.Workplane("XY").circle(R).circle(R - 15).extrude(6).translate((0, 0, 40))
    hc = R - TC4_TUBE / 2
    cone = (cq.Workplane("XY").circle(R + GA14).workplane(offset=-hc).circle(TC4_TUBE / 2 + GA14).loft()
            .cut(cq.Workplane("XY").workplane(offset=0.01).circle(R).workplane(offset=-hc - 0.02).circle(TC4_TUBE / 2).loft()))
    fer = ferrule4().translate((0, 0, -hc - 28.6))
    part = hs.union(ledge).union(cone).union(fer)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        part = part.union(cq.Workplane("XY").box(50, 40, 8).translate((math.cos(a) * (R + 25), math.sin(a) * (R + 25), 146))
                          .faces(">Z").workplane(centerOption="CenterOfBoundBox").hole(11))
    return part.translate((0, 0, hc + 28.6))


def p1_309():
    """Dolly base: Ø560 x 3 mm plate with a 25 mm rim, 4 caster pads with 4 x Ø9 each (Colson 2 series plate 2.5 x 3.6 in, VERIFY)."""
    base = cq.Workplane("XY").circle(280).extrude(GA11)
    rim = cq.Workplane("XY").circle(280).circle(280 - GA11).extrude(25)
    part = base.union(rim)
    pts = []
    for k in range(4):
        a = math.radians(45 + 90 * k); cx, cy = math.cos(a) * 190, math.sin(a) * 190
        pts += [(cx - 23.8, cy - 35.7), (cx + 23.8, cy - 35.7), (cx - 23.8, cy + 35.7), (cx + 23.8, cy + 35.7)]
    part = part.faces("<Z").workplane().pushPoints([(x, -y) for x, y in pts]).hole(9)
    return part.faces("<Z").workplane().center(0, 0).hole(40)       # drain / lift-pin hole


def p1_408():
    """Turntable: Ø762 disc 14 ga with 25 mm rim; centre bolt pattern 4 x Ø7 on 250 sq for a 12 in lazy-susan bearing (VERIFY)."""
    disc = cq.Workplane("XY").circle(381).extrude(GA14)
    rim = cq.Workplane("XY").circle(381).circle(381 - GA14).extrude(25)
    d = disc.union(rim)
    return d.faces("<Z").workplane().rect(250, 250, forConstruction=True).vertices().hole(7)


def p1_208():
    """Pail tumbler: 600 x 400 x 3 mm base with 4 bearing uprights 10 mm thick, roller shafts Ø25.4 at 180 mm centres
    and 200 mm high (a 5 gal pail Ø300 sits between two Ø60 UHMW rollers). Gearmotor plate 4 x Ø9 on 100 x 70 (VERIFY motor)."""
    base = cq.Workplane("XY").rect(600, 400).extrude(GA11)
    ups = None
    for x in (-270, 270):
        for y in (-90, 90):
            u = cq.Workplane("YZ", origin=(x - 5, y, GA11)).rect(80, 240, centered=(True, False)).extrude(10)
            ups = u if ups is None else ups.union(u)
    part = base.union(ups)
    for y in (-90, 90):                                     # bearing bores through each pair of uprights
        bore = cq.Workplane("YZ", origin=(-320, y, 200)).circle(12.7 + 0.15).extrude(640)
        part = part.cut(bore)
    part = part.faces("<Z").workplane().pushPoints([(x, y) for x in (-250, 250) for y in (-170, 170)]).hole(9)     # floor / table anchors
    return part.faces("<Z").workplane().pushPoints([(200 + dx, dy) for dx in (-50, 50) for dy in (-35, 35)]).hole(9)   # gearmotor plate


# 3D-printed fixtures (PETG), never touch product
def nest(dia_in, h=40.0):
    d = dia_in * IN + 1.0                                  # 0.5 mm radial clearance
    blk = cq.Workplane("XY").box(d + 30, d + 30, h).translate((0, 0, h / 2)).edges("|Z").fillet(8)
    blk = blk.faces(">Z").workplane().hole(d, h - 4)
    blk = blk.faces(">Z").workplane().rect(d + 30 - 20, d + 30 - 20, forConstruction=True).vertices().cboreHole(4.5, 8, 4)  # M4 to the filler plate
    return blk.faces(">Z").edges().chamfer(1.0)


def grip(cap_mm, h=30.0):
    """Cap grip: ribbed bore to the cap OD + 0.4, T-handle, for consistent hand torque."""
    bore = cap_mm + 0.4
    body = cq.Workplane("XY").circle(bore / 2 + 6).extrude(h)
    handle = cq.Workplane("XY").box(bore + 90, 22, 14).translate((0, 0, h - 7))
    body = body.union(handle)
    return body.faces("<Z").workplane().hole(bore, h - 4)            # cap enters from below


PARTS = [
    dict(id="P1-206", fn=p1_206, title="Stainless work table 60 x 30 in", material="SS 304 #4, 14 ga top, 1.5 in sq tube", qty="5",
         process="Laser cut, brake, TIG, ground", tol="sheet", assy="Weigh bench (1) + pack bench (4)", flat="top", contact=True,
         notes=["Top seams continuous welded and ground; legs capped and sealed (no open hollow tube)", "Adjustable bullet feet, 1 in travel"],
         fasteners=lambda f: "Ø10 for accessory clamps (hood, nests)"),
    dict(id="P1-207", fn=p1_207, title="Weigh bench backdraft dust hood", material="SS 304, 14 ga", qty="1", tol="sheet", flat="front",
         process="Laser cut, brake, TIG", assy="Weigh bench P1-206", contact=False,
         notes=["3 slots 1300 x 25 mm: 300 cfm gives 2.6 m/s slot velocity, capture 0.5 m/s at 300 mm", "4 in duct collar to P1-310 dust collector"],
         fasteners=lambda f: "M6 x 16 A2-70 to table edge, 6 N·m" if f["dia"] < 8 else "4 in duct, quick clamp"),
    dict(id="P1-208", fn=p1_208, title="Premix pail tumbler frame (5 gal pail)", material="SS 304, 3 mm base, 10 mm uprights", qty="1",
         process="Laser cut, brake, TIG, ground", assy="Weigh & dispense (minors premix)", tol="sheet", flat="base", contact=False,
         notes=["Rollers: 2 x Ø60 UHMW on Ø25.4 SS shafts, 4 x 1 in flange bearings; 30 rpm, 5 min",
                "Pail is sealed (lid + liner) while it turns, so the frame never touches product", "Gearmotor 1/8 HP 90 V DC with chain to one roller: VERIFY plate"],
         fasteners=lambda f: "1 in shaft, flange bearing" if f["dia"] > 20 else "M8 x 20 A2-70"),
    dict(id="P1-210", fn=p1_210, title="Ingredient bin ring frame (12 positions)", material="SS 304 2 in sq tube 11 ga, 10 mm foot plates", qty="1",
         process="Saw, TIG, ground, passivated", tol="sheet", assy="Dosing station", flat=None, contact=False,
         notes=["Bin centres on R1,250 mm; ring 1,250 high so feeder spouts drop into the weigh hopper inlet ring", "Anchor 4 x 1/2 in wedge anchors per foot"],
         fasteners=lambda f: "1/2 in wedge anchor, 3 in embed" if f["dia"] > 13 else "M12 to bin lug"),
    dict(id="P1-211", fn=p1_211, title="Ingredient bin 5 cu ft", material="SS 304 #4, 14 ga; flanges 6 mm", qty="9 (12 positions)", tol="sheet",
         process="Laser cut, brake, TIG, ground, passivated", assy="Dosing station", flat="flange", contact=True,
         notes=["Working volume 141 L [5.0 cu ft] at 90 % fill; cone valley angle >= 60° for herbs", "Outlet flange 4 x Ø11 on 160 sq: VERIFY feeder inlet before cutting",
                "Lid: hinged with bag-rest grate and vent sock to P1-310"],
         fasteners=lambda f: "M10 x 30 A2-70 + FDA gasket, 25 N·m" if abs(f["dia"] - 11) < 1 else ("M8 lid hinge" if f["dia"] < 10 else "M12 x 40 to ring frame")),
    dict(id="P1-220", fn=p1_220, title="Weigh hopper 141 L on 3 load cells", material="SS 316L #4, 14 ga; lugs 10 mm 304", qty="1", tol="sheet",
         process="Laser cut, roll, TIG, ground, polished, passivated", assy="Dosing station", flat="lid", contact=True,
         notes=["Load cells 3 x 50 kg S-beam/compression with mounts: VERIFY lug holes to the mount", "12 feeder inlets Ø70 on Ø560; flexible boots isolate feeders from the scale",
                "4 in Tri-Clamp outlet to sanitary butterfly valve P1-223"],
         fasteners=lambda f: "M12 x 40 to load-cell mount" if abs(f["dia"] - 13) < 1 else "feeder boot, hose clamp"),
    dict(id="P1-302", fn=p1_302, title="Blender bag-dump grate and dust upstand", material="SS 304, 10 mm bar + 14 ga", qty="1", tol="sheet",
         process="Laser cut, TIG, ground", assy="Blender P1-301", flat="grate", contact=True,
         notes=["Bars 10 mm wide at 50 mm pitch keep bags and gloves out", "VERIFY outside 600 x 400 against the used blender's cover opening"],
         fasteners=lambda f: "4 in Tri-Clamp to dust duct"),
    dict(id="P1-303", fn=p1_303, title="Blender discharge chute to 4 in Tri-Clamp", material="SS 316L #4, 14 ga; flange 6 mm 304", qty="1", tol="sheet",
         process="Laser cut, form, TIG, polish", assy="Blender P1-301 to sieve P1-304", flat="flange", contact=True,
         notes=["VERIFY flange to the used blender's discharge valve before cutting"],
         fasteners=lambda f: "M8 x 25 A2-70, 18 N·m + FDA silicone gasket"),
    dict(id="P1-304", fn=p1_304, title="Sieve deck housing for 18 in screen", material="SS 304 #4, 14 ga", qty="1", tol="sheet",
         process="Laser cut, roll, TIG, ground", assy="Blending", flat=None, contact=True,
         notes=["Screen (P1-305) sits on the 15 mm ledge; 4 quick clamps on the lugs", "Vibrator P1-306 bolts to the leg frame, not the housing"],
         fasteners=lambda f: "quick clamp 1/2 in"),
    dict(id="P1-309", fn=p1_309, title="Drum dolly base", material="SS 304, 3 mm [11 ga]", qty="3", tol="sheet", process="Laser cut, roll rim, TIG",
         assy="Blend drums P1-308", flat="base", contact=False, notes=["4 casters 3 in, 2 with brakes"],
         fasteners=lambda f: "5/16-18 x 3/4 SS + nyloc (caster plate)" if f["dia"] < 10 else "drain"),
    dict(id="P1-408", fn=p1_408, title="Accumulation turntable disc 30 in", material="SS 304 #4, 14 ga", qty="1", tol="sheet",
         process="Laser cut, roll rim, TIG", assy="Pack bench", flat="disc", contact=False, notes=["12 in lazy-susan bearing, 500 lb: VERIFY hole pattern"],
         fasteners=lambda f: "#10-24 x 1/2 SS flat head"),
]
PRINTS = [
    dict(id="P1-410a", fn=lambda: nest(2.6), title="Filler nest, shaker-250 (Ø66 mm)", qty=2),
    dict(id="P1-410b", fn=lambda: nest(3.4), title="Filler nest, jar-12 (Ø86 mm)", qty=2),
    dict(id="P1-410c", fn=lambda: grip(53 + 3), title="Cap grip, 53 mm sifter cap", qty=2),
    dict(id="P1-410d", fn=lambda: grip(89 + 3), title="Cap grip, 89 mm jar cap", qty=2),
]


def dxf(shape, pid, kind, outdir):
    """Cut file from the part: a planar section through its flat element, written in mm and inch."""
    sv = shape.val()
    bb = sv.BoundingBox()
    if kind == "front":                                   # hood slot plate: section normal to Y at the front skin
        sec = cq.Workplane("XZ", origin=(0, bb.ymin + 0.9, 0)).add(sv).section(0)
        flat = sec.val().rotate(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -90)
    else:
        z = {"top": bb.zmax - 0.95, "flange": bb.zmin + 3, "lid": bb.zmax - 1.5, "grate": bb.zmin + 5,
             "base": bb.zmin + 1.5, "disc": bb.zmin + 0.9}[kind]
        flat = cq.Workplane("XY").add(sv).section(z).val().translate(cq.Vector(0, 0, -z))
    cq.exporters.export(cq.Workplane("XY").add(flat), str(outdir / f"{pid}_{kind}_mm.dxf"), "DXF")
    cq.exporters.export(cq.Workplane("XY").add(flat.scale(1 / IN)), str(outdir / f"{pid}_{kind}_in.dxf"), "DXF")


def main():
    cad, dwg, dx, pr = HERE, P1 / "drawings" / "parts", P1 / "dxf", HERE / "print"
    for d in (cad / "step", cad / "stl", dwg, dx, pr):
        d.mkdir(parents=True, exist_ok=True)
    summary = []
    for p in PARTS:
        s = p["fn"]()
        cq.exporters.export(s, str(cad / "step" / f"{p['id']}.step"))
        cq.exporters.export(s, str(cad / "stl" / f"{p['id']}.stl"), tolerance=0.2, angularTolerance=0.2)
        info = dict(title=p["title"], partno=p["id"], material=p["material"], process=p["process"], qty=p["qty"], density=8.0, tol=p["tol"],
                    notes=p["notes"], project=PROJECT, assy=p["assy"], qty_label="QTY PHASE 1")
        svg, feats = partsheet.sheet(s, info, fasteners=p["fasteners"])
        (dwg / f"{p['id']}.svg").write_text(svg)
        files = []
        if p["flat"]:
            try:
                dxf(s, p["id"], p["flat"], dx); files = [f"dxf/{p['id']}_{p['flat']}_mm.dxf", f"dxf/{p['id']}_{p['flat']}_in.dxf"]
            except Exception as e:                              # report, never hide
                print("  DXF failed", p["id"], e)
        bb = s.val().BoundingBox()
        summary.append(dict(id=p["id"], title=p["title"], qty=p["qty"], material=p["material"], features=len(feats), contact=p["contact"],
                            size_mm=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)], mass_kg=round(s.val().Volume() * 8.0e-6, 2),
                            step=f"cad/step/{p['id']}.step", drawing=f"drawings/parts/{p['id']}.svg", dxf=files))
        print(p["id"], len(feats), "features", summary[-1]["size_mm"], summary[-1]["mass_kg"], "kg", files and "dxf ok" or "")
    for p in PRINTS:
        s = p["fn"]()
        cq.exporters.export(s, str(pr / f"{p['id']}.stl"), tolerance=0.02, angularTolerance=0.1)
        cq.exporters.export(s, str(cad / "step" / f"{p['id']}.step"))
        bb = s.val().BoundingBox()
        summary.append(dict(id=p["id"], title=p["title"], qty=p["qty"], material="PETG", print=True, stl=f"cad/print/{p['id']}.stl",
                            size_mm=[round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)], grams_est=round(s.val().Volume() * 1.27e-3 * 0.45, 1)))
        print(p["id"], "print", summary[-1]["size_mm"])
    (cad / "parts.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
