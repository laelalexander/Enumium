"""AON-1 3U CubeSat: design basis. Every number the CAD, drawings, BOM and firmware use comes from here.

Run:  python design.py   -> writes design-basis.json and design-basis.md (budgets: mass, power, link, orbit life, deploy timeline)

Tags in the text: [req] requirement, [calc] calculated here, [est] engineering estimate, [ds] datasheet value (confirm on the
datasheet before ordering), [asm] design choice.
Frame: +Z is the antenna end (top), -Z the dispenser pusher end. Origin: XY on the long axis, Z = 0 at the -Z rail end.
"""
import json
import math
import pathlib

HERE = pathlib.Path(__file__).parent

# ------------------------------------------------------------------ envelope (AON dispenser ICD, built to CDS rev 14.1 3U numbers)
ENV = dict(
    w=100.0, w_tol=0.1,            # rail outer face to rail outer face, X and Y [req CDS 3U]
    L=340.5, L_tol=0.3,            # rail end to rail end [req CDS 3U]
    rail=8.5,                      # rail square [req >= 8.5 contact width]
    rail_r=1.0,                    # rail long-edge radius [req >= 1 mm]
    protrude=6.5,                  # max protrusion beyond the rail plane on +-X/+-Y [req]
    m_max=6.0,                     # 3U mass limit [req CDS rev 14.1], design target below
    m_target=4.0,                  # program target from the decision card (about 4 kg)
    cg_xy=20.0, cg_z=70.0,         # CG box from geometric centre [req]
)
HALF = ENV["w"] / 2                # 50
RI = HALF - ENV["rail"]            # 41.5 rail inner face

# ------------------------------------------------------------------ frames (3 identical-section machined rings: -Z, mid, +Z)
FR = dict(
    t=10.0,                        # frame thickness along Z (two crossing M2.5 screws per corner, offset +-2.25 in Z)
    bar_x0=42.0, bar_x1=48.0,      # bar section (x for the +X bar): outer face recessed 2.0 from the rail plane for the panels
    blk=9.5,                       # corner block square, x and y from 32.5 to 42.0 (joins the X and Y bars)
    relief=1.5,                    # relief square at the block's outer corner (40.5-42.0) clears the rail inner edge
    z=[6.5, 165.25, 321.0],        # frame -Z faces: -Z frame (6.5-16.5), mid frame (centred on 170.25), +Z frame (321-331, leaves 9.5 for the +Z spring plunger bores)
)
FR["blk0"] = FR["bar_x0"] - FR["blk"]   # 32.5
Z_MID = ENV["L"] / 2               # 170.25
FR["z"][1] = Z_MID - FR["t"] / 2
FR["dz_screw"] = 2.25              # the X-direction and Y-direction rail screws sit at frame mid -2.25 / +2.25 so they cannot cross

# fasteners frame -> rail: M2.5 countersunk (ISO 14581, Torx, A4-70) through the rail outer face into a tapped hole in each bar end
RAIL_SCREW = dict(d=2.5, L=14.0, csk_d=4.7, csk_ang=90.0, tap_depth=8.0, torque_Nm=0.45, bar_mid=(FR["bar_x0"] + FR["bar_x1"]) / 2)

# ------------------------------------------------------------------ AON board standard (in-house, not PC/104: rails are solid 8.5 mm)
BRD = dict(w=81.0, t=1.6, hole=3.2, hp=36.5, corner_ch=3.0)   # 81 x 81 boards, Ø3.2 holes on a 73.0 square
STACK_ROD = dict(thread="M3", mat="Ti-6Al-4V grade 5", d=3.0)

# stack: (board id, name, z of the board's bottom face). Spacers fill the gaps; heights are the tallest part on the top side.
STACK = [
    ("E02", "Battery board (2S2P 18650)", 22.0, 44.0),     # id, name, z bottom face, height above board incl. cells and holder
    ("E01", "EPS (MPPT, regulators, switches)", 80.0, 12.0),
    ("E03", "OBC + ADCS (EOR-1 flight computer)", 108.0, 12.0),
    ("E04", "COM UHF transceiver", 186.0, 14.0),
]
PAYLOAD_BAY = (215.0, 318.0)       # free volume above COM for the next payload (camera, S-band, second radio) [asm]

# ------------------------------------------------------------------ outer boards
PANEL = dict(w=82.0, t=1.6, z0=7.5, z1=330.0, hole_y=34.0, hole_d=2.2)  # +-X/+-Y solar panels on the frame bars (x = 48.0 to 49.6): 4 x M2 at the ends, bonded pad on the mid frame
PANEL["L"] = PANEL["z1"] - PANEL["z0"]
CELL = dict(name="Azur Space 3G30C-Advanced 80x40 mm (TJ GaInP/GaAs/Ge, 30 % class)", l=80.0, w=40.0, t=0.15 + 0.10 + 0.05,   # cell + CMX cover glass + adhesive [ds]
            area_cm2=30.18, eff_bol=0.30, vmp=2.41, imp=0.504, voc=2.70, isc=0.520, mass_g=2.6, n_per_face=7)
GAP_CELL = 1.2
CELL_Z0 = 18.0                     # first cell edge (clear of the -Z screw heads at z 11.5); 7 cells end at 305.2, sun sensor + thermistor zone 306-318
SPRING = dict(thread="M3", depth=9.0, protrude=2.0)   # +Z separation spring plungers in 2 rails (diagonal +x-y, -x+y)
SWITCH = dict(notch_w=2.0, notch_d=4.5, notch_h=6.5, protrude=1.5,
              body=(5.8, 12.8, 6.5), tap_y=(17.0, 23.0), leg_x=41.1, t=1.0)   # D2F body W x L x H [ds]; bracket AON-106 taps on the bar underside  # -Z deployment switches: lever through a notch in 2 rails (+x+y, -x-y)
ROD = dict(z0=3.0, z1=335.0)        # stack rods: through the -Z frame (tapped M3 thru), thin nut under E07; hex standoff H7 on the +Z frame top
END_PANEL = dict(w=81.0, t=1.6)    # -Z end board E07 and +Z antenna board E05 (81 x 81, corner chamfers clear the rails)

# ------------------------------------------------------------------ mass list: (item, qty, unit mass g, basis)
MASS_BOUGHT = [
    ("Solar cells 3G30C incl. cover glass (28)", 28, 2.6, "ds"),
    ("Li-ion 18650 cells LG INR18650 MJ1 (4)", 4, 47.0, "ds"),
    ("Battery holder + straps + heater", 1, 38.0, "est"),
    ("E01 EPS PCBA", 1, 62.0, "est"),
    ("E02 battery PCBA (without cells)", 1, 48.0, "est"),
    ("E03 OBC/ADCS PCBA", 1, 55.0, "est"),
    ("E04 COM PCBA incl. shield can", 1, 85.0, "est"),
    ("E05 antenna board + 2 tape elements + burn resistors", 1, 70.0, "est"),
    ("E06 solar panel substrate PCBA (4) without cells", 4, 72.0, "est"),
    ("E07 -Z end board (Z torquer, sun sensor)", 1, 60.0, "est"),
    ("Stack rods, spacers, nuts", 1, 64.0, "est"),
    ("Harness (connectors, wire)", 1, 55.0, "est"),
    ("Deployment switches (2) + separation spring plungers (2)", 1, 22.0, "ds"),
    ("Fasteners", 1, 30.0, "est"),
    ("Thermal (tape, MLI patch on battery)", 1, 25.0, "est"),
]
MARGIN_MASS = 0.20                 # system margin at concept/PDR level [asm]

# ------------------------------------------------------------------ power
ORBIT = dict(h=500.0, inc=97.4, note="sun-synchronous ~97.4° if the AODV-1 trajectory allows, else the launch-site latitude; 500 km circular [asm]")
RE, MU = 6378.137, 398600.4418
SOLAR = 1361.0                     # W/m2 AM0
LOADS = [  # (load, W when on, duty) [est from the parts' datasheets: confirm at board bring-up]
    ("OBC STM32H743 + FRAM + NOR + sensors", 0.45, 1.0),
    ("EPS quiescent (MPPT, regulators, monitors)", 0.20, 1.0),
    ("COM receiver (always listening)", 0.24, 1.0),
    ("COM transmit beacon 2 W RF (1 s every 30 s)", 6.5, 1 / 30),
    ("COM transmit pass downlink (3 passes x 6 min/day)", 6.5, 18 / 1440),
    ("ADCS magnetorquers (B-dot / pointing, average)", 0.35, 0.5),
    ("Battery heater (cold case, thermostat duty)", 2.0, 0.10),
    ("Payload bay reserve", 0.50, 0.5),
]
BATT = dict(cells="2S2P LG INR18650 MJ1", cell_ah=3.5, cell_v=3.635, s=2, p=2, dod_max=0.20)
DEGR = dict(temp=0.90, uv_rad=0.95, pointing_misc=0.92, mppt=0.93)

# ------------------------------------------------------------------ link (UHF, both ways)
LINK = dict(f_hz=401.5e6, rate_bps=9600, mod="GMSK BT 0.5 (G3RUH-compatible framing replaced by CCSDS TM/TC, see firmware)",
            sat_tx_dbm=33.0, sat_line_db=-1.0, sat_ant_dbi=0.0, gs_ant_dbi=15.5, gs_pol_db=-3.0, gs_line_db=-1.5,
            gs_tsys_k=550.0, atm_db=-1.0, point_db=-1.0, req_ebn0_db=10.6, impl_db=-2.0,
            gs_tx_dbm=47.0, sat_tsys_k=900.0, el_min=10.0,
            band_note="Frequency is a placeholder in the 400.15-403 MHz space operation band: final frequency comes from the FCC/ITU filing (50-certification-path.md). Amateur 435-438 MHz is not usable for a commercial messaging mission.")

# ------------------------------------------------------------------ deploy timeline (CDS + Ambient range safety)
DEPLOY = dict(t_antenna_s=30 * 60, t_rf_s=45 * 60, burn_on_s=6.0, burn_retries=4, burn_current_a=1.0, burn_r_ohm=4.7,
              rbf_inhibits=["deployment switch SW1 (-Z rail end, battery minus)", "deployment switch SW2 (-Z rail end, battery plus)",
                            "remove-before-flight pin RBF1 (solar + battery path)"],
              rf_inhibits=["SW1/SW2 (no battery to COM until deployed)", "EPS COM load switch, enabled by OBC only after t_rf",
                           "COM PA enable line, separate GPIO with its own 45 min hardware timer (TPL5111 on E04)"])


# ================================================================== budgets
def orbit():
    a = RE + ORBIT["h"]
    T = 2 * math.pi * math.sqrt(a ** 3 / MU)
    beta0 = math.asin(RE / a)                     # eclipse half-angle at beta = 0 (worst)
    ecl = T * beta0 / math.pi
    v = math.sqrt(MU / a)
    return dict(a_km=a, period_min=T / 60, eclipse_max_min=ecl / 60, sun_frac_min=1 - ecl / T, v_kms=v)


def slant(h, el):
    e = math.radians(el)
    return math.sqrt((RE + h) ** 2 - (RE * math.cos(e)) ** 2) - RE * math.sin(e)


def power():
    o = orbit()
    total_cell = 4 * CELL["n_per_face"] * CELL["area_cm2"] * 1e-4
    face_cell = CELL["n_per_face"] * CELL["area_cm2"] * 1e-4
    k = DEGR["temp"] * DEGR["uv_rad"] * DEGR["pointing_misc"] * DEGR["mppt"]
    p_face = face_cell * SOLAR * CELL["eff_bol"] * k
    # tumbling: long faces only, average projected cell area of 4 faces around the long axis with random spin axis ~ total/4 * 0.79 (end faces have no cells)
    tumble_proj = total_cell / 4 * (math.pi / 4)
    p_tumble = tumble_proj * SOLAR * CELL["eff_bol"] * k
    # spin about Z with sun normal to Z (best): projected = face * (2*sqrt2 / pi) * ... average |cos| over 4 faces = 4 * face * (1/pi)
    p_spin = 4 * face_cell / math.pi * SOLAR * CELL["eff_bol"] * k
    load = sum(w * d for _, w, d in LOADS)
    gen_t = p_tumble * o["sun_frac_min"]
    gen_s = p_spin * o["sun_frac_min"]
    e_wh = BATT["cell_ah"] * BATT["cell_v"] * BATT["s"] * BATT["p"]
    ecl_wh = load * o["eclipse_max_min"] / 60
    return dict(face_peak_W=p_face, tumble_sun_W=p_tumble, spin_sun_W=p_spin, orbit_avg_gen_tumble_W=gen_t, orbit_avg_gen_spin_W=gen_s,
                orbit_avg_load_W=load, margin_tumble=gen_t / load - 1, margin_spin=gen_s / load - 1, batt_Wh=e_wh,
                eclipse_Wh=ecl_wh, dod_eclipse=ecl_wh / e_wh, string_vmp=CELL["vmp"] * CELL["n_per_face"], string_voc_cold=CELL["voc"] * CELL["n_per_face"] * 1.08,
                loads=[dict(load=n, W=w, duty=d, avg_W=w * d) for n, w, d in LOADS])


def link():
    L = LINK
    d_km = slant(ORBIT["h"], L["el_min"])
    fspl = 20 * math.log10(d_km * 1e3) + 20 * math.log10(L["f_hz"]) - 147.55
    k = -228.6
    rate = 10 * math.log10(L["rate_bps"])
    eirp = L["sat_tx_dbm"] - 30 + L["sat_line_db"] + L["sat_ant_dbi"]
    gt = L["gs_ant_dbi"] + L["gs_pol_db"] + L["gs_line_db"] - 10 * math.log10(L["gs_tsys_k"])
    dl_ebn0 = eirp - fspl + L["atm_db"] + L["point_db"] + gt - k - rate
    eirp_up = L["gs_tx_dbm"] - 30 + L["gs_ant_dbi"] + L["gs_line_db"]
    gt_up = L["sat_ant_dbi"] + L["sat_line_db"] - 3.0 - 10 * math.log10(L["sat_tsys_k"])
    ul_ebn0 = eirp_up - fspl + L["atm_db"] + L["point_db"] + gt_up - k - rate
    return dict(slant_km=d_km, fspl_dB=fspl, dl_ebn0_dB=dl_ebn0, dl_margin_dB=dl_ebn0 - L["req_ebn0_db"] + L["impl_db"],
                ul_ebn0_dB=ul_ebn0, ul_margin_dB=ul_ebn0 - L["req_ebn0_db"] + L["impl_db"],
                bits_per_day=3 * 6 * 60 * L["rate_bps"] * 0.7)


def lifetime(m_kg):
    """Orbit decay from 500 km with a simple exponential atmosphere (moderate solar activity). [est] Replace with a STK/DAS run for the FCC filing."""
    # density table (kg/m3) moderate solar flux, from US Std 1976 / CIRA mid: h(km) -> rho
    tab = [(300, 2.4e-11), (350, 9.5e-12), (400, 3.7e-12), (450, 1.6e-12), (500, 6.9e-13), (550, 3.1e-13)]

    def rho(h):
        for (h0, r0), (h1, r1) in zip(tab, tab[1:]):
            if h0 <= h <= h1:
                return r0 * (r1 / r0) ** ((h - h0) / (h1 - h0))
        return tab[0][1] if h < 300 else tab[-1][1]
    cd, area = 2.2, 0.1 * 0.34 * 0.6 + 0.01 * 0.4     # random tumble average area m2 [est]
    h, t = ORBIT["h"], 0.0
    dt = 86400.0
    while h > 180 and t < 40 * 365 * 86400:
        a = (RE + h) * 1e3
        dadt = -math.sqrt(MU * 1e9 * a) * rho(h) * cd * area / m_kg
        h += dadt * dt / 1e3
        t += dt
    return t / 86400 / 365.25


def mass(structure_g):
    rows = [(n, q, g, q * g, b) for n, q, g, b in MASS_BOUGHT]
    bought = sum(r[3] for r in rows)
    cbe = bought + structure_g
    return dict(rows=rows, structure_g=structure_g, bought_g=bought, cbe_g=cbe, with_margin_g=cbe * (1 + MARGIN_MASS))


def run(structure_g=None):
    sp = HERE.parent / "cad" / "structure_kg.json"
    if structure_g is None:
        structure_g = json.loads(sp.read_text())["total_kg"] * 1000 if sp.exists() else 520.0
    m = mass(structure_g)
    out = dict(env=ENV, frames=FR, board=BRD, stack=STACK, panel=PANEL, cell=CELL, orbit=dict(ORBIT, **orbit()), power=power(), link=link(),
               mass=m, life_years=lifetime(m["with_margin_g"] / 1000), deploy=DEPLOY)
    (HERE / "design-basis.json").write_text(json.dumps(out, indent=1, default=str))
    return out


def report(d):
    p, l, m, o = d["power"], d["link"], d["mass"], d["orbit"]
    L = ["# AON-1 design basis (generated by design/design.py)", "",
         "3U CubeSat, 100.0 x 100.0 x 340.5 mm [3.937 x 3.937 x 13.406 in] on four 8.5 mm hard-anodised 6061-T6 rails. "
         "Launched from Ambient's own AODV-1 dispenser (built to CubeSat Design Specification rev 14.1 3U numbers so a commercial rideshare dispenser also fits).", "",
         "## Orbit [asm/calc]",
         f"- {ORBIT['h']:.0f} km circular, {ORBIT['note']}",
         f"- Period {o['period_min']:.1f} min, worst eclipse {o['eclipse_max_min']:.1f} min, sunlit fraction ≥ {o['sun_frac_min'] * 100:.0f} %",
         f"- Natural decay to re-entry ≈ {d['life_years']:.1f} years at {m['with_margin_g'] / 1000:.2f} kg (simple exponential atmosphere, moderate solar activity [est]); FCC 5-year rule: "
         + ("met" if d["life_years"] <= 5 else "NOT met at this altitude: lower the orbit or add drag sail"), "",
         "## Mass [calc + est]",
         "| Item | Qty | Unit g | Total g | Basis |", "|---|---|---|---|---|",
         *[f"| {n} | {q} | {g:.1f} | {t:.0f} | {b} |" for n, q, g, t, b in m["rows"]],
         f"| Structure (rails, frames, from the CAD volumes x 2.70 g/cm³) | 1 | | {m['structure_g']:.0f} | calc |",
         f"| **Current best estimate** | | | **{m['cbe_g']:.0f}** | |",
         f"| **With {MARGIN_MASS * 100:.0f} % margin** | | | **{m['with_margin_g']:.0f}** | limit {ENV['m_max'] * 1000:.0f} g, target {ENV['m_target'] * 1000:.0f} g |", "",
         "## Power [calc]",
         f"- 7 cells per long face in series: string Vmp {p['string_vmp']:.1f} V, Voc at -40 °C ≈ {p['string_voc_cold']:.1f} V; one face in full sun ≈ {p['face_peak_W']:.1f} W after losses",
         f"- Orbit-average generation: tumbling {p['orbit_avg_gen_tumble_W']:.2f} W, spinning about Z with the sun broadside {p['orbit_avg_gen_spin_W']:.2f} W",
         f"- Orbit-average load {p['orbit_avg_load_W']:.2f} W  ->  margin {p['margin_tumble'] * 100:.0f} % tumbling, {p['margin_spin'] * 100:.0f} % spinning",
         f"- Battery 2S2P 18650: {p['batt_Wh']:.1f} Wh; worst eclipse uses {p['eclipse_Wh']:.2f} Wh = {p['dod_eclipse'] * 100:.1f} % depth of discharge", "",
         "| Load | W on | Duty | Avg W |", "|---|---|---|---|",
         *[f"| {r['load']} | {r['W']:.2f} | {r['duty']:.3f} | {r['avg_W']:.3f} |" for r in p["loads"]], "",
         "## UHF link [calc]",
         f"- {LINK['f_hz'] / 1e6:.1f} MHz placeholder, {LINK['rate_bps']} bit/s {LINK['mod']}",
         f"- Worst case at {LINK['el_min']:.0f}° elevation: slant range {l['slant_km']:.0f} km, path loss {l['fspl_dB']:.1f} dB",
         f"- Downlink (2 W, dipole, 15.5 dBi crossed Yagi): Eb/N0 {l['dl_ebn0_dB']:.1f} dB, margin {l['dl_margin_dB']:.1f} dB over 10.6 dB for 1e-5 BER",
         f"- Uplink (50 W): Eb/N0 {l['ul_ebn0_dB']:.1f} dB, margin {l['ul_margin_dB']:.1f} dB",
         f"- Throughput about {l['bits_per_day'] / 8 / 1e6:.1f} MB/day over 3 passes (70 % framing efficiency)",
         f"- {LINK['band_note']}", "",
         "## Deployment and inhibits [req]",
         f"- Antenna release no earlier than {DEPLOY['t_antenna_s'] // 60} min after separation; first RF no earlier than {DEPLOY['t_rf_s'] // 60} min.",
         f"- Burn wire: {DEPLOY['burn_r_ohm']} Ω resistor, {DEPLOY['burn_current_a']} A for {DEPLOY['burn_on_s']} s, up to {DEPLOY['burn_retries']} retries, release confirmed by element switches.",
         "- Battery/deploy inhibits: " + "; ".join(DEPLOY["rbf_inhibits"]),
         "- RF inhibits: " + "; ".join(DEPLOY["rf_inhibits"]), ""]
    (HERE / "design-basis.md").write_text("\n".join(L))


if __name__ == "__main__":
    d = run()
    report(d)
    p, l, m = d["power"], d["link"], d["mass"]
    print(f"mass CBE {m['cbe_g']:.0f} g, +margin {m['with_margin_g']:.0f} g | power avg gen {p['orbit_avg_gen_tumble_W']:.2f}/{p['orbit_avg_gen_spin_W']:.2f} W load {p['orbit_avg_load_W']:.2f} W "
          f"| DL margin {l['dl_margin_dB']:.1f} dB UL {l['ul_margin_dB']:.1f} dB | life {d['life_years']:.1f} y | ecl {d['orbit']['eclipse_max_min']:.1f} min")
