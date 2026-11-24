"""Build every TS-2 rev B part, export STEP (each unique part once, column C1 frame, mm), and the twin model:
../assembled/ts2b.glb (every instance, world mm, Z up) + ../assembled/assembly.json (node -> part data).

Run:  python build_all.py            (about 2-3 minutes)
"""
import json
import math
import os
import sys
import time

import numpy as np
import trimesh
from build123d import export_step, Compound

HERE = os.path.dirname(os.path.abspath(__file__))
MECH = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import parts as T  # noqa: E402
from params import P, slot_z  # noqa: E402

STEP = os.path.join(MECH, "step")
ASM = os.path.join(MECH, "assembled")
for d in (STEP, ASM):
    os.makedirs(d, exist_ok=True)

t0 = time.time()

# ------------------------------------------------------------------ catalogue: key -> meta
# kind: make (our drawing), buy (market part), pcb (our KiCad board)
META = {}


def meta(key, pn, name, kind, material, color, bom, drawing=None, finish=None):
    META[key] = dict(pn=pn, name=name, kind=kind, material=material, color=color, bom=bom, drawing=drawing, finish=finish)


meta("base_plate", "TS2B-201", "Column base plate", "make", "6061-T6 plate 12 mm", "#b9bdc3", "M-201", "TS2B-201", "clear anodise Type II")
meta("top_plate", "TS2B-202", "Column top plate", "make", "6061-T6 plate 10 mm", "#b9bdc3", "M-202", "TS2B-202", "clear anodise Type II")
meta("bulkhead", "TS2B-203", "Exhaust bulkhead (16 card windows)", "make", "6061-T6 sheet 3.0 mm", "#a9adb3", "M-203", "TS2B-203", "black anodise (plenum side)")
meta("post", "B-110", "Post, HFS6-3030 extrusion 952.8 mm", "buy", "6063-T5 extrusion", "#aeb2b8", "B-110")
meta("bracket_rail", "TS2B-205", "Bracket screw rail (8x 6-32)", "make", "6061-T6 bar 12 x 7.6", "#c9ccd1", "M-205", "TS2B-205", "clear anodise")
meta("tail_comb", "TS2B-206", "Tail guide comb (16 slots)", "make", "6061-T6 bar 16 x 22", "#c9ccd1", "M-206", "TS2B-206", "black anodise")
meta("comb_liner", "B-206", "EPDM U-trim 1.0 mm (comb liners)", "buy", "EPDM 60A", "#111111", "B-206")
meta("holddown_bar", "TS2B-207", "Hold-down bar, hinged", "make", "6061-T6 channel 20 x 14", "#c9ccd1", "M-207", "TS2B-207", "clear anodise")
meta("holddown_pad", "TS2B-208", "Hold-down pad, EPDM 3 mm", "make", "EPDM 60A sheet 3 mm (die cut)", "#111111", "M-208", "TS2B-208")
meta("hinge_block", "TS2B-209", "Hold-down hinge block pair", "make", "6061-T6", "#c9ccd1", "M-209", "TS2B-209", "clear anodise")
meta("latch", "TS2B-210", "Hold-down latch handle", "make", "6061-T6", "#c8102e", "M-210", "TS2B-210", "red anodise")
meta("crossmember", "TS2B-211", "Midspan crossmember", "make", "6061-T6 plate 10 mm", "#c9ccd1", "M-211", "TS2B-211", "clear anodise")
meta("light_bar", "TS2B-212", "Red light-bar diffuser", "make", "PC opal, signal red", "#c8102e", "M-212", "TS2B-212")
meta("side_skin", "TS2B-213", "Side skin", "make", "5052-H32 1.5 mm", "#c9ccd1", "M-213", "TS2B-213", "brushed, clear anodise")
meta("bp_carrier", "TS2B-214", "Backplane carrier plate", "make", "6061-T6 3 mm", "#8d9198", "M-214", "TS2B-214", "clear chromate")
meta("busbar_pos", "TS2B-215", "12 V busbar 14 x 10", "make", "C11000 Cu, tin plated", "#c87533", "M-215", "TS2B-215")
meta("busbar_neg", "TS2B-216", "RTN busbar 14 x 10", "make", "C11000 Cu, tin plated", "#7a7d82", "M-216", "TS2B-216")
meta("coil_sheet", "TS2B-220", "Tracing coil: tube sheets + frame", "make", "304 SS 1.2 mm", "#b8bcc2", "M-220", "TS2B-220")
meta("coil_fins", "TS2B-220", "Tracing coil: fin pack 12 FPI", "make", "1100-H14 Al fins 0.15 mm", "#d6d9dd", "M-220", "TS2B-220")
meta("coil_tubes", "TS2B-220", "Tracing coil: 3/8 in serpentine + return bends", "make", "C12200 Cu tube 3/8 x 0.032", "#c87533", "M-220", "TS2B-220")
meta("coil_headers", "TS2B-220", "Tracing coil: 7/8 in headers", "make", "C12200 Cu tube 7/8", "#c87533", "M-220", "TS2B-220")
meta("drip_tray", "TS2B-221", "Coil drip tray", "make", "304 SS 1.0 mm", "#b8bcc2", "M-221", "TS2B-221")
meta("filter_frame", "B-222", "MERV 8 filter 200 x 905 x 12 (frame)", "buy", "galvanised steel", "#8d9198", "B-222")
meta("filter_media", "B-222", "MERV 8 filter media", "buy", "synthetic", "#e9e6dc", "B-222")
meta("grille", "TS2B-223", "Intake grille segment (printed)", "make", "PETG, printed 0.2 mm", "#2a2b2e", "M-223", "TS2B-223")
meta("gpu_shroud", "B-001", "GPU: RTX PRO 6000 Blackwell Max-Q (shroud)", "buy", "Al/Mg die cast", "#1d1e21", "B-001")
meta("gpu_back", "B-001", "GPU backplate", "buy", "Al", "#2b2c30", "B-001")
meta("gpu_pcb", "B-001", "GPU PCB + x16 fingers", "buy", "FR4", "#5cb82f", "B-001")
meta("gpu_fan", "B-001", "GPU blower + fins", "buy", "plastic / Cu", "#3a3c42", "B-001")
meta("gpu_pwr", "B-001", "GPU 12V-2x6 socket", "buy", "LCP", "#111111", "B-001")
meta("gpu_bracket", "B-001", "GPU full-height bracket", "buy", "steel, nickel", "#b8bcc2", "B-001")
meta("cem", "B-010", "PCIe x16 Gen5 slot connector", "buy", "LCP", "#1a1a1a", "B-010")
meta("mcio", "B-011", "MCIO 8i receptacle, right angle", "buy", "LCP", "#222222", "B-011")
meta("mcio_plug", "B-012", "MCIO 8i cable plug", "buy", "LCP/steel", "#404040", "B-012")
meta("mcio_cable", "B-012", "MCIO 8i Gen5 cable", "buy", "PVC jacket", "#2b6cb0", "B-012")
meta("h12v", "B-013", "12V-2x6 right-angle header", "buy", "LCP", "#101010", "B-013")
meta("gpu_cable", "B-014", "12V-2x6 GPU power cable 150 mm", "buy", "16 AWG silicone", "#111111", "B-014")
meta("cbp", "CBP-8", "CBP-8 GPU backplane (KiCad)", "pcb", "Megtron 6 8L 2.0 mm", "#1f6b3a", "E-001", "CBP-8")
meta("cbp_rear", "CBP-8", "CBP-8 rear components", "pcb", "mixed", "#26282c", "E-001", "CBP-8")
meta("plenum_corner", "TS2B-301", "Plenum corner panel", "make", "5052-H32 1.5 mm", "#2a2b2e", "M-301", "TS2B-301", "black powder coat")
meta("arm", "TS2B-501", "Plinth arm weldment", "make", "S355 3 mm + 8 mm deck", "#141416", "M-501", "TS2B-501", "powder coat RAL 9005 textured")
meta("hub", "TS2B-502", "Plinth hub weldment", "make", "S355 3 mm", "#141416", "M-502", "TS2B-502", "powder coat RAL 9005 textured")
meta("caster", "B-070", "Leveling caster 300 kg", "buy", "steel, zinc", "#a8acb1", "B-070")
meta("host_tray", "TS2B-503", "Host node tray", "make", "S355 2 mm", "#2b2c30", "M-503", "TS2B-503")
meta("host_board", "B-020", "ASRock Rack ROMED8-2T", "buy", "FR4", "#1f4f8a", "B-020")
meta("host_cooler", "B-022", "SilverStone XE04-SP3B on EPYC 7543P", "buy", "Al/Cu", "#b98c6a", "B-022")
meta("host_dimm", "B-023", "32 GB DDR4-3200 RDIMM", "buy", "FR4", "#1b5e20", "B-023")
meta("host_cards", "B-024", "HighPoint Rocket 1628A (x4) + ConnectX-6 Dx", "buy", "FR4/Al", "#3b3d43", "B-024")
meta("crps", "B-030", "Murata D1U54T-W-2000-12-HC4TC CRPS 2000 W", "buy", "steel", "#2f3136", "B-030")
meta("crps_fan", "B-030", "CRPS fan grille", "buy", "steel", "#111111", "B-030")
meta("cpd", "CPD-1", "CPD-1 column power distribution board (KiCad)", "pcb", "FR4 6L 4 oz", "#1f6b3a", "E-002", "CPD-1")
meta("strap_p12", "TS2B-232", "CPD-1 +12 V strap (flat, 6 mm Cu)", "make", "C11000 plate 6 mm", "#d08a4a", "M-232", "TS2B-232", "bright tin 5-8 um")
meta("strap_rtn", "TS2B-233", "CPD-1 RTN strap (flat, 6 mm Cu)", "make", "C11000 plate 6 mm", "#8a8d92", "M-233", "TS2B-233", "bright tin 5-8 um")
meta("tec_housing", "TS2B-601", "Base thermal module housing", "make", "304 SS 2 mm", "#26282c", "M-601", "TS2B-601", "black powder coat")
meta("tec_cold", "TS2B-602", "Split cold block", "make", "C11000 Cu, nickel plated", "#c87533", "M-602", "TS2B-602")
meta("tec", "B-040", "Peltier module 40 x 40, TEC1-12715 class (x4)", "buy", "ceramic", "#e8e8e6", "B-040")
meta("tec_towers", "B-041", "Hot-side Cu spreader + heat-pipe fin stacks", "buy", "Cu/Al", "#c87533", "B-041")
meta("tec_fans", "B-042", "120 mm PWM fan (x2)", "buy", "PBT", "#1b1c1f", "B-042")
meta("crown_base", "TS2B-401", "Crown base ring", "make", "6061-T6 8 mm", "#c9ccd1", "M-401", "TS2B-401", "clear anodise")
meta("crown_shell", "TS2B-402", "Crown octagon shell", "make", "5052-H32 2 mm", "#c9ccd1", "M-402", "TS2B-402", "brushed, clear anodise")
meta("crown_band", "TS2B-403", "Crown red band", "make", "5052 2 mm", "#c8102e", "M-403", "TS2B-403", "red anodise")
meta("crown_deck", "TS2B-404", "Fan deck (3 inlet rings)", "make", "5052-H32 5 mm", "#8d9198", "M-404", "TS2B-404")
meta("crown_top", "TS2B-406", "Crown top + 18 in collar", "make", "5052-H32 5 mm", "#c9ccd1", "M-406", "TS2B-406")
meta("flap", "TS2B-405", "Backdraft flap pair", "make", "5052 0.8 mm", "#8d9198", "M-405", "TS2B-405")
meta("imp_ring", "B-051", "ebm-papst inlet ring 31050-2-4013", "buy", "Al", "#8d9198", "B-051")
meta("impeller", "B-050", "ebm-papst R3G310-AN12-30 impeller", "buy", "Al sheet", "#2b2d30", "B-050")
meta("imp_motor", "B-050", "R3G310 motor M3G084-FA", "buy", "Al", "#1b1c1f", "B-050")
meta("chimney", "B-060", "18 in spiral duct, 26 ga", "buy", "galvanised", "#cfd2d6", "B-060")
meta("console_post", "TS2B-701", "Console post 40 x 40", "make", "6063 tube", "#141416", "M-701", "TS2B-701")
meta("console_head", "TS2B-702", "Console bezel (printed ASA)", "make", "ASA", "#1d1e21", "M-702", "TS2B-702")
meta("console_screen", "B-080", "Raspberry Pi Touch Display 2", "buy", "glass", "#0c0d10", "B-080")

# ------------------------------------------------------------------ unique shapes (built once)
S = {}
g = T.gpu_card()
for k, v in g.items():
    S["gpu_" + k] = v
S["base_plate"] = T.base_plate()
S["top_plate"] = T.top_plate()
S["bulkhead"] = T.bulkhead()
S["post"] = T.post(0.0, 0.0)
S["bracket_rail"] = T.bracket_rail(0)
S["tail_comb_n"] = T.tail_comb(-1)
S["tail_comb_p"] = T.tail_comb(1)
S["comb_liner"] = T.comb_liners()
S["holddown_bar0"] = T.holddown_bar(0)
S["holddown_bar1"] = T.holddown_bar(1)
S["holddown_pad0"] = T.holddown_pads(0)
S["hinge_block0"] = T.hinge_block(0)
S["hinge_block1"] = T.hinge_block(1)
S["latch0"] = T.latch(0)
S["latch1"] = T.latch(1)
S["crossmember"] = T.crossmember()
S["light_bar"] = T.light_bar()
S["side_skin_n"] = T.side_skin(-1)
S["side_skin_p"] = T.side_skin(1)
S["bp_carrier"] = T.bp_carrier()
S["busbar_pos"], S["busbar_neg"] = T.busbars()
S["coil_sheet"], S["coil_fins"], S["coil_tubes"], S["coil_headers"] = T.tracing_coil()
S["drip_tray"] = T.drip_tray()
S["filter_frame"], S["filter_media"] = T.filter_frame()
for k in range(4):
    S["grille%d" % k] = T.grille_segment(k)
S["cem"] = T.cem_x16(0, 0)
S["mcio"], S["mcio_plug"] = T.mcio_ra(0, 0)
S["h12v"] = T.h12v2x6(0, 0)
S["gpu_cable"] = T.gpu_power_cable(0, 0)
S["cbp0"] = T.cbp_board(0)
S["cbp_rear0"] = T.cbp_rear_parts(0)
S["arm"] = T.plinth_arm()
S["hub"] = T.plinth_hub()
S["caster"] = T.caster(0.0, 0.0)
S["host_tray"], S["host_board"], S["host_cooler"], S["host_dimm"], S["host_cards"] = T.host_node()
S["crps"], S["crps_fan"] = T.crps(0)
S["cpd"] = T.cpd_board()
S["strap_p12"], S["strap_rtn"] = T.strap_p12(), T.strap_rtn()
S["tec_housing"], S["tec_cold"], S["tec"], S["tec_towers"], S["tec_fans"] = T.tec_module()
CR = T.crown_parts()
S["crown_base"], S["crown_shell"], S["crown_band"], S["crown_deck"], S["crown_top"] = CR["base"], CR["shell"], CR["band"], CR["deck"], CR["top"]
S["imp_ring"], S["impeller"], S["imp_motor"] = T.impeller(0.0, 0.0, CR["deck_z"] + 5.0)
S["flap"] = T.backdraft_flap(0.0, 0.0, CR["deck_z"])
S["chimney"] = T.chimney()
S["console_post"], S["console_head"], S["console_screen"] = T.panel_console()
S["plenum_corner"] = T.plenum_corner(0)
print("shapes built %.1f s" % (time.time() - t0))

# mcio cables differ per slot (length): build per (group, i)
CABLES = {(gg, i): T.mcio_cable(gg, i) for gg in (0, 1) for i in range(8)}

# ------------------------------------------------------------------ STEP export (unique parts, C1 frame)
STEP_KEYS = {
    "TS2B-201_column_base_plate": "base_plate", "TS2B-202_column_top_plate": "top_plate", "TS2B-203_exhaust_bulkhead": "bulkhead",
    "TS2B-205_bracket_rail": "bracket_rail", "TS2B-206_tail_comb": "tail_comb_p", "TS2B-207_holddown_bar": "holddown_bar0",
    "TS2B-208_holddown_pads": "holddown_pad0", "TS2B-209_hinge_block": "hinge_block0", "TS2B-210_latch_handle": "latch0",
    "TS2B-211_crossmember": "crossmember", "TS2B-212_light_bar": "light_bar", "TS2B-213_side_skin": "side_skin_p",
    "TS2B-214_bp_carrier": "bp_carrier", "TS2B-215_busbar_12V": "busbar_pos", "TS2B-216_busbar_RTN": "busbar_neg", "TS2B-232_strap_12V": "strap_p12", "TS2B-233_strap_RTN": "strap_rtn",
    "TS2B-221_drip_tray": "drip_tray", "TS2B-223_grille_segment": "grille0", "TS2B-301_plenum_corner": "plenum_corner",
    "TS2B-401_crown_base": "crown_base", "TS2B-402_crown_shell": "crown_shell", "TS2B-403_crown_band": "crown_band",
    "TS2B-404_fan_deck": "crown_deck", "TS2B-405_backdraft_flap": "flap", "TS2B-406_crown_top": "crown_top",
    "TS2B-501_plinth_arm": "arm", "TS2B-502_plinth_hub": "hub", "TS2B-601_tec_housing": "tec_housing", "TS2B-602_cold_block": "tec_cold",
    "TS2B-701_console_post": "console_post", "TS2B-702_console_bezel": "console_head",
}
for name, key in STEP_KEYS.items():
    export_step(S[key], os.path.join(STEP, name + "_mm.step"))
coil = Compound(children=[S["coil_sheet"], S["coil_fins"], S["coil_tubes"], S["coil_headers"]])
export_step(coil, os.path.join(STEP, "TS2B-220_tracing_coil_mm.step"))
gpu = Compound(children=[S["gpu_" + k] for k in g])
export_step(gpu, os.path.join(STEP, "B-001_gpu_envelope_card_frame_mm.step"))
print("STEP exported %.1f s" % (time.time() - t0))

# ------------------------------------------------------------------ tessellation cache
MESH = {}


def mesh_of(key, shape=None, tol=0.25):
    if key in MESH:
        return MESH[key]
    sh = shape if shape is not None else S[key]
    v, f = sh.tessellate(tol, 0.35)
    m = trimesh.Trimesh(vertices=np.array([[p.X, p.Y, p.Z] for p in v]), faces=np.array(f), process=False)
    MESH[key] = m
    return m


def Rz(deg):
    a = math.radians(deg)
    M = np.eye(4)
    M[0:2, 0:2] = [[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]]
    return M


def Tr(x=0.0, y=0.0, z=0.0):
    M = np.eye(4)
    M[:3, 3] = (x, y, z)
    return M


scene = trimesh.Scene()
NODES = []
MATS = {}


def material(color, kind):
    key = (color, kind)
    if key not in MATS:
        c = trimesh.visual.color.hex_to_rgba(color)
        metal = 0.75 if kind in ("make",) and not color.startswith("#1") else 0.25
        MATS[key] = trimesh.visual.material.PBRMaterial(baseColorFactor=[c[0] / 255, c[1] / 255, c[2] / 255, 1.0],
                                                        metallicFactor=metal, roughnessFactor=0.45)
    return MATS[key]


def add(node, key, mkey, M, extra=None, shape=None):
    m = mesh_of(key, shape)
    md = META[mkey]
    mm = m.copy()
    mm.visual = trimesh.visual.TextureVisuals(material=material(md["color"], md["kind"]))
    scene.add_geometry(mm, node_name=node, geom_name=node, transform=M)
    rec = dict(node=node, key=mkey, **md)
    if extra:
        rec.update(extra)
    NODES.append(rec)


for c in range(4):
    C = Rz(90 * c)
    cn = "C%d" % (c + 1)
    add(f"{cn}_base_plate", "base_plate", "base_plate", C)
    add(f"{cn}_top_plate", "top_plate", "top_plate", C)
    add(f"{cn}_bulkhead", "bulkhead", "bulkhead", C)
    k = 0
    for xr in (T.RPI, T.RPO):
        for sgn in (-1, 1):
            k += 1
            add(f"{cn}_post_{k}", "post", "post", C @ Tr(sum(xr) / 2, sgn * (T.PV0 + T.PV1) / 2, 0))
    add(f"{cn}_tail_comb_lower", "tail_comb_n", "tail_comb", C)
    add(f"{cn}_tail_comb_upper", "tail_comb_p", "tail_comb", C)
    add(f"{cn}_comb_liners", "comb_liner", "comb_liner", C)
    for gg in (0, 1):
        gl = "L" if gg == 0 else "U"
        dz = T.G_Z[gg] - T.G_Z[0]
        add(f"{cn}{gl}_bracket_rail", "bracket_rail", "bracket_rail", C @ Tr(0, 0, dz))
        add(f"{cn}{gl}_holddown_bar", "holddown_bar%d" % gg, "holddown_bar", C)
        add(f"{cn}{gl}_holddown_pads", "holddown_pad0", "holddown_pad", C @ Tr(0, 0, dz))
        add(f"{cn}{gl}_hinge_block", "hinge_block%d" % gg, "hinge_block", C)
        add(f"{cn}{gl}_latch", "latch%d" % gg, "latch", C)
        add(f"{cn}{gl}_cbp8", "cbp0", "cbp", C @ Tr(0, 0, dz), dict(group=gl))
        add(f"{cn}{gl}_cbp8_rear", "cbp_rear0", "cbp_rear", C @ Tr(0, 0, dz))
        for i in range(8):
            sl = gg * 8 + i + 1
            zz = slot_z(gg, i)
            CARD = C @ Tr(T.RB, T.V0, zz)
            gid = dict(column=c + 1, slot=sl, gpu_index=c * 16 + sl - 1)
            for part in ("shroud", "back", "pcb", "fan", "pwr", "bracket"):
                add(f"{cn}_S{sl:02d}_gpu_{part}", "gpu_" + part, "gpu_" + part, CARD, gid)
            dzs = zz - slot_z(0, 0)
            dxm = T.mcio_x(gg, i) - T.mcio_x(0, 0)
            add(f"{cn}_S{sl:02d}_cem", "cem", "cem", C @ Tr(0, 0, dzs), gid)
            add(f"{cn}_S{sl:02d}_mcio", "mcio", "mcio", C @ Tr(dxm, 0, dzs), gid)
            add(f"{cn}_S{sl:02d}_mcio_plug", "mcio_plug", "mcio_plug", C @ Tr(dxm, 0, dzs), gid)
            add(f"{cn}_S{sl:02d}_mcio_cable", "cable_%d_%d" % (gg, i), "mcio_cable", C, gid, shape=CABLES[(gg, i)])
            add(f"{cn}_S{sl:02d}_h12v", "h12v", "h12v", C @ Tr(0, 0, dzs), gid)
            add(f"{cn}_S{sl:02d}_gpu_cable", "gpu_cable", "gpu_cable", C @ Tr(0, 0, dzs), gid)
    add(f"{cn}_crossmember", "crossmember", "crossmember", C)
    add(f"{cn}_light_bar", "light_bar", "light_bar", C)
    add(f"{cn}_side_skin_neg", "side_skin_n", "side_skin", C)
    add(f"{cn}_side_skin_pos", "side_skin_p", "side_skin", C)
    add(f"{cn}_bp_carrier", "bp_carrier", "bp_carrier", C)
    add(f"{cn}_busbar_12V", "busbar_pos", "busbar_pos", C)
    add(f"{cn}_busbar_RTN", "busbar_neg", "busbar_neg", C)
    for key in ("coil_sheet", "coil_fins", "coil_tubes", "coil_headers"):
        add(f"{cn}_{key}", key, key, C)
    add(f"{cn}_drip_tray", "drip_tray", "drip_tray", C)
    add(f"{cn}_filter_frame", "filter_frame", "filter_frame", C)
    add(f"{cn}_filter_media", "filter_media", "filter_media", C)
    for k in range(4):
        add(f"{cn}_grille_{k + 1}", "grille%d" % k, "grille", C)
    add(f"{cn}_plenum_corner", "plenum_corner", "plenum_corner", C)
    # plinth arm and its contents
    add(f"{cn}_arm", "arm", "arm", C)
    for xx, yy in ((P["ARM_R1"] - 70.0, -110.0), (P["ARM_R1"] - 70.0, 110.0)):
        add(f"{cn}_caster_{'a' if yy < 0 else 'b'}", "caster", "caster", C @ Tr(xx, yy, 0))
    for key in ("host_tray", "host_board", "host_cooler", "host_dimm", "host_cards"):
        add(f"{cn}_{key}", key, key, C)
    for k in range(4):
        add(f"{cn}_crps_{k + 1}", "crps", "crps", C @ Tr(0, k * 58.0, 0), dict(column=c + 1, psu=k + 1))
        add(f"{cn}_crps_{k + 1}_fan", "crps_fan", "crps_fan", C @ Tr(0, k * 58.0, 0))
    add(f"{cn}_cpd1", "cpd", "cpd", C)
    add(f"{cn}_cpd1_strap_p12", "strap_p12", "strap_p12", C)
    add(f"{cn}_cpd1_strap_rtn", "strap_rtn", "strap_rtn", C)
    for key in ("tec_housing", "tec_cold", "tec", "tec_towers", "tec_fans"):
        add(f"{cn}_{key}", key, key, C, dict(column=c + 1))
add("hub", "hub", "hub", np.eye(4))
for k, (x, y) in enumerate(CR["impellers"]):
    M = Tr(x, y, 0)
    add(f"impeller_{k + 1}_ring", "imp_ring", "imp_ring", M)
    add(f"impeller_{k + 1}_rotor", "impeller", "impeller", M, dict(spin=True, impeller=k + 1, axis=[x, y]))
    add(f"impeller_{k + 1}_motor", "imp_motor", "imp_motor", M)
    add(f"impeller_{k + 1}_flap", "flap", "flap", M)
for key in ("crown_base", "crown_shell", "crown_band", "crown_deck", "crown_top"):
    add(key, key, key, np.eye(4))
add("chimney", "chimney", "chimney", np.eye(4))
C3 = Rz(180)
for key in ("console_post", "console_head", "console_screen"):
    add("C3_" + key, key, key, C3)
print("scene %d nodes %.1f s" % (len(NODES), time.time() - t0))

glb = os.path.join(ASM, "ts2b.glb")
scene.export(glb)
print("glb", os.path.getsize(glb) // 1024, "kB")

steps = [
    dict(n=1, title="Plinth: hub, 4 arms, casters, levelled", add=["hub", "arm", "caster"]),
    dict(n=2, title="Arm fit-out: host node tray, CRPS bank, CPD-1", add=["host_", "crps", "cpd1"]),
    dict(n=3, title="Column frames: base plate, 4 posts, bulkhead, top plate, crossmember", add=["base_plate", "post", "bulkhead", "top_plate", "crossmember"]),
    dict(n=4, title="Backplane carrier, busbars, CBP-8 boards, MCIO cables down the rear channel", add=["bp_carrier", "busbar", "cbp8", "mcio"]),
    dict(n=5, title="Bracket rails, tail combs (lined), hinge blocks", add=["bracket_rail", "tail_comb", "comb_liners", "hinge_block"]),
    dict(n=6, title="GPUs: 16 per column, slide in along -v into the CEM slot, thumbscrew the bracket, plug 12V-2x6", add=["_gpu_", "h12v", "gpu_cable", "_cem"]),
    dict(n=7, title="Close the hold-down bars, latch (red), check each card", add=["holddown", "latch"]),
    dict(n=8, title="Tracing coils, drip trays, filters, grilles, side skins", add=["coil_", "drip_tray", "filter", "grille", "side_skin", "light_bar", "plenum_corner"]),
    dict(n=9, title="Base thermal modules (Peltier trim) and coolant risers", add=["tec_"]),
    dict(n=10, title="Crown: base ring, deck, 3 impellers with flaps, shell, band, top, chimney", add=["crown", "impeller", "chimney"]),
    dict(n=11, title="Console on the C3 nose", add=["console"]),
]
json.dump(dict(units="mm", up="Z", glb="ts2b.glb", rev=P["rev"], n_gpus=P["n_gpus"], nodes=NODES, steps=steps,
               note="Every node name in ts2b.glb maps to one record here (part number, kind, material, BOM line, drawing)."),
          open(os.path.join(ASM, "assembly.json"), "w"), indent=0)
print("done %.1f s" % (time.time() - t0))
