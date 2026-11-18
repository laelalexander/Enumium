"""Build PFD-001, ASM-001, ASM-002, ELE-001 and ELE-002 for the Down Home Creole plant from the design data.

Heights and lengths come from equipment.json (documented where the maker publishes them) and the layout;
elevations are drawn at true scale. Run after design_basis.py, plant_layout.py, io_list.py, equipment.py, linebal.
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent / "drawings"
sys.path.insert(0, str(HERE.parents[2] / "skills" / "anatomy" / "tools" / "plant"))
import engsheets as es  # noqa: E402

EQ = {e["tag"]: e for e in json.loads((HERE / "equipment.json").read_text())}
IO = json.loads((HERE / "io.json").read_text())
LB = json.loads((HERE / "out" / "line-balance.json").read_text())
PROJECT = "Down Home Creole · dry blending and packing plant · 6,000 lb/day"
IN = 25.4


def src(tag):
    e = EQ[tag]
    return f'{e["maker"]} {e["model"]}'[:60]


# ------------------------------------------------------------------ PFD-001
def pfd():
    c = LB["blending"]["chosen"]
    A = LB["pack_lines"][0]; B = LB["pack_lines"][1]
    wk = LB["weekly_lb"]
    U = [
        dict(id="rcv", tag="RCV-101", name="Receive, verify weight\n& COA, quarantine", x=80, y=200, w=300, h=110, fill="#e3f2fd"),
        dict(id="wh", tag="WH-102 / WH-103", name="Raw storage 2 weeks\nwheat in locked cage", x=80, y=420, w=300, h=110, fill="#e3f2fd"),
        dict(id="ws", tag="WS-201/202/203", name="Weigh & dispense\nscan every lot", x=480, y=420, w=300, h=110),
        dict(id="pm", tag="PM-210", name="Premix minors <2%\nwith carrier salt", x=480, y=640, w=300, h=110),
        dict(id="bd", tag="BD-301", name="Bag dump +\nflex screw", x=880, y=420, w=260, h=110),
        dict(id="bb", tag="BB-302", name="Salt bulk bag\nflex screw", x=880, y=200, w=260, h=110),
        dict(id="rb", tag="RB-303", name=f"Ribbon blend {c['working_cuft']} cu ft\nmix 12 min, CV <= 5%", x=1240, y=300, w=320, h=120),
        dict(id="sc", tag="SC-304 + DH-101/102", name="Sift 12 mesh\n+ magnet (CCP-2)", x=1240, y=520, w=320, h=110),
        dict(id="md", tag="MD-305", name="Metal detect\nCCP-1, auto reject", x=1240, y=720, w=320, h=110, fill="#ffebee"),
        dict(id="bf", tag="FC-307 + BF-306", name="Fill blend bag\n1 batch = 1 bag", x=1660, y=720, w=320, h=110),
        dict(id="qc", tag="HOLD-1 / QC", name="QC hold: CV, micro\nrelease in MES", x=1660, y=500, w=320, h=110, fill="#fff3e0"),
        dict(id="la", tag="BU-401 > FL-403 > CP-404 > IS-405", name="Line A fill, cap, seal\nshakers 80 / jars 45 per min", x=2080, y=300, w=420, h=120),
        dict(id="lb2", tag="LB-406 + TT-407 > VS-408 > CW-409", name="Label, code, inspect,\ncheckweigh (reject < declared)", x=2080, y=500, w=420, h=120),
        dict(id="cp", tag="CE-411 > CK-412 > CS-413 > PA-414", name="Erect, cobot pack,\nseal, GS1 case label", x=2080, y=700, w=420, h=120),
        dict(id="pl", tag="PL-415 + SW-416", name="Palletize + wrap\nSSCC pallet label", x=2080, y=900, w=420, h=110),
        dict(id="sb", tag="BU-502 > NW-501 > BS-503/IM-504", name="Station B (wheat room)\npouch, tub, carton", x=1660, y=950, w=320, h=120, fill="#fde8e8"),
        dict(id="fg", tag="FG / ships", name="Finished goods\n3 days, FIFO by lot", x=2080, y=1080, w=420, h=100, fill="#e8f5e9"),
    ]
    S = [
        dict(n=1, frm="rcv", to="wh", name="Ingredients received", material="bags, totes, 2,000 lb salt bags", rate=f"{wk:,.0f} lb/week", basis="design basis 6,000 lb/day x 5 days",
             pts=[(230, 310), (230, 420)]),
        dict(n=2, frm="wh", to="ws", name="Ingredients to weighing", material="bagged majors + minors", rate=f"{wk * 0.7:,.0f} lb/week", basis="all non-salt ingredients"),
        dict(n=3, frm="ws", to="pm", name="Minor kit", material="weighed minors (<2%)", rate="<= 10% of batch with carrier", basis="site premix rule", pts=[(630, 530), (630, 640)]),
        dict(n=4, frm="ws", to="bd", name="Major kit", material="weighed bags on cart", rate=f"{c['batches']} kits/week", basis="line balance"),
        dict(n=5, frm="pm", to="bd", name="Premix", material="premix bag", rate=f"{c['batches']} premixes/week", basis="line balance", pts=[(780, 695), (1010, 695), (1010, 530)]),
        dict(n=6, frm="bb", to="rb", name="Salt", material="salt, fine flake", rate="by weight, 18-38% of batch", basis="site formulas", pts=[(1140, 255), (1400, 255), (1400, 300)]),
        dict(n=7, frm="bd", to="rb", name="Majors + premix", material="dry powders, flakes", rate="6,000 lb/h screw", basis="BD-301 rate (assumed)", pts=[(1140, 475), (1190, 475), (1190, 360), (1240, 360)]),
        dict(n=8, frm="rb", to="sc", name="Blend discharge", material="blend", rate="6,000 lb/h", basis="SC-304 rate (estimate)", pts=[(1400, 420), (1400, 520)]),
        dict(n=9, frm="sc", to="md", name="Sifted blend", material="blend", rate="6,000 lb/h", basis="", pts=[(1400, 630), (1400, 720)]),
        dict(n=10, frm="md", to="bf", name="Metal-free blend", material="blend", rate=f"avg {LB['weekly_lb'] / c['batches']:,.0f} lb/batch", basis="line balance"),
        dict(n=11, frm="bf", to="qc", name="Blend bag to hold", material="FIBC 1 per batch", rate=f"{c['batches']} bags/week", basis="", pts=[(1820, 720), (1820, 610)]),
        dict(n=12, frm="qc", to="la", name="Released bag, line A", material="blend", rate=f"{sum(r['units'] for r in A['rows']):,} units/week", basis="line A", pts=[(1980, 530), (2030, 530), (2030, 360), (2080, 360)]),
        dict(n=13, frm="la", to="lb2", name="Sealed containers", material="filled, capped, induction sealed", rate="80 upm (shaker)", basis="FL-403 rated (assumed)", pts=[(2290, 420), (2290, 500)]),
        dict(n=14, frm="lb2", to="cp", name="Accepted units", material="labeled, coded, weighed", rate="80 upm", basis="", pts=[(2290, 620), (2290, 700)]),
        dict(n=15, frm="cp", to="pl", name="Sealed cases", material="RSC 12-count", rate="6.7 cases/min peak", basis="80 / 12", pts=[(2290, 820), (2290, 900)]),
        dict(n=16, frm="qc", to="sb", name="Released bag, station B", material="blend", rate=f"{sum(r['units'] for r in B['rows']):,} units/week", basis="station B", pts=[(1700, 610), (1700, 950)]),
        dict(n=17, frm="pl", to="fg", name="Pallets", material="wrapped pallet, SSCC", rate="~2.5 pallets/h", basis="~90 cases per pallet (estimate)", pts=[(2290, 1010), (2290, 1080)]),
        dict(n=18, frm="sb", to="fg", name="Station B cases", material="hand-stacked pallet", rate="by campaign", basis="", pts=[(1980, 1010), (2040, 1010), (2040, 1130), (2080, 1130)]),
        dict(n=19, frm="md", to="qc", name="Metal reject", material="rejected blend, locked bin", rate="event", basis="CCP-1 deviation: hold + investigate", color="#c62828", dash="8,5",
             pts=[(1560, 800), (1610, 800), (1610, 560), (1660, 560)]),
    ]
    svg = es.pfd(U, S, "PFD-001 PROCESS FLOW DIAGRAM", "DH-PFD-001", PROJECT, [
        "Rates from design/out/line-balance.json; weekly basis 30,000 lb, 5 days x 1 shift.",
        "CCP-1 metal detection (MD-305); CCP-2 is NOT claimed for the sifter: it is a prerequisite program.",
        "Every lot scanned at weighing; MES links ingredient lots -> batch -> blend bag -> unit lot code.",
        "Wheat (station B) is opened only in Pack room B and on the Friday blender campaign.",
        "Blend bags are released in MES only after CV <= 5% and micro results; unreleased bags cannot be scanned at BU-401/BU-502."])
    (OUT / "PFD-001_process_flow.svg").write_text(svg)


# ------------------------------------------------------------------ ASM-001 blending train elevation (1:20)
def asm001():
    R = lambda xywh, **k: dict(t="rect", xywh=xywh, **k)
    P = lambda pts, **k: dict(t="poly", pts=pts, **k)
    T = lambda s, at, fs=14: dict(t="text", s=s, at=at, fs=fs)
    steel = "#eceff1"
    # blender: trough body bottom at 2,700 (leg extension), length 2,921, body height 1,250, discharge valve at east end
    rb_x0, rb_y0, rb_L, rb_H = 1900, 2700, 2921, 1250
    dvx = rb_x0 + rb_L - 520           # discharge centreline x
    items = [
        dict(n=1, tag="BB-302", name=EQ["BB-302"]["name"], src=src("BB-302"), balloon=(-1500, 5200), target=(-1500, 4270),
             shapes=[R((-2500, 0, 2030, 4270), fill="none", sw=2.5), P([(-2400, 2400), (-570, 2400), (-1300, 1200), (-1700, 1200)], fill=steel),
                     R((-2300, 2600, 1630, 1500), fill="#fffde7", dash="10,5"), T("SALT FIBC 2,000 lb", (-1485, 3400)),
                     P([(-1500, 600), (rb_x0 + 300, rb_y0 + rb_H + 150)], closed=False, sw=5, stroke="#5d4037"), T("4 in flex screw", (-200, 2700))]),
        dict(n=2, tag="BD-301", name=EQ["BD-301"]["name"], src=src("BD-301"), balloon=(400, 3300), target=(760, 2440),
             shapes=[R((0, 0, 1520, 900), fill=steel), P([(0, 900), (1520, 900), (1300, 1150), (220, 1150)], fill=steel), R((150, 1150, 1220, 1290), fill="none", dash="8,4"),
                     T("bag shelf 900 [35.4]", (760, 950), 13), P([(760, 300), (rb_x0 + 700, rb_y0 + rb_H + 150)], closed=False, sw=5, stroke="#5d4037")]),
        dict(n=3, tag="RB-303", name=EQ["RB-303"]["name"] + " on 1,600 mm leg extension", src=src("RB-303"), balloon=(rb_x0 + 400, 4700), target=(rb_x0 + 600, rb_y0 + rb_H),
             shapes=[P([(rb_x0, rb_y0 + 450), (rb_x0, rb_y0 + rb_H), (rb_x0 + rb_L, rb_y0 + rb_H), (rb_x0 + rb_L, rb_y0 + 450), (rb_x0 + rb_L - 300, rb_y0), (rb_x0 + 300, rb_y0)], fill=steel, sw=2.5),
                     R((rb_x0 - 450, rb_y0 + 500, 450, 500), fill="#cfd8dc"), T("15 HP drive", (rb_x0 - 225, rb_y0 + 1100), 12),
                     R((rb_x0 + 100, 0, 120, rb_y0)), R((rb_x0 + rb_L - 220, 0, 120, rb_y0)), R((rb_x0 + 100, 1100, rb_L - 200, 80), fill="#cfd8dc"),
                     T("leg extension 1,600 [63.0] + std legs", (rb_x0 + rb_L / 2, 1300), 13),
                     P([(rb_x0 + 150, rb_y0 + 650), (rb_x0 + rb_L - 150, rb_y0 + 650)], closed=False, dash="20,6,4,6", stroke="#2e7d32", sw=1.5),
                     R((dvx - 150, rb_y0 - 120, 300, 120), fill="#b0bec5"), T("discharge valve", (dvx + 330, rb_y0 - 40), 12)]),
        dict(n=4, tag="DH-101", name="Blender discharge transition chute (custom, drawing DH-101)", src="custom fabricated", balloon=(dvx + 900, 2400), target=(dvx + 120, rb_y0 - 260),
             shapes=[P([(dvx - 125, rb_y0 - 120), (dvx + 125, rb_y0 - 120), (dvx + 76, rb_y0 - 120 - 266), (dvx - 76, rb_y0 - 120 - 266)], fill="url(#h45)", sw=2),
                     R((dvx - 83, rb_y0 - 120 - 295, 166, 29), fill="url(#h135)")]),
        dict(n=5, tag="SC-304", name=EQ["SC-304"]["name"], src=src("SC-304"), balloon=(dvx + 1300, 1900), target=(dvx + 610, 1700),
             shapes=[R((dvx - 610, 1000, 1220, 1290), fill=steel, sw=2.5), R((dvx - 650, 1880, 1300, 60), fill="#90a4ae"), R((dvx - 650, 1500, 1300, 60), fill="#90a4ae"),
                     T("12 mesh screen", (dvx, 1720), 12), R((dvx - 500, 0, 80, 1000)), R((dvx + 420, 0, 80, 1000)),
                     R((dvx + 610, 1150, 300, 160), fill="#fff3e0"), T("overs", (dvx + 760, 1100), 12)]),
        dict(n=6, tag="DH-102", name="Metal detector inlet spool with magnet port (custom, drawing DH-102)", src="custom fabricated", balloon=(dvx - 1000, 1200), target=(dvx - 80, 850),
             shapes=[R((dvx - 76, 700, 152, 300), fill="url(#h45)"), R((dvx - 76 - 60 - 32, 820, 92, 64), fill="url(#h135)")]),
        dict(n=7, tag="MD-305", name=EQ["MD-305"]["name"], src=src("MD-305"), balloon=(dvx - 1100, 600), target=(dvx - 300, 500),
             shapes=[R((dvx - 300, 300, 600, 400), fill="#ffebee", sw=2.5), P([(dvx + 300, 400), (dvx + 700, 250), (dvx + 700, 120)], closed=False, sw=3, stroke="#c62828"),
                     R((dvx + 550, 0, 400, 240), fill="#ffcdd2"), T("locked reject bin", (dvx + 750, -80), 12)]),
        dict(n=8, tag="FC-307", name=EQ["FC-307"]["name"], src=src("FC-307"), balloon=(dvx + 2000, 3900), target=(dvx + 1700, 2600),
             shapes=[P([(dvx - 400, 300), (dvx + 450, 300), (dvx + 300, 0), (dvx - 250, 0)], fill=steel),
                     P([(dvx + 350, 150), (8000 - 300, 4500)], closed=False, sw=6, stroke="#5d4037")]),
        dict(n=9, tag="BF-306", name=EQ["BF-306"]["name"], src=src("BF-306"), balloon=(6500, 4700), target=(6800, 4100),
             shapes=[R((6800, 0, 2130, 4270), fill="none", sw=2.5), R((6900, 0, 1930, 250), fill="#cfd8dc"), T("scale + densifier deck", (7865, 330), 12),
                     R((7365, 400, 1000, 1500), fill="#fffde7", dash="10,5"), T("blend FIBC", (7865, 1150), 13), R((7765, 3900, 200, 600), fill=steel)]),
    ]
    det = []
    # detail A: 6 in Tri-Clamp joint, scale 1:1 is too big for the sheet, drawn at 1:2 in the lower left
    kx = 2 * 96 / IN; dx0, dy0 = 160 - 72 * kx, 1930
    def D(x, y): return dx0 + x * kx, dy0 - y * kx
    fer = [(76.2 - 2.11, 0), (83.4, 0), (83.4, 5.7), (78, 7.1), (78, 28.6), (76.2, 28.6), (76.2 - 2.11, 28.6)]
    for sgn in (1, -1):
        pts = [D(x, sgn * y) for x, y in fer]
        det.append(f'<polygon points="{" ".join(f"{a},{b}" for a, b in pts)}" fill="url(#h45)" stroke="#111" stroke-width="1.5"/>')
    gx0, gy0 = D(76.2 - 2.11, 1.6); gx1, gy1 = D(83.4, -1.6)
    det.append(f'<rect x="{gx0}" y="{gy0}" width="{gx1 - gx0}" height="{gy1 - gy0}" fill="#212121"/>')
    cl = [D(80, 9.5), D(88, 9.5), D(92, 0), D(88, -9.5), D(80, -9.5), D(84.5, 0)]
    det.append(f'<polygon points="{" ".join(f"{a},{b}" for a, b in cl)}" fill="url(#h135)" stroke="#111" stroke-width="1.5"/>')
    det.append(f'<text x="160" y="{dy0 - 250}" font-size="16" font-weight="bold">DETAIL A · 6 in TRI-CLAMP JOINT (J4, J5, J6) · 2:1, half section</text>'
               f'<text x="{D(96, 0)[0]}" y="{dy0 + 4}" font-size="13">ferrule 316L, flange Ø166.8 [6.565] · FDA gasket · 13MHHM clamp</text>')
    conn = [
        ["J1", "BB-302 screw > RB-303 inlet 1", "4 in Tri-Clamp ferrule, flex boot", "EPDM FDA", "hand tight + 1/4 turn"],
        ["J2", "BD-301 screw > RB-303 inlet 2", "4 in Tri-Clamp ferrule, flex boot", "EPDM FDA", "hand tight + 1/4 turn"],
        ["J3", "RB-303 valve > DH-101 flange", "12 x M10 x 30 A2-70 on 210 sq", "DH-106 silicone 3 mm", "25 N·m [18 lbf·ft]"],
        ["J4", "DH-101 > SC-304 inlet", "6 in Tri-Clamp (detail A)", "EPDM FDA", "wing nut, hand tight"],
        ["J5", "SC-304 outlet > DH-102", "6 in Tri-Clamp (detail A)", "EPDM FDA", "wing nut, hand tight"],
        ["J6", "DH-102 > MD-305 inlet", "6 in Tri-Clamp, 300 mm metal-free spool", "EPDM FDA", "wing nut, hand tight"],
        ["J7", "MD-305 outlet > FC-307 hopper", "BFM 150 mm snap-fit spigot", "BFM seal (FDA PU)", "tool-free"],
        ["J8", "FC-307 discharge > BF-306 head", "BFM 150 mm snap-fit spigot", "BFM seal (FDA PU)", "tool-free"],
        ["J9", "RB-303 / BF-306 vents > DC-310", "4 in duct, quick clamp, flap valve", "silicone sleeve", "clamp 5 N·m"],
        ["J10", "RB-303 stand > slab", "4 x Hilti KB-TZ2 5/8 in, 4 in embed", "grout pad", "115 N·m [85 lbf·ft]"],
        ["J11", "DH-102 magnet port", "2 in Tri-Clamp, bullet magnet 10,000 G", "EPDM FDA", "hand tight"],
    ]
    spec = dict(notes_at=(1150, 1720), scale=1 / 20, origin=(100 + 2700 * 0.05 * 96 / IN, 1560), floor_from=-2700, floor_to=9100, ceiling=6706, items=items, conn=conn, details=det,
                dims=[dict(dir="v", x=rb_x0 + rb_L + 650, y1=0, y2=rb_y0 - 120, label=f"VALVE OUTLET {es.mm_in(rb_y0 - 120)}", ext=rb_x0 + rb_L),
                      dict(dir="v", x=rb_x0 - 700, y1=0, y2=rb_y0 + rb_H, label=f"BLENDER TOP {es.mm_in(rb_y0 + rb_H)}", ext=rb_x0),
                      dict(dir="v", x=9200, y1=0, y2=4270, label="FRAME 4,270 [168.11]", ext=8930),
                      dict(dir="v", x=-2650, y1=0, y2=6706, label="CLEAR HEIGHT 6,706 [264.02] (22 ft)"),
                      dict(dir="h", x1=rb_x0, x2=rb_x0 + rb_L, y=rb_y0 + rb_H + 300, label="2,921 [115.00] (Ross 42N-36, documented)", ext=rb_y0 + rb_H),
                      dict(dir="h", x1=dvx - 610, x2=dvx + 610, y=-300, label="Ø1,219 [48.00]", ext=0)],
                notes=["Side elevation looking north. True scale 1:20 on ARCH D; heights from maker data, see SOURCE.",
                       "Gravity train RB-303 > DH-101 > SC-304 > DH-102 > MD-305 > FC-307: every joint opens by hand for dry cleaning.",
                       "DH-101 and DH-102 shown in section (hatched). Verify RB-303 valve flange and MD-305 aperture on certified GA.",
                       "Blender cover and grate interlocks wired to SR-607 (Cat 3 min); lock out before opening (OSHA 1910.147).",
                       "Bond all metal parts in the train to ground (< 10 ohm) against static ignition of spice dust.",
                       "Access platform for blender top supplied with RB-303 leg extension (OSHA 1910.29 guardrails)."])
    (OUT / "ASM-001_blending_train.svg").write_text(es.elevation(spec, "ASM-001 BLENDING TRAIN ELEVATION", "DH-ASM-001", PROJECT))


# ------------------------------------------------------------------ ASM-002 pack line A elevation (1:40)
def asm002():
    R = lambda xywh, **k: dict(t="rect", xywh=xywh, **k)
    P = lambda pts, **k: dict(t="poly", pts=pts, **k)
    T = lambda s, at, fs=13: dict(t="text", s=s, at=at, fs=fs)
    CH = 914      # conveyor top height 36 in
    x0 = 20600
    L = json.loads((HERE / "layout.json").read_text())
    pos = {p["tag"]: p["x"] - x0 for p in L["equipment"]}
    def box(tag, h, fill="#eceff1", y=0, dash=""):
        fp = EQ[tag]["footprint_mm"]
        return R((pos[tag], y, fp[0], h), fill=fill, sw=2.2, dash=dash)
    items, n = [], 0
    spec_rows = [("BU-401", 4270, "#fffde7"), ("UN-402", 1000, "#eceff1"), ("FL-403", 2800, "#ffe0b2"), ("CP-404", 1830, "#eceff1"), ("IS-405", 1600, "#eceff1"),
                 ("LB-406", 1041, "#eceff1"), ("VS-408", 1500, "#e3f2fd"), ("CW-409", 1500, "#eceff1"), ("AT-410", 1000, "#eceff1"), ("CE-411", 2030, "#f5f5f5"),
                 ("CK-412", 2000, "#e3f2fd"), ("CS-413", 1700, "#eceff1"), ("PA-414", 1700, "#eceff1")]
    for tag, h, fill in spec_rows:
        n += 1
        fp = EQ[tag]["footprint_mm"]
        sh = [box(tag, h, fill, dash="10,5" if tag == "CE-411" else "")]
        if tag == "FL-403":
            sh += [P([(pos[tag] + 700, 2800), (pos[tag] + 1100, 2800), (pos[tag] + 1000, 2300), (pos[tag] + 800, 2300)], fill="#ffcc80"), T("twin servo augers", (pos[tag] + 1200, 2000))]
        if tag == "BU-401":
            sh += [P([(pos[tag] + 1000, 600), (pos["FL-403"] + 900, 2950)], closed=False, sw=5, stroke="#5d4037")]
        if tag == "CK-412":
            sh += [P([(pos[tag] + 600, 2000), (pos[tag] + 600, 2600), (pos[tag] + 1500, 2900), (pos[tag] + 1700, 2400)], closed=False, sw=7, stroke="#1565c0"), T("UR10e", (pos[tag] + 1100, 3050))]
        if tag == "LB-406":
            sh += [R((pos[tag] + 700, 1041, 500, 500), fill="#fff"), T("TT-407 on label web", (pos[tag] + 950, 1700))]
        items.append(dict(n=n, tag=tag, name=EQ[tag]["name"], src=src(tag), balloon=(pos[tag] + fp[0] / 2, h + 900 + (n % 3) * 450), target=(pos[tag] + fp[0] / 2, h)))
    n += 1
    cv = [R((0, CH - 60, 20600, 60), fill="#90a4ae")]
    for x in range(1500, 20000, 260):
        cv.append(R((x, CH, 66, 109), fill="#fff", sw=1))       # shaker-250 containers at pitch
    items.append(dict(n=n, tag="CV-417", name=EQ["CV-417"]["name"], src=src("CV-417"), balloon=(19500, 2600), target=(19800, CH), shapes=cv))
    n += 1
    items.append(dict(n=n, tag="DH-104", name="Guide-rail bracket (custom), 36 per line", src="custom fabricated", balloon=(16500, 3300), target=(16800, CH + 40),
                      shapes=[R((x, CH - 20, 60, 80), fill="#263238") for x in range(1300, 20000, 1200)]))
    n += 1
    items.append(dict(n=n, tag="DH-105", name="Photo-eye bracket (custom) + PE-625 sensor, 14 per plant", src="custom fabricated", balloon=(13700, 3500), target=(13300, CH + 150),
                      shapes=[R((x, CH + 100, 40, 120), fill="#6a1b9a") for x in (2000, 4900, 8500, 10500, 11300, 11900, 12800, 13300)]))
    items[0]["shapes"] = items[0].get("shapes", []) + []
    for it in items:
        it.setdefault("shapes", [])
    # attach shapes for machine items
    for it, (tag, h, fill) in zip(items, spec_rows):
        pass
    for i, (tag, h, fill) in enumerate(spec_rows):
        items[i]["shapes"] = items[i].get("shapes") or []
    # rebuild machine shapes (done above in sh); store
    k = 0
    for tag, h, fill in spec_rows:
        fp = EQ[tag]["footprint_mm"]
        sh = [box(tag, h, fill, dash="10,5" if tag == "CE-411" else "")]
        if tag == "FL-403":
            sh += [P([(pos[tag] + 700, 2800), (pos[tag] + 1100, 2800), (pos[tag] + 1000, 2300), (pos[tag] + 800, 2300)], fill="#ffcc80")]
        if tag == "BU-401":
            sh += [P([(pos[tag] + 1000, 600), (pos["FL-403"] + 900, 2950)], closed=False, sw=5, stroke="#5d4037"), R((pos[tag] + 100, 2300, 1800, 1500), fill="#fffde7", dash="10,5")]
        if tag == "CK-412":
            sh += [P([(pos[tag] + 600, 2000), (pos[tag] + 600, 2600), (pos[tag] + 1500, 2900), (pos[tag] + 1700, 2400)], closed=False, sw=7, stroke="#1565c0")]
        if tag == "LB-406":
            sh += [R((pos[tag] + 700, 1041, 500, 500), fill="#fff")]
        items[k]["shapes"] = sh; k += 1
    conn = [
        ["Guide rail width", "CV-417 / DH-104", "70 [2.76]", "90 [3.54]", "slots ±15 [.59]"],
        ["Container Ø x H", "all", "66 x 109 [2.60 x 4.30]", "86 x 155 [3.40 x 6.10]", "site data"],
        ["Filler funnel / starwheel", "FL-403", "53 mm funnel, 66 pocket wheel", "89 mm funnel, 86 pocket wheel", "tool-free"],
        ["Cap chuck / torque", "CP-404", "53 mm, 2.5-2.9 N·m [22-26 in-lb]", "89 mm, 4.5-5.4 N·m [40-48 in-lb]", "verify w/ closure"],
        ["Induction head gap", "IS-405", "3-6 mm above cap", "3-6 mm above cap", "Enercon setup"],
        ["Label", "LB-406", "lbl-84 7.50 x 2.75 in", "lbl-12 9.50 x 3.50 in", "site packaging"],
        ["TTO code", "TT-407", "DHyyjjj-B## + BEST BY", "same", "MES lot rule"],
        ["Checkweigh target", "CW-409", "per SKU from MES", "per SKU from MES", "reject < declared"],
        ["Case / layer pick", "CK-412", "12 = 2 x 6, 1 layer", "12 = 3 x 4, 1 layer", "Omega recipe"],
        ["Line speed", "FL-403 sets", "80 upm (assumed)", "45 upm (assumed)", "confirm on FAT"],
    ]
    spec = dict(scale=1 / 40, origin=(130, 1500), floor_from=-300, floor_to=20900, ceiling=6706, items=items, conn=conn,
                conn_title="CHANGE PARTS AND SETTINGS PER CONTAINER (mm [in])",
                conn_cols=[("SETTING", 230), ("STATION", 190), ("SHAKER-250 (2-4 oz)", 300), ("JAR-12 (12 oz)", 300), ("NOTE", 240)],
                dims=[dict(dir="h", x1=0, x2=20500, y=-500, label="LINE A 20,500 [807.1] = 67'-3\"", ext=0),
                      dict(dir="v", x=-150, y1=0, y2=CH, label="914 [36.0]"),
                      dict(dir="v", x=pos["FL-403"] - 250, y1=0, y2=2800, label="2,800 [110.2] est."),
                      dict(dir="h", x1=pos["FL-403"], x2=pos["CP-404"], y=3400, label=es.mm_in(pos["CP-404"] - pos["FL-403"]), ext=2800)],
                notes=["Elevation of pack line A looking north, true scale 1:40. Conveyor top 914 mm [36 in] for every machine.",
                       "Machine heights: documented where the maker publishes them (CP-404, LB-406), others estimates until OEM GA drawings.",
                       "CE-411 (dashed) sits behind the cobot cell and feeds open cases south into CK-412.",
                       "PL-415 palletizer and SW-416 wrapper are south of the line in the case & pallet area (LAY-001).",
                       "Every machine's own guarding stays; the line adds e-stops ES-626 every <= 10 m and a safety reset per zone.",
                       "Container drawn: shaker-250 (66 x 109 mm) at 260 mm pitch, 80 upm = 20.8 m/min [68 ft/min] < 72 ft/min conveyor."])
    (OUT / "ASM-002_pack_line_A.svg").write_text(es.elevation(spec, "ASM-002 PACK LINE A ELEVATION", "DH-ASM-002", PROJECT))


def ele():
    (OUT / "ELE-001_power_and_network.svg").write_text(es.oneline(IO, "ELE-001 POWER ONE-LINE AND CONTROL NETWORK", "DH-ELE-001", PROJECT))
    (OUT / "ELE-002_io_list_and_cables.svg").write_text(es.iolist(IO, "ELE-002 I/O LIST AND CABLE SCHEDULE", "DH-ELE-002", PROJECT))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    pfd(); asm001(); asm002(); ele()
    print("sheets written to", OUT)
