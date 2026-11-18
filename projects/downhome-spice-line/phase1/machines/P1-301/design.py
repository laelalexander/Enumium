"""P1-301 ribbon blender 6 cu ft, rev B: engineering numbers for every drawing, cut file and the 3D model.

Axes: x along the shaft (+x = drive end), y across (+y = back / hinge side), z up from the finished floor.
Angles on the agitator: measured from top dead centre, positive counter-clockwise viewed from the drive end
(right-hand rule about +x). Shaft turns CLOCKWISE viewed from the drive end (negative about +x).
"""
import math

IN = 25.4
# ---- process
BATCH_L, BULK = 131.0, 0.51                   # L per batch, kg/L blended seasoning
RPM = 40.0
# ---- trough
R_IN, W_IN, L_IN, H_SIDE, T_SH = 280.0, 560.0, 900.0, 294.0, 3.0   # inside radius, width, length, side above axis (to flange underside), shell
T_FL, FL_OUT_X, FL_OUT_Y = 6.0, 1000.0, 646.0                      # flange plate, outside size
T_EP, EP_OFF = 8.0, 15.0                                            # end plate thickness, profile offset beyond the shell outside (drive end, welded)
# free end: bolted end plate on a shell end ring so the agitator slides in from the free end (both shaft ends pass through the end plates)
RING = dict(t=8.0, r_out=323.0, r_bolt=303.0, hole=11.0)
Z_AX = 1683.0
Z_TB = Z_AX - R_IN - T_SH                                           # 1,400 trough bottom outside
Z_FLTOP = Z_AX + H_SIDE + T_FL                                      # 1,983 flange top
TC4_OD, TC4_FER_OD, TC4_FER_L = 101.6, 119.0, 28.6                  # 4 in tube OD, ferrule flange OD (ASME BPE 4 in = 119.0), short ferrule length
TC15_OD = 38.1                                                      # 1.5 in
# ---- shaft and seals
D_SH, D_DRV = 60.0, 45.0
X_BRG = 641.0                                                       # bearing centres ±641 (plate outer face 612 + A2 29)
X_FREE_END, X_SHOULDER, X_DRV_END = -690.0, 690.0, 860.0
KEY = dict(b=14, h=9, t1=5.5, L=140, x0=705.0)                      # DIN 6885 A 14 x 9 for Ø45
BOX = dict(od=150.0, spig_d=100.0, spig_l=T_EP, throat=64.0, bore=80.0, x_face=T_EP + 50.0, pcd=115.0, stud="M10", stud_depth=20.0)
PACK = dict(size=10.0, rings=4)
FOLLOW = dict(od=150.0, t=12.0, spig_d=80.0, spig_l=18.0, bore=62.0)
# ---- ribbons (OD, width radial, thickness, pitch, hand, phase at x=0 in deg)
RIB = {
    "OL": dict(od=550.0, w=50.0, t=8.0, p=600.0, hand="RH", x0=-435.0, x1=0.0, ph=0.0),     # outer left: conveys +x (to the centre)
    "OR": dict(od=550.0, w=50.0, t=8.0, p=600.0, hand="LH", x0=0.0, x1=435.0, ph=180.0),    # outer right: conveys -x
    "IL": dict(od=320.0, w=40.0, t=8.0, p=450.0, hand="LH", x0=-435.0, x1=0.0, ph=None),    # inner left: conveys -x (to the ends)
    "IR": dict(od=320.0, w=40.0, t=8.0, p=450.0, hand="RH", x0=0.0, x1=435.0, ph=None),
}
ARM_O = dict(d=25.0, spig=20.0, spig_l=12.0, slot=25.0, x=[-425.0, -220.0, -15.0, 15.0, 220.0, 425.0])
ARM_I = dict(d=20.0, spig=16.0, spig_l=10.0, slot=20.0, x=[-405.0, -290.0, -160.0, -30.0, 30.0, 160.0, 290.0, 405.0])
# ---- frame
LEG, LEG_T = 76.2, 3.05
X_LEG, Y_LEG = 606.0, 400.0
Z_RAIL = 1783.0                                                     # top rail top = lug seat
Z_LOW = 300.0                                                       # lower rail top
FOOT = 150.0
BP = dict(t=12.0, x_in=600.0, z0=1543.0, z1=1783.0, hole=80.0, bolt_sq=143.0, bolt_d=17.5)  # bearing plate: UCF212 J=143, M16 (slotted 17.5 x 20 for alignment)
LUG = dict(x=[-300.0, 300.0], t=10.0, w=120.0)


def ring_bolts():
    """(y, z-from-axis) of the free-end bolt circle: 9 on the radius every 22.5°, 3 up each side."""
    pts = [(RING["r_bolt"] * math.cos(math.radians(a)), RING["r_bolt"] * math.sin(math.radians(a))) for a in [180 + 22.5 * i for i in range(9)]]
    for sy in (-1, 1):
        pts += [(sy * RING["r_bolt"], z) for z in (85.0, 175.0, 265.0)]
    return pts


def theta(name, x):
    r = RIB[name]
    s = 1 if r["hand"] == "RH" else -1
    return (r["ph"] + s * 360.0 * x / r["p"]) % 360.0


def _clash(ph_i):
    for n in ("IL", "IR"):
        RIB[n]["ph"] = ph_i[n]
    worst = 999
    for xa in ARM_O["x"]:
        no = "OL" if xa < 0 else "OR"; ni = "IL" if xa < 0 else "IR"
        d = abs((theta(no, xa) - theta(ni, xa) + 180) % 360 - 180)
        worst = min(worst, d)
    for xa in ARM_I["x"]:                       # inner arm vs the outer ribbon cannot touch (r 30-120 < 225); vs other inner arms: spacing
        pass
    return worst


best = max(((a, b) for a in range(0, 360, 5) for b in range(0, 360, 5)), key=lambda ab: _clash({"IL": ab[0], "IR": ab[1]}))
_clash({"IL": best[0], "IR": best[1]})
CLEAR_DEG = _clash({"IL": best[0], "IR": best[1]})


def arms():
    out = []
    for xa in ARM_O["x"]:
        n = "OL" if xa < 0 else "OR"
        out.append(dict(tag="A", ribbon=n, x=xa, ang=round(theta(n, xa), 1), r0=D_SH / 2, r1=RIB[n]["od"] / 2 - RIB[n]["w"], d=ARM_O["d"], slot=ARM_O["slot"]))
    for xa in ARM_I["x"]:
        n = "IL" if xa < 0 else "IR"
        out.append(dict(tag="B", ribbon=n, x=xa, ang=round(theta(n, xa), 1), r0=D_SH / 2, r1=RIB[n]["od"] / 2 - RIB[n]["w"], d=ARM_I["d"], slot=ARM_I["slot"]))
    return out


def lead_deg(name, r):
    """helix lead angle from the circumferential direction at radius r."""
    return math.degrees(math.atan(RIB[name]["p"] / (2 * math.pi * r)))


def blank(name):
    """Flight blank for a ribbon formed by stretching a flat annular sector (sectional flight method)."""
    r = RIB[name]
    Do, Di, p, w = r["od"], r["od"] - 2 * r["w"], r["p"], r["w"]
    Lo, Li = math.hypot(math.pi * Do, p), math.hypot(math.pi * Di, p)
    Ri = w * Li / (Lo - Li); Ro = Ri + w
    turn = math.degrees(Lo / Ro)                       # blank sector angle per full turn
    turns = (r["x1"] - r["x0"]) / p
    sect = turn * turns
    return dict(Do=Do, Di=Di, p=p, Lo=Lo, Li=Li, Ri=Ri, Ro=Ro, turn_deg=turn, gap_deg=360 - turn, turns=turns, sector_deg=sect,
                sector_cut=sect + 2 * math.degrees(15 / Ro), helix_deg_out=math.degrees(math.atan(p / (math.pi * Do))))


def calcs():
    P = 1.5e3                                            # 2 HP motor
    w = 2 * math.pi * RPM / 60
    T = P / w
    tau = lambda d, t: 16 * t / (math.pi * (d / 1e3) ** 3) / 1e6
    vol_total = (math.pi * R_IN ** 2 / 2 + W_IN * (H_SIDE)) * L_IN / 1e6
    return dict(power_kw=1.5, torque_nm=T, tau_60=tau(60, 2 * T), tau_45=tau(45, 2 * T), tip=math.pi * 0.55 * RPM / 60,
                vol_total_l=vol_total, batch_l=BATCH_L, fill=BATCH_L / vol_total, batch_kg=BATCH_L * BULK,
                key_shear=2 * T / ((D_DRV / 2e3) * KEY["b"] * (KEY["L"] - KEY["b"]) * 1e-6) / 1e6,
                key_bear=2 * T / ((D_DRV / 2e3) * (KEY["h"] - KEY["t1"]) * (KEY["L"] - KEY["b"]) * 1e-6) / 1e6)


if __name__ == "__main__":
    print("inner phases", best, "min outer-arm / inner-ribbon clearance", CLEAR_DEG, "deg")
    for a in arms():
        print(a)
    for n in RIB:
        print(n, {k: round(v, 2) if isinstance(v, float) else v for k, v in blank(n).items()})
    print({k: round(v, 2) for k, v in calcs().items()})
