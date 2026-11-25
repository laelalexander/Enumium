"""Project file + library tables, and the netlist-vs-design check (KiCad's own netlist export is the referee)."""
import json
import os
import shutil
import subprocess

from core import LIBNAME, LIBSYM, LIBFP
from sexpr import parse, find, findall


def write_project(D, out, sch_files):
    classes = []

    def ncls(name, width, clearance, prio, dp=(0.2, 0.25), via=(0.6, 0.3)):
        return {"bus_width": 12, "clearance": clearance, "diff_pair_gap": dp[1], "diff_pair_via_gap": 0.25,
                "diff_pair_width": dp[0], "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                "name": name, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
                "track_width": width, "via_diameter": via[0], "via_drill": via[1], "wire_width": 6}
    classes.append(ncls('Default', D.signal_width, D.signal_clearance, 0))
    pats = []
    for name, c in D.netclasses.items():
        classes.append(ncls(name, c['width'], c['clearance'], 0, c.get('diff', (0.2, 0.25)), c.get('via', (0.6, 0.3))))
        for n in c['nets']:
            pats.append({"netclass": name, "pattern": n})
    pro = {
        "board": {"design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "silk_line_width": 0.12,
                         "silk_text_size_h": 1.0, "silk_text_size_v": 1.0, "silk_text_thickness": 0.15},
            "rules": dict(D.fab.get('rules', {})),
            "rule_severities": {"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore", "silk_over_copper": "ignore", "silk_overlap": "ignore", "silk_edge_clearance": "ignore"},
            "track_widths": [0.0] + sorted({c['width'] for c in D.netclasses.values()} | {D.signal_width}),
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}]}},
        "boards": [], "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": D.project + ".kicad_pro", "version": 1},
        "net_settings": {"classes": classes, "meta": {"version": 3}, "net_colors": None,
                         "netclass_assignments": None, "netclass_patterns": pats},
        "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [], "text_variables": {}}
    json.dump(pro, open(os.path.join(out, D.project + '.kicad_pro'), 'w'), indent=2)
    # project-local library copies so the project folder is self-contained
    shutil.copy(LIBSYM, os.path.join(out, LIBNAME + '.kicad_sym'))
    dst = os.path.join(out, LIBNAME + '.pretty')
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(LIBFP, dst)
    syml = sorted({p['sym'].split(':')[0] for p in D.parts})
    fpl = sorted({p['fp'].split(':')[0] for p in D.parts if p['fp']})
    with open(os.path.join(out, 'sym-lib-table'), 'w') as f:
        f.write('(sym_lib_table\n')
        for l in syml:
            uri = '${KIPRJMOD}/%s.kicad_sym' % l if l == LIBNAME else '${KICAD7_SYMBOL_DIR}/%s.kicad_sym' % l
            f.write('  (lib (name "%s")(type "KiCad")(uri "%s")(options "")(descr ""))\n' % (l, uri))
        f.write(')\n')
    with open(os.path.join(out, 'fp-lib-table'), 'w') as f:
        f.write('(fp_lib_table\n')
        for l in fpl:
            uri = '${KIPRJMOD}/%s.pretty' % l if l == LIBNAME else '${KICAD7_FOOTPRINT_DIR}/%s.pretty' % l
            f.write('  (lib (name "%s")(type "KiCad")(uri "%s")(options "")(descr ""))\n' % (l, uri))
        f.write(')\n')


def check_netlist(D, out):
    """Export KiCad's netlist from the schematic and compare it, net by net, with the design table."""
    os.makedirs(os.path.join(out, 'build'), exist_ok=True)
    net = os.path.join(out, 'build', 'netlist.net')
    r = subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', net,
                        os.path.join(out, D.project + '.kicad_sch')], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit('netlist export failed: ' + r.stdout + r.stderr)
    t = parse(open(net, encoding='utf-8').read())
    nets, padnet = {}, {}
    for n in findall(find(t, 'nets'), 'net'):
        name = find(n, 'name')[1].lstrip('/')
        for node in findall(n, 'node'):
            ref, pin = find(node, 'ref')[1], find(node, 'pin')[1]
            nets.setdefault(name, set()).add((ref, pin))
            padnet.setdefault(ref, {})[pin] = name
    exp = D.expected_nets()
    bad = []
    for name, pins in exp.items():
        if nets.get(name) != pins:
            bad.append('net %s missing %s extra %s' % (name, sorted(pins - nets.get(name, set()))[:6],
                                                       sorted(nets.get(name, set()) - pins)[:6]))
    for name in nets:
        if name not in exp and not name.startswith('unconnected-') and not name.startswith('Net-('):
            bad.append('unexpected net ' + name)
    comps = {find(c, 'ref')[1] for c in findall(find(t, 'components'), 'comp')}
    want = {p['ref'] for p in D.parts}
    if comps != want:
        bad.append('component mismatch ' + str(sorted(comps ^ want))[:300])
    rep = os.path.join(out, 'build', 'netlist-check.txt')
    with open(rep, 'w') as f:
        f.write('schematic netlist vs design table: %s\n' % ('MATCH' if not bad else 'DIFFERS'))
        f.write('components %d, named nets %d\n' % (len(comps), len(exp)))
        f.write('\n'.join(bad) + '\n')
    print('netlist check:', 'MATCH' if not bad else 'DIFFERS (%d)' % len(bad), '-', len(comps), 'parts', len(exp), 'nets')
    for b in bad[:15]:
        print('  ', b)
    json.dump(padnet, open(os.path.join(out, 'build', 'netlist.json'), 'w'), indent=0)
    return not bad, padnet
