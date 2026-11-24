// Home page hero: the shop at work. Three looping scenes drawn on one canvas:
// a laser cutting a gear, a printer building a part, and a pen drawing a bracket and a schematic.
(() => {
  const canvas = document.getElementById('shop-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const readout = document.getElementById('shop-readout');
  const progress = document.getElementById('shop-progress');
  const buttons = [...document.querySelectorAll('.machine-window .scenes button')];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const W = canvas.width, H = canvas.height, cx = W / 2, cy = H / 2;
  const MONO = '"JetBrains Mono", ui-monospace, monospace';

  function bed() {
    ctx.clearRect(0, 0, W, H);
    const g = ctx.createLinearGradient(0, 0, W, H);
    g.addColorStop(0, '#2a2c32'); g.addColorStop(1, '#212328');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = 'rgba(255,255,255,.045)'; ctx.lineWidth = 1;
    for (let x = 20; x < W; x += 20) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  }
  const glowDot = (x, y, r) => {
    ctx.save(); ctx.fillStyle = '#fff4e0'; ctx.shadowColor = '#ff8a1f'; ctx.shadowBlur = 24;
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  };

  /* Scene 1: laser cutting a gear, inner hole first */
  const gear = [];
  const teeth = 14, rO = 150, rI = 128;
  for (let i = 0; i <= 720; i++) {
    const a = i / 720 * Math.PI * 2, ph = (a * teeth / (Math.PI * 2)) % 1;
    const r = ph < .18 ? rI + (rO - rI) * ph / .18 : ph < .5 ? rO : ph < .68 ? rO - (rO - rI) * (ph - .5) / .18 : rI;
    gear.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
  }
  const hole = [];
  for (let i = 0; i <= 120; i++) { const a = i / 120 * Math.PI * 2; hole.push([cx + 34 * Math.cos(a), cy + 34 * Math.sin(a)]); }
  const cut = hole.concat(gear);
  const sparks = [];
  function drawCut(p, t) {
    bed();
    const upto = Math.min(Math.floor(p * cut.length), cut.length - 1);
    const stroke = (from, to, style, w, blur) => {
      ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      ctx.strokeStyle = style; ctx.lineWidth = w; ctx.shadowColor = '#ff8a1f'; ctx.shadowBlur = blur; ctx.beginPath();
      for (let i = from; i <= to; i++) { const q = cut[i]; if (i === from || i === hole.length) ctx.moveTo(q[0], q[1]); else ctx.lineTo(q[0], q[1]); }
      ctx.stroke(); ctx.restore();
    };
    stroke(0, upto, '#0b0b0d', 3, 0);
    stroke(Math.max(0, upto - 40), upto, 'rgba(255,170,80,.9)', 2, 14);
    if (p < 1) {
      const [hx, hy] = cut[upto];
      ctx.strokeStyle = 'rgba(255,138,31,.3)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(hx, 0); ctx.lineTo(hx, H); ctx.moveTo(0, hy); ctx.lineTo(W, hy); ctx.stroke();
      glowDot(hx, hy, 4 + Math.sin(t / 40));
      if (!reduce) for (let k = 0; k < 3; k++) sparks.push({ x: hx, y: hy, vx: (Math.random() - .5) * 3, vy: (Math.random() - .8) * 3, life: 1 });
    }
    for (let i = sparks.length - 1; i >= 0; i--) {
      const s = sparks[i]; s.x += s.vx; s.y += s.vy; s.vy += .12; s.life -= .04;
      if (s.life <= 0) { sparks.splice(i, 1); continue; }
      ctx.fillStyle = `rgba(255,${150 + 100 * s.life | 0},60,${s.life})`; ctx.fillRect(s.x, s.y, 2, 2);
    }
    return Math.round(upto / (cut.length - 1) * 388);
  }

  /* Scene 2: a vase printed layer by layer */
  const LAYERS = 48, lh = 6;
  const profile = i => { const t = i / (LAYERS - 1); return 70 + 55 * Math.sin(t * Math.PI * .9 + .3) + 20 * (1 - t); };
  function drawPrint(p, t) {
    bed();
    const prog = p * LAYERS, plateY = H - 60;
    ctx.fillStyle = '#3a3c43'; ctx.fillRect(70, plateY, W - 140, 12);
    ctx.fillStyle = 'rgba(255,138,31,.35)'; ctx.fillRect(70, plateY, W - 140, 2);
    const done = Math.floor(prog), frac = prog - done;
    for (let i = 0; i < Math.min(done, LAYERS); i++) {
      const w = profile(i) * 2, y = plateY - (i + 1) * lh, age = Math.min(1, (done - i) / 8);
      ctx.fillStyle = `rgba(255,${Math.round(150 - 70 * age)},${Math.round(60 - 30 * age)},${1 - .5 * age})`;
      ctx.fillRect(cx - w / 2, y, w, lh - 1);
    }
    let nx = cx, ny = plateY - Math.min(done, LAYERS) * lh;
    if (done < LAYERS) {
      const w = profile(done) * 2, y = plateY - (done + 1) * lh, dir = done % 2 ? -1 : 1;
      const start = cx - dir * w / 2, len = w * frac;
      ctx.save(); ctx.fillStyle = '#ffd9a8'; ctx.shadowColor = '#ff8a1f'; ctx.shadowBlur = 16;
      if (dir > 0) ctx.fillRect(start, y, len, lh - 1); else ctx.fillRect(start - len, y, len, lh - 1);
      ctx.restore();
      nx = start + dir * len; ny = y;
    }
    ctx.fillStyle = '#44464d'; ctx.fillRect(24, ny - 50, W - 48, 5);
    ctx.fillStyle = '#18191d'; ctx.strokeStyle = '#4a4c53'; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.roundRect(nx - 24, ny - 62, 48, 36, 6); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#7a7c82'; ctx.beginPath(); ctx.moveTo(nx - 7, ny - 26); ctx.lineTo(nx + 7, ny - 26); ctx.lineTo(nx, ny - 3); ctx.closePath(); ctx.fill();
    if (done < LAYERS) glowDot(nx, ny - 1, 3 + Math.sin(t / 60));
    return Math.min(LAYERS, done + (done < LAYERS ? 1 : 0));
  }

  /* Scene 3: a dimensioned bracket and an indicator-light schematic */
  const circle = (x, y, r, n = 48) => Array.from({ length: n + 1 }, (_, i) => [x + r * Math.cos(i / n * 2 * Math.PI), y + r * Math.sin(i / n * 2 * Math.PI)]);
  const zig = (x1, x2, y) => { const q = [[x1, y]], n = 6, s = (x2 - x1) / n; for (let i = 0; i < n; i++) q.push([x1 + s * (i + .5), y + (i % 2 ? 9 : -9)]); q.push([x2, y]); return q; };
  const strokes = [
    [[[50, 90], [250, 90], [250, 170], [170, 170], [170, 320], [50, 320], [50, 90]], 'part'],
    [circle(110, 140, 22), 'part'],
    [circle(110, 270, 12), 'part'],
    [[[30, 140], [270, 140]], 'center'], [[[110, 70], [110, 340]], 'center'],
    [[[50, 64], [250, 64]], 'dim', ['80.0', 136, 56]],
    [[[28, 90], [28, 320]], 'dim', ['92.0', 2, 210]],
    [[[170, 346], [250, 346]], 'dim', ['32.0', 194, 362]],
    [[[310, 182], [310, 300], [380, 300]], 'wire'],
    [[[380, 300], [416, 284]], 'wire', ['S1', 388, 278]],
    [[[420, 300], [500, 300], [500, 172]], 'wire'],
    [[[485, 140], [515, 140], [500, 166], [485, 140]], 'wire'],
    [[[485, 168], [515, 168]], 'wire', ['D1 LED', 488, 192]],
    [[[500, 140], [500, 90], [440, 90]], 'wire'],
    [zig(370, 440, 90), 'wire', ['R1 220 Ω', 372, 72]],
    [[[370, 90], [310, 90], [310, 168]], 'wire'],
    [[[290, 168], [330, 168]], 'wire'], [[[300, 182], [320, 182]], 'wire', ['12 V', 334, 180]],
  ];
  const dense = strokes.map(([pts]) => {
    const out = [pts[0]];
    for (let i = 1; i < pts.length; i++) {
      const [ax, ay] = pts[i - 1], [bx, by] = pts[i], n = Math.max(1, Math.round(Math.hypot(bx - ax, by - ay) / 4));
      for (let k = 1; k <= n; k++) out.push([ax + (bx - ax) * k / n, ay + (by - ay) * k / n]);
    }
    return out;
  });
  const TOTAL = dense.reduce((s, d) => s + d.length, 0);
  function drawDesign(p, t) {
    bed();
    ctx.strokeStyle = 'rgba(255,255,255,.1)'; ctx.beginPath(); ctx.moveTo(282, 40); ctx.lineTo(282, H - 30); ctx.stroke();
    ctx.font = `500 10px ${MONO}`; ctx.fillStyle = '#8b8880';
    ctx.fillText('MECHANICAL · BRACKET-02', 40, 32); ctx.fillText('ELECTRICAL · INDICATOR', 300, 32);
    let left = Math.floor(p * TOTAL), head = null;
    dense.forEach((pts, si) => {
      if (left <= 0) return;
      const k = Math.min(pts.length, left); left -= pts.length;
      const kind = strokes[si][1];
      ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      if (kind === 'part') { ctx.strokeStyle = '#f1efe9'; ctx.lineWidth = 2; }
      else if (kind === 'center') { ctx.strokeStyle = 'rgba(170,166,158,.6)'; ctx.lineWidth = 1; ctx.setLineDash([10, 4, 2, 4]); }
      else if (kind === 'dim') { ctx.strokeStyle = '#ff8a1f'; ctx.lineWidth = 1; }
      else { ctx.strokeStyle = '#ffb066'; ctx.lineWidth = 2; }
      ctx.beginPath(); pts.slice(0, k).forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.stroke(); ctx.restore();
      if (kind === 'dim' && k > 1) { ctx.fillStyle = '#ff8a1f'; [pts[0], pts[pts.length - 1]].forEach(q => ctx.fillRect(q[0] - 2, q[1] - 2, 4, 4)); }
      const lab = strokes[si][2];
      if (lab && k === pts.length) { ctx.font = `500 11px ${MONO}`; ctx.fillStyle = kind === 'dim' ? '#ff8a1f' : '#d8d5cd'; ctx.fillText(lab[0], lab[1], lab[2]); }
      if (k < pts.length) head = pts[k - 1];
    });
    if (head) glowDot(head[0], head[1], 3.5 + Math.sin(t / 50) * .8);
  }

  const SCENES = [
    { ms: cut.length * 8, draw: drawCut,
      text: v => `<span>Laser cutting · xTool X1</span><span>3 mm acrylic</span><span>Power <b>80%</b></span><span>Cut <b>${v}</b> mm</span>` },
    { ms: LAYERS * 150, draw: drawPrint,
      text: v => `<span>3D printing · Bambu Lab</span><span>PETG · 0.20 mm</span><span>Layer <b>${v}</b> / ${LAYERS}</span>` },
    { ms: TOTAL * 9, draw: drawDesign,
      text: () => `<span>Design · blueprints and schematics</span><span>Mechanical + electrical</span><span>Rev <b>A</b></span>` },
  ];
  const HOLD = 1400;
  let scene = 0, start = performance.now(), lastText = '';

  function render(p, t) {
    p = Math.max(0, Math.min(1, p));
    const html = SCENES[scene].text(SCENES[scene].draw(p, t));
    if (html !== lastText) { readout.innerHTML = html; lastText = html; }
    progress.style.width = (p * 100).toFixed(1) + '%';
  }
  function setScene(i) {
    scene = i; start = performance.now(); sparks.length = 0;
    buttons.forEach((b, k) => b.setAttribute('aria-pressed', String(k === i)));
    if (reduce) render(1, 0);
  }
  buttons.forEach((b, k) => b.addEventListener('click', () => setScene(k)));
  render(1, 0);
  if (reduce) return;

  let visible = true;
  if ('IntersectionObserver' in window) new IntersectionObserver(es => { visible = es[0].isIntersecting; }).observe(canvas);
  function frame(now) {
    if (visible && !document.hidden) {
      const el = now - start, s = SCENES[scene];
      if (el > s.ms + HOLD) setScene((scene + 1) % SCENES.length);
      else render(el / s.ms, now);
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
