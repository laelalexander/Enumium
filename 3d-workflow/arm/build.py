"""python -m arm.build [--payload-lb 5] [--extension-m 1.0]
Sizes the drives, generates + validates every printed part, writes BOM.md."""
import argparse, json, math, sys
from pathlib import Path
from . import design as D, hardware as H
from .actuators import BY_KEY
import pipeline

AMAZON_ITEMS = [  # (item, qty, search terms / spec to check, used for)
    ("1.5 in OD aluminium round tube, 0.065 in wall, 6061 (36 in or 48 in length)", 4, "1.5 inch OD aluminum tube 0.065 wall 48 inch", "2 links + riser + wrist stub (cut to length)"),
    ("Heavy-duty turntable bearing 12 in (rated >= 500 lb)", 1, "12 inch heavy duty lazy susan turntable bearing 1000 lb", "yaw bearing; check bolt circle then set HW.turntable_pcd"),
    ("12 mm hardened/stainless shaft rod, 150 mm", 3, "12mm linear shaft rod 150mm (6 mm too small)", "shoulder/elbow/wrist joint shafts"),
    ("6001-2RS ball bearing 12x28x8", 8, "6001-2RS bearing 12x28x8", "2 per pitch joint + spares"),
    ("12 mm shaft clamping hub with 4-hole flange (aluminium)", 3, "12mm clamping shaft hub flange coupling aluminum", "locks distal link to joint shaft; check bolt circle -> HW.hub_pcd"),
    ("Shaft collars 12 mm", 6, "12mm shaft collar clamp type", "axial retention"),
    ("HTD 5M timing pulley, 15 mm belt, 16T (bore = gearbox output shaft)", 3, "HTD 5M 16 tooth pulley 15mm belt bore 14mm (check bore)", "motor pulleys, one per pitch joint"),
    ("HTD 5M pulley, 12 mm bore, large (see BOM table for teeth)", 3, "HTD 5M pulley 12mm bore 15mm belt", "joint-shaft pulleys: teeth listed below"),
    ("HTD 5M belt, 15 mm wide (lengths listed below)", 3, "HTD 5M timing belt 15mm closed loop", "one per pitch joint, pick closest stock length"),
    ("Stepper driver DM542 (or DM556), 24-48 V", 5, "DM542 stepper driver 4.2A", "4 joints + gripper (gripper may use TB6600)"),
    ("NEMA 17 stepper w/ T8 lead screw 150 mm + nut + 5->8 mm coupler", 1, "NEMA 17 stepper motor T8 lead screw 150mm with nut", "gripper drive"),
    ("8 mm linear rod 150 mm + LM8UU bearings", 2, "8mm linear rod 150mm LM8UU", "gripper slides: 2 rods, 2 bearings"),
    ("24 V 15 A (360 W) power supply", 1, "24V 15A power supply 360W", "motors"),
    ("Arduino Mega 2560 R3", 1, "Arduino Mega 2560 R3", "controller (firmware/arm_controller)"),
    ("E-stop mushroom button, latching, NC", 1, "emergency stop switch latching NC 22mm", "cuts 24 V to all drivers"),
    ("Mechanical limit switches (NC)", 5, "micro limit switch lever 5 pack NC", "homing, one per joint"),
    ("Fuse holder + 20 A fuse, 14 AWG wire, ferrules", 1, "inline fuse holder 20A 14awg", "power distribution"),
    ("M5 screws 16/25/40/60 mm + nuts + washers, M3, M4 heat-set inserts", 1, "M5 socket head screw assortment; M4 heat set inserts", "assembly"),
    ("PETG or nylon-CF filament, 2 kg; TPU for gripper pads", 1, "PETG 1.75mm 1kg x2; TPU 95A", "printed parts"),
    ("Plywood or MDF board 18 x 18 in, 3/4 in", 1, "3/4 inch plywood 18x18", "base; drill hole for yaw gearbox"),
]

def belt_teeth(small_t, ratio, c):
    dp = small_t * 5 / math.pi; dl = dp * ratio
    length = 2 * c + math.pi * (dl + dp) / 2 + (dl - dp) ** 2 / (4 * c)
    return round(length / 5)

def make_bom(d):
    lines = ["# Bill of materials (generated)", "",
             f"Payload {d['payload_lb']} lb, extension {d['extension_in']} in. **Verify every listing's dimensions and shaft sizes before buying; ASINs deliberately omitted because listings change.**", "",
             "## Drives", "", "| Joint | Amazon search | Required N·m | Rated N·m | Margin |", "|---|---|---|---|---|"]
    for j, v in d["joints"].items():
        lines.append(f"| {j} | {BY_KEY[v['drive']].search_terms} | {v['required_nm']} | {v['rated_nm']} | {v['margin']}x |")
    lines.append(f"| yaw | {BY_KEY['n23_20'].search_terms} | (inertia only) | {BY_KEY['n23_20'].rated_nm} | n/a |")
    lines += ["", "## Belt stages (HTD 5M, 15 mm)", "", "| Joint | Ratio | Small / large teeth | Center dist (mm) | Belt teeth (approx) |", "|---|---|---|---|---|"]
    for j, v in d["joints"].items():
        dr = BY_KEY[v["drive"]]; r = round(dr.ratio / 20) if dr.ratio >= 20 else 1
        if j == "wrist": r = 1
        c = H.belt_center_mm(r)
        lines.append(f"| {j} | {r}:1 | 16 / {16 * r} | {c} | {belt_teeth(16, r, c)}T |")
    lines += ["", "## Tube lengths (cut)", "", f"- upper arm: {d['l1_mm'] - 55} mm, forearm: {d['l2_mm'] - 55} mm, riser: ~150 mm, wrist stub: ~120 mm", "",
              "## Other purchased parts", "", "| Item | Qty | Amazon search / check | Used for |", "|---|---|---|---|"]
    lines += [f"| {a} | {q} | {s} | {u} |" for a, q, s, u in AMAZON_ITEMS]
    lines += ["", "## Printed parts", "", "| Part | Qty | Note |", "|---|---|---|"]
    lines += [f"| {n} | {p['qty']} | {p['note']} |" for n, p in d["parts"].items()]
    return "\n".join(lines) + "\n"

def build(payload_lb=5.0, extension_m=1.0, out_root=None):
    d = D.design(payload_lb, extension_m)
    ratios = {j: round(BY_KEY[v["drive"]].ratio / 20) if BY_KEY[v["drive"]].ratio >= 20 else 1
              for j, v in d["joints"].items() if j != "wrist"}
    d["parts"] = {}
    root = Path(out_root or pipeline.HERE / "out" / "arm")
    for name, (code, qty, note) in H.parts(ratios).items():
        spec = {"name": name, "units": "mm", "min_feature_mm": 2.0, "process": "fdm"}
        r = pipeline.run(spec, "import math\n" + code, None, 1, root)
        d["parts"][name] = {"qty": qty, "note": note, "ok": r["ok"], "bbox_mm": r["metrics"].get("bbox_mm"), "errors": r["errors"]}
    (root / "design.json").write_text(json.dumps(d, indent=2))
    (root / "BOM.md").write_text(make_bom(d))
    return d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--payload-lb", type=float, default=5.0)
    ap.add_argument("--extension-m", type=float, default=1.0, help="max 1.219 (4 ft)")
    a = ap.parse_args()
    d = build(a.payload_lb, a.extension_m)
    print(json.dumps({"joints": d["joints"], "parts_ok": {k: v["ok"] for k, v in d["parts"].items()}}, indent=1))
    sys.exit(0 if all(v["ok"] for v in d["parts"].values()) else 1)

if __name__ == "__main__":
    main()
