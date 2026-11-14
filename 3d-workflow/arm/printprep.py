"""Print package for the 3D-printed robot arm parts.   python run.py print [--bed 256x256x256] [--slicer PATH]

  1. Orients every printed part for strength and minimal supports (load paths across layer lines,
     bolt and shaft bores vertical where possible) and writes one STL per part to print/stl/.
  2. Packs all copies (BOM quantities) onto build plates with a shelf packer, writes print/plates/plate_N.stl
     and, if PrusaSlicer is found, a 3MF project and a reference G-code per plate.
  3. Verifies each G-code: every move inside the bed, top layer height = tallest part, filament
     grams and time present, then writes print/REPORT.md.

The slicer profile is print/profiles/petg_structural_bambu256.ini (PETG, 0.4 mm nozzle, 0.2 mm layers,
5 perimeters, 40 % gyroid). The G-code uses a generic start script: for a Bambu printer open the
3MF in Bambu Studio, pick your printer and "Bambu PETG HF" (or your PETG), keep the per-part settings
in this file, slice, and send. The reference G-code is how the parts are verified to fit and print."""
import argparse, json, math, os, re, shutil, subprocess, sys
from pathlib import Path

import cadquery as cq
from . import hardware as H
from .actuators import BY_KEY

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "print"
PROFILE = OUT / "profiles" / "petg_structural_bambu256.ini"
GAP = 10.0  # mm between parts on a plate
BRIM = 5.0  # mm brim on tube_socket and parts over 90 mm tall
EDGE = 5.0  # mm clear of the bed edge (Bambu plates print the full 256 mm; the 245 mm shoulder cheek needs <= 5.3)

# name -> (rotations [(axis, deg)], supports, why).  Rotations apply in order about the part's own origin.
ORIENT = {
    "cheek":           ([((1, 0, 0), -90)], False, "Flat on the 12 mm face: bearing recess and bolt holes vertical, bending loads across layers"),
    "tube_block":      ([((0, 1, 0), -90)], False, "Tube bore vertical: round bore without supports, clamp bolts across layers"),
    "tube_socket":     ([((1, 0, 0), 90)], True, "Hub flange on the bed: flat bolting face, flange bolts vertical; socket needs supports underneath"),
    "base_top_plate":  ([], False, "As modelled: disc on the bed, riser socket up"),
    "gripper_body":    ([((0, 1, 0), 90)], False, "Fixed jaw on the bed: rod and lead-screw bores vertical, no overhangs"),
    "gripper_jaw":     ([((0, 1, 0), -90)], False, "Rod bearing and lead-screw bores vertical for a true sliding fit"),
    "gripper_adapter": ([((0, 1, 0), -90)], False, "Tube socket vertical: round bore, mounting plate as a vertical wall"),
}
SETTINGS = {  # shown in REPORT.md and used for the reference slice
    "Material": "PETG (Bambu PETG HF or similar), 1.75 mm",
    "Nozzle / layer": "0.4 mm / 0.20 mm (first layer 0.20 mm)",
    "Walls": "5 perimeters, 6 top / 5 bottom layers",
    "Infill": "40 % gyroid",
    "Temperatures": "nozzle 250 °C (255 first layer), bed 70 °C",
    "Supports": "only where listed, build plate only",
    "Brim": "5 mm on tube_socket and tall parts over 90 mm",
}


def kind(name):
    for k in ORIENT:
        if k in name:
            return k
    raise KeyError(name)


def ratios_from_design():
    d = json.loads((HERE / "design" / "design.json").read_text(encoding="utf-8"))
    return {j: round(BY_KEY[v["drive"]].ratio / 20) if BY_KEY[v["drive"]].ratio >= 20 else 1
            for j, v in d["joints"].items() if j != "wrist"}


def load(code):
    ns = {"cq": cq, "math": math}
    exec("import math\n" + code, ns)
    r = ns["result"]
    return r.val() if hasattr(r, "val") else r


def oriented(name, code):
    s = load(code)
    rots, sup, why = ORIENT[kind(name)]
    for axis, deg in rots:
        s = s.rotate((0, 0, 0), axis, deg)
    bb = s.BoundingBox()
    s = s.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))
    bb = s.BoundingBox()
    return s, (bb.xlen, bb.ylen, bb.zlen), sup, why


def pack(items, bw, bd):
    """Shelf packing. items: [(key, w, d)] -> plates: [[(key, cx, cy, rotated)]] with centres in bed coords."""
    usable_w, usable_d = bw - 2 * EDGE, bd - 2 * EDGE
    items = sorted(items, key=lambda t: -max(t[1], t[2]))
    plates = []
    for key, w, d in items:
        if w < d and d <= usable_w:
            w, d, rot = d, w, True    # long side along X
        else:
            rot = False
        if w > usable_w or d > usable_d:
            raise ValueError(f"{key} ({w:.0f} x {d:.0f} mm) does not fit a {bw:.0f} x {bd:.0f} bed")
        placed = False
        for pl in plates:
            for sh in pl["shelves"]:
                if sh["x"] + w <= usable_w and d <= sh["h"]:
                    pl["items"].append((key, EDGE + sh["x"] + w / 2, EDGE + sh["y"] + d / 2, rot)); sh["x"] += w + GAP; placed = True; break
            if placed:
                break
            y = pl["shelves"][-1]["y"] + pl["shelves"][-1]["h"] + GAP if pl["shelves"] else 0
            if y + d <= usable_d:
                pl["shelves"].append({"y": y, "h": d, "x": w + GAP})
                pl["items"].append((key, EDGE + w / 2, EDGE + y + d / 2, rot)); placed = True; break
        if not placed:
            plates.append({"shelves": [{"y": 0, "h": d, "x": w + GAP}], "items": [(key, EDGE + w / 2, EDGE + d / 2, rot)]})
    return [p["items"] for p in plates]


def find_slicer(explicit=None):
    cands = [explicit, os.environ.get("PRUSASLICER"), shutil.which("prusa-slicer"), shutil.which("prusa-slicer-console"),
             shutil.which("PrusaSlicer"), r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"]
    return next((c for c in cands if c and Path(c).exists()), None)


def verify(gcode, bw, bd, expect_h):
    xs, ys, zs = [], [], []
    x = y = z = 0.0
    fil_g = time_s = None
    for line in gcode.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(("G0 ", "G1 ")) and "E" in line or line.startswith("G1 Z"):
            for k, v in re.findall(r"([XYZ])(-?\d+\.?\d*)", line):
                if k == "X": x = float(v)
                elif k == "Y": y = float(v)
                else: z = float(v)
            if " E" in line and not re.search(r" E-", line):
                xs.append(x); ys.append(y); zs.append(z)
        elif line.startswith("; total filament used [g]") or line.startswith("; filament used [g]"):
            fil_g = float(re.findall(r"[\d.]+", line.split("=")[1])[0])
        elif line.startswith("; estimated printing time (normal mode)"):
            t = line.split("=")[1]
            time_s = sum(int(n) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u] for n, u in re.findall(r"(\d+)([dhms])", t))
    res = dict(x=(min(xs), max(xs)), y=(min(ys), max(ys)), top=max(zs), grams=fil_g, seconds=time_s)
    errs = []
    if not (0 <= res["x"][0] and res["x"][1] <= bw and 0 <= res["y"][0] and res["y"][1] <= bd):
        errs.append(f"extrusion outside the bed: X {res['x']} Y {res['y']}")
    if abs(res["top"] - expect_h) > 0.45:
        errs.append(f"top layer {res['top']:.2f} mm, expected {expect_h:.2f}")
    if not fil_g or fil_g <= 0:
        errs.append("no filament weight in G-code")
    if not time_s:
        errs.append("no time estimate in G-code")
    res["errors"] = errs
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bed", default="256x256x256", help="W x D x H in mm (Bambu X1/P1/A1: 256x256x256)")
    ap.add_argument("--slicer", help="path to prusa-slicer(-console)")
    ap.add_argument("--no-slice", action="store_true")
    a = ap.parse_args(argv)
    bw, bd, bh = map(float, a.bed.lower().split("x"))
    for sub in ("stl", "plates", "gcode"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    parts = H.parts(ratios_from_design())
    info, items, shapes = {}, [], {}
    for name, (code, qty, note) in parts.items():
        s, (w, d, h), sup, why = oriented(name, code)
        if h > bh:
            sys.exit(f"{name} is {h:.0f} mm tall, bed allows {bh:.0f}")
        cq.exporters.export(s, str(OUT / "stl" / f"{name}.stl"), tolerance=0.01, angularTolerance=0.1)
        shapes[name] = s
        info[name] = dict(qty=qty, note=note, size=(round(w, 1), round(d, 1), round(h, 1)), supports=sup, why=why,
                          volume_cm3=round(s.Volume() / 1000, 1), brim=sup or h > 90)
        m = 2 * BRIM if info[name]["brim"] else 0          # a brim needs its own room: it must stay on the bed
        items += [(f"{name}#{i + 1}", w + m, d + m) for i in range(qty)]
    plates = pack(items, bw, bd)
    slicer = None if a.no_slice else find_slicer(a.slicer)
    report = []
    for pi, plate in enumerate(plates, 1):
        names = []
        for key, cx, cy, rot in plate:
            name = key.split("#")[0]
            s = shapes[name].rotate((0, 0, 0), (0, 0, 1), 90) if rot else shapes[name]
            bb = s.BoundingBox()
            s = s.translate((cx - (bb.xmin + bb.xmax) / 2, cy - (bb.ymin + bb.ymax) / 2, 0))
            f = OUT / "plates" / f"plate_{pi}_{key.replace('#', '_')}.stl"
            cq.exporters.export(s, str(f), tolerance=0.01, angularTolerance=0.1)
            names.append((name, f))
        entry = dict(plate=pi, parts=[n for n, _ in names], height=max(info[n]["size"][2] for n, _ in names))
        if slicer:
            sup = any(info[n]["supports"] for n, _ in names)
            brim = any(info[n]["brim"] for n, _ in names)
            base = [slicer, "--load", str(PROFILE), "--dont-arrange",
                    f"--bed-shape=0x0,{bw:g}x0,{bw:g}x{bd:g},0x{bd:g}", f"--max-print-height={bh:g}",
                    f"--brim-width={BRIM if brim else 0:g}"]
            if sup:
                base += ["--support-material", "--support-material-auto", "--support-material-buildplate-only"]
            files = [str(f) for _, f in names]
            g = OUT / "gcode" / f"plate_{pi}.gcode"
            m3 = OUT / "plates" / f"plate_{pi}.3mf"
            r1 = subprocess.run(base + ["--export-gcode", "--output", str(g)] + files, capture_output=True, text=True)
            r2 = subprocess.run(base + ["--export-3mf", "--output", str(m3)] + files, capture_output=True, text=True)
            if r1.returncode or not g.exists():
                entry["errors"] = [f"slicer failed: {(r1.stderr or r1.stdout).strip()[-400:]}"]
            else:
                entry.update(verify(g, bw, bd, entry["height"]))
            entry["supports"], entry["brim"] = sup, brim
            entry["3mf"] = m3.exists()
        report.append(entry)
        for _, f in names:
            f.unlink()   # per-plate STLs are only slicer input; the 3MF holds the layout
    write_report(info, report, (bw, bd, bh), slicer)
    manifest = {n: dict(i, plates=sorted({e["plate"] for e in report if n in e["parts"]}), print_stl=f"stl/{n}.stl")
                for n, i in info.items()}
    for e in report:
        for n in set(e["parts"]):
            manifest[n].setdefault("plate_check", {})[e["plate"]] = "pass" if not e.get("errors") else "; ".join(e["errors"])
    (OUT / "manifest.json").write_text(json.dumps(dict(bed=[bw, bd, bh], parts=manifest, settings=SETTINGS), indent=1), encoding="utf-8")
    bad = [e for e in report if e.get("errors")]
    print(f"{len(info)} parts, {sum(i['qty'] for i in info.values())} prints, {len(report)} plates -> {OUT}")
    for e in report:
        print(f"  plate {e['plate']}: {', '.join(e['parts'])}" + (f"  {e.get('grams', 0):.0f} g, {fmt_t(e.get('seconds'))}" if 'grams' in e else "")
              + ("  ERRORS: " + "; ".join(e["errors"]) if e.get("errors") else ""))
    if not slicer and not a.no_slice:
        print("PrusaSlicer not found: wrote oriented STLs only. Install it or pass --slicer PATH to slice and verify.")
    return 0 if not bad else 1


def fmt_t(s):
    return "?" if not s else f"{s // 3600}h {s % 3600 // 60:02d}m"


def write_report(info, report, bed, slicer):
    bw, bd, bh = bed
    L = ["# Print package: robot arm printed parts", "",
         f"Generated by `python run.py print --bed {bw:g}x{bd:g}x{bh:g}`. Bed {bw:g} x {bd:g} x {bh:g} mm (Bambu X1 / P1 / A1).", "",
         "## How to print on a Bambu printer", "",
         "1. Open `plates/plate_N.3mf` in Bambu Studio (File > Import). Parts arrive oriented and laid out.",
         "2. Choose your printer, a 0.4 mm nozzle and *Bambu PETG HF* (or your PETG), then apply the settings below.",
         "3. Turn on supports only for plates marked *supports*. Slice, check the preview, send.",
         "",
         "The `gcode/plate_N.gcode` files are reference slices from PrusaSlicer with a generic start script. They are how "
         "each plate was verified (fit, height, filament, time); don't send them to a Bambu printer as-is.", "",
         "## Settings", "", "| Setting | Value |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in SETTINGS.items()]
    L += ["", "## Parts and orientation", "", "| Part | Qty | Size on bed (mm) | Supports | Orientation |", "|---|---|---|---|---|"]
    for n, i in info.items():
        w, d, h = i["size"]
        L.append(f"| [{n}](stl/{n}.stl) | {i['qty']} | {w:g} × {d:g} × {h:g} | {'yes' if i['supports'] else 'no'} | {i['why']} |")
    L += ["", "## Plates", ""]
    if slicer:
        tot_g = sum(e.get("grams") or 0 for e in report); tot_s = sum(e.get("seconds") or 0 for e in report)
        L += ["| Plate | Parts | Height | Filament | Time (est.) | Check |", "|---|---|---|---|---|---|"]
        for e in report:
            ok = "pass" if not e.get("errors") else "FAIL: " + "; ".join(e["errors"])
            parts = ", ".join(f"{p}" for p in e["parts"])
            L.append(f"| {e['plate']}{' (supports)' if e.get('supports') else ''} | {parts} | {e['height']:.0f} mm | "
                     f"{(e.get('grams') or 0):.0f} g | {fmt_t(e.get('seconds'))} | {ok} |")
        L += ["", f"Total: **{tot_g:.0f} g** PETG (about {tot_g / 1000:.2f} kg), **{fmt_t(tot_s)}** at PrusaSlicer's estimate. "
              "Bambu printers run faster; Bambu Studio's estimate will be lower.", "",
              "Each check confirms: all extrusion inside the bed, top layer equals the tallest part, filament weight and time present."]
    else:
        L += ["Not sliced (PrusaSlicer not found). Plate layout:", ""]
        for e in report:
            L.append(f"- Plate {e['plate']}: {', '.join(e['parts'])}")
    L += ["", "## Before printing", "",
          "- The parts are DRAFT rev A. Measure the purchased gearboxes, hubs and turntable and set `HW` in "
          "`arm/hardware.py` first, then rerun `python run.py build` and `python run.py print`.",
          "- Print one `tube_block` first and test-fit the aluminium tube and bolts before printing the rest.",
          "- Ream the 12 mm shaft and 8 mm rod bores after printing; press bearings in with a vise, not a hammer."]
    (OUT / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
