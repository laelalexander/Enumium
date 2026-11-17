"""Phase 1 layout: about 2,000 sq ft (50 x 40 ft). Coordinates mm, origin SW outside corner, x east, y north.
Running this writes layout.json for tools/plant/layout.py."""
import json, pathlib

HERE = pathlib.Path(__file__).parent
FT = 304.8
W, H = 50 * FT, 40 * FT          # 15,240 x 12,192

L = dict(
    title=dict(title="LAY-P1 PHASE 1 PROTOTYPE LAYOUT", project="Down Home Creole · Phase 1 prototype · 1,000 lb/week, 5 blends (13-blend ready)",
               number="DH-LAY-P1", rev="A", date="2026-11-17", status="FOR REVIEW"),
    building=dict(w=W, h=H, clear_height_mm=12 * FT),
    rules=dict(min_clear_mm=900),
    rooms=[
        dict(name="Receiving & ingredient storage", x=0, y=0, w=9000, h=4000, zone="Z1 warehouse", label_at=(300, 3880)),
        dict(name="Finished goods & shipping", x=9000, y=0, w=W - 9000, h=4000, zone="Z1 warehouse", label_at=(9300, 3250)),
        dict(name="Hygiene vestibule", x=0, y=4000, w=2000, h=3000, zone="support", label_at=(120, 6850), label="Hygiene\nvestibule", compact=True),
        dict(name="Office & QC", x=0, y=7000, w=2000, h=H - 7000, zone="support", label_at=(120, H - 250), compact=True),
        dict(name="Dosing & blending room", x=2000, y=4000, w=6800, h=H - 4000, zone="Z3 high-care dry (exposed product)", label_at=(2300, H - 300)),
        dict(name="Pack room", x=8800, y=4000, w=W - 8800, h=H - 4000, zone="Z3 high-care dry (exposed product)", label_at=(9100, H - 200)),
        dict(name="Dust collector pad (outside)", x=600, y=H + 400, w=2000, h=1600, zone="Z0 outside", wall=False, label_at=(600, H + 2750)),
    ],
    racks=[],
    equipment=[
        dict(tag="P1-101", room="Receiving & ingredient storage", x=1500, y=150),
        *[dict(tag=f"SH-{k + 1}", room="Receiving & ingredient storage", x=300 + k * 1650, y=2300, size=[1524, 610], name="NSF shelving 24 x 60 in (P1-102)") for k in range(5)],
        dict(tag="PAL-RM", room="Receiving & ingredient storage", x=4000, y=150, size=[2500, 1200], name="Floor pallets: salt, garlic, paprika (2 weeks)"),
        dict(tag="P1-103", room="Receiving & ingredient storage", x=7400, y=300),
        dict(tag="P1-210", room="Dosing & blending room", x=2300, y=7300, name="Dosing station: 12-bin ring P1-210/211, feeders P1-212, weigh hopper P1-220"),
        dict(tag="P1-227", room="Dosing & blending room", x=3500, y=6200),
        dict(tag="P1-225", room="Dosing & blending room", x=2100, y=4300, size=[600, 250], name="Dosing controller P1-225 + drives P1-226"),
        dict(tag="P1-224", room="Dosing & blending room", x=5630, y=9300, size=[1000, 400], name="Flexible screw P1-224 (inclined)"),
        dict(tag="P1-301", room="Dosing & blending room", x=6650, y=9100, rot=90),
        dict(tag="P1-304", room="Dosing & blending room", x=6680, y=7900),
        dict(tag="P1-308", room="Dosing & blending room", x=6780, y=7300, size=[560, 560], name="Blend drum on dolly P1-309 under sieve"),
        dict(tag="P1-206", room="Dosing & blending room", x=2800, y=4300, name="Weigh bench P1-206 + hood P1-207 (minors, hand adds)"),
        dict(tag="P1-208", room="Dosing & blending room", x=4500, y=4300),
        dict(tag="HOLD-1", room="Dosing & blending room", x=5500, y=4300, size=[3000, 1100], name="QC hold: 6 drums on dollies"),
        dict(tag="P1-310", room="Dust collector pad (outside)", x=800, y=H + 600),
        dict(tag="P1-401", room="Pack room", x=9100, y=10300),
        dict(tag="TBL-1", room="Pack room", x=9850, y=10250, size=[1524, 762], name="Cap + induction seal table"),
        dict(tag="TBL-2", room="Pack room", x=11400, y=10250, size=[1524, 762], name="Label table (AP360e + LX910)"),
        dict(tag="P1-406", room="Pack room", x=12950, y=10300),
        dict(tag="P1-408", room="Pack room", x=13950, y=8600, size=[762, 762], name="Turntable P1-408"),
        dict(tag="TBL-3", room="Pack room", x=12100, y=8500, size=[1524, 762], name="Checkweigh table (P1-407)"),
        dict(tag="TBL-4", room="Pack room", x=10500, y=8500, size=[1524, 762], name="Case-pack table"),
        dict(tag="PKG", room="Pack room", x=9100, y=4300, size=[2400, 1200], name="Empty containers, caps, labels (1 day)"),
        dict(tag="PAL-FG", room="Pack room", x=12500, y=4300, size=[1220, 1020], name="Pallet being built"),
        dict(tag="FG-1", room="Finished goods & shipping", x=9500, y=600, size=[3700, 1300], name="FG pallets (3 days)"),
    ],
    lines=[["P1-401", "TBL-1", "TBL-2", "P1-406"], ["TBL-4", "TBL-3", "P1-408"], ["SH-1", "SH-2", "SH-3", "SH-4", "SH-5"]],
    linked=[["P1-210", "P1-224"], ["P1-224", "P1-301"], ["P1-301", "P1-304"], ["P1-224", "P1-304"], ["P1-304", "P1-308"], ["P1-210", "P1-227"], ["P1-406", "P1-408"],
            ["P1-206", "P1-208"], ["P1-206", "P1-225"], ["P1-208", "HOLD-1"], ["TBL-3", "P1-408"]],
    doors=[
        dict(name="Roll-up (receiving)", x=600, y=0, w=2400, side="S"),
        dict(name="Roll-up (shipping)", x=13300, y=0, w=2400, side="S"),
        dict(name="Staff entry", x=0, y=5000, w=1000, side="W"),
        dict(name="Ingredients in", x=5000, y=4000, w=1500, side="S"),
        dict(name="Packaging in", x=9000, y=4000, w=1200, side="S"),
        dict(name="Cases out", x=12000, y=4000, w=1200, side="S"),
        dict(name="Released drums", x=8800, y=5600, w=1500, side="E"),
        dict(name="Gowning", x=2000, y=5000, w=1000, side="E"),
    ],
    flows=[
        dict(name="raw in", type="raw", pts=[[1800, 300], [1800, 1950], [5700, 1950], [5700, 4300], [4000, 6800]]),
        dict(name="dose, blend, sieve", type="product", pts=[[3950, 8950], [6200, 9500], [7100, 9500], [7050, 8200], [7050, 7600]]),
        dict(name="drum to QC hold", type="product", pts=[[7050, 7300], [7050, 5500]]),
        dict(name="released drum to filler", type="product", pts=[[8000, 5000], [8800, 6300], [9400, 10250]]),
        dict(name="containers along the bench", type="product", pts=[[9500, 10650], [14400, 10650], [14300, 9000], [11000, 8900]]),
        dict(name="packaging in", type="packaging", pts=[[8600, 2800], [9600, 3600], [9600, 4300]]),
        dict(name="cases to pallet, pallet to FG", type="finished", pts=[[11000, 8500], [12900, 5400], [12600, 4000], [12000, 1900], [14500, 300]]),
        dict(name="staff", type="people", pts=[[300, 5500], [1500, 5500], [2400, 5500]]),
        dict(name="dust to collector", type="waste", pts=[[3500, 4800], [2200, 6500], [2200, 12000], [1600, 12900]]),
    ],
    dims=[dict(dir="h", x1=9100, x2=14450, y=9950, label=f"PACK BENCH {14450 - 9100:,} [{(14450 - 9100) / FT:.1f} ft]"),
          dict(dir="v", x=2150, y1=7300, y2=10630, label="DOSING RING 3,330 [10.9 ft]")],
    notes=[
        "About 2,000 sq ft (50 x 40 ft) light-industrial or food-grade unit; 12 ft clear is enough (no bulk bags in Phase 1).",
        "Dosing station: 12 bin positions (9 used for the 5 launch blends); bins are loaded from the rolling platform P1-227.",
        "Blend path: weigh hopper > flexible screw > 6 cu ft blender > discharge chute > sieve + magnet > lined drum > QC hold > filler.",
        "Metal detection (CCP-1) is on the finished pack (P1-406), after labeling, with a locked reject bin.",
        "Z3 rooms: sealed epoxy floor, coved base, washable ceiling; enter only through the hygiene vestibule.",
        "Footprints from equipment.json (Phase 1); used-machine sizes are estimates until the unit is chosen.",
    ],
)

if __name__ == "__main__":
    (HERE / "layout.json").write_text(json.dumps(L, indent=1))
    print("layout.json written")
