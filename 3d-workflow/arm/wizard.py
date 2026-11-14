"""Build wizard engine: turn the current specs into a complete build kit in one run.

    python run.py wizard [--payload-lb 5] [--reach-in 39.4] [--bed 256x256x256] [--arms 1] [--kit-only]

Runs every generator in order and prints "== STEP i/N title" / "== OK" / "== WARN" lines that the app's Build wizard
turns into a progress list. A failed optional step (PNG render, slicing, pictures, PDFs) is reported and skipped;
the kit is still built from the newest files available."""
import argparse, sys, time, traceback


def _run(label, fn, required):
    t = time.time()
    try:
        fn()
        print(f"== OK {label} ({time.time() - t:.0f} s)", flush=True)
        return True
    except SystemExit as e:
        if e.code in (0, None):
            print(f"== OK {label} ({time.time() - t:.0f} s)", flush=True)
            return True
        print(f"== {'FAIL' if required else 'WARN'} {label}: {e.code}", flush=True)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(f"== {'FAIL' if required else 'WARN'} {label}: {e.__class__.__name__}: {e}", flush=True)
    return not required


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--payload-lb", type=float, default=5.0)
    ap.add_argument("--reach-in", type=float, default=39.4)
    ap.add_argument("--bed", default="256x256x256")
    ap.add_argument("--arms", type=int, default=1)
    ap.add_argument("--kit-only", action="store_true", help="skip regeneration; package the current design as a kit")
    a = ap.parse_args(argv)
    ext_m = round(a.reach_in * 0.0254, 4)
    if not 0.3 <= ext_m <= 1.219:
        sys.exit("reach must be 12-48 in")
    from . import build, drawings, fab, render, printprep, procure, assembly, buildbook, twin, kit

    steps = [] if a.kit_only else [
        ("Size the drives and generate the CAD", lambda: (build.build(a.payload_lb, ext_m), drawings.main()), True),
        ("Cut files, drawings and fastener schedule", fab.main, True),
        ("Render drawing pictures", render.main, False),
        (f"Plate and slice the 3D prints ({a.bed} bed)", lambda: printprep.main(["--bed", a.bed]), False),
        ("Purchase list with prices", procure.main, True),
        ("Illustrated assembly guide", lambda: assembly.guide([]), False),
        ("Build book PDF", buildbook.main, False),
    ]
    steps += [("App model and Library", twin.write, True),
              (f"Build kit for {a.arms} arm{'s' if a.arms > 1 else ''}", lambda: kit.build(a.arms), True)]
    print(f"== PLAN {len(steps)}", flush=True)
    ok = True
    for i, (label, fn, req) in enumerate(steps, 1):
        print(f"== STEP {i}/{len(steps)} {label}", flush=True)
        ok = _run(label, fn, req) and ok
        if not ok:
            break
    print("== DONE" if ok else "== STOPPED", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
