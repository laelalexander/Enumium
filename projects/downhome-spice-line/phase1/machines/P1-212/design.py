"""P1-212 bin screw feeder rev B: every engineered number (mm unless noted). Feeder frame: x along the screw, x = 0 under the
bin outlet centre, +x toward the weigh hopper (discharge), drive at -x (outboard); z up, z = 0 on the barrel axis; y across.

Plant interfaces (DH-ASM-P1-001): bin centres on R1,250, bin outlet flange underside at 1,730 = axis + 204 (gasket 3 incl.),
hopper lid inlet circle R280 at 1,231 (12 positions). One feeder per used bin, 9 off."""
import math

IN = 25.4
# ---- plant interface
R_BIN, R_INLET = 1250.0, 280.0
Z_AXIS_FFL = 1526.0                 # axis height above finished floor
BIN_FL = dict(sq=200.0, open=120.0, bolt_sq=160.0, hole=11.0, gasket=3.0)
Z_FL_TOP = 204.0 - BIN_FL["gasket"]  # feeder flange top (gasket on top, bin flange above)
T_FL = 6.0
Z_FL_BOT = Z_FL_TOP - T_FL           # 195: transition top
X_SPOUT = R_BIN - R_INLET            # 970: spout centre over the lid port
Z_SPOUT_END = -132.0                 # spout bottom
Z_LID = 1231.0 - Z_AXIS_FFL          # -295: hopper lid top in feeder frame
# ---- barrel (ASTM A270 sanitary tube 2.5 in x 16 ga)
B_OD, B_T = 63.5, 1.65
B_ID = B_OD - 2 * B_T                # 60.2
X_FL_IN, X_FL_OUT = -120.0, -130.0   # drive-end flange P1-212-03: inner (product) face, outer face
T_EF = 10.0
X_TAIL = 1065.0                      # tail TC ferrule face
FER = dict(L=21.5, fl_od=77.5, groove="2.5 in per ASME BPE DT-7")   # 14WMP short ferrule
X_TUBE0, X_TUBE1 = X_FL_IN - 4.0, X_TAIL - FER["L"]               # tube sits 4 deep in a Ø63.6 socket in the flange (3 web to the Ø70 recess)
INLET = dict(lx=120.0, wy=50.0)      # slot in the barrel top
TR_T = 1.9                           # transition walls 14 ga
# ---- screw (bought formed flight welded on our shaft)
S_OD, S_P, S_T = 56.0, 56.0, 3.0
S_D = 25.0                           # shaft Ø25 h9 316
X_S0 = -115.0                        # screw drive-end face (5 gap to the flange inner face)
X_F0, X_F1 = -110.0, 1000.0          # flighted length (stops at the spout far edge)
SOCKET = dict(d=20.2, depth=45.0, slot_w=6.5, slot_d=25.0)
X_SP0, X_SP1 = 1062.0, 1095.0        # tail spigot Ø20 f7 (runs in the UHMW bush in the end cap)
SPIGOT_D = 20.0
# ---- drive end
X_PIN = -93.0                        # cross pin Ø6 x 24 in the drive shaft
SHAFT = dict(d=20.0, x_tip=-75.0, x_end=-292.0, key=(6, 6, 32), x_key0=-250.0, x_key1=-290.0)
HSG = dict(spig_d=70.0, spig_h=3.0, collar_d=90.0, collar_t=8.0, pcd_front=80.0, body_d=60.0, rear_d=110.0, rear_t=10.0, pcd_rear=90.0,
           seal_bore=35.0, seal_w=7.0, brg_bore=42.0, brg_w=12.0, spacer=64.0, oring=(46.0, 2.5))
X_H_FACE = X_FL_OUT + HSG["spig_h"]  # -127: housing spigot face on the recess floor
X_BRG_A0 = X_H_FACE - 12.0           # -139
X_BRG_A1 = X_BRG_A0 - HSG["brg_w"]   # -151
X_BRG_B0 = X_BRG_A1 - HSG["spacer"]  # -215
X_BRG_B1 = X_BRG_B0 - HSG["brg_w"]   # -227
X_H_REAR0 = X_BRG_B1 - 2.0           # -229
X_H_REAR1 = X_H_REAR0 - HSG["rear_t"]  # -239
LANT = dict(t=8.0, front_sq=110.0, rear_sq=140.0, bar=(103.0, 8.0), spig=80.0, pcd_gm=100.0)
X_GM = X_H_REAR1 - LANT["t"] - 90.0 - LANT["t"]   # -345: gearmotor flange face
GM_LEN = 280.0                        # NORD SK 072.1 + 71S/4 overall from flange (confirm)
EF = dict(sq=110.0, recess=70.0, recess_d=3.0, tap="M6", pcd=80.0)
# ---- tail end
CAP = dict(boss_d=44.0, boss_l=40.0, bush_od=30.0, bush_id=20.3, bush_l=30.0)
# ---- duty
RHO_BULK = 0.55                      # kg/L typical seasoning
FILL = 0.40
I_GEAR, N_MOTOR = 10.25, 1690.0      # rpm at 60 Hz
N_FAST, N_SLOW = 150.0, 15.0
P_MOTOR = 0.25                        # kW


def calcs():
    vol_rev = math.pi / 4 * (S_OD ** 2 - S_D ** 2) * S_P * 1e-6       # L per rev, full
    q = vol_rev * FILL
    n60 = N_MOTOR / I_GEAR
    T_out = P_MOTOR * 1000 * 0.9 / (2 * math.pi * n60 / 60)
    # flight blank (one pitch)
    Lo = math.hypot(math.pi * S_OD, S_P); Li = math.hypot(math.pi * S_D, S_P); w = (S_OD - S_D) / 2
    Ri = w * Li / (Lo - Li); Ro = Ri + w
    cut = 360 * (1 - Lo / (2 * math.pi * Ro))
    # deflection: shaft + flight, simply supported between drive socket and tail bush
    E = 193000.0; I = math.pi * S_D ** 4 / 64
    m_shaft = math.pi / 4 * S_D ** 2 * 7.95e-6                         # kg/mm
    m_fl = (math.pi / 4 * (S_OD ** 2 - S_D ** 2)) * S_T * 1.06 * 7.95e-6 / S_P
    w_l = (m_shaft + m_fl) * 9.81                                       # N/mm
    L = X_SP0 + 15 - (X_PIN)
    defl = 5 * w_l * L ** 4 / (384 * E * I)
    tau_pin = T_out * 1000 / (SOCKET["d"] / 2) / (2 * math.pi * 3 ** 2)
    return dict(vol_rev=vol_rev, q_rev=q, n60=n60, f_fast=N_FAST / n60 * 60, f_slow=N_SLOW / n60 * 60,
                q_fast_lh=q * N_FAST * 60, q_slow_lh=q * N_SLOW * 60, q_fast_kgmin=q * N_FAST * RHO_BULK, q_slow_gs=q * N_SLOW * RHO_BULK * 1000 / 60,
                T_out=T_out, Lo=Lo, Li=Li, Ri=Ri, Ro=Ro, cut=cut, w=w, defl=defl, span=L, clear=(B_ID - S_OD) / 2,
                tau_pin=tau_pin, mass_screw=(m_shaft + m_fl) * (X_SP1 - X_S0))


if __name__ == "__main__":
    for k, v in calcs().items():
        print(f"{k:14s} {v:.4g}")
