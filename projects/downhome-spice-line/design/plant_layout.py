"""Plant layout data for the Down Home Creole dry plant (LAY-001) and the storage calculation behind the rack count.

Coordinates in mm, origin at the south-west outside corner of the building, x east, y north.
Each equipment placement is the lower-left corner of its footprint (equipment.json); rot 90 swaps L and W.
Running this file writes layout.json and storage.json, then layout.py draws and checks it.
"""
import json, math, pathlib

HERE = pathlib.Path(__file__).parent
FT = 304.8
basis = json.loads((HERE / "design-basis.json").read_text())

# ------------------------------------------------------------------ storage requirement -> rack positions
POS_PER_BAY = 8                     # 2 pallets per beam level x (3 beam levels + floor)
RAW_WEEKS, PKG_WEEKS, FG_DAYS = 2, 1, 3


def raw_positions():
    lb_by_ing = {}
    for d in basis["demand"]:
        f = basis["formulas"][d["formula"]]
        tot = sum(f["lines"].values())
        for i, p in f["lines"].items():
            lb_by_ing[i] = lb_by_ing.get(i, 0) + d["weekly_lb"] * p / tot * RAW_WEEKS
    rows, n = [], 0
    for i, lb in sorted(lb_by_ing.items(), key=lambda x: -x[1]):
        dens = basis["ingredients"][i]["density"]
        pallet_lb = min(2000, dens * 62.428 * 40)          # 48 x 40 in pallet, ~40 cu ft of bags, 2,000 lb cap
        k = max(1, math.ceil(lb / pallet_lb))
        if i == "salt":
            k = max(1, math.ceil(lb / 2000))                 # salt in 2,000 lb bulk bags, floor-stacked on rack floor level
        rows.append(dict(ingredient=i, lb=round(lb), pallet_lb=round(pallet_lb), positions=k)); n += k
    return n, rows


raw_n, raw_rows = raw_positions()
wk_units = {}
for d in basis["demand"]:
    wk_units[d["container"]] = wk_units.get(d["container"], 0) + d["weekly_units"]
UNITS_PER_PALLET = {"shaker-250": 2600, "jar-12": 1100, "pouch-12": 6000, "tub-5lb": 160, "box-16": 3000}   # estimate, confirm with supplier pallet specs
pkg_rows = [dict(item=c, units=round(u * PKG_WEEKS), per_pallet=UNITS_PER_PALLET[c], positions=math.ceil(u * PKG_WEEKS / UNITS_PER_PALLET[c]))
            for c, u in wk_units.items()]
pkg_n = sum(r["positions"] for r in pkg_rows) + 6        # + caps, labels, liners, cases, tape, film (estimate)
fg_cases = sum(d["weekly_cases"] for d in basis["demand"]) * FG_DAYS / basis["basis"]["days_per_week"]["v"]
fg_n = math.ceil(fg_cases / 90)                          # ~90 cases of 12 per pallet (estimate, set by Ti x Hi at first run)
storage = dict(raw=dict(weeks=RAW_WEEKS, positions=raw_n, rows=raw_rows), packaging=dict(weeks=PKG_WEEKS, positions=pkg_n, rows=pkg_rows),
               finished=dict(days=FG_DAYS, cases=round(fg_cases), positions=fg_n), positions_per_bay=POS_PER_BAY)
bays = {k: math.ceil(storage[k]["positions"] / POS_PER_BAY) for k in ("raw", "packaging", "finished")}
storage["bays"] = bays; storage["total_bays"] = sum(bays.values())

W, H = 140 * FT, 90 * FT          # 42,672 x 27,432 mm


def rack(name, x, y, n, d="x"):
    return dict(name=name, x=x, y=y, bays=n, dir=d, bay_mm=2438, depth_mm=1067, positions_per_bay=POS_PER_BAY)


def split(n, k):
    return [n // k + (1 if i < n % k else 0) for i in range(k)]


rb, pb, fb = split(bays["raw"], 3), split(bays["packaging"], 3), split(bays["finished"], 2)
L = dict(
    title=dict(title="LAY-001 PLANT LAYOUT", project="Down Home Creole · dry blending and packing plant · Growth option 6,000 lb/day",
               number="DH-LAY-001", rev="A", date="2026-11-17", status="FOR REVIEW"),
    building=dict(w=W, h=H, clear_height_mm=22 * FT),
    rules=dict(min_clear_mm=900),
    rooms=[
        dict(name="Raw material warehouse", x=0, y=0, w=15000, h=12000, zone="Z1 warehouse", label_at=(4000, 3800)),
        dict(name="Packaging materials", x=15000, y=0, w=12000, h=12000, zone="Z1 warehouse", label_at=(15400, 3800)),
        dict(name="Utilities & electrical", x=27000, y=0, w=5000, h=6000, zone="support", label_at=(27200, 5600)),
        dict(name="Maintenance", x=27000, y=6000, w=5000, h=6000, zone="support", label_at=(27200, 11600)),
        dict(name="Finished goods & shipping", x=32000, y=0, w=W - 32000, h=12000, zone="Z1 warehouse", label_at=(32400, 3800)),
        dict(name="Weigh & dispense", x=0, y=12000, w=8000, h=8000, zone="Z3 high-care dry (exposed product)", label_at=(300, 19600)),
        dict(name="Hygiene vestibule & lockers", x=0, y=20000, w=4000, h=H - 20000, zone="support", label_at=(200, H - 400)),
        dict(name="Offices, QC lab & IT", x=4000, y=20000, w=4000, h=H - 20000, zone="support", label_at=(4200, H - 400)),
        dict(name="Blending room", x=8000, y=12000, w=12000, h=H - 12000, zone="Z3 high-care dry (exposed product)", label_at=(8300, H - 400)),
        dict(name="Pack room B (wheat)", x=20000, y=12000, w=11000, h=5500, zone="Z3A allergen (wheat) exposed", hatch=True, label_at=(20300, 13700)),
        dict(name="Case & pallet area", x=31000, y=12000, w=W - 31000, h=5500, zone="Z2 controlled (packaging, non-exposed)", label_at=(31300, 17100)),
        dict(name="Packing hall A", x=20000, y=17500, w=W - 20000, h=H - 17500, zone="Z3 high-care dry (exposed product)", label_at=(28000, H - 400)),
        dict(name="Allergen cage (wheat)", x=300, y=4800, w=3048, h=6096, zone="Z1 warehouse", wall=False, hatch=True, label_at=(400, 10700)),
        dict(name="Dust collector pad (outside)", x=12000, y=H + 500, w=3000, h=2500, zone="Z0 outside", wall=False, label_at=(15200, H + 2900)),
    ],
    racks=[
        rack("R1 raw", 3800, 10900, rb[0]), rack("R2 raw", 3800, 4800, rb[1]), rack("R3 raw", 3800, 5867, rb[2]),
        rack("P1 packaging", 15300, 10900, pb[0]), rack("P2 packaging", 15300, 4800, pb[1]), rack("P3 packaging", 15300, 5867, pb[2]),
        rack("F1 finished", 32400, 10900, fb[0]), rack("F2 finished", 32400, 5600, fb[1]),
    ],
    equipment=[
        dict(tag="RCV-101", room="Raw material warehouse", x=11500, y=1000),
        dict(tag="WS-201", room="Weigh & dispense", x=600, y=12700),
        dict(tag="WS-202", room="Weigh & dispense", x=2300, y=12700),
        dict(tag="WS-203", room="Weigh & dispense", x=3600, y=12700, size=[1830, 760], name="WS-203 micro scale on 72 x 30 in SS bench"),
        dict(tag="WS-204", room="Weigh & dispense", x=2300, y=14200, size=[400, 400]),
        dict(tag="PM-210", room="Weigh & dispense", x=4900, y=16800),
        dict(tag="BD-301", room="Blending room", x=9000, y=23800),
        dict(tag="BB-302", room="Blending room", x=9000, y=19800),
        dict(tag="RB-303", room="Blending room", x=12000, y=22000),
        dict(tag="SC-304", room="Blending room", x=15300, y=21900),
        dict(tag="MD-305", room="Blending room", x=15700, y=22300),
        dict(tag="FC-307", room="Blending room", x=17200, y=22100),
        dict(tag="BF-306", room="Blending room", x=17000, y=18800),
        dict(tag="HOLD-1", room="Blending room", x=15000, y=12600, size=[4500, 3200], name="QC hold: 6 filled blend bags awaiting release"),
        dict(tag="CP-300", room="Blending room", x=8150, y=14200, size=[762, 305]),
        dict(tag="DC-310", room="Dust collector pad (outside)", x=12500, y=H + 800),
        dict(tag="AC-311", room="Utilities & electrical", x=27500, y=500),
        dict(tag="AF-312", room="Utilities & electrical", x=29000, y=500),
        dict(tag="SRV-611", room="Offices, QC lab & IT", x=7000, y=20300, size=[600, 1000]),
        dict(tag="BU-401", room="Packing hall A", x=20600, y=23300),
        dict(tag="UN-402", room="Packing hall A", x=20800, y=19700),
        dict(tag="FL-403", room="Packing hall A", x=22700, y=19300),
        dict(tag="CP-404", room="Packing hall A", x=25600, y=19800),
        dict(tag="IS-405", room="Packing hall A", x=28100, y=19980),
        dict(tag="LB-406", room="Packing hall A", x=29200, y=19780),
        dict(tag="VS-408", room="Packing hall A", x=31400, y=20080),
        dict(tag="CW-409", room="Packing hall A", x=32200, y=19880),
        dict(tag="AT-410", room="Packing hall A", x=33900, y=19650),
        dict(tag="CK-412", room="Packing hall A", x=35500, y=19300),
        dict(tag="CE-411", room="Packing hall A", x=35400, y=22200),
        dict(tag="CS-413", room="Packing hall A", x=38200, y=19850),
        dict(tag="PA-414", room="Packing hall A", x=40250, y=19950),
        dict(tag="CP-400", room="Packing hall A", x=26200, y=23000, size=[762, 305]),
        dict(tag="PL-415", room="Case & pallet area", x=40000, y=12700, rot=90),
        dict(tag="SW-416", room="Case & pallet area", x=36000, y=12800),
        dict(tag="BU-502", room="Pack room B (wheat)", x=20500, y=14300, allergen="wheat"),
        dict(tag="NW-501", room="Pack room B (wheat)", x=23300, y=14700, allergen="wheat"),
        dict(tag="BS-503", room="Pack room B (wheat)", x=25700, y=15100),
        dict(tag="IM-504", room="Pack room B (wheat)", x=27000, y=14900),
        dict(tag="CW-506", room="Pack room B (wheat)", x=28000, y=14900),
        dict(tag="TBL-B", room="Pack room B (wheat)", x=28900, y=14600, size=[1830, 760], name="Pack-off table, SS 72 x 30 in"),
    ],
    lines=[["UN-402", "FL-403", "CP-404", "IS-405", "LB-406", "VS-408", "CW-409", "AT-410", "CK-412", "CS-413", "PA-414"],
           ["BU-502", "NW-501", "BS-503", "IM-504", "CW-506", "TBL-B"], ["WS-201", "WS-202", "WS-203"]],
    linked=[["WS-201", "WS-204"], ["RB-303", "MD-305"], ["AC-311", "AF-312"], ["SC-304", "MD-305"], ["MD-305", "FC-307"], ["SC-304", "FC-307"], ["RB-303", "SC-304"], ["CE-411", "CK-412"]],
    doors=[
        dict(name="DOCK 1 (receiving)", x=1500, y=0, w=2700, side="S"), dict(name="DOCK 2 (receiving)", x=6000, y=0, w=2700, side="S"),
        dict(name="DOCK 3 (shipping)", x=34000, y=0, w=2700, side="S"), dict(name="DOCK 4 (shipping)", x=38500, y=0, w=2700, side="S"),
        dict(name="Staff entry", x=0, y=22000, w=1000, side="W"),
        dict(name="Airlock to weigh", x=2500, y=12000, w=2400, side="S"),
        dict(name="Bag door", x=8000, y=13000, w=2400, side="E"),
        dict(name="Bulk bag door", x=20000, y=21000, w=3000, side="E"),
        dict(name="Bag door B", x=20000, y=13000, w=2400, side="E"),
        dict(name="Pkg airlock A", x=21000, y=17500, w=2400, side="S"),
        dict(name="Pkg airlock B", x=22000, y=12000, w=2000, side="S"),
        dict(name="Cases out B", x=31000, y=14000, w=1500, side="E"),
        dict(name="Pallets to FG", x=36000, y=12000, w=3000, side="S"),
    ],
    flows=[
        dict(name="raw in", type="raw", pts=[[3000, 300], [3000, 3600], [14000, 3600], [14000, 9000], [14500, 11500], [3700, 11500], [3700, 12500]]),
        dict(name="weighed kits to blending", type="product", pts=[[6500, 13500], [9200, 13500], [9200, 23000]]),
        dict(name="blend through sifter to bag", type="product", pts=[[13400, 22600], [15900, 22600], [17600, 21000], [18000, 19900]]),
        dict(name="filled bag to QC hold", type="product", pts=[[18000, 18700], [18000, 16000]]),
        dict(name="released bag to line A", type="product", pts=[[19500, 15000], [19500, 21000], [21600, 24000]]),
        dict(name="released bag to station B", type="product", pts=[[19400, 14500], [21500, 15300]]),
        dict(name="line A containers", type="product", pts=[[21400, 20300], [41000, 20300], [41000, 17000], [40900, 15700]]),
        dict(name="empty containers in", type="packaging", pts=[[20500, 6500], [22200, 6500], [22200, 17000], [21400, 19700]]),
        dict(name="pallets to FG", type="finished", pts=[[40800, 12600], [40800, 9000], [37000, 9000], [37000, 600]]),
        dict(name="station B cases", type="finished", pts=[[30700, 15000], [32500, 15000], [34500, 13500], [34500, 9000]]),
        dict(name="staff", type="people", pts=[[500, 22500], [2000, 22500], [2000, 19000], [3500, 19000]]),
        dict(name="dust + bag waste out", type="waste", pts=[[10000, 25500], [10000, 26800], [13500, 26800], [13500, H + 600]]),
    ],
    dims=[
        dict(dir="h", x1=20800, x2=41100, y=26500, label="LINE A  " + f"{41100 - 20800:,} [{(41100 - 20800) / FT:.1f} ft]"),
        dict(dir="v", x=19800, y1=12000, y2=H, label=f"BLENDING ROOM {H - 12000:,.0f} [{(H - 12000) / FT:.1f} ft]"),
    ],
    notes=[
        "Clear height 22 ft [6,706 mm] minimum: bulk bag frames BB-302, BF-306, BU-401, BU-502 are 14 ft [4,270 mm] tall plus forklift lift.",
        "Ribbon blender RB-303 stands on a 1,600 mm [63 in] leg extension so it discharges by gravity through SC-304 and MD-305.",
        "Exposed-product rooms (Z3): sealed epoxy floor sloped 1% to dry-clean points, coved base 4 in, washable ceiling, no overhead ledges.",
        "Wheat products are opened only in Pack room B (Z3A) and the blender on the Friday wheat campaign; room B is held at negative pressure.",
        "Rack positions from storage.json: raw 2 weeks, packaging 1 week, finished goods 3 days (estimate of pallet loads).",
        "Dust collector outside the north wall with explosion vent pointed away from walkways; return no air to the building.",
        "Sizes from equipment.json; maker-documented footprints where published, otherwise estimates to be replaced by vendor GA drawings.",
    ],
)

if __name__ == "__main__":
    (HERE / "layout.json").write_text(json.dumps(L, indent=1))
    (HERE / "storage.json").write_text(json.dumps(storage, indent=1))
    print("rack positions needed:", {k: storage[k]["positions"] for k in ("raw", "packaging", "finished")}, "bays", bays, "total", storage["total_bays"])
