"""Post-finish touch-up for a routed board: narrow over-wide routed power tracks that break clearance, drop dangling
unlocked stubs, re-stitch fill islands, then re-run the repair pass and DRC.  python3 touchup.py <board>"""
import math
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew   # noqa: E402
import build    # noqa: E402
import pcb      # noqa: E402

name = sys.argv[1]
m = build.load(name)
D = m.D
c = pcb.Ctx(D)
out = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'boards', name))
path = os.path.join(out, name + '.kicad_pcb')
board = pcbnew.LoadBoard(path)
rpt = os.path.join(out, 'build', 'touchup-drc.rpt')
item = re.compile(r'@\(([-\d.]+) mm, ([-\d.]+) mm\): (Track|Via) \[([^\]]*)\] on ([\w.]+)(?: - [\w.]+)?(?:, length ([\d.]+) mm)?')


def find_track(x, y, net, lay, ln):
    best = None
    for t in board.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetNetname() != net or board.GetLayerName(t.GetLayer()) != lay:
            continue
        if ln and abs(pcbnew.ToMM(t.GetLength()) - float(ln)) > 0.002:
            continue
        a, e = t.GetStart(), t.GetEnd()
        d = pcb._sd(x, y, pcbnew.ToMM(a.x), pcbnew.ToMM(a.y), pcbnew.ToMM(e.x), pcbnew.ToMM(e.y))
        if d < 0.05 and (best is None or d < best[0]):
            best = (d, t)
    return best[1] if best else None


def drc():
    pcb.fill(board)
    pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    return open(rpt).read()


best = None
for rnd in range(int(os.environ.get('ROUNDS', '6'))):
    txt = drc()
    n_v = int(re.search(r'Found (\d+) DRC violations', txt).group(1))
    n_u = int(re.search(r'Found (\d+) unconnected', txt).group(1))
    print('round %d: %s violations, %s unconnected' % (rnd, n_v, n_u), flush=True)
    if best is None or n_v + n_u < best:
        best = n_v + n_u
        pcbnew.SaveBoard(path, board)
        print('  saved (best so far)', flush=True)
    if n_v + n_u == 0:
        break
    changed = pcb.drop_clashes(board, rpt) if rnd else 0
    if changed:
        print('  dropped clashes', changed)
    for blk in re.split(r'\n(?=\[)', txt):
        if blk.startswith('[clearance]'):
            need = re.search(r'clearance ([\d.]+) mm; actual ([\d.]+) mm', blk)
            short = float(need.group(1)) - float(need.group(2)) if need else 0.1
            for (x, y, kind, net, lay, ln) in item.findall(blk):
                if kind != 'Track':
                    continue
                t = find_track(float(x), float(y), net, lay, ln)
                if t is None or t.IsLocked():
                    continue
                w = pcbnew.ToMM(t.GetWidth())
                if w > 0.3 + 1e-6:
                    t.SetWidth(pcbnew.FromMM(max(0.3, w - 2 * short - 0.04)))
                    changed += 1
                    break
        elif blk.startswith('[via_dangling]'):
            for (x, y, kind, net, lay, ln) in item.findall(blk):
                for t in list(board.GetTracks()):
                    if t.GetClass() == 'PCB_VIA' and not t.IsLocked() and t.GetNetname() == net and \
                            math.hypot(pcbnew.ToMM(t.GetPosition().x) - float(x), pcbnew.ToMM(t.GetPosition().y) - float(y)) < 0.01:
                        board.Remove(t)
                        changed += 1
        elif blk.startswith('[track_dangling]'):
            for (x, y, kind, net, lay, ln) in item.findall(blk):
                t = find_track(float(x), float(y), net, lay, ln)
                if t is not None and not t.IsLocked():
                    board.Remove(t)
                    changed += 1
    ni = sum(pcb.stitch_islands(board, c, n_) for n_ in sorted({z['net'] for z in D.pours if z['layer'] in ('F', 'B')}))
    if ni:
        print('  island vias', ni)
        changed += ni
    pcb.fill(board)
    pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    pairs = pcb.drc_pairs(rpt, board)
    if pairs:
        clr = max([0.25, getattr(D, 'signal_clearance', 0.2)] + [nc.get('clearance', 0.2) for nc in getattr(D, 'netclasses', {}).values()])
        fixed, failed = pcb.repair(board, c, pairs, clearance=clr)
        print('  repair: %d of %d, left %s' % (fixed, len(pairs), sorted(set(failed))))
        changed += fixed
    if not changed:
        break
pcb.set_stackup(D, path)
board = pcbnew.LoadBoard(path)
final = os.path.join(out, 'fab', D.project + '-drc.rpt')
pcbnew.WriteDRCReport(board, final, pcbnew.EDA_UNITS_MILLIMETRES, True)
print('DRC:', re.findall(r'\*\* Found (\d+) (DRC violations|unconnected pads|Footprint errors)', open(final).read()))
