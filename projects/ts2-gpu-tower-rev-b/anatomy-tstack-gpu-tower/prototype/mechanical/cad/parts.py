"""TS-2 rev B part builders (build123d, OpenCascade B-rep).

Every builder returns a Part placed in the COLUMN-LOCAL frame (x = u radial, y = v tangential, z up, mm)
or the tower frame for tower-level parts (plinth, crown).  build_all.py rotates column parts to C1..C4.
Made parts carry real features (holes with their thread/fit, slots, fillets, chamfers); bought parts are
datasheet-envelope models with their interface features (fingers, connectors, ports, mounting holes).
"""
import math

from build123d import (Align, Axis, Box, Cylinder, Part, Pos, Rot, Location, fillet, chamfer, Plane, extrude,
                       Rectangle, RectangleRounded, Circle, SlotOverall, Polygon, Sketch, Torus, Sphere, Cone,
                       Compound, sweep, Polyline, Line, make_face, Wire, Edge, Vector, Locations, GridLocations,
                       loft, offset, mirror, Mode, BuildPart, BuildSketch, BuildLine, add, RegularPolygon, revolve,
                       JernArc, Spline, ThreePointArc, Face, Solid)

from params import P, slot_z

MIN = (Align.MIN, Align.MIN, Align.MIN)
CEN = (Align.CENTER, Align.CENTER, Align.CENTER)
CXY = (Align.CENTER, Align.CENTER, Align.MIN)


def box(x0, x1, y0, y1, z0, z1):
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=MIN)


def cyl_z(x, y, z0, z1, d):
    return Pos(x, y, z0) * Cylinder(d / 2, z1 - z0, align=CXY)


def cyl_x(x0, x1, y, z, d):
    return Pos(x0, y, z) * (Rot(0, 90, 0) * Cylinder(d / 2, x1 - x0, align=CXY))


def cyl_y(x, y0, y1, z, d):
    return Pos(x, y0, z) * (Rot(-90, 0, 0) * Cylinder(d / 2, y1 - y0, align=CXY))


def round_z(part, r):
    """fillet the vertical (Z-parallel) edges"""
    try:
        return fillet(part.edges().filter_by(Axis.Z), r)
    except Exception:
        return part


def round_x(part, r):
    try:
        return fillet(part.edges().filter_by(Axis.X), r)
    except Exception:
        return part


def round_y(part, r):
    try:
        return fillet(part.edges().filter_by(Axis.Y), r)
    except Exception:
        return part


def soft(part, r):
    try:
        return fillet(part.edges(), r)
    except Exception:
        return part


# ---------------------------------------------------------------- derived column numbers
RB = P["R_BULK"]                     # 203: bracket seat
RP = P["R_PLENUM"]                   # 200
V0, V1 = P["CARD_V0"], P["CARD_V1"]  # -55.4, 56.4
HW = P["HALF_W"]                     # 100
PV0, PV1 = P["POST_V"]               # 70, 100
RPI = P["R_POST_IN"]                 # (203, 233)
RPO = P["R_POST_OUT"]                # (508, 538)
ZC0 = P["Z_COL0"]                    # 400
ZB1 = ZC0 + P["BASE_T"]              # 412: top of column base plate
ZT0 = P["Z_COL1"]                    # 1364.8: underside of top plate
ZT1 = ZT0 + P["TOP_T"]
PITCH = P["SLOT_PITCH"]
VBP = P["V_BP"]                      # -62
BPT = P["BP_T"]
TAB_V = V0 + 120.0                   # 64.6: underside of the bracket tab (CEM bracket datum: 120.02 mm)
G_Z = P["Z_GROUP"]
MID0 = G_Z[0] + 8 * PITCH            # 858.4
MID1 = G_Z[1]                        # 918.4
XMEM_Z = (MID0 + MID1) / 2 - 5.0     # crossmember 10 mm plate centred in the midspan band
POST_LEN = ZT0 - ZB1


def card_pcb_z(group, i):
    return slot_z(group, i) + 2.0    # PCB bottom face (backplate 2 mm below it)


# ---------------------------------------------------------------- BOUGHT: GPU (card frame -> column frame)
def gpu_card():
    """RTX PRO 6000 Blackwell Max-Q, dual-slot blower.  Card frame: x from bracket outer face (0) to tail (267),
    y from the finger edge (0) up, z from the backplate (0) to the shroud top (40)."""
    L, H, T = P["GPU_L"], P["GPU_H"], P["GPU_T"]
    back = box(1.2, L - 1, 1.0, H - 0.5, 0, 2.0)
    pcb = box(1.2, L - 2, 0.0, H - 2.0, 2.0, 3.6)
    shroud = round_x(box(6.0, L, 2.0, H, 3.6, T), 3.0)
    # blower intake on the top face near the tail, with the fan hub
    intake = cyl_z(L - 62, H / 2 + 4, T - 3.0, T + 0.1, 64.0)
    shroud = shroud - intake
    hub = cyl_z(L - 62, H / 2 + 4, T - 3.0, T - 0.8, 30.0)
    blades = Part()
    for k in range(11):
        a = math.radians(k * 360 / 11)
        blades += Pos(L - 62 + 23 * math.cos(a), H / 2 + 4 + 23 * math.sin(a), T - 2.0) * (
            Rot(0, 0, math.degrees(a) + 35) * Box(16, 1.2, 1.6, align=CEN))
    # side fins visible through the vents near the bracket
    fins = Part()
    for k in range(14):
        fins += box(8, 60, 6 + k * 7.6, 6 + k * 7.6 + 0.6, 5.0, T - 2)
    shroud = shroud - box(6, 62, 4, H - 4, T - 1.2, T + 0.1)
    # gold fingers (x16: 41.9 .. 130.9) under the PCB edge
    fingers = box(P["GPU_FINGER_U0"], P["GPU_FINGER_U0"] + P["GPU_FINGER_L"], -8.0, 0.0, 2.0, 3.6)
    # 12V-2x6 socket on the tail edge
    pwr = box(L - 1.0, L + 1.5, P["GPU_PWR_V"] - 10.5, P["GPU_PWR_V"] + 10.5, 9.0, 19.0)
    # full-height dual-slot bracket with vent slots and the screw tab
    br = box(0.0, 1.2, -9.0, 120.0, -0.4, T + 0.4)
    for k in range(7):
        br = br - box(-0.1, 1.3, 8 + k * 14, 18 + k * 14, 4, T - 4)
    tab = box(0.0, 11.0, 120.0, 121.0, 2.0, 18.0) - cyl_y(6.0, 119.9, 121.1, 10.0, 4.4)
    tab2 = box(0.0, 11.0, 120.0, 121.0, 22.3, 38.3) - cyl_y(6.0, 119.9, 121.1, 30.3, 4.4)
    return dict(pcb=pcb + fingers, back=back, shroud=shroud, fan=hub + blades + fins, pwr=pwr, bracket=br + tab + tab2)


def card_to_column(shape, group, i):
    return Pos(RB, V0, slot_z(group, i)) * shape


# ---------------------------------------------------------------- BOUGHT: connectors on the backplane
def cem_x16(group, i):
    """Amphenol 10163106-A41410HLF class PCIe x16 vertical slot (164 pos, 1.00 mm): body 98 x 7.6 x 11.25."""
    z = card_pcb_z(group, i) + 0.8
    x0 = RB + P["GPU_FINGER_U0"] - 4.6
    body = box(x0, x0 + 98.0, VBP, VBP + P["CEM_H"], z - 3.8, z + 3.8)
    slot = box(x0 + 2.5, x0 + 95.5, VBP + 4.6, VBP + P["CEM_H"] + 0.1, z - 1.0, z + 1.0)
    key = box(x0 + 4.6 + 11.65 - 0.6, x0 + 4.6 + 11.65 + 0.6, VBP + 4.0, VBP + P["CEM_H"], z - 1.1, z + 1.1)
    latch = box(x0 + 95.0, x0 + 103.0, VBP, VBP + 14.0, z - 3.0, z + 3.0)
    return round_y(body - slot, 0.4) + key + latch


def mcio_x(group, i):
    """stagger so cables from higher slots drop past lower connectors without crossing"""
    return 258.0 + 24.0 * (7 - i)


def mcio_ra(group, i):
    """Amphenol G97R22332HR MCIO 8i (74 pos, 0.60 mm) right-angle receptacle on the CBP back face; cable exits -z."""
    z = slot_z(group, i) + 20.0
    x = mcio_x(group, i)
    y0 = VBP - BPT
    body = box(x - 12.0, x + 12.0, y0 - 8.6, y0, z - 5.0, z + 5.0)
    mouth = box(x - 10.5, x + 10.5, y0 - 7.4, y0 - 1.6, z - 5.1, z - 2.0)
    plug = box(x - 11.0, x + 11.0, y0 - 8.2, y0 - 1.0, z - 16.0, z - 5.0)
    return body - mouth, plug


def mcio_cable(group, i):
    """MCIO 8i cable (Gen5, 85 ohm, ~ 4.5 x 16 mm flat) from the plug down the rear channel to the base plate."""
    z = slot_z(group, i) + 20.0 - 16.0
    x = mcio_x(group, i)
    y = VBP - BPT - 12.0 - (4.0 if group == 0 else 13.0)    # upper-group cables run outboard of the lower connectors
    return box(x - 8.0, x + 8.0, y - 2.25, y + 2.25, ZB1, z)


def h12v2x6(group, i):
    """12V-2x6 right-angle header (Amphenol Minitek Pwr 10160920 family) at the tail end of the backplane."""
    z = slot_z(group, i) + 20.0
    x = 486.0
    hdr = box(x - 10.0, x + 10.0, VBP, VBP + 12.8, z - 6.6, z + 6.6) - box(x - 8.8, x + 8.8, VBP + 1.0, VBP + 13.0, z - 5.0, z + 5.0)
    return hdr


def gpu_power_cable(group, i):
    """12V-2x6 cable: header (x 486) -> 90 deg -> GPU tail socket (x 470, y ~ 0)."""
    z = slot_z(group, i) + 14.0
    plug_hdr = box(476.0, 496.0, VBP + 12.8, VBP + 26.0, z - 5.0, z + 5.0)
    run = box(490.0, 500.0, VBP + 26.0, V0 + P["GPU_PWR_V"] - 8.0, z - 4.0, z + 4.0)
    plug_gpu = box(471.5, 500.0, V0 + P["GPU_PWR_V"] - 10.0, V0 + P["GPU_PWR_V"] + 10.0, z - 5.0, z + 5.0)
    return plug_hdr + run + plug_gpu


# ---------------------------------------------------------------- MADE: CBP-8 backplane (PCB envelope + features)
CBP_X0, CBP_X1 = 236.0, 504.0


def cbp_board(group):
    z0 = G_Z[group] - 14.0
    z1 = G_Z[group] + 8 * PITCH + 14.0
    b = box(CBP_X0, CBP_X1, VBP - BPT, VBP, z0, z1)
    b = round_y(b, 4.0)
    for x in (CBP_X0 + 6, (CBP_X0 + CBP_X1) / 2, CBP_X1 - 6):
        for z in (z0 + 6, z0 + 205.0, z1 - 6):            # middle row matches CBP-8 H4-H6 (clear of slot 4)
            b = b - cyl_y(x, VBP - BPT - 0.1, VBP + 0.1, z, 3.4)
    return b


def cbp_rear_parts(group):
    """TPS25985 eFuse envelopes on the rear face and the four M6 press-fit power studs (2x +12V, 2x RTN).
    No PCIe redrivers: links run Gen4 x8 (loss budget in docs/electrical-architecture.md)."""
    out = Part()
    z0 = G_Z[group]
    y0 = VBP - BPT
    for i in range(8):
        z = slot_z(group, i) + 20.0
        out += box(452.0, 466.0, y0 - 1.2, y0, z - 6.0, z + 6.0)              # TPS25985 eFuse 4.5 x 5 + IMON/ILIM parts
    for zz in (z0 + 1 * PITCH + 35.9, z0 + 5 * PITCH + 35.9):              # in the gaps between 12V-2x6 header rows
        out += cyl_y(489.5, y0 - 35.0, y0, zz, 6.0) + cyl_y(489.5, y0 - 6.0, y0, zz, 12.0)          # +12V stud FHS-M6-35 + 6 mm bush
        out += cyl_y(489.5, y0 - 35.0, y0, zz + 19.0, 6.0) + cyl_y(489.5, y0 - 18.0, y0, zz + 19.0, 12.0)   # RTN stud + 18 mm bush
    return out


# ---------------------------------------------------------------- MADE: column structure
def base_plate():
    """TS2B-201 column base plate, 6061-T6 12 mm.  Datum A bottom face, B inner edge (x 200), C centre line (y 0)."""
    x0, x1 = RP, P["R_OUT"] + 2.0
    p = box(x0, x1, -HW - 2.0, HW + 2.0, ZC0, ZB1)
    p = round_z(p, 6.0)
    # post bores: counterbored M8 x 25 SHCS into the HFS6 tapped end (cbore 14 x 8.6 from below, 8.6 thru)
    for xp in (sum(RPI) / 2, sum(RPO) / 2):
        for yp in (-(PV0 + PV1) / 2, (PV0 + PV1) / 2):
            p = p - cyl_z(xp, yp, ZC0 - 0.1, ZB1 + 0.1, 8.6) - cyl_z(xp, yp, ZC0 - 0.1, ZC0 + 8.6, 14.0)
    # plinth bolts: 4x M10 clearance 11.0 thru, spot face 20 on top
    for xp in (RP + 60.0, P["R_OUT"] - 40.0):
        for yp in (-50.0, 50.0):
            p = p - cyl_z(xp, yp, ZC0 - 0.1, ZB1 + 0.1, 11.0) - cyl_z(xp, yp, ZB1 - 1.0, ZB1 + 0.1, 20.0)
    # MCIO cable pass (rear channel) and busbar pass, R4 slots
    p = p - round_z(box(240.0, 450.0, -98.0, -66.5, ZC0 - 0.1, ZB1 + 0.1), 4.0)
    p = p - round_z(box(470.0, 512.0, -96.0, -68.0, ZC0 - 0.1, ZB1 + 0.1), 4.0)
    # coolant riser holes 2x 16.5 (3/8 in tube + grommet), drip-tray drain 12
    for yp in (78.0, 90.0):
        pass
    p = p - cyl_z(575.0, 84.0, ZC0 - 0.1, ZB1 + 0.1, 16.5) - cyl_z(575.0, -84.0, ZC0 - 0.1, ZB1 + 0.1, 16.5)
    p = p - cyl_z(600.0, 0.0, ZC0 - 0.1, ZB1 + 0.1, 12.0)
    # bulkhead slot: 3.2 wide x 6 deep groove locates the bulkhead
    p = p - box(RP - 0.1, RP + 3.2, -HW, HW, ZB1 - 6.0, ZB1 + 0.1)
    # hold-down hinge block holes, 2x M5 tapped (4.2 drill 12 deep) per group bar
    p = p - cyl_z(290.0, 66.0, ZB1 - 12.0, ZB1 + 0.1, 4.2) - cyl_z(290.0, 52.0, ZB1 - 12.0, ZB1 + 0.1, 4.2)
    try:
        p = chamfer(p.edges().group_by(Axis.Z)[-1], 1.0)
    except Exception:
        pass
    return p


def top_plate():
    """TS2B-202 column top plate, 6061-T6 10 mm"""
    x0, x1 = RP, P["R_OUT"] + 2.0
    p = round_z(box(x0, x1, -HW - 2.0, HW + 2.0, ZT0, ZT1), 6.0)
    for xp in (sum(RPI) / 2, sum(RPO) / 2):
        for yp in (-(PV0 + PV1) / 2, (PV0 + PV1) / 2):
            p = p - cyl_z(xp, yp, ZT0 - 0.1, ZT1 + 0.1, 8.6) - cyl_z(xp, yp, ZT1 - 8.6, ZT1 + 0.1, 14.0)
    for xp in (RP + 40.0, RP + 160.0):           # crown ring bolts M8
        p = p - cyl_z(xp, 0, ZT0 - 0.1, ZT1 + 0.1, 9.0)
    p = p - box(RP - 0.1, RP + 3.2, -HW, HW, ZT0 - 0.1, ZT0 + 6.0)
    p = p - round_z(box(240.0, 450.0, -98.0, -66.5, ZT0 - 0.1, ZT1 + 0.1), 4.0)
    return p


def post(x, y):
    """HFS6-3030 extrusion envelope with the four slot-6 grooves and the centre bore"""
    L = POST_LEN
    s = box(x - 15, x + 15, y - 15, y + 15, ZB1, ZB1 + L)
    for a in range(4):
        g = box(-3.1, 3.1, 15 - 5.5, 15.1, ZB1 - 0.1, ZB1 + L + 0.1)
        s = s - Pos(x, y, 0) * (Rot(0, 0, 90 * a) * g)
    s = s - cyl_z(x, y, ZB1 - 0.1, ZB1 + L + 0.1, 6.8)
    return round_z(s, 1.5)


def posts():
    out = []
    for xr in (RPI, RPO):
        for sgn in (-1, 1):
            out.append(post(sum(xr) / 2, sgn * (PV0 + PV1) / 2))
    return out


def bulkhead():
    """TS2B-203 exhaust bulkhead, 6061-T6 3.0 mm.  One 98 x 34 window per card (R3), 6 bleed holes per group
    behind the backplane, 4 rail screw holes per group (M4 cbore for flush screw heads on the plenum side),
    edge mounting holes into the inner posts (M6 into slot-6 T-nuts)."""
    z0, z1 = ZB1 - 6.0, ZT0 + 6.0
    b = box(RP, RB, -HW, HW, z0, z1)
    for g in (0, 1):
        for i in range(8):
            z = slot_z(g, i)
            # window behind the bracket vents (bracket vent area y 8..106 of the card -> v -47.4..50.6)
            w = Pos((RP + RB) / 2, (V0 + 8 + V0 + 106) / 2, z + 22.0) * Box(4.0, 98.0, 34.0)
            b = b - round_x(w, 3.0) if False else b - w
            # 6-32 bracket screw clearance is in the rail, not here
        for k in range(6):
            b = b - cyl_x(RP - 0.1, RB + 0.1, -80.0, G_Z[g] + 40.0 + k * 65.0, 6.0)
        for zz in (G_Z[g] + 30.0, G_Z[g] + 200.0, G_Z[g] + 376.0):
            b = b - cyl_x(RP - 0.1, RB + 0.1, (TAB_V + V0 + 113.0) / 2 - 2.0, zz, 4.5)
    for zz in range(int(z0 + 40), int(z1 - 20), 120):
        for yy in (-(PV0 + PV1) / 2, (PV0 + PV1) / 2):
            b = b - cyl_x(RP - 0.1, RB + 0.1, yy, zz, 6.6)
    return b


def bracket_rail(group):
    """TS2B-205 bracket screw rail, 6061-T6 12 x 7.6 x 418.  The card bracket tab sits on its +y face
    (y = TAB_V); 8x 6-32 UNC-2B x 6 deep (#36 drill 2.85 x 9) for the bracket thumbscrews; 3x M4x0.7 x 8
    from the plenum side through the bulkhead."""
    z0, z1 = G_Z[group] - 8.0, G_Z[group] + 8 * PITCH + 2.0
    r = box(RB + 1.0, RB + 13.0, TAB_V - 7.6, TAB_V, z0, z1)
    for i in range(8):
        r = r - cyl_y(RB + 6.0, TAB_V - 9.0, TAB_V + 0.1, slot_z(group, i) + 10.0, 2.85)
    for zz in (G_Z[group] + 30.0, G_Z[group] + 200.0, G_Z[group] + 376.0):
        r = r - cyl_x(RB + 0.9, RB + 9.0, TAB_V - 3.8, zz, 3.3)
    return round_z(r, 1.0)


def tail_comb(side):
    """TS2B-206 tail guide comb, 6061-T6 16 x 22 x full height.  16 slots 41.0 +0.3/0 wide x 9 deep, each
    lined with 1.0 mm EPDM U-trim, so the card tail is held in z while it slides along y during insertion."""
    x0, x1 = P["R_CARD_TAIL"] - 9.0, P["R_CARD_TAIL"] + 7.0
    y0, y1 = (V0 - 1.0, V0 + 21.0) if side < 0 else (V1 - 22.0, V1 + 0.0)
    c = box(x0, x1, y0, y1, ZB1, ZT0)
    for g in (0, 1):
        for i in range(8):
            z = slot_z(g, i)
            c = c - box(x0 - 0.1, x0 + 9.0, y0 - 0.1, y1 + 0.1, z - 0.5, z + 40.5)
    # end tapped M6 x 12 into base/top plate (drawn as 5.0 drill)
    c = c - cyl_z((x0 + x1) / 2, (y0 + y1) / 2, ZB1 - 0.1, ZB1 + 14.0, 5.0)
    c = c - cyl_z((x0 + x1) / 2, (y0 + y1) / 2, ZT0 - 14.0, ZT0 + 0.1, 5.0)
    return round_z(c, 1.0)


def comb_liners():
    out = Part()
    for side in (-1, 1):
        y0, y1 = (V0 - 1.0, V0 + 21.0) if side < 0 else (V1 - 22.0, V1)
        for g in (0, 1):
            for i in range(8):
                z = slot_z(g, i)
                out += box(P["R_CARD_TAIL"] - 9.0, P["R_CARD_TAIL"], y0, y1, z - 0.5, z) + box(P["R_CARD_TAIL"] - 9.0, P["R_CARD_TAIL"], y0, y1, z + 40.0, z + 40.5)
    return out


HD_X = (280.0, 300.0)


def holddown_bar(group):
    """TS2B-207 hold-down bar, 6061-T6 20 x 14 channel x 420, hinged at its outer end.  It presses each card's
    top edge over the connector through a 3 mm EPDM 60A pad (TS2B-208) with ~ 1 mm squeeze = 15-25 N per card,
    so shipping shock (15 g x 1.45 kg = 213 N peak) cannot walk a card out of the CEM connector."""
    z0 = G_Z[group] - 4.0
    z1 = G_Z[group] + 8 * PITCH + 4.0
    y0 = V1 + 3.0
    b = box(HD_X[0], HD_X[1], y0, y0 + 14.0, z0, z1)
    b = b - box(HD_X[0] + 3.0, HD_X[1] - 3.0, y0 + 3.0, y0 + 14.1, z0 + 6.0, z1 - 6.0)    # channel
    hz = z0 + 8.0 if group == 0 else z1 - 8.0
    b = b - cyl_x(HD_X[0] - 0.1, HD_X[1] + 0.1, y0 + 7.0, hz, 6.1)                        # 6 mm hinge pin, H8
    return round_x(b, 1.0)


def holddown_pads(group):
    out = Part()
    for i in range(8):
        z = slot_z(group, i)
        out += box(HD_X[0] + 2.0, HD_X[1] - 2.0, V1, V1 + 3.0, z + 6.0, z + 34.0)
    return out


def hinge_block(group):
    """TS2B-209 hinge block, 6061-T6, bolted to the base plate (lower group) or top plate (upper group)"""
    y0 = V1 + 3.0
    if group == 0:
        z0, z1 = ZB1, G_Z[0] + 4.0 + 6.0
    else:
        z0, z1 = G_Z[1] + 8 * PITCH - 6.0, ZT0
    hb = box(HD_X[0] - 12.0, HD_X[0] - 0.5, y0 - 2.0, y0 + 16.0, z0, z1) + box(HD_X[1] + 0.5, HD_X[1] + 12.0, y0 - 2.0, y0 + 16.0, z0, z1)
    hz = G_Z[0] + 4.0 if group == 0 else G_Z[1] + 8 * PITCH - 4.0
    hb = hb - cyl_x(HD_X[0] - 12.1, HD_X[1] + 12.1, y0 + 7.0, hz, 6.0)
    return hb


def latch(group):
    """TS2B-210 red latch handle (6061, anodised signal red) + spring plunger; locks the bar free end to the
    midspan crossmember."""
    y0 = V1 + 3.0
    z = MID0 + 4.0 if group == 0 else MID1 - 4.0
    zz = (z, z + 22.0) if group == 0 else (z - 22.0, z)
    h = box(HD_X[0] - 6.0, HD_X[1] + 6.0, y0, y0 + 26.0, zz[0], zz[1])
    h = h - box(HD_X[0] - 0.2, HD_X[1] + 0.2, y0 - 0.1, y0 + 14.2, zz[0] - 0.1, zz[1] + 0.1)
    h = soft(h, 1.5)
    zm = (zz[0] + zz[1]) / 2
    h = h - cyl_x(HD_X[0] - 6.1, HD_X[1] + 6.1, y0 + 20.0, zm, 4.1)          # pivot pin 4 m6 / 4.1 slip (pin in the keeper)
    h = h - cyl_y((HD_X[0] + HD_X[1]) / 2, y0 + 16.0, y0 + 26.1, zm, 5.0)   # M6 spring plunger (GN 617-6) tapped
    return h


def crossmember():
    """TS2B-211 midspan crossmember, 6061-T6 10 mm: ties the four posts at mid height, carries both latch
    keepers and the red light bar; slotted for the rear channel."""
    c = box(RPI[1], RPO[0], -HW + 1.5, HW - 1.5, XMEM_Z, XMEM_Z + 10.0)
    c = c - box(RPI[1] - 0.1, RPO[0] + 0.1, V0 - 1.0, V1 + 1.0, XMEM_Z - 0.1, XMEM_Z + 10.1)     # card zone open
    c = c - round_z(box(240.0, 450.0, -98.0, -66.5, XMEM_Z - 0.1, XMEM_Z + 10.1), 4.0)
    c = c + box(RPI[1], RPO[0], V1 + 1.0, V1 + 34.0, XMEM_Z, XMEM_Z + 10.0)
    for x in (RPI[1] + 8, RPO[0] - 8):
        for y in (-85.0, 85.0):
            c = c - cyl_z(x, y, XMEM_Z - 0.1, XMEM_Z + 10.1, 6.6)
    c = round_z(c, 2.0)
    for yy in (-80.0, 80.0):     # light bar screws, M3 tapped in the outer edge
        c = c - cyl_x(RPO[0] - 10.0, RPO[0] + 0.1, yy, XMEM_Z + 5.0, 2.5)
    return c


def light_bar():
    """TS2B-212 signal-red diffuser on the crossmember outer edge (SK6812 strip behind)"""
    b = soft(box(RPO[0] - 2.0, RPO[0] + 30.0, -HW + 2.0, HW - 2.0, XMEM_Z - 4.0, XMEM_Z + 14.0), 2.0)
    b = b - box(RPO[0] - 2.1, RPO[0] + 26.0, -HW + 6.0, HW - 6.0, XMEM_Z - 1.0, XMEM_Z + 11.0)   # LED strip / crossmember pocket
    for yy in (-80.0, 80.0):     # 2x M3 x 35 into the crossmember edge (tapped M3, 2.5 x 10), counterbored 6 x 4
        b = b - cyl_x(RPO[0] - 2.1, RPO[0] + 30.1, yy, XMEM_Z + 5.0, 3.4) - cyl_x(RPO[0] + 26.0, RPO[0] + 30.1, yy, XMEM_Z + 5.0, 6.0)
    return b


def side_skin(side):
    """TS2B-213 side skin 5052-H32 1.5 mm brushed; 20 x M5 button heads into post T-nuts"""
    y = side * HW
    s = box(RP + 3.0, RPO[1], min(y, y + side * 1.5), max(y, y + side * 1.5), ZB1, ZT0)
    for zz in range(int(ZB1 + 30), int(ZT0 - 10), 180):
        for xx in (sum(RPI) / 2, sum(RPO) / 2):
            s = s - cyl_y(xx, min(y, y + side * 1.5) - 0.1, max(y, y + side * 1.5) + 0.1, zz, 5.5)
    return s


def bp_carrier():
    """TS2B-214 backplane carrier, 6061-T6 3 mm: holds both CBP-8 boards on M3 x 8 standoffs and stiffens the
    connector field against card insertion force (8 x 115 N)."""
    c = box(CBP_X0 - 4.0, CBP_X1 + 4.0, VBP - BPT - 12.0 - 3.0, VBP - BPT - 12.0, ZB1 + 10.0, ZT0 - 10.0)
    for g in (0, 1):
        for i in range(8):
            z = slot_z(g, i) + 20.0
            x = mcio_x(g, i)
            c = c - box(x - 13.0, x + 13.0, VBP - BPT - 15.1, VBP - BPT - 11.9, z - 18.0, z + 6.0)
    c = c - box(479.0, 497.0, VBP - BPT - 15.1, VBP - BPT - 11.9, ZB1 + 9.0, ZT0 - 20.0)     # open at the bottom: the busbars enter from the arm
    yy0, yy1 = VBP - BPT - 15.1, VBP - BPT - 11.9
    for g in (0, 1):                     # M3 clearance for the M3 x 12 standoffs under the CBP-8 mounting holes
        za, zb = G_Z[g] - 14.0, G_Z[g] + 8 * PITCH + 14.0
        # the right-hand hole column (x 498) has no standoff: the busbar stud stack (4 x M6 + Cu bushes) carries that edge
        for x in (CBP_X0 + 6, (CBP_X0 + CBP_X1) / 2):
            for z in (za + 6, za + 205.0, zb - 6):
                c = c - cyl_y(x, yy0, yy1, z, 3.4)
    for x in (CBP_X0 + 2.0, 470.0):      # 4x M4 clearance: angle clips (30 x 30 x 3, B-215C) to the base and top plates
        for z in (ZB1 + 22.0, ZT0 - 22.0):
            c = c - cyl_y(x, yy0, yy1, z, 4.5)
    return c


def busbars():
    """TS2B-215 / 216 column busbars, C11000 14 x 10 (140 mm2: 2.9 A/mm2 at the 400 A feed end, 1.4 A/mm2 above the
    lower CBP-8), bright tin.  Stack behind each CBP-8: board rear -> 6 mm Cu bush -> +12 V bar -> 2 mm FR4 spacer ->
    RTN bar.  The RTN studs reach their bar through 18 mm Cu bushes that pass the +12 V bar in a 17 mm hole with a
    PTFE sleeve.  Feed: two 4/0 lugs back to back on 2x M8 at the bottom end (harness C01 / C02)."""
    y0 = VBP - BPT
    xa, xb = 481.0, 495.0
    z0, z1 = ZC0 - 300.0, G_Z[1] + 330.0
    pos = box(xa, xb, y0 - 16.0, y0 - 6.0, z0, z1)
    neg = box(xa, xb, y0 - 28.0, y0 - 18.0, z0, z1)
    for g in (0, 1):
        for zz in (G_Z[g] + 1 * PITCH + 35.9, G_Z[g] + 5 * PITCH + 35.9):
            pos = pos - cyl_y(489.5, y0 - 16.1, y0 - 5.9, zz, 6.6) - cyl_y(489.5, y0 - 16.1, y0 - 5.9, zz + 19.0, 17.0)
            neg = neg - cyl_y(489.5, y0 - 28.1, y0 - 17.9, zz + 19.0, 6.6)
    for zz in (z0 + 25.0, z0 + 25.0 + LUG_PITCH_BB):
        pos = pos - cyl_y(488.0, y0 - 16.1, y0 - 5.9, zz, 8.5)
        neg = neg - cyl_y(488.0, y0 - 28.1, y0 - 17.9, zz, 8.5)
    return pos, neg


LUG_PITCH_BB = 44.45


# ---------------------------------------------------------------- MADE/BUILD: tracing coil
TR0, TR1 = P["R_TRACE0"], P["R_TRACE1"]


def tracing_coil():
    """TS2B-220 tracing coil (built by a coil shop to our drawing): 3 rows x 32 passes of 3/8 in OD x 0.032
    C12200 tube on 25.4 x 22 staggered pitch, 0.15 mm 1100-H14 plate fins at 12 FPI, 1.2 mm 304 tube sheets,
    4 circuits (2 per 8-GPU group), headers 7/8 in on the +y side.  Returns (frame, fins, tubes, headers)."""
    zc0, zc1 = ZB1 + 30.0, ZT0 - 12.0
    fins = box(TR0 + 1.0, TR1 - 1.0, -HW + 6.0, HW - 6.0, zc0 + 8.0, zc1 - 8.0)
    # suggest the fins with shallow grooves on the outer face so the coil reads as finned at any distance
    gro = Part()
    n = int((2 * HW - 12.0) / 6.0)
    for k in range(n):
        y = -HW + 6.0 + 3.0 + k * 6.0
        gro += box(TR1 - 2.2, TR1 - 0.9, y - 0.4, y + 0.4, zc0 + 9.0, zc1 - 9.0)
    fins = fins - gro
    sheet = box(TR0, TR1, -HW - 1.2, -HW + 6.0, zc0, zc1) + box(TR0, TR1, HW - 6.0, HW + 1.2, zc0, zc1)
    sheet += box(TR0, TR1, -HW - 1.2, HW + 1.2, zc0, zc0 + 8.0) + box(TR0, TR1, -HW - 1.2, HW + 1.2, zc1 - 8.0, zc1)
    # return bends (visible "tracing") on both tube sheets: rows at x = TR0 + 11, 33, 55; passes every 25.4 mm
    tubes = Part()
    od = P["trace_tube_od_in"] * 25.4
    rows_x = [TR0 + 11.0, TR0 + 33.0, TR0 + 55.0]
    nz = P["trace_passes"]
    zz0 = zc0 + 8.0 + 12.7
    for r, x in enumerate(rows_x):
        for k in range(nz):
            z = zz0 + k * 25.4 + (12.7 if r == 1 else 0.0)
            if z > zc1 - 20:
                continue
            # tube stubs through each sheet
            tubes += cyl_y(x, -HW - 6.0, -HW + 6.0, z, od) + cyl_y(x, HW - 6.0, HW + 6.0, z, od)
        for k in range(nz - 1):
            z = zz0 + k * 25.4 + (12.7 if r == 1 else 0.0)
            if z + 25.4 > zc1 - 20:
                continue
            side = -1 if k % 2 == 0 else 1
            yb = side * (HW + 6.0)
            t = Rot(0, 90, 0) * Torus(12.7, od / 2)
            half = t - Pos(0, -side * 20.0, 0) * Box(40, 40, 40)
            tubes += Pos(x, yb, z + 12.7) * half
    hdr = Part()
    for k, (z0h, z1h) in enumerate([(zc0 + 10, (zc0 + zc1) / 2 - 10), ((zc0 + zc1) / 2 + 10, zc1 - 10)]):
        hdr += cyl_z(TR0 + 18.0, HW + 18.0, z0h, z1h, 22.2) + cyl_z(TR0 + 48.0, HW + 18.0, z0h, z1h, 22.2)
    return sheet, fins, tubes, hdr


def drip_tray():
    """TS2B-221 drip tray 304 SS 1.0 mm, 15 mm deep, 1:50 fall to a 12 mm drain spud at the low corner"""
    z0 = ZB1 + 2.0
    t = box(TR0 - 6.0, TR1 + 6.0, -HW - 4.0, HW + 4.0, z0, z0 + 15.0)
    t = t - box(TR0 - 5.0, TR1 + 5.0, -HW - 3.0, HW + 3.0, z0 + 1.0, z0 + 15.1)
    return t + cyl_z(TR0 + 20.0, 0.0, z0 - 10.0, z0 + 1.0, 12.0)


def filter_frame():
    """TS2B-222 MERV 8 pleated filter, custom 200 x 905 x 12 (bought to size) in an extruded U frame"""
    z0, z1 = ZB1 + 26.0, ZT0 - 8.0
    f = box(TR1, TR1 + 12.0, -HW, HW, z0, z1) - box(TR1 + 2.0, TR1 + 12.1, -HW + 4.0, HW - 4.0, z0 + 4.0, z1 - 4.0)
    media = Part()
    for k in range(int((2 * HW - 10) / 7.0)):
        y = -HW + 6.0 + k * 7.0
        media += box(TR1 + 2.0, TR1 + 11.0, y, y + 0.6, z0 + 4.0, z1 - 4.0)
    return f, media


def grille_segment(seg, nseg=4):
    """TS2B-223 intake grille segment, printed PETG, 12 mm deep, serpentine louvres (concept FIG. 5 airflow
    guides) at 55 % open area; 4 segments per column fit the 256 mm Bambu plate on edge."""
    z0, z1 = ZB1 + 20.0, ZT0 - 4.0
    h = (z1 - z0) / nseg
    za, zb = z0 + seg * h + 0.5, z0 + (seg + 1) * h - 0.5
    g = box(TR1 + 12.0, TR1 + 24.0, -HW - 2.0, HW + 2.0, za, zb)
    n = int((zb - za - 16.0) / 9.0)
    for k in range(n):
        z = za + 10.0 + k * 9.0
        g = g - round_y(box(TR1 + 11.9, TR1 + 24.1, -HW + 12.0, HW - 12.0, z, z + 5.0), 2.4)
    g = round_x(g, 3.0)
    return g


# ---------------------------------------------------------------- plenum, plinth, crown (tower frame)
def plenum_corner(c):
    """TS2B-301 plenum corner panel, 5052 1.5 mm L, closes the plenum square between two columns"""
    a = box(RP, RP + 1.5, HW + 1.5, RP + 1.5, ZB1, ZT0) + box(HW + 1.5, RP + 1.5, RP, RP + 1.5, ZB1, ZT0)
    return Rot(0, 0, 90 * c) * a


def plinth_arm():
    """TS2B-501 plinth arm weldment, S355 3 mm sheet + 8 mm deck, powder coat RAL 9005 textured.
    Column frame (x radial).  Nose has 4 CRPS bays and the cord grommet; sides carry 2 louvre fields."""
    z0, z1 = P["Z_PLINTH0"], P["Z_DECK"]
    x0, x1 = P["ARM_R0"] - 40.0, P["ARM_R1"]
    w = P["ARM_HALF_W"]
    shell = box(x0, x1, -w, w, z0, z1 - 8.0) - box(x0 - 0.1, x1 - 3.0, -w + 3.0, w - 3.0, z0 + 3.0, z1 - 7.9)
    deck = box(x0, x1, -w, w, z1 - 8.0, z1)
    # deck openings: MCIO/busbar pass under the column base plate, hub-side air, TEC coolant
    deck = deck - round_z(box(240.0, 450.0, -98.0, -66.5, z1 - 8.1, z1 + 0.1), 4.0)
    deck = deck - round_z(box(470.0, 512.0, -96.0, -68.0, z1 - 8.1, z1 + 0.1), 4.0)
    for xp in (RP + 60.0, P["R_OUT"] - 40.0):
        for yp in (-50.0, 50.0):
            deck = deck - cyl_z(xp, yp, z1 - 8.1, z1 + 0.1, 8.5)
    for sgn in (-1, 1):          # TEC module exhaust into the arm (under TS2B-601 floor openings)
        deck = deck - box(700.0, 860.0, min(sgn * 46.0, sgn * 112.0), max(sgn * 46.0, sgn * 112.0), z1 - 8.1, z1 + 0.1)
    for xx in (675.0, 885.0):    # TS2B-601 M5 tapped
        for yy in (-105.0, 105.0):
            deck = deck - cyl_z(xx, yy, z1 - 8.1, z1 + 0.1, 4.2)
    # nose: 4 CRPS bays 56 x 42
    for k in range(4):
        y = -112.0 + k * 58.0
        shell = shell - box(x1 - 3.1, x1 + 0.1, y, y + 56.0, z0 + 40.0, z0 + 82.0)
    # louvres on both sides
    for sgn in (-1, 1):
        for k in range(10):
            x = x0 + 40 + k * 26.0
            shell = shell - box(x, x + 14.0, sgn * w - 3.1 if sgn > 0 else -w - 0.1, sgn * w + 0.1 if sgn > 0 else -w + 3.1, z0 + 160, z0 + 260)
    arm = shell + deck
    return round_x(arm, 6.0) if False else arm


def plinth_hub():
    """TS2B-502 plinth hub, S355 3 mm octagon weldment, deck open to the plenum through a 380 x 380 grille"""
    z0, z1 = P["Z_PLINTH0"], P["Z_DECK"]
    r = P["HUB_R"]
    oct_ = Pos(0, 0, z0) * extrude(RegularPolygon(r / math.cos(math.pi / 8), 8, rotation=22.5), z1 - z0)
    inner = Pos(0, 0, z0 + 3) * extrude(RegularPolygon(r / math.cos(math.pi / 8) - 3, 8, rotation=22.5), z1 - z0 - 11)
    h = oct_ - inner
    h = h - box(-190, 190, -190, 190, z1 - 8.1, z1 + 0.1)
    bars = Part()
    for k in range(-8, 9):
        bars += box(k * 22.0 - 2.0, k * 22.0 + 2.0, -190, 190, z1 - 8.0, z1)
    return h + bars


def caster(x, y):
    """bought: leveling caster, 100 x 100 plate, 300 kg (e.g. Fallshaw/ Jergens class), 95 mm to plate"""
    z1 = P["Z_PLINTH0"]
    plate = box(x - 50, x + 50, y - 50, y + 50, z1 - 6, z1)
    fork = box(x - 25, x + 25, y - 20, y + 20, z1 - 40, z1 - 6)
    wheel = Pos(x, y, 38) * (Rot(90, 0, 0) * Cylinder(38, 32, align=CEN))
    pad = cyl_z(x + 55, y, 0, 12, 60) + cyl_z(x + 55, y, 12, z1 - 6, 16)
    return plate + fork + wheel + pad


def host_node():
    """bought envelopes in the arm: ROMED8-2T (305 x 244), EPYC + XE04-SP3B cooler, 8 RDIMM, 4x Rocket 1628A
    (LP 155 x 68.9) and a ConnectX-6 Dx, mounted on 10 mm standoffs on a 2 mm tray."""
    zb = P["Z_PLINTH0"] + 3.0 + 10.0
    tray = box(215.0, 530.0, -130.0, 130.0, zb - 12.0, zb - 10.0)
    board = box(220.0, 525.0, -122.0, 122.0, zb, zb + 1.6)
    cooler = box(330.0, 440.0, -60.0, 50.0, zb + 1.6, zb + 1.6 + 126.0)
    dimms = Part()
    for k in range(8):
        dimms += box(300.0 + (k % 4) * 8.0 + (0 if k < 4 else 160.0), 301.4 + (k % 4) * 8.0 + (0 if k < 4 else 160.0), -110.0, 23.0, zb + 1.6, zb + 33.0)
    cards = Part()
    for k in range(5):
        x = 245.0 + k * 40.64
        cards += box(x, x + 1.6, -120.0, 35.0, zb + 8.0, zb + 8.0 + 68.9) + box(x + 1.6, x + 14.0, -110.0, 25.0, zb + 12.0, zb + 70.0)
    return tray, board, cooler, dimms, cards


def crps(k):
    """bought: Murata D1U54T-W-2000-12-HC4TC, 54.5 x 40 x 321.3 mm, output edge toward the hub"""
    y = -112.0 + k * 58.0 + 0.75
    x1 = P["ARM_R1"] - 3.0
    body = box(x1 - 321.3, x1, y, y + 54.5, P["Z_PLINTH0"] + 41.0, P["Z_PLINTH0"] + 81.0)
    handle = box(x1, x1 + 12.0, y + 8, y + 46, P["Z_PLINTH0"] + 52.0, P["Z_PLINTH0"] + 70.0) - box(x1 + 2, x1 + 10.0, y + 12, y + 42, P["Z_PLINTH0"] + 51.9, P["Z_PLINTH0"] + 70.1)
    fan = cyl_x(x1 - 0.5, x1 + 0.6, y + 27.0, P["Z_PLINTH0"] + 61.0, 36.0)
    return body + handle, fan


def cpd_board():
    """CPD-1 column power distribution board envelope (KiCad outline), vertical at x 560"""
    x = P["ARM_R1"] - 3.0 - 321.3 - 4.0
    return box(x - 2.4, x, -125.0, 125.0, P["Z_PLINTH0"] + 20.0, P["Z_PLINTH0"] + 115.0)


def tec_module():
    """TS2B-601 base thermal module (Peltier trim) on the arm deck: 304 SS housing, 4 TECs (40 x 40, TEC1-12715 class,
    15 A max, run at 14 A by TCD-1) in a row on the split copper cold block in the coolant line, one 8 mm copper hot-side
    spreader with 8 heat pipes into two fin stacks, two 120 mm fans blowing down through the fins and the deck into the
    arm (air leaves through the hub into the plenum).  D5 pump, RSP-750-12 and TCD-1 sit beside it in the arm."""
    x0, x1 = 660.0, 900.0
    z0 = P["Z_DECK"]
    hous = box(x0, x1, -120.0, 120.0, z0, z0 + 170.0) - box(x0 + 2.0, x1 - 2.0, -118.0, 118.0, z0 + 2.0, z0 + 168.1)
    hous = hous - box(x0 + 30.0, x1 - 30.0, -110.0, 110.0, z0 + 167.9, z0 + 170.1)          # fan opening (top)
    for sgn in (-1, 1):                                                                       # exhaust openings (floor)
        hous = hous - box(x0 + 40.0, x1 - 40.0, min(sgn * 46.0, sgn * 112.0), max(sgn * 46.0, sgn * 112.0), z0 - 0.1, z0 + 2.1)
    for xx in (x0 + 15.0, x1 - 15.0):                                                         # 4x M5 to the deck
        for yy in (-105.0, 105.0):
            hous = hous - cyl_z(xx, yy, z0 - 0.1, z0 + 2.1, 5.5)
    for yy in (-15.0, 15.0):                                                                  # coolant tube grommets (-x wall)
        hous = hous - cyl_x(x0 - 0.1, x0 + 2.1, yy, z0 + 35.0, 16.5)
    hous = hous - box(x1 - 2.1, x1 + 0.1, -60.0, -20.0, z0 + 20.0, z0 + 40.0)                   # TEC / fan harness pass
    cold = cold_block()
    tecs = Part()
    for k in range(4):
        xt = x0 + 32.0 + k * 44.0
        tecs += box(xt, xt + 40.0, -20.0, 20.0, z0 + 50.0, z0 + 53.8)
    towers = box(x0 + 30.0, x1 - 30.0, -112.0, 112.0, z0 + 54.0, z0 + 62.0)                   # hot-side spreader 8 mm Cu
    for xx in (x0 + 74.0, x0 + 118.0, x0 + 162.0):
        for yy in (-30.0, 30.0):
            towers = towers - cyl_z(xx, yy, z0 + 53.9, z0 + 62.1, 4.5)
    for sgn in (-1, 1):
        for k in range(18):
            y = (45.0 + k * 3.8) * sgn
            towers += box(x0 + 45.0, x1 - 45.0, min(y, y + 0.5 * sgn), max(y, y + 0.5 * sgn), z0 + 62.0, z0 + 160.0)
        for k in range(4):
            towers += cyl_z(x0 + 70 + k * 33.0, sgn * 76.0, z0 + 62.0, z0 + 165.0, 6.0)
    fans = Part()
    for sgn in (-1, 1):
        fx = (x0 + x1) / 2
        f = box(fx - 60, fx + 60, sgn * 76 - 60, sgn * 76 + 60, z0 + 166.0, z0 + 191.0) - cyl_z(fx, sgn * 76, z0 + 165.9, z0 + 191.1, 112.0)
        hub = cyl_z(fx, sgn * 76, z0 + 170.0, z0 + 188.0, 40.0)
        bl = Part()
        for k in range(7):
            a = k * 360 / 7
            bl += Pos(fx, sgn * 76, z0 + 179.0) * (Rot(0, 0, a) * (Pos(33, 0, 0) * (Rot(25, 0, 0) * Box(34, 14, 1.5))))
        fans += f + hub + bl
    return hous, cold, tecs, towers, fans


def cold_block():
    """TS2B-602 TEC cold block, C11000 30 x 80 x 180, electroless nickel.  Coolant U-path: two 8 mm gun-drilled
    passages from the -x face (y -15 / +15, z mid-height, 165 deep) joined by an 8 mm cross-drill from the -y face
    at x 160 that is closed with a G1/8 plug; G1/4 ports (11.8 tap drill x 12) on the -x face for the 3/8 in barbs.
    TEC face flat within 0.025, Ra 0.8.  6x M4 (3.3 x 10) clamp screws between the TECs, through the spreader."""
    x0 = 660.0
    z0 = P["Z_DECK"]
    xa, xb = x0 + 30.0, x0 + 210.0
    c = box(xa, xb, -40.0, 40.0, z0 + 20.0, z0 + 50.0)
    zc = z0 + 35.0
    for yy in (-15.0, 15.0):
        c = c - cyl_x(xa - 0.1, xa + 165.0, yy, zc, 8.0) - cyl_x(xa - 0.1, xa + 12.0, yy, zc, 11.8)
    c = c - cyl_y(xa + 160.0, -40.1, 15.0, zc, 8.0) - cyl_y(xa + 160.0, -40.1, -32.0, zc, 8.8)
    for xx in (x0 + 74.0, x0 + 118.0, x0 + 162.0):
        for yy in (-30.0, 30.0):
            c = c - cyl_z(xx, yy, z0 + 40.0, z0 + 50.1, 3.3)
    for xx in (xa + 15.0, xb - 15.0):                         # 2x M5 (4.2 x 10) from below into the housing floor stand-offs
        c = c - cyl_z(xx, 0.0, z0 + 19.9, z0 + 30.0, 4.2)
    return c


def crown_parts():
    """TS2B-401..404 crown: 8 mm base ring with the plenum opening, 2 mm octagon shell with the red band,
    5 mm fan deck with 3 inlet rings, top plate with the 18 in chimney collar."""
    ap = 430.0
    R = ap / math.cos(math.pi / 8)
    z0 = P["Z_CROWN0"]
    z1 = P["Z_CROWN1"]
    base = Pos(0, 0, z0) * extrude(RegularPolygon(R, 8, rotation=22.5), 8.0) - box(-200, 200, -200, 200, z0 - 0.1, z0 + 8.1)
    for c in range(4):
        for xp in (RP + 40.0, RP + 160.0):
            a = math.radians(90 * c)
            base = base - cyl_z(xp * math.cos(a), xp * math.sin(a), z0 - 0.1, z0 + 8.1, 9.0)
    shell = Pos(0, 0, z0 + 8.0) * extrude(RegularPolygon(R, 8, rotation=22.5), z1 - z0 - 13.0) - \
        Pos(0, 0, z0 + 7.9) * extrude(RegularPolygon(R - 2.2, 8, rotation=22.5), z1 - z0 - 12.8)
    band = Pos(0, 0, z0 + 90.0) * extrude(RegularPolygon(R + 2.0, 8, rotation=22.5), 26.0) - \
        Pos(0, 0, z0 + 89.9) * extrude(RegularPolygon(R - 0.1, 8, rotation=22.5), 26.2)
    deck_z = z0 + 110.0
    deck = Pos(0, 0, deck_z) * extrude(RegularPolygon(R - 2.3, 8, rotation=22.5), 5.0)
    imp = []
    for k in range(3):
        a = math.radians(90 + 120 * k)
        x, y = 205.0 * math.cos(a), 205.0 * math.sin(a)
        deck = deck - cyl_z(x, y, deck_z - 0.1, deck_z + 5.1, 232.0)
        imp.append((x, y))
    top = Pos(0, 0, z1 - 5.0) * extrude(RegularPolygon(R, 8, rotation=22.5), 5.0) - cyl_z(0, 0, z1 - 5.1, z1 + 0.1, P["CHIMNEY_D"] - 2)
    collar = cyl_z(0, 0, z1, z1 + 80.0, P["CHIMNEY_D"] + 3.0) - cyl_z(0, 0, z1 - 0.1, z1 + 80.1, P["CHIMNEY_D"] - 2.0)
    return dict(base=base, shell=shell, band=band, deck=deck, top=top + collar, impellers=imp, deck_z=deck_z)


def impeller(x, y, z):
    """bought: ebm-papst R3G310-AN12-30 (48 VDC EC, 310 mm, 4.4 kg) + inlet ring 31050-2-4013"""
    ring = cyl_z(x, y, z, z + 22.0, 270.0) - cyl_z(x, y, z - 0.1, z + 22.1, 226.0)
    disc = cyl_z(x, y, z + 30.0, z + 34.0, 310.0) - cyl_z(x, y, z + 29.9, z + 34.1, 228.0)
    back = cyl_z(x, y, z + 92.0, z + 96.0, 310.0)
    motor = cyl_z(x, y, z + 96.0, z + 150.0, 140.0)
    blades = Part()
    for k in range(6):
        a = k * 60.0
        blades += Pos(x, y, z + 34.0) * (Rot(0, 0, a) * (Pos(122.0, 0, 0) * (Rot(0, 0, 38) * Box(70.0, 2.5, 58.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))))
    return ring, disc + back + blades, motor


def backdraft_flap(x, y, z):
    """TS2B-405 gravity backdraft flap pair, 0.8 mm 5052 on a piano hinge, under each inlet ring: a stopped
    impeller can no longer short-circuit the running ones (rev A AC-THM-06 finding)."""
    return box(x - 113, x - 1, y - 113, y + 113, z - 3.0, z - 2.2) + box(x + 1, x + 113, y - 113, y + 113, z - 3.0, z - 2.2)


def chimney():
    """bought: 18 in (457 mm) 26 ga galvanised spiral duct, flanged to the crown collar"""
    z0, z1 = P["Z_CROWN1"] + 80.0, P["Z_CHIMNEY1"]
    d = P["CHIMNEY_D"]
    t = cyl_z(0, 0, z0, z1, d + 1.0) - cyl_z(0, 0, z0 - 0.1, z1 + 0.1, d - 1.0)
    for k in range(int((z1 - z0) / 140.0)):
        t += Pos(0, 0, z0 + 70.0 + k * 140.0) * Torus(d / 2 + 0.5, 1.6)
    return t


def panel_console():
    """TS2B-701 operator console on the C3 arm nose: Raspberry Pi Touch Display 2 (7 in), Pi 5, TPM, in a
    printed ASA bezel on a 40 x 40 post"""
    x = P["ARM_R1"] - 30.0
    z0 = P["Z_DECK"]
    postp = box(x - 20, x + 20, -20, 20, z0, z0 + 760.0)
    head = Pos(x + 18, 0, z0 + 860.0) * (Rot(0, -15, 0) * Box(40.0, 210.0, 140.0))
    screen = Pos(x + 39, 0, z0 + 860.0 + 5.0) * (Rot(0, -15, 0) * Box(1.5, 180.0, 110.0))
    return postp, head, screen


# ---------------------------------------------------------------- MADE: CPD-1 power straps (flat, cut from 6 mm C11000)
CPD_BX = [41.0 + 58.0 * k + d for k in range(4) for d in (-13.0, 13.0)]    # stud x on the board (CPD-1 design.py)
CPD_P12_BY, CPD_RTN_BY = 65.0, 81.0
STRAP_T = 6.0
LUG_PITCH = 44.45                    # NEMA 2-hole lug, 1.75 in


def cpd_frame():
    """(x of the B face, board-x -> tower y, board-y -> tower z) for the CPD-1 board in the arm"""
    xb = P["ARM_R1"] - 3.0 - 321.3 - 4.0 - 2.4
    return xb, (lambda bx: bx - 125.0), (lambda by: P["Z_PLINTH0"] + 20.0 + by)


def _flat(xb, rects, holes):
    """union of (bx0, bx1, by0, by1) rectangles in the strap plane minus (bx, by, d) holes; board frame -> tower"""
    _, ty, tz = cpd_frame()
    s = Part()
    for bx0, bx1, by0, by1 in rects:
        s += box(xb - STRAP_T, xb, ty(bx0), ty(bx1), tz(by0), tz(by1))
    s = round_x(s, 2.0)
    for bx, by, d in holes:
        s = s - cyl_x(xb - STRAP_T - 0.1, xb + 0.1, ty(bx), tz(by), d)
    return s


def strap_p12():
    """TS2B-232 +12 V strap, C11000 6 mm plate, waterjet/laser cut, deburred, bright tin 5-8 um.  A 12 mm bar over the
    eight +12 V studs (6.6 thru, M6 nut + Belleville, 6 N m) with a tab at each end that rises past the board top edge
    to a 38 x 70 lug paddle: 2x 8.5 thru at 44.45 (1.75 in) for one 4/0 two-hole lug per end (harness C01 L1 / L2).
    Each end carries half the column current (200 A in 12 x 6 = 2.8 A/mm2)."""
    xb, _, _ = cpd_frame()
    y0, y1 = CPD_P12_BY - 6.0, CPD_P12_BY + 6.0
    rects = [(6.0, 250.0, y0, y1),                           # bar
             (6.0, 18.0, y0, 175.0), (238.0, 250.0, y0, 175.0),   # rising tabs, 4 mm clear of the RTN bar ends
             (-20.0, 18.0, 105.0, 175.0), (238.0, 276.0, 105.0, 175.0)]   # lug paddles above the board edge (95)
    holes = [(bx, CPD_P12_BY, 6.6) for bx in CPD_BX]
    for bx in (-1.0, 257.0):
        holes += [(bx, 117.5, 8.5), (bx, 117.5 + LUG_PITCH, 8.5)]
    return _flat(xb, rects, holes)


def strap_rtn():
    """TS2B-233 RTN strap, C11000 6 mm plate, cut, bright tin.  Bar over the eight RTN studs with one centre tab
    (20 mm neck between studs 4 and 5: 400 A in 120 mm2) rising to an 80 x 70 paddle that takes both 4/0 two-hole lugs
    side by side (harness C02 L1 / L2)."""
    xb, _, _ = cpd_frame()
    y0, y1 = CPD_RTN_BY - 6.0, CPD_RTN_BY + 6.0
    rects = [(22.0, 234.0, y0, y1), (115.0, 135.0, y0, 110.0), (85.0, 165.0, 105.0, 175.0)]
    holes = [(bx, CPD_RTN_BY, 6.6) for bx in CPD_BX]
    for bx in (105.0, 145.0):
        holes += [(bx, 117.5, 8.5), (bx, 117.5 + LUG_PITCH, 8.5)]
    return _flat(xb, rects, holes)
