"""TS-2 rev B thermal, airflow, tracing-coil, turbine and electrical sizing.

Reads ../mechanical/cad/params.py; writes calc.json and calc.md next to this file.
First-order models with every correlation named.  Status: CALCULATED, not measured.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mechanical", "cad"))
from params import P  # noqa: E402

R = {"inputs": {}, "gpu": {}, "coil": {}, "air": {}, "turbine": {}, "tec": {}, "elec": {}, "checks": {}, "cases": {}}

# ------------------------------------------------------------------ properties
def air_rho(T):  # kg/m3 at 101.3 kPa
    return 101325.0 / (287.05 * (T + 273.15))

CP_AIR = 1007.0
CP_W, RHO_W, MU_W, K_W, PR_W = 4186.0, 999.0, 1.08e-3, 0.594, 7.6   # water 17-20 C (inhibited, no glycol: 17.5 C supply cannot freeze)


def dew_point(T, RH):  # Magnus, deg C
    a, b = 17.62, 243.12
    g = math.log(RH) + a * T / (b + T)
    return b * g / (a - g)


# ------------------------------------------------------------------ GPU air path
def gpu_path(T_in):
    q = P["GPU_AIR_M3H"] / 3600.0
    m = q * air_rho(T_in)
    dT = P["GPU_TDP"] / (m * CP_AIR)
    return m, dT


# ------------------------------------------------------------------ tracing coil (per column)
def coil(T_air_in, T_w_in, lpm, rows=3, circuits=4, face_w=0.196, face_h=None, v_air=None):
    face_h = face_h or (2 * P["slots_per_group"] * P["SLOT_PITCH"] + P["MID_GAP"]) / 1000.0
    A_face = face_w * face_h
    Q_air = P["gpus_per_column"] * P["GPU_AIR_M3H"] / 3600.0
    v_face = Q_air / A_face
    m_air = Q_air * air_rho(T_air_in)
    C_air = m_air * CP_AIR
    # air side: plate fins 12 FPI, 0.15 mm, row depth 22 mm (3/8 in tube, 25.4 x 22 mm staggered)
    row_depth, fp, ft = 0.022, P["fin_pitch_mm"] / 1000.0, P["fin_t_mm"] / 1000.0
    A_fin = 2.0 * row_depth * A_face / fp * rows
    od = P["trace_tube_od_in"] * 0.0254
    n_tubes_per_row = 4 * P["slots_per_group"]          # two horizontal passes per slot height (25.4 mm tube pitch), per row
    L_tube = face_w * n_tubes_per_row * rows
    A_tube_o = math.pi * od * L_tube * (1 - ft / fp)
    # h_o: Wang, Chi & Chang (2000) plate-fin class result at Re_Dc ~ 900 -> j ~ 0.012
    rho = air_rho(T_air_in)
    sigma = 0.55                                        # min free-flow / frontal area
    G = rho * v_face / sigma
    j = 0.012 * (max(G * od / 1.85e-5, 300) / 900.0) ** -0.35
    h_o = j * G * CP_AIR / 0.71 ** (2.0 / 3.0)
    # fin efficiency (Schmidt equivalent circular fin)
    k_al = 205.0
    mfin = math.sqrt(2 * h_o / (k_al * ft))
    r_e = 0.0254 * 0.5 * 1.27                           # equivalent fin radius
    phi = (r_e / (od / 2) - 1) * (1 + 0.35 * math.log(r_e / (od / 2)))
    eta_f = math.tanh(mfin * (od / 2) * phi) / (mfin * (od / 2) * phi)
    eta_o = 1 - A_fin / (A_fin + A_tube_o) * (1 - eta_f)
    hA_o = h_o * eta_o * (A_fin + A_tube_o)
    # water side: Gnielinski, ID = OD - 2 x 0.032 in
    di = od - 2 * 0.032 * 0.0254
    q_c = lpm / 60000.0 / circuits
    v_w = q_c / (math.pi * di ** 2 / 4)
    Re = RHO_W * v_w * di / MU_W
    f = (0.79 * math.log(Re) - 1.64) ** -2
    Nu = (f / 8) * (Re - 1000) * PR_W / (1 + 12.7 * math.sqrt(f / 8) * (PR_W ** (2 / 3) - 1))
    h_i = Nu * K_W / di
    A_i = math.pi * di * L_tube
    hA_i = h_i * A_i
    UA = 1.0 / (1.0 / hA_o + 1.0 / hA_i + 1.0 / 20000.0)   # wall + fin-collar contact ~ 1/20 kW/K
    C_w = lpm / 60000.0 * RHO_W * CP_W
    Cmin, Cmax = min(C_air, C_w), max(C_air, C_w)
    Cr = Cmin / Cmax
    NTU = UA / Cmin
    # counter-crossflow, >= 3 rows: close to counterflow
    eps = (1 - math.exp(-NTU * (1 - Cr))) / (1 - Cr * math.exp(-NTU * (1 - Cr)))
    Q = eps * Cmin * (T_air_in - T_w_in)
    T_air_out = T_air_in - Q / C_air
    T_w_out = T_w_in + Q / C_w
    # pressure drops
    dp_air = rows * 6.2 * (v_face / 1.0) ** 1.7           # 12 FPI plate fin, ~6 Pa/row at 1 m/s (vendor class data)
    L_c = L_tube / circuits
    n_bends = n_tubes_per_row * rows / circuits - 1
    dp_w = f * L_c / di * RHO_W * v_w ** 2 / 2 + n_bends * 0.9 * RHO_W * v_w ** 2 / 2
    return dict(A_face_m2=round(A_face, 4), v_face_m_s=round(v_face, 3), rows=rows, circuits=circuits,
                A_fin_m2=round(A_fin, 2), A_tube_o_m2=round(A_tube_o, 3), h_o=round(h_o, 1), eta_fin=round(eta_f, 3),
                hA_o_W_K=round(hA_o, 1), v_water_m_s=round(v_w, 3), Re_water=round(Re), h_i=round(h_i), hA_i_W_K=round(hA_i, 1),
                UA_W_K=round(UA, 1), NTU=round(NTU, 3), eps=round(eps, 3), Q_W=round(Q), T_air_out_C=round(T_air_out, 2),
                T_water_out_C=round(T_w_out, 2), dp_air_Pa=round(dp_air, 1), dp_water_kPa=round(dp_w / 1000, 1),
                tube_length_m=round(L_tube, 2), bends_per_circuit=int(n_bends))


# ------------------------------------------------------------------ fan law on the documented 48 V curve
def fan_curve(V):
    k = V / 48.0                                         # EC speed ~ bus voltage at 100 % demand (documented 57 V point: 2325/2000 rpm = 1.16)
    return [(q * k, dp * k * k) for q, dp in P["imp_curve_48V"]]


def fan_q_at(dp, V, demand=1.0):
    pts = sorted(fan_curve(V), key=lambda t: t[1])
    pts = [(q * demand, p * demand * demand) for q, p in pts]
    for (q0, p0), (q1, p1) in zip(pts, pts[1:]):
        if p0 <= dp <= p1:
            return q0 + (q1 - q0) * (dp - p0) / (p1 - p0)
    return 0.0 if dp > pts[-1][1] else pts[0][0]


def run(T_room=P["T_room_design_C"], RH=P["RH_design"], load=1.0, chill=True, tec=True, n_imp_running=3, label=""):
    out = {}
    Tdew = dew_point(T_room, RH)
    Tw = max(P["T_coolant_supply_C"], Tdew + 2.0)
    if chill:
        c = coil(T_room, Tw, P["coolant_lpm_per_column"])
        T_gpu_in = c["T_air_out_C"]
    else:
        c = None
        T_gpu_in = T_room
    m, dT = gpu_path(T_gpu_in)
    dT *= load
    T_gpu_out = T_gpu_in + dT
    # host-node air (plinth arm), TEC hot side (base module), both discharge into the hub -> plenum
    host_W = (P["col_power_W"]["host_node"] + P["col_power_W"]["switch_cards"] + P["col_power_W"]["nic"]) * (0.4 + 0.6 * load)
    q_host = host_W / (air_rho(T_room) * CP_AIR * 15.0)
    tec_cool = P["tec_per_module"] * P["tec_q_each_W"] if tec else 0.0
    tec_in = tec_cool / P["tec_cop_trim"]
    tec_hot = tec_cool + tec_in
    q_tec = tec_hot / (air_rho(T_room) * CP_AIR * 12.0) if tec else 0.0
    nC = P["n_columns"]
    Q_gpu = nC * P["gpus_per_column"] * P["GPU_AIR_M3H"] / 3600.0 * air_rho(T_gpu_in) / air_rho(T_room)
    Q_in = Q_gpu + nC * (q_host + q_tec)                  # m3/s at room density
    H_gpu = nC * P["gpus_per_column"] * P["GPU_TDP"] * load
    H_tot = H_gpu + nC * (host_W + tec_hot + P["col_power_W"]["cbp_backplanes"] + P["col_power_W"]["controls"])
    m_tot = Q_in * air_rho(T_room)
    # energy: air enters at room T, is chilled by Q_coil, then picks up H_tot
    Q_coil = nC * (c["Q_W"] if c else 0.0)
    T_plenum = T_room + (H_tot - Q_coil) / (m_tot * CP_AIR)
    Q_plenum = m_tot / air_rho(T_plenum)
    # chimney + crown losses
    A_ch = math.pi * (P["CHIMNEY_D"] / 1000.0) ** 2 / 4
    v_ch = Q_plenum / A_ch
    L_ch = (P["Z_CHIMNEY1"] - P["Z_CROWN1"]) / 1000.0
    rho_p = air_rho(T_plenum)
    dp_chimney = (0.02 * L_ch / (P["CHIMNEY_D"] / 1000.0) + 1.0) * rho_p * v_ch ** 2 / 2   # friction + exit loss
    dp_crown = 0.6 * rho_p * (Q_plenum / (0.25 * nC * 0.090)) ** 2 / 2                     # 4 bulkhead throats into crown, K 0.6
    stack = 9.81 * (air_rho(T_room) - rho_p) * (P["Z_CHIMNEY1"] - P["Z_SLOT0"]) / 1000.0
    dp_set_plenum = -((c["dp_air_Pa"] if c else 0) + 30.0 + 5.0)                             # coil + filter (MERV 8 at ~1 m/s, 30 Pa clean) + grille
    dp_fan = -dp_set_plenum + dp_chimney + dp_crown - stack
    q_each = Q_plenum * 3600.0 / n_imp_running
    V = 56.0                                             # fan bus: Mean Well RSP-1600-48 trimmed to 56 V (fan range 36-57 V)
    q_avail = fan_q_at(dp_fan, V) if n_imp_running else 0
    demand = None
    for d in [x / 100.0 for x in range(20, 101)]:
        if fan_q_at(dp_fan, V, d) >= q_each:
            demand = d
            break
    out.update(label=label, T_room_C=T_room, RH=RH, T_dew_C=round(Tdew, 2), T_coolant_C=round(Tw, 2), load=load,
               T_gpu_inlet_C=round(T_gpu_in, 2), gpu_air_dT_K=round(dT, 2), T_gpu_exhaust_C=round(T_gpu_out, 2),
               Q_coil_total_W=round(Q_coil), heat_to_air_W=round(H_tot), T_plenum_C=round(T_plenum, 2),
               airflow_in_m3_h=round(Q_in * 3600), airflow_plenum_m3_h=round(Q_plenum * 3600),
               chimney_v_m_s=round(v_ch, 2), dp_chimney_Pa=round(dp_chimney, 1), dp_crown_Pa=round(dp_crown, 1), stack_Pa=round(stack, 1),
               plenum_setpoint_Pa=round(dp_set_plenum, 1), dp_fan_Pa=round(dp_fan, 1), impellers_running=n_imp_running,
               q_per_impeller_m3_h=round(q_each), q_available_at_56V_m3_h=round(q_avail),
               impeller_demand=demand, gpu_core_C_est=round(T_gpu_in + 0.167 * P["GPU_TDP"] * load + 0.0, 1),
               host_air_m3_h_per_col=round(q_host * 3600), tec_hot_W_per_col=round(tec_hot), tec_cool_W_per_col=round(tec_cool))
    if c:
        out["coil"] = c
    return out


DP = run(label="design point: 27 C / 50 %, full load, chilled water + TEC trim, 3 impellers")
R["design_point"] = DP
R["cases"] = {
    "hot_room_35C_40pct": run(35.0, 0.40, label="hot room 35 C / 40 %"),
    "no_chill_27C": run(chill=False, tec=False, label="chiller off, TEC off"),
    "one_impeller_failed": run(n_imp_running=2, label="N+1: one impeller failed"),
    "humid_27C_70pct": run(27.0, 0.70, label="humid room 27 C / 70 % (coolant lifts to dew + 2 K)"),
    "idle_15pct": run(load=0.15, label="idle 15 %"),
}

# ------------------------------------------------------------------ electrical
col = P["col_power_W"]
gpu_12v = col["gpus"] + col["cbp_backplanes"] + col["controls"]
crps_in = gpu_12v / P["crps_eff"]
host_dc = col["host_node"] + col["switch_cards"] + col["nic"]
host_in = host_dc / P["host_psu_eff"]
tec_dc = P["tec_per_module"] * P["tec_q_each_W"] / P["tec_cop_trim"] + 2 * 15 + 25    # TECs + 2 hot-side fans + pump
tec_in = tec_dc / 0.90                                                                  # Mean Well RSP-750-12 ~ 90 %
col_ac = crps_in + host_in + tec_in
imp_W = 3 * 0.55 * 1.35 * P["imp_W_48V"]                                                # 3 fans at ~ 55 % demand (cube law), 54 V
aux_W = imp_W + 150.0 + 30.0                                                            # panel, switches, TMC-1
tower_ac = P["n_columns"] * col_ac + aux_W
per_crps_share = gpu_12v / P["n_crps_per_column"]
per_crps_n1 = gpu_12v / (P["n_crps_per_column"] - 1)
I_line = lambda W: W / (math.sqrt(3) * 208.0)
feedA = 2 * col_ac + aux_W / 2
R["elec"] = dict(col_gpu_12V_W=round(gpu_12v), col_gpu_12V_A=round(gpu_12v / 12.2), crps_share_W=round(per_crps_share),
                 crps_N1_W=round(per_crps_n1), crps_load_N1=round(per_crps_n1 / P["CRPS_W"], 3), col_crps_input_W=round(crps_in),
                 host_input_W=round(host_in), tec_module_input_W=round(tec_in), col_ac_W=round(col_ac), aux_W=round(aux_W),
                 tower_ac_W=round(tower_ac), feed_A_W=round(feedA), feed_A_line_A_balanced=round(I_line(feedA), 1),
                 gpu_channel_A=round(P["GPU_TDP"] / 12.0, 2), gpu_channel_ocp_A=30.0,
                 slot_12V_A=5.5, cbp_input_A=round((col["gpus"] / 2 + 9) / 12.0, 1))

# ------------------------------------------------------------------ checks
c = DP["coil"]
R["checks"] = {
    "gpu_inlet_le_25C": [DP["T_gpu_inlet_C"], 25.0, DP["T_gpu_inlet_C"] <= 25.0],
    "gpu_inlet_hot_room_le_32C": [R["cases"]["hot_room_35C_40pct"]["T_gpu_inlet_C"], 32.0, R["cases"]["hot_room_35C_40pct"]["T_gpu_inlet_C"] <= 32.0],
    "coil_face_velocity_le_2.5": [c["v_face_m_s"], 2.5, c["v_face_m_s"] <= 2.5],
    "coil_surface_above_dew_+2K": [DP["T_coolant_C"] - DP["T_dew_C"], 2.0, DP["T_coolant_C"] - DP["T_dew_C"] >= 1.99],
    "coil_water_dp_le_50kPa": [c["dp_water_kPa"], 50.0, c["dp_water_kPa"] <= 50.0],
    "chimney_velocity_le_10": [DP["chimney_v_m_s"], 10.0, DP["chimney_v_m_s"] <= 10.0],
    "impeller_demand_le_0.85": [DP["impeller_demand"], 0.85, (DP["impeller_demand"] or 9) <= 0.85],
    "impeller_N+1_flow_ge_95pct": [round(R["cases"]["one_impeller_failed"]["q_available_at_56V_m3_h"] / R["cases"]["one_impeller_failed"]["q_per_impeller_m3_h"], 3), 0.95,
                                    R["cases"]["one_impeller_failed"]["q_available_at_56V_m3_h"] / R["cases"]["one_impeller_failed"]["q_per_impeller_m3_h"] >= 0.95],
    "crps_N+1_load_le_0.90": [R["elec"]["crps_load_N1"], 0.90, R["elec"]["crps_load_N1"] <= 0.90],
    "feed_A_le_48A": [R["elec"]["feed_A_line_A_balanced"], 48.0, R["elec"]["feed_A_line_A_balanced"] <= 48.0],
    "plenum_hot_day_le_60C": [R["cases"]["hot_room_35C_40pct"]["T_plenum_C"], 60.0, R["cases"]["hot_room_35C_40pct"]["T_plenum_C"] <= 60.0],
}
R["all_pass"] = all(v[2] for v in R["checks"].values())

json.dump(R, open(os.path.join(HERE, "calc.json"), "w"), indent=1)

# ------------------------------------------------------------------ markdown
L = []
w = L.append
w("# TS-2 rev B: thermal, airflow, tracing coil, turbine and power sizing\n")
w("Generated by `calc.py` from `mechanical/cad/params.py`. Status: **calculated**, not measured. Replace the assumed coil and fan numbers with vendor ratings and a first-article airflow test.\n")
w("## Cooling path (one column)\n")
w("1. Room air enters the outer face through the printed grille and a MERV 8 filter.")
w("2. The **tracing coil** chills it. That is 3 rows of 3/8 in copper serpentine with 12 FPI aluminium fins, 32 passes per row at 25.4 mm tube pitch, and 4 water circuits (2 per 8-GPU group).")
w("3. The chilled air crosses the cable zone and is drawn in by each card's blower through the 10.8 mm gap above its shroud (50.8 mm slot pitch).")
w("4. The blower pushes it through the card heat sink and out the bracket vents. The exhaust passes through a window in the exhaust bulkhead into the central plenum.")
w("5. The crown turbine (3 x ebm-papst R3G310 EC impellers, N+1, on a 56 V bus) holds the plenum below the column interior, so the cards never fight back-pressure. It sends the heat up the 18 in chimney.")
w("6. Host-node air (plinth arms) and the base Peltier hot sides discharge into the hub and join the plenum. None of that heat is released back into the room at intake height.\n")
w("## Design point (27 C, 50 % RH, full load)\n")
w("| Quantity | Value |")
w("|---|---|")
for k, lab in [("T_dew_C", "Room dew point, C"), ("T_coolant_C", "Coolant supply (dew + 2 K floor), C"), ("T_gpu_inlet_C", "GPU inlet after tracing, C"),
               ("gpu_air_dT_K", "Air rise through each GPU, K"), ("T_gpu_exhaust_C", "GPU exhaust, C"), ("gpu_core_C_est", "GPU core estimate (0.167 K/W blower), C"),
               ("Q_coil_total_W", "Tracing coil duty, all 4 columns, W"), ("heat_to_air_W", "Heat into the air stream, W"), ("T_plenum_C", "Plenum, C"),
               ("airflow_in_m3_h", "Air drawn from the room, m3/h"), ("airflow_plenum_m3_h", "Air through the turbine, m3/h"),
               ("plenum_setpoint_Pa", "Plenum set point vs room, Pa"), ("dp_fan_Pa", "Impeller static pressure, Pa"),
               ("q_per_impeller_m3_h", "Flow per impeller, m3/h"), ("impeller_demand", "Impeller demand at 56 V"), ("chimney_v_m_s", "Chimney velocity, m/s")]:
    w(f"| {lab} | {DP[k]} |")
w("\n## Tracing coil, per column\n")
w("| Quantity | Value |")
w("|---|---|")
for k, v in DP["coil"].items():
    w(f"| {k} | {v} |")
w("\nCorrelations used:")
w("- Air side: Wang, Chi and Chang (2000) plate-fin j-factor class, with Schmidt fin efficiency.")
w("- Water side: Gnielinski.")
w("- Effectiveness: counterflow for at least 3 rows.")
w("- Pressure drop: Darcy plus 0.9 velocity heads per return bend.")
w("\n## Cases\n")
w("| Case | GPU inlet C | GPU core est C | Plenum C | Coil kW | Impeller demand |")
w("|---|---|---|---|---|---|")
for k, cse in [("design", DP)] + list(R["cases"].items()):
    w(f"| {cse['label']} | {cse['T_gpu_inlet_C']} | {cse['gpu_core_C_est']} | {cse['T_plenum_C']} | {round(cse['Q_coil_total_W']/1000, 2)} | {cse['impeller_demand']} |")
w("\n## Electrical\n")
w("| Quantity | Value |")
w("|---|---|")
for k, v in R["elec"].items():
    w(f"| {k} | {v} |")
w("\n## Checks\n")
w("| Check | Value | Limit | Result |")
w("|---|---|---|---|")
for k, (v, lim, ok) in R["checks"].items():
    w(f"| {k} | {v} | {lim} | {'PASS' if ok else 'FAIL'} |")
w("\n## Honest reading\n")
w("- The base Peltier modules are **trim only**: 4 x 110 W of cooling per column against about 1.6 kW of coil duty. Their real job is closing the last 1 to 2 K and holding the coolant above dew point when the chiller cycles. The main chilling is the 17.5 C water loop from a 2-ton-class chiller or building chilled water through a plate heat exchanger.")
w("- The coil surface never goes below dew point + 2 K, so it runs dry. A drip tray is still fitted under each coil for the humid-day case, where CCM-1 raises the coolant set point.")
w("- With one impeller failed, the other two at 100 % give about 99 % of the design plenum flow. The GPU blowers carry the remainder, and the plenum set point relaxes by a few pascals. CCM-1 and TMC-1 raise an alarm but do not throttle.")
w("- The GPU core estimate uses a generic blower-card resistance. NVIDIA's real fan curve and slowdown behaviour replace it at first article.")
open(os.path.join(HERE, "calc.md"), "w").write("\n".join(L) + "\n")
print(json.dumps({k: DP[k] for k in ("T_gpu_inlet_C", "T_plenum_C", "airflow_plenum_m3_h", "dp_fan_Pa", "impeller_demand", "Q_coil_total_W", "chimney_v_m_s")}, indent=0))
print(json.dumps(DP["coil"]))
print(json.dumps(R["elec"]))
print({k: v for k, v in R["checks"].items()}, R["all_pass"])
for k, v in R["cases"].items():
    print(k, v["T_gpu_inlet_C"], v["T_plenum_C"], v["impeller_demand"], v["q_per_impeller_m3_h"], v["dp_fan_Pa"])
