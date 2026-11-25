"""Build one board:  python3 kgen/build.py <board> [sch|place|route|finish|fab|all]  (default all)."""
import importlib.util
import json
import os
import sys

KG = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KG)
import symgen, fpgen, sch, proj, pcb   # noqa: E401,E402


def load(board):
    path = os.path.join(KG, '..', 'boards', board, 'design.py')
    spec = importlib.util.spec_from_file_location('design_' + board, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main(board, stage="all", passes=14, timeout=2400):
    symgen.write()
    fpgen.write()
    m = load(board)
    D = m.D
    out = os.path.normpath(os.path.join(KG, '..', 'boards', board))
    files = sch.write(D, out)
    proj.write_project(D, out, files)
    ok, padnet = proj.check_netlist(D, out)
    if not ok:
        raise SystemExit('schematic netlist differs from the design table - stop')
    if hasattr(m, 'REPORT'):
        json.dump(m.REPORT, open(os.path.join(out, 'build', 'hs-pairs.json'), 'w'), indent=0)
    if stage in ('place', 'all', 'route'):
        pcb.place(D, out, padnet)
    if stage in ('all', 'route'):
        pcb.route(D, out, passes=passes, timeout=timeout)
    if stage in ('all', 'finish', 'route'):
        pcb.finish(D, out, padnet)
    if stage in ('all', 'fab', 'finish', 'route'):
        import fab
        fab.make(D, out, m)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'all')
