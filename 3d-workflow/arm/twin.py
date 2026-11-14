"""Digital twin / control surface for the robot arm.

    python run.py ui            # write control/arm_model.json, serve on http://127.0.0.1:8765, open the browser
    python -m arm.twin --no-open --port 8765
    python -m arm.twin --write-only

The browser app (control/index.html) assembles the real STL parts from design/cad/stl,
simulates every stepper channel with the same protocol as firmware/arm_controller, and can
drive the real Arduino over Web Serial (Chrome or Edge; localhost counts as a secure context).
Everything it knows about the arm comes from arm_model.json, generated here from the same
sources as the BOM and drawings, so `python run.py build` followed by `python run.py ui`
keeps the twin in step with the design."""
import argparse, functools, http.server, json, math, socketserver, sys, threading, webbrowser
from pathlib import Path

from . import design as D, hardware as H, build as B, assembly as A
from .actuators import BY_KEY
from .control import Arm, MICROSTEP, STEPS_PER_MM_GRIP

HERE = Path(__file__).resolve().parent.parent
CONTROL = HERE / "control"
DESIGN_JSON = HERE / "design" / "design.json"

# Driver DIP options (DM542 family). Values are what the twin offers in its dropdowns.
PULSES_PER_REV = [400, 800, 1600, 3200, 6400, 12800, 25600, 1000, 2000, 4000, 5000, 8000, 10000, 20000, 25000]
CURRENT_PEAK_A = [1.00, 1.46, 1.91, 2.37, 2.84, 3.31, 3.76, 4.20]

WIRING = {  # channel -> pins, same as docs/WIRING.md and firmware/arm_controller
    0: dict(step=2, dir=7, limit=22), 1: dict(step=3, dir=8, limit=23), 2: dict(step=4, dir=9, limit=24),
    3: dict(step=5, dir=10, limit=25), 4: dict(step=6, dir=11, limit=26),
}
ENABLE_PIN = 12
MEGA_COMBINED_SPS = 4000   # firmware note: Mega + AccelStepper tops out near ~4 kHz combined


def belt_ratio(drive_key, joint):
    if joint == "wrist":
        return 1
    r = BY_KEY[drive_key].ratio
    return round(r / 20) if r >= 20 else 1


def model(d=None):
    d = d or json.loads(DESIGN_JSON.read_text(encoding="utf-8"))
    drives = {j: v["drive"] for j, v in d["joints"].items()}
    drives["yaw"] = "n23_20"
    joints = []
    for name in ("yaw", "shoulder", "elbow", "wrist"):
        dr = BY_KEY[drives[name]]
        br = 1 if name == "yaw" else belt_ratio(dr.key, name)
        center = None if name == "yaw" else H.belt_center_mm(br)
        lo, hi = Arm.LIMITS[name]
        jd = d["joints"].get(name, {})
        joints.append(dict(
            name=name, channel=Arm.CH[name], drive=dr.key, search_terms=dr.search_terms,
            motor="NEMA23", motor_hold_nm=dr.motor_hold_nm, motor_amps=dr.amps,
            gearbox_ratio=20, belt_ratio=br, total_ratio=dr.ratio, eff=dr.eff,
            rated_nm=round(dr.rated_nm, 2), required_nm=jd.get("required_nm"), backlash_arcmin=dr.backlash_arcmin,
            mass_kg=dr.mass_kg, belt_center_mm=center, block_x0=None if name == "yaw" else H.block_x0(br), small_teeth=16, large_teeth=16 * br,
            belt_teeth=None if center is None else B.belt_teeth(16, br, center),
            limits_deg=[lo, hi], home_dir=Arm.HOME_DIR[name], home_deg=Arm.HOME_DEG[name],
            max_dps={"yaw": 30, "shoulder": 10, "elbow": 15, "wrist": 30}[name], pins=WIRING[Arm.CH[name]]))
    gripper = dict(name="gripper", channel=Arm.GRIP, motor="NEMA17", lead_mm_per_rev=8, open_mm=[0, 70],
                   motor_amps=1.5, steps_per_mm_default=STEPS_PER_MM_GRIP, max_mm_s=10, pins=WIRING[Arm.GRIP])
    ratios = {j: belt_ratio(v, j) for j, v in drives.items() if j in ("shoulder", "elbow")}
    pm = HERE / "print" / "manifest.json"
    manifest = json.loads(pm.read_text(encoding="utf-8"))["parts"] if pm.exists() else {}
    printed = [dict(id=n, qty=q, note=note, stl=f"{n}.stl", drawing=f"{n}.svg", step=f"{n}.step", obj=f"{n}.obj",
                    code=code.strip(), bbox_mm=d.get("parts", {}).get(n, {}).get("bbox_mm"), print=manifest.get(n))
               for n, (code, q, note) in H.parts(ratios).items()]
    STOCK = [("round tube", ["TUBE-01", "TUBE-02", "TUBE-03", "TUBE-04"]), ("12 mm hardened", ["SHAFT-01"]), ("Plywood", ["BASE-01"]),
             ("plate 6 mm", ["YAW-01"]), ("sheet 5052", [f"ENC-0{i}" for i in range(1, 7)]), ("angle 10 x 10", ["ANG"]),
             ("Neoprene", ["GSK-01"]), ("Rubber sheet", ["GSK-02", "GSK-03"]), ("Hardwood", ["LEG-01"])]
    purchased = [dict(item=a, qty=q, search=s, use=u, makes=next((m for k, m in STOCK if k.lower() in a.lower()), None))
                 for a, q, s, u in B.AMAZON_ITEMS]
    fj = HERE / "fab" / "fab.json"
    fabricated = json.loads(fj.read_text(encoding="utf-8")) if fj.exists() else []
    return dict(
        generated_by="python -m arm.twin", stl_base="../design/cad/stl/", drawing_base="../design/drawings/",
        step_base="../design/cad/step/", obj_base="../design/cad/obj/", print_base="../print/", sheet_base="../design/drawings/",
        fab_base="../fab/", fabricated=fabricated, assembly=A.twin_steps(),
        payload_lb=d["payload_lb"], extension_in=d["extension_in"], l1_mm=d["l1_mm"], l2_mm=d["l2_mm"],
        max_extension_mm=round(D.MAX_EXTENSION * 1000), safety=D.SAFETY,
        mass=dict(tube_kg_per_m=D.TUBE_KG_PER_M, joint_hw_kg=D.JOINT_HW_KG, gripper_kg=D.GRIPPER_KG,
                  payload_arm_m=D.PAYLOAD_ARM, tool_len_m=D.TOOL_LEN),
        hw=H.HW, microstep_default=MICROSTEP, pulses_per_rev_options=PULSES_PER_REV, current_options_a=CURRENT_PEAK_A,
        enable_pin=ENABLE_PIN, mega_combined_sps=MEGA_COMBINED_SPS, baud=115200,
        joints=joints, gripper=gripper, printed=printed, purchased=purchased)


def write(dest=CONTROL / "arm_model.json"):
    dest.write_text(json.dumps(model(), indent=1), encoding="utf-8")
    from . import library
    library.build()
    return dest


def serve(port=8765, open_browser=True):
    write()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(HERE))
    handler.extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                              ".js": "text/javascript", ".json": "application/json", ".stl": "model/stl"}
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), handler) as httpd:
        url = f"http://127.0.0.1:{port}/control/index.html"
        print(f"Robot arm control surface: {url}\n(Chrome or Edge for the hardware link. Ctrl+C to stop.)")
        if open_browser:
            threading.Timer(0.6, webbrowser.open, (url,)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--write-only", action="store_true")
    a = ap.parse_args(argv)
    if a.write_only:
        print("wrote", write())
    else:
        serve(a.port, not a.no_open)


if __name__ == "__main__":
    main()
