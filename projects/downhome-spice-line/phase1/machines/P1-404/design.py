"""P1-404 wrap labeler for round containers rev B: every engineered number (mm unless noted).
Frame: z up, z = 0 on the bench top (table TBL-2, 914 AFF); x along the roller axes (drive side at -x); y toward the back (operator at -y);
the container lies on the two drive rollers with its axis along x, label centre at x 0.

How it works: the operator lays the container on the two driven rollers against the end fence and lowers the idler arm onto it.
The arm closes a proximity sensor; one servo-stepper drives both rollers and the liner drive roller through two timing belts, so the
liner (label) speed always equals the container surface speed, whatever the diameter. The label peels off the peel plate tip onto the
top of the container; the silicone idler wipes it down as the container turns. A fork gap sensor stops the drive at the next label gap.

Sub-assemblies: 100 frame (base, 2 side plates, end fence), 200 drive (motor mount, liner drive roller, bearing housings, pulleys, guard),
300 web path (unwind and rewind spindles, guide roller, pinch lever, brake), 400 peel plate and idler arm.
Bought: rollers P1-425, ClearPath + ClearCore P1-426, gap sensor P1-427, kits P1-454..458."""
import math

IN = 25.4
# ---- plant interface
Z_BENCH = 914.0                      # TBL-2 top AFF
CONT = {                             # matches machines/P1-401 and P1-412 design.py; label wraps the body
    "shaker-250": dict(d=66.0, h=109.2, cap_h=16.0, lab_L=190.0, lab_H=80.0, setting="S"),
    "jar-12": dict(d=86.4, h=154.9, cap_h=19.0, lab_L=255.0, lab_H=100.0, setting="J"),
}
LAB = dict(gap=3.0, liner=6.0, core=76.2, od_max=200.0, t=0.15, speed=150.0)        # web: liner 6 wider than the label; 3 in core; 200 OD roll
# ---- frame 100
BASE = dict(w=640.0, d=360.0, t=8.0, y0=-180.0, hole=7.0, hx=290.0, hy=150.0)       # 4 x Ø7 for M6 to the bench at (±290, ±150)
SP = dict(t=10.0, x=160.0)                                                          # side plates: inner faces at x ±155, plates x ±155..±165
SPL = dict(y0=-100.0, y1=265.0, z1=450.0)                                           # -x (drive) side plate outline y -100..265, z 8..450 (overhangs the base at the back)
SPR = dict(y0=-100.0, y1=140.0, z1=265.0)                                           # +x side plate: low, so the label roll slides on over it
# ---- drive rollers (bought P1-425): Ø50 urethane 70A, face 240, Ø12 shaft ends in 6001-2RS in both side plates
ROL = dict(d=50.0, face=240.0, shaft=12.0, y=45.0, z=80.0, brg="6001-2RS (12 x 28 x 8)")
def c_height(d):                     # container centre above the roller centres
    return math.sqrt(((d + ROL["d"]) / 2) ** 2 - ROL["y"] ** 2)
def z_cent(d):
    return ROL["z"] + c_height(d)
def z_top(d):
    return z_cent(d) + d / 2
def contact_deg(d):                  # contact angle from the vertical
    return math.degrees(math.asin(ROL["y"] / ((d + ROL["d"]) / 2)))
# ---- drive: one ClearPath NEMA 23 on the inner face of the -x plate, belts on the outer face (HTD 3M, 9 wide)
PULLEY = dict(p=3.0, w=9.0)
MOT = dict(y=100.0, z=42.0, T=15, flange=57.2, pilot=38.1, bolt_sq=47.14, body_L=100.0, shaft=8.0)      # ClearPath-SDSK-2311S class
ROLLER_T = 30                        # both rollers, belt 1 plane x -180
LD = dict(d=30.0, y=130.0, z=120.0, T=18, x0=-110.0, x1=70.0)                                  # liner drive roller Ø30 knurled, cantilever; belt 2 from roller B (plane x -200)
REW = dict(y=235.0, z=110.0, hub_d=76.0, od_max=150.0, oring=5.0)                    # rewind spindle, O-ring slip belt from the liner drive shaft
UNW = dict(y=190.0, z=380.0, hub_d=76.0, flange_d=220.0)                            # unwind spindle
G1 = dict(y=145.0, z=205.0, d=20.0)                                                 # guide roller
PINCH = dict(d=20.0, F=20.0, piv_y=170.0, piv_z=150.0)                              # pinch roller on a sprung lever over the liner drive
X_BELT1, X_BELT2, X_ORING = -180.0, -200.0, -218.0
BELT1, BELT2 = "375-3M-9 (125 T)", "261-3M-9 (87 T)"
def pd(T):                           # pitch diameter
    return T * PULLEY["p"] / math.pi
def belt_len(pts):                   # closed belt round pulleys (y, z, pd) in order, all wrapped on the outside
    n = len(pts); L = 0.0
    for i in range(n):
        y1, z1, d1 = pts[i]; y2, z2, d2 = pts[(i + 1) % n]
        dd = math.hypot(y2 - y1, z2 - z1); r1, r2 = d1 / 2, d2 / 2
        L += math.sqrt(dd ** 2 - (r1 - r2) ** 2)
    # arcs: sum of wrap angles x r, from the external tangent directions
    def tang(a, b):
        (y1, z1, d1), (y2, z2, d2) = a, b
        r1, r2 = d1 / 2, d2 / 2; th = math.atan2(z2 - z1, y2 - y1); dd = math.hypot(y2 - y1, z2 - z1)
        return th + math.asin((r1 - r2) / dd)          # direction of the tangent line, belt running counter-clockwise round the outside
    for i in range(n):
        a_in = tang(pts[i - 1], pts[i]); a_out = tang(pts[i], pts[(i + 1) % n])
        wrap = (a_out - a_in) % (2 * math.pi)
        L += wrap * pts[i][2] / 2
    return L
B1_PTS = [(-ROL["y"], ROL["z"], pd(ROLLER_T)), (MOT["y"], MOT["z"], pd(MOT["T"])), (ROL["y"], ROL["z"], pd(ROLLER_T))]
B2_PTS = [(ROL["y"], ROL["z"], pd(ROLLER_T)), (LD["y"], LD["z"], pd(LD["T"]))]
# ---- peel plate and idler 400
PEEL = dict(t=2.0, tip_y=15.0, L=70.0, w=120.0, slope=8.0, r_tip=1.0)               # 2 mm 304, tip radius 1, slopes down 8° to the tip
IDL = dict(d=30.0, face=220.0, shaft=12.0, piv_y=120.0, piv_z=245.0, arm_w=25.0, arm_t=8.0, F=15.0)
def idler_at(k):                     # idler centre (y, z) resting on container k, and arm angle
    d = CONT[k]["d"]; zc = z_top(d) + IDL["d"] / 2
    R = math.hypot(IDL["piv_y"] - (-20.0), IDL["piv_z"] - (z_top(CONT["jar-12"]["d"]) + IDL["d"] / 2))
    yc = IDL["piv_y"] - math.sqrt(R ** 2 - (IDL["piv_z"] - zc) ** 2)
    return yc, zc, R
FENCE = dict(t=8.0, w=30.0, h=125.0)                                                # UHMW end fence between the rollers
def fence_x(k):                      # container bottom at the fence; label centred on the body at x 0
    return -CONT[k]["h"] / 2
# ---- electrics
ELE = dict(V=120.0, A=1.2, fuse=3.0, V_dc=24.0, I_dc=6.5)                            # one 24 V supply feeds the ClearPath and the ClearCore
ENC = dict(x0=190.0, x1=320.0, y0=-125.0, y1=125.0, h=200.0)                     # PC box on the +x end of the base, lid outward (+x), operators on the -y end wall
ENC_OPS = {"estop": (255.0, 160.0), "sel": (225.0, 110.0), "sj": (285.0, 110.0), "feed": (255.0, 55.0)}   # (x, z above the base top)


def calcs():
    c = {}
    v = LAB["speed"]
    c["n_roll"] = v / (math.pi * ROL["d"]) * 60
    c["n_mot"] = c["n_roll"] * ROLLER_T / MOT["T"]
    c["v_liner"] = c["n_roll"] * ROLLER_T / LD["T"] * math.pi * LD["d"] / 60          # liner drive surface speed (mm/s)
    c["ratio_err"] = c["v_liner"] / v - 1
    c["L_b1"] = belt_len(B1_PTS); c["L_b2"] = belt_len(B2_PTS)
    for k, ct in CONT.items():
        circ = math.pi * ct["d"]
        rl = math.pi * ((LAB["od_max"] / 2) ** 2 - (LAB["core"] / 2) ** 2) / LAB["t"]
        c[k] = dict(circ=circ, wrap=ct["lab_L"] / circ, t_lab=(ct["lab_L"] + 20) / v, z_c=z_cent(ct["d"]), z_top=z_top(ct["d"]),
                    contact=contact_deg(ct["d"]), labels_roll=rl / (ct["lab_L"] + LAB["gap"]), fence=fence_x(k), web=ct["lab_H"] + LAB["liner"],
                    idler=idler_at(k), n_cont=v / circ * 60)
    c["t_cycle"] = 1.0 + 0.5 + c["jar-12"]["t_lab"] + 1.0
    F_surf = 2.0 + IDL["F"] * 0.05 + 0.6 * 9.81 * 0.05 + 2.0          # peel 2 N, idler + container rolling drag, rewind slip 2 N (N at the roller surface)
    c["F_surf"] = F_surf
    c["T_mot"] = F_surf * ROL["d"] / 2000 * MOT["T"] / ROLLER_T / 0.85     # N·m at the motor, belt efficiency 0.85
    return c


if __name__ == "__main__":
    for k, v in calcs().items():
        print(k, v)
