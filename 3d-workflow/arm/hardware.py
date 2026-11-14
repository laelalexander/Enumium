"""Printed-part generators (CadQuery source strings) for the tube-and-cheek-plate
arm.  DRAFT geometry: every dimension marked MEASURE depends on the exact part
you receive.  Check each against the purchased item (calipers) and edit
HW below before printing.  Print in PETG/ASA or nylon-CF, >=5 perimeters,
40%+ gyroid infill, load axis NOT along layer lines."""
import math

HW = dict(
    tube_od=38.1,          # 1.5" aluminium tube
    tube_clear=0.3,
    shaft=12.0,            # joint shaft (12 mm keyless steel/stainless rod)
    bearing_od=28.0, bearing_w=8.0,      # 6001-2RS (12x28x8)
    motor_pilot=38.1, motor_pcd_sq=47.14, motor_hole=5.5,   # NEMA23 face: MEASURE gearbox flange
    hub_pcd=40.0, hub_hole=5.5, hub_bore=14.0,              # shaft clamp hub flange: MEASURE
    nema17_sq=31.0, nema17_pilot=22.5,
    insert_m4_hole=5.6,    # M4 heat-set insert (OD 5.7-6.0, L 8.1): pilot hole for PETG
    turntable_pcd=170.0, turntable_hole=6.5,                # base_top_plate -> YAW-01 disc bolt circle (M6)
    # 12 in round turntable bearing (typical listing values; MEASURE yours, then python run.py cut)
    turntable_od=305.0, turntable_id=200.0, turntable_h=12.0,
    turntable_fixed_pcd=285.0, turntable_rot_pcd=230.0, turntable_ring_holes=4, turntable_ring_hole=5.5,
    yaw_flange_sq=60.0,    # yaw gearbox output flange, square (MEASURE): sets the BASE-01 underside pocket
    hub_flange_od=52.0,    # clamp-hub flange OD (MEASURE): sets the YAW-01 centre clearance
)

def belt_center_mm(ratio, small_teeth=16):
    """Center distance for the HTD 5M stage (pitch 5 mm): pulley flanges 5 mm apart, never under 45 mm so the
    gearbox flange clears the shaft collar. Kept short so the shoulder cheek still fits a 256 mm bed.
    Cheek slots give +-4 mm tensioning; pick the nearest stock belt (BOM)."""
    dp_s = small_teeth * 5 / math.pi
    dp_l = dp_s * ratio
    return round(max((dp_s + dp_l) / 2 + 12, 45.0), 1)


def block_x0(ratio, small_teeth=16):
    """Distance from the joint axis to the tube block's inner face. The joint pulley (flange radius = pitch radius
    + 2.5) turns inside the cheeks, so the block and the incoming tube start 4 mm beyond it (never under 20)."""
    r_flange = small_teeth * ratio * 5 / math.pi / 2 + 2.5
    return float(max(20, math.ceil(r_flange + 4)))

def tube_block(x0=20.0):
    """Spacer block between the cheeks, x0 .. x0+50 from the joint axis; clamps the incoming tube (50 mm engagement)."""
    h = HW
    return f'''bore = {h["tube_od"] + h["tube_clear"]}
blk = cq.Workplane("XY").box(50, 56, 80)           # x 50, y 56, z 80, centred
blk = blk.translate(({x0 + 25}, 0, 0))             # x in [{x0:g}, {x0 + 50:g}]
blk = blk.cut(cq.Workplane("YZ").workplane(offset={x0}).circle(bore / 2).extrude(50))
blk = blk.cut(cq.Workplane("XY").workplane(offset=-40).center({x0 + 25}, 0).circle(2.75).extrude(80))   # cross pin M5
result = blk.cut(cq.Workplane("XZ").workplane(offset=-30).pushPoints([({x0 + 8}, 30), ({x0 + 8}, -30), ({x0 + 42}, 30), ({x0 + 42}, -30)]).circle(2.75).extrude(60))
'''

def cheek(motor_side: bool, center_mm: float, x0=20.0):
    h = HW
    C = center_mm
    x1 = x0 + 50
    x0c, x1c = (-C - 36, x1) if motor_side else (-30, x1)   # 36: slot end + 5 mm wall behind the gearbox bolts
    L = x1c - x0c
    code = f'''t, x0, L = 12.0, {x0c}, {L}
plate = cq.Workplane("XY").box(L, t, 100, centered=(False, True, True)).translate((x0, 0, 0)).edges("|Y").fillet(8)
# bearing recess on outer face (y=+t/2 side) + shaft clearance
plate = plate.cut(cq.Workplane("XZ").workplane(offset=-t/2).circle({h["bearing_od"] + 0.15}/2).extrude({h["bearing_w"] + 0.2}))   # XZ normal is -Y: +extrude cuts into the plate
plate = plate.cut(cq.Workplane("XZ").workplane(offset=-t/2).circle(10.0).extrude(t))
# block bolt holes (M5)
plate = plate.cut(cq.Workplane("XZ").workplane(offset=-t/2).pushPoints([({x0 + 8}, 30), ({x0 + 8}, -30), ({x0 + 42}, 30), ({x0 + 42}, -30)]).circle(2.75).extrude(t))
'''
    if motor_side:
        s = h["motor_pcd_sq"] / 2
        code += f'''# gearbox pilot + 4 slotted bolt holes (slots along X: +-4.25 mm belt tension travel)
plate = plate.cut(cq.Workplane("XZ").workplane(offset=-t/2).center({-C}, 0).circle({h["motor_pilot"] + 0.5}/2).extrude(t))
for sx in (-{s}, {s}):
    for sz in (-{s}, {s}):
        plate = plate.cut(cq.Workplane("XZ").workplane(offset=-t/2).center({-C} + sx, sz).slot2D(14, {h["motor_hole"]}, 0).extrude(t))
'''
    code += "result = plate\n"
    return code

def tube_socket():
    h = HW
    return f'''bore = {h["tube_od"] + h["tube_clear"]}
plate = cq.Workplane("XY").box(90, 10, 80, centered=(True, False, True)).edges("|Y").fillet(10)   # y in [0,10], hub face
plate = plate.cut(cq.Workplane("XZ").circle({h["hub_bore"]}/2).extrude(-10))
pts = [({h["hub_pcd"]}/2*math.cos(a), {h["hub_pcd"]}/2*math.sin(a)) for a in (math.pi/4 + k*math.pi/2 for k in range(4))]
plate = plate.cut(cq.Workplane("XZ").pushPoints(pts).circle({h["hub_hole"]}/2).extrude(-10))
sock = cq.Workplane("YZ").workplane(offset=30).center(25, 0).circle(25).extrude(65)    # tube axis at y=25
gus = cq.Workplane("XY").box(65, 10, 50, centered=(False, False, True)).translate((30, 0, 0))
body = plate.union(sock).union(gus)
body = body.cut(cq.Workplane("YZ").workplane(offset=35).center(25, 0).circle(bore/2).extrude(60))
result = body.cut(cq.Workplane("XY").workplane(offset=-30).center(62, 25).circle(2.75).extrude(60))   # cross pin
'''.replace("cq.Workplane(\"XZ\")", "cq.Workplane(\"XZ\")")

def base_top_plate():
    h = HW
    return f'''disc = cq.Workplane("XY").circle(105).extrude(10)
disc = disc.cut(cq.Workplane("XY").circle({h["hub_bore"]}/2).extrude(10))
pts = [({h["hub_pcd"]}/2*math.cos(a), {h["hub_pcd"]}/2*math.sin(a)) for a in (math.pi/4 + k*math.pi/2 for k in range(4))]
disc = disc.cut(cq.Workplane("XY").pushPoints(pts).circle({h["hub_hole"]}/2).extrude(10))
pts2 = [({h["turntable_pcd"]}/2*math.cos(k*math.pi/4), {h["turntable_pcd"]}/2*math.sin(k*math.pi/4)) for k in range(8)]
disc = disc.cut(cq.Workplane("XY").pushPoints(pts2).circle({h["turntable_hole"]}/2).extrude(10))
sock = cq.Workplane("XY").workplane(offset=10).circle(25).extrude(70)
body = disc.union(sock)
result = body.cut(cq.Workplane("XY").workplane(offset=14).circle({h["tube_od"] + h["tube_clear"]}/2).extrude(70))
'''

def gripper_body():
    h = HW; s = h["nema17_sq"] / 2
    return f'''body = cq.Workplane("XY").box(110, 62, 34, centered=(False, True, True))
body = body.cut(cq.Workplane("XY").box(40, 30, 24, centered=(False, True, True)).translate((5, 0, 0)))   # coupler pocket
body = body.cut(cq.Workplane("YZ").circle({h["nema17_pilot"]}/2).extrude(5))
body = body.cut(cq.Workplane("YZ").pushPoints([({s}, {s}), ({s}, -{s}), (-{s}, {s}), (-{s}, -{s})]).circle(1.7).extrude(12))
body = body.cut(cq.Workplane("YZ").workplane(offset=45).circle(5.0).extrude(65))                      # lead screw clearance
body = body.cut(cq.Workplane("YZ").workplane(offset=40).pushPoints([(20, 0), (-20, 0)]).circle(4.05).extrude(70))   # 8 mm rods
body = body.cut(cq.Workplane("XY").workplane(offset=-17).pushPoints([(60, 20), (60, -20), (92, 20), (92, -20)]).circle({h["insert_m4_hole"]}/2).extrude(11))   # M4 heat-set inserts
fixed = cq.Workplane("XY").box(10, 62, 56, centered=(False, True, True)).translate((110, 0, 0))
body = body.union(fixed)
result = body.cut(cq.Workplane("YZ").workplane(offset=110).pushPoints([(20, 0), (-20, 0)]).circle(4.05).extrude(10))
'''

def gripper_adapter():
    h = HW
    return f'''bore = {h["tube_od"] + h["tube_clear"]}
sock = cq.Workplane("YZ").circle(25).extrude(55)
plate = cq.Workplane("XY").box(62, 62, 8, centered=(False, True, False)).translate((0, 0, 20))
body = sock.union(plate)
body = body.cut(cq.Workplane("YZ").circle(bore/2).extrude(55)).union(cq.Workplane("XY").box(55, 30, 6, centered=(False, True, False)).translate((0, 0, 20)).cut(cq.Workplane("YZ").circle(bore/2).extrude(55)))
result = body.cut(cq.Workplane("XY").workplane(offset=20).pushPoints([(15, 20), (15, -20), (47, 20), (47, -20)]).circle(2.25).extrude(8))
'''

def gripper_jaw():
    return '''jaw = cq.Workplane("XY").box(30, 62, 56, centered=(False, True, True))
jaw = jaw.cut(cq.Workplane("YZ").pushPoints([(20, 0), (-20, 0)]).circle(7.7).extrude(30))              # LM8UU 15 mm bearings
jaw = jaw.cut(cq.Workplane("YZ").circle(5.5).extrude(30))                                              # lead screw
jaw = jaw.cut(cq.Workplane("YZ").pushPoints([(8, 0), (-8, 0), (0, 8), (0, -8)]).circle(1.7).extrude(30)) # T8 nut flange M3 holes
result = jaw
'''

# part name -> (code, qty, bbox_mm or None, note)
def parts(ratios):
    sh, el = ratios["shoulder"], ratios["elbow"]
    ratios = dict(ratios, wrist=1)
    out = {}
    for j, r in (("shoulder", sh), ("elbow", el), ("wrist", 1)):
        c, x0 = belt_center_mm(r), block_x0(r)
        out[f"{j}_cheek_motor"] = (cheek(True, c, x0), 1, "Motor-side cheek plate")
        out[f"{j}_cheek_plain"] = (cheek(False, c, x0), 1, "Plain cheek plate")
        out[f"{j}_tube_block"] = (tube_block(x0), 1, "Spacer block that clamps the incoming tube")
    out["tube_socket"] = (tube_socket(), 3, "Distal link end: hub flange + tube socket (shoulder, elbow, wrist)")
    out["base_top_plate"] = (base_top_plate(), 1, "Rotating plate: yaw hub + turntable + riser socket")
    out["gripper_body"] = (gripper_body(), 1, "NEMA17 lead-screw gripper body + fixed jaw")
    out["gripper_adapter"] = (gripper_adapter(), 1, "Tube-stub socket + plate bolting to gripper body (M4 heat-set inserts)")
    out["gripper_jaw"] = (gripper_jaw(), 1, "Sliding jaw on 2x8 mm rods")
    return out
