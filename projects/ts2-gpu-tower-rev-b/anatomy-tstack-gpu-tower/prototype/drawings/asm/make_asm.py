"""TS2B-ASM-100: illustrated column build, focused on how the 16 GPUs are connected, secured and cooled.

Renders each step from the assembled model (mechanical/assembled/ts2b.glb) in headless Chromium (render.html,
shoot.mjs), then lays out one A3 sheet per step: picture with numbered balloons, parts list, numbered instructions,
torques, tools and checks.  Output: drawings/TS2B-ASM-100_column_build.pdf

Run:  python3 drawings/asm/make_asm.py
"""
import json
import os
import socket
import subprocess
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Rectangle               # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..'))       # folder holding prototype/ and sim/
OUT = os.path.join(HERE, 'render')
os.makedirs(OUT, exist_ok=True)
IN = 25.4

FRAME = ['^C1_(base_plate|top_plate|bulkhead|post_\\d|crossmember)$']
CARRIER = ['C1_bp_carrier', 'C1_busbar']
BOARDS = ['^C1[LU]_cbp8']
CABLES = ['^C1_S\\d\\d_(cem|mcio)']
GUIDES = ['^C1[LU]?_(bracket_rail|tail_comb|comb_liners|hinge_block)']
GPU = ['^C1_S\\d\\d_gpu_']
PWR = ['^C1_S\\d\\d_(h12v|gpu_cable)']
HOLD = ['^C1[LU]_(holddown|latch)']
COOL = ['C1_coil_', 'C1_drip_tray', 'C1_filter', 'C1_grille']
SKIN = ['C1_side_skin', 'C1_light_bar', 'C1_plenum_corner']
FRONT = [1.15, 1.35, 0.55]        # card-insertion side (+v) of column C1
REAR = [0.55, -1.35, 0.45]        # rear cable / busbar channel (-v)

STEPS = [
    dict(id='01', title='Column frame', view=dict(show=FRAME, highlight=FRAME, dir=FRONT,
         balloons={'1': ['C1_base_plate'], '2': ['C1_post_1'], '3': ['C1_bulkhead'], '4': ['C1_top_plate'], '5': ['C1_crossmember']}),
         parts=[('1', 'TS2B-201', 'Column base plate', 1), ('2', 'B-110', 'Post, HFS6-3030 x 952.8', 4),
                ('3', 'TS2B-203', 'Exhaust bulkhead', 1), ('4', 'TS2B-202', 'Column top plate', 1),
                ('5', 'TS2B-211', 'Midspan crossmember', 1), ('-', 'B-111', 'SHCS M8 x 25 A2-70, slot-6 T-nut M6', '8 / 24')],
         text=['Set the base plate (1) on the bench, datum face A down.  Stand the four posts (2) on it and fit M8 x 25 '
               'SHCS from below through the counterbores into the tapped post ends: 25 N m, Loctite 243.',
               'Slide the bulkhead (3) down into the 3.2 mm groove in the base plate, black (plenum) face toward the '
               'column centre.  Fix its edge holes to the inner posts with M6 x 10 into slot-6 T-nuts: 8 N m.',
               'Fit the crossmember (5) at mid height on 4x M6 into post T-nuts (8 N m).  Its latch keepers face +v.',
               'Lower the top plate (4) onto the posts and the bulkhead groove; M8 x 25 SHCS from above, 25 N m.',
               'Check: diagonals of the post square equal within 1.0 mm; bulkhead free of bow (0.5 mm over 900 mm).'],
         tools='Hex keys 5 / 6 mm, torque wrench 5-30 N m, square, 1 m straight edge'),
    dict(id='02', title='Backplane carrier and column busbars', view=dict(show=FRAME + CARRIER, highlight=CARRIER, ghost=FRAME, dir=REAR,
         balloons={'1': ['C1_bp_carrier'], '2': ['C1_busbar_12V'], '3': ['C1_busbar_RTN']}),
         parts=[('1', 'TS2B-214', 'Backplane carrier plate', 1), ('2', 'TS2B-215', '+12 V busbar 14 x 10 Cu', 1),
                ('3', 'TS2B-216', 'RTN busbar 14 x 10 Cu', 1), ('-', 'B-215C', 'Angle clip 30 x 30 x 3 + M4 x 10', 4),
                ('-', 'B-215S', 'FR4 spacer 2 mm, PTFE sleeves, Cu bushes 6 / 18 mm', 'set')],
         text=['Fix the carrier (1) to the base and top plates with four angle clips, M4 x 10: 2.5 N m.  Its open bottom '
               'slot lines up with the busbar pass in the base plate.',
               'Feed the +12 V busbar (2, red sleeve) up from the arm through the base-plate pass, then the 2 mm FR4 '
               'spacer strip, then the RTN busbar (3, black sleeve).  Leave the stud holes loosely aligned.',
               'Do not tighten anything yet: the CBP-8 studs set the final position in step 3.',
               'Check: 3 mm minimum air or FR4 between the bars everywhere; bars clear the carrier slot by 1 mm.'],
         tools='Hex key 2.5 mm, torque screwdriver 1-5 N m'),
    dict(id='03', title='CBP-8 backplanes (lower and upper)', view=dict(show=FRAME + CARRIER + BOARDS, highlight=BOARDS, ghost=FRAME, dir=REAR,
         balloons={'1': ['^C1L_cbp8$'], '2': ['^C1U_cbp8$'], '3': ['C1L_cbp8_rear'], '4': ['C1_busbar_12V']}),
         parts=[('1', 'CBP-8', 'GPU backplane, lower (ADDR straps 0x20)', 1), ('2', 'CBP-8', 'GPU backplane, upper (0x21, R904 + JP901 fitted)', 1),
                ('3', 'B-112', 'FHS-M6-35 studs (pressed at PCBA) + Cu bushes', 8), ('-', 'B-113', 'M3 x 12 hex standoff + M3 x 6', 12),
                ('4', 'TS2B-215/216', 'Busbars from step 2', '-')],
         text=['ESD: wrist strap and mat for every board step from here on.',
               'Fit the M3 x 12 standoffs into the carrier (6 per board).  The right-hand board edge has no standoff: '
               'the four stud stacks carry it.',
               'Put a 6 mm Cu bush on each +12 V stud and an 18 mm Cu bush in a PTFE sleeve on each RTN stud.  Offer the '
               'board up so the studs pass through the busbar holes, then screw it to the standoffs: M3, 0.5 N m.',
               'Busbar nuts: M6 flange nut + Belleville on every stud, 6 N m, +12 V bar first, then RTN.  Joint compound '
               'on every copper face.',
               'Upper board only: fit R904 (120 ohm) and the JP901 link to terminate the column RS-485 bus.',
               'Check: 0.0 ohm stud to bar; > 10 Mohm +12 V to RTN with the PSUs disconnected.'],
         tools='Torque wrench 2-10 N m, 10 mm socket, ESD kit, multimeter'),
    dict(id='04', title='CEM slots and MCIO host cables', view=dict(show=FRAME + CARRIER + BOARDS + CABLES, highlight=CABLES,
         ghost=FRAME + CARRIER, dir=REAR, balloons={'1': ['C1_S04_cem'], '2': ['^C1_S04_mcio$'], '3': ['C1_S04_mcio_cable'], '4': ['C1_S12_mcio_cable']}),
         parts=[('1', 'B-010', 'PCIe x16 CEM slot (on CBP-8, x8 electrical)', 16), ('2', 'B-011', 'MCIO 8i receptacle (on CBP-8)', 16),
                ('3', 'B-012', 'MCIO 8i cable, lower group 1.0-1.75 m', 8), ('4', 'B-012', 'MCIO 8i cable, upper group 1.5-2.25 m', 8)],
         text=['Each slot has its own MCIO 8i cable (Gen4 x8) to a HighPoint Rocket 1628A port in the arm host.  Lengths '
               'and gauge per TS2B-ELE-102 sheet "Cables"; every cable carries its slot label at both ends.',
               'Plug each cable into its CBP-8 receptacle until it clicks; pull test 20 N.  Route straight down the rear '
               'channel (x 240-450) to the base-plate pass; minimum bend radius 25 mm; no ties tighter than finger tight.',
               'Upper-group cables run behind the lower board in the same channel, in slot order.',
               'Check: every link label matches the host port map; channel cover clear of all plugs.'],
         tools='Cable labels, Velcro ties, flush cutters'),
    dict(id='05', title='Card guides: bracket rails, tail combs, hinge blocks', view=dict(show=FRAME + CARRIER + BOARDS + CABLES + GUIDES,
         highlight=GUIDES, ghost=FRAME + CARRIER + BOARDS + CABLES, dir=FRONT,
         balloons={'1': ['C1L_bracket_rail'], '2': ['C1_tail_comb_lower'], '3': ['C1_comb_liners'], '4': ['C1L_hinge_block']}),
         parts=[('1', 'TS2B-205', 'Bracket screw rail (8x 6-32)', 2), ('2', 'TS2B-206', 'Tail guide comb (16 slots)', 2),
                ('3', 'B-206', 'EPDM U-trim 1.0 mm, comb liners', 32), ('4', 'TS2B-209', 'Hold-down hinge block pair', 2)],
         text=['Bracket rails (1): 3x M4 x 16 from the plenum side through the bulkhead countersinks, 2.5 N m.  The rail '
               'face is the datum the GPU bracket tab seats on (v 64.6).',
               'Press an EPDM U-trim liner (3) onto both cheeks of every comb slot, then fit the combs (2) between base and '
               'top plate: M6 x 12 at each end, 8 N m.  A card tail must slide with 5-15 N and no side play.',
               'Hinge blocks (4): lower pair on the base plate, upper pair under the top plate, M5 x 16, 4.5 N m.',
               'Check: slot-to-slot pitch 50.8 +/- 0.2 on comb and rail (gauge pin 6-32 thread check on all 16 holes).'],
         tools='Hex keys 2.5 / 3 / 4 mm, torque screwdriver, 6-32 thread gauge'),
    dict(id='06', title='GPU insertion (one card shown)', view=dict(show=FRAME + BOARDS + CABLES + GUIDES + ['C1_S01_gpu', 'C1_S02_gpu', 'C1_S03_gpu'],
         highlight=['C1_S03_gpu'], red=False, ghost=FRAME + CABLES, dir=FRONT, explode=dict(nodes=['C1_S03_gpu'], vec=[0, 260, 0]),
         fitTo=['^C1_S0[1-4]_'], zoom=0.75,
         balloons={'1': ['C1_S03_gpu_shroud'], '2': ['C1_S03_gpu_bracket'], '3': ['C1_S03_cem'], '4': ['C1_tail_comb_lower'], '5': ['C1L_bracket_rail']}),
         parts=[('1', 'B-001', 'RTX PRO 6000 Blackwell Max-Q (300 W, blower)', 1), ('2', 'B-001', 'Card full-height bracket + thumbscrew 6-32', 1),
                ('3', 'B-010', 'CEM slot on CBP-8 (step 4)', '-'), ('4', 'TS2B-206', 'Tail comb slot', '-'), ('5', 'TS2B-205', 'Bracket rail', '-')],
         text=['Work from the bottom slot up.  ESD strap on.  Remove the card from its bag by the shroud, never the fingers.',
               'Lay the card flat, shroud up, with its tail in the lined comb slot (4) and its bracket toward the bulkhead.',
               'Slide it along -v into the CEM slot (3).  Push square on the bracket end; the fingers seat at 60-115 N.  '
               'The bracket tab lands on the rail (5).',
               'Fit the bracket thumbscrew into the rail: 6-32, 0.6 N m (finger tight plus 1/8 turn).',
               'The blower exhausts through the bracket vents into the bulkhead window behind it (plenum); never block '
               'a window.',
               'Check: no visible gold on the fingers; card level with its neighbours within 0.5 mm.'],
         tools='ESD kit, torque screwdriver 0.3-1.5 N m'),
    dict(id='07', title='GPU power: 12V-2x6 cable', view=dict(show=FRAME + BOARDS + GUIDES + ['^C1_S0[1-4]_'], highlight=PWR, red=True,
         ghost=FRAME, dir=FRONT, fitTo=['^C1_S0[2-4]_'], zoom=0.6, balloons={'1': ['C1_S03_h12v'], '2': ['C1_S03_gpu_cable'], '3': ['C1_S03_gpu_pwr']}),
         parts=[('1', 'B-013', '12V-2x6 right-angle header on CBP-8', 1), ('2', 'B-014', '12V-2x6 cable 150 mm, 16 AWG', 1),
                ('3', 'B-001', 'Card 12V-2x6 socket', '-')],
         text=['Plug the 150 mm 12V-2x6 cable (2) into the CBP-8 header (1) and into the card socket (3).',
               'Push until the latch clicks and the housing sits flat: no gap at all along the connector edge (a partly '
               'seated 12V-2x6 senses as low power or not at all).',
               'Keep the first 35 mm straight out of each connector; no side load on the housing.',
               'Check: the slot LED on the CBP-8 stays off until power-on (slot power is gated by the slot manager).'],
         tools='None (hand fit)'),
    dict(id='08', title='All 16 GPUs installed', view=dict(show=FRAME + BOARDS + CABLES + GUIDES + GPU + PWR, highlight=GPU, ghost=FRAME + CABLES, dir=FRONT,
         balloons={'1': ['C1_S01_gpu_shroud'], '2': ['C1_S08_gpu_shroud'], '3': ['C1_S09_gpu_shroud'], '4': ['C1_S16_gpu_shroud']}),
         parts=[('1-2', 'B-001', 'Lower group: slots 1-8 on CBP-8 lower', 8), ('3-4', 'B-001', 'Upper group: slots 9-16 on CBP-8 upper', 8)],
         text=['Repeat steps 6 and 7 for slots 1-16, bottom up.  Record each card serial number against its slot in the '
               'build record (the host maps slot to MCIO port).',
               'Cards stack at 50.8 mm pitch: 10.8 mm of air over each blower intake.  Nothing may sit in that gap.',
               'Check: 16 thumbscrews, 16 power cables latched, 16 MCIO plugs seated.'],
         tools='As steps 6 and 7'),
    dict(id='09', title='Hold-down bars and latches', view=dict(show=FRAME + BOARDS + GUIDES + GPU + PWR + HOLD, highlight=HOLD, red=True, ghost=FRAME,
         dir=FRONT, balloons={'1': ['C1L_holddown_bar'], '2': ['C1L_holddown_pads'], '3': ['C1L_latch'], '4': ['C1U_holddown_bar']}),
         parts=[('1', 'TS2B-207', 'Hold-down bar, hinged (lower / upper)', 2), ('2', 'TS2B-208', 'EPDM pad 3 mm (one per card)', 16),
                ('3', 'TS2B-210', 'Latch handle (red) + GN 617-6 plunger', 2), ('-', 'B-207P', 'Hinge pin 6 m6 x 40', 2)],
         text=['Stick one EPDM pad (2) inside the bar channel over every card position.',
               'Fit each bar (1) on its hinge pin and swing it closed over the card top edges.',
               'Close the red latch (3) onto the crossmember keeper until the plunger snaps in.  Each pad squeezes about '
               '1 mm: 15-25 N per card holds it in the CEM slot against 15 g shipping shock.',
               'Check: every card is touched by its pad (feeler 0.1 mm must not pass); red latches fully home.'],
         tools='None'),
    dict(id='10', title='Tracing coil, drip tray, filter and grille (inlet side)', view=dict(show=FRAME + GPU + HOLD + COOL, highlight=COOL, ghost=FRAME + GPU + HOLD,
         dir=[1.4, 0.6, 0.5], balloons={'1': ['C1_coil_fins'], '2': ['C1_coil_headers'], '3': ['C1_drip_tray'], '4': ['C1_filter_frame'], '5': ['C1_grille_2']}),
         parts=[('1', 'TS2B-220', 'Tracing coil, 3 row x 32 pass, 12 FPI', 1), ('2', 'TS2B-220', 'Coil headers 7/8 in, 4 circuits', '-'),
                ('3', 'TS2B-221', 'Drip tray + 12 mm drain spud', 1), ('4', 'B-222', 'MERV 8 filter 200 x 905 x 12', 1),
                ('5', 'TS2B-223', 'Intake grille segment (printed PETG)', 4)],
         text=['The coil sits on the inlet face of the column: room air passes the filter (4), the chilled fins (1), then '
               'into the GPU blower intakes; the crown impellers pull it out through the plenum.',
               'Before fitting: pressure test the coil with dry nitrogen at 10 bar for 30 min, no drop.',
               'Fit the drip tray (3) first, drain hose to the arm drain; then the coil on its tube sheets; connect supply '
               'and return headers (2) to the risers with 3/8 in push fittings.',
               'Supply water is held at dew point + 2 K or more (17.5 C design) by CCM-1, so the fins stay dry.  The tray '
               'and the two leak sensors are the backstop.',
               'Fit the filter (4) and clip the four grille segments (5).',
               'Check: flow at least 4 L/min per column on both meters at commissioning.'],
         tools='N2 bottle + regulator, 3/8 in tube cutter, leak spray'),
    dict(id='11', title='Side skins and light bar', view=dict(show=FRAME + GPU + HOLD + COOL + SKIN, highlight=SKIN, ghost=FRAME + GPU, dir=FRONT,
         balloons={'1': ['C1_side_skin_pos'], '2': ['C1_light_bar'], '3': ['C1_plenum_corner']}),
         parts=[('1', 'TS2B-213', 'Side skin 1.5 mm, brushed', 2), ('2', 'TS2B-212', 'Red light-bar diffuser + SK6812 strip', 1),
                ('3', 'TS2B-301', 'Plenum corner panel', 1)],
         text=['Hang the side skins (1) on M5 button heads into the post T-nuts, 3 N m.',
               'Fit the LED strip into the crossmember pocket, then the red diffuser (2): 2x M3 x 35, 0.6 N m.',
               'Close the plenum corner (3) between this column and the next.'],
         tools='Hex keys 2 / 3 mm'),
    dict(id='12', title='Arm: CRPS bank, CPD-1, straps and TEC trim module', view=dict(show=['C1_arm', 'C1_crps', 'C1_cpd1', 'C1_tec', 'C1_busbar', 'C1_host_tray'],
         highlight=['C1_cpd1', 'C1_tec', 'C1_crps'], ghost=['C1_arm', 'C1_host_tray'], dir=[0.9, -1.3, 1.1], fitTo=['C1_crps', 'C1_cpd1', 'C1_tec'],
         balloons={'1': ['^C1_crps_2$'], '2': ['^C1_cpd1$'], '3': ['C1_cpd1_strap_p12'], '4': ['C1_cpd1_strap_rtn'], '5': ['C1_tec_housing'], '6': ['C1_tec_cold']}),
         parts=[('1', 'B-030', 'Murata D1U54T-W-2000-12 CRPS 2000 W', 4), ('2', 'CPD-1', 'Column power board', 1),
                ('3', 'TS2B-232', '+12 V strap, 6 mm Cu', 1), ('4', 'TS2B-233', 'RTN strap, 6 mm Cu', 1),
                ('5', 'TS2B-601', 'TEC module housing', 1), ('6', 'TS2B-602', 'Cold block + 4 TECs + spreader', 1)],
         text=['CPD-1 (2) mounts on the arm bulkhead, receptacle face toward the nose.  Straps (3, 4) go on its 16 M6 studs: '
               'flange nut + Belleville, 6 N m, joint compound on the faces.  4/0 lugs (harness C01 / C02): M8, 12 N m.',
               'Slide the four CRPS (1) into the nose bays until they latch.  Three carry the column, one is redundant.',
               'TEC module: thermal grease (0.05 mm) both sides of each TEC, spreader on, 6x M4 crisscross in 3 passes to '
               '1.2 N m.  Coolant in/out to the G1/4 ports, PTFE tape not allowed (use bonded seals).',
               'Check: CPD-1 LED "OK" with AC on and PSON_REQ# released (PSUs stay off until CCM-1 says cooling is ready).'],
         tools='Torque wrench 5-15 N m, 10 / 13 mm sockets, grease, bonded seals'),
]


def serve(root):
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    handler = partial(SimpleHTTPRequestHandler, directory=root)
    handler.log_message = lambda *a, **k: None
    httpd = ThreadingHTTPServer(('127.0.0.1', port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, 'http://127.0.0.1:%d/' % port


def wrap(t, n):
    words, out, cur = t.split(' '), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > n:
            out.append(cur)
            cur = w
        else:
            cur = (cur + ' ' + w) if cur else w
    if cur:
        out.append(cur)
    return out


def sheet(pdf, st, img, balloons, k, n):
    fig = plt.figure(figsize=(420 / IN, 297 / IN))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 420)
    ax.set_ylim(0, 297)
    ax.axis('off')
    ax.add_patch(Rectangle((10, 10), 400, 277, fill=False, lw=0.8))
    # picture 262 x 189 mm (1800 x 1300 px)
    px0, py0, pw = 14.0, 90.0, 250.0
    ph = pw * 1300 / 1800
    im = plt.imread(img)
    ax.imshow(im, extent=(px0, px0 + pw, py0, py0 + ph), zorder=1)
    ax.add_patch(Rectangle((px0, py0), pw, ph, fill=False, lw=0.4, color='0.6'))
    # balloons: leader from the part centre to a circle offset outward
    cx, cy = px0 + pw / 2, py0 + ph / 2
    for lab, (bx, by) in sorted(balloons.items()):
        x = px0 + bx / 1800 * pw
        y = py0 + ph - by / 1300 * ph
        if not (px0 <= x <= px0 + pw and py0 <= y <= py0 + ph):
            continue
        dx, dy = x - cx, y - cy
        L = max((dx * dx + dy * dy) ** 0.5, 1e-6)
        tx, ty = x + 18 * dx / L, y + 18 * dy / L
        tx = min(max(tx, px0 + 6), px0 + pw - 6)
        ty = min(max(ty, py0 + 6), py0 + ph - 6)
        ax.plot([x, tx], [y, ty], color='#c8102e', lw=0.7, zorder=3)
        ax.plot([x], [y], 'o', color='#c8102e', ms=1.8, zorder=3)
        ax.add_patch(plt.Circle((tx, ty), 4.0, facecolor='white', edgecolor='#c8102e', lw=0.9, zorder=4))
        ax.text(tx, ty, lab, ha='center', va='center', fontsize=8, fontweight='bold', zorder=5)
    # header
    ax.text(14, 281, 'STEP %s of %d   %s' % (st['id'], n, st['title']), fontsize=13, fontweight='bold', va='top')
    ax.text(14, 274, 'TS2B-ASM-100 column build (column C1 shown; columns C2-C4 identical, rotated 90 deg).  New parts in '
                     'colour, earlier parts ghosted.', fontsize=6.5, va='top', color='0.25')
    # parts list under the picture
    y = 86.0
    ax.text(14, y, 'PARTS IN THIS STEP', fontsize=7.5, fontweight='bold', va='top')
    y -= 5
    for col, hdr in ((14, 'Item'), (26, 'Part no.'), (52, 'Description'), (180, 'Qty')):
        ax.text(col, y, hdr, fontsize=6.2, fontweight='bold', va='top')
    ax.plot([14, 200], [y - 3.2, y - 3.2], 'k-', lw=0.3)
    y -= 4.6
    for it, pn, desc, q in st['parts']:
        for col, v in ((14, it), (26, pn), (52, desc), (180, str(q))):
            ax.text(col, y, v, fontsize=6.2, va='top')
        y -= 4.0
    ax.text(14, y - 2, 'Tools: ' + st['tools'], fontsize=6.2, va='top', style='italic')
    # instructions (right column)
    x0 = 282.0
    y = 281.0
    ax.text(x0, y, 'INSTRUCTIONS', fontsize=8, fontweight='bold', va='top')
    y -= 6
    for i, t in enumerate(st['text']):
        lines = wrap(t, 64)
        for j, ln in enumerate(lines):
            ax.text(x0 + (0 if j == 0 else 4.2), y, ('%d.  ' % (i + 1) if j == 0 else '') + ln, fontsize=6.6, va='top')
            y -= 3.6
        y -= 1.8
    # title block
    tb = [('TS-2 rev B 64-GPU tower', 'Anatomy'), ('TS2B-ASM-100  Illustrated column build', 'REV A'),
          ('Sheet %d of %d   A3   not to scale' % (k, n), 'Units mm [in]'), ('Generated 2026-11-24 from mechanical/assembled/ts2b.glb', '')]
    bx, by, bw, bh = 282.0, 10.0, 128.0, 6.0
    for i, (a, b) in enumerate(tb):
        yy = by + bh * (len(tb) - 1 - i)
        ax.add_patch(Rectangle((bx, yy), bw, bh, fill=False, lw=0.5))
        ax.text(bx + 1.5, yy + bh / 2, a, fontsize=6.0 if i else 7, va='center', fontweight='bold' if i < 2 else 'normal')
        if b:
            ax.text(bx + bw - 1.5, yy + bh / 2, b, fontsize=5.6, va='center', ha='right')
    pdf.savefig(fig)
    plt.close(fig)


def main():
    json.dump([dict(id=s['id'], view=s['view']) for s in STEPS], open(os.path.join(OUT, 'steps.json'), 'w'), indent=1)
    httpd, base = serve(REPO)
    try:
        r = subprocess.run(['node', os.path.join(HERE, 'shoot.mjs'), base, OUT], cwd=HERE, timeout=1800)
    finally:
        httpd.shutdown()
    if r.returncode:
        sys.exit('render failed')
    balloons = json.load(open(os.path.join(OUT, 'balloons.json')))
    path = os.path.join(HERE, '..', 'TS2B-ASM-100_column_build.pdf')
    with PdfPages(path) as pdf:
        for k, st in enumerate(STEPS):
            sheet(pdf, st, os.path.join(OUT, 'step_%s.png' % st['id']), balloons.get(st['id'], {}), k + 1, len(STEPS))
    print('wrote', os.path.normpath(path))


if __name__ == '__main__':
    main()
