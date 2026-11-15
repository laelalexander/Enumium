#!/usr/bin/env node
// Anatomy supply and change tool. No npm dependencies (Node 18+).
//
// Keeps every purchase line of a build package orderable:
//   - quantity audit: each line's order quantity against what the design needs (+ spares / pack rounding)
//   - stock check: live availability and price for the primary source and every alternate
//   - fit check: each alternate against the line's design requirements (in-kind vs needs a design change)
//   - supply feedback: "sold out", "price changed", "found this elsewhere" from the user or a check
//   - swap: switch a line to an in-kind alternate and carry it through build.json, purchase list, carts, bom.csv
//   - engineering change orders (ECO): open, impact scan across the project, verify nothing still uses the old part
//
// Data lives in build/1-purchase/supply.json (survives regeneration of build.json) and changes/ (CHANGELOG.md,
// changes.json, ECO-nnn.md). See references/supply-and-change.md of the anatomy skill.
//
// CLI:  node supply.js <projectDir> <command> [args]
//   status                          one line per purchase line: stock, alternates, fit
//   audit                           quantity audit -> build/1-purchase/qty-audit.md (exit 1 on a short line)
//   refresh [LINE ...]              check stock and price of primaries and alternates (all lines by default)
//   evaluate                        recompute fit of every alternate against its line's requirements
//   feedback LINE TARGET STATUS [PRICE] [NOTE...]   TARGET = primary | alternate id; STATUS = sold_out|in_stock|backorder|discontinued|price
//   candidate LINE URL [NOTE...]    add a source the user found (fit 'unverified' until its specs are filled in)
//   swap LINE ALT_ID [REASON...]    make an in-kind alternate the primary (add --force for a non-in-kind one after an ECO)
//   impact TERM [TERM ...]          files in the project that mention the terms, grouped by area
//   eco-open LINE ALT_ID|- TITLE... scaffold changes/ECO-nnn.md with the impact list
//   eco-verify ECO-nnn              fail if any non-history file still uses the old part; on pass close the ECO and bump the revision
'use strict';

const fs = require('fs');
const path = require('path');

const SUPPLY_REL = 'build/1-purchase/supply.json';
const SKIP_DIRS = new Set(['.anatomy', '.git', 'node_modules', '.venv', 'venv', 'env', '__pycache__', '.pio', '.mypy_cache', '.pytest_cache', '.claude', 'vendor']);
const TEXT_EXT = new Set(['.md', '.csv', '.json', '.py', '.scad', '.txt', '.html', '.htm', '.js', '.mjs', '.ts', '.kicad_sch', '.kicad_pcb', '.kicad_pro',
  '.xml', '.yaml', '.yml', '.ini', '.toml', '.c', '.cpp', '.h', '.hpp', '.ino', '.svg', '.tsv', '.cfg', '.net']);

// ---------------------------------------------------------------- files
const readJson = f => JSON.parse(fs.readFileSync(f, 'utf8').replace(/^﻿/, ''));
const writeJson = (f, j) => { fs.mkdirSync(path.dirname(f), { recursive: true }); fs.writeFileSync(f, JSON.stringify(j, null, 2) + '\n'); };
const today = () => new Date().toISOString().slice(0, 10);

function walk(dir, out = [], base = dir, depth = 0) {
  if (depth > 10) return out;
  let ents = []; try { ents = fs.readdirSync(dir, { withFileTypes: true }); } catch { return out; }
  for (const e of ents) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (!SKIP_DIRS.has(e.name)) walk(p, out, base, depth + 1); }
    else out.push(path.relative(base, p).split(path.sep).join('/'));
  }
  return out;
}

function findBuild(dir) {
  const direct = path.join(dir, 'build', 'build.json');
  if (fs.existsSync(direct)) return 'build/build.json';
  const hits = walk(dir).filter(f => /(^|\/)build\/build\.json$/.test(f)).sort((a, b) => a.length - b.length);
  return hits[0] || null;
}
function buildRoot(rel) { return rel ? path.posix.dirname(path.posix.dirname(rel)) : '.'; } // folder that holds build/

function load(dir) {
  const rel = findBuild(dir);
  if (!rel) throw new Error('no build/build.json in this project');
  const build = readJson(path.join(dir, rel));
  const root = buildRoot(rel);
  const supplyRel = path.posix.join(root, SUPPLY_REL);
  const sf = path.join(dir, supplyRel);
  const supply = fs.existsSync(sf) ? readJson(sf) : { version: 1, lines: {}, feedback: [] };
  supply.lines = supply.lines || {}; supply.feedback = supply.feedback || [];
  return { dir, rel, root, build, supply, supplyRel };
}
function saveSupply(ctx) { ctx.supply.updated = new Date().toISOString(); writeJson(path.join(ctx.dir, ctx.supplyRel), ctx.supply); }
function saveBuild(ctx) { writeJson(path.join(ctx.dir, ctx.rel), ctx.build); }

// ---------------------------------------------------------------- CSV
function parseCsv(text) {
  const rows = []; let row = [], f = '', q = false;
  text = text.replace(/^﻿/, '');
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"') q = true;
    else if (c === ',') { row.push(f); f = ''; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; row.push(f); rows.push(row); row = []; f = ''; }
    else f += c;
  }
  if (f !== '' || row.length) { row.push(f); rows.push(row); }
  return rows.filter(r => r.length > 1 || r[0] !== '');
}
const csvCell = v => { const s = v == null ? '' : String(v); return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
const toCsv = rows => rows.map(r => r.map(csvCell).join(',')).join('\n') + '\n';
function readCsv(f) { try { return parseCsv(fs.readFileSync(f, 'utf8')); } catch { return null; } }

// ---------------------------------------------------------------- quantity audit
const SPARE_WORDS = /spare|pack|roll|spool|sheet|reel|bag|box|smallest|minimum|moq|cut |cut$|length|lot|strip|tube|bottle|kit|round(ed)? up|as sold|\bof \d+|x \d+ ?m\b/i;
function numberFrom(s) { const m = String(s ?? '').match(/-?\d+(\.\d+)?/); return m ? parseFloat(m[0]) : null; }
function safeExpr(expr) { // "17*6", "(17*6)+4"
  if (!/^[\d\s.+\-*/()]+$/.test(String(expr))) return null;
  try { return Function('"use strict";return (' + expr + ')')(); } catch { return null; }
}
function neededFor(ctx, p, plRow) {
  const s = ctx.supply.lines[p.line] || {};
  if (s.need && s.need.qty != null) return { needed: +s.need.qty, basis: s.need.basis || 'supply.json', expr: s.need.expr, spares: s.need.spares, per_unit: s.need.per_unit, unit: s.need.unit || '' };
  if (plRow && plRow.needed_qty !== undefined && plRow.needed_qty !== '') return { needed: numberFrom(plRow.needed_qty), basis: s.need && s.need.basis || 'purchase-list.csv needed_qty', per_unit: s.need && s.need.per_unit, unit: s.need && s.need.unit || '' };
  const m = String(p.notes || '').match(/needed in the (?:pack|build|product|unit|assembly)[^:]*:\s*([\d.]+)/i);
  if (m) return { needed: parseFloat(m[1]), basis: 'notes', per_unit: s.need && s.need.per_unit, unit: s.need && s.need.unit || '' };
  if (p.needed != null) return { needed: +p.needed, basis: 'build.json needed' };
  return { needed: null, basis: '' };
}
function purchaseListRows(ctx) {
  const rows = readCsv(path.join(ctx.dir, ctx.root, 'build/1-purchase/purchase-list.csv'));
  if (!rows || !rows.length) return {};
  const h = rows[0]; const out = {};
  for (const r of rows.slice(1)) { const o = {}; h.forEach((k, i) => o[k] = r[i]); if (o.line) out[o.line] = o; }
  return out;
}
function audit(ctx) {
  const pl = purchaseListRows(ctx);
  const rows = [];
  for (const p of ctx.build.purchase || []) {
    const n = neededFor(ctx, p, pl[p.line]);
    const qty = +p.qty;
    const why = [p.notes, pl[p.line] && pl[p.line].pack_note].filter(Boolean).join('; ');
    let verdict = 'OK', reason = '';
    if (n.expr != null) {
      const v = safeExpr(n.expr);
      if (v == null || Math.abs(v - n.needed) > 1e-9) { verdict = 'FAIL'; reason = `the design count ${n.expr} = ${v} does not match the needed quantity ${n.needed}`; }
    }
    if (verdict === 'OK') {
      if (n.needed != null && n.per_unit) { // sold by the spool, roll, sheet or length: compare the amount, not the count
        const cap = qty * n.per_unit;
        if (cap + 1e-9 < n.needed) { verdict = 'FAIL'; reason = `${qty} x ${n.per_unit} ${n.unit} = ${cap} ${n.unit}, the design needs ${n.needed} ${n.unit}`; }
        else reason = `${qty} x ${n.per_unit} ${n.unit} = ${+cap.toFixed(3)} ${n.unit} for ${n.needed} ${n.unit} needed`;
      }
      else if (n.needed == null) { verdict = 'CHECK'; reason = 'no needed quantity recorded (add need.qty in supply.json, or needed_qty in purchase-list.csv)'; }
      else if (!Number.isFinite(qty) || qty <= 0) { verdict = 'FAIL'; reason = 'order quantity missing'; }
      else if (Number.isInteger(n.needed) && qty < n.needed && !SPARE_WORDS.test(why)) { verdict = 'FAIL'; reason = `orders ${qty}, the design needs ${n.needed}`; }
      else if (Number.isInteger(n.needed) && qty < n.needed) { verdict = 'CHECK'; reason = `orders ${qty} for ${n.needed} needed; the note says it is sold in packs or lengths, confirm the pack size covers it`; }
      else if (Number.isInteger(n.needed) && qty > n.needed) {
        const extra = qty - n.needed, small = Math.max(2, Math.ceil(0.1 * n.needed));
        if (extra <= small) reason = `${n.needed} + ${extra} spare`;
        else if (SPARE_WORDS.test(why)) reason = `${n.needed} needed; ${qty} because: ${why.split(';')[0].trim()}`;
        else { verdict = 'CHECK'; reason = `orders ${qty} for ${n.needed} needed with no reason given for the extra ${extra}`; }
      } else reason = Number.isInteger(n.needed) ? 'exact' : `${n.needed} (length/weight) covered by ${qty} as sold`;
    }
    rows.push({ line: p.line, desc: p.desc, qty, needed: n.needed, basis: n.basis, expr: n.expr || '', verdict, reason });
  }
  const md = ['# Quantity audit', '', `Checked ${new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC by tools/supply/supply.js against the design's needed quantities.`, '',
    `${rows.filter(r => r.verdict === 'OK').length} OK · ${rows.filter(r => r.verdict === 'CHECK').length} to check · ${rows.filter(r => r.verdict === 'FAIL').length} wrong`, '',
    '| Line | Part | Order qty | Needed | Design basis | Result | Why |', '|---|---|---|---|---|---|---|',
    ...rows.map(r => `| ${r.line} | ${String(r.desc || '').replace(/\|/g, '/')} | ${r.qty} | ${r.needed ?? '?'} | ${(r.expr ? r.expr + ' — ' : '') + String((ctx.supply.lines[r.line] || {}).need?.basis || r.basis).replace(/\|/g, '/')} | ${r.verdict} | ${String(r.reason).replace(/\|/g, '/')} |`)];
  fs.mkdirSync(path.join(ctx.dir, ctx.root, 'build/1-purchase'), { recursive: true });
  fs.writeFileSync(path.join(ctx.dir, ctx.root, 'build/1-purchase/qty-audit.md'), md.join('\n') + '\n');
  return rows;
}

// ---------------------------------------------------------------- stock check
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 AnatomyStockCheck/1.0';
async function get(url, ms = 15000) {
  const ac = new AbortController(); const t = setTimeout(() => ac.abort(), ms);
  try { return await fetch(url, { headers: { 'User-Agent': UA, Accept: 'text/html,application/json;q=0.9,*/*;q=0.8' }, signal: ac.signal, redirect: 'follow' }); }
  finally { clearTimeout(t); }
}
function availFromSchema(s) {
  s = String(s || '').toLowerCase();
  if (/instock|in_stock|limitedavailability|onlineonly/.test(s)) return 'in_stock';
  if (/outofstock|out_of_stock|soldout|sold_out/.test(s)) return 'sold_out';
  if (/backorder|preorder|presale/.test(s)) return 'backorder';
  if (/discontinued/.test(s)) return 'discontinued';
  return null;
}
function fromHtml(html) {
  const r = { status: null, price: null, via: '' };
  for (const m of html.matchAll(/<script[^>]+application\/ld\+json[^>]*>([\s\S]*?)<\/script>/gi)) {
    let j; try { j = JSON.parse(m[1].trim()); } catch { continue; }
    const stack = [j];
    while (stack.length) {
      const o = stack.pop(); if (!o || typeof o !== 'object') continue;
      if (Array.isArray(o)) { stack.push(...o); continue; }
      if (o.availability && !r.status) { r.status = availFromSchema(o.availability); r.via = 'schema.org offer'; }
      if ((o.price || o.lowPrice) && r.price == null) { const v = parseFloat(o.price || o.lowPrice); if (Number.isFinite(v)) r.price = v; }
      for (const k of ['offers', '@graph', 'hasVariant', 'mainEntity']) if (o[k]) stack.push(o[k]);
    }
  }
  if (!r.status) {
    const m = html.match(/itemprop=["']availability["'][^>]*(?:href|content)=["']([^"']+)/i) || html.match(/property=["']product:availability["'][^>]*content=["']([^"']+)/i);
    if (m) { r.status = availFromSchema(m[1]) || (/in ?stock/i.test(m[1]) ? 'in_stock' : /out/i.test(m[1]) ? 'sold_out' : null); r.via = 'page metadata'; }
  }
  if (r.price == null) { const m = html.match(/(?:itemprop=["']price["']|property=["']product:price:amount["'])[^>]*content=["']([\d.,]+)/i); if (m) r.price = parseFloat(m[1].replace(/,/g, '')); }
  if (!r.status) {
    const text = html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/gi, ' ').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');
    if (/expected to ship|back[- ]?order|pre-?order/i.test(text)) r.status = 'backorder';
    else if (/\b(sold out|out of stock|currently unavailable|no longer available|discontinued)\b/i.test(text)) r.status = /discontinued|no longer available/i.test(text) ? 'discontinued' : 'sold_out';
    else if (/\b(in stock|add to cart|add to basket)\b/i.test(text)) r.status = 'in_stock';
    if (r.status) r.via = 'page text';
  }
  return r;
}
async function checkUrl(url) {
  const checked = new Date().toISOString();
  if (!url || !/^https?:\/\//i.test(url)) return { status: 'unknown', checked, via: 'no link' };
  try {
    const u = new URL(url);
    if (u.pathname === '/' || u.pathname === '') return { status: 'unknown', checked, via: 'link is the shop, not the product page', final: true };
    const m =u.pathname.match(/^(.*\/products\/[^/]+?)\/?$/);
    if (m) { // Shopify stores publish the product as JSON at <product>.js
      try {
        const r = await get(u.origin + m[1] + '.js');
        if (r.ok && /json|javascript/.test(r.headers.get('content-type') || '')) {
          const j = await r.json();
          const vid = u.searchParams.get('variant');
          const v = (j.variants || []).find(x => String(x.id) === vid) || (j.variants || []).find(x => x.available) || (j.variants || [])[0] || {};
          const vs = j.variants || [];
          if (!vid && vs.length > 1 && vs.some(x => x.available) && vs.some(x => !x.available)) // some options in stock, some not: which one the design needs is unknown
            return { status: 'unknown', checked, via: `${vs.filter(x => x.available).length} of ${vs.length} options in stock; link the exact option (?variant=) to check it`, final: true };
          const avail = vid ? !!v.available : !!j.available;
          return { status: avail ? 'in_stock' : 'sold_out', price: (v.price ?? j.price) != null ? (v.price ?? j.price) / 100 : null, checked, via: 'store product data' };
        }
      } catch {}
    }
    const r = await get(url);
    if ([401, 403, 429, 503].includes(r.status)) return { status: 'unknown', checked, via: `site refused an automated check (HTTP ${r.status}); open the link` };
    if (r.status === 404 || r.status === 410) return { status: 'discontinued', checked, via: `page gone (HTTP ${r.status})` };
    if (!r.ok) return { status: 'unknown', checked, via: `HTTP ${r.status}` };
    const x = fromHtml(await r.text());
    return { status: x.status || 'unknown', price: x.price, checked, via: x.via || 'no stock signal on the page; open the link' };
  } catch (e) {
    return { status: 'unknown', checked, via: e.name === 'AbortError' ? 'timed out' : String((e.cause && (e.cause.code || e.cause.message)) || e.message || e).slice(0, 120) };
  }
}
async function pool(items, n, fn) { const out = []; let i = 0; await Promise.all(Array.from({ length: Math.min(n, items.length) }, async () => { while (i < items.length) { const k = i++; out[k] = await fn(items[k]); } })); return out; }

function entry(ctx, line) {
  const p = (ctx.build.purchase || []).find(x => x.line === line);
  const s = ctx.supply.lines[line] = ctx.supply.lines[line] || {};
  s.alternates = s.alternates || []; s.requirements = s.requirements || [];
  return { p, s };
}

async function refresh(ctx, lines) {
  const want = lines && lines.length ? new Set(lines) : null;
  const jobs = [];
  for (const p of ctx.build.purchase || []) {
    if (want && !want.has(p.line)) continue;
    const { s } = entry(ctx, p.line);
    s.primary = s.primary || {};
    jobs.push({ tgt: s.primary, url: p.url, keep: s.primary.stock });
    for (const a of s.alternates) if (a.url) jobs.push({ tgt: a, url: a.url, keep: a.stock });
  }
  await pool(jobs, 6, async j => {
    const r = await checkUrl(j.url);
    // A failed or blocked check says nothing new: keep the last known status (a user report, an earlier check)
    // and note that the re-check did not get through.
    if (r.status === 'unknown' && !r.final && j.keep && j.keep.status && j.keep.status !== 'unknown') j.tgt.stock = { ...j.keep, recheck: r.via, rechecked: r.checked };
    else j.tgt.stock = r;
  });
  evaluate(ctx);
  saveSupply(ctx);
  return summary(ctx);
}

// ---------------------------------------------------------------- fit
function fitOf(alt, reqs) {
  const out = []; let unknown = 0, fail = 0;
  for (const q of reqs || []) {
    const v = (alt.specs || {})[q.key];
    let ok = null;
    if (v === undefined || v === null || v === '') { unknown++; }
    else if (q.eq !== undefined) ok = String(v).toLowerCase() === String(q.eq).toLowerCase();
    else { const n = +v; ok = Number.isFinite(n) && (q.min === undefined || n >= q.min) && (q.max === undefined || n <= q.max); }
    if (ok === false) fail++;
    out.push({ key: q.key, value: v ?? null, min: q.min, max: q.max, eq: q.eq, ok, why: q.why || '' });
  }
  const sameMpn = alt.same_part === true;
  const fit = fail ? 'needs-change' : unknown && !sameMpn ? 'unverified' : 'in-kind';
  return { fit, checks: out };
}
function evaluate(ctx) {
  for (const [line, s] of Object.entries(ctx.supply.lines)) {
    const p = (ctx.build.purchase || []).find(x => x.line === line);
    const base = p && +p.unit_price;
    for (const a of s.alternates || []) {
      const f = fitOf(a, s.requirements); a.fit = f.fit; a.checks = f.checks;
      const ap = +((a.stock && a.stock.price) ?? a.unit_price);
      // Cost against the line's current price, so a dearer drop-in is never offered as if it were free.
      if (base > 0 && ap > 0) { a.price_delta_pct = Math.round(100 * (ap - base) / base); a.extra_cost = Math.round((ap - base) * (+p.qty || 0) * 100) / 100; }
      else { delete a.price_delta_pct; delete a.extra_cost; }
    }
    s.state = lineState(ctx, line);
  }
}
function lineState(ctx, line) {
  const s = ctx.supply.lines[line] || {}; const ps = s.primary && s.primary.stock && s.primary.stock.status;
  const alts = s.alternates || [];
  if (ps === 'in_stock') return 'ok';
  // "In stock" counts as confirmed only if the latest live check got through; a status kept from an earlier
  // check (the re-check was refused or failed) has to be confirmed on the page before anyone relies on it.
  const inKindIn = alts.filter(a => a.fit === 'in-kind' && a.stock && a.stock.status === 'in_stock');
  if (inKindIn.some(a => !a.stock.recheck)) return 'swap-ready';
  if (inKindIn.length) return 'swap-to-confirm';
  if (alts.some(a => a.fit === 'in-kind' && a.stock && a.stock.status === 'backorder') || ps === 'backorder') return 'backorder';
  if (alts.some(a => a.fit === 'needs-change' && a.stock && a.stock.status === 'in_stock')) return 'redesign-option';
  if (ps === 'sold_out' || ps === 'discontinued') return 'no-source';
  return 'unknown';
}
function summary(ctx) {
  const out = [];
  for (const p of ctx.build.purchase || []) {
    const s = ctx.supply.lines[p.line] || {}; const st = s.primary && s.primary.stock || {};
    out.push({ line: p.line, desc: p.desc, supplier: p.supplier, status: st.status || 'unchecked', price: st.price, state: s.state || 'unknown',
      alternates: (s.alternates || []).map(a => ({ id: a.id, supplier: a.supplier, mpn: a.mpn, fit: a.fit, status: a.stock && a.stock.status, price: (a.stock && a.stock.price) ?? a.unit_price })) });
  }
  return out;
}

// ---------------------------------------------------------------- feedback / candidates
function feedback(ctx, line, target, status, price, note, by = 'user') {
  const { p, s } = entry(ctx, line);
  if (!p) throw new Error(`no purchase line ${line}`);
  const st = { status, checked: new Date().toISOString(), via: `${by} report${note ? ': ' + note : ''}` };
  if (price != null && price !== '' && Number.isFinite(+price)) st.price = +price;
  if (target === 'primary') { s.primary = s.primary || {}; s.primary.stock = { ...(s.primary.stock || {}), ...st, recheck: undefined, rechecked: undefined }; }
  else { const a = s.alternates.find(x => x.id === target); if (!a) throw new Error(`no alternate ${target} on ${line}`); a.stock = { ...(a.stock || {}), ...st, recheck: undefined, rechecked: undefined }; }
  ctx.supply.feedback.push({ when: st.checked, line, target, status, price: st.price, note: note || '', by });
  evaluate(ctx); saveSupply(ctx);
  const alts = (s.alternates || []).filter(a => a.id !== target);
  return { state: s.state, inKind: alts.filter(a => a.fit === 'in-kind' && (!a.stock || a.stock.status !== 'sold_out')).map(a => a.id),
    needsChange: alts.filter(a => a.fit === 'needs-change').map(a => a.id) };
}
async function candidate(ctx, line, url, note) {
  const { p, s } = entry(ctx, line);
  if (!p) throw new Error(`no purchase line ${line}`);
  let host = ''; try { host = new URL(url).hostname.replace(/^www\./, ''); } catch { throw new Error('not a link'); }
  const id = `${line}-U${s.alternates.filter(a => /-U\d+$/.test(a.id)).length + 1}`;
  const a = { id, supplier: host, url, mfr: '', mpn: '', unit_price: null, specs: {}, notes: note || '', source: 'user', added: today() };
  s.alternates.push(a);
  a.stock = await checkUrl(url);
  if (a.stock.price != null) a.unit_price = a.stock.price;
  ctx.supply.feedback.push({ when: new Date().toISOString(), line, target: id, status: 'candidate', note: note || url, by: 'user' });
  evaluate(ctx); saveSupply(ctx);
  return a;
}

// ---------------------------------------------------------------- change log and revision
function changesDir(ctx) { return path.join(ctx.dir, ctx.root, 'changes'); }
function readChanges(ctx) { try { return readJson(path.join(changesDir(ctx), 'changes.json')); } catch { return { revision: ctx.build.revision || 'A', changes: [] }; } }
function nextRev(r) {
  r = String(r || 'A');
  const m = r.match(/^([A-Z]+)$/); if (!m) return r + '+1';
  let s = m[1].split(''), i = s.length - 1;
  while (i >= 0) { if (s[i] === 'Z') { s[i] = 'A'; i--; } else { s[i] = String.fromCharCode(s[i].charCodeAt(0) + 1); return s.join(''); } }
  return 'A' + s.join('');
}
function logChange(ctx, ch, bump) {
  const C = readChanges(ctx);
  if (bump) { C.revision = nextRev(C.revision || ctx.build.revision || 'A'); ctx.build.revision = C.revision; }
  ch.revision = C.revision; ch.when = ch.when || new Date().toISOString();
  C.changes.push(ch);
  writeJson(path.join(changesDir(ctx), 'changes.json'), C);
  const md = ['# Change log', '', `Current revision: **${C.revision}**`, '',
    '| When | Rev | Id | Kind | Line | Change | Why | Files |', '|---|---|---|---|---|---|---|---|',
    ...C.changes.slice().reverse().map(c => `| ${c.when.slice(0, 10)} | ${c.revision} | ${c.id} | ${c.kind} | ${c.line || ''} | ${String(c.summary || '').replace(/\|/g, '/')} | ${String(c.reason || '').replace(/\|/g, '/')} | ${(c.files || []).length} |`)];
  fs.writeFileSync(path.join(changesDir(ctx), 'CHANGELOG.md'), md.join('\n') + '\n');
  return ch;
}

// ---------------------------------------------------------------- swap
const CARTS = [
  { key: /digi-?key/i, file: 'digikey-cart.csv' }, { key: /mouser/i, file: 'mouser-cart.csv' }, { key: /lcsc/i, file: 'lcsc-cart.csv' },
  { key: /mcmaster/i, file: 'mcmaster-cart.csv' }, { key: /newark|farnell/i, file: 'newark-cart.csv' },
];
const cartFor = supplier => (CARTS.find(c => c.key.test(supplier || '')) || { file: 'other-suppliers.csv' }).file;
function refCol(h) { return h.findIndex(x => /^(line|customer (part number|reference)|customer part number|line note)$/i.test(x.trim())); }
function setCol(h, row, re, v) { const i = h.findIndex(x => re.test(x.trim())); if (i >= 0) row[i] = v; }
function moveInCarts(ctx, p, old) {
  const dir = path.join(ctx.dir, ctx.root, 'build/1-purchase'); const touched = [];
  for (const f of new Set([cartFor(old.supplier), 'other-suppliers.csv'])) { // drop the line from where it was
    const rows = readCsv(path.join(dir, f)); if (!rows) continue;
    const rc = refCol(rows[0]); if (rc < 0) continue;
    const kept = rows.filter((r, i) => i === 0 || r[rc] !== p.line);
    if (kept.length !== rows.length) { fs.writeFileSync(path.join(dir, f), toCsv(kept)); touched.push(f); }
  }
  const f = cartFor(p.supplier); const fp = path.join(dir, f);
  let rows = readCsv(fp);
  if (!rows) rows = [f === 'other-suppliers.csv' ? ['Supplier', 'Line', 'Quantity', 'Part', 'Description', 'Unit price USD', 'Link', 'Note'] : ['Quantity', 'Mfr Part Number', 'Customer Reference', 'Description']];
  const h = rows[0]; const r = h.map(() => '');
  setCol(h, r, /^supplier$/i, p.supplier); setCol(h, r, /^(line|customer (part number|reference)|customer part number|line note)$/i, p.line);
  setCol(h, r, /^quantity/i, p.qty); setCol(h, r, /^(part|mfr part number|manufacture part number)$/i, p.mpn);
  setCol(h, r, /^manufacturer$/i, p.mfr); setCol(h, r, /^description$/i, p.desc); setCol(h, r, /^unit price/i, p.unit_price);
  setCol(h, r, /^link$/i, p.url); setCol(h, r, /^note$/i, `switched from ${old.supplier} ${old.mpn}`);
  if (f === 'mcmaster-cart.csv') setCol(h, r, /^part number$/i, p.supplier_pn || p.mpn);
  if (/digikey|mouser|newark/.test(f)) setCol(h, r, /^(part number|mouser part number|newark part number)$/i, p.supplier_pn || '');
  rows.push(r); fs.writeFileSync(fp, toCsv(rows)); touched.push(f);
  return touched.map(x => path.posix.join(ctx.root, 'build/1-purchase', x));
}
function updatePurchaseList(ctx, p) {
  const f = path.join(ctx.dir, ctx.root, 'build/1-purchase/purchase-list.csv'); const rows = readCsv(f); if (!rows) return null;
  const h = rows[0]; const i = rows.findIndex((r, k) => k > 0 && r[h.indexOf('line')] === p.line); if (i < 0) return null;
  const r = rows[i];
  setCol(h, r, /^manufacturer$/i, p.mfr); setCol(h, r, /^part_number_or_standard$/i, p.mpn); setCol(h, r, /^supplier$/i, p.supplier);
  setCol(h, r, /^link$/i, p.url); setCol(h, r, /^unit_price_usd$/i, p.unit_price);
  setCol(h, r, /^line_total_usd$/i, (+p.qty * +p.unit_price).toFixed(2)); setCol(h, r, /^alternative$/i, p.alt); setCol(h, r, /^price_checked$/i, `${today()}: ${p.price_note || 'switched by supply tool'}`);
  fs.writeFileSync(f, toCsv(rows));
  return path.posix.join(ctx.root, 'build/1-purchase/purchase-list.csv');
}
function updateBomCsv(ctx, p) { // the design's source BOM, so a regenerated build.json keeps the swap
  const hits = walk(path.join(ctx.dir, ctx.root)).filter(f => /(^|\/)bom\.csv$/i.test(f)); const done = [];
  for (const rel of hits) {
    const f = path.join(ctx.dir, ctx.root, rel); const rows = readCsv(f); if (!rows) continue;
    const h = rows[0]; const li = h.indexOf('line'); if (li < 0) continue;
    const r = rows.find((x, k) => k > 0 && x[li] === p.line); if (!r) continue;
    setCol(h, r, /^manufacturer$/i, p.mfr); setCol(h, r, /^mpn_or_standard$/i, p.mpn); setCol(h, r, /^supplier$/i, p.supplier);
    setCol(h, r, /^supplier_url$/i, p.url); setCol(h, r, /^unit_price$/i, p.unit_price); setCol(h, r, /^price_date$/i, today()); setCol(h, r, /^alt_mpn$/i, p.alt);
    fs.writeFileSync(f, toCsv(rows)); done.push(path.posix.join(ctx.root, rel));
  }
  return done;
}
function recomputeTotals(ctx) {
  const t = ctx.build.totals = ctx.build.totals || {};
  t.parts_cost = Math.round((ctx.build.purchase || []).reduce((a, p) => a + (+p.qty || 0) * (+p.unit_price || 0), 0) * 100) / 100;
}
function swap(ctx, line, altId, reason, force) {
  const { p, s } = entry(ctx, line);
  if (!p) throw new Error(`no purchase line ${line}`);
  const a = s.alternates.find(x => x.id === altId); if (!a) throw new Error(`no alternate ${altId} on ${line}`);
  if ((a.mpn || '') === (p.mpn || '') && (a.supplier || '') === (p.supplier || '') && (a.url || '') === (p.url || ''))
    throw new Error(`${line} already uses ${a.supplier} ${a.mpn}: the BOM was regenerated before the swap, so the previous source is no longer on the line. Run swap before regenerating the BOM, or restore the line first.`);
  evaluate(ctx);
  if (a.fit !== 'in-kind' && !force) throw new Error(`${altId} is ${a.fit}: it is not a drop-in. Use an engineering change (eco-open) for it, then swap with --force once the design is updated.`);
  const old = { supplier: p.supplier, url: p.url, mfr: p.mfr, mpn: p.mpn, unit_price: p.unit_price, stock: s.primary && s.primary.stock, specs: s.primary && s.primary.specs };
  const samePart = (a.mpn || p.mpn) === p.mpn;
  // The old primary becomes an alternate so it can come back when it is in stock again.
  s.alternates = s.alternates.filter(x => x.id !== altId);
  s.alternates.unshift({ id: `${line}-was-${(old.supplier || 'old').replace(/[^a-z0-9]+/gi, '').slice(0, 16)}`, supplier: old.supplier, url: old.url, mfr: old.mfr, mpn: old.mpn,
    unit_price: old.unit_price, specs: old.specs || (samePart ? a.specs : {}), same_part: samePart || undefined, stock: old.stock, notes: `previous primary, replaced ${today()}` });
  Object.assign(p, { supplier: a.supplier, url: a.url, mfr: a.mfr || p.mfr, mpn: a.mpn || p.mpn, unit_price: a.unit_price ?? (a.stock && a.stock.price) ?? p.unit_price, supplier_pn: a.supplier_pn });
  if (!p.supplier_pn) delete p.supplier_pn;
  p.alt = `was ${old.supplier} ${old.mpn}` + (p.alt ? `; ${p.alt}` : '');
  p.price_note = `${a.stock && a.stock.status || 'stock unknown'} on ${(a.stock && a.stock.checked || '').slice(0, 10) || today()}`;
  s.primary = { stock: a.stock, specs: a.specs };
  recomputeTotals(ctx);
  const files = [ctx.rel, ctx.supplyRel, ...moveInCarts(ctx, p, old)];
  const pl = updatePurchaseList(ctx, p); if (pl) files.push(pl);
  files.push(...updateBomCsv(ctx, p));
  const C = readChanges(ctx);
  const ch = logChange(ctx, { id: `SUP-${String(C.changes.filter(c => c.kind === 'supplier' || c.kind === 'part').length + 1).padStart(3, '0')}`, kind: samePart ? 'supplier' : 'part', line,
    summary: samePart ? `${p.mpn}: ${old.supplier} -> ${p.supplier} ($${old.unit_price} -> $${p.unit_price})` : `${old.mpn} (${old.supplier}) -> ${p.mpn} (${p.supplier}), in-kind`,
    reason: reason || 'primary source unavailable', files: [...new Set(files)] }, !samePart);
  evaluate(ctx); saveBuild(ctx); saveSupply(ctx);
  return ch;
}

// ---------------------------------------------------------------- impact and ECO
const AREAS = [
  ['BOM and purchasing', /(^|\/)(bom|1-purchase)\/|bom|cart|purchase|order/i], ['PCB and PCBA', /kicad|pcba|gerber|\.kicad_|\/pcb\//i],
  ['Firmware and software', /firmware|software|src\/|\.ino$|\.c$|\.cpp$|\.h$|platformio/i], ['3D printing and G-code', /print\/|gcode|slice|\.3mf/i],
  ['CAD and 3D twin', /cad\/|step\/|stl\/|assembl|parts\.json|viewer|twin|mechanical/i], ['Drawings', /drawing/i],
  ['Assembly guide and build package', /4-assemble|guide|instructions|build\.json|README/i], ['Simulation and tests', /sim\/|test/i],
  ['Calculations and design notes', /calc|thermal|electrical|design-basis|nonfunctional|budget/i],
];
function areaOf(f) { const a = AREAS.find(([, re]) => re.test(f)); return a ? a[0] : 'Other documents'; }
function impact(ctx, terms, opts = {}) {
  terms = terms.filter(Boolean); if (!terms.length) return [];
  const res = [];
  for (const f of walk(ctx.dir)) {
    if (!TEXT_EXT.has(path.extname(f).toLowerCase())) continue;
    if (opts.skipHistory && (/(^|\/)changes\//.test(f) || f.endsWith('supply.json') || /qty-audit\.md$/.test(f))) continue;
    let t; try { const st = fs.statSync(path.join(ctx.dir, f)); if (st.size > 5e6) continue; t = fs.readFileSync(path.join(ctx.dir, f), 'utf8'); } catch { continue; }
    const lines = t.split(/\r?\n/); const hits = [];
    lines.forEach((l, i) => { if (terms.some(x => l.includes(x))) hits.push({ n: i + 1, text: l.trim().slice(0, 200), full: l }); });
    if (hits.length) res.push({ file: f, area: areaOf(f), hits });
  }
  const zips = walk(ctx.dir).filter(f => /\.zip$/i.test(f) && /pcba|build|kit/i.test(f));
  if (zips.length && opts.withZips !== false) res.push({ file: zips.join(', '), area: 'Packages to regenerate', hits: [{ n: 0, text: 'zip packages are not searched; regenerate them from their sources' }] });
  return res;
}
// The MPN plus its distinctive core (INR-21700-P45B -> P45B), which is how notes, comments and drawings name a part.
function partTerms(mpn, extra) {
  const t = new Set([mpn, ...(extra || [])].filter(Boolean));
  for (const tok of String(mpn || '').split(/[\s,;()/]+|-(?=[A-Za-z0-9])/)) if (tok.length >= 4 && /[A-Za-z]/.test(tok) && /\d/.test(tok) && !/^(INR|ICR|IMR|NCR)?\d+$/i.test(tok)) t.add(tok);
  return [...t];
}
function ecoOpen(ctx, line, altId, title) {
  const { p, s } = entry(ctx, line);
  const a = altId && altId !== '-' ? s.alternates.find(x => x.id === altId) : null;
  const C = readChanges(ctx);
  const n = C.changes.filter(c => c.kind === 'eco').length + (C.open || []).length + 1;
  const id = `ECO-${String(n).padStart(3, '0')}`;
  const terms = p ? partTerms(p.mpn, s.terms) : [];
  const imp = impact(ctx, terms);
  const byArea = {}; for (const r of imp) (byArea[r.area] = byArea[r.area] || []).push(r);
  const md = [`# ${id}: ${title || (a ? `${p.mpn} -> ${a.mpn || a.supplier}` : 'design change')}`, '',
    `Status: **open** · opened ${today()} · revision before: ${C.revision || ctx.build.revision || 'A'}`, '',
    '## Why', '', a ? `Line ${line} (${p.desc}, ${p.mpn} from ${p.supplier}) is to change to ${a.mfr || ''} ${a.mpn || ''} from ${a.supplier}. ${a.notes || ''}` : `Line ${line || '(none)'}: ${title || ''}`, '',
    '## Requirement check of the new part', '', a && (a.checks || []).length ? ['| Requirement | Needed | New part | Result | Design reason |', '|---|---|---|---|---|',
      ...a.checks.map(c => `| ${c.key} | ${c.eq ?? [c.min != null ? '>= ' + c.min : '', c.max != null ? '<= ' + c.max : ''].filter(Boolean).join(', ')} | ${c.value ?? '?'} | ${c.ok === null ? 'unknown' : c.ok ? 'pass' : 'FAIL'} | ${c.why} |`)].join('\n') : '(none recorded)', '',
    '## Decision and design changes', '', '_Fill in: what changes in the design (parameters, parts, firmware constants, limits), with the numbers and the calculation behind each._', '',
    '## Impact: every place that uses the old part', '', `Search terms: ${terms.map(t => '`' + t + '`').join(', ') || '(none)'}`, '',
    ...Object.entries(byArea).flatMap(([ar, list]) => [`### ${ar}`, '', ...list.map(r => `- [ ] \`${r.file}\` (${r.hits.length} mention${r.hits.length === 1 ? '' : 's'}${r.hits[0].n ? ', first at line ' + r.hits[0].n : ''})`), '']),
    '## Regenerate and re-check', '', '- [ ] CAD sources changed, STL/STEP re-exported', '- [ ] drawings re-rendered and looked at', '- [ ] affected parts re-sliced, G-code check passes', '- [ ] PCBA package rebuilt (if a board part changed)',
    '- [ ] firmware constants changed, host tests pass', '- [ ] BOM regenerated, BOM check passes, build.json + carts regenerated', '- [ ] assembly guide, assembly.json and the 3D twin updated', '- [ ] simulator tests re-run, results/latest.json updated',
    '- [ ] calculations (current, thermal, mass, cost) redone with the new numbers', `- [ ] \`node supply.js <project> eco-verify ${id}\` passes`, ''];
  fs.mkdirSync(changesDir(ctx), { recursive: true });
  fs.writeFileSync(path.join(changesDir(ctx), `${id}.md`), md.join('\n'));
  C.open = (C.open || []).concat([{ id, line, alt: a ? a.id : null, old_terms: terms, title: title || '', opened: new Date().toISOString() }]);
  writeJson(path.join(changesDir(ctx), 'changes.json'), C);
  return { id, file: path.posix.join(ctx.root, 'changes', `${id}.md`), impact: imp.map(r => ({ file: r.file, area: r.area, hits: r.hits.length })) };
}
const HISTORY_OK = /\b(was|previous(ly)?|replaced|instead of|alternat|alt:|ECO-\d|SUP-\d|formerly|old part|superseded)\b/i;
function ecoVerify(ctx, id) {
  const C = readChanges(ctx);
  const o = (C.open || []).find(x => x.id === id); if (!o) throw new Error(`${id} is not open`);
  const left = impact(ctx, o.old_terms, { skipHistory: true, withZips: false })
    .map(r => ({ ...r, hits: r.hits.filter(h => !HISTORY_OK.test(h.full || h.text)) })).filter(r => r.hits.length);
  if (left.length) return { ok: false, left };
  C.open = C.open.filter(x => x.id !== id);
  writeJson(path.join(changesDir(ctx), 'changes.json'), C);
  const ecoMd = path.join(changesDir(ctx), `${id}.md`);
  try { fs.writeFileSync(ecoMd, fs.readFileSync(ecoMd, 'utf8').replace('Status: **open**', `Status: **closed ${today()}**`)); } catch {}
  const ch = logChange(ctx, { id, kind: 'eco', line: o.line, summary: o.title, reason: 'engineering change', files: [path.posix.join(ctx.root, 'changes', `${id}.md`)] }, true);
  saveBuild(ctx);
  return { ok: true, revision: ch.revision };
}

// ---------------------------------------------------------------- API for the app server
function view(dir) {
  const ctx = load(dir); evaluate(ctx);
  let auditRows = []; try { auditRows = audit(ctx); } catch {}
  const C = readChanges(ctx);
  return { supply: ctx.supply, audit: auditRows, revision: C.revision || ctx.build.revision || 'A', changes: C.changes || [], open: C.open || [] };
}
module.exports = { load, view, audit, refresh: async (dir, lines) => refresh(load(dir), lines), feedback: (dir, ...a) => feedback(load(dir), ...a),
  candidate: (dir, ...a) => candidate(load(dir), ...a), swap: (dir, ...a) => swap(load(dir), ...a), impact: (dir, terms) => impact(load(dir), terms),
  ecoOpen: (dir, ...a) => ecoOpen(load(dir), ...a), ecoVerify: (dir, id) => ecoVerify(load(dir), id), checkUrl, fromHtml, fitOf, safeExpr, parseCsv, partTerms };

// ---------------------------------------------------------------- CLI
if (require.main === module) {
  (async () => {
    const [dirArg, cmd, ...rest] = process.argv.slice(2);
    if (!dirArg || !cmd) { console.log(fs.readFileSync(__filename, 'utf8').split('\n').slice(14, 26).map(l => l.replace(/^\/\/ ?/, '')).join('\n')); process.exit(2); }
    const dir = path.resolve(dirArg); const force = rest.includes('--force'); const args = rest.filter(a => a !== '--force');
    const ctx = load(dir);
    const out = x => console.log(typeof x === 'string' ? x : JSON.stringify(x, null, 2));
    switch (cmd) {
      case 'status': evaluate(ctx); for (const r of summary(ctx)) console.log(`${r.line.padEnd(6)} ${String(r.status).padEnd(12)} ${String(r.state).padEnd(15)} ${r.supplier || ''}${r.alternates.length ? '  | alts: ' + r.alternates.map(a => `${a.id} ${a.fit} ${a.status || '?'}`).join(', ') : ''}`); break;
      case 'audit': { const rows = audit(ctx); for (const r of rows.filter(r => r.verdict !== 'OK')) console.log(`${r.verdict} ${r.line}: ${r.reason}`); console.log(`${rows.filter(r => r.verdict === 'OK').length}/${rows.length} OK; written to build/1-purchase/qty-audit.md`); process.exit(rows.some(r => r.verdict === 'FAIL') ? 1 : 0); }
      case 'refresh': { const s = await refresh(ctx, args); for (const r of s) console.log(`${r.line.padEnd(6)} ${String(r.status).padEnd(12)} ${r.state}`); break; }
      case 'evaluate': evaluate(ctx); saveSupply(ctx); out(summary(ctx)); break;
      case 'feedback': out(feedback(ctx, args[0], args[1], args[2], args[3], args.slice(4).join(' '))); break;
      case 'candidate': out(await candidate(ctx, args[0], args[1], args.slice(2).join(' '))); break;
      case 'swap': out(swap(ctx, args[0], args[1], args.slice(2).join(' '), force)); break;
      case 'impact': for (const r of impact(ctx, args)) console.log(`[${r.area}] ${r.file}: ${r.hits.length}`); break;
      case 'eco-open': out(ecoOpen(ctx, args[0], args[1], args.slice(2).join(' '))); break;
      case 'eco-verify': { const r = ecoVerify(ctx, args[0]); if (!r.ok) { console.log(`${args[0]}: the old part is still used in:`); for (const x of r.left) for (const h of x.hits) console.log(`  ${x.file}:${h.n}: ${h.text}`); process.exit(1); } console.log(`${args[0]} closed; revision ${r.revision}`); break; }
      default: console.error('unknown command ' + cmd); process.exit(2);
    }
  })().catch(e => { console.error(e.message || e); process.exit(1); });
}
