"""Tower bill of materials (TS2B-BOM) rolled up from the CAD assembly (mechanical/assembled/assembly.json).
Sub-meshes of one item count once; a description ending '(xN)' is one kit of N.\nWrites bom/TS2B-BOM.csv and bom/TS2B-BOM.xlsx: one line per part number, quantity per tower and per column."""
import csv, json, os, re, collections
here = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(here, '..', 'mechanical', 'assembled', 'assembly.json')))
# one physical item is often several meshes (a GPU = shroud, back plate, PCB, fan, power plug, bracket): count items
SUB = re.compile(r'_(shroud|back|pcb|fan|pwr|bracket|rear|rotor|motor|sheet|fins|tubes|headers|cable|plug)$')
seen = set()
rows = collections.OrderedDict()
for n in A['nodes']:
    item = (n['pn'], SUB.sub('', n['node']))
    if item in seen:
        continue
    seen.add(item)
    k = n['pn']
    r = rows.setdefault(k, dict(pn=k, name=n['name'], kind=n['kind'], material=n['material'] or '', finish=n['finish'] or '',
                                drawing=n['drawing'] or '', qty=0, per_col=collections.Counter()))
    r['qty'] += 1
    r['per_col'][n.get('column', 0)] += 1
for k in rows.values():
    k['name'] = k['name'].replace(' (shroud)', '')
# boards that are not drawn in the CAD (they sit inside the plinth arm and the thermal module)
for pn, name, q in (('CCM-1', 'CCM-1 cooling controller board (KiCad, RushPCB turnkey)', 4),
                    ('TCD-1', 'TCD-1 Peltier driver board (KiCad, RushPCB turnkey)', 4),
                    ('HAR-1', 'Column wiring harness set per TS2B-ELE-101 / -102', 4)):
    rows.setdefault(pn, dict(pn=pn, name=name, kind='pcb' if pn != 'HAR-1' else 'make', material='', finish='',
                             drawing='electrical/harness/out' if pn == 'HAR-1' else 'electrical/boards/' + pn.lower().replace('-', ''),
                             qty=q, per_col=collections.Counter({c: 1 for c in (1, 2, 3, 4)})))
order = {'make': 0, 'pcb': 1, 'buy': 2}
lines = sorted(rows.values(), key=lambda r: (order.get(r['kind'], 3), r['pn']))
hdr = ['Line', 'Part number', 'Description', 'Make / buy', 'Material', 'Finish', 'Drawing', 'Qty per column', 'Qty per tower']
out = []
for i, r in enumerate(lines, 1):
    pc = [v for c, v in r['per_col'].items() if c]
    if pc:
        per_col = pc[0] if len(set(pc)) == 1 and len(pc) == 4 else ''
    else:                       # untagged parts: the four columns are identical, so a multiple of 4 is per column
        per_col = r['qty'] // 4 if r['qty'] % 4 == 0 and not r['name'].lower().startswith(('tower', 'crown', 'chimney')) else ''
    out.append([i, r['pn'], r['name'], r['kind'], r['material'], r['finish'], r['drawing'], per_col, r['qty']])
with open(os.path.join(here, 'TS2B-BOM.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(hdr); w.writerows(out)
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    wb = Workbook(); ws = wb.active; ws.title = 'TS2B-BOM rev B'
    ws.append(hdr)
    for c in ws[1]:
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='C8102E')
    for r in out:
        ws.append(r)
    for col, wdt in zip('ABCDEFGHI', (6, 14, 60, 10, 30, 26, 12, 14, 13)):
        ws.column_dimensions[col].width = wdt
    ws.freeze_panes = 'A2'
    wb.save(os.path.join(here, 'TS2B-BOM.xlsx'))
except ImportError:
    pass
print('BOM lines', len(out), 'placed parts', sum(r['qty'] for r in rows.values()))
