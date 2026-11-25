"""TS-2 rev B (64-GPU column tower): single source of truth for geometry, loads and thermal inputs.

Units: mm, kg, W, s unless noted.  Global frame: Z up, floor at z = 0, tower axis on Z.
Columns C1..C4 sit at azimuth 0, 90, 180, 270 deg.  Column local frame: u = radial outward,
v = tangential (v = z x u), z = up.  global = Rz(90*(c-1)) * local.

GPU orientation inside a column (the core of rev B):
  * cards lie FLAT, stacked in z at SLOT_PITCH; 2 groups of 8 per column (lower L, upper U)
  * the card's bracket (I/O) end faces the central plenum (u = R_BULK) -> blower exhaust goes
    straight into the plenum and up the turbine chimney
  * the card's tail faces the outer intake face, where the chilled tracing coil sits
  * the gold fingers run along u at the v- side, plugged into the vertical column backplane CBP-8

Tags: [D] documented (datasheet / standard), [I] inferred, [A] assumed design choice, [V] verify on first article.
Run this file to write ../../design_basis.json.
"""
import json
import math
import os

P = {}
P["rev"] = "B"

# ---------------------------------------------------------------- architecture
P["n_columns"] = 4                     # [A] cruciform, from concept + user render 2026-11-22
P["gpus_per_column"] = 16              # user requirement 2026-11-22 ("16 GPUs per column")
P["groups_per_column"] = 2             # [A] two 8-slot groups; one CBP-8 backplane + one hold-down per group
P["slots_per_group"] = 8
P["n_gpus"] = P["n_columns"] * P["gpus_per_column"]   # 64
P["pcie_link"] = "PCIe x8 per GPU at Gen4 (16 GT/s) over one Gen5-rated MCIO 8i cable (SFF-TA-1016), 4 GPUs per host switch card"

# ---------------------------------------------------------------- GPU (bought)  [D] parts research 2026-11-22
P["GPU"] = "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition 96 GB (PNY VCNRTXPRO6000BQ-PB)"
P["GPU_L"] = 267.0                     # [D] bracket face to tail
P["GPU_H"] = 111.8                     # [D] 112 mm incl. fingers (CEM full height 111.15 + shroud lip)
P["GPU_T"] = 40.0                      # [D] dual slot
P["GPU_TDP"] = 300.0                   # [D] total board power
P["GPU_MASS"] = 1.45                   # [I] blower dual-slot class
P["GPU_FINGER_U0"] = 41.9              # [D/V] bracket datum to first x16 finger (PCI-SIG CEM 5.x add-in card drawing)
P["GPU_FINGER_L"] = 89.0               # [D] x16 finger length (164 contacts at 1.0 mm in two halves)
P["GPU_PWR_U"] = 267.0                 # [D] 12V-2x6 at the "east edge" (tail end), NVIDIA QSG
P["GPU_PWR_V"] = 55.0                  # [V] 12V-2x6 position up the tail edge from the finger edge
P["GPU_AIR_M3H"] = 50.0                # [I] blower flow at TDP (Max-Q class 25-32 CFM); 50 m3/h = 29.4 CFM
P["GPU_TJ_MAX"] = 90.0                 # [I] slowdown class

# ---------------------------------------------------------------- column envelope (local frame)
P["R_PLENUM"] = 200.0                  # plenum boundary = inner face of the exhaust bulkhead
P["BULK_T"] = 3.0                      # exhaust bulkhead 6061-T6 3.0 mm (carries 8 bracket tabs + hold-down hinge)
P["R_BULK"] = P["R_PLENUM"] + P["BULK_T"]   # card bracket seats on this face
P["R_CARD_TAIL"] = P["R_BULK"] + P["GPU_L"]   # 470
P["R_CABLE"] = P["R_CARD_TAIL"] + 38.0       # 12V-2x6 plug + 25 mm bend radius zone (NVIDIA: 30-35 mm)
P["POST"] = 30.0                       # [D] Misumi HFS6-3030 slot-6 extrusion posts, 4 per column
P["R_POST_IN"] = (P["R_BULK"], P["R_BULK"] + 30.0)
P["R_POST_OUT"] = (P["R_CABLE"], P["R_CABLE"] + 30.0)
P["TRACE_DEPTH"] = 66.0                # tracing coil depth (3 rows x 22 mm, 3/8 in tube + 12 FPI fins)
P["R_TRACE0"] = P["R_POST_OUT"][1] + 2.0
P["R_TRACE1"] = P["R_TRACE0"] + P["TRACE_DEPTH"]
P["R_OUT"] = P["R_TRACE1"] + 24.0      # MERV 8 filter 12 mm + printed grille 12 mm
P["HALF_W"] = 100.0                    # column width 200 (v -100..+100); cards centred on the radial axis
P["POST_V"] = (70.0, 100.0)            # posts occupy |v| 70..100 at the inner and outer corners
P["V_BP"] = -62.0                      # backplane PCB component face (+v side) plane; rear cable/busbar channel v -100..-64.4
P["BP_T"] = 2.0                        # CBP-8 thickness, 8-layer Megtron 6 (electrical/boards/cbp8)
P["CEM_H"] = 11.25                     # [D] PCIe vertical x16 connector body height above PCB
P["CARD_V0"] = P["V_BP"] + 6.6         # card finger bottom edge (connector seating depth: 11.25 - 4.65)
P["CARD_V1"] = P["CARD_V0"] + P["GPU_H"]

# ---------------------------------------------------------------- column heights
P["Z_DECK"] = 400.0                    # top of plinth deck
P["Z_COL0"] = 400.0                    # column base plate bottom
P["BASE_T"] = 12.0                     # column base plate 6061-T6 12 mm
P["SLOT_PITCH"] = 50.8                 # [A] 2.5 x 20.32: 10.8 mm air gap over each blower intake
P["Z_SLOT0"] = 452.0                   # bottom face of the first (lowest) card shroud, lower group
P["MID_GAP"] = 60.0                    # midspan crossmember band (red latch handles + light bar)
P["Z_GROUP"] = [P["Z_SLOT0"], P["Z_SLOT0"] + 8 * P["SLOT_PITCH"] + P["MID_GAP"]]
P["Z_COL1"] = P["Z_GROUP"][1] + 8 * P["SLOT_PITCH"] + 40.0   # top plate bottom
P["TOP_T"] = 10.0
P["Z_CROWN0"] = P["Z_COL1"] + P["TOP_T"]
P["CROWN_H"] = 260.0
P["Z_CROWN1"] = P["Z_CROWN0"] + P["CROWN_H"]
P["CHIMNEY_D"] = 457.2                 # [D] 18 in round spiral duct
P["Z_CHIMNEY1"] = 2300.0

# ---------------------------------------------------------------- plinth + host node
P["Z_PLINTH0"] = 95.0                  # leveling caster plate height [D/V]
P["ARM_HALF_W"] = 165.0
P["ARM_R0"] = 200.0
P["ARM_R1"] = 920.0                     # arm nose: CRPS AC inlets face out here (hot-swap from outside)
P["HUB_R"] = 260.0
P["HOST_BOARD"] = "ASRock Rack ROMED8-2T (ATX 305 x 244) + EPYC 7543P + 8x 32 GB RDIMM"   # carried from rev A, [D]
P["HOST_SWITCH"] = "HighPoint Rocket 1628A (Broadcom PEX89048, x16 Gen5 host, 4x MCIO 8i x8)"   # [D] datasheet v1.01; GPU use [V]
P["SWITCH_CARDS_PER_HOST"] = 4
P["HOST_NIC"] = "NVIDIA ConnectX-6 Dx 2x100GbE (MCX623106AN-CDAT)"   # [I]

# ---------------------------------------------------------------- loads per column [I]/[D]
P["col_power_W"] = {
    "gpus": 16 * 300.0,
    "cbp_backplanes": 2 * 18.0,        # eFuse losses 8 x 25 A^2 x 0.6 mOhm + logic
    "host_node": 225.0 + 40.0 + 45.0 + 16.0 + 6.0,   # CPU, DIMMs, board/BMC, NVMe, cooler fan
    "switch_cards": 4 * 16.26,         # [D] Rocket 1628A 16.26 W
    "nic": 22.0,
    "controls": 12.0,                  # CCM-1 + sensors + light bar
}
P["crps_eff"] = 0.94                   # [D] Murata D1U54 94 % at 50 % load, 230 V
P["host_psu_eff"] = 0.92
P["n_crps_per_column"] = 4             # 3 + 1 redundant, 2000 W each at 200-240 V [D]
P["CRPS"] = "Murata D1U54T-W-2000-12-HC4TC (CRPS 2000 W 12 V 166.7 A)"
P["CRPS_W"] = 2000.0

# ---------------------------------------------------------------- turbine (crown)
P["n_impellers"] = 2
P["IMPELLER"] = "ebm-papst R3G310-AN12-30, 48 VDC EC, 0-10 V / PWM, tach"
P["imp_curve_48V"] = [[2275, 0], [1840, 200], [1395, 350], [925, 450]]   # [D] (m3/h, Pa) datasheet
P["imp_W_48V"] = 190.0                 # [D]
P["imp_mass"] = 4.4                    # [D]

# ---------------------------------------------------------------- tracing + chiller + TEC trim
P["T_room_design_C"] = 27.0            # [D] ASHRAE A1 recommended upper bound
P["T_room_max_C"] = 35.0               # [D] ASHRAE A2 allowable
P["RH_design"] = 0.50
P["coolant"] = "inhibited water (supply never below 15 C, so no glycol; glycol would push the tube side laminar)"
P["T_coolant_supply_C"] = 17.5         # [A] held >= dew point + 2 K by CCM-1 (dew point 15.8 C at 27 C / 50 %)
P["coolant_lpm_per_column"] = 6.0
P["trace_tube_od_in"] = 0.375          # 3/8 in OD copper, 0.032 wall (ASTM B75 C12200)
P["trace_rows"] = 2
P["trace_passes"] = 32                 # horizontal passes per row, 25.4 mm tube pitch (2 per slot)
P["trace_circuits"] = 4               # 2 per 8-GPU group, each 16 passes x 3 rows
P["fin_pitch_mm"] = 2.1                # 12 FPI aluminium plate fins 0.15 mm
P["fin_t_mm"] = 0.15
P["TEC"] = "TE Technology / Laird class 62 x 62 mm, Qmax ~ 230 W, Imax 21 A (see bom)"
P["tec_per_module"] = 4
P["tec_cop_trim"] = 0.9                # [I] at dT ~ 12 K across the TEC (cold 15 C, hot 27 C)
P["tec_q_each_W"] = 110.0              # [I] operating point at ~ 55 % Imax
P["chiller"] = "air-cooled process chiller, >= 7.5 kW at 17 C LWT (2-ton class), or building CHW via plate HX"

# ---------------------------------------------------------------- electrical service
P["supply"] = "2x 208Y/120 V 3-phase 60 A feeds (A: C1+C2, B: C3+C4), IEC 60309 460P9W inlets"
P["feed_A_cont_limit"] = 48.0

# ---------------------------------------------------------------- livery (kept from rev A)
P["livery"] = {
    "body": "#c9ccd1", "base": "#141416", "accent": "#c8102e", "grille": "#2a2b2e",
}


def col_angle(c):
    return math.radians(90.0 * c)


def slot_z(group, i):
    """Bottom face of card shroud for slot i (0..7) in group (0 lower, 1 upper)."""
    return P["Z_GROUP"][group] + i * P["SLOT_PITCH"]


def col_dc_W():
    return sum(P["col_power_W"].values())


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "design_basis.json")
    d = dict(P)
    d["col_dc_W"] = col_dc_W()
    json.dump(d, open(out, "w"), indent=1)
    print("wrote", os.path.abspath(out))
    for k in ("R_CARD_TAIL", "R_CABLE", "R_TRACE0", "R_TRACE1", "R_OUT", "Z_GROUP", "Z_COL1", "Z_CROWN0", "Z_CROWN1", "CARD_V0", "CARD_V1"):
        print(k, P[k])
    print("column DC", col_dc_W())
