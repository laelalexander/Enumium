"""Illustrated assembly guide.   python run.py guide

One list of build steps drives three things:
  * the 3D twin's Assembly mode (Parts tab): each step shows the parts built so far, the new ones highlighted
  * the step pictures, rendered from the twin (docs/design/assembly/step-NN-*.png, needs Node + Playwright, see guide.js)
  * docs/design/robot-arm-assembly-guide.html (+ .pdf): pictures, parts, fasteners with torque, tools, steps, checks

`show` selectors pick twin objects: "key" or "key~regex" (regex on the object's label, case-insensitive)."""
import json, re
from datetime import date
from html import escape
from pathlib import Path

from .fasteners import FASTENERS

HERE = Path(__file__).resolve().parent.parent
OUT = HERE.parent / "docs" / "design"
PICS = OUT / "assembly"

ISO, LOW, FRONT, TOP = [1, -1.25, 0.9], [1.1, -1, -0.45], [0.25, -1, 0.35], [0.15, -0.35, 1]

STEPS = [
    dict(id="base", title="Prepare the base board", show=["BASE-01", "LEG-01", "GSK-03", "grommet"], view=ISO, zoom=1.0,
         parts=[("BASE-01", "base board", 1), ("LEG-01", "base leg", 4), ("GSK-03", "foot pad", 4), ("-", "32 mm grommet", 1)],
         fasteners=[("F14", 8), ("F07T", 4)], tools="CNC router or jigsaw, drill press, 90° countersink, 3 mm and 8 mm bits",
         time="2 h + finish drying",
         do=["Cut BASE-01 from fab/dxf (or tape the 1:1 template to the plywood and centre-punch every cross).",
             "Rout the 61.5 x 61.5 mm [2.42 in] pocket 12 mm [.47 in] deep on the UNDERSIDE, centred on the Ø39.1 pilot hole.",
             "Drill holes A-F to the sizes in the BASE-01 hole table. Countersink the eight E holes 90° x Ø10.5 on the top face.",
             "Press the four F07T tee nuts into the C holes from below (tap home with a hammer and a block).",
             "Saw four LEG-01 at 200 mm, drill two Ø3.0 x 60 pilots in each top face on the diagonal, glue a GSK-03 pad under each.",
             "Screw the legs on with F14 (two per leg) and seal the board with two coats of polyurethane. Fit the grommet."],
         check=["Board sits flat on all four legs (no rock).", "Tee nuts flush, threads clean (run an M5 screw through each)."]),
    dict(id="yaw_motor", title="Mount the yaw gearmotor", show=["gm_yaw", "limit~yaw"], view=[0.12, -1, 0.04], zoom=0.7,
         parts=[("-", "NEMA 23 + 20:1 gearbox (yaw)", 1), ("-", "limit switch", 1)],
         fasteners=[("F05", 4), ("F05W", 4), ("F13", 2)], tools="hex keys, torque driver, blue threadlocker", time="20 min",
         do=["Measure the gearbox flange and pilot; if they differ from HW in arm/hardware.py, re-run python run.py cut before drilling.",
             "From below, seat the gearbox flange in the pocket with the output shaft up through the Ø39.1 pilot hole.",
             "Fit the four F05 screws from the top through fender washers into the flange. Threadlocker, 4.0 N·m.",
             "Mount the yaw limit switch on the top face with two F13 at the F holes, lever toward the YAW-01 home dog."],
         check=["Shaft square to the board (feeler gauge under a square: < 0.3 mm over 50 mm).", "Shaft protrudes enough to engage the clamp hub fully."]),
    dict(id="turntable", title="Seat the gasket and turntable", show=["GSK-01", "turntable~12 in"], view=ISO, zoom=1.0,
         parts=[("GSK-01", "turntable seat gasket", 1), ("-", "12 in turntable bearing", 1)],
         fasteners=[("F07", 4)], tools="hex keys, torque driver", time="15 min",
         do=["Lay GSK-01 on the board with its holes over the tee nuts.",
             "Place the turntable, fixed (outer) ring down, holes over the gasket holes, centred on the gearbox shaft.",
             "Fit four F07 button heads into the tee nuts, 3.0 N·m, crossing pattern."],
         check=["Turntable turns freely with no rub on the gearbox shaft.", "Ring is concentric with the shaft within 1 mm (measure to the ring edge)."]),
    dict(id="yaw_rotor", title="Yaw adapter disc, hub and base plate", show=["YAW-01", "turntable~upper", "hub~yaw", "base_top_plate"], view=ISO, zoom=1.0,
         parts=[("YAW-01", "turntable adapter disc", 1), ("P-11", "base_top_plate (printed)", 1), ("-", "clamp hub (bore = gearbox output)", 1)],
         fasteners=[("F08", 4), ("F06", 8), ("F03", 4)], tools="hex keys, torque driver, blue threadlocker", time="30 min",
         do=["Bolt YAW-01 to the turntable's rotating ring with four F08 (washer + nyloc), 4.0 N·m.",
             "Slide the clamp hub onto the gearbox output shaft through YAW-01's centre hole; do not clamp yet.",
             "Lower base_top_plate onto YAW-01 and bolt it with eight F06 (washers both sides, nyloc), 3.5 N·m.",
             "Fit four F03 through base_top_plate into the hub flange, 2.5 N·m. Now clamp the hub on the shaft.",
             "Bolt the home dog (20 x 10 x 3 aluminium tab) across YAW-01's two Ø3.4 holes, M3 x 10 + nuts."],
         check=["Rotate by hand through ±150°: smooth, no tight spot, dog trips the switch with an audible click."]),
    dict(id="riser", title="Bond the riser tube", show=["TUBE-03"], view=ISO, zoom=1.0,
         parts=[("TUBE-03", "riser tube 150 mm", 1)], fasteners=[], tools="structural epoxy, square, isopropyl alcohol", time="10 min + cure",
         do=["Cut TUBE-03 at 150 mm, deburr, and drill the Ø5.5 cross-pin hole 25 mm from the TOP end (V-block).",
             "Scuff and degrease the bottom 70 mm, butter with structural epoxy and push it fully into base_top_plate's socket.",
             "Hold it square while the epoxy cures (check two directions with a square)."],
         check=["Riser vertical within 0.5° in both directions."]),
    dict(id="shoulder", title="Build and fit the shoulder joint", show=["shoulder_cheek_motor", "shoulder_cheek_plain", "shoulder_tube_block", "gm_shoulder",
                                                                        "pulley_s~shoulder", "pulley_l~shoulder", "belt~shoulder", "bearing~shoulder",
                                                                        "SHAFT-01~shoulder", "collar~shoulder", "hub~shoulder", "tube_socket~shoulder", "limit~shoulder"],
         view=ISO, zoom=1.0,
         parts=[("P-01", "shoulder_cheek_motor", 1), ("P-02", "shoulder_cheek_plain", 1), ("P-03", "shoulder_tube_block", 1),
                ("P-10", "tube_socket", 1), ("SHAFT-01", "joint shaft", 1), ("-", "6001-2RS bearing", 2), ("-", "HTD 5M 16T + 80T pulleys, belt", 1),
                ("-", "shaft collar", 2), ("-", "clamp hub", 1), ("-", "NEMA 23 + 20:1 gearbox (shoulder)", 1)],
         fasteners=[("F01", 5), ("F04", 4), ("F03", 4)], tools="arbor press or vice with soft jaws, 12 mm reamer, torque driver", time="1.5 h",
         do=["Ream the Ø20 shaft holes lightly and check the Ø28.15 bearing counterbores with a bearing: light press fit.",
             "Press one 6001-2RS into each cheek's counterbore (outer faces).",
             "Slide the shoulder_tube_block onto the riser top, line up the cross holes and fit F01 as the cross pin.",
             "Bolt the cheeks to the block with four F01 (washer both sides, nyloc), 2.5 N·m.",
             "Slide SHAFT-01 through both bearings with the flat on the motor side; fit the 80T pulley on the flat and a collar each side.",
             "Mount the gearmotor on the motor cheek with four F04 through the slots; fit the 16T pulley and the belt.",
             "Tension: slide the motor until the belt deflects about 3 mm at mid-span under finger pressure; F04 to 2.5 N·m.",
             "On the plain side fit the clamp hub, then bolt the tube_socket to it with four F03, 2.5 N·m. Clamp the hub."],
         check=["Shaft turns smoothly by hand through the belt, no axial play.", "Limit switch trips at the home end of travel."]),
    dict(id="upper_arm", title="Fit the upper arm tube", show=["TUBE-01"], view=ISO, zoom=1.0,
         parts=[("TUBE-01", "upper arm tube", 1)], fasteners=[("F02", 1)], tools="drill + 5.5 mm bit, V-block", time="20 min",
         do=["Cut TUBE-01 to length (fab/CUTLIST.md), deburr, drill the pin hole 27 mm from the socket end on a V-block.",
             "Push it fully into the shoulder tube_socket and fit F02 as the cross pin, 2.5 N·m.",
             "With the tube in the elbow_tube_block (next step), drill the second hole (25 mm from that end) through the block's hole as a guide."],
         check=["Tube fully seated (no gap at the socket mouth)."]),
    dict(id="elbow", title="Build and fit the elbow joint", show=["elbow_cheek_motor", "elbow_cheek_plain", "elbow_tube_block", "gm_elbow",
                                                                  "pulley_s~elbow", "pulley_l~elbow", "belt~elbow", "bearing~elbow",
                                                                  "SHAFT-01~elbow", "collar~elbow", "hub~elbow", "tube_socket~elbow", "limit~elbow"],
         view=ISO, zoom=1.0,
         parts=[("P-04..06", "elbow cheeks and tube block", 3), ("P-10", "tube_socket", 1), ("SHAFT-01", "joint shaft", 1), ("-", "6001-2RS", 2),
                ("-", "16T + 48T pulleys, belt", 1), ("-", "collars, clamp hub", 3), ("-", "NEMA 23 + 20:1 (elbow)", 1)],
         fasteners=[("F01", 5), ("F04", 4), ("F03", 4)], tools="as the shoulder", time="1.5 h",
         do=["Repeat the shoulder steps with the elbow parts (3:1 belt stage, 48T joint pulley).",
             "The upper arm's free end goes into the elbow_tube_block; cross pin F01 through the block and tube."],
         check=["Elbow axis parallel to the shoulder axis (sight along both shafts)."]),
    dict(id="forearm", title="Fit the forearm tube", show=["TUBE-02"], view=ISO, zoom=1.0,
         parts=[("TUBE-02", "forearm tube", 1)], fasteners=[("F02", 1)], tools="drill + 5.5 mm bit, V-block", time="20 min",
         do=["As the upper arm: pin 27 mm from the end in the elbow tube_socket (F02), second hole 25 mm from the other end, drilled through the wrist_tube_block."],
         check=["Tube fully seated."]),
    dict(id="wrist", title="Build and fit the wrist joint", show=["wrist_cheek_motor", "wrist_cheek_plain", "wrist_tube_block", "gm_wrist",
                                                                  "pulley_s~wrist", "pulley_l~wrist", "belt~wrist", "bearing~wrist",
                                                                  "SHAFT-01~wrist", "collar~wrist", "hub~wrist", "tube_socket~wrist", "limit~wrist"],
         view=ISO, zoom=1.0,
         parts=[("P-07..09", "wrist cheeks and tube block", 3), ("P-10", "tube_socket", 1), ("SHAFT-01", "joint shaft", 1), ("-", "6001-2RS", 2),
                ("-", "16T + 16T pulleys, belt", 1), ("-", "collars, clamp hub", 3), ("-", "NEMA 23 + 20:1 (wrist)", 1)],
         fasteners=[("F01", 5), ("F04", 4), ("F03", 4)], tools="as the shoulder", time="1.5 h",
         do=["Repeat the joint steps with the wrist parts (1:1 belt stage)."], check=["Wrist turns freely through its full range."]),
    dict(id="gripper", title="Assemble and fit the gripper", show=["TUBE-04", "gripper_adapter", "gripper_body", "nema17", "rod", "gripper_jaw",
                                                                   "GSK-02", "limit~gripper"],
         view=ISO, zoom=0.6,
         parts=[("TUBE-04", "wrist stub tube", 1), ("P-12", "gripper_body", 1), ("P-13", "gripper_adapter", 1), ("P-14", "gripper_jaw", 1),
                ("GSK-02", "jaw pad", 2), ("-", "NEMA 17 + T8 lead screw + coupler", 1), ("-", "8 mm rods + LM8UU", 2)],
         fasteners=[("F10", 4), ("F09", 4), ("F11", 4), ("F12", 4), ("F02", 1)], tools="soldering iron with insert tip, torque driver, retaining compound",
         time="1.5 h",
         do=["Set four F10 M4 inserts in gripper_body's Ø5.6 holes at 230-250 °C, flush with the face.",
             "Press LM8UU bearings into gripper_jaw. Press the 8 mm rods into the body with retaining compound, jaw on the rods.",
             "Mount the NEMA 17 with four F11, 1.0 N·m; couple the T8 screw; bolt the T8 nut flange through the jaw with four F12, 0.6 N·m.",
             "Glue a GSK-02 pad on each jaw face.",
             "Bolt gripper_adapter to the body with four F09 into the inserts, 1.2 N·m.",
             "Pin TUBE-04 into the wrist tube_socket (F02); bond the other end into gripper_adapter with epoxy."],
         check=["Jaw runs end to end by turning the coupler by hand, no binding.", "Gripper limit switch trips at full open."]),
    dict(id="enclosure", title="Build the electronics enclosure", show=["ENC-01", "ENC-02", "ENC-03", "ENC-04", "ENC-05", "ENC-06", "ANG", "glands",
                                                                       "psu", "fuse", "mega", "driver", "estop"],
         view=[0.9, -1.2, 1.1], zoom=1.0,
         parts=[("ENC-01..06", "enclosure panels", 6), ("ANG", "corner angle pieces", 12), ("-", "PSU, 5 DM542 drivers, Mega, fuse, E-stop", 1),
                ("-", "PG9 x5 + PG7 x5 glands, IEC inlet", 1)],
         fasteners=[("F15", 60), ("F16", 4), ("F17", 24), ("F18", 4)], tools="laser/waterjet shop or jigsaw + drill, deburr tool, crimper",
         time="3 h",
         do=["Cut ENC-01..06 from fab/dxf; cut the 12 angle pieces (fab/CUTLIST.md) and deburr.",
             "Clamp each angle in place and transfer-drill Ø3.4 through the panel holes; assemble the box with F15.",
             "Drill the PSU, driver and Mega holes from the parts themselves (green MARK outlines on ENC-01) and mount them with F16/F17.",
             "Fit the IEC inlet, PG glands, E-stop on the lid, and the M5 earth stud. Bond every aluminium panel to earth.",
             "Set the driver DIP switches: 800 pulses/rev, current per motor (NEMA 23 about 3.0 A peak, NEMA 17 about 1.5 A)."],
         check=["Earth continuity < 0.1 Ω from the IEC earth pin to every panel.", "Mains wiring checked by a qualified person before power-up."]),
    dict(id="wiring", title="Wire the arm", show=["@Wiring"], view=[0.6, -1.3, 1.0], zoom=1.0,
         parts=[("-", "harness per fab/CUTLIST.md", 1)], fasteners=[], tools="ferrule crimper, multimeter, heat-shrink, cable ties",
         time="3 h",
         do=["Cut every run to the harness cut list (lengths include a 300 mm service loop).",
             "Motors: 4-core shielded cable through the PG9 glands to each driver A+/A-/B+/B-; shield to GND at the driver end only.",
             "Limits: 2-core twisted pair through the PG7 glands to D22-D26 and GND, 100 nF across each switch.",
             "Signals: Mega 5 V to PUL+/DIR+/ENA+; D2-D6 to PUL-, D7-D11 to DIR-, D12 to all ENA- (ELE-001).",
             "Dress cables along the arm with spiral wrap, leaving a loop at every joint for full travel."],
         check=["Each motor phase pair reads 1-3 Ω; no continuity between phases or to the case.", "Every joint moves through full travel without pulling a cable."]),
    dict(id="commission", title="Power up, home and load-test", show=["payload", "screws", "filament", "bearing~spare"], view=ISO, zoom=1.0,
         parts=[("-", "test payload, 5 lb in 1 lb steps", 1)], fasteners=[], tools="PC with Chrome or Edge, multimeter, the 3D twin",
         time="2 h",
         do=["Flash firmware/arm_controller, connect USB, open python run.py ui and use the Link tab.",
             "Rehearse every motion in SIMULATION first; then power the drivers with the arm supported, E-stop in reach.",
             "Home each joint, then calibrate HOME_DEG in arm/control.py against a protractor.",
             "Load test in 1 lb steps to 5 lb at full reach, holding 30 s at each step; watch for belt slip and creep.",
             "Re-torque every F01, F03 and F06 after the first hour of running."],
         check=["E-stop cuts all motion instantly.", "5 lb held at full reach for 30 s with no slip, no audible skipping."]),
]


def twin_steps():
    return [dict(id=s["id"], title=s["title"], show=s["show"], view=s["view"], zoom=s.get("zoom", 1.0)) for s in STEPS]


def _img(p):
    return f"{PICS.name}/{p.name}" if p.exists() else ""   # relative: the HTML sits next to the assembly/ folder


def main(argv=None):
    tot = {}
    for s in STEPS:
        for f, q in s["fasteners"]:
            tot[f] = tot.get(f, 0) + q
    css = """@page{size:A4 portrait;margin:12mm}
    :root{--ink:#14181d;--muted:#5d6670;--line:#d5dae0;--accent:#c4561a}
    body{font:10.5pt/1.45 "Segoe UI",system-ui,sans-serif;color:var(--ink);margin:0;background:#fff}
    .step{page-break-after:always;padding:0 2mm}
    h1{font-size:22pt;margin:0 0 6pt} h2{font-size:15pt;margin:0 0 6pt;border-bottom:2px solid var(--accent);padding-bottom:3pt}
    .num{display:inline-block;background:var(--accent);color:#fff;border-radius:4pt;padding:0 6pt;margin-right:6pt}
    .pic{width:100%;height:92mm;object-fit:cover;border:1px solid var(--line);border-radius:4pt;margin:4pt 0 6pt}
    .cover .pic{height:75mm} body{font-size:9.5pt}
    .cols{display:grid;grid-template-columns:1fr 1fr;gap:8pt}
    table{border-collapse:collapse;width:100%;font-size:9pt} td,th{border:1px solid var(--line);padding:2pt 4pt;text-align:left;vertical-align:top} th{background:#f2f4f6}
    ol{margin:4pt 0 6pt 16pt;padding:0} li{margin:2pt 0} .check li{list-style:'☐  '} .meta{color:var(--muted);font-size:9pt}
    .cover .lede{font-size:12pt;color:var(--muted);max-width:170mm}"""
    rows = "".join(f"<tr><td>{k}</td><td>{escape(FASTENERS[k][0])}</td><td>{escape(FASTENERS[k][1])}</td><td>{q}</td>"
                   f"<td>{FASTENERS[k][3] if FASTENERS[k][3] else '-'}</td></tr>" for k, q in sorted(tot.items()))
    cover = (f'<section class="step cover"><div class="meta">Desktop robot arm · assembly guide · rev A · {date.today().isoformat()}</div>'
             f'<h1>Assembly guide</h1><p class="lede">{len(STEPS)} steps from bare plywood to a load-tested arm. Every picture comes from the 3D test '
             'table (python run.py ui, Parts tab, Assembly steps), new parts in colour and the parts already fitted in grey. Part numbers match the drawings '
             '(P-xx printed, BASE/YAW/GSK/ENC/TUBE/SHAFT/LEG cut), fastener numbers match fab/FASTENERS.md. Torques in N·m.</p>'
             f'<img class="pic" src="{_img(PICS / "step-00-overview.png")}">'
             '<h2>Steps</h2><ol>' + "".join(f"<li>{escape(s['title'])}</li>" for s in STEPS) + "</ol>"
             '<h2>Fasteners used in this guide</h2><table><tr><th>No.</th><th>Fastener</th><th>Std</th><th>Qty</th><th>N·m</th></tr>'
             + rows + "</table></section>")
    body = ""
    for i, s in enumerate(STEPS, 1):
        pic = PICS / f"step-{i:02d}-{s['id']}.png"
        parts = "".join(f"<tr><td>{escape(a)}</td><td>{escape(b)}</td><td>{q}</td></tr>" for a, b, q in s["parts"])
        fas = "".join(f"<tr><td>{k}</td><td>{escape(FASTENERS[k][0].split(',')[0])}</td><td>{q}</td><td>{FASTENERS[k][3] or '-'}</td></tr>"
                      for k, q in s["fasteners"]) or "<tr><td colspan=4>none</td></tr>"
        body += (f'<section class="step"><h2><span class="num">{i}</span>{escape(s["title"])}</h2>'
                 f'<div class="meta">Time about {escape(s["time"])} · Tools: {escape(s["tools"])}</div>'
                 f'<img class="pic" src="{_img(pic)}">'
                 f'<div class="cols"><div><b>Parts</b><table><tr><th>Part</th><th>Description</th><th>Qty</th></tr>{parts}</table></div>'
                 f'<div><b>Fasteners</b><table><tr><th>No.</th><th>Fastener</th><th>Qty</th><th>N·m</th></tr>{fas}</table></div></div>'
                 f'<b>Do</b><ol>' + "".join(f"<li>{escape(t)}</li>" for t in s["do"]) + "</ol>"
                 f'<b>Check before moving on</b><ul class="check">' + "".join(f"<li>{escape(t)}</li>" for t in s["check"]) + "</ul></section>")
    html = f"<!doctype html><meta charset=utf-8><title>Robot arm assembly guide</title><style>{css}</style>{cover}{body}"
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "robot-arm-assembly-guide.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out, f"({len(STEPS)} steps, {sum(1 for i, s in enumerate(STEPS, 1) if (PICS / f'step-{i:02d}-{s[chr(105)+chr(100)]}.png').exists())} pictures)")
    from .pdfout import html_to_pdf
    how = html_to_pdf(out, out.with_suffix(".pdf"))
    print(f"wrote {out.with_suffix('.pdf')} ({how})" if how else "PDF skipped: no Playwright or Edge/Chrome found; open the HTML and print to PDF")
    return 0


def guide(argv=None):
    """Write arm_model.json, serve the twin on a spare port, render the step pictures with Node, then build the guide."""
    import subprocess, threading, socketserver, http.server, functools
    from . import twin
    twin.write()
    class Quiet(http.server.SimpleHTTPRequestHandler):
        extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, ".js": "text/javascript"}
        def log_message(self, *a): pass
    handler = functools.partial(Quiet, directory=str(HERE))
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{httpd.server_address[1]}/control/index.html"
    try:
        r = subprocess.run(["node", str(HERE / "tools" / "guide_pictures.js"), str(PICS), url], check=False)
        if r.returncode:
            print("pictures not rendered (npm i playwright && npx playwright install chromium); building with the existing ones")
    except FileNotFoundError:
        print("Node.js not found: building the guide with the existing pictures")
    finally:
        httpd.shutdown()
    return main(argv)


if __name__ == "__main__":
    main()
