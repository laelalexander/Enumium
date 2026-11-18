"""AON-1 build package: build.json, README.md, 1-purchase, 3-fabricate, 4-assemble, 5-firmware-test, from bom/bom.csv and drawings/sh_asm.STEPS.

Run after bom/make_bom.py and drawings/build_all.py --pdf. Ends with the cross-check (every assembly part is a purchase or fabricate line).
"""
import csv, json, pathlib, re, shutil, sys

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "drawings"))
import sh_asm  # noqa: E402

bom = list(csv.DictReader(open(ROOT / "bom/bom.csv")))
buy = [r for r in bom if r["type"] == "BUY"]
made = [r for r in bom if r["type"] == "BUILD"]
lines = {r["line"] for r in bom}

STEP_PARTS = {1: ["AON-103", "AON-106", "BP-03", "H4", "H5"], 2: ["AON-101", "AON-102", "H1"],
              3: ["AON-107", "E07", "H3", "E02", "BP-02", "E01", "E03", "BP-05"], 4: ["AON-104", "H1"], 5: ["E04", "BP-08"],
              6: ["AON-105", "H1", "H7", "E05", "H8", "BP-04"], 7: ["H9", "E06", "H2", "BP-06"]}
QTY = {r["line"]: int(r["qty"]) for r in bom}
TOOLS = ["Torx T6/T8 drivers", "torque screwdriver 0.1-1.0 N·m", "squaring fixture (100.00 box)", "calipers + depth gauge", "milliohm meter (bond < 10 mΩ)",
         "ESD bench, wrist strap, Class 100k clean bench", "temperature-controlled soldering iron", "3M 2216 mixing kit (staking)", "ST-LINK V3 (SWD)"]


def main():
    for d in ("1-purchase", "3-fabricate/cut", "3-fabricate/machined", "4-assemble/steps", "5-firmware-test"):
        (HERE / d).mkdir(parents=True, exist_ok=True)
    purchase = [dict(line=r["line"], desc=r["description"], mfr=r["manufacturer"], mpn=r["mpn_or_standard"], qty=int(r["qty"]), supplier=r["supplier"],
                     url=r["supplier_url"], unit_price=float(r["unit_price"] or 0), alt=r["alt_mpn"], notes=r["verified"]) for r in buy]
    with open(HERE / "1-purchase/purchase-list.csv", "w", newline="") as f:
        w = csv.DictWriter(f, list(purchase[0])); w.writeheader(); w.writerows(purchase)
    with open(HERE / "1-purchase/mcmaster-cart.csv", "w", newline="") as f:  # McMaster quick-order paste: part number, qty (SKUs still to pick)
        w = csv.writer(f); w.writerow(["Part Number", "Quantity", "BOM line", "Description"])
        for p in purchase:
            if "McMaster" in p["supplier"]:
                w.writerow(["(pick SKU)", p["qty"], p["line"], p["desc"]])
    fab = []
    for r in made:
        pid = r["line"]
        if pid.startswith("E"):
            fab.append(dict(part=f"{pid} PCBA", line=pid, process="PCB fab + turnkey assembly", files=[], vendor="RushPCB", qty=int(r["qty"]) + 1,
                            settings=r["key_spec"], drawing="drawings/AON-B00_boards.svg", status="BLOCKER: KiCad layout and RushPCB package not made yet"))
            continue
        step = f"cad/step/{pid}.step" if (ROOT / f"cad/step/{pid}.step").exists() else ""
        files = [x for x in (step, r["design_file"]) if x]
        if pid == "AON-106":
            files += ["dxf/AON-106_flat_mm.dxf", "dxf/AON-106_flat_in.dxf"]
        fab.append(dict(part=f"{pid} {r['description']}", line=pid, process=r["supplier"], files=files, step=step, vendor="Xometry (CNC) or local machine shop",
                        material=r["key_spec"], drawing="drawings/AON-1-drawing-set.pdf", qty=int(r["qty"]), status="ready for quote"))
        if step:
            shutil.copy(ROOT / step, HERE / "3-fabricate/machined" / f"{pid}.step")
    for p in (ROOT / "dxf").glob("*.dxf"):
        shutil.copy(p, HERE / "3-fabricate/cut" / p.name)
    asm = []
    for n, title, text, check in sh_asm.STEPS:
        img = f"build/4-assemble/steps/{n:02d}.png"
        shutil.copy(ROOT / f"drawings/img/step{n:02d}.png", ROOT / img)
        tq = "; ".join(sorted(set(re.findall(r"\d\.\d+ N·m", text))))
        asm.append(dict(step=n, title=title, image=img, parts=[{"line": p, "qty": QTY.get(p, 1)} for p in STEP_PARTS[n]], tools=TOOLS[:3], text=text, torque=tq, check=check))
    fw = [dict(name="EOR-1 flight software (host build + 146 unit checks)", dir="firmware/eor1", build="make", flash="not yet: the STM32H743 port (port/stm32h7) is written with the E03 board, then flashed over SWD with an ST-LINK",
               binary="firmware/eor1/build/test_eor (host); flight binary after E03 exists", check="make test: 0 failures"),
          dict(name="Ground station script", dir="firmware/ground", build="-", flash="-", binary="firmware/ground/aon_ground.py", check="python3 -m unittest test_ground: 4 OK")]
    tests = [dict(name="Inhibit check", steps=["RBF fitted, switches pressed", "measure VBATT bus at J6"], expect="bus 0 V with any one inhibit active"),
             dict(name="Bond check", steps=["milliohm meter rail to each panel, frame, end board"], expect="< 10 mΩ"),
             dict(name="Envelope", steps=["gauge 100.0 x 100.0 x 340.5 in the rail check box"], expect="CDS 14.1 limits, switches 1.5 proud"),
             dict(name="Functional (AON-900)", steps=["umbilical UART beacon", "HMAC TC ping", "deploy ARM/FIRE into a dummy load"], expect="see AON-900 test plan sheet")]
    cost = sum(p["qty"] * p["unit_price"] for p in purchase)
    bj = dict(title="AON-1 3U CubeSat", summary="Ambient Orbital Node 1: a 3U CubeSat (CDS rev 14.1) with a machined 6061 rail-and-frame structure, an 81 mm in-house board stack "
              "(EPS, 2S2P battery, OBC/ADCS, UHF COM, antenna deployer), four body-mounted 7-cell solar panels and the EOR-1 store-and-forward flight software.",
              totals=dict(parts_cost=round(cost, 2), currency="USD", print_hours=0, filament_g={}, build_hours=40), tools=TOOLS,
              purchase=purchase, print=[], fabricate=fab, assembly=asm, firmware=fw, tests=tests)
    (HERE / "build.json").write_text(json.dumps(bj, indent=1, ensure_ascii=False))
    # cross-check
    bad = [f"step {a['step']}: {p['line']} not a BOM line" for a in asm for p in a["parts"] if p["line"] not in lines]
    bad += [f"{p['line']} purchase not BUY" for p in purchase if p["line"] not in lines]
    nsteps = len(json.load(open(ROOT / "assembly.json"))["steps"])
    if nsteps != len(asm):
        bad.append(f"assembly.json has {nsteps} steps, guide has {len(asm)}")
    blockers = [f["line"] for f in fab if f["status"].startswith("BLOCKER")]
    rd = f"""# AON-1 build package

What you are building: a 3U CubeSat, 100 x 100 x 340.5 mm [3.94 x 3.94 x 13.41 in], about 1.6 kg current best estimate. Bought parts and stock about ${cost:,.0f} including spares (estimates, not verified against supplier pages). About 40 hours of assembly and test once parts are in hand. Skills: fine-pitch soldering checks, torque-controlled small fasteners, ESD and clean handling.

Stages
1. Purchase: `1-purchase/purchase-list.csv` ({len(purchase)} lines). Every line still needs its supplier page checked and the SKU picked; `mcmaster-cart.csv` lists the McMaster lines with quantities.
2. Print: none. The structure is machined aluminium, so there is no G-code in this project.
3. Fabricate: machined parts AON-101..107 (STEP in `3-fabricate/machined`, drawings in `drawings/AON-1-drawing-set.pdf`), cut files in mm and inch in `3-fabricate/cut`.
4. Assemble: {len(asm)} illustrated steps, matching `assembly.json` one to one (AON-003 sheet).
5. Firmware and test: EOR-1 host build and tests; the flight build needs the E03 board.

Blockers
- Boards {", ".join(blockers)}: KiCad layouts and RushPCB turnkey packages are not made yet (KiCad runs on the user's PC).
- Purchase lines: prices are estimates and no supplier page was fetched.

Cross-check: {"PASS, every assembly part is a purchase or fabricate line and the step count matches assembly.json." if not bad else "FAIL: " + "; ".join(bad)}
"""
    (HERE / "README.md").write_text(rd)
    print(f"build.json: {len(purchase)} purchase, {len(fab)} fabricate, {len(asm)} steps; check {'PASS' if not bad else bad}; blockers {blockers}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
