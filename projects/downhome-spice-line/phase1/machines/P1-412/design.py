"""P1-412 bench spindle capper rev B: every engineered number (mm unless noted).
Frame: z up, z = 0 on the bench top (table TBL-1, 914 AFF); container axis at x 0, y 0; column behind at +y; operator at -y.

How it works: the operator stands the filled container in the V-nest and closes the toggle clamp (left hand), then pulls the lever (right hand).
The lever pulls the carriage down an MGN15 rail on the column; the spinning chuck lands on the loosely placed cap, a spring in the chuck
gives 12 mm of float, and the cap is driven down until the slip clutch slips at the set torque. Releasing the lever lets the gas spring lift
the carriage; at the top a limit switch inhibits the motor. A stop screw sets the lowest carriage position for each container height.

Sub-assemblies: 100 base weldment (base plate, column, gussets, top cap, rail seat bar), 200 carriage weldment (machined after welding),
300 spindle parts (stub shaft, chuck adapter, chuck guard), 400 nest and clamp (nest plate, V-block, clamp pad, toggle bracket),
500 lever, link and stop. Bought: gearmotor + speed control P1-422, clutch + chuck inserts P1-423, rail + gas spring P1-424, kit P1-428..P1-433."""
import math

IN = 25.4
# ---- plant interface
Z_BENCH = 914.0                       # TBL-1 top AFF
CONT = {                              # container on the nest (matches machines/P1-401 design.py), cap height above the rim
    "shaker-250": dict(d=66.0, h=109.2, cap_d=53.0, cap_h=16.0, T=1.6, T_lbin=14.0, nest="S"),
    "jar-12": dict(d=86.4, h=154.9, cap_d=89.0, cap_h=19.0, T=2.5, T_lbin=22.0, nest="J"),
}
# ---- base weldment 100 (304)
BASE = dict(w=400.0, d=350.0, t=12.0, y0=-175.0, hole=9.0, hx=170.0, hy=145.0)      # 4 x Ø9 for M8 to the bench at (±170, ±145)
COL = dict(a=50.8, t=3.05, y=125.0, L=650.0)                                         # 2 in sq x 11 ga, axis at y 125, z 12..662
Z_COL0 = BASE["t"]
Z_COL1 = Z_COL0 + COL["L"]            # 662
GUS = dict(t=6.0, a=90.0)             # 2 gussets 90 x 90 x 6 on the column sides
CAPPL = dict(x0=-35.0, x1=100.0, y0=90.0, y1=160.0, t=6.0)   # top cap 135 x 70 x 6, z 662..668, carries the lever clevis on the +x side
Z_CAP = Z_COL1 + CAPPL["t"]           # 668
RSB = dict(w=30.0, t=10.0, z0=110.0, L=520.0)        # rail seat bar 30 x 10 x 520, welded to the column front, faced flat 0.05 after welding
Y_COLF = COL["y"] - COL["a"] / 2      # 99.6 column front face
Y_RSB = Y_COLF - RSB["t"]             # 89.6 rail seat face (machined)
# ---- MGN15 rail and block (HIWIN, bought P1-424)
RAIL = dict(w=15.0, h=10.0, L=500.0, z0=120.0, pitch=40.0, e=20.0, bolt="M3 x 16")    # rail z 120..620
BLK = dict(H=16.0, W=32.0, L=58.8, B=25.0, C=25.0, bolt="M3")                          # MGN15H block: total height 16 rail bottom to block top
Y_BLK = Y_RSB - BLK["H"]              # 73.6 block mounting face
# ---- carriage weldment 200 (304, machined after welding)
CAR = dict(w=120.0, h=170.0, t=10.0, sh_x0=-100.0, sh_x1=100.0, sh_t=10.0, gus=60.0, lug_x=82.0, lug_y=10.0, lug_h=30.0)
# vertical plate x ±60, y Y_BLK-10..Y_BLK, z shelf..shelf+170; motor shelf under it, x -75..100 (lug side), y -75..Y_BLK; link lug on the shelf at x 82
SHELF_Y0 = -100.0
MOTOR_BORE = 30.0                     # gearmotor pilot Ø29.97 [1.180 in] (confirm), shaft down through the shelf
# ---- drive line (bought): gearmotor on the shelf, shaft down; clutch, stub shaft 301, chuck adapter 302, urethane insert
GM = dict(hp=0.125, rpm=190.0, T=4.4, shaft=12.7, body_d=80.0, body_h=230.0, flange=4, pcd=60.0, bolt="10-32", V=130.0, A=1.1)   # Bodine 42A-E class PMDC
CLU = dict(d=50.0, L=60.0, bore=12.7, Tmin=0.5, Tmax=5.0, name="Zero-Max Torq-Tender TT1 class")                                     # slip clutch
STUB = dict(d=12.7, L=70.0, collar_d=22.0, collar_t=6.0, spig_d=16.0, spig_L=30.0)
CHK = dict(d=112.0, h=46.0, float_=12.0, spring_k=3.0)                                                                            # chuck adapter 302 + insert, 12 float
INSERT = {"S": dict(id_top=50.0, id_bot=56.0, depth=14.0), "J": dict(id_top=86.0, id_bot=92.0, depth=16.0)}                       # urethane cone inserts
# stack below the shelf underside: clutch 60, stub collar 6, chuck 46 (float out) -> chuck face 112 below the shelf underside
STACK = CLU["L"] + STUB["collar_t"] + CHK["h"]
# ---- carriage travel
NEST_T = 8.0                          # UHMW nest plate on the base: container stands at z 20
Z_STAND = BASE["t"] + NEST_T          # 20
CLR_UP = 40.0                         # chuck face above the tallest capped container with the carriage up
Z_CHK_UP = Z_STAND + CONT["jar-12"]["h"] + CONT["jar-12"]["cap_h"] + CLR_UP        # 234 chuck face, carriage up
Z_SHELF_UP = 350.0                    # shelf underside, carriage up = gas spring at full extension (z_lo 20 + 330)
Z_CHK_UP = Z_SHELF_UP - STACK          # 238 chuck face, carriage up (44 above a capped jar)
def z_shelf_down(k):                  # chuck face 6 below the cap top (insert grips the skirt, spring 6 compressed) -> stop setting
    c = CONT[k]
    return Z_STAND + c["h"] + c["cap_h"] - 6.0 + STACK
STROKE_MAX = Z_SHELF_UP - z_shelf_down("shaker-250")
# ---- lever, link, gas spring, stop (500)
PIV = dict(x=82.0, y=COL["y"] - 10.0, z=Z_CAP + 32.0)   # lever pivot on the clevis plate on the cap (+x side, clear of the motor), Ø10 shoulder bolt
CLEV = dict(t=8.0, x=92.0, y0=90.0, y1=150.0, h=52.0)   # clevis plate x 92..100 (lever at x 77..87, 5 gap = nylon washer)
LEV = dict(a=110.0, L=400.0, w=25.0, t=10.0, knob=40.0, x=82.0)   # flat bar 25 x 10 at x 77..87; link pin 110 from the pivot, handle 400 from the pivot
GAS = dict(F=200.0, stroke=120.0, L_ext=330.0, x=-90.0, y=50.0, z_lo=20.0, name="Stabilus LIFT-O-MAT 200 N, 330 / 120 stroke")   # eye to eye
STOP = dict(d=16.0, thread="M16 x 1.5", x=85.0, y=62.0, flip_t=48.7)   # stop rod Ø16 screwed into the base (jam nut), top at the shaker stop; flip block adds 48.7 for jars
# ---- nest and clamp (400)
VB = dict(L=100.0, h=60.0, t=60.0, depth=40.0, angle=90.0, mat="UHMW-PE natural")   # V-block on the +x side, slides on 2 slots, 2 pin positions S/J
def v_offset(d):                      # V apex to container centre for a 90 deg V
    return d / 2 / math.sin(math.radians(VB["angle"] / 2))
def vb_face(d):                       # V-block front face x for container d centred on the axis (apex is 40 behind the face)
    return v_offset(d) - VB["depth"]
VB_BOLT_DX = 45.0                     # 2 x M8 at (face + 45, ±35) per setting S / J
Z_LUGPIN = 30.0                      # link pin above the shelf underside
LINK = dict(d=10.0, rod_end="M8 female rod end (igus KBRM-08)", L=PIV["z"] - ((Z_SHELF_UP + z_shelf_down("shaker-250")) / 2 + Z_LUGPIN))   # lever horizontal at mid-stroke
TH0 = math.degrees(math.asin(STROKE_MAX / 2 / LEV["a"]))      # lever swing ± from horizontal
TGL = dict(name="De-Sta-Co 603-M push-pull", F_hold=1360.0, stroke=32.0)    # push-pull toggle clamp on the -x side, V pad
PAD = dict(w=60.0, h=40.0, t=20.0)
# ---- guard (300): clear polycarbonate shroud around the chuck, fixed to the shelf
GUARD = dict(d=150.0, h=100.0, t=3.0, r_bolt=85.0)
# ---- electrics (120 V, cord and plug)
ELE = dict(V=120.0, f=60.0, A=1.4, fuse=3.0)


def calcs():
    c = {}
    w_carr = 2.6 + 3.6 + 0.8 + 0.6 + 0.4          # carriage weldment, gearmotor, clutch, chuck + stub, guard (kg); refined by masses.json
    c["w_carr"] = w_carr
    c["W"] = w_carr * 9.81
    c["F_gas_net"] = GAS["F"] - c["W"]               # net up force with the lever released
    c["F_hand"] = (c["F_gas_net"] + 40.0) * LEV["a"] / LEV["L"]   # hand force to pull down against the spring + 40 N chuck spring at full float
    c["ang"] = math.degrees(math.asin(min(1.0, STROKE_MAX / 2 / LEV["a"]))) * 2
    for k, v in CONT.items():
        T = v["T"]
        c[k] = dict(F_t=T / (v["d"] / 2000), F_clamp=T / (v["d"] / 2000) / (2 * 0.5) * 1.5,   # 2 contact lines, mu 0.5 urethane-PP, SF 1.5
                    z_down=z_shelf_down(k), stroke=Z_SHELF_UP - z_shelf_down(k), v_off=v_offset(v["d"]),
                    t_cap=(360 * 1.5 / 360) / (GM["rpm"] / 60))     # about 1.5 turns of thread
    c["P_motor"] = GM["T"] * GM["rpm"] * 2 * math.pi / 60
    c["T_ratio"] = GM["T"] / CLU["Tmax"]
    c["stroke"] = STROKE_MAX
    c["z_up"] = Z_SHELF_UP
    return c


if __name__ == "__main__":
    for k, v in calcs().items():
        print(k, v)
