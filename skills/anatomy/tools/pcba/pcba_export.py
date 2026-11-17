#!/usr/bin/env python3
"""Anatomy PCBA export: one turnkey order package (RushPCB-ready) from a KiCad board.

    python pcba_export.py path/to/board.kicad_pcb [--sch board.kicad_sch] [--bom old-bom.csv]
                          [--config pcba.json] [--out DIR] [--qty 5] [--rev A] [--offline]

It writes <out>/<board>-PCBA-rev<rev>/ and a zip of it with:

  01-fabrication/  <board>-gerbers.zip (RS-274X Gerbers + Excellon drill, PTH and NPTH),
                   drill map PDF, FAB-DRAWING.pdf (outline, dims, hole and drill tables, stackup
                   and fab notes, every value in mm [in]), FAB-NOTES.md
  02-assembly/     <board>-BOM.xlsx and .csv (turnkey layout: refdes, qty, manufacturer, MPN,
                   supplier PN, description, package, mount, side, DNP), <board>-centroid.csv
                   and .xlsx (board lower-left origin, mm and inch), ASSEMBLY-DRAWING.pdf (top and
                   bottom, pin 1 / polarity marked), ASSEMBLY-NOTES.md
  03-test/         TEST-NOTES.md (power-up, test points, programming, inspection)
  04-reference/    schematic PDF, board STEP, renders, ERC/DRC reports, KiCad's own pos file
  QUOTE-SHEET.md   values to type into the PCBA quote form
  README.md        READY / NOT READY with every blocker and warning

KiCad's own kicad-cli (KiCad 8 or newer) produces the Gerbers, drill files, DRC/ERC, STEP and
schematic PDF. Everything else is computed from the .kicad_pcb here. --offline skips kicad-cli
(for testing); the package is then marked NOT READY because it has no Gerbers.
"""
import argparse
import csv
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicad_board import load_board  # noqa: E402
from xlsx_lite import write_xlsx  # noqa: E402

MM_PER_IN = 25.4
DEFAULT_FAB = {
    "material": "FR-4, Tg 130-140 (standard)",
    "copper_outer_oz": 1,
    "copper_inner_oz": 0.5,
    "finish": "HASL lead-free",
    "mask_color": "Green",
    "silk_color": "White",
    "ipc_class": "IPC-6012 / IPC-A-600 Class 2",
    "impedance_control": "None",
    "panelization": "Single boards (assembler may panelize with rails; no fiducials on the board)",
    "via_treatment": "Tented",
    "castellated": "No",
    "edge_plating": "No",
}
DEFAULT_ASSEMBLY = {
    "solder": "Lead-free (SAC305), RoHS",
    "workmanship": "IPC-A-610 Class 2",
    "cleaning": "No-clean flux acceptable",
    "conformal_coat": "None",
    "service": "Turnkey (assembler buys all parts)",
}


def inch(mm):
    return mm / MM_PER_IN


def dual(mm, nd=2, ni=3):
    return "%.*f mm [%.*f in]" % (nd, mm, ni, inch(mm))


# ---------------------------------------------------------------- kicad-cli
def find_kicad_cli():
    env = os.environ.get("KICAD_CLI")
    if env and os.path.isfile(env):
        return env
    w = shutil.which("kicad-cli")
    if w:
        return w
    pats = []
    la = os.environ.get("LOCALAPPDATA", "")
    if la:
        pats.append(os.path.join(la, "Programs", "KiCad", "*", "bin", "kicad-cli.exe"))
    for pf in (os.environ.get("ProgramFiles", r"C:\Program Files"), r"C:\Program Files"):
        pats.append(os.path.join(pf, "KiCad", "*", "bin", "kicad-cli.exe"))
    pats += ["/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli", "/usr/bin/kicad-cli", "/usr/local/bin/kicad-cli"]
    found = []
    for p in pats:
        found += glob.glob(p)
    found.sort(key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", p)])
    return found[-1] if found else None


class Cli:
    def __init__(self, exe, log):
        self.exe, self.log = exe, log
        self.version = ""
        if exe:
            r = subprocess.run([exe, "version"], capture_output=True, text=True)
            self.version = (r.stdout or r.stderr).strip()

    def run(self, args, ok_codes=(0,)):
        cmd = [self.exe] + args
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.log.append({"cmd": " ".join('"%s"' % a if " " in a else a for a in cmd), "code": r.returncode,
                         "out": (r.stdout + r.stderr)[-2000:]})
        return r.returncode in ok_codes, r


# ---------------------------------------------------------------- BOM merge
ALIASES = {
    "refs": ["designator", "designators", "refs", "ref", "reference", "references", "refdes", "referencedesignators"],
    "qty": ["qty", "quantity"],
    "value": ["value", "val", "comment"],
    "footprint": ["footprint", "package"],
    "manufacturer": ["manufacturer", "mfr", "mfg", "manufacturername", "mfrname"],
    "mpn": ["mpn", "manufacturerpartnumber", "mfrpn", "mfrpartnumber", "manufacturerpn", "partnumber", "mfgpn"],
    "digikey": ["digikeypartnumber", "digikeypn", "digikey", "digikeypart", "digikeypartno"],
    "mouser": ["mouserpartnumber", "mouserpn", "mouser"],
    "lcsc": ["lcscpart", "lcscpartnumber", "lcsc", "lcscpn", "jlcpcbpart"],
    "description": ["description", "desc"],
    "unit_price": ["unitpriceusd", "unitcostusdest", "unitprice", "unitcost", "price"],
    "dnp": ["dnp", "dnf", "donotplace", "fitted"],
    "notes": ["notes", "note", "comments"],
}
PROP_ALIASES = {
    "manufacturer": ["Manufacturer", "MFR", "Mfr", "Manufacturer_Name", "MANUFACTURER"],
    "mpn": ["MPN", "Manufacturer_Part_Number", "MFR_PN", "Mfr PN", "MPN#", "Part Number", "PartNumber"],
    "digikey": ["Digi-Key_PN", "Digikey", "DigiKey", "Digi-Key Part #", "Digi-Key", "DK_PN"],
    "mouser": ["Mouser", "Mouser_PN", "Mouser Part #"],
    "lcsc": ["LCSC", "LCSC Part #", "LCSC_PN", "JLCPCB"],
    "description": ["Description", "Desc"],
}


def norm(h):
    return re.sub(r"[^a-z0-9]", "", h.lower())


def split_refs(s):
    out = []
    for tok in re.split(r"[\s,;]+", s.strip()):
        if not tok:
            continue
        m = re.match(r"^([A-Za-z_]+)(\d+)-(?:[A-Za-z_]+)?(\d+)$", tok)
        if m:
            out += ["%s%d" % (m.group(1), i) for i in range(int(m.group(2)), int(m.group(3)) + 1)]
        else:
            out.append(tok)
    return out


def read_bom_csv(path):
    """Return {ref: {field: value}} from any of the BOM layouts Anatomy has written."""
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return {}
    hdr = [norm(h) for h in rows[0]]
    col = {}
    for field, names in ALIASES.items():
        for i, h in enumerate(hdr):
            if h in names and field not in col:
                col[field] = i
    if "refs" not in col:
        raise ValueError("%s: no designator/refs column" % path)
    out = {}
    for r in rows[1:]:
        if not r or len(r) <= col["refs"]:
            continue
        rec = {f: r[i].strip() for f, i in col.items() if i < len(r) and f not in ("refs", "qty")}
        for ref in split_refs(r[col["refs"]]):
            out[ref] = rec
    return out


def ref_key(ref):
    m = re.match(r"^([A-Za-z_]+)(\d+)(.*)$", ref)
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (ref, 0, "")


def classify(fp):
    """'smd' / 'tht' / 'mech' for a footprint."""
    a = fp["attrs"]
    if "smd" in a:
        return "smd"
    if "through_hole" in a:
        return "tht"
    types = set(p["type"] for p in fp["pads"])
    if "smd" in types:
        return "smd"
    if "thru_hole" in types:
        return "tht"
    return "mech"


def is_dnp(fp, ext):
    if "dnp" in fp["attrs"]:
        return True
    v = (ext.get("dnp") or "").strip().lower()
    return v in ("1", "y", "yes", "true", "dnp", "dnf", "x") or (ext.get("value", "").upper() in ("DNP", "DNF"))


def describe(fp, ext):
    if ext.get("description") and ext.get("description") != fp["props"].get("Description"):
        return ext["description"]  # written for this BOM line
    sym = fp["props"].get("Description", "")
    pre = re.match(r"[A-Za-z]+", fp["ref"])
    kind = {"R": "Resistor", "C": "Capacitor", "L": "Inductor", "D": "Diode", "LED": "LED", "Q": "Transistor",
            "U": "IC", "J": "Connector", "SW": "Switch", "F": "Fuse", "Y": "Crystal", "FB": "Ferrite bead",
            "BZ": "Buzzer", "TP": "Test point", "K": "Relay"}.get(pre.group(0).upper() if pre else "", "Part")
    d = "%s %s, %s" % (kind, fp["value"], fp["footprint"])
    return d + (" (%s)" % sym if sym and sym.lower() not in d.lower() else "")


def polarity_note(fp):
    """What pin 1 means for this part, or '' when it has no orientation."""
    ref = fp["ref"].upper()
    lib = (fp["lib"] + " " + fp["value"]).lower()
    npads = len([p for p in fp["pads"] if p["num"]])
    pre = re.match(r"[A-Z]+", ref)
    pre = pre.group(0) if pre else ""
    if pre in ("LED",) or (pre == "D" and "led" in lib):
        return "LED: pin 1 = cathode (K)"
    if pre == "D":
        return "Diode: pin 1 = cathode (K, band)" if npads <= 2 else "Diode array: pin 1 marked"
    if pre == "C" and re.search(r"cp_|elec|tantal|polar|_pol", lib):
        return "Polarized capacitor: pin 1 = +"
    if pre == "BZ":
        return "Buzzer: pin 1 = +"
    if pre in ("R", "C", "L", "FB", "F", "TP", "H", "MH", "JP", "NT") and npads <= 2:
        return ""
    if npads >= 3 or pre in ("U", "Q", "J", "P", "SW", "Y", "X", "K", "CN"):
        return "Pin 1 marked (red pad)"
    return ""


# ---------------------------------------------------------------- drawing
def make_drawings(board, parts, origin, meta, fab, out_asm, out_fab):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        from matplotlib.patches import Polygon, Circle, Rectangle
    except ImportError:
        return "matplotlib is not installed (pip install matplotlib): no assembly or fab drawing PDFs"
    from kicad_board import arc_points, rotate

    x0, y0, x1, y1 = board["bbox"]
    W, H = x1 - x0, y1 - y0
    ox, oy = origin

    def tb(fig, title, sheet, nsheet, extra=""):
        fig.text(0.02, 0.975, "%s  |  %s" % (meta["board"], title), fontsize=13, weight="bold", va="top")
        fig.text(0.02, 0.945, "Project: %s    Rev %s    %s    Units: mm [in]    Generated by Anatomy pcba_export from %s" %
                 (meta["project"], meta["rev"], meta["date"], os.path.basename(board["path"])), fontsize=7.5, va="top", color="#333")
        fig.text(0.98, 0.975, "Sheet %d of %d" % (sheet, nsheet), fontsize=9, ha="right", va="top")
        if extra:
            fig.text(0.98, 0.945, extra, fontsize=7.5, ha="right", va="top", color="#333")

    def outline(ax, mirror, lw=1.6):
        for e in board["edges"]:
            if e["kind"] == "circle":
                cx, cy = e["center"]
                ax.add_patch(Circle((m(cx, mirror), cy), e["radius"], fill=False, lw=lw, color="k"))
                continue
            pts = arc_points(*e["pts"]) if e["kind"] == "arc" and len(e["pts"]) == 3 else e["pts"]
            ax.plot([m(p[0], mirror) for p in pts], [p[1] for p in pts], color="k", lw=lw, solid_capstyle="round")

    def m(x, mirror):
        return (x0 + x1 - x) if mirror else x

    def pad_poly(p, mirror):
        w, h = p["w"] / 2, p["h"] / 2
        corners = [(-w, -h), (w, -h), (w, h), (-w, h)]
        pts = []
        for cx, cy in corners:
            rx, ry = rotate(cx, cy, p["rot"])
            pts.append((m(p["x"] + rx, mirror), p["y"] + ry))
        return pts

    def draw_side(ax, side, mirror):
        fab_layer = "F.Fab" if side == "top" else "B.Fab"
        crt_layer = "F.CrtYd" if side == "top" else "B.CrtYd"
        cu = "F.Cu" if side == "top" else "B.Cu"
        outline(ax, mirror)
        # holes
        for fp in board["footprints"]:
            for p in fp["pads"]:
                if p["drill"] and p["type"] == "np_thru_hole":
                    ax.add_patch(Circle((m(p["x"], mirror), p["y"]), p["drill"][0] / 2, fill=False, lw=0.8, color="k", hatch="////"))
        fs = 5.0 if len(parts) < 120 else 4.2
        for fp in board["footprints"]:
            mine = fp["side"] == side
            for p in fp["pads"]:
                if p["type"] == "np_thru_hole" or p["w"] <= 0:
                    continue
                on = mine and (p["type"] == "thru_hole" or cu in p["layers"] or "*.Cu" in p["layers"]) or (not mine and p["type"] == "thru_hole")
                if not on:
                    continue
                pin1 = mine and p["num"] in ("1", "A1") and fp.get("polarity")
                col = "#d62728" if pin1 else ("#9aa7b5" if mine else "#dde3ea")
                if p["shape"] == "circle":
                    ax.add_patch(Circle((m(p["x"], mirror), p["y"]), p["w"] / 2, color=col, lw=0))
                else:
                    ax.add_patch(Polygon(pad_poly(p, mirror), closed=True, color=col, lw=0))
            if not mine:
                continue
            body = [g for g in fp["gfx"] if g["layer"] == fab_layer] or [g for g in fp["gfx"] if g["layer"] == crt_layer]
            for g in body:
                if g["kind"] == "circle":
                    ax.add_patch(Circle((m(g["center"][0], mirror), g["center"][1]), g["radius"], fill=False, lw=0.5, color="#1f3b57"))
                else:
                    pts = arc_points(*g["pts"]) if g["kind"] == "arc" and len(g["pts"]) == 3 else g["pts"]
                    ax.plot([m(q[0], mirror) for q in pts], [q[1] for q in pts], color="#1f3b57", lw=0.5)
            if fp["ref"] in parts and parts[fp["ref"]]["place"]:
                dnp = parts[fp["ref"]]["dnp"]
                ax.text(m(fp["x"], mirror), fp["y"], fp["ref"] + (" DNP" if dnp else ""), fontsize=fs, ha="center", va="center",
                        color="#7f7f7f" if dnp else "#0b2239", weight="bold",
                        bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.65))
        # origin marker (centroid origin, as seen from the top)
        omx = m(ox, mirror)
        L = max(W, H) * 0.07
        dx = -L if mirror else L
        ax.annotate("", xy=(omx + dx, oy), xytext=(omx, oy), arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.4))
        ax.annotate("", xy=(omx, oy - L), xytext=(omx, oy), arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.4))
        ax.text(omx + dx, oy + L * 0.25, "X+", color="#2ca02c", fontsize=7, ha="center")
        ax.text(omx + (L * 0.2 if not mirror else -L * 0.2), oy - L, "Y+", color="#2ca02c", fontsize=7)
        ax.text(omx, oy + L * 0.45, "0,0 (centroid origin)", color="#2ca02c", fontsize=6.5, ha="center", va="top")
        # overall dimensions
        dim(ax, (x0, y1 + 0.12 * H), (x1, y1 + 0.12 * H), "%s" % dual(W, 2, 3), horiz=True)
        sx = x0 - 0.10 * W if not mirror else x1 + 0.10 * W
        dim(ax, (sx, y0), (sx, y1), "%s" % dual(H, 2, 3), horiz=False)
        ax.set_xlim(x0 - 0.22 * W, x1 + 0.22 * W)
        ax.set_ylim(y1 + 0.24 * H, y0 - 0.12 * H)
        ax.set_aspect("equal")
        ax.axis("off")

    def dim(ax, a, b, label, horiz):
        ax.annotate("", xy=a, xytext=b, arrowprops=dict(arrowstyle="<->", lw=0.8, color="#444"))
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        ax.text(mx, my, label, fontsize=7.5, ha="center", va="center", rotation=0 if horiz else 90,
                bbox=dict(fc="white", ec="none", pad=0.5))

    top_parts = [r for r, p in parts.items() if p["place"] and p["side"] == "top"]
    bot_parts = [r for r, p in parts.items() if p["place"] and p["side"] == "bottom"]
    pol = sorted([(r, p["polarity"], p["side"]) for r, p in parts.items() if p["place"] and p["polarity"] and not p["dnp"]],
                 key=lambda t: ref_key(t[0]))
    sides = [("top", False, top_parts)] + ([("bottom", True, bot_parts)] if bot_parts else [])
    nsheet = len(sides)

    legend = ("Red pad = pin 1 (diodes and LEDs: cathode; polarized caps and buzzers: +). Dark outline = component body (fab layer). "
              "Grey label 'DNP' = do not place. Green arrows = centroid origin (board lower-left as seen from the top, X right, Y up).")
    with PdfPages(out_asm) as pdf:
        for i, (side, mirror, plist) in enumerate(sides):
            fig = plt.figure(figsize=(16.54, 11.69))  # A3 landscape
            tb(fig, "Assembly drawing, %s side%s" % (side.upper(), " (viewed from bottom, mirrored)" if mirror else ""),
               i + 1, nsheet, "%d parts placed on this side" % len(plist))
            ax = fig.add_axes([0.02, 0.07, 0.70, 0.85])
            draw_side(ax, side, mirror)
            fig.text(0.02, 0.035, legend, fontsize=7.5, wrap=True)
            # polarity table
            rows = [(r, n) for r, n, s in pol if s == side]
            fig.text(0.74, 0.91, "Orientation check list (%s)" % side, fontsize=9, weight="bold", va="top")
            col_h = 0.0145
            per_col = int(0.82 / col_h)
            for k, (r, n) in enumerate(rows[: per_col * 2]):
                cx = 0.74 + (k // per_col) * 0.13
                cy = 0.89 - (k % per_col) * col_h
                fig.text(cx, cy, "[ ] %-6s %s" % (r, n.replace("Pin 1 marked (red pad)", "pin 1").replace("Polarized capacitor: ", "")
                                                    .replace("Diode: ", "").replace("LED: ", "LED ")), fontsize=6.3, family="monospace", va="top")
            if len(rows) > per_col * 2:
                fig.text(0.74, 0.06, "... %d more in ASSEMBLY-NOTES.md" % (len(rows) - per_col * 2), fontsize=7)
            pdf.savefig(fig)
            plt.close(fig)

    # ------------------------------------------------ fab drawing
    holes = []
    drills = {}
    for fp in board["footprints"]:
        for p in fp["pads"]:
            if p["drill"]:
                plated = p["type"] == "thru_hole"
                key = (round(p["drill"][0], 3), round(p["drill"][1], 3), plated)
                drills[key] = drills.get(key, 0) + 1
                if not plated or fp["ref"].upper().startswith(("H", "MH")):
                    holes.append((fp["ref"], p["x"] - ox, oy - p["y"], p["drill"][0], plated))
    for v in board["vias"]:
        key = (round(v["drill"], 3), round(v["drill"], 3), True)
        drills[key] = drills.get(key, 0) + 1
    with PdfPages(out_fab) as pdf:
        fig = plt.figure(figsize=(16.54, 11.69))
        tb(fig, "Fabrication drawing (bare board)", 1, 1, "Bare board %s x %s" % (dual(W), dual(H)))
        ax = fig.add_axes([0.02, 0.24, 0.50, 0.68])
        outline(ax, False, 1.8)
        for fp in board["footprints"]:
            for p in fp["pads"]:
                if p["drill"]:
                    ax.add_patch(Circle((p["x"], p["y"]), p["drill"][0] / 2, fill=p["type"] != "np_thru_hole", lw=0.4,
                                        color="#555" if p["type"] == "thru_hole" else "k"))
        for v in board["vias"]:
            ax.add_patch(Circle((v["x"], v["y"]), v["drill"] / 2, color="#999", lw=0))
        for (ref, hx, hy, d, pl) in holes:
            ax.annotate("%s" % ref, xy=(hx + ox, oy - hy), xytext=(hx + ox + 0.04 * W, oy - hy - 0.05 * H), fontsize=7,
                        arrowprops=dict(arrowstyle="-", lw=0.5))
        dim(ax, (x0, y1 + 0.10 * H), (x1, y1 + 0.10 * H), dual(W), True)
        dim(ax, (x0 - 0.08 * W, y0), (x0 - 0.08 * W, y1), dual(H), False)
        ax.plot([ox], [oy], marker="+", color="#2ca02c", ms=14, mew=1.5)
        ax.text(ox, oy + 0.06 * H, "DATUM 0,0", color="#2ca02c", fontsize=7, ha="center")
        ax.set_xlim(x0 - 0.18 * W, x1 + 0.08 * W)
        ax.set_ylim(y1 + 0.18 * H, y0 - 0.06 * H)
        ax.set_aspect("equal")
        ax.axis("off")

        def table(x, y, title, rows, widths, fs=7.2):
            fig.text(x, y, title, fontsize=9, weight="bold", va="top")
            yy = y - 0.022
            for k, row in enumerate(rows):
                xx = x
                for c, cell in enumerate(row):
                    fig.text(xx, yy, str(cell), fontsize=fs, va="top", weight="bold" if k == 0 else "normal", family="monospace")
                    xx += widths[c]
                yy -= 0.0155
            return yy

        drows = [("Tool", "Finished hole", "Plating", "Qty")]
        for k, ((d0, d1, pl), n) in enumerate(sorted(drills.items())):
            size = dual(d0, 2, 4) if abs(d0 - d1) < 1e-6 else "%s x %s (slot)" % (dual(d0, 2, 4), dual(d1, 2, 4))
            drows.append(("T%d" % (k + 1), size, "PTH" if pl else "NPTH", n))
        yy = table(0.55, 0.91, "Drill table (finished sizes; vias included)", drows, [0.035, 0.20, 0.05, 0.03])
        hrows = [("Ref", "X from datum", "Y from datum", "Dia", "Type")]
        for ref, hx, hy, d, pl in sorted(holes, key=lambda t: ref_key(t[0])):
            hrows.append((ref, dual(hx), dual(hy), dual(d, 2, 3), "PTH" if pl else "NPTH"))
        yy = table(0.55, yy - 0.015, "Mounting / tooling holes", hrows, [0.04, 0.12, 0.12, 0.11, 0.04])
        frows = [("Item", "Requirement")] + [(k, v) for k, v in fab_rows(board, fab)]
        table(0.55, yy - 0.015, "Fabrication notes", frows, [0.13, 0.30], fs=7.0)
        notes = [
            "1. Fabricate per the Gerber files in %s-gerbers.zip (RS-274X) and Excellon drill files. Gerbers govern." % meta["board"],
            "2. Hole sizes are finished sizes. Tolerance: PTH +/-0.076 mm [0.003 in], NPTH +/-0.05 mm [0.002 in] unless noted.",
            "3. Outline tolerance +/-0.13 mm [0.005 in]. Datum 0,0 is the lower-left corner of the outline bounding box.",
            "4. Board must pass 100% electrical (flying probe) test against the Gerber netlist.",
            "5. Marking: silkscreen per Gerbers. Fab may add date code and UL mark on bottom silk in a clear area.",
            "6. RoHS / lead-free compatible materials and finish.",
        ]
        fig.text(0.02, 0.20, "General notes", fontsize=9, weight="bold", va="top")
        for k, n in enumerate(notes):
            fig.text(0.02, 0.178 - k * 0.017, n, fontsize=7.2, va="top")
        pdf.savefig(fig)
        plt.close(fig)
    return None


def fab_rows(board, fab):
    x0, y0, x1, y1 = board["bbox"]
    ncu = len(board["copper_layers"])
    rows = [
        ("Layers", "%d copper (%s)" % (ncu, ", ".join(board["copper_layers"]))),
        ("Board size", "%s x %s" % (dual(x1 - x0), dual(y1 - y0))),
        ("Finished thickness", dual(fab.get("thickness_mm", board["thickness_mm"]), 2, 4) + " +/-10%"),
        ("Material", fab["material"]),
        ("Copper, outer", "%s oz (%d um) finished" % (fab["copper_outer_oz"], round(fab["copper_outer_oz"] * 35))),
    ]
    if ncu > 2:
        rows.append(("Copper, inner", "%s oz (%d um)" % (fab["copper_inner_oz"], round(fab["copper_inner_oz"] * 35))))
    rows += [
        ("Surface finish", fab["finish"]),
        ("Solder mask", "%s, both sides, LPI" % fab["mask_color"]),
        ("Silkscreen", "%s, both sides as in Gerbers" % fab["silk_color"]),
        ("Min track / space", "%s / %s" % (dual(fab["min_track_mm"], 3, 4) if fab.get("min_track_mm") else "n/a",
                                          dual(fab["min_space_mm"], 3, 4) if fab.get("min_space_mm") else "see Gerbers")),
        ("Min finished hole", dual(fab["min_drill_mm"], 2, 4) if fab.get("min_drill_mm") else "n/a"),
        ("Min via (pad / drill)", "%s / %s" % (dual(fab["min_via_mm"][0], 2, 4), dual(fab["min_via_mm"][1], 2, 4)) if fab.get("min_via_mm") else "no vias"),
        ("Vias", fab["via_treatment"]),
        ("Impedance control", fab["impedance_control"]),
        ("Castellated / edge plating", "%s / %s" % (fab["castellated"], fab["edge_plating"])),
        ("Quality", fab["ipc_class"]),
        ("Panel", fab["panelization"]),
    ]
    return rows


# ---------------------------------------------------------------- quote-form answers
def pad_pitch(fp):
    """Smallest centre-to-centre distance between two copper pads of a part (mm), or None."""
    pts = [(p["x"], p["y"]) for p in fp["pads"] if p["type"] in ("smd", "thru_hole") and p["num"]]
    best = None
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = ((pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2) ** 0.5
            if d > 0.05 and (best is None or d < best):
                best = d
    return best


def body_size(fp):
    xs, ys = [], []
    for g in fp["gfx"]:
        if g["layer"] in ("F.CrtYd", "B.CrtYd", "F.Fab", "B.Fab"):
            for q in g.get("pts", []):
                xs.append(q[0])
                ys.append(q[1])
    for p in fp["pads"]:
        xs += [p["x"] - p["w"] / 2, p["x"] + p["w"] / 2]
        ys += [p["y"] - p["h"] / 2, p["y"] + p["h"] / 2]
    return (max(xs) - min(xs), max(ys) - min(ys)) if xs else (0.0, 0.0)


def assembly_breakdown(act):
    """Split placed parts into the categories turnkey quote forms ask for. Every part lands in exactly one."""
    cat = {"pth": [], "bga": [], "qfn": [], "fine_pitch": [], "large": [], "standard": []}
    pitches = []
    for r, p in sorted(act.items(), key=lambda t: ref_key(t[0])):
        fp = p["fp"]
        lib = fp["lib"].lower()
        if p["mount"] == "tht":
            cat["pth"].append(r)
            continue
        pitch = pad_pitch(fp)
        npads = len([q for q in fp["pads"] if q["num"]])
        if npads > 2 and pitch:
            pitches.append(pitch)
        w, h = body_size(fp)
        if re.search(r"bga", lib):
            cat["bga"].append(r)
        elif re.search(r"qfn|dfn|wson|vson|lga", lib) and not re.search(r"module|wroom|wrover", lib):
            cat["qfn"].append(r)
        elif re.search(r"module|wroom|wrover", lib):
            cat["large"].append(r)
        elif npads > 2 and pitch and pitch < 0.64:
            cat["fine_pitch"].append(r)
        elif max(w, h) >= 15.0 or (re.match(r"^(L|T|HS)\d", r) and max(w, h) >= 10.0):
            cat["large"].append(r)
        else:
            cat["standard"].append(r)
    return cat, (min(pitches) if pitches else None)


def pick_le(options, value):
    """Largest option not above value (or the smallest option)."""
    ok = [o for o in options if o <= value + 1e-9]
    return max(ok) if ok else min(options)


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("board")
    ap.add_argument("--sch")
    ap.add_argument("--bom", help="existing BOM csv to merge MPN/manufacturer/supplier numbers from")
    ap.add_argument("--config", help="pcba.json (default: pcba.json next to the board, if present)")
    ap.add_argument("--out")
    ap.add_argument("--qty", type=int)
    ap.add_argument("--rev")
    ap.add_argument("--name", help="board name used in file names (default: board file stem)")
    ap.add_argument("--offline", action="store_true", help="do not call kicad-cli (testing only)")
    ap.add_argument("--no-zip", action="store_true")
    a = ap.parse_args(argv)

    board_path = os.path.abspath(a.board)
    bdir = os.path.dirname(board_path)
    cfg = {}
    cfg_path = a.config or os.path.join(bdir, "pcba.json")
    if os.path.isfile(cfg_path):
        with open(cfg_path, encoding="utf-8-sig") as fh:
            cfg = json.load(fh)
        cfg_base = os.path.dirname(os.path.abspath(cfg_path))
    else:
        cfg_path, cfg_base = None, bdir

    def cfg_file(key, cli):
        v = cli or cfg.get(key)
        return os.path.abspath(os.path.join(cfg_base, v)) if v and not os.path.isabs(v) else v

    stem = os.path.splitext(os.path.basename(board_path))[0]
    name = a.name or cfg.get("board_name") or stem
    rev = a.rev or str(cfg.get("revision", "A"))
    qty = a.qty or int(cfg.get("quantity", 5))
    sch = cfg_file("schematic", a.sch)
    if not sch:
        cand = os.path.join(bdir, stem.replace("_placed", "") + ".kicad_sch")
        sch = cand if os.path.isfile(cand) else None
    bom_path = cfg_file("bom", a.bom)
    out_root = os.path.abspath(a.out or cfg_file("out", None) or os.path.join(bdir, "pcba"))
    pkg_name = "%s-PCBA-rev%s" % (name, rev)
    pkg = os.path.join(out_root, pkg_name)
    if os.path.isdir(pkg):
        shutil.rmtree(pkg)
    d_fab, d_asm, d_test, d_ref = (os.path.join(pkg, s) for s in ("01-fabrication", "02-assembly", "03-test", "04-reference"))
    for d in (d_fab, d_asm, d_test, d_ref):
        os.makedirs(d)

    blockers, warnings, log = [], [], []
    meta = {"board": name, "rev": rev, "project": cfg.get("project", name), "date": datetime.date.today().isoformat()}

    board = load_board(board_path)
    if not board["bbox"]:
        blockers.append("No board outline on Edge.Cuts.")
        raise SystemExit("no Edge.Cuts outline in %s" % board_path)
    x0, y0, x1, y1 = board["bbox"]
    origin = (x0, y1)  # lower-left corner as seen from the top (KiCad Y grows down)

    # ---------------- kicad-cli outputs
    cli = Cli(None if a.offline else find_kicad_cli(), log)
    drc = erc = None
    gerber_files = []
    if not cli.exe:
        blockers.append("kicad-cli not found (or --offline): no Gerbers, drill files or DRC/ERC in this package. "
                        "Install KiCad 8+ or set KICAD_CLI and run again.")
    else:
        rep = d_ref
        ok, _ = cli.run(["pcb", "drc", "--format", "json", "--severity-all", "--schematic-parity", "--units", "mm",
                         "-o", os.path.join(rep, "drc.json"), board_path], ok_codes=(0, 5))
        if not ok:  # older kicad-cli without --schematic-parity
            ok, _ = cli.run(["pcb", "drc", "--format", "json", "--severity-all", "-o", os.path.join(rep, "drc.json"), board_path], ok_codes=(0, 5))
        cli.run(["pcb", "drc", "--format", "report", "--severity-all", "--schematic-parity", "-o", os.path.join(rep, "drc.rpt"), board_path], ok_codes=(0, 5))
        if os.path.isfile(os.path.join(rep, "drc.json")):
            with open(os.path.join(rep, "drc.json"), encoding="utf-8") as fh:
                drc = json.load(fh)
        if sch and os.path.isfile(sch):
            cli.run(["sch", "erc", "--format", "json", "--severity-all", "-o", os.path.join(rep, "erc.json"), sch], ok_codes=(0, 5))
            cli.run(["sch", "erc", "--format", "report", "--severity-all", "-o", os.path.join(rep, "erc.rpt"), sch], ok_codes=(0, 5))
            if os.path.isfile(os.path.join(rep, "erc.json")):
                with open(os.path.join(rep, "erc.json"), encoding="utf-8") as fh:
                    erc = json.load(fh)
            cli.run(["sch", "export", "pdf", "-o", os.path.join(rep, "%s-schematic.pdf" % name), sch])
        else:
            warnings.append("No schematic found: ERC not run and no schematic PDF in the package (pass --sch).")

        gdir = os.path.join(pkg, "_gerbers")
        os.makedirs(gdir)
        layers = board["copper_layers"] + ["F.Mask", "B.Mask", "F.Paste", "B.Paste", "F.Silkscreen", "B.Silkscreen", "Edge.Cuts"]
        ok, r = cli.run(["pcb", "export", "gerbers", "--layers", ",".join(layers), "--no-x2", "--subtract-soldermask",
                         "-o", gdir + os.sep, board_path])
        if not ok:
            ok, r = cli.run(["pcb", "export", "gerbers", "--layers", ",".join(layers), "-o", gdir + os.sep, board_path])
        ok2, _ = cli.run(["pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
                          "--excellon-zeros-format", "decimal", "--excellon-oval-format", "alternate",
                          "--excellon-separate-th", "--generate-map", "--map-format", "pdf", "-o", gdir + os.sep, board_path])
        if not ok2:
            ok2, _ = cli.run(["pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm", "-o", gdir + os.sep, board_path])
        for f in sorted(os.listdir(gdir)):
            if f.lower().endswith(".pdf"):
                shutil.move(os.path.join(gdir, f), os.path.join(d_fab, f))
        gerber_files = sorted(os.listdir(gdir))
        if not ok or not any("Edge_Cuts" in f for f in gerber_files):
            blockers.append("Gerber export failed or has no Edge.Cuts layer (see 04-reference/kicad-cli.log).")
        if not ok2 or not any(f.lower().endswith(".drl") for f in gerber_files):
            blockers.append("Drill export failed (see 04-reference/kicad-cli.log).")
        with zipfile.ZipFile(os.path.join(d_fab, "%s-gerbers.zip" % name), "w", zipfile.ZIP_DEFLATED) as z:
            for f in gerber_files:
                z.write(os.path.join(gdir, f), f)
        shutil.rmtree(gdir)

        cli.run(["pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
                 "-o", os.path.join(d_ref, "%s-kicad-pos.csv" % name), board_path])
        cli.run(["pcb", "export", "step", "--subst-models", "--force", "-o", os.path.join(d_ref, "%s.step" % name), board_path])
        for side in ("top", "bottom"):
            cli.run(["pcb", "render", "--side", side, "--quality", "high", "--width", "2400", "--height", "1600",
                     "-o", os.path.join(d_ref, "%s-render-%s.png" % (name, side)), board_path])

    # ---------------- DRC / ERC verdict
    def count_sev(items, sev):
        return sum(1 for v in items if v.get("severity") == sev)

    checks = {}
    if drc is not None:
        v = drc.get("violations", [])
        checks["drc_errors"] = count_sev(v, "error")
        checks["drc_warnings"] = count_sev(v, "warning")
        checks["unconnected"] = len(drc.get("unconnected_items", []))
        checks["parity"] = len(drc.get("schematic_parity", []))
        if checks["drc_errors"]:
            blockers.append("DRC: %d error(s). Fix them in KiCad first (04-reference/drc.rpt)." % checks["drc_errors"])
        if checks["unconnected"]:
            blockers.append("DRC: %d unconnected item(s): the board is not fully routed." % checks["unconnected"])
        if checks["parity"]:
            blockers.append("DRC: %d schematic/board parity issue(s): the board does not match the schematic." % checks["parity"])
        if checks["drc_warnings"]:
            types = sorted(set(x.get("type", "?") for x in v if x.get("severity") == "warning"))
            warnings.append("DRC: %d warning(s) (%s). Confirm each is intentional (04-reference/drc.rpt)." % (checks["drc_warnings"], ", ".join(types)))
    elif cli.exe:
        blockers.append("DRC did not run (see 04-reference/kicad-cli.log).")
    if erc is not None:
        ev = [x for s in erc.get("sheets", []) for x in s.get("violations", [])]
        checks["erc_errors"] = count_sev(ev, "error")
        checks["erc_warnings"] = count_sev(ev, "warning")
        if checks["erc_errors"]:
            blockers.append("ERC: %d error(s) in the schematic (04-reference/erc.rpt)." % checks["erc_errors"])
        if checks["erc_warnings"]:
            warnings.append("ERC: %d warning(s) (04-reference/erc.rpt)." % checks["erc_warnings"])

    # ---------------- parts, centroid
    ext = {}
    if bom_path:
        if os.path.isfile(bom_path):
            ext = read_bom_csv(bom_path)
        else:
            warnings.append("BOM file %s not found; using footprint properties only." % bom_path)
    parts = {}
    kpos = {}
    kpos_path = os.path.join(d_ref, "%s-kicad-pos.csv" % name)
    if os.path.isfile(kpos_path):
        with open(kpos_path, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                kpos[r.get("Ref", "")] = r
    pos_delta = 0.0
    for fp in board["footprints"]:
        ref = fp["ref"]
        e = dict(ext.get(ref, {}))
        for f, names in PROP_ALIASES.items():
            if not e.get(f):
                for nm in names:
                    if fp["props"].get(nm):
                        e[f] = fp["props"][nm]
                        break
        mount = classify(fp)
        place = (mount != "mech" and "exclude_from_pos_files" not in fp["attrs"] and "exclude_from_bom" not in fp["attrs"]
                 and not re.match(r"^(TP|H|MH|FID|LOGO|NT)\d", ref, re.I))
        dnp = is_dnp(fp, e)
        x_mm, y_mm = fp["x"] - origin[0], origin[1] - fp["y"]
        rot = fp["rot"]
        if ref in kpos:
            try:
                kx, ky = float(kpos[ref]["PosX"]), float(kpos[ref]["PosY"])
                pos_delta = max(pos_delta, abs(kx - fp["x"]), abs(-ky - fp["y"]))
                rot = float(kpos[ref]["Rot"]) % 360.0
            except (KeyError, ValueError):
                pass
        parts[ref] = {"fp": fp, "ext": e, "mount": mount, "place": place, "dnp": dnp, "side": fp["side"],
                      "x": x_mm, "y": y_mm, "rot": rot, "polarity": polarity_note(fp) if place else ""}
        fp["polarity"] = parts[ref]["polarity"]
    if kpos and pos_delta > 0.01:
        warnings.append("Centroid cross-check: this tool and KiCad's own pos export differ by up to %.3f mm. Check %s-kicad-pos.csv." % (pos_delta, name))
    dup = [r for r in set(f["ref"] for f in board["footprints"]) if sum(1 for f in board["footprints"] if f["ref"] == r) > 1]
    if dup:
        blockers.append("Duplicate reference designators on the board: %s." % ", ".join(sorted(dup)))
    unannotated = [r for r in parts if "?" in r]
    if unannotated:
        blockers.append("Unannotated parts on the board: %s." % ", ".join(unannotated))
    missing_on_board = sorted(set(ext) - set(parts), key=ref_key)
    if missing_on_board:
        warnings.append("In the old BOM but not on the board (left out): %s." % ", ".join(missing_on_board))

    placed = {r: p for r, p in parts.items() if p["place"]}
    # ---------------- BOM grouping
    groups = {}
    for r, p in placed.items():
        e = p["ext"]
        key = (p["dnp"], (e.get("mpn") or "").strip().lower(), p["fp"]["value"].strip().lower(), p["fp"]["footprint"].lower())
        groups.setdefault(key, []).append(r)
    bom_hdr = ["Item", "Qty per board", "Reference designators", "Manufacturer", "Manufacturer part number",
               "Digi-Key PN", "Mouser PN", "LCSC PN", "Description", "Value", "Package / footprint", "Mount",
               "Side", "DNP", "Notes"]
    bom_rows = []
    no_mpn, verify = [], []
    for key in sorted(groups, key=lambda k: (k[0], ref_key(sorted(groups[k], key=ref_key)[0]))):
        refs = sorted(groups[key], key=ref_key)
        p = placed[refs[0]]
        e = p["ext"]
        mpn = (e.get("mpn") or "").strip()
        mfr = (e.get("manufacturer") or "").strip()
        notes = []
        if not p["dnp"]:
            if not mpn or mpn.lower() in ("~", "-", "n/a", "tbd", "?"):
                no_mpn += refs
                notes.append("NO MPN")
            if not mfr:
                notes.append("no manufacturer")
            if any("verify" in (e.get(f) or "").lower() for f in ("mpn", "manufacturer", "digikey", "mouser", "lcsc")):
                verify += refs
                notes.append("supplier PN not confirmed")
        if p["polarity"]:
            notes.append(p["polarity"])
        if p["mount"] == "tht":
            notes.append("through-hole")
        if e.get("notes"):
            notes.append(e["notes"])
        sides = sorted(set(placed[r]["side"] for r in refs))

        def clean(v):
            v = (v or "").strip()
            return "" if re.fullmatch(r"\[?verify\]?", v, re.I) else v.replace("[verify]", "").strip()

        bom_rows.append([len(bom_rows) + 1, len(refs), " ".join(refs), mfr, mpn, clean(e.get("digikey")), clean(e.get("mouser")),
                         clean(e.get("lcsc")), describe(p["fp"], e), p["fp"]["value"], p["fp"]["footprint"],
                         "SMD" if p["mount"] == "smd" else "THT", "/".join(s.title() for s in sides),
                         "DNP" if p["dnp"] else "", "; ".join(notes)])
    if no_mpn:
        blockers.append("No manufacturer part number for %d placed part(s): %s. A turnkey assembler cannot buy them."
                        % (len(no_mpn), ", ".join(sorted(no_mpn, key=ref_key))))
    if verify:
        warnings.append("Supplier numbers marked [verify] for %d part(s): %s. The MPN is used; check stock and the exact suffix."
                        % (len(verify), ", ".join(sorted(verify, key=ref_key))))
    with open(os.path.join(d_asm, "%s-BOM.csv" % name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(bom_hdr)
        w.writerows(bom_rows)

    cen_hdr = ["Designator", "Mid X (mm)", "Mid Y (mm)", "Mid X (in)", "Mid Y (in)", "Rotation (deg)", "Layer",
               "Value", "Package", "Mount", "DNP"]
    cen_rows = []
    for r in sorted(placed, key=ref_key):
        p = placed[r]
        cen_rows.append([r, round(p["x"], 4), round(p["y"], 4), round(inch(p["x"]), 5), round(inch(p["y"]), 5),
                         round(p["rot"], 2), p["side"].title(), p["fp"]["value"], p["fp"]["footprint"],
                         "SMD" if p["mount"] == "smd" else "THT", "DNP" if p["dnp"] else ""])
    with open(os.path.join(d_asm, "%s-centroid.csv" % name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cen_hdr)
        w.writerows(cen_rows)

    # ---------------- fab parameters
    fab = dict(DEFAULT_FAB)
    fab.update(cfg.get("fab", {}))
    fab.setdefault("thickness_mm", board["thickness_mm"])
    if board["stackup"] and board["stackup"].get("copper_finish") and "finish" not in cfg.get("fab", {}):
        fab["finish"] = board["stackup"]["copper_finish"]
    pad_tracks = [w for w in [board["min_track_mm"]] if w]
    fab.setdefault("min_track_mm", min(pad_tracks) if pad_tracks else None)
    rules = {}
    pro = os.path.splitext(board_path)[0].replace("_placed", "") + ".kicad_pro"
    if os.path.isfile(pro):
        try:
            with open(pro, encoding="utf-8") as fh:
                rules = json.load(fh).get("board", {}).get("design_settings", {}).get("rules", {})
        except (ValueError, OSError):
            rules = {}
    if rules.get("min_clearance"):
        fab.setdefault("min_space_mm", rules["min_clearance"])
    drills_all = [p["drill"][0] for f in board["footprints"] for p in f["pads"] if p["drill"]] + [v["drill"] for v in board["vias"]]
    fab.setdefault("min_drill_mm", min(drills_all) if drills_all else None)
    if board["vias"]:
        mv = min(board["vias"], key=lambda v: (v["drill"], v["size"]))
        fab.setdefault("min_via_mm", (mv["size"], mv["drill"]))
    if "copper_outer_oz" not in cfg.get("fab", {}):
        warnings.append("Copper weight not set in pcba.json; 1 oz assumed. Check the power budget before ordering.")
    asm = dict(DEFAULT_ASSEMBLY)
    asm.update(cfg.get("assembly", {}))

    # ---------------- drawings
    err = make_drawings(board, parts, origin, meta, fab, os.path.join(d_asm, "ASSEMBLY-DRAWING.pdf"),
                        os.path.join(d_fab, "FAB-DRAWING.pdf"))
    if err:
        blockers.append(err)

    # ---------------- counts
    act = {r: p for r, p in placed.items() if not p["dnp"]}
    n_smd = sum(1 for p in act.values() if p["mount"] == "smd")
    n_tht = sum(1 for p in act.values() if p["mount"] == "tht")
    sides_used = sorted(set(p["side"] for p in act.values() if p["mount"] == "smd"))
    tht_sides = sorted(set(p["side"] for p in act.values() if p["mount"] == "tht"))
    unique = len([r for r in bom_rows if not r[13]])
    fine = sorted(r for r, p in act.items() if re.search(r"qfn|dfn|bga|lga|wson|son-|_ep|-1ep|thermalvias|module|wroom|esp32", p["fp"]["lib"].lower()))
    small = sorted(r for r, p in act.items() if re.search(r"0201|0402", p["fp"]["footprint"]))
    if "bottom" in sides_used:
        warnings.append("SMD parts on both sides (%d on bottom): double-sided assembly costs more than top-only."
                        % sum(1 for p in act.values() if p["side"] == "bottom" and p["mount"] == "smd"))
    tps = sorted([f for f in board["footprints"] if re.match(r"^TP\d", f["ref"], re.I)], key=lambda f: ref_key(f["ref"]))

    # ---------------- notes
    W, H = x1 - x0, y1 - y0

    def md_table(hdr, rows):
        s = "| " + " | ".join(hdr) + " |\n|" + "---|" * len(hdr) + "\n"
        for r in rows:
            s += "| " + " | ".join(str(c).replace("|", "/") for c in r) + " |\n"
        return s

    with open(os.path.join(d_fab, "FAB-NOTES.md"), "w", encoding="utf-8") as fh:
        fh.write("# %s rev %s - bare board fabrication notes\n\n" % (name, rev))
        fh.write("Gerbers: `%s-gerbers.zip` (RS-274X, %d files incl. Excellon drill). Drawing: `FAB-DRAWING.pdf`.\n\n" % (name, len(gerber_files)))
        fh.write(md_table(["Item", "Requirement"], fab_rows(board, fab)))
        fh.write("\nGerber files in the zip:\n\n" + "".join("- `%s`\n" % f for f in gerber_files))

    pol_rows = [(r, p["polarity"], p["side"].title()) for r, p in sorted(act.items(), key=lambda t: ref_key(t[0])) if p["polarity"]]
    with open(os.path.join(d_asm, "ASSEMBLY-NOTES.md"), "w", encoding="utf-8") as fh:
        fh.write("# %s rev %s - assembly instructions\n\n" % (name, rev))
        fh.write(md_table(["Item", "Requirement"], [
            ("Service", asm["service"]), ("Quantity", "%d boards" % qty),
            ("Solder / RoHS", asm["solder"]), ("Workmanship", asm["workmanship"]),
            ("Cleaning", asm["cleaning"]), ("Conformal coat", asm["conformal_coat"]),
            ("SMD placements per board", "%d (%s side%s)" % (n_smd, " and ".join(sides_used) or "none", "s" if len(sides_used) > 1 else "")),
            ("Through-hole parts per board", "%d (%s)" % (n_tht, ", ".join(tht_sides) or "none")),
            ("Unique BOM lines", unique),
            ("Leadless / bottom-terminated / modules", ", ".join(fine) or "none"),
            ("0402 or smaller", ", ".join(small) or "none"),
            ("DNP (do not place)", ", ".join(sorted([r for r, p in placed.items() if p["dnp"]], key=ref_key)) or "none"),
        ]))
        fh.write("\n## Placement file\n\n`%s-centroid.csv`: one row per placed part. Origin 0,0 is the **lower-left corner of the "
                 "board outline seen from the top**, X to the right, Y up, in mm and inches. Bottom-side parts keep the same "
                 "top-view coordinates (not mirrored). Rotation is KiCad's (counter-clockwise, degrees, as seen from the top). "
                 "KiCad's zero orientation follows IPC-7351, but some assemblers use their own reel zero for SOT-23, "
                 "diodes, USB and JST parts: check every part in the list below against the assembly drawing in your placement preview.\n\n" % name)
        fh.write("Board size: %s x %s. KiCad origin used: (%.4f, %.4f) mm in board coordinates.\n\n" % (dual(W), dual(H), origin[0], origin[1]))
        fh.write("## Orientation and polarity check list\n\n")
        fh.write(md_table(["Ref", "What pin 1 means", "Side"], pol_rows) if pol_rows else "No polarized or multi-pin parts.\n")
        if fine:
            fh.write("\n## Inspection\n\nX-ray (or equivalent) the solder joints under: %s.\n" % ", ".join(fine))
        for n in asm.get("notes", []):
            fh.write("\n- %s" % n)
        fh.write("\n")

    tests = cfg.get("tests", [])
    power_nets = sorted(set(p["net"] for f in board["footprints"] for p in f["pads"]
                            if re.match(r"^(\+|VCC|VDD|VBUS|VIN|VBAT|VLOGIC|VACT|V\d|\d+V|\+\d)", p["net"].lstrip("/"), re.I)))
    with open(os.path.join(d_test, "TEST-NOTES.md"), "w", encoding="utf-8") as fh:
        fh.write("# %s rev %s - test notes for the assembler and first article\n\n" % (name, rev))
        fh.write("1. **Visual / AOI** 100%% per %s. Check every part in the orientation list (ASSEMBLY-NOTES.md).\n" % asm["workmanship"])
        fh.write("2. **Before first power**: measure resistance from each power net to GND. Expect no short (> 100 ohm; "
                 "rails with big capacitors read low at first and climb).\n\n")
        fh.write(md_table(["Power net", "To GND, unpowered", "Powered"],
                          [(n, "> 100 ohm, no short", cfg.get("rails", {}).get(n, "[fill in nominal V]")) for n in power_nets]) if power_nets else "")
        fh.write("\n3. **Power up** from a current-limited supply. ")
        fh.write("%s\n" % cfg.get("power_up", "Set the input voltage and current limit from the design's power budget [fill in]."))
        if tps:
            fh.write("\n## Test points (coordinates from the centroid origin)\n\n")
            fh.write(md_table(["TP", "Net", "X", "Y", "Side"], [(f["ref"], (f["pads"][0]["net"] if f["pads"] else ""),
                                                               dual(f["x"] - origin[0]), dual(origin[1] - f["y"]), f["side"]) for f in tps]))
        if tests:
            fh.write("\n## Functional tests\n\n")
            fh.write(md_table(["#", "Test", "Pass if"], [(i + 1, t.get("step", ""), t.get("expect", "")) for i, t in enumerate(tests)]))
        else:
            warnings.append("No functional tests in pcba.json: TEST-NOTES.md has the generic checks only.")
        if cfg.get("programming"):
            fh.write("\n## Programming\n\n%s\n" % cfg["programming"])
        fh.write("\nAssembler scope: visual/AOI and the unpowered short check are standard. Powered and functional tests "
                 "are for the first article at our end unless the quote includes test.\n")

    # ---------------- quote sheet
    quote = [
        ("Service", "Turnkey PCB assembly (fab + parts + assembly)"),
        ("Quantity", "%d" % qty),
        ("Board size", "%.2f x %.2f mm (%.3f x %.3f in)" % (W, H, inch(W), inch(H))),
        ("Layers", "%d" % len(board["copper_layers"])),
        ("Material", fab["material"]),
        ("Thickness", "%.2f mm (%.3f in)" % (fab["thickness_mm"], inch(fab["thickness_mm"]))),
        ("Copper weight (outer)", "%s oz" % fab["copper_outer_oz"]),
        ("Surface finish", fab["finish"]),
        ("Solder mask / silkscreen", "%s / %s" % (fab["mask_color"], fab["silk_color"])),
        ("Min trace / space", "%s / %s" % (("%.3f mm (%.1f mil)" % (fab["min_track_mm"], inch(fab["min_track_mm"]) * 1000)) if fab.get("min_track_mm") else "n/a",
                                           ("%.3f mm (%.1f mil)" % (fab["min_space_mm"], inch(fab["min_space_mm"]) * 1000)) if fab.get("min_space_mm") else "see Gerbers")),
        ("Min hole", ("%.2f mm (%.1f mil)" % (fab["min_drill_mm"], inch(fab["min_drill_mm"]) * 1000)) if fab.get("min_drill_mm") else "n/a"),
        ("Impedance control", fab["impedance_control"]),
        ("Assembly sides", " and ".join(s.title() for s in sorted(set(sides_used) | set(tht_sides))) or "none"),
        ("SMT placements per board", n_smd),
        ("Through-hole parts per board", n_tht),
        ("Unique parts (BOM lines)", unique),
        ("BGA / QFN / leadless", "Yes: %s" % ", ".join(fine) if fine else "No"),
        ("Files to upload", "%s-gerbers.zip, %s-BOM.xlsx, %s-centroid.csv, ASSEMBLY-DRAWING.pdf, FAB-DRAWING.pdf, ASSEMBLY-NOTES.md" % (name, name, name)),
    ]
    # RushPCB form answers (field names as on app.rushpcb.com, checked 2026-11-15)
    cat, min_pitch = assembly_breakdown(act)
    n_holes = sum(1 for f in board["footprints"] for p in f["pads"] if p["drill"]) + len(board["vias"])
    n_slots = sum(1 for f in board["footprints"] for p in f["pads"] if p["drill"] and abs(p["drill"][0] - p["drill"][1]) > 1e-6)
    ts = min([v for v in (fab.get("min_track_mm"), fab.get("min_space_mm")) if v] or [0.2])
    ts_mil = pick_le([3, 4, 5, 6, 8], inch(ts) * 1000)
    small_hole_in = pick_le([0.006, 0.008, 0.010, 0.012, 0.015, 0.020], inch(fab["min_drill_mm"]) + 0.0005) if fab.get("min_drill_mm") else 0.012
    lead_free = not re.search(r"\bleaded\b|tin.?lead|snpb", (fab["finish"] + asm["solder"]).lower())
    finish = fab["finish"].lower()
    rush_finish = "ENIG" if "enig" in finish else ("Immersion Silver" if "silver" in finish else ("OSP" if "osp" in finish else ("LeadFree HAL" if lead_free else "Leaded")))
    pitch_mil = pick_le([15, 19, 25, 31, 50], inch(min_pitch) * 1000) if min_pitch else 50
    all_sides = sorted(set(sides_used) | set(tht_sides))
    rush = {
        "_note": "Answers for the RushPCB online turnkey quote (app.rushpcb.com). Fill these in; never click a price (that places the order) or enter payment without the user's go-ahead.",
        "pcb": {
            "Number of layers": len(board["copper_layers"]),
            "Material Type": "FR4 130 Tg (RushPCB may switch to FR4 170 Tg (RoHS) when RoHS is on; both are fine)",
            "Board Size (Inches)": [round(inch(W), 3), round(inch(H), 3)],
            "Board Thickness (Inches)": round(inch(fab["thickness_mm"]), 3),
            "Setup as an Array": False,
            "Finish Type": rush_finish,
            "IPC Class": "IPC Class-III" if "class 3" in fab["ipc_class"].lower() else "IPC Class-II",
            "Routing": "Individually Routed",
            "Total hole count": n_holes,
            "Smallest Hole (Inches)": small_hole_in,
            "Min. Trace/Space (Mil)": "%d/%dmil" % (ts_mil, ts_mil),
            "Outer Copper Finish (Oz)": "%s Oz" % fab["copper_outer_oz"],
            "Inner Copper Finish (Oz)": ("%s Oz" % fab["copper_inner_oz"]) if len(board["copper_layers"]) > 2 else None,
            "Mask Sides": "Both", "Mask Color": fab["mask_color"], "Silk Sides": "Both", "Silk Color": fab["silk_color"],
            "Flying Probe Electric Testing": True, "RoHs": lead_free,
            "No. of Slots per board": n_slots, "No. of Cutouts per board": 0, "Countersink per board": 0, "Counterbore per board": 0,
            "No. of gold fingers": 0, "Impedance": fab["impedance_control"].lower() not in ("none", "no", ""),
            "Edgeplating/Castellation": "None" if fab["castellated"] == "No" and fab["edge_plating"] == "No" else "see FAB-NOTES",
            "Mask Tented": "tent" in fab["via_treatment"].lower(),
            "Blind/Buried Vias": False, "Carbon Ink": False,
        },
        "bom": {
            "upload": "02-assembly/%s-BOM.csv (or .xlsx, first sheet)" % name,
            "column_mapping": {"Qty per board": "Quantity", "Reference designators": "Reference designator",
                               "Manufacturer part number": "Mfg. part number", "Description": "Description", "DNP": "DNI/DNP"},
            "expect_total_parts": len(act), "expect_unique_parts": unique,
            "consigned": [], "dni": sorted([r for r, p in placed.items() if p["dnp"]], key=ref_key),
        },
        "assembly": {
            "Assembly Sides": "Both" if len(all_sides) > 1 else (all_sides[0].title() if all_sides else "Top"),
            "Total Line Items": unique, "Total Components": len(act),
            "PTH Components": len(cat["pth"]), "QFN Per Board": len(cat["qfn"]), "BGAs Per Board": len(cat["bga"]),
            "Standard SMDs": len(cat["standard"]), "Fine Pitch ICs": len(cat["fine_pitch"]),
            "Large Devices (incl. Heat Sinks)": len(cat["large"]),
            "Pressfit Connectors/Modules": 0,
            "Min SMD Pitch (Mil)": "%d Mil" % pitch_mil if pitch_mil < 50 else "50 Mil",
            "ITAR": False, "Class III": "class 3" in asm["workmanship"].lower(),
            "01005 Package Used": any("01005" in p["fp"]["footprint"] for p in act.values()),
            "0201 Package Used": any(re.search(r"\b0201\b|_0201_", p["fp"]["footprint"]) for p in act.values()),
            "0402 Package Used": any(re.search(r"_0402_|0402", p["fp"]["footprint"]) for p in act.values()),
            "Conformal Coating": asm["conformal_coat"].lower() not in ("none", "no", ""),
            "De-panel after assembly": False,
            "_which_parts": {k: v for k, v in cat.items()},
            "_notes": "Pressfit Connectors/Modules stays 0: the online quote refuses any value there. SMD modules (ESP32 etc.) count as Large Devices.",
        },
        "after_order_uploads": ["01-fabrication/%s-gerbers.zip" % name, "02-assembly/%s-centroid.csv" % name,
                                "02-assembly/ASSEMBLY-DRAWING.pdf", "01-fabrication/FAB-DRAWING.pdf", "02-assembly/ASSEMBLY-NOTES.md"],
    }
    assert sum(len(v) for v in cat.values()) == len(act)
    with open(os.path.join(pkg, "rushpcb-quote.json"), "w", encoding="utf-8") as fh:
        json.dump(rush, fh, indent=2)

    with open(os.path.join(pkg, "QUOTE-SHEET.md"), "w", encoding="utf-8") as fh:
        fh.write("# %s rev %s - values for the PCBA quote form\n\n" % (name, rev))
        fh.write("Type these into the quote form (RushPCB or any turnkey house). Nothing here is sent anywhere by this tool. "
                 "`rushpcb-quote.json` has the same answers keyed by RushPCB's field names, for the Get PCBA quote step.\n\n")
        fh.write(md_table(["Field", "Value"], quote))
        fh.write("\n## Assembly breakdown (quote forms ask for these counts; they add up to %d)\n\n" % len(act))
        fh.write(md_table(["Category", "Count", "Parts"], [
            ("Through-hole (PTH)", len(cat["pth"]), " ".join(cat["pth"])),
            ("QFN / DFN / LGA", len(cat["qfn"]), " ".join(cat["qfn"])),
            ("BGA", len(cat["bga"]), " ".join(cat["bga"])),
            ("Fine pitch ICs (< 0.65 mm)", len(cat["fine_pitch"]), " ".join(cat["fine_pitch"])),
            ("Large devices / modules (>= 10 mm)", len(cat["large"]), " ".join(cat["large"])),
            ("Standard SMD", len(cat["standard"]), "%d parts" % len(cat["standard"])),
            ("Smallest SMD pitch", ("%.2f mm (%.1f mil)" % (min_pitch, inch(min_pitch) * 1000)) if min_pitch else "n/a", ""),
            ("Holes / slots", "%d / %d" % (n_holes, n_slots), ""),
        ]))

    write_xlsx(os.path.join(d_asm, "%s-BOM.xlsx" % name), [
        {"name": "BOM", "rows": [bom_hdr] + bom_rows, "wrap_cols": (2, 8, 14)},
        {"name": "Centroid", "rows": [cen_hdr] + cen_rows},
        {"name": "Order info", "header": False, "rows": [["Board", name], ["Revision", rev], ["Quantity", qty],
                                                         ["Date", meta["date"]]] + [[k, v] for k, v in quote]},
    ])
    write_xlsx(os.path.join(d_asm, "%s-centroid.xlsx" % name), [{"name": "Centroid", "rows": [cen_hdr] + cen_rows}])

    # ---------------- README / status
    with open(os.path.join(d_ref, "kicad-cli.log"), "w", encoding="utf-8") as fh:
        fh.write("kicad-cli: %s\nversion: %s\n\n" % (cli.exe, cli.version))
        for e in log:
            fh.write("$ %s\n[exit %s]\n%s\n\n" % (e["cmd"], e["code"], e["out"]))
    ready = not blockers
    status = {"board": name, "revision": rev, "ready": ready, "blockers": blockers, "warnings": warnings, "checks": checks,
              "kicad_cli": cli.version, "board_file": board_path, "kicad_file_version": board["version"],
              "size_mm": [round(W, 3), round(H, 3)], "layers": len(board["copper_layers"]), "smd": n_smd, "tht": n_tht,
              "bom_lines": unique, "sides": sides_used, "quantity": qty, "generated": datetime.datetime.now().isoformat(timespec="seconds")}
    with open(os.path.join(pkg, "status.json"), "w", encoding="utf-8") as fh:
        json.dump(status, fh, indent=2)
    with open(os.path.join(pkg, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("# %s rev %s - turnkey PCBA order package\n\n" % (name, rev))
        fh.write("**Status: %s**\n\n" % ("READY TO QUOTE" if ready else "NOT READY - fix the blockers below first"))
        if blockers:
            fh.write("## Blockers\n\n" + "".join("- %s\n" % b for b in blockers) + "\n")
        if warnings:
            fh.write("## Check before ordering\n\n" + "".join("- %s\n" % w for w in warnings) + "\n")
        fh.write("## Checks\n\n")
        fh.write(md_table(["Check", "Result"], [
            ("KiCad", cli.version or "not run"),
            ("DRC errors / warnings", "%s / %s" % (checks.get("drc_errors", "n/a"), checks.get("drc_warnings", "n/a"))),
            ("Unconnected items", checks.get("unconnected", "n/a")),
            ("Schematic parity issues", checks.get("parity", "n/a")),
            ("ERC errors / warnings", "%s / %s" % (checks.get("erc_errors", "n/a"), checks.get("erc_warnings", "n/a"))),
            ("Placed parts with MPN", "%d of %d" % (len(act) - len(set(no_mpn)), len(act))),
        ]))
        fh.write("\n## What to upload\n\n")
        fh.write("| File | Is |\n|---|---|\n")
        fh.write("| `01-fabrication/%s-gerbers.zip` | Gerber RS-274X + NC Excellon drill (PTH and NPTH) |\n" % name)
        fh.write("| `02-assembly/%s-BOM.xlsx` | Turnkey BOM (also `.csv`) |\n" % name)
        fh.write("| `02-assembly/%s-centroid.csv` | Pick-and-place / XY (also `.xlsx`) |\n" % name)
        fh.write("| `02-assembly/ASSEMBLY-DRAWING.pdf` | Top/bottom assembly drawing, pin 1 and polarity marked |\n")
        fh.write("| `01-fabrication/FAB-DRAWING.pdf` | Outline, drill and hole tables, fab notes, mm [in] |\n")
        fh.write("| `02-assembly/ASSEMBLY-NOTES.md`, `03-test/TEST-NOTES.md` | Special instructions and tests |\n")
        fh.write("\n`QUOTE-SHEET.md` lists the values to type into the quote form. `04-reference/` has the schematic, STEP, renders and the raw reports.\n")
        fh.write("\nA clean DRC means the board follows its own rules, not that the circuit works. Machine-generated boards "
                 "should be reviewed by a person before the first order.\n")

    zpath = None
    if not a.no_zip:
        zpath = os.path.join(out_root, pkg_name + ".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for rootd, _, files in os.walk(pkg):
                for f in files:
                    full = os.path.join(rootd, f)
                    z.write(full, os.path.join(pkg_name, os.path.relpath(full, pkg)))
    print(json.dumps({"package": pkg, "zip": zpath, "ready": ready, "blockers": blockers, "warnings": warnings}, indent=2))
    return 0 if ready else 2


if __name__ == "__main__":
    sys.exit(main())
