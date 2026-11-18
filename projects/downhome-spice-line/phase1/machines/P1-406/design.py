"""P1-406 metal detector conveyor rev B: every engineered number (mm unless noted).
Frame: z up, z = 0 on the floor; x along the flow (infeed at -x, outfeed at +x); y across (operator at -y); head centre at x 0, belt centre y 0.

How it works: closed, labelled packs from the labeler are set on the 6 in belt at the infeed and pass through the bought search head P1-418 (CCP-1).
Inside the metal-free zone (MFZ) the belt runs on a UHMW bed carried by two FRP rails: no metal within 1.5 x the aperture height of the head faces
(2 x for moving metal). The steel end frames, legs, pulleys and drive all sit outside the MFZ. On a detect the PLC tracks the pack to the reject
station, stops the belt, the electric pusher P1-421 pushes it into the locked bin, and a bin-entry eye confirms the reject; anything else stops the belt.

Sub-assemblies: 100 frame (2 end frames, legs, spine, head stand), 200 belt run (pulleys, take-up, FRP rails, UHMW bed, guides),
300 reject (pusher bracket, paddle, locked bin, sensor brackets), 400 drive and controls (motor torque arm, box bracket, beacon pole).
Bought: head P1-418, belt + bearings P1-419, gearmotor P1-420, pusher P1-421, kits P1-459..462."""
import math

IN = 25.4
# ---- plant interface
Z_BELT = 905.0                       # belt top, level with the bench tables (914) less 9 for the push-across
CONT = {                             # matches machines/P1-401 / P1-404 design.py
    "shaker-250": dict(d=66.0, h=109.2, setting="S"),
    "jar-12": dict(d=86.4, h=154.9, setting="J"),
}
RATE = 14.0                          # packs / min from the labeler (one operator)
# ---- belt and pulleys
BELT = dict(w=152.4, t=2.0, mat="PU 2 mm FDA, white, finger-spliced in place (it threads through the closed head)", speed=None)
PUL = dict(d=60.0, crown=0.5, face=175.0, shaft=20.0, x=710.0, brg="UCFL204 SS (Ø20, 4-bolt flange)", brg_sq=86.0, brg_bolt=64.0, brg_t=25.5)
Z_PUL = Z_BELT - BELT["t"] - PUL["d"] / 2      # pulley centre
TAKEUP = 30.0                        # tail pulley slot travel (+-15)
# ---- search head (bought used, confirm every number against the actual head before cutting the head stand)
HEAD = dict(ap_w=300.0, ap_h=250.0, ap_z0=850.0, L=200.0, W=520.0, H=480.0, z0=760.0, lug_y=290.0, lug_z=760.0)
MFZ = dict(static=1.5 * HEAD["ap_h"], moving=2.0 * HEAD["ap_h"])
X_STATIC = HEAD["L"] / 2 + MFZ["static"]      # 475: no static metal inside |x| < this (frame, guides, screws)
X_MOVING = HEAD["L"] / 2 + MFZ["moving"]      # 600: no moving metal inside (pulleys, motor, pusher)
# ---- frame 100: two bolted end frames outside the MFZ, joined low by the spine
SIDE = dict(t=4.0, h=140.0, y_in=100.0, x0=X_STATIC, x1=760.0)   # side plates 4 mm, inner faces y +-100, z 763..903, |x| 475..760
Z_SIDE0, Z_SIDE1 = Z_BELT - BELT["t"] - SIDE["h"], Z_BELT - BELT["t"]
BED_SS = dict(t=3.0)                 # 304 bed on each end frame, top z 903
LEG = dict(sq=40.0, t=2.0, x=690.0, y=124.0, z_foot=60.0, foot="M16 levelling foot Ø80, +-25")
BRACE_Z = 300.0
SPINE = dict(h=80.0, w=40.0, t=3.0, z=BRACE_Z)                    # 80 x 40 x 3 tube along x at y 0
STAND = dict(post=50.0, t=3.0, beam_y=HEAD["lug_y"] + 30.0)        # head stand: cross beam on the spine at x 0, 2 posts to the head lugs
# ---- belt run 200 through the MFZ
FRP = dict(h=38.1, w=19.05, t=3.2, y=80.0, x=535.0)               # FRP rect tube 1-1/2 x 3/4 x 1/8 in on edge, |x| <= 535, clips at 485..535
UBED = dict(t=10.0, w=196.0, x=480.0)                              # UHMW bed, top z 903, |x| <= 480
GUIDE = dict(t=10.0, h=40.0, gap={"S": 66.0 + 10.0, "J": 86.4 + 10.0})   # UHMW guide strips on the end frames only (none in the MFZ)
# ---- reject 300
REJ = dict(x=620.0, stroke=150.0, paddle_w=120.0, paddle_h=80.0, z=Z_BELT + 45.0, speed=38.0)      # PA-14 class 24 V, 38 mm/s at load (confirm)
BIN = dict(x0=530.0, x1=710.0, y0=110.0, y1=370.0, z0=520.0, z1=1030.0, slot_w=150.0, slot_h=120.0, t=1.5)
B1_X, B2_Z = REJ["x"] - 40.0, Z_BELT + 60.0                           # pack-at-reject eye, bin-entry eye
# ---- drive 400
MOTOR = dict(rpm=85.0, hp=0.125, V=115.0, A=2.0, bore=20.0, T=8.5)     # right-angle hollow-shaft gearmotor on the head pulley, -y side
ENC = dict(x0=-790.0, x1=-590.0, y0=-290.0, y1=-160.0, z0=520.0, h=250.0)   # controls box on the infeed -y legs, lid toward the operator
POLE = dict(x=-690.0, y=164.0, h=500.0)                                # beacon pole on the infeed +y leg, light seen from the whole bench
ELE = dict(V=120.0, A=3.5, fuse=6.0, V_dc=24.0, I_dc=3.2)


def calcs():
    c = {}
    v = math.pi * PUL["d"] * MOTOR["rpm"] / 60.0
    c["v"] = v; c["v_mpm"] = v * 60 / 1000
    c["pitch_min"] = v * 60.0 / RATE                     # belt travel per pack at the line rate
    c["t_head"] = (HEAD["L"] + CONT["jar-12"]["d"]) / v  # time in the aperture
    c["t_reject"] = 0.3 + REJ["stroke"] / REJ["speed"] * 2 + 0.5
    c["t_track"] = (REJ["x"] - 0.0) / v                  # head centre to the reject station
    c["L_belt"] = 2 * 2 * PUL["x"] + math.pi * (PUL["d"] + BELT["t"])
    m_pack = 0.6
    n_on = 2 * PUL["x"] / c["pitch_min"] + 1
    c["F_belt"] = n_on * m_pack * 9.81 * 0.3 + 2 * 0.7 * 9.81 * 0.3 + 5.0   # packs + belt on the bed (μ 0.3) + pulley drag
    c["T_pul"] = c["F_belt"] * PUL["d"] / 2000 * 1.5      # with the start factor
    c["P"] = c["T_pul"] * MOTOR["rpm"] * 2 * math.pi / 60
    c["T_motor_ratio"] = MOTOR["T"] / c["T_pul"]
    for k, ct in CONT.items():
        c[k] = dict(top=Z_BELT + ct["h"], clear=HEAD["ap_z0"] + HEAD["ap_h"] - (Z_BELT + ct["h"]),
                    centre_off=(Z_BELT + ct["h"] / 2) - (HEAD["ap_z0"] + HEAD["ap_h"] / 2), guide=GUIDE["gap"][ct["setting"]])
    E = 17000.0; I = (FRP["w"] * FRP["h"] ** 3 - (FRP["w"] - 2 * FRP["t"]) * (FRP["h"] - 2 * FRP["t"]) ** 3) / 12
    span = 2 * 485.0; w = (3 * m_pack * 9.81 + 2.0 + 20.0) / span / 2       # 3 packs + bed + belt over two rails (N/mm)
    c["FRP_defl"] = 5 * w * span ** 4 / (384 * E * I)
    return c


if __name__ == "__main__":
    for k, v in calcs().items():
        print(k, v)
    print("Z_PUL", Z_PUL, "X_STATIC", X_STATIC, "X_MOVING", X_MOVING)
