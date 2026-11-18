"""Phase 1 engineering sheets (Anatomy plant toolkit, engsheets.py):

  G-P1-000   cover and sheet index
  PFD-P1-001 process flow diagram with stream table (rates from the line balance and dosing plan)
  ASM-P1-001 dosing station and blending train elevation 1:20, ring plan, height stack-up
  ASM-P1-002 sifting and grinding elevations 1:10
  ASM-P1-003 pack bench elevation 1:20: fill, cap, seal, label, metal detect, checkweigh, pack
  ELE-P1-001 power one-line and control network
  ELE-P1-002 I/O list, wire numbers and field cable schedule (also writes io_p1.json)
  ELE-P1-003 typical control wiring: one bin channel, transfer interlocks, safety circuit

Heights are true scale from the CAD parts (cad/parts.json) and equipment.json; anything set by a bought or used machine
is marked VERIFY. Run after equipment_p1.py, p1_parts.py and the line balance / dosing plan.
"""
import json
import pathlib
import sys
from html import escape

HERE = pathlib.Path(__file__).parent
P1 = HERE.parent
OUT = P1 / "drawings"
sys.path.insert(0, str(P1.parents[2] / "skills" / "anatomy" / "tools" / "plant"))
import engsheets as es  # noqa: E402

EQ = {e["tag"]: e for e in json.loads((HERE / "equipment.json").read_text())}
LB = json.loads((HERE / "out" / "line-balance.json").read_text())
DP = json.loads((HERE / "out" / "dosing-plan.json").read_text())
PROJECT = "Down Home Creole · Phase 1 prototype · 1,000 lb/week, 5 blends (13-blend ready)"
SW, SH, IN = es.SW, es.SH, 25.4
mm_in = es.mm_in
STEEL, SS = "#eceff1", "#cfd8dc"

R = lambda xywh, **k: dict(t="rect", xywh=xywh, **k)
P = lambda pts, **k: dict(t="poly", pts=pts, **k)
C = lambda c, r, **k: dict(t="circle", c=c, r=r, **k)
T = lambda s, at, fs=13: dict(t="text", s=s, at=at, fs=fs)


def src(tag):
    e = EQ[tag]
    return (e["maker"] if e["maker"] != "fabricated" else "fabricated, drawing " + tag) + ("" if e["maker"] == "fabricated" else f" {e['model']}")[:70]


def item(n, tag, shapes, balloon, target, name=None, qty=None):
    e = EQ.get(tag, {})
    return dict(n=n, tag=tag, name=(name or e.get("name", tag))[:95], src=src(tag)[:52] if tag in EQ else "", qty=qty if qty is not None else e.get("qty", 1),
                shapes=shapes, balloon=balloon, target=target)


# ================================================================== PFD-P1-001
def pfd():
    c = LB["blending"]["chosen"]
    wk = LB["weekly_lb"]
    nb = len(DP["bins"])
    U = [
        dict(id="rcv", tag="P1-101", name="Receive, weigh, COA check\nquarantine or release (MES)", x=80, y=180, w=320, h=110, fill="#e3f2fd"),
        dict(id="st", tag="P1-102 / PAL-RM", name="Raw storage 2 weeks\nNSF shelving + floor pallets", x=80, y=400, w=320, h=110, fill="#e3f2fd"),
        dict(id="mill", tag="P1-320 + P1-321/322", name="Grind whole spices\nmagnet ahead of hammers", x=80, y=640, w=320, h=110),
        dict(id="bins", tag=f"P1-211 x {nb} (12 positions)", name="Ingredient bins\nlot scan at every refill", x=500, y=180, w=340, h=110),
        dict(id="feed", tag="P1-212 x 9 > P1-220", name="Screw feeders dose by weight\ninto the weigh hopper", x=500, y=400, w=340, h=110),
        dict(id="hand", tag="P1-201 on P1-206", name="Hand weigh: lines under 4 kg\nscan lot, MES tolerance", x=500, y=640, w=340, h=110),
        dict(id="pm", tag="P1-202 + P1-208", name="Premix minors < 2 %\nwith carrier salt, tumble", x=500, y=860, w=340, h=110),
        dict(id="scr", tag="P1-223 > P1-224", name="Valve, flexible screw\nhand adds + premix at intake", x=940, y=400, w=340, h=110),
        dict(id="bl", tag="P1-301 (built) > P1-331", name=f"Ribbon blend {c['working_cuft']} cu ft\nmix 12 min, CV <= 5 %", x=1380, y=400, w=340, h=110),
        dict(id="sv", tag="P1-304/305/307 on drum", name="Drum-top sifter 12 mesh\n+ magnet, oversize to reject", x=1380, y=620, w=340, h=110),
        dict(id="drum", tag="P1-308 on P1-309", name="Lined 55 gal drum\n1 batch = 1 drum, labeled", x=1380, y=840, w=340, h=110),
        dict(id="qc", tag="HOLD-1 / QC", name="QC hold: CV, micro\nrelease in MES", x=1820, y=840, w=320, h=110, fill="#fff3e0"),
        dict(id="fill", tag="P1-401 (built) + P1-410", name="Servo auger fill by weight\nnests hold the container", x=1820, y=180, w=320, h=110),
        dict(id="cap", tag="TBL-1: P1-412 + P1-403", name="Spindle capper, clutch torque\ninduction seal", x=2240, y=180, w=320, h=110),
        dict(id="lab", tag="TBL-2: P1-404 + P1-405", name="Print label with lot + best-by\nbuilt wrap labeler", x=2240, y=400, w=320, h=110),
        dict(id="md", tag="P1-406 + P1-418", name="Metal detect finished pack\nCCP-1, locked reject", x=2240, y=620, w=320, h=110, fill="#ffebee"),
        dict(id="cw", tag="TBL-3: P1-407", name="Checkweigh every unit\nreject < declared", x=2240, y=840, w=320, h=110),
        dict(id="pk", tag="P1-408 > TBL-4", name="Accumulate, case pack\nGS1 case label (P1-204)", x=2660, y=840, w=320, h=110),
        dict(id="fg", tag="PAL-FG > FG-1", name="Pallet, SSCC label\nfinished goods 3 days", x=2660, y=1060, w=320, h=100, fill="#e8f5e9"),
    ]
    auto = DP["auto_pct_overall"]
    per_batch = wk / c["batches"]
    S = [
        dict(n=1, frm="rcv", to="st", name="Ingredients received", material="25 kg bags, boxes", rate=f"{wk:,.0f} lb/week", basis="design basis 1,000 lb/week", pts=[(240, 290), (240, 400)]),
        dict(n=2, frm="st", to="bins", name="Bags to bin refill", material="bagged ingredients", rate=f"{auto:.0f} % of blend weight", basis="dosing-plan.json: binned lines", pts=[(400, 430), (450, 430), (450, 235), (500, 235)]),
        dict(n=3, frm="st", to="mill", name="Whole spices to mill", material="peppercorns, chiles, leaf", rate="~50 lb/week at launch", basis="P1-320 duty, 1 h/week", pts=[(240, 510), (240, 640)]),
        dict(n=4, frm="mill", to="bins", name="Ground spice to bin", material="ground, in lined drum", rate="~50 lb/week", basis="coarse black pepper (B06)", pts=[(400, 695), (460, 695), (460, 260), (500, 260)]),
        dict(n=5, frm="bins", to="feed", name="Bin to feeder", material="powders, flakes", rate="one bin at a time", basis="P1-212 2 in screw ~700 L/h", pts=[(670, 290), (670, 400)]),
        dict(n=6, frm="st", to="hand", name="Bags to hand weigh", material="lines < 4 kg", rate=f"{100 - auto:.0f} % incl. premix", basis="min dose 4 kg (dosing-config)", pts=[(400, 480), (440, 480), (440, 700), (500, 700)]),
        dict(n=7, frm="hand", to="pm", name="Minors", material="lines < 2 %", rate="0.1 g scale", basis="site premix rule", pts=[(670, 750), (670, 860)]),
        dict(n=8, frm="feed", to="scr", name="Bin charge", material="dosed ingredients", rate=f"up to {max(b['max_dose_kg'] for b in DP['bins']):.0f} kg per line", basis="±1 % (20 g min)"),
        dict(n=9, frm="hand", to="scr", name="Hand adds", material="pails, tipped at 600 mm", rate=f"{c['batches']} batches/week", basis="after the bin charge", pts=[(840, 695), (1110, 695), (1110, 510)]),
        dict(n=10, frm="pm", to="scr", name="Premix (last)", material="sealed pail", rate=f"{c['batches']} premixes/week", basis="", pts=[(840, 915), (1170, 915), (1170, 510)]),
        dict(n=11, frm="scr", to="bl", name="Charge to blender", material="dry blend parts", rate=f"avg {per_batch:,.0f} lb/batch", basis="line balance"),
        dict(n=12, frm="bl", to="sv", name="Blend discharge", material="blend", rate="~8 lb/min", basis="sieve design rate", pts=[(1550, 510), (1550, 620)]),
        dict(n=13, frm="sv", to="drum", name="Sifted blend", material="blend", rate=f"{per_batch:,.0f} lb/batch", basis="", pts=[(1550, 730), (1550, 840)]),
        dict(n=14, frm="drum", to="qc", name="Drum to hold", material="sealed lined drum", rate=f"{c['batches']} drums/week", basis=""),
        dict(n=15, frm="qc", to="fill", name="Released drum to filler", material="blend", rate=f"{sum(r['units'] for r in LB['pack_lines'][0]['rows']):,} units/week",
             basis="pack bench", pts=[(1980, 840), (1980, 290)]),
        dict(n=16, frm="fill", to="cap", name="Filled containers", material="open containers", rate="12 upm shaker (rated)", basis="FL-P401 bottleneck"),
        dict(n=17, frm="cap", to="lab", name="Sealed containers", material="capped, induction sealed", rate="12 upm", basis="", pts=[(2400, 290), (2400, 400)]),
        dict(n=18, frm="lab", to="md", name="Labeled units", material="lot + best-by printed", rate="12 upm", basis="", pts=[(2400, 510), (2400, 620)]),
        dict(n=19, frm="md", to="cw", name="Metal-free units", material="finished pack", rate="12 upm", basis="CCP-1", pts=[(2400, 730), (2400, 840)]),
        dict(n=20, frm="cw", to="pk", name="Accepted units", material="weighed", rate="12 upm", basis="NIST HB 133"),
        dict(n=21, frm="pk", to="fg", name="Cases to pallet", material="RSC cases", rate="~1 case/min", basis="12-count", pts=[(2820, 950), (2820, 1060)]),
        dict(n=22, frm="md", to="qc", name="Metal reject", material="rejected unit, locked bin", rate="event", basis="CCP-1 deviation: hold + investigate",
             color="#c62828", dash="8,5", pts=[(2240, 700), (2190, 700), (2190, 870), (2140, 870)]),
        dict(n=23, frm="sv", to="qc", name="Sieve overs / magnet catch", material="oversize, tramp metal", rate="event", basis="record and investigate",
             color="#c62828", dash="8,5", pts=[(1720, 700), (1780, 700), (1780, 890), (1820, 890)]),
    ]
    svg = es.pfd(U, S, "PFD-P1-001 PROCESS FLOW DIAGRAM", "DH-PFD-P1-001", PROJECT, [
        "Rates from design/out/line-balance.json and dosing-plan.json; 1,000 lb/week on 5 days, 1 shift.",
        f"{nb} bins dosed automatically ({auto} % of blend weight); lines under 4 kg are hand-weighed, under 2 % go to premix.",
        "CCP-1 is metal detection of the finished pack (P1-406). Sieve and magnets are prerequisite programs.",
        "MES links ingredient lots > bin (every lot since last empty) > batch > drum > unit lot code > case > pallet.",
        "Grinding is optional at launch: the bins accept bought ground spice; the mill takes whole peppercorns in house.",
        "Seasonings only in Phase 1: no wheat on site, so the gluten-free claim is protected by separation."])
    (OUT / "PFD-P1-001_process_flow.svg").write_text(svg)


# ================================================================== ASM-P1-001 dosing and blending
XC = 1800.0                 # dosing station centre
H_RING, Y_BIN, Y_FEED, Y_LID, Y_HOP, Y_VALVE = 2210, 1730, 1380, 1231, 650, 550
XV = 6100.0                 # blender valve / sifter centreline (built blender P1-301, no riser stand)
TB, Y_VOUT, Y_FLG = 1400, 1261, 1983          # trough bottom, valve outlet, top flange (cad/p1_machines.py)
BX0, BX1 = XV - 480 - 38, XV + 480 + 38       # frame legs


def bin_shapes(x, label):
    return [R((x - 100, Y_BIN, 200, 6), fill=SS),
            P([(x - 60, Y_BIN + 6), (x + 60, Y_BIN + 6), (x + 300, Y_BIN + 406), (x - 300, Y_BIN + 406)], fill=STEEL, sw=2),
            R((x - 302, Y_BIN + 406, 604, 250), fill=STEEL, sw=2), R((x - 340, Y_BIN + 656, 680, 6), fill=SS),
            R((x - 330, Y_BIN + 662, 660, 4), fill="#90a4ae"), R((x - 312, Y_BIN + 506, 10, 100), fill=SS), R((x + 302, Y_BIN + 506, 10, 100), fill=SS),
            T(label, (x, Y_BIN + 300), 11)]


def asm1():
    b_left, b_right = XC - 1250, XC + 1250
    lab = {b["bin"]: b for b in DP["bins"]}
    ring = [R((XC - 1590 - 25, 0, 51, H_RING + 25), fill=SS), R((XC + 1590 - 25, 0, 51, H_RING + 25), fill=SS),
            R((XC - 1590 - 25, H_RING - 25, 3180 + 50, 51), fill=SS), R((b_left - 25, H_RING - 25, 51, 51), fill="#90a4ae"),
            R((XC - 1590, 975, 1185, 51), fill=SS), R((XC + 405, 975, 1185, 51), fill=SS),
            R((XC - 1590 - 75, 0, 150, 10), fill="#90a4ae"), R((XC + 1590 - 75, 0, 150, 10), fill="#90a4ae"),
            T("ring 2 in sq tube on R1,590; bins on R1,250", (XC, 2560), 12)]
    FA = Y_BIN - 204.0           # built feeder P1-212 barrel axis: bin outlet flange on the transition top (P1-212-GA)
    FS = FA - 132.0              # spout bottom (P1-212 rev B: vertical spout at R280, sleeve P1-214 down to the lid stub)
    def feeder(bx, d):           # d = +1 screw runs right (inward), -1 left; P1-212 rev B frame (x 0 under the bin outlet)
        xs = lambda a, b: (min(bx + d * a, bx + d * b), abs(b - a))
        x0, w = xs(-130, 1065)
        sh = [R((x0, FA - 32, w, 64), fill=SS, sw=2), P([(bx - 75, Y_BIN - 6), (bx + 75, Y_BIN - 6), (bx + 60, FA + 32), (bx - 60, FA + 32)], fill=SS, sw=1.5),
              R((bx - 100, Y_BIN - 6, 200, 6), fill=SS)]
        x0, w = xs(938, 1002)
        sh.append(R((x0, FS, w, 100), fill=SS))
        x0, w = xs(-345, -130)
        sh.append(R((x0, FA - 55, w, 110), fill=SS, sw=1.5))
        x0, w = xs(-625, -345)
        sh += [R((x0, FA - 60, w, 120), fill="#b3c7e6", sw=2), T("0.25 kW", (bx - d * 485, FA + 90), 11)]
        return sh
    fl = feeder(b_left, 1)
    fr = feeder(b_right, -1)
    bfm = [R((XC - 280 - 35, Y_LID, 70, FS + 30 - Y_LID), fill="#fffde7", sw=1.5), R((XC + 280 - 35, Y_LID, 70, FS + 30 - Y_LID), fill="#fffde7", sw=1.5)]
    probe = [R((b_left + 160, Y_BIN + 250, 120, 40), fill="#ffe0b2"), R((b_right - 280, Y_BIN + 250, 120, 40), fill="#ffe0b2")]
    hop = [R((XC - 380, Y_LID - 3, 760, 3), fill=SS), R((XC - 352, Y_LID - 253, 704, 250), fill=STEEL, sw=2.5),
           P([(XC - 352, Y_LID - 253), (XC + 352, Y_LID - 253), (XC + 52, Y_HOP + 29), (XC - 52, Y_HOP + 29)], fill=STEEL, sw=2.5),
           R((XC - 60, Y_HOP, 120, 29), hatch="h45", fill="none"),
           R((XC - 460, 1123, 108, 10), fill=SS), R((XC + 352, 1123, 108, 10), fill=SS)]
    cells = [R((XC - 455, 1033, 100, 90), fill="#ffcc80"), R((XC + 355, 1033, 100, 90), fill="#ffcc80")]
    valve = [R((XC - 70, Y_VALVE, 140, 100), fill="#b0bec5", sw=2), P([(XC + 70, Y_VALVE + 50), (XC + 260, Y_VALVE + 50)], closed=False, sw=4)]
    scr_t = (XC + 500, 220)
    top = (XV + 330, Y_FLG + 170)
    screw = [P([(XC - 350, Y_VALVE), (XC + 350, Y_VALVE), (XC + 150, 160), (XC - 150, 160)], fill="#fff3e0", sw=2),
             R((XC - 200, 0, 900, 160), fill="#fff3e0", sw=2), P([(XC - 320, Y_VALVE + 15), (XC - 120, Y_VALVE + 15)], closed=False, sw=3, stroke="#5d4037"),
             T("intake grate 600 [23.6]", (XC - 560, Y_VALVE - 40), 12),
             P([scr_t, top], closed=False, sw=9, stroke="#8d6e63"), R((top[0] - 120, top[1], 240, 170), fill=SS), T("screw drive 1 HP", (top[0], top[1] + 230), 12)]
    ax = TB + 3 + 280
    frame = [R((BX0, 0, 76, ax + 150), fill=SS), R((BX1 - 76, 0, 76, ax + 150), fill=SS), R((BX0, 282, BX1 - BX0, 76), fill=SS),
             R((XV - 338, TB - 76, 76, 76), fill=SS), R((XV + 262, TB - 76, 76, 76), fill=SS),
             R((BX0 - 12, ax - 320, 12, 520), fill=SS), R((BX1, ax - 320, 12, 520), fill=SS),
             R((BX0 - 37, 0, 150, 12), fill="#90a4ae"), R((BX1 - 113, 0, 150, 12), fill="#90a4ae")]
    blender = [P([(XV - 450, Y_FLG), (XV + 450, Y_FLG), (XV + 450, ax), (XV - 450, ax)], fill=STEEL, sw=2.5),
               P([(XV - 450, ax), (XV + 450, ax), (XV + 450, TB + 140), (XV + 300, TB), (XV - 300, TB), (XV - 450, TB + 140)], fill=STEEL, sw=2.5),
               R((XV - 500, Y_FLG, 1000, 6), fill=SS), R((XV - 500, Y_FLG + 6, 1000, 3), fill=SS),
               P([(BX0 - 160, ax), (BX1 + 380, ax)], closed=False, dash="18,6,4,6", stroke="#2e7d32", sw=1.5),
               R((XV - 460, ax - 285, 10, 570), fill=SS), R((XV + 450, ax - 285, 10, 570), fill=SS),
               R((BX0 - 52, ax - 95, 40, 190), fill="#ffcc80"), R((BX1 + 12, ax - 95, 40, 190), fill="#ffcc80"),
               R((BX1 + 60, ax - 195, 230, 330), fill="#90a4ae"), C((BX1 + 420, ax + 80), 100, fill="#90a4ae"), T("2 HP gearmotor 40 rpm", (BX1 + 300, ax + 280), 12),
               P([(XV - 275, ax - 260), (XV + 275, ax - 260)], closed=False, sw=2, stroke="#37474f", dash="10,6"), T("double ribbons OD 550", (XV, ax + 60), 12)]
    grate = [R((XV - 410, Y_FLG + 9, 600, 25), hatch="h135", fill="none"), R((XV - 410, Y_FLG + 34, 100, 280), fill=SS),
             P([(XV - 360, Y_FLG + 314), (XV - 360, 3350), (7400, 3350)], closed=False, sw=5, stroke="#78909c", dash="14,6"), T("to P1-310", (7250, 3400), 12)]
    valve = [R((XV - 60, TB - 29, 120, 29), fill=SS), R((XV - 70, Y_VOUT + 29, 140, 81), fill="#b0bec5", sw=2), R((XV - 60, Y_VOUT, 120, 29), fill=SS),
             R((XV + 70, Y_VOUT + 40, 160, 60), fill="#90a4ae")]
    sock = [P([(XV - 50, Y_VOUT), (XV + 50, Y_VOUT), (XV + 45, 1235), (XV - 45, 1235)], fill="#fffde7")]
    sv_b = 1054 - 60
    sieve = [R((XV - 310, 1054, 620, 6), fill=SS), R((XV - 242, sv_b, 4, 60), fill=SS), R((XV + 238, sv_b, 4, 60), fill=SS),
             R((XV - 242, 1060, 484, 150), fill=STEEL, sw=2), P([(XV - 225, 1100), (XV + 225, 1100)], closed=False, sw=3, stroke="#37474f", dash="6,3"),
             R((XV - 250, 1210, 500, 3), fill=SS), R((XV - 60, 1213, 120, 22), fill=SS)]
    vib = [R((XV + 250, 1090, 180, 110), fill="#ffe0b2")]
    drum = [R((XV - 320, 114, 640, 26), fill=SS), C((XV - 230, 57), 57, fill="#90a4ae"), C((XV + 230, 57), 57, fill="#90a4ae"),
            R((XV - 292, 140, 584, 914), fill="#e8f5e9", sw=2), T("55 gal drum + liner", (XV, 620), 12)]
    plat = [P([(-1500, 0), (-1500, 1016), (-300, 1016), (-300, 762), (-50, 762), (-50, 508), (200, 508), (200, 254), (450, 254), (450, 0)], fill="none", sw=2),
            P([(-1450, 1016), (-1450, 1930), (-350, 1930), (-350, 1016)], closed=False, sw=3, stroke="#546e7a"), T("4-step platform, 40 in top", (-750, 1100), 12)]
    items = [
        item(1, "P1-210", ring, (XC - 1900, 2700), (XC - 1590, 2000)),
        item(2, "P1-211", bin_shapes(b_left, f"B01 {lab['B01']['name'].upper()}") + bin_shapes(b_right, f"B07 {lab.get('B07', lab['B01'])['name'].upper()}"),
             (b_left, 2900), (b_left, Y_BIN + 600)),
        item(3, "P1-212", fl + fr, (b_left - 600, 1650), (b_left - 150, FA)),
        item(4, "P1-213", probe, (b_left + 600, 2050), (b_left + 220, Y_BIN + 270)),
        item(5, "P1-214", bfm, (XC - 750, 1500), (XC - 520, 1300)),
        item(6, "P1-220", hop, (XC + 750, 1500), (XC + 300, 1050)),
        item(7, "P1-221", cells, (XC - 900, 1050), (XC - 405, 1080)),
        item(8, "P1-223", valve, (XC + 650, 700), (XC + 70, 600)),
        item(9, "P1-224", screw, (XC + 1350, 420), (XC + 900, 700), name=EQ["P1-224"]["name"]),
        item(10, "P1-301", frame + blender, (XV + 800, 2700), (XV + 300, Y_FLG - 200), name="Ribbon blender 6 cu ft, built (GA P1-301-GA): trough, double ribbons, cover, frame"),
        item(11, "P1-302", grate, (XV - 900, 2700), (XV - 300, Y_FLG + 120)),
        item(12, "P1-331", valve, (XV - 750, 1450), (XV - 70, Y_VOUT + 60)),
        item(13, "P1-304", sock + sieve, (XV - 900, 1150), (XV - 242, 1130), name="Drum-top sifter: 12 mesh screen P1-305 and grate magnet P1-307 on the drum rim"),
        item(14, "P1-306", vib, (XV + 900, 1250), (XV + 430, 1140)),
        item(15, "P1-308", drum, (XV + 800, 800), (XV + 292, 700)),
        item(16, "P1-309", [], (XV + 800, 300), (XV + 300, 127)),
        item(17, "P1-227", plat, (-900, 2200), (-900, 1930)),
    ]
    # ---- plan of the ring (1:40) and stack-up table, drawn in px below the floor
    det = []
    k = 1 / 40 * 96 / IN
    cx, cy = 560, 1640
    det.append(f'<text x="{cx - 380}" y="{cy - 230}" font-size="18" font-weight="bold">PLAN · BIN RING POSITIONS (1:40) · launch assignment from dosing-plan.md</text>')
    import math
    det.append(f'<circle cx="{cx}" cy="{cy}" r="{1590 * k}" fill="none" stroke="#90a4ae" stroke-width="3"/><circle cx="{cx}" cy="{cy}" r="{352 * k}" fill="{STEEL}" stroke="#111" stroke-width="2"/>'
               f'<text x="{cx}" y="{cy + 5}" font-size="12" text-anchor="middle">P1-220</text>')
    for i in range(12):
        a = math.radians(90 - 30 * i - 15)
        x, y = cx + math.cos(a) * 1250 * k, cy - math.sin(a) * 1250 * k
        b = DP["bins"][i] if i < len(DP["bins"]) else None
        fill = "#fff8e1" if b else "#f5f5f5"
        det.append(f'<rect x="{x - 300 * k}" y="{y - 300 * k}" width="{600 * k}" height="{600 * k}" fill="{fill}" stroke="#111" stroke-width="1.5" '
                   f'transform="rotate({-math.degrees(a) + 90},{x},{y})"/>')
        det.append(f'<text x="{x}" y="{y - 2}" font-size="12" font-weight="bold" text-anchor="middle">B{i + 1:02d}</text>'
                   f'<text x="{x}" y="{y + 13}" font-size="10" text-anchor="middle">{escape(b["ingredient"] if b else "spare")}</text>')
        xi, yi = cx + math.cos(a) * 450 * k, cy - math.sin(a) * 450 * k
        det.append(f'<line x1="{cx + math.cos(a) * 1050 * k}" y1="{cy - math.sin(a) * 1050 * k}" x2="{xi}" y2="{yi}" stroke="#ef6c00" stroke-width="3"/>')
    det.append(f'<text x="{cx - 380}" y="{cy + 215}" font-size="12">Feeders (orange) point to the hopper inlet ring Ø560 [22.05]. Spares B10-B12 blanked for growth to 13 blends.</text>')
    stack = [["Ring top (bin lugs rest here)", mm_in(H_RING + 25)], ["Bin rim / lid", mm_in(Y_BIN + 662)], ["Bin outlet flange = feeder inlet", mm_in(Y_BIN)],
             ["Feeder barrel axis (built P1-212)", mm_in(FA)], ["Feeder spout end (sleeve P1-214 to lid stub)", mm_in(FS)], ["Hopper lid, inlet ring Ø560", mm_in(Y_LID)], ["Load-cell mount plate top", mm_in(1028)],
             ["Hopper outlet (4 in TC)", mm_in(Y_HOP)], ["Valve outlet = screw intake top", mm_in(Y_VALVE)], ["Blender cover / screw inlet", mm_in(Y_FLG)],
             ["Blender agitator axis", mm_in(TB + 283)], ["Blender trough bottom", mm_in(TB)], ["Blender valve outlet", mm_in(Y_VOUT)],
             ["Sifter inlet (4 in TC)", mm_in(1235)], ["Sifter seat = drum rim on dolly", mm_in(1054)], ["Screw discharge", mm_in(Y_FLG + 170)]]
    t, h = es.table(1060, 1440, [("HEIGHT STACK-UP (above finished floor)", 420), ("mm [in]", 160)], stack, "STACK-UP", fs=13, rh=20)
    det.append(t)
    conn = [
        ["J1", "P1-211 bin > P1-212 feeder inlet", "4 x M10 x 30 A2-70 on 160 sq", "FDA silicone 3 mm", "25 N·m [18 lbf·ft]"],
        ["J2", "P1-211 lugs > P1-210 ring", "2 x M12 x 40 A2-70 per lug", "-", "70 N·m [52 lbf·ft]"],
        ["J3", "P1-212 spout > P1-220 lid stub", "silicone sleeve 2.5 in + 2 band clamps (scale isolation)", "FDA silicone", "screwdriver"],
        ["J4", "P1-220 lugs > P1-221 cells", "2 x M12 x 40 A2-70 per lug", "-", "70 N·m; check free float"],
        ["J5", "P1-220 > P1-223 valve", "4 in Tri-Clamp 13MHHM", "EPDM FDA", "hand tight"],
        ["J6", "P1-223 > P1-224 intake", "4 in Tri-Clamp + flex sock", "EPDM FDA", "hand tight"],
        ["J7", "P1-224 > P1-301 inlet", "4 in Tri-Clamp at cover collar", "EPDM FDA", "hand tight"],
        ["J8", "P1-301 trough port > P1-331 valve", "4 in Tri-Clamp 13MHHM", "EPDM FDA", "hand tight"],
        ["J9", "P1-331 > P1-304 sifter inlet", "4 in TC + cotton sock", "cotton sock", "drawstring"],
        ["J10", "P1-304 seat > P1-308 drum rim", "3 rubber isolator feet, skirt into liner", "-", "rests (no bolts)"],
        ["J11", "P1-301 trough > frame end plates", "4 x M12 x 35 A2-70 each end", "-", "70 N·m [52 lbf·ft]"],
        ["J12", "P1-210 / P1-301 feet > slab", "1/2 in wedge anchor, 3 in embed", "grout pad", "60 N·m [45 lbf·ft]"],
    ]
    spec = dict(scale=1 / 20, origin=(150 + 1600 * 0.05 * 96 / IN, 1000), floor_from=-1600, floor_to=7700, ceiling=3658, items=items, conn=conn, details=det,
                dims=[dict(dir="v", x=XC - 1700, y1=0, y2=H_RING + 25, label=f"RING {mm_in(H_RING + 25)}", ext=XC - 1615),
                      dict(dir="v", x=XC - 1950, y1=0, y2=Y_BIN + 662, label=f"BIN RIM {mm_in(Y_BIN + 662)}", ext=b_left - 340),
                      dict(dir="v", x=XC + 1850, y1=0, y2=Y_BIN, label=f"BIN OUTLET {mm_in(Y_BIN)}", ext=b_right + 100),
                      dict(dir="v", x=XC + 1050, y1=0, y2=Y_LID, label=f"HOPPER LID {mm_in(Y_LID)}", ext=XC + 380),
                      dict(dir="v", x=XC - 950, y1=0, y2=Y_VALVE, label=f"INTAKE {mm_in(Y_VALVE)}", ext=XC - 350),
                      dict(dir="v", x=BX0 - 250, y1=0, y2=TB, label=f"TROUGH {mm_in(TB)}", ext=XV - 300),
                      dict(dir="v", x=XV + 1350, y1=0, y2=Y_FLG, label=f"COVER {mm_in(Y_FLG)}", ext=XV + 500),
                      dict(dir="v", x=XV + 1150, y1=0, y2=Y_VOUT, label=f"VALVE OUTLET {mm_in(Y_VOUT)}", ext=XV + 100),
                      dict(dir="v", x=7650, y1=0, y2=3658, label="CLEAR 3,658 [144.0] (12 ft)"),
                      dict(dir="h", x1=XC - 1590, x2=XC + 1590, y=H_RING + 400, label=f"RING Ø3,180 [125.20] legs", ext=H_RING),
                      dict(dir="h", x1=BX0, x2=BX1, y=-250, label=f"BLENDER FRAME {mm_in(BX1 - BX0)}", ext=0)],
                notes_at=(SW - 1290, 1335),
                notes=["Section through the ring on the blender axis, looking north. True scale 1:20; heights from CAD and equipment.json.",
                       "Bins B01-B09 per dosing-plan.md; B10-B12 blanked. Only one feeder runs at a time (DosingStation.st).",
                       "The hopper floats on 3 cells: only the silicone sleeves touch it. Check free float before calibration.",
                       "Hand adds and premix are tipped into the P1-224 intake grate at 550 [21.7] after the bin charge.",
                       "Blender built in house (P1-301-GA): no riser stand; a drum on its dolly rolls in from the free end between the legs (664 clear).",
                       "Bond bins, feeders, hopper, screw, blender and sifter to ground (< 10 ohm). Lock out before opening (1910.147)."])
    (OUT / "ASM-P1-001_dosing_and_blending.svg").write_text(es.elevation(spec, "ASM-P1-001 DOSING AND BLENDING", "DH-ASM-P1-001", PROJECT))


# ================================================================== ASM-P1-002 sifting and grinding (1:10)
def asm2():
    XS = 600.0                     # drum / sifter centreline
    Z0 = 994.0                     # sifter skirt bottom (60 into the liner): seat ring rests on the drum rim at 1,054
    zs = Z0 + 60                   # drum rim = seat ring underside (machines/P1-304 design.py z 0)
    zh, zl = zs + 159, zs + 182.5  # lid underside, inlet ferrule top (1,236)
    BAND = "#efe9d0"
    sieve = [R((XS - 235, Z0, 1.5, 60), fill=SS), R((XS + 233.5, Z0, 1.5, 60), fill=SS), R((XS - 340, zs, 680, 6), fill=SS, sw=2),
             R((XS - 242, zs + 6, 2, 30), fill=SS), R((XS + 240, zs + 6, 2, 30), fill=SS),
             R((XS - 330, zs + 6, 30, 30), fill="#263238"), R((XS + 300, zs + 6, 30, 30), fill="#263238"), T("isolator x 3 (R315)", (XS - 470, zs - 30), 11),
             R((XS - 342, zs + 36, 100, 6), fill=SS), R((XS + 242, zs + 36, 100, 6), fill=SS),
             R((XS - 246, zs + 20, 4, 40), fill=BAND), R((XS + 242, zs + 20, 4, 40), fill=BAND), T("flex band", (XS - 420, zs + 70), 11),
             R((XS - 242, zs + 40, 2, 110), fill=STEEL), R((XS + 240, zs + 40, 2, 110), fill=STEEL),
             R((XS - 240, zs + 84, 15, 6), fill=SS), R((XS + 225, zs + 84, 15, 6), fill=SS),
             R((XS - 270, zs + 150, 540, 6), fill=SS), R((XS - 270, zh, 540, 2), fill=SS),
             R((XS - 51, zh + 2, 102, 21.5), hatch="h135", fill="none"), R((XS - 198, zh + 2, 76, 21.5), hatch="h135", fill="none"),
             T("4 draw latches", (XS - 470, zh + 10), 11)]
    screen = [R((XS - 238, zs + 92, 476, 35), fill="none", sw=1.5, stroke="#37474f"), P([(XS - 236, zs + 102), (XS + 236, zs + 102)], closed=False, dash="4,3", sw=2),
              T("12 mesh deck", (XS, zs + 118), 11)]
    magnet = [C((XS + 60 * k, zs + 68), 12.7, fill="#b71c1c") for k in (-2, -1, 0, 1, 2)] + [R((XS - 240, zs + 48, 480, 5), fill="#455a64")]
    vib = [R((XS + 282, zs + 40, 10, 220), fill=SS), R((XS + 292, zs + 20, 160, 260), fill="#ffe0b2"), T("115 V", (XS + 372, zs + 150), 11)]
    chute = [R((XS - 60, zl, 120, 26), hatch="h45", fill="none"), P([(XS - 50, zl + 26), (XS - 50, 1500), (XS + 50, 1500), (XS + 50, zl + 26)], fill="#fffde7", dash="5,3"),
             T("sock from P1-331 valve (outlet 1,261)", (XS + 380, 1400), 11)]
    drum = [R((XS - 320, 114, 640, 26), fill=SS), C((XS - 230, 57), 57, fill="#90a4ae"), C((XS + 230, 57), 57, fill="#90a4ae"),
            R((XS - 292, 140, 584, 914), fill="#e8f5e9", sw=2), T("55 gal drum, poly liner", (XS, 600), 12), T("ground clip", (XS - 160, 980), 10)]
    # hammer mill on its stand, pail under the discharge
    XM = 2300.0
    mill = [R((XM - 350, 0, 50, 900), fill=SS), R((XM + 300, 0, 50, 900), fill=SS), R((XM - 350, 850, 700, 50), fill=SS), R((XM - 350, 250, 700, 40), fill=SS),
            R((XM - 250, 900, 500, 450), fill=STEEL, sw=2.5), C((XM, 1125), 170, fill="none", dash="10,5"), T("rotor + swing hammers", (XM, 1130), 11),
            P([(XM - 180, 960), (XM + 180, 960)], closed=False, dash="4,3", sw=2), T("screen 1/16-3/16 in", (XM, 985), 10),
            R((XM + 250, 1000, 420, 280), fill=SS), T("2 HP motor", (XM + 460, 1150), 12), R((XM + 600, 600, 200, 260), fill="#ffe0b2"), T("starter", (XM + 700, 560), 11)]
    feed = [R((XM - 100, 1350, 200, 6), fill=SS), P([(XM - 55, 1356), (XM + 55, 1356), (XM + 150, 1556), (XM - 150, 1556)], fill=STEEL, sw=2),
            R((XM - 160, 1416, 320, 40), fill="none", dash="5,3")]
    fmag = [C((XM - 60, 1436), 12, fill="#b71c1c"), C((XM, 1436), 12, fill="#b71c1c"), C((XM + 60, 1436), 12, fill="#b71c1c"), R((XM + 150, 1416, 120, 40), fill="#ef9a9a")]
    dis = [R((XM - 100, 894, 200, 6), fill=SS), P([(XM - 55, 894), (XM + 55, 894), (XM + 52, 744), (XM - 52, 744)], hatch="h45", fill="none", sw=2),
           R((XM - 60, 715, 120, 29), hatch="h135", fill="none"), P([(XM - 50, 715), (XM - 70, 430), (XM + 70, 430), (XM + 50, 715)], fill="#fffde7", dash="5,3"),
           R((XM - 150, 40, 300, 380), fill="#e8f5e9", sw=2), R((XM - 170, 0, 340, 40), fill=SS), T("5 gal pail + liner", (XM, 230), 11)]
    duct = [P([(XM - 250, 1300), (XM - 450, 1300), (XM - 450, 1900)], closed=False, sw=5, stroke="#78909c", dash="14,6"), T("150 cfm to P1-310", (XM - 450, 1950), 11),
            P([(XS - 160, zl), (XS - 160, zl + 80), (XS - 520, zl + 80), (XS - 520, 1900)], closed=False, sw=5, stroke="#78909c", dash="14,6"), T("200 cfm to P1-310 (3 in TC dust port)", (XS - 520, 1950), 11)]
    items = [
        item(1, "P1-304", sieve, (XS - 750, 1350), (XS - 243, zs + 100), name="Drum-top sifter rev B (set P1-304-000..900): Ø480 body on 3 isolators, seat Ø680 on the drum rim, skirt, 4 in TC inlet"),
        item(2, "P1-305", screen, (XS + 750, 900), (XS + 200, zs + 110), name="12 mesh 316 cloth in screen deck P1-304-400 (spare deck)"),
        item(3, "P1-307", magnet, (XS + 750, 1550), (XS + 120, zs + 68)),
        item(4, "P1-306", vib, (XS + 900, 1350), (XS + 452, zs + 200)),
        item(5, "P1-331", chute, (XS - 300, 1750), (XS - 50, 1450), name="Blender valve sock and 4 in TC clamp onto the sifter inlet"),
        item(6, "P1-308", drum, (XS - 700, 700), (XS - 292, 700)),
        item(7, "P1-309", [], (XS - 700, 300), (XS - 320, 127)),
        item(8, "P1-320", mill, (XM - 750, 1150), (XM - 250, 1150)),
        item(9, "P1-322", feed + dis, (XM - 600, 1650), (XM - 120, 1520), name="Mill feed hopper (magnet slot) and discharge transition"),
        item(10, "P1-321", fmag, (XM + 650, 1700), (XM + 210, 1436)),
        item(11, "P1-310", duct, (XM - 450, 2150), (XM - 450, 1900), name="Dust pickups to the cartridge collector P1-310 (outside)"),
    ]
    conn = [["J1", "P1-331 valve > P1-304 inlet", "cotton sock over the 4 in TC ferrule", "sock", "drawstring"],
            ["J2", "P1-304-400 deck > ledge", "deck on the 15 mm ledge, lid pads press it; 4 draw latches", "2 mm + 3 mm FDA silicone", "latch, hand"],
            ["J3", "P1-307 magnet", "rests on 2 bars under the deck, lifts out after the deck", "-", "-"],
            ["J4", "P1-304 seat > drum rim", "seat Ø680 on the rim, 3 centring tabs, skirt 60 into the liner", "liner folded over rim", "rests (no bolts)"],
            ["J5", "P1-306 > bracket P1-304-206", "4 x M10 x 35 A2-70, nyloc + thread lock", "-", "45 N·m [33 lbf·ft]"],
            ["J6", "P1-322 feed > P1-320 inlet", "4 x M8 x 20 A2-70 on 170 sq (VERIFY)", "FDA silicone 3 mm", "18 N·m [13 lbf·ft]"],
            ["J7", "P1-321 magnet drawer", "slides through the hopper slot, pull to clean", "-", "-"],
            ["J8", "P1-320 > P1-322 discharge", "4 x M8 x 20 A2-70 on 170 sq (VERIFY)", "FDA silicone 3 mm", "18 N·m"],
            ["J9", "P1-322 outlet > pail", "4 in TC + cotton sock into the pail liner", "sock", "drawstring"],
            ["J10", "P1-320 stand > slab", "4 x 3/8 in wedge anchors", "-", "34 N·m [25 lbf·ft]"]]
    det = []
    sched = [["Sifter screen", "12 mesh 0.023 wire (1.53 mm) 316, Ø450 deck", "check for tears every batch; spare deck on the shadow board"],
             ["Sifter rate", "about 8 lb/min [3.6 kg/min]", "valve throttled: a 147 lb batch empties in about 20 min"],
             ["Sifter magnet", "12 x 12 in rare earth grate under the deck", "wipe every batch, log catches (prerequisite program)"],
             ["Mill screens", "1/16, 1/8, 3/16 in perforated SS", "1/8 in for coarse black pepper (B06)"],
             ["Mill batch", "about 25 lb [11 kg] per run, under 20 min", "keeps the spice below 40 °C [104 °F]; check with an IR gun"],
             ["Mill magnet", "6 x 6 in grate in the feed slot", "tramp metal stops before the hammers (NFPA 61 ignition control)"],
             ["Mill clean", "dry clean between spices; screen and hammers out", "ATP swab before a spice change (P1-701)"],
             ["Dust", "drum vent 200 cfm, mill 150 cfm", "collector P1-310 sized 1,400 cfm (foodsafety.py PASS)"]]
    t, h = es.table(130, 1460, [("SETTING", 200), ("VALUE", 380), ("WHY / CHECK", 600)], sched, "SIFTING AND GRINDING SETTINGS", fs=13, rh=22)
    det.append(t)
    spec = dict(scale=1 / 10, origin=(330 + 1000 * 0.1 * 96 / IN, 1130), floor_from=-900, floor_to=3500, items=items, conn=conn, details=det,
                dims=[dict(dir="v", x=XS + 1000, y1=0, y2=zl, label=f"SIFTER INLET {mm_in(zl)}", ext=XS + 60),
                      dict(dir="v", x=XS + 1150, y1=0, y2=1054, label=f"DRUM RIM {mm_in(1054)}", ext=XS + 292),
                      dict(dir="v", x=XM + 1150, y1=0, y2=1556, label=f"FEED HOPPER TOP {mm_in(1556)}", ext=XM + 150),
                      dict(dir="v", x=XM + 950, y1=0, y2=900, label=f"MILL STAND {mm_in(900)}", ext=XM + 350),
                      dict(dir="h", x1=XS - 340, x2=XS + 340, y=-150, label="SEAT RING Ø680 [26.77]", ext=0),
                      dict(dir="h", x1=XS - 270, x2=XS + 270, y=1620, label="LID + FLANGE Ø540 [21.26]", ext=zh)],
                notes_at=(SW - 1290, 1100),
                notes=["Left: drum-top sifter on the drum under the blender (section, looking north). Right: hammer mill station (looking east). True scale 1:10.",
                       "The sifter rides on the drum: roll the drum in on its dolly, set the sifter on the rim, clamp the sock. No sieve frame, no chute.",
                       "Mill model and flanges VERIFY on the chosen mill; run a grind trial with our peppercorns before ordering.",
                       "Ground spice goes in lined pails to bin B06 (coarse black pepper); the pail lot is the new MES lot.",
                       "Bond sieve, mill and drums to ground; mill motor TEFC; electrical class per the DHA."])
    (OUT / "ASM-P1-002_sifting_and_grinding.svg").write_text(es.elevation(spec, "ASM-P1-002 SIFTING AND GRINDING", "DH-ASM-P1-002", PROJECT))


# ================================================================== ASM-P1-003 pack bench (1:15, two runs)
def asm3():
    Y2 = 2700.0                 # second run drawn above the first, with its own floor
    TT = 914.0                  # table top
    def table_sh(x0, y0=0.0):
        return [R((x0, y0 + TT - 40, 1524, 40), fill=SS, sw=2), R((x0 + 40, y0, 38, TT - 40), fill=SS), R((x0 + 1446, y0, 38, TT - 40), fill=SS),
                R((x0 + 40, y0 + 200, 1444, 25), fill=SS)]
    ZH = 1118.5                 # built filler P1-401 rev B: hopper outlet TC face (machines/P1-401 design.py); cabinet top 760, outlet 1,020
    filler = [R((20, 60, 600, 697), fill=STEEL, sw=2), R((0, 757, 640, 3), fill=SS), R((40, 80, 560, 650), fill="none", dash="6,4"), T("door", (320, 420), 11),
              R((60, 0, 40, 60), fill="#90a4ae"), R((540, 0, 40, 60), fill="#90a4ae"),
              R((269, 772, 102, 936), fill=SS, dash="6,3"), R((85, 1720, 485, 10), fill=SS, sw=2), R((48, 1570, 544, 20), fill=SS),
              P([(290, 1140), (350, 1140), (545, 1440), (95, 1440)], fill=STEEL, sw=2), R((95, 1440, 450, 150), fill=STEEL, sw=2),
              R((85, 1590, 470, 3), fill=SS), R((105, 1593, 170, 40), fill="none", sw=1.5), T("scoop port", (190, 1660), 10),
              R((288, ZH, 64, 21.5), hatch="h135", fill="none")]
    drive = [R((131, 1850, 80, 150), fill="#ffe0b2", sw=2), T("servo 750 W", (171, 2030), 11), R((464, 1730, 80, 160), fill="#ffe0b2"),
             R((294.6, 1020, 50.8, 98.5), fill="#90a4ae"), R((480, 760, 140, 110), fill="#e1f5fe", sw=2), T("HMI", (550, 820), 11),
             R((-260, 0, 300, 60), fill="#90a4ae"), T("foot switch", (-110, 90), 11)]
    nest = [R((200, 849, 240, 6), fill="#c5e1a5"), R((277, 855, 86, 155), fill="#fff", dash="4,3"), T("jar 86 x 155 on the indexed stage", (-170, 1000), 10)]
    tb1 = table_sh(750)
    CX = 1100.0                 # spindle capper P1-412 on TBL-1
    capper = [R((CX - 200, TT, 400, 12), fill=SS, sw=2), R((CX + 95, TT + 12, 51, 650), fill=SS), R((CX + 87, TT + 142, 8, 500), fill="#90a4ae"),
              R((CX - 60, TT + 462, 160, 140), fill=SS), R((CX - 33, TT + 12, 66, 120), fill="#fff", dash="4,3"), T("container in V-nest", (CX - 300, TT + 80), 10)]
    cdrive = [R((CX - 45, TT + 492, 90, 220), fill="#ffe0b2", sw=2), T("1/8 HP", (CX - 160, TT + 650), 11), R((CX - 40, TT + 432, 80, 50), fill="#90a4ae"),
              T("slip clutch", (CX - 200, TT + 460), 10), R((CX - 55, TT + 387, 110, 40), fill="#c5e1a5"), R((CX + 160, TT + 132, 22, 350), fill="#90a4ae"),
              T("gas spring", (CX + 260, TT + 300), 10)]
    sealer = [R((1700, TT, 60, 500), fill=SS), R((1700, TT + 450, 300, 40), fill=SS), R((1900, TT + 230, 210, 220), fill="#ffe0b2"), T("sealer head", (2005, TT + 520), 11)]
    tb2 = table_sh(2300)
    printer = [R((2400, TT, 500, 270), fill="#e1f5fe", sw=2), T("LX910", (2650, TT + 140), 12)]
    LX = 3400.0                 # built wrap labeler P1-404 on TBL-2
    labeler = [R((LX - 260, TT, 520, 8), fill=SS, sw=2), R((LX - 80, TT + 8, 40, 60), fill=SS), R((LX + 40, TT + 8, 40, 60), fill=SS),
               R((LX - 208, TT + 8, 16, 240), fill=SS), R((LX + 192, TT + 8, 16, 240), fill=SS), R((LX - 10, TT + 8, 20, 160), fill=SS),
               P([(LX + 100, TT + 160), (LX + 210, TT + 110)], closed=False, sw=3)]
    ldrive = [C((LX - 60, TT + 58), 25, fill="#90a4ae"), C((LX + 60, TT + 58), 25, fill="#90a4ae"), C((LX, TT + 198), 20, fill="#cfd8dc"),
              C((LX - 200, TT + 258), 90, fill="#fff8e1"), C((LX + 200, TT + 258), 60, fill="#fff8e1"), R((LX - 188, TT + 8, 57, 80), fill="#ffe0b2"),
              C((LX, TT + 116), 33, fill="none", dash="4,3"), T("container rolls on 2 rollers", (LX, TT + 400), 11)]
    MX0, ZB = 3850.0, 905.0     # built detector conveyor P1-406, belt top 905
    md = [R((MX0, ZB - 120, 1500, 120), fill=STEEL, sw=2), R((MX0 + 130, 0, 40, ZB - 120), fill=SS), R((MX0 + 1330, 0, 40, ZB - 120), fill=SS),
          R((MX0 + 110, 0, 80, 8), fill=SS), R((MX0 + 1310, 0, 80, 8), fill=SS), R((MX0 + 130, 280, 1240, 40), fill=SS),
          R((5350, 0, 400, 550), fill="#ffcdd2", sw=2), T("locked reject bin", (5550, 600), 11)]
    mdrive = [R((MX0 + 30, ZB - 4, 1440, 4), fill="#455a64"), C((MX0 + 40, ZB - 32), 30, fill="#90a4ae"), C((MX0 + 1460, ZB - 32), 30, fill="#90a4ae"),
              C((MX0 + 1460, ZB - 32), 50, fill="none", stroke="#e65100", sw=2), T("gearmotor 1/6 HP", (MX0 + 1460, ZB - 130), 10)]
    head = [R((4390, ZB - 150, 420, 620), fill="#ffebee", sw=2.5), R((4390, ZB, 420, 152), fill="#fff"), T("aperture 254 x 152", (4600, ZB + 520), 11),
            R((4910, ZB, 80, 80), fill="#ffe0b2"), T("pusher", (4950, ZB + 110), 10), R((4950, ZB + 470, 60, 350), fill="#90a4ae"), C((4980, ZB + 860), 40, fill="#ffeb3b")]
    floor2 = [R((-200, Y2 - 20, 6300, 20), fill="url(#h45)", sw=0), P([(-200, Y2), (6100, Y2)], closed=False, sw=3)]
    turn = table_sh(0, Y2)[:0] + [R((0, Y2, 762, 40), fill="none"), R((30, Y2, 38, TT - 60), fill=SS), R((694, Y2, 38, TT - 60), fill=SS),
                                  R((0, Y2 + TT - 60, 762, 40), fill=SS), R((250, Y2 + TT - 20, 262, 20), fill="#90a4ae"), R((0, Y2 + TT, 762, 26), fill=STEEL, sw=2),
                                  R((0, Y2 + TT + 26, 3, 25), fill="#111"), R((759, Y2 + TT + 26, 3, 25), fill="#111")]
    tb3 = table_sh(1000, Y2)
    cw = [R((1300, Y2 + TT, 350, 150), fill="#e1f5fe", sw=2), R((1600, Y2 + TT + 150, 40, 400), fill="#90a4ae"), C((1620, Y2 + TT + 590), 30, fill="#a5d6a7"),
          C((1620, Y2 + TT + 650), 30, fill="#ef9a9a"), T("over/under", (1820, Y2 + TT + 560), 11), R((2000, Y2 + TT, 400, 300), fill="#ffcdd2"), T("short units bin", (2200, Y2 + TT + 340), 11)]
    tb4 = table_sh(2900, Y2)
    case = [R((3100, Y2 + TT, 330, 220), fill="#fff3e0", sw=2), T("12-ct RSC", (3265, Y2 + TT + 260), 11), R((3700, Y2 + TT, 200, 180), fill="#e1f5fe"), T("case label", (3800, Y2 + TT + 220), 11)]
    pal = [R((4700, Y2, 1219, 140), fill="#d7ccc8"), R((4750, Y2 + 140, 1100, 900), fill="#fff3e0", dash="8,4"), T("pallet being built (PAL-FG)", (5300, Y2 + 600), 12)]
    items = [
        item(1, "P1-401", filler, (-450, 1500), (95, 1500), name="Auger filler rev B, built (set P1-401-000..900): cabinet, column, drive head, 42 L hopper, stage"),
        item(12, "P1-413", drive, (700, 2150), (211, 1930), name="Filler servo 750 W + drive, agitator motor, tooling, HMI, foot switch (P1-413..417)", qty=1),
        item(2, "P1-410", nest, (700, 1250), (363, 930), name="3D-printed container nests (filler), PETG, no product contact", qty=8),
        item(3, "P1-409", tb1 + tb2 + tb3 + tb4, (1200, 400), (1300, TT - 20), name="Stainless tables 60 x 30 in (TBL-1 cap/seal, TBL-2 label, TBL-3, TBL-4)", qty=4),
        item(4, "P1-412", capper, (1450, 1850), (CX + 120, TT + 600), name="Spindle capper rev B, built (set P1-412-000..900): base, column, rail carriage, V-nest"),
        item(13, "P1-423", cdrive, (700, 1700), (CX - 45, TT + 600), name="Capper gearmotor + KB drive, slip clutch + chucks, rail and gas spring, toggle, controls (P1-422..424, P1-450..453)", qty=1),
        item(5, "P1-403", sealer, (2050, 1700), (2005, TT + 450)),
        item(6, "P1-405", printer, (2650, 1550), (2650, TT + 270)),
        item(7, "P1-404", labeler, (3000, 1700), (LX - 200, TT + 200), name="Wrap labeler, built (GA P1-404-GA): base, roller blocks, spindle posts, peel plate"),
        item(14, "P1-426", ldrive, (3700, 1800), (LX + 200, TT + 300), name="Labeler rollers, stepper + controller, gap sensor, label rolls (P1-425..427)", qty=1),
        item(8, "P1-406", md + mdrive, (4100, 1500), (MX0 + 150, 600), name="Detector conveyor, built (GA P1-406-GA): frame, 6 in belt, gearmotor"),
        item(15, "P1-418", head, (4600, 2100), (4600, ZB + 470), name="Metal detector head + control (used, validated) and reject pusher P1-421", qty=1),
        item(9, "P1-408", turn, (380, Y2 + 1500), (380, Y2 + TT + 26)),
        item(10, "P1-407", cw, (1450, Y2 + 1700), (1450, Y2 + TT + 150)),
        item(11, "P1-411", case + pal + floor2, (3400, Y2 + 1500), (3265, Y2 + TT + 220), name="Case pack: tape gun and stretch-wrap dispenser (Uline), case and pallet labels"),
    ]
    items.sort(key=lambda d: d["n"])
    conn = [["S1", "P1-401 filler (built)", "servo auger by count, trimmed by weight, net + 1.5 %", "nest per container", "12 upm shaker / 8 jar"],
            ["S2", "TBL-1 capping", "P1-412 spindle capper, slip clutch sets torque", "torque check hourly (P1-402)", "53 mm 14 lbf·in, 89 mm 22 lbf·in (set on the clutch)"],
            ["S3", "TBL-1 sealing", "P1-403 handheld over each cap", "pull test 1/hour", "per liner supplier"],
            ["S4", "TBL-2 labels", "P1-405 prints lot + best-by", "first-off check in MES", "label UPC scan"],
            ["S5", "TBL-2 apply", "P1-404 built wrap labeler, gap sensor stops feed", "position ±1.5 mm", "-"],
            ["S6", "P1-406 metal detect", "CCP-1, Fe 1.5 / NFe 2.0 / SS 2.5", "test pieces start + hourly", "reject to locked bin"],
            ["S7", "TBL-3 checkweigh", "every unit on P1-407", "reject under declared", "HB 133 lot check"],
            ["S8", "P1-408 + TBL-4", "accumulate, pack 12-ct case", "GS1 case label", "-"]]
    det = []
    spec = dict(scale=1 / 15, origin=(140 + 600 * (1 / 15) * 96 / IN, 1960), floor_from=-600, floor_to=5900, items=items, conn=conn, details=det,
                conn_title="STATIONS, SETTINGS AND CHECKS", conn_cols=[("STN", 60), ("STATION", 230), ("METHOD / SETTING", 420), ("CHECK", 300), ("RATE / VALUE", 250)],
                dims=[dict(dir="v", x=-450, y1=0, y2=2000, label=f"FILLER {mm_in(2000)}", ext=131),
                      dict(dir="v", x=-300, y1=0, y2=855, label=f"STAGE {mm_in(855)}", ext=0),
                      dict(dir="v", x=2200, y1=0, y2=TT, label=f"TABLE {mm_in(TT)}", ext=2274),
                      dict(dir="v", x=6150, y1=0, y2=ZB, label=f"BELT {mm_in(ZB)}", ext=5350),
                      dict(dir="h", x1=0, x2=5350, y=-250, label="RUN 1: FILL > CAP > SEAL > LABEL > DETECT 5,350 [210.6]", ext=0),
                      dict(dir="h", x1=0, x2=4424, y=Y2 - 250, label=f"RUN 2: TURNTABLE > CHECKWEIGH > CASE PACK {mm_in(4424)}", ext=Y2)],
                notes_at=(SW - 1290, 1150),
                notes=["Two runs of the U-shaped bench (DH-LAY-P1), unfolded and drawn true scale 1:15. Run 2 is drawn above run 1.",
                       "One operator fills, one caps and seals, one labels and packs; the bench is loaded to 29 % (line balance).",
                       "Container change: swap the printed nest and grip, then a first-off label and weight check in the MES.",
                       "Built in house: filler, capper, labeler and the detector conveyor (GA sheets P1-xxx-GA). The detector head P1-418 is bought used: validate on site with certified test pieces.",
                       "All units weighed: under declared are rejected; the lot is accepted by the MES HB 133 check."])
    (OUT / "ASM-P1-003_pack_bench.svg").write_text(es.elevation(spec, "ASM-P1-003 PACK BENCH (BUILT MACHINES)", "DH-ASM-P1-003", PROJECT))


# ================================================================== electrical data (io_p1.json)
def io_data():
    bins = {b["bin"]: b for b in DP["bins"]}
    io = []
    def add(tag, desc, typ, slot, ch, device, cable, addr):
        io.append(dict(tag=tag, desc=desc, type=typ, plc="P1-225", device=device, signal="24 V DC", slot=slot, channel=ch,
                       wire=f"225-{slot:02d}-{ch:02d}", address=addr, cable=cable))
    di1 = [("DI_SafetyOK", "SR-P1 safety relay healthy (e-stops, hopper lid, screw guard)", "SR-P1", "panel"),
           ("DI_ValveClosed", "P1-223 valve closed limit", "P1-223", "W-P02"), ("DI_ValveOpen", "P1-223 valve open limit", "P1-223", "W-P02"),
           ("DI_ScrewRunning", "P1-224 screw contactor K-224 aux", "P1-224", "panel MS-P1"), ("DI_BlenderReady", "P1-301 cover closed and valve shut", "P1-301", "W-P04"),
           ("DI_BlenderHigh", "P1-301 high level probe", "P1-301", "W-P04"), ("DI_DustFanOn", "P1-310 fan running (aux)", "P1-310", "W-P05"),
           ("DI_BlValveClosed", "P1-331 blender valve closed limit", "P1-331", "W-P07"), ("DI_BlValveOpen", "P1-331 blender valve open limit", "P1-331", "W-P07"),
           ("DI_BlCoverOK", "P1-332 cover interlock (via SR-P1 AES input)", "P1-332", "W-P04"), ("DI_BlenderRun", "P1-336 VFD run feedback", "P1-336", "W-P30")]
    for ch, (t, d, dev, cab) in enumerate(di1):
        add(t, d, "DI", 1, ch, dev, cab, f"%IX0.{ch}")
    for i in range(12):
        b = bins.get(f"B{i + 1:02d}")
        add(f"DI_BinLow[{i + 1}]", f"B{i + 1:02d} low level, Soliphant FTM20 ({b['ingredient'] if b else 'spare position'})", "DI", 2, i, "P1-213", f"W-P{11 + i}", f"%IX1.{i}")
    do1 = [("DO_ValveOpen", "P1-223 actuator open command", "P1-223", "W-P02"), ("DO_ScrewRun", "K-224 screw contactor coil (via SR-P1)", "P1-224", "panel MS-P1"),
           ("DO_Horn", "alarm horn", "HN-P1", "W-P06"), ("DO_Beacon", "alarm beacon", "BC-P1", "W-P06"),
           ("DO_BlValveOpen", "P1-331 blender valve open command", "P1-331", "W-P07"), ("DO_SifterVib", "P1-306 sifter vibrator contactor", "P1-306", "panel MS-P1")]
    for ch, (t, d, dev, cab) in enumerate(do1):
        add(t, d, "DO", 3, ch, dev, cab, f"%QX0.{ch}")
    for i in range(12):
        b = bins.get(f"B{i + 1:02d}")
        add(f"DO_Agitator[{i + 1}]", f"B{i + 1:02d} agitator relay KA-{i + 1:02d}" + (" (flow aid fitted)" if b and b["agitator"] else " (no flow aid at launch)"),
            "DO", 4, i, "P1-212", f"W-P{11 + i}", f"%QX1.{i}")
    cables = [dict(cable="W-P02", plc="P1-225", device="P1-223", cores=7, spec="7C x 18 AWG [0.82 mm²] TC-ER, 600 V", from_="P1-225 X2", to="P1-223 actuator"),
              dict(cable="W-P04", plc="P1-225", device="P1-301", cores=5, spec="5C x 18 AWG [0.82 mm²] TC-ER, 600 V", from_="P1-225 X4", to="P1-301 junction box"),
              dict(cable="W-P07", plc="P1-225", device="P1-331", cores=7, spec="7C x 18 AWG [0.82 mm²] TC-ER, 600 V", from_="P1-225 X7", to="P1-331 actuator"),
              dict(cable="W-P05", plc="P1-225", device="P1-310", cores=3, spec="3C x 18 AWG [0.82 mm²] TC-ER, 600 V", from_="P1-225 X5", to="P1-310 starter aux"),
              dict(cable="W-P06", plc="P1-225", device="HN/BC-P1", cores=4, spec="4C x 18 AWG [0.82 mm²] TC-ER", from_="P1-225 X6", to="horn + beacon on panel top")]
    cables += [dict(cable=f"W-P{11 + i}", plc="P1-225", device=f"B{i + 1:02d}", cores=5, spec="5C x 18 AWG [0.82 mm²] shielded TC-ER", from_=f"P1-225 X{11 + i}",
                    to=f"bin B{i + 1:02d} JB (probe + agitator)") for i in range(12)]
    cables += [dict(cable="W-P30", plc="P1-225", device="P1-226 x 9 + P1-336", cores=3, spec="RS-485 1 pair + drain, Belden 3105A, daisy chain", from_="750-652", to="GS21 #1 > #9 > P1-336 blender VFD, 120 ohm end"),
               dict(cable="E-P31", plc="P1-225", device="P1-222", cores=8, spec="Cat 6 S/FTP, Modbus TCP", from_="SW-P1 port 2", to="Rice Lake 880"),
               dict(cable="E-P32", plc="P1-225", device="P1-205", cores=8, spec="Cat 6 S/FTP, OPC UA", from_="SW-P1 port 3", to="MES PC")]
    di = sum(1 for x in io if x["type"] == "DI"); do = sum(1 for x in io if x["type"] == "DO")
    modules = {"P1-225-DI": {"points": di, "modules": 2, "catalog": "WAGO 750-1405 (16 DI)", "spare_pct": round(100 * (32 - di) / 32)},
               "P1-225-DO": {"points": do, "modules": 2, "catalog": "WAGO 750-1504 (16 DO)", "spare_pct": round(100 * (32 - do) / 32)},
               "P1-225-COM": {"points": 10, "modules": 1, "catalog": "WAGO 750-652 RS-485 Modbus RTU", "spare_pct": 25}}
    motors = [dict(tag="M-212-01..09", load="P1-212 built feeders, P1-216 1/3 HP gearmotor each, via GS21 drives", hp=0.33, fla=1.6, qty=9, supply="208 V 1-ph in, 3-ph out", brk="5 x 20 A 2-pole (2 drives each)"),
              dict(tag="M-224", load="P1-224 flexible screw", hp=1, fla=4.6, qty=1, supply="208 V 3-ph", brk="MS-P1 MMS 4-6.3 A"),
              dict(tag="M-301", load="P1-301 built ribbon blender, P1-333 NORD gearmotor via P1-336 VFD", hp=2, fla=7.5, qty=1, supply="208 V 1-ph in, 3-ph out", brk="20 A 2-pole"),
              dict(tag="M-320", load="P1-320 hammer mill", hp=2, fla=7.5, qty=1, supply="208 V 3-ph", brk="MS-P1 MMS 6.3-10 A"),
              dict(tag="M-310", load="P1-310 dust collector fan", hp=2, fla=13.2, qty=1, supply="208 V 1-ph", brk="20 A 2-pole"),
              dict(tag="M-306", load="P1-306 drum-top sifter vibrator", hp=0.25, fla=2.9, qty=1, supply="120 V", brk="15 A 1-pole"),
              dict(tag="M-208", load="P1-208 tumbler gearmotor (DC control)", hp=0.125, fla=2.0, qty=1, supply="120 V", brk="15 A 1-pole")]
    loads = [("P1-401 built filler: P1-413 750 W servo, P1-414 agitator, P1-416 controls", "208 V 1-ph", 8.0, "20 A 2-pole"), ("P1-403 induction sealer", "120 V", 9.0, "15 A dedicated"),
             ("P1-412 spindle capper (P1-422 1/8 HP PMDC)", "120 V", 2.0, "15 A"),
             ("P1-404 built labeler (P1-426 stepper) + P1-405 printer", "120 V", 4.0, "15 A"), ("P1-406 conveyor (P1-420 1/6 HP) + P1-418 head + P1-421 pusher", "120 V", 5.0, "15 A dedicated (clean power)"),
             ("P1-225 PLC panel, 24 V PSU, 880", "120 V", 4.0, "15 A dedicated"), ("P1-205 MES PC + UPS, SW-P1", "120 V", 8.0, "20 A dedicated"),
             ("Scales P1-201/202/407, P1-204 printer", "120 V", 3.0, "15 A"), ("Receptacles and lighting (by electrician)", "120 V", 16.0, "per NEC")]
    network = [("SW-P1", "industrial unmanaged switch 8-port (WAGO 852-1111 class)"), ("P1-225", "WAGO PFC200 750-8212: CODESYS, OPC UA server"),
               ("P1-222", "Rice Lake 880: Modbus TCP gross/net/motion"), ("P1-205", "MES PC: dhmes server :8080, OPC UA client"),
               ("P1-204", "Zebra ZD421t: ZPL bag/case/pallet labels"), ("P1-201/202/407", "Mettler ICS scales (Ethernet option) or USB to PC"),
               ("Office", "router uplink: no internet path to the PLC (firewall)")]
    data = dict(io=io, cables=cables, modules=modules, motors=motors, loads=loads, network=network,
                service=dict(voltage="208Y/120 V 3-ph 4-w", main_a=100, src="assumed for a small light-industrial unit; confirm with the landlord"))
    (HERE / "io_p1.json").write_text(json.dumps(data, indent=1))
    return data


# ================================================================== ELE-P1-001 one-line and network
def ele1(D):
    o = es.frame("ELE-P1-001 POWER ONE-LINE AND NETWORK", "DH-ELE-P1-001", PROJECT)
    sv = D["service"]
    x0, y0 = 120, 120
    o.append(f'<text x="{x0}" y="{y0 - 40}" font-size="22" font-weight="bold">POWER ONE-LINE</text>'
             f'<rect x="{x0}" y="{y0}" width="320" height="70" fill="#fff" stroke="#111" stroke-width="2"/><text x="{x0 + 160}" y="{y0 + 30}" font-size="16" font-weight="bold" text-anchor="middle">UTILITY SERVICE</text>'
             f'<text x="{x0 + 160}" y="{y0 + 54}" font-size="14" text-anchor="middle">{escape(sv["voltage"])}</text>'
             f'<line x1="{x0 + 160}" y1="{y0 + 70}" x2="{x0 + 160}" y2="{y0 + 130}" stroke="#111" stroke-width="3"/><rect x="{x0 + 130}" y="{y0 + 130}" width="60" height="40" fill="#fff" stroke="#111" stroke-width="2"/>'
             f'<text x="{x0 + 210}" y="{y0 + 156}" font-size="14">MAIN {sv["main_a"]} A, panel LP-P1 42-circuit ({escape(sv["src"])})</text>')
    bus = y0 + 230
    o.append(f'<line x1="{x0 + 160}" y1="{y0 + 170}" x2="{x0 + 160}" y2="{bus}" stroke="#111" stroke-width="3"/><line x1="{x0}" y1="{bus}" x2="{x0 + 2100}" y2="{bus}" stroke="#111" stroke-width="6"/>'
             f'<text x="{x0 + 2110}" y="{bus + 6}" font-size="15">208Y/120 V BUS LP-P1</text>')
    groups = [("MS-P1 motor panel (208 V 3-ph, 30 A feeder)", [m for m in D["motors"] if m["supply"] == "208 V 3-ph"]),
              ("P1-226 drive circuits", [m for m in D["motors"] if "GS21" in m["load"]]),
              ("Branch circuits", [m for m in D["motors"] if m["supply"] in ("208 V 1-ph", "120 V")])]
    fx = x0 + 60
    for name, ms in groups:
        amps = sum(m["fla"] * m["qty"] for m in ms)
        big = max((m["fla"] for m in ms), default=0)
        o.append(f'<line x1="{fx}" y1="{bus}" x2="{fx}" y2="{bus + 60}" stroke="#111" stroke-width="3"/><rect x="{fx - 22}" y="{bus + 60}" width="44" height="30" fill="#fff" stroke="#111" stroke-width="2"/>'
                 f'<line x1="{fx}" y1="{bus + 90}" x2="{fx}" y2="{bus + 130}" stroke="#111" stroke-width="3"/>'
                 f'<rect x="{fx - 110}" y="{bus + 130}" width="620" height="34" fill="#e3f2fd" stroke="#111"/><text x="{fx - 100}" y="{bus + 153}" font-size="15" font-weight="bold">{escape(name)} · FLA {amps:.1f} A · NEC 430.24 {1.25 * big + amps - big:.1f} A</text>')
        my = bus + 190
        for m in ms:
            o.append(f'<line x1="{fx}" y1="{my - 10}" x2="{fx}" y2="{my + 8}" stroke="#111" stroke-width="2"/><circle cx="{fx}" cy="{my + 24}" r="16" fill="#fff" stroke="#111" stroke-width="2"/>'
                     f'<text x="{fx}" y="{my + 29}" font-size="13" text-anchor="middle">M</text><text x="{fx + 26}" y="{my + 20}" font-size="13" font-weight="bold">{escape(m["tag"])} {escape(m["load"])}</text>'
                     f'<text x="{fx + 26}" y="{my + 37}" font-size="12">{m["hp"]} HP x {m["qty"]} · {m["fla"]} A each (NEC 430.248/250) · {escape(m["supply"])} · {escape(m["brk"])}</text>')
            my += 58
        fx += 740
    rows = [[n, v, f"{a:.1f} A", b] for n, v, a, b in D["loads"]]
    t, h = es.table(x0, 900, [("OTHER LOADS FROM LP-P1", 420), ("SUPPLY", 140), ("LOAD", 100), ("BREAKER", 300)], rows, "PLUG AND PANEL LOADS (nameplates VERIFY)", fs=13, rh=21)
    o.append(t)
    tot3 = sum(m["fla"] * m["qty"] for m in D["motors"]) + sum(a for _, _, a, _ in D["loads"])
    o.append(f'<text x="{x0}" y="{900 + h + 40}" font-size="15">Connected load about {tot3:.0f} A summed across phases at 208/120 V, so a 100 A service with balanced phases has margin. '
             f'Stamped design to confirm.</text>')
    nx, ny = 1250, 900
    o.append(f'<text x="{nx}" y="{ny - 20}" font-size="20" font-weight="bold">CONTROL NETWORK (one flat plant LAN, no internet path to the PLC)</text>'
             f'<rect x="{nx}" y="{ny}" width="520" height="36" fill="#ede7f6" stroke="#111" stroke-width="2"/><text x="{nx + 10}" y="{ny + 24}" font-size="14" font-weight="bold">{escape(D["network"][0][0])} {escape(D["network"][0][1])}</text>')
    for j, (tg, dv) in enumerate(D["network"][1:]):
        yy = ny + 60 + j * 36
        o.append(f'<line x1="{nx + 20}" y1="{ny + 36}" x2="{nx + 20}" y2="{yy + 13}" stroke="#5e35b1" stroke-width="1.5"/><line x1="{nx + 20}" y1="{yy + 13}" x2="{nx + 40}" y2="{yy + 13}" stroke="#5e35b1" stroke-width="1.5"/>'
                 f'<rect x="{nx + 40}" y="{yy}" width="560" height="28" fill="#fff" stroke="#5e35b1"/><text x="{nx + 46}" y="{yy + 19}" font-size="13"><tspan font-weight="bold">{escape(tg)}</tspan> {escape(dv)}</text>')
    yy = ny + 60 + len(D["network"]) * 36 + 20
    o.append(f'<rect x="{nx}" y="{yy}" width="600" height="30" fill="#fff8e1" stroke="#111"/><text x="{nx + 10}" y="{yy + 20}" font-size="13"><tspan font-weight="bold">W-P30</tspan> RS-485 Modbus RTU from 750-652 to GS21 drives #1-#9 (addresses 1-9)</text>')
    o.append(es.notes(SW - 820, 1300, 796, ["Motor FLA from NEC Tables 430.248 (1-ph) and 430.250 (3-ph) at 208 V; conductors at 125 % FLA.",
                                          "Drive input current from the GS21 manual (VERIFY); 2 drives per 20 A 2-pole breaker.",
                                          "Feeder motors, screw, blender and mill stop on SR-P1 (drive STO and contactor), not on PLC outputs alone.",
                                          "Electrical class in the dosing room per the dust hazard analysis (NFPA 652 / 61).",
                                          "Panels P1-225 and MS-P1 stainless Type 4X, dry-clean area, no hoses.",
                                          "A licensed electrician installs; final design to NEC 2023 and NFPA 79 for machines."]))
    o.append("</svg>")
    (OUT / "ELE-P1-001_power_and_network.svg").write_text("\n".join(o))


# ================================================================== ELE-P1-002 I/O list and cables
def ele2(D):
    svg = es.iolist(D, "ELE-P1-002 I/O LIST, WIRE NUMBERS, CABLES", "DH-ELE-P1-002", PROJECT)
    svg = svg.replace("I/O LIST · PLC-601 and PLC-602", "I/O LIST · P1-225 WAGO PFC200")
    (OUT / "ELE-P1-002_io_list_and_cables.svg").write_text(svg)


# ================================================================== ELE-P1-003 typical wiring
def ele3(D):
    o = es.frame("ELE-P1-003 TYPICAL CONTROL WIRING", "DH-ELE-P1-003", PROJECT)
    L = []
    def line(x1, y1, x2, y2, c="#111", w=2, d=""):
        L.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}" stroke-dasharray="{d}"/>')
    def box(x, y, w, h, t, sub="", fill="#fff"):
        L.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#111" stroke-width="2"/><text x="{x + w / 2}" y="{y + 22}" font-size="15" font-weight="bold" text-anchor="middle">{escape(t)}</text>'
                 + (f'<text x="{x + w / 2}" y="{y + 42}" font-size="12" text-anchor="middle">{escape(sub)}</text>' if sub else ""))
    def wn(x, y, n):
        L.append(f'<rect x="{x - 34}" y="{y - 11}" width="68" height="16" fill="#fffde7" stroke="#b00020" stroke-width="0.8"/><text x="{x}" y="{y + 2}" font-size="11" text-anchor="middle" fill="#b00020">{n}</text>')
    def txt(x, y, s, fs=13, b=False):
        L.append(f'<text x="{x}" y="{y}" font-size="{fs}"{" font-weight=\"bold\"" if b else ""}>{escape(s)}</text>')
    # rails
    txt(100, 90, "A. 24 V DC CONTROL: SAFETY CIRCUIT, BIN B01 CHANNEL, VALVE AND SCREW PERMISSIVES", 20, True)
    line(120, 130, 120, 1150, "#c62828", 4); line(2100, 130, 2100, 1150, "#1565c0", 4)
    txt(70, 125, "+24 V (PS-1, 10 A)", 13, True); txt(2060, 125, "0 V", 13, True)
    # rung 1 safety
    y = 200
    for i, (t, s) in enumerate([("ES-1", "e-stop dosing"), ("ES-2", "e-stop blender"), ("ES-3", "e-stop mill"), ("ZS-220", "hopper lid closed"), ("ZS-224", "screw guard")]):
        x = 220 + i * 260
        line(x - 100 if i else 120, y, x, y); L.append(f'<rect x="{x}" y="{y - 18}" width="120" height="36" fill="#fff" stroke="#111"/>'); txt(x + 8, y - 2, t, 13, True); txt(x + 8, y + 13, s, 10)
        wn(x + 140, y - 14, f"SF-{i + 1:02d}")
        line(x + 120, y, x + 160, y)
    box(1560, y - 30, 300, 70, "SR-P1 safety relay", "dual channel, PL d (Pilz PNOZ s4 class)", "#ffebee")
    line(1380, y, 1560, y); line(1860, y, 2100, y)
    txt(1560, y + 70, "outputs: 13-14 > GS21 STO (all 9), 23-24 > K-224 / K-301 / K-320 coils, 33-34 > DI_SafetyOK", 12)
    wn(1700, y + 90, "225-01-00")
    # rung 2 Soliphant B01
    y = 380
    line(120, y, 300, y); box(300, y - 35, 260, 70, "LS-213-01 Soliphant FTM20", "bin B01, PNP, covered = ON", "#ffe0b2")
    txt(305, y + 55, "BN +24 V   BK signal   BU 0 V", 11)
    line(560, y, 900, y); wn(730, y - 14, "225-02-00")
    box(900, y - 35, 300, 70, "750-1405 slot 2 ch 0", "%IX1.0 DI_BinLow[1]", "#e3f2fd"); line(1200, y, 2100, y)
    txt(1220, y - 10, "W-P11 cores 1-3 (shield to panel ground bar only)", 11)
    # rung 3 agitator
    y = 520
    line(120, y, 900, y); box(900, y - 35, 300, 70, "750-1504 slot 4 ch 0", "%QX1.0 DO_Agitator[1]", "#e3f2fd")
    line(1200, y, 1450, y); wn(1325, y - 14, "225-04-00"); box(1450, y - 35, 260, 70, "KA-01 relay coil", "24 V DC, with diode", "#fff8e1"); line(1710, y, 2100, y)
    txt(1450, y + 55, "KA-01 13-14 switches the B01 agitator motor (W-P11 cores 4-5)", 11)
    # rung 4 valve
    y = 660
    line(120, y, 900, y); box(900, y - 35, 300, 70, "750-1504 slot 3 ch 0", "%QX0.0 DO_ValveOpen", "#e3f2fd"); line(1200, y, 1450, y); wn(1325, y - 14, "225-03-00")
    box(1450, y - 35, 300, 70, "P1-223 actuator OPEN", "24 V DC, spring/power close", "#fff8e1"); line(1750, y, 2100, y)
    y = 760
    line(120, y, 300, y); box(300, y - 30, 200, 60, "ZSO-223", "open limit"); line(500, y, 900, y); wn(700, y - 14, "225-01-02")
    box(900, y - 30, 300, 60, "%IX0.2 DI_ValveOpen", "", "#e3f2fd"); line(1200, y, 2100, y)
    y = 850
    line(120, y, 300, y); box(300, y - 30, 200, 60, "ZSC-223", "closed limit"); line(500, y, 900, y); wn(700, y - 14, "225-01-01")
    box(900, y - 30, 300, 60, "%IX0.1 DI_ValveClosed", "", "#e3f2fd"); line(1200, y, 2100, y)
    # rung 5 screw
    y = 970
    line(120, y, 900, y); box(900, y - 35, 300, 70, "750-1504 slot 3 ch 1", "%QX0.1 DO_ScrewRun", "#e3f2fd"); line(1200, y, 1330, y); wn(1265, y - 14, "225-03-01")
    box(1330, y - 30, 170, 60, "SR-P1 23-24", "safety"); line(1500, y, 1560, y); box(1560, y - 30, 170, 60, "ZSO-223", "hard permissive"); line(1730, y, 1780, y)
    box(1780, y - 35, 220, 70, "K-224 coil", "MS-P1 screw starter", "#fff8e1"); line(2000, y, 2100, y)
    txt(1330, y + 55, "The screw can only run with the valve proven open and the safety circuit made, even if the PLC output is forced.", 11)
    # drive section
    txt(100, 1250, "B. FEEDER DRIVE (TYPICAL OF 9): GS21 #1 FOR BIN B01", 20, True)
    box(140, 1300, 240, 80, "LP-P1 CB-21", "20 A 2-pole, 208 V", "#fff"); line(380, 1340, 520, 1340); wn(450, 1326, "L1/L2-21")
    box(520, 1290, 360, 110, "P1-226 GS21-20P5 #1", "Modbus addr 1 · STO from SR-P1 13-14", "#e3f2fd"); line(880, 1340, 1040, 1340); wn(960, 1326, "U/V/W-12-01")
    L.append(f'<circle cx="1090" cy="1340" r="40" fill="#fff" stroke="#111" stroke-width="2"/><text x="1090" y="1346" font-size="16" text-anchor="middle">M</text>')
    txt(1140, 1335, "M-212-01 feeder 0.5 HP, 230 V 3-ph (P1-212 B01)", 13, True); txt(1140, 1355, "4C x 14 AWG VFD cable, shield bonded both ends", 11)
    line(700, 1400, 700, 1480, "#5e35b1", 2, "6,3"); txt(710, 1470, "RS-485 W-P30: D+/D-/SG daisy chain to #2 ... #9; 120 ohm terminator at #9", 12)
    rows = [["Fast speed", "60 Hz (about 700 L/h)", "FastHz[b] in DosingStation.st"], ["Slow speed", "12 Hz", "SlowHz[b], tuned at SAT"],
            ["Accel / decel", "0.5 s / 0.2 s", "short stop for a clean cut-off"], ["Control source", "Modbus RTU", "P09.00 per GS21 manual (VERIFY)"],
            ["Motor overload", "nameplate FLA", "drive electronic overload"]]
    t, h = es.table(140, 1560, [("DRIVE SETTING", 220), ("VALUE", 260), ("WHERE", 420)], rows, "GS21 SETTINGS (TYPICAL)", fs=13, rh=21)
    L.append(t)
    o += L
    o.append(es.notes(SW - 820, 1340, 796, ["Wire numbers are 225-slot-channel for PLC I/O and SF-nn for the safety loop; every wire is ferruled at both ends.",
                                          "Bins B02-B12 repeat sections A rungs 2-3 and B with their own slot channels, cables W-P12...W-P22 and drives #2-#9.",
                                          "Safety functions are hard-wired through SR-P1. The PLC only reads SR-P1's status.",
                                          "24 V DC: PS-1 10 A for I/O and actuator, PS-2 2 A for the PFC200 and 880 interface (separate fuses).",
                                          "Field cables: 18 AWG [0.82 mm²] TC-ER; shields grounded at the panel end only."]))
    o.append("</svg>")
    (OUT / "ELE-P1-003_typical_wiring.svg").write_text("\n".join(o))


# ================================================================== G-P1-000 cover and index
VIEWS_3D = [("3D-P1-001", "3D assembly: whole plant, every machine placed (cad/plant/DH-P1-plant.step)"),
            ("3D-P1-002", "3D view: dosing and blending"), ("3D-P1-003", "3D view: blender, sifting and drum"),
            ("3D-P1-004", "3D view: grinding, hand weighing and QC hold"), ("3D-P1-005", "3D view: pack bench")]
SHEETS = [("G-P1-000", "Cover and sheet index", "cover"), ("DH-LAY-P1", "Plant layout 1:50, flows, zones, equipment schedule, checks", "LAY-P1_plant_layout"),
          ("DH-PFD-P1-001", "Process flow diagram and stream table", "PFD-P1-001_process_flow"),
          ("DH-ASM-P1-001", "Dosing station and blending train elevation 1:20, ring plan, height stack-up", "ASM-P1-001_dosing_and_blending"),
          ("DH-ASM-P1-002", "Sifting and grinding elevations 1:10, settings", "ASM-P1-002_sifting_and_grinding"),
          ("DH-ASM-P1-003", "Pack bench 1:15: fill, cap, seal, label, metal detect, checkweigh, case pack", "ASM-P1-003_pack_bench"),
          ("P1-301-GA", "Ribbon blender 6 cu ft, built in house: general arrangement and item list", "machines/P1-301-GA"),
          ("P1-212-GA", "Bin screw feeder, built in house (x 9): general arrangement", "machines/P1-212-GA"),
          ("P1-401-GA", "Servo auger filler rev B, built in house: general arrangement (full set machines/P1-401, 18 sheets)", "machines/P1-401-GA"),
          ("P1-406-GA", "Metal detector conveyor, built in house (used head): general arrangement", "machines/P1-406-GA"),
          ("P1-412-GA", "Bench spindle capper rev B, built in house: general arrangement (full set machines/P1-412, 12 sheets)", "machines/P1-412-GA"),
          ("P1-404-GA", "Wrap labeler, built in house: general arrangement", "machines/P1-404-GA"),
          ("DH-ELE-P1-001", "Power one-line and control network", "ELE-P1-001_power_and_network"),
          ("DH-ELE-P1-002", "I/O list, wire numbers and field cable schedule", "ELE-P1-002_io_list_and_cables"),
          ("DH-ELE-P1-003", "Typical control wiring: safety circuit, bin channel, valve and screw, feeder drive", "ELE-P1-003_typical_wiring")]


def cover(parts):
    o = es.frame("G-P1-000 COVER AND SHEET INDEX", "DH-G-P1-000", PROJECT)
    o.append('<text x="120" y="200" font-size="56" font-weight="bold">Down Home Creole</text>'
             '<text x="120" y="270" font-size="36">Phase 1 prototype spice plant · drawing set</text>'
             '<text x="120" y="330" font-size="22">1,000 lb a week of blended seasonings · 5 launch blends, laid out for 13 · bins with automatic dosing · in-house stainless fabrication</text>')
    tot = sum(e["ext_usd"] for e in EQ.values())
    facts = [f"{len(DP['bins'])} of 12 bin positions used; {DP['auto_pct_overall']} % of blend weight dosed automatically",
             f"Built in house: 6 cu ft ribbon blender (no riser stand), {LB['blending']['chosen']['batches']} batches a week; 9 bin feeders",
             "Drum-top sifter 12 mesh with magnet on the drum under the blender; hammer mill with feed magnet for whole spices",
             "Pack bench with built servo auger filler, spindle capper, wrap labeler and detector conveyor (used head, CCP-1)",
             f"Equipment {len(EQ)} lines, ${tot:,.0f} (bought and fabricated), see bom/phase1-bom.xlsx",
             "All dimensions mm [in]; DXF cut files in mm and inch in dxf/"]
    for i, f in enumerate(facts):
        o.append(f'<text x="140" y="{400 + 34 * i}" font-size="20">• {escape(f)}</text>')
    rows = [[n, d] for n, d, _ in SHEETS] + [[p["id"], f"Part sheet: {p['title']}"] for p in parts]
    rows[1:1] = [[n, d] for n, d in VIEWS_3D]
    t, h = es.table(120, 650, [("DRAWING", 260), ("TITLE", 1300)], rows, f"SHEET INDEX ({len(rows)} sheets)", fs=15, rh=26)
    o.append(t)
    o.append(es.notes(SW - 820, 1500, 796, ["Read with README.md and build/build.json (Anatomy Build wizard).",
                                          "VERIFY marks a dimension set by a bought or used machine: measure it before cutting.",
                                          "Status FOR REVIEW: not for construction until the mill and the used detector head are chosen and the bought parts confirmed."]))
    o.append("</svg>")
    (OUT / "G-P1-000_cover.svg").write_text("\n".join(o))


if __name__ == "__main__":
    pfd()
    asm1()
    asm2()
    asm3()
    D = io_data()
    ele1(D)
    ele2(D)
    ele3(D)
    parts = [p for p in json.loads((P1 / "cad" / "parts.json").read_text()) if not p.get("print")]
    parts += json.loads((P1 / "cad" / "machines.json").read_text())["parts"]
    cover(parts)
    print("sheets written")
