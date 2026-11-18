"""P1-401 servo auger filler rev B: every engineered number (mm unless noted).
Frame: z up from the floor, origin on the auger axis; x to the operator's right, y away from the operator (column at the back).

Duty (design-basis.json, linebal-config.json): shaker-250 113.4 g (Ø66 x 109), jar-12 340.2 g (Ø86 x 155), pouch-12 340.2 g (165 x 229),
tub-5lb 2,268 g (Ø203 x 191). Blend 0.538-0.548 g/mL. Filler rated 15 upm, operator paced (foot switch), net checked downstream on P1-407.

Stack (bottom up): cabinet P1-401-100 (controls inside) > container stage P1-401-700 on 2 guide rods, indexed at 4 heights >
tooling (auger + tube, P1-415, made to our spec P1-401-600) > hopper P1-401-400 (316L, 42 L) hung on the horseshoe of column P1-401-200 >
agitator P1-401-500 > drive head P1-401-300: head plate, spindle cartridge, agitator hub under the plate (chain from a gearmotor),
servo on a bridge driving the spindle by an HTD belt 2:1."""
import math

IN = 25.4
# ---- cabinet 100 (304, controls inside)
CAB = dict(w=600.0, d=600.0, h=697.0, t=1.5, y0=-200.0)      # body box x ±300, y -200..400, z 60..757 (column bolts at y 370 clear the back wall)
FEET = dict(h=60.0, thread="M12", adj=25.0, pad=60.0, x=260.0, y=260.0)   # levelling feet M12, pad Ø60, set to 60 (±25 [1 in])
FEET["yc"] = CAB["y0"] + CAB["d"] / 2   # 100: foot pattern centre
Z_FOOT = FEET["h"]                   # cabinet base underside
ZC = Z_FOOT + CAB["h"]               # 757: cabinet shell top = top plate underside
TOP = dict(w=640.0, d=640.0, t=3.0)  # top plate overhang 20 all round, y -220..420
Z_TOP = ZC + TOP["t"]                # 760: top surface
DOOR = dict(w=560.0, h=650.0, gap=3.0, z0=Z_FOOT + 20.0)
# ---- container stage 700
Z_OUT = Z_TOP + 260.0                # 1,020: tooling tube outlet
STAGE = dict(w=240.0, d=240.0, t=6.0, rod_d=20.0, rod_y=85.0, rod_L=290.0, bush_L=80.0, bush_a=60.0, bar_x=100.0, bar_L=150.0)   # rods at (0, ±85), pin bar at x 100
CONT = {  # container: (diameter or width, height, net g, positions)
    "shaker-250": dict(d=66.0, h=109.2, g=113.4, cap="53 mm flip", tool="S"),
    "jar-12": dict(d=86.4, h=154.9, g=340.2, cap="89 mm sifter", tool="J"),
    "tub-5lb": dict(d=203.2, h=190.5, g=2268.0, cap="tub lid", tool="J"),
    "pouch-12": dict(d=165.1, h=228.6, g=340.2, cap="zip", tool="J"),
}
GAP_FILL = 10.0                      # tube outlet above the container rim
STAGE_POS = {k: round(Z_OUT - GAP_FILL - v["h"] - Z_TOP - STAGE["t"]) for k, v in CONT.items()}  # stage plate underside above the top, per container
STAGE_POS["pouch-12"] = 40           # pouch: lowest stop; the tube enters the pouch mouth 14 mm, operator holds it open
PLG = dict(h=20.0, x=160.0, thread="M16 x 1.5", name="GN 617-10-AK")   # index plunger axis 20 above the top, in a block at x 160 (operator's right)
PINBAR_HOLES = {k: v - PLG["h"] for k, v in STAGE_POS.items()}   # hole centres below the stage plate underside
PIN = dict(d=10.0, bar_w=40.0, bar_t=12.0, hole=10.2)
# ---- column 200 (304)
COL = dict(a=101.6, t=3.05, y=300.0)          # 4 in sq x 11 ga tube, axis at y 300
Z_HP = 1720.0                                 # head plate underside
CAP = dict(a=160.0, t=12.0)                   # column cap plate (head plate bolts to it)
COL["L"] = Z_HP - CAP["t"] - (Z_TOP + 12.0)   # tube between the base plate top (12) and the cap underside
CBASE = dict(a=180.0, t=12.0, bolt="M12", pcd=140.0, back_t=10.0)   # column base plate, 4 x M12 through the top into a backing plate
HSH = dict(ri=232.0, w=40.0, t=20.0, open=150.0, pin_d=8.0, pin_a=(30.0, 150.0))  # horseshoe: R232..272, open at the front (-y) 150 wide
# ---- hopper 400 (316L, 14 ga)
T14 = 1.9
HOP = dict(r=225.0, h_cyl=150.0, h_cone=300.0, r_lo=30.1)   # ID Ø450, cone to the 2.5 in TC (ID 60.2)
Z_CONE0 = 1140.0                     # cone small end (ferrule weld)
Z_CYL0 = Z_CONE0 + HOP["h_cone"]     # 1,440
Z_RIM = Z_CYL0 + HOP["h_cyl"]        # 1,590 hopper top (rim angle top)
RIM = dict(w=25.0, t=3.0)            # rim angle 25 x 25 x 3 rolled, sits on the horseshoe (z 1,590 underside of the outstand at Z_RIM - 3)
TC25 = dict(od=63.5, id=60.2, fl=77.5, L=21.5)        # 2.5 in BPE ferrule at the hopper outlet
Z_TC = Z_CONE0 - TC25["L"]           # 1,118.5 clamp face
LID = dict(t=1.5, bore=80.0, port_w=170.0, port_l=280.0, port_x=-120.0, up=40.0)   # 2-piece lid, scoop port with flap on the operator side
# ---- drive head 300
HPL = dict(t=10.0, x0=-235.0, x1=250.0, y0=-115.0, y1=385.0)   # head plate 304
Z_HPT = Z_HP + HPL["t"]              # 1,730 head plate top
BRG_SP = dict(d=25.0, D=52.0, B=15.0, name="6205-2RS")        # spindle bearings x 2
BRG_AG = dict(d=40.0, D=68.0, B=15.0, name="6008-2RS", n=2)  # agitator hub bearings (2) on the housing spigot
HOUS = dict(fl_d=110.0, fl_t=12.0, body_d=72.0, h_up=60.0, spig_d=40.0, pilot_d=50.0, pcd=90.0, bolt="M8", cap_t=12.0)   # cap: Ø36 x 3 ring recess + Ø40 x 7 seal pocket from below
HOUS["z_top"] = Z_HPT + HOUS["fl_t"] + HOUS["h_up"]           # 1,802
HOUS["brg_up"] = HOUS["z_top"] - BRG_SP["B"]                     # upper 6205 1,787..1,802
HOUS["brg_lo"] = Z_HPT + HOUS["fl_t"]                            # lower 6205 1,742..1,757 (45 between centres)
Z_PUL = HOUS["z_top"] + HOUS["cap_t"] + 5.0                     # 1,819 pulley plane bottom (both pulleys, 22 wide)
SPN = dict(d=25.0, top=Z_PUL + 30.0, seat=20.0, thread="M16 x 1.5 LH", Z_cpl=1500.0)  # spindle: Ø20 pulley seat 1,815..1,845, coupling face in the hopper
HUB = dict(od=80.0, z1=Z_HP - 3.0, seal="25 x 40 x 7", seal_d=40.0, seal_b=7.0, fl_d=140.0, fl_t=8.0, spr_pcd=100.0)   # hub top 3 below the plate
HUB["z_brg"] = HUB["z1"] - 2 * BRG_AG["B"]                 # 1,687 bearings bottom
HUB["z_seal"] = HUB["z_brg"] - 4.0 - HUB["seal_b"]         # 1,676 (4 mm Ø48 relief for the DIN 471 ring on the spigot)
Z_AGTC = HUB["z_seal"] - 21.5                               # 1,654.5 agitator TC face (hub ferrule bottom)
HOUS["spig_L"] = HPL["t"] + (Z_HP - HUB["z_brg"]) + 3      # pilot in the plate + bearings + ring groove (spigot end 1,684)
SPACER = dict(od=52.0, id_o=46.0, d_i=25.1, od_i=30.0, L=30.0)   # outer + inner spacers between the 6205s (cartridge loads from the top)
BELT = dict(pitch=5.0, z1=20, z2=40, width=15.0, L=450.0, name="HTD 450-5M-15")
PD1, PD2 = BELT["z1"] * BELT["pitch"] / math.pi, BELT["z2"] * BELT["pitch"] / math.pi
BELT["C"] = 149.0                    # centre distance for a 450 mm belt (checked in calcs)
SERVO_X = -BELT["C"]                 # servo on axis x -149, y 0, on a bridge above the plate
BRIDGE = dict(a=140.0, t=10.0, h=110.0, post_d=25.0)          # servo bridge: 4 posts Ø25 x 110 on 110 sq, flange 140 sq; servo face at 1,850, shaft end 1,815
CHAIN = dict(p=12.7, z1=15, z2=30, name="#40 SS", C=184.0, links=52)    # agitator chain under the plate
GM_X = CHAIN["C"]                    # gearmotor shaft x +180 (slotted for tension)
AGIT = dict(sleeve_od=63.5, sleeve_t=1.65, rpm=30.0, tc="2.5 in", z_arm=1525.0, arm_w=25.0, arm_t=6.0, r_tip=212.0, blade_w=25.0, blade_t=6.0,
            z_cone_end=1200.0, clear=10.0)   # 2.5 in BPE tube sleeve, 2.5 in TC to the hub; blades 10 off the wall
# ---- tooling (P1-415, made to P1-401-600)
TOOL = {
    "S": dict(name="shaker tooling", tube_od=31.75, tube_id=28.45, auger_od=27.0, shaft=10.0, pitch=27.0, L_tube=98.5),
    "J": dict(name="jar / pouch / tub tooling", tube_od=50.8, tube_id=47.5, auger_od=46.0, shaft=16.0, pitch=46.0, L_tube=98.5),
}
FILL_EFF = 0.85                      # volumetric efficiency of a full auger (confirm in calibration)
RPM = dict(S=900.0, J=600.0)         # auger dose speed
# ---- duty
RHO = 0.548                          # g/mL (f-orig), range 0.538-0.548
UPM = dict(rated=15.0, shaker=12.0, jar=8.0)
SERVO = dict(kw=0.75, T_rated=2.39, T_peak=7.16, n_max=3000.0, J=1.13e-4)     # SureServo2 SV2L-207B (confirm)
GM = dict(hp=0.25, rpm=60.0, T=27.0)                                            # agitator gearmotor (confirm)
T_AUGER = dict(S=1.0, J=3.0)         # N·m running torque estimate with the hopper full (confirm with the tooling maker)
M_HEAD_BOUGHT = dict(servo=3.0, gearmotor=7.0, pulleys=1.2, chain=0.6, bearings=0.5)


def _masses():
    import json, pathlib
    p = pathlib.Path(__file__).parent / "cad" / "masses.json"
    return json.loads(p.read_text()) if p.exists() else {}


def auger_vol(t):
    T = TOOL[t]
    return math.pi / 4 * (T["auger_od"] ** 2 - T["shaft"] ** 2) * T["pitch"] / 1000 * FILL_EFF     # mL / rev


def calcs():
    ms = _masses()
    out = {}
    for k, c in CONT.items():
        t = c["tool"]
        v = auger_vol(t)
        mL = c["g"] / RHO
        rev = mL / v
        out[k] = dict(mL=mL, rev=rev, t_dose=rev / RPM[t] * 60 + 0.15, g_rev=v * RHO, g_pulse=v * RHO / 10000, stage=STAGE_POS[k])
    vol_hop = (math.pi * HOP["r"] ** 2 * HOP["h_cyl"] + math.pi * HOP["h_cone"] / 3 * (HOP["r"] ** 2 + HOP["r"] * HOP["r_lo"] + HOP["r_lo"] ** 2)) / 1e6
    cone_ang = math.degrees(math.atan(HOP["h_cone"] / (HOP["r"] - HOP["r_lo"])))
    ratio = BELT["z2"] / BELT["z1"]
    T_out = SERVO["T_rated"] * ratio * 0.95
    belt_L = 2 * BELT["C"] + math.pi * (PD1 + PD2) / 2 + (PD2 - PD1) ** 2 / (4 * BELT["C"])
    F_belt = 2 * T_AUGER["J"] / (PD2 / 1000) * 1.5 + 2 * 60                             # effective + 2 x 60 N static tension
    # spindle bearings: belt pull at the pulley (overhang 25 above the upper bearing, bearings 45 apart)
    a, b = 31.5, 45.0                                                   # pulley centre 31.5 above the upper bearing centre, bearings 45 apart
    R_up = F_belt * (a + b) / b
    C_6205 = 14.8e3
    L10h = (C_6205 / R_up) ** 3 * 1e6 / (60 * RPM["J"])
    chain_links = 2 * CHAIN["C"] / CHAIN["p"] + (CHAIN["z1"] + CHAIN["z2"]) / 2 + ((CHAIN["z2"] - CHAIN["z1"]) / (2 * math.pi)) ** 2 * CHAIN["p"] / CHAIN["C"]
    m_made = sum(ms.values()) if ms else 0.0
    m_head = sum(v for k, v in ms.items() if k.startswith("P1-401-3")) + sum(M_HEAD_BOUGHT.values())
    m_hop_full = sum(v for k, v in ms.items() if k.startswith("P1-401-4") or k.startswith("P1-401-5")) + vol_hop * RHO
    arm = COL["y"]                                                              # head and hopper CG on the axis, column at y 300
    M_col = 9.81 * (m_head + m_hop_full) * arm / 1000                            # N·m at the column base
    Ix = (COL["a"] ** 4 - (COL["a"] - 2 * COL["t"]) ** 4) / 12                    # mm^4
    Zx = Ix / (COL["a"] / 2)
    sig = M_col * 1000 / Zx
    defl = (9.81 * (m_head + m_hop_full)) * arm * (COL["L"] ** 2) / (2 * 193e3 * Ix)  # end moment on a cantilever: θ L²/2 approx (M L²/2EI)
    bolt_T = M_col / (CBASE["pcd"] / 1000) / 2                                   # tension in the 2 back bolts
    m_cab = sum(v for k, v in ms.items() if k.startswith("P1-401-1")) + 12.0     # + controls
    m_tot = m_made + sum(M_HEAD_BOUGHT.values()) + 12.0 + vol_hop * RHO
    # tip forward: all mass of head + hopper at y 0, cabinet mass at y 100, feet at y -200 (front)
    y_cg = ((m_head + m_hop_full) * 0 + m_cab * FEET["yc"] + (m_tot - m_head - m_hop_full - m_cab) * COL["y"]) / m_tot
    # horseshoe: each arm a cantilever from the column face carrying half the full hopper at the mean ring radius
    I_h = HSH["w"] * HSH["t"] ** 3 / 12
    F_arm = 9.81 * m_hop_full / 2
    L_arm = COL["y"] - COL["a"] / 2 + HSH["ri"] + HSH["w"] / 2
    d_hsh = F_arm * (L_arm * 0.6) ** 3 / (3 * 193e3 * I_h)          # load centroid ≈ 0.6 L along the arm
    s_hsh = F_arm * L_arm * 0.6 * (HSH["t"] / 2) / I_h
    out.update(d_hsh=d_hsh, s_hsh=s_hsh, clr_J=(TOOL["J"]["tube_id"] - TOOL["J"]["auger_od"]) / 2, clr_S=(TOOL["S"]["tube_id"] - TOOL["S"]["auger_od"]) / 2)
    out.update(vol_hop=vol_hop, kg_hop=vol_hop * RHO, cone_ang=cone_ang, ratio=ratio, T_out=T_out, SF_T=T_out / T_AUGER["J"], belt_L=belt_L,
               F_belt=F_belt, R_up=R_up, L10h=L10h, chain_links=chain_links, m_made=m_made, m_head=m_head, m_hop_full=m_hop_full, M_col=M_col,
               sig=sig, defl=defl, bolt_T=bolt_T, m_tot=m_tot, y_cg=y_cg, agit_tip=math.pi * 2 * (HOP["r"] - 10) * AGIT["rpm"] / 60 / 1000,
               n_servo_J=RPM["J"] * ratio, n_servo_S=RPM["S"] * ratio, units_per_hopper=vol_hop * RHO * 1000 / CONT["shaker-250"]["g"],
               t_cycle=60 / UPM["rated"])
    return out


if __name__ == "__main__":
    c = calcs()
    for k, v in c.items():
        if isinstance(v, dict):
            print(f"{k:12s} " + "  ".join(f"{a}={b:.3g}" for a, b in v.items()))
        else:
            print(f"{k:12s} {v:.4g}")
    print("stage", STAGE_POS, "col L", COL["L"], "PD", PD1, PD2)
