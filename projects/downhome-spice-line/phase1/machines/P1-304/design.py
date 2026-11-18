"""P1-304 drum-top vibratory sifter rev B: every engineered number (mm unless noted).
Frame: z up, z = 0 on the drum rim top (1,054 AFF, 55 gal open-top drum on its dolly); x toward the vibrator (east), y north.

Plant interfaces (DH-ASM-P1-002): drum OD 584 (rim), blender valve P1-331 outlet at 1,261 AFF on the drum axis, sock to the 4 in TC inlet
(ferrule top 1,235 AFF = z 181). Dust port 3 in TC to the collector P1-310 drum-vent hose. One sifter.

Stack (bottom up): base weldment P1-304-100 (seat ring on the rim, upstand, skirt into the liner, 3 centring tabs) is fixed;
3 rubber isolators carry the vibrating body P1-304-200 (shell, magnet bars, screen ledge, top flange, isolator brackets, vibrator bracket);
grate magnet P1-307 on the bars, screen deck P1-304-400 on the ledge, lid P1-304-300 clamped by 4 draw latches presses the deck down through 3 pads.
A silicone flex band P1-304-501 seals the 4 mm gap between the upstand and the body; a braided bond strap bridges the isolators."""
import math

IN = 25.4
# ---- plant interface
Z_RIM_FFL = 1054.0
DRUM = dict(od=584.0, id=572.0, rim_r=292.0)
Z_VALVE = 1261.0 - Z_RIM_FFL          # 207: blender valve outlet
Z_INLET_TOP = 1235.0 - Z_RIM_FFL      # 181: inlet ferrule top
# ---- sheet and tube
T14 = 1.9                             # 14 ga shell
R_I = 240.0                           # shell inside radius (Ø480 ID)
R_O = R_I + T14
# ---- base weldment 100 (fixed, 304; skirt is product-contact 316L)
SEAT = dict(od=680.0, id=466.0, t=6.0)          # isolator nuts sit outside the drum rim (R292)
UPST = dict(z0=SEAT["t"], h=30.0)     # upstand: same shell, z 6..36
SKIRT = dict(od=470.0, t=1.5, h=60.0)  # into the liner, below the rim
TAB = dict(w=40.0, t=3.0, h=35.0, r=DRUM["od"] / 2 + 1.5)  # centring tabs outside the rim, 3 at 0/120/240 deg + 60
R_ISO = 315.0                         # isolator circle (outside the rim: nut under the seat clears the drum)
A_ISO = (90.0, 210.0, 330.0)          # isolator angles (deg from +x)
# ---- isolators (bought)
ISO = dict(d=30.0, h=30.0, thread="M8", k=60.0, shore=40)   # k N/mm compression (confirm with maker curve)
Z_ISO_TOP = SEAT["t"] + ISO["h"]      # 36
# ---- vibrating body 200 (316L shell; 304 brackets)
Z_B0 = Z_ISO_TOP + 4.0                # 40: body shell bottom (4 gap to the upstand)
Z_B1 = 150.0                          # body shell top (flange underside)
TOPFL = dict(od=540.0, id=R_I * 2, t=6.0)            # top flange z 150..156
Z_TOP = Z_B1 + TOPFL["t"]             # 156
BAR = dict(w=25.0, t=5.0, z=48.0, y=(-110.0, 110.0))   # 2 magnet bars across x, top at z 53
LEDGE = dict(id=450.0, w=15.0, t=6.0, z=84.0)          # screen ledge ring, top at z 90
BRK = dict(t=6.0, w=50.0, l=100.0)    # isolator bracket (angle 6 thk, horizontal leg R_O..R_O+100 sits on the isolator at z 36..42)
VBR = dict(t=10.0, w=150.0, z0=40.0, z1=260.0, x=R_O + 40.0, gus_t=8.0)  # vibrator plate (vertical, normal +x) 40 off the shell, z 40..260
Z_VIB = 150.0                         # vibrator axis centre height (vertical axis): body z 20..280 clears the seat ring
VB_HOLES = dict(sy=70.0, sz=120.0, d=11.0)            # motor feet 4 x M10: 120 along the (vertical) motor axis x 70 across (confirm OLI drawing)
# ---- magnet (bought), screen deck 400 (made), lid 300 (made)
MAG = dict(sq=305.0, h=30.0)          # sits on the bars z 53..83
DECK = dict(od=476.0, t=3.0, h_up=25.0, h_lo=10.0, gasket=2.0)   # deck rings, gasket on the ledge
Z_DECK0 = LEDGE["z"] + LEDGE["t"] + DECK["gasket"]   # 92
Z_DECK1 = Z_DECK0 + DECK["h_lo"] + DECK["h_up"]       # 127 (cloth between the rings at z 102)
MESH = dict(no=12, wire=0.584, open=1.533)            # 12 x 12 mesh, 0.023 in wire, 316 (opening 1.53 mm)
LID = dict(od=540.0, t=2.0, gasket=3.0, pad_h=None)
Z_LID0 = Z_TOP + LID["gasket"]        # 159: lid underside
PAD = dict(d=30.0, r=200.0, a=(30.0, 150.0, 270.0))   # 3 hold-down pads on R200 under the lid
PAD["h"] = Z_LID0 - Z_DECK1 + 2.0     # 34 free (steel 31 + cap 3): squeezed 2 mm onto the deck when the lid is latched
PAD["steel"] = PAD["h"] - 3.0
TC4 = dict(od=101.6, id=97.4, fl=119.0, L=21.5)        # 4 in BPE short ferrule (inlet)
TC3 = dict(od=76.2, id=72.9, fl=91.0, L=21.5, r=170.0, a=200.0)  # 3 in dust port at R170
Z_FER0 = Z_LID0 + LID["t"]            # 161 ferrules start on the lid top
LATCH = dict(n=4, a0=45.0, r=275.0, hold=1100.0)       # draw latches at 45 + 90k: latch on a plate on the shell, keeper on a tab hanging from the lid rim
LPLATE = dict(w=40.0, h=60.0, t=3.0, z0=Z_B1 - 60.0, holes=(20.0, 5.5))   # latch plate on the shell (2 x M5 on 20 vertical, confirm latch)
KTAB = dict(w=40.0, h=35.0, t=3.0)    # keeper tab welded to the lid edge, hangs down outside the flange
BOND = dict(a_seat=60.0, r=330.0, a_brk=90.0)   # bond strap holes Ø9: seat ring at 60° R330, isolator bracket at 90°
# ---- duty
RHO = 0.51                            # kg/L blend
BATCH_KG = 66.7                       # 147 lb
RATE_KGMIN = 3.6                      # 8 lb/min target (valve throttled)
N_VIB = 3600.0                        # rpm, 2-pole 60 Hz
F_MAX = 2000.0                        # N, vibrator max centrifugal force (OLI MVE 200/36 class, confirm)
AMP_TARGET = 0.30                     # mm half-amplitude at the deck
M_PARTS = dict(magnet=6.5, vibrator=12.0, latches=0.6, band=0.4)  # kg bought (estimates); body, deck and lid come from cad/masses.json
SCREEN_LOAD = 1.0                     # kg/(min·dm²) upper sieving rate for 12 mesh free-flowing seasoning (design check)


def _masses():
    import json, pathlib
    p = pathlib.Path(__file__).parent / "cad" / "masses.json"
    return json.loads(p.read_text()) if p.exists() else {}


def calcs(m_body=None):
    ms = _masses()
    m_body = m_body or sum(v for k, v in ms.items() if k[7] in "234") or 17.0      # body 20x + lid 30x + deck 40x
    M = m_body + sum(M_PARTS.values())
    w = 2 * math.pi * N_VIB / 60
    me = M * AMP_TARGET / 1000                         # kg·m static moment needed
    F = me * w ** 2
    setting = F / F_MAX
    k_tot = 3 * ISO["k"] * 1000                       # N/m
    fn = math.sqrt(k_tot / M) / (2 * math.pi)
    r = (N_VIB / 60) / fn
    T = 1 / (r ** 2 - 1)
    static = M * 9.81 / 3 / ISO["k"]
    acc_g = w ** 2 * AMP_TARGET / 1000 / 9.81
    area_dm2 = math.pi / 4 * (LEDGE["id"] / 100) ** 2
    cap = SCREEN_LOAD * area_dm2
    t_batch = BATCH_KG / RATE_KGMIN
    open_area = (MESH["open"] / (MESH["open"] + MESH["wire"])) ** 2
    latch = LATCH["n"] * LATCH["hold"]
    lift = F                                           # worst-case vertical component on the lid stack
    return dict(M=M, m_body=m_body, me=me, F=F, setting=setting, fn=fn, r=r, T=T, F_tx=F * T, static=static, acc_g=acc_g,
                area_dm2=area_dm2, cap=cap, t_batch=t_batch, open_area=open_area, latch=latch, lift=lift,
                pad_h=PAD["h"], z_inlet=Z_FER0 + TC4["L"] - 1.5, gap_valve=Z_VALVE - (Z_FER0 + TC4["L"] - 1.5))


if __name__ == "__main__":
    for k, v in calcs().items():
        print(f"{k:10s} {v:.4g}")
