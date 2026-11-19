// Production tab: the Engineering and Manufacturing Summary (prototype-to-production brief) for investors and manufacturers.
// Reads production/production.json and the files make_brief.py renders next to it. Schema: references/production-brief.md.

export const PRODUCTION_PROMPT = `Prepare the Engineering and Manufacturing Summary for this project, following references/production-brief.md of the anatomy skill exactly.
It is the prototype-to-production brief for investors and manufacturers who never saw the design work: what the product is and the problem it solves, what has been verified versus what exists only on paper, cost per unit at 1, 100, 1,000 and 10,000 units, the design changes and tooling needed for volume, supply chain and alternates, certification and compliance, manufacturing partners, risks, staged timeline and capital, and IP notes.
Use the project's own build package, BOM, supply data, change log and test results as the base. Research current volume prices, tooling and certification costs on the web and cite them with the date read. Tag every figure measured/observed, quoted, documented, estimate or assumed; never present an estimate as a quote, never invent a market size, and say plainly if nothing has been built.
Write production/production.json, run tools/production/make_brief.py on the project until its check passes, open the PDF and look at every page, then report what is estimated or assumed and what would firm it up.`;

const TAGS = { measured: 'ok', observed: 'ok', quoted: 'q', documented: 'q', estimate: 'e', assumed: 'a' };
const CSS = `
.pb-head{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;align-items:flex-start}
.pb-head h2{margin:0 0 4px}.pb-acts{display:flex;gap:8px;flex-wrap:wrap}
.pb-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:16px 0}
.pb-kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 12px}.pb-kpi b{display:block;font-size:20px}
.pb-kpi span{font-size:12px;color:var(--muted)}
.pb-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.pb-card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px;min-width:0}
.pb-card h3{margin:0 0 8px;font-size:14px}.pb-card ul{margin:0;padding-left:18px}.pb-card li{margin:3px 0}
.pb-tag{font-size:10px;border:1px solid var(--line);border-radius:4px;padding:1px 4px;margin-left:4px;color:var(--muted);white-space:nowrap}
.pb-tag.ok{color:#3fb950;border-color:#2e6b3a}.pb-tag.q{color:#58a6ff;border-color:#1f4a7a}.pb-tag.e{color:#e3b341;border-color:#6b5317}.pb-tag.a{color:#f85149;border-color:#7a2a26}
.pb-tiers{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;align-items:end;height:170px;margin:8px 0 4px}
.pb-bar{display:flex;flex-direction:column;justify-content:flex-end;height:100%;text-align:center;font-size:12px}
.pb-bar i{display:block;background:var(--accent);border-radius:4px 4px 0 0;min-height:2px}.pb-bar b{display:block;margin-bottom:4px}
.pb-bar span{color:var(--muted);margin-top:4px}
.pb-t{width:100%;border-collapse:collapse;font-size:13px}.pb-t td,.pb-t th{padding:5px 6px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
.pb-t th{color:var(--muted);font-weight:600;font-size:12px}.pb-t .n{text-align:right;white-space:nowrap}
.pb-ok{color:#3fb950}.pb-no{color:#f85149}.pb-check{font-size:12px;margin-top:6px}
.pb-frame{width:100%;height:calc(100vh - 160px);border:0;border-radius:10px;background:#fff;margin-top:16px}
@media (max-width:1000px){.pb-grid{grid-template-columns:1fr}}
`;

const money = (x, cur = 'USD') => x == null ? '—' : (cur === 'USD' ? '$' : cur === 'EUR' ? '€' : '') + Number(x).toLocaleString('en-US', { maximumFractionDigits: Math.abs(x) < 100 ? 2 : 0 });
const rng = (lo, hi, cur) => lo == null && hi == null ? '—' : hi == null || lo === hi ? money(lo, cur) : `${money(lo, cur)}–${money(hi, cur)}`;

export async function productionTab(el, { S, esc, raw, btn, openExt, reveal }) {
  if (!document.getElementById('pb-css')) { const st = document.createElement('style'); st.id = 'pb-css'; st.textContent = CSS; document.head.append(st); }
  const find = re => S.files.filter(f => re.test(f.path)).sort((a, b) => a.path.length - b.path.length)[0];
  const pj = find(/(^|\/)production\/production\.json$/i);
  if (!pj) {
    el.innerHTML = `<div class="buildintro"><h2>Engineering and Manufacturing Summary</h2>
      <p class="lead">A report for investors and manufacturers on taking this product from prototype to mass production: what has been verified and what is still on paper, cost per unit at 1, 100, 1,000 and 10,000, design changes and tooling for volume, supply chain, certification, partners, risks, and the timeline and capital for each stage. Every figure is tagged as measured, quoted, documented, estimated or assumed, with its source. It is exported as a PDF you can send.</p>
      <p class="empty">Best done after the build package exists (Build tab). This runs Claude on the project, searches for current prices and certification costs, and can take a while.</p><div class="ib"></div></div>`;
    el.querySelector('.ib').append(btn('Prepare production brief', () => S.startRun(PRODUCTION_PROMPT), 'primary'));
    return;
  }
  const dir = pj.path.slice(0, pj.path.lastIndexOf('/') + 1);
  const P = await fetch(raw(pj.path)).then(r => r.json()).catch(e => ({ _err: e.message }));
  if (P._err) { el.innerHTML = `<div class="alert">${esc(pj.path)} could not be read: ${esc(P._err)}</div>`; return; }
  const has = n => S.files.some(f => f.path === dir + n);
  const check = has('brief-check.md') ? await fetch(raw(dir + 'brief-check.md')).then(r => r.text()).catch(() => '') : '';
  const pass = /Result: \*\*PASS\*\*/.test(check), fail = /Result: \*\*FAIL\*\*/.test(check);
  const cur = P.currency || 'USD';
  const tag = b => b ? `<span class="pb-tag ${TAGS[b] || ''}">${esc(b)}</span>` : '';
  const ex = P.executive_summary || {}, st = P.status || {}, cm = P.cost_model || {};
  const tiers = (cm.tiers || [1, 100, 1000, 10000]).map(String);
  const tot = Object.fromEntries(tiers.map(t => [t, (cm.categories || []).reduce((a, c) => a + (c.lines || []).reduce((b, l) => b + (l.unit_cost?.[t] != null ? +l.unit_cost[t] * (+l.qty_per_unit || 1) : 0), 0), 0)]));
  const mx = Math.max(...Object.values(tot), 1);
  const stages = P.stages || [];
  const clo = stages.reduce((a, s) => a + (s.capital_low || 0), 0), chi = stages.reduce((a, s) => a + (s.capital_high || 0), 0);
  const mlo = stages.reduce((a, s) => a + (s.months_low || 0), 0), mhi = stages.reduce((a, s) => a + (s.months_high || 0), 0);

  el.innerHTML = `<div class="pb-head"><div><h2>${esc(P.title || 'Engineering and Manufacturing Summary')}</h2>
      <p class="lead">${esc(ex.one_liner || '')}</p>
      <div class="empty">Engineering and Manufacturing Summary · revision ${esc(P.revision || '')} · ${esc(P.date || '')}</div>
      ${check ? `<div class="pb-check ${pass ? 'pb-ok' : 'pb-no'}">${pass ? '✓ Check passed: every figure tagged and sourced' : fail ? '✗ Check failed: see brief-check.md' : ''}</div>` : ''}</div>
    <div class="pb-acts" id="pbacts"></div></div>
    <div class="pb-kpis">${(ex.key_numbers || []).map(k => `<div class="pb-kpi"><b>${esc(k.value)}</b><span>${esc(k.label)}${tag(k.basis)}</span></div>`).join('')}</div>
    <div class="pb-grid">
      <div class="pb-card"><h3>Unit cost of goods by volume</h3>
        <div class="pb-tiers">${tiers.map(t => `<div class="pb-bar" title="${esc(money(tot[t], cur))} per unit at ${(+t).toLocaleString()} units"><b>${esc(money(tot[t], cur))}</b><i style="height:${Math.max(2, 120 * tot[t] / mx)}px"></i><span>${(+t).toLocaleString()} unit${+t > 1 ? 's' : ''}</span></div>`).join('')}</div>
        <div class="empty">Tooling and certification are one-time costs, listed in the report.</div></div>
      <div class="pb-card"><h3>Stages to production · ${esc(rng(clo, chi, cur))} over ${mlo}–${mhi} months ${tag('estimate')}</h3>
        <table class="pb-t"><tr><th>Stage</th><th class="n">Months</th><th class="n">Capital</th></tr>${stages.map(s => `<tr><td><b>${esc(s.id)}</b> ${esc(s.name)}<div class="empty">${esc(s.goal || '')}</div></td><td class="n">${esc(s.months_low)}–${esc(s.months_high)}</td><td class="n">${esc(rng(s.capital_low, s.capital_high, cur))}</td></tr>`).join('')}</table></div>
      <div class="pb-card"><h3 class="pb-ok">Verified</h3><ul>${(st.verified || []).map(v => `<li><b>${esc(v.item)}</b>${tag(v.basis)}<div class="empty">${esc(v.how || '')}</div></li>`).join('') || '<li class="empty">Nothing verified yet.</li>'}</ul></div>
      <div class="pb-card"><h3 class="pb-no">On paper only</h3><ul>${(st.on_paper || []).map(v => `<li><b>${esc(v.item)}</b> <span class="empty">· closes in ${esc(v.closes_in || '?')}</span><div class="empty">${esc(v.why || '')}</div></li>`).join('')}</ul>
        ${st.trl ? `<p class="empty" style="margin-top:8px">TRL ${esc(st.trl.level)} · MRL ${esc(st.mrl?.level || '?')}</p>` : ''}</div>
      <div class="pb-card"><h3>Certification and compliance</h3>
        <table class="pb-t"><tr><th>Standard</th><th>Required</th><th class="n">Cost</th></tr>${(P.compliance || []).map(c => `<tr><td><b>${esc(c.standard)}</b><div class="empty">${esc(c.status || '')}</div></td><td>${esc(c.required || '')}</td><td class="n">${esc(rng(c.cost_low, c.cost_high, cur))}</td></tr>`).join('')}</table></div>
      <div class="pb-card"><h3>Top risks</h3><ul>${(P.risks || []).slice(0, 6).map(r => `<li><b>${esc(r.risk)}</b> <span class="empty">· ${esc(r.likelihood || '')} / ${esc(r.impact || '')}</span><div class="empty">${esc(r.mitigation || '')}</div></li>`).join('')}</ul></div>
    </div>
    <div id="pbframe"></div>`;
  const acts = el.querySelector('#pbacts');
  if (has('production-brief.pdf')) acts.append(btn('Open PDF', () => openExt(dir + 'production-brief.pdf'), 'primary'));
  if (has('production-brief.html')) {
    let shown = false;
    const b = btn('Show full report', () => {
      shown = !shown; b.textContent = shown ? 'Hide full report' : 'Show full report';
      el.querySelector('#pbframe').innerHTML = shown ? `<iframe class="pb-frame" src="${raw(dir + 'production-brief.html')}"></iframe>` : '';
    });
    acts.append(b);
  }
  if (has('cost-model.csv')) acts.append(btn('Cost model (CSV)', () => openExt(dir + 'cost-model.csv')));
  acts.append(btn('Show in folder', () => reveal(pj.path)));
  acts.append(btn('Refresh the brief', () => { if (confirm('Run Claude again to refresh the Engineering and Manufacturing Summary with current prices and the latest design?')) S.startRun(PRODUCTION_PROMPT); }));
}
