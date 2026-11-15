// Xometry routing for the Build tab: which parts go out to xometry.com instead of the home printer or bench.
// A part goes to Xometry when it is too big for the printer bed, needs a material the user does not print
// at home (settings "Materials on hand"), is a metal or engineering-plastic part that is machined or cut,
// or the user moved it there by hand. Choices and per-part notes live in build/xometry.json so Claude
// sees them on the next run. Nothing is ever sent to Xometry from here: the app only prepares the files.
'use strict';

const fs = require('fs');
const path = require('path');

const readJson = f => JSON.parse(fs.readFileSync(f, 'utf8').replace(/^﻿/, ''));

// ---------------------------------------------------------------- settings
function printerFromSettings(text) {
  const bedM = /Bed size[^:\n]*:\s*([\d.]+)\s*[x×]\s*([\d.]+)(?:\s*[x×]\s*([\d.]+))?/i.exec(text || '');
  const bed = bedM ? [+bedM[1], +bedM[2], +(bedM[3] || bedM[2])] : [256, 256, 256];
  const matM = /Materials on hand[^:\n]*:\s*([^\n]*)/i.exec(text || '');
  const mats = (matM ? matM[1] : 'PLA, PETG').split(/[,;/]+/).map(s => s.trim().toUpperCase()).filter(s => s && !s.startsWith('('));
  return { bed, materials: mats.length ? mats : ['PLA', 'PETG'] };
}

// ---------------------------------------------------------------- STL size (no dependencies)
const sizeCache = new Map();
function stlSize(file) {
  let st; try { st = fs.statSync(file); } catch { return null; }
  const k = file + '|' + st.mtimeMs;
  if (sizeCache.has(k)) return sizeCache.get(k);
  let r = null;
  try {
    const b = fs.readFileSync(file);
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
    const add = (x, y, z) => { if (x < min[0]) min[0] = x; if (y < min[1]) min[1] = y; if (z < min[2]) min[2] = z; if (x > max[0]) max[0] = x; if (y > max[1]) max[1] = y; if (z > max[2]) max[2] = z; };
    const n = b.length >= 84 ? b.readUInt32LE(80) : 0;
    let tris = 0;
    if (b.length >= 84 && 84 + n * 50 === b.length) {
      for (let i = 0; i < n; i++) { const o = 84 + i * 50 + 12; for (let v = 0; v < 3; v++) add(b.readFloatLE(o + v * 12), b.readFloatLE(o + v * 12 + 4), b.readFloatLE(o + v * 12 + 8)); }
      tris = n;
    } else {
      const re = /vertex\s+(\S+)\s+(\S+)\s+(\S+)/g; const t = b.toString('latin1'); let m, nv = 0;
      while ((m = re.exec(t))) { add(+m[1], +m[2], +m[3]); nv++; }
      tris = Math.round(nv / 3);
    }
    if (isFinite(min[0])) r = { size: max.map((v, i) => +(v - min[i]).toFixed(2)), tris };
  } catch { r = null; }
  sizeCache.set(k, r);
  return r;
}

// 2D extents of a DXF cut file, in mm. Header $EXTMIN/$EXTMAX is often unset (ezdxf), so walk the entities.
const dxfCache = new Map();
function dxfSize(file) {
  let st; try { st = fs.statSync(file); } catch { return null; }
  const k = file + '|' + st.mtimeMs; if (dxfCache.has(k)) return dxfCache.get(k);
  let r = null;
  try {
    const L = fs.readFileSync(file, 'latin1').split(/\r?\n/);
    let units = /_in\.dxf$/i.test(file) ? 25.4 : 1, inEnt = false, type = '', x = null;
    const mn = [Infinity, Infinity], mx = [-Infinity, -Infinity];
    const add = (a, b) => { if (a < mn[0]) mn[0] = a; if (b < mn[1]) mn[1] = b; if (a > mx[0]) mx[0] = a; if (b > mx[1]) mx[1] = b; };
    let cx = null, cy = null;
    for (let i = 0; i + 1 < L.length; i += 2) {
      const code = L[i].trim(), v = L[i + 1].trim();
      if (code === '9' && v === '$INSUNITS') { const u = +(L[i + 3] || '').trim(); if (u === 1) units = 25.4; else if (u === 4) units = 1; else if (u === 5) units = 10; }
      if (code === '2' && v === 'ENTITIES') inEnt = true;
      if (code === '0') { if (v === 'ENDSEC') inEnt = false; type = v; cx = cy = null; }
      if (!inEnt || /^(TEXT|MTEXT|DIMENSION|ATTRIB|ATTDEF|INSERT|POINT|LEADER|MULTILEADER)$/.test(type)) continue; // labels are not part outline
      if (code === '10') x = +v;
      else if (code === '20' && x !== null) { add(x, +v); cx = x; cy = +v; x = null; }
      else if (code === '40' && (type === 'CIRCLE' || type === 'ARC') && cx !== null) { add(cx - +v, cy - +v); add(cx + +v, cy + +v); }
    }
    if (isFinite(mn[0])) r = [(mx[0] - mn[0]) * units, (mx[1] - mn[1]) * units];
  } catch { r = null; }
  dxfCache.set(k, r); return r;
}
// Sheet thickness from a material string: "6061-T6 aluminium 6.35 mm (1/4 in)", "5052-H32 aluminium 0.190 in".
function thickness(mat) {
  const mm = /(\d+(?:\.\d+)?)\s*mm\b/i.exec(mat || ''); if (mm) return +mm[1];
  const inch = /(\d*\.\d+|\d+)\s*(?:in\b|")/i.exec(mat || ''); if (inch) return +(+inch[1] * 25.4).toFixed(2);
  return null;
}

// Does a box fit the bed in some axis-aligned orientation? (Sorted dims against sorted bed dims.)
function fitsBed(size, bed) {
  const s = [...size].sort((a, b) => b - a), d = [...bed].sort((a, b) => b - a);
  return s.every((v, i) => v <= d[i] - 2); // 2 mm margin for brim and skirt
}

// ---------------------------------------------------------------- material and process rules
const METAL = /\b(alumin(i)?um|6061|7075|5052|2024|mic-?6|steel|stainless|303|304|316|17-4|brass|bronze|copper|titanium|ti-6al|inconel)\b/i;
const ENG_PLASTIC = /\b(nylon|pa ?6|pa ?12|pa-?cf|pet-?cf|polycarbonate|\bpc\b|delrin|acetal|pom|peek|ultem|uhmw|abs|asa|resin|sla|mjf|sls)\b/i;
const SERVICE_PROCESS = /\b(cnc|mill|lathe|turn(ed|ing)|waterjet|laser|machin|bend|brake|anodi[sz]e|sheet ?metal|cast|injection)\b/i;
const NOT_XOMETRY = /\b(pcb|pcba|harness|cable|wire|wiring|pigtail|lead|cut list|extrusion cut|crimp|solder)\b/i;
const arr = v => Array.isArray(v) ? v : v ? [v] : [];

function guessProcess(kind, mat, proc, files) {
  const m = (mat || '') + ' ' + (proc || '');
  if (kind === 'print') { // Xometry's own names: Process "3D Printing", then Technology
    if (/pa-?cf|pet-?cf|carbon/i.test(m)) return '3D Printing · FDM (carbon-fibre nylon)';
    if (/nylon|pa ?12|mjf/i.test(m)) return '3D Printing · MJF (Nylon 12)';
    if (/sls/i.test(m)) return '3D Printing · SLS (Nylon 12)';
    if (/resin|sla/i.test(m)) return '3D Printing · SLA';
    return '3D Printing · FDM';
  }
  const hasDxf = (files || []).some(f => /\.dxf$/i.test(f));
  if (hasDxf && /\b(waterjet|laser|cut from sheet)/i.test(m) && !/\b(mill|lathe|turn|machin|pocket|tap)/i.test(m)) return METAL.test(m) ? 'Sheet cutting (laser or waterjet)' : 'Sheet cutting (laser, waterjet or router)';
  if (/\b(cnc|mill|lathe|turn|machin)/i.test(m)) return 'CNC machining';
  if (/\bbend|brake|sheet ?metal/i.test(m)) return 'Sheet metal (cut and bend)';
  if (/\b(waterjet|laser|cut from sheet|router)/i.test(m) || hasDxf) return METAL.test(m) ? 'Sheet cutting (laser or waterjet)' : 'Sheet cutting (laser, waterjet or router)';
  if (/\btube|rod|bar\b/i.test(m)) return 'CNC machining (cut to length, drill)';
  return 'CNC machining';
}

function defaults(kind, p) {
  if (kind === 'print') return { finish: 'Standard (supports removed)', tolerance: 'Standard; see drawing and checks' };
  if (METAL.test(p.material || '')) return { finish: /alumin/i.test(p.material || '') ? 'As machined, deburred (anodize optional)' : 'As machined, deburred', tolerance: 'ISO 2768-m unless the drawing says tighter' };
  return { finish: 'Standard, deburred', tolerance: 'ISO 2768-m unless the drawing says tighter' };
}

// ---------------------------------------------------------------- file lookup
const norm = s => String(s || '').toLowerCase().replace(/\.(gcode\.3mf|step|stp|stl|3mf|dxf|pdf|obj)$/i, '').replace(/[^a-z0-9]+/g, '');
function stemOf(p) { return path.posix.basename(p).replace(/\.gcode\.3mf$/i, '').replace(/\.[^.]+$/, ''); }

function findFiles(files, names, exts) {
  const keys = [...new Set(names.filter(Boolean).map(norm).filter(k => k.length >= 3))];
  const cand = files.filter(f => exts.test(f.path));
  const exact = [], loose = [];
  for (const f of cand) {
    const s = norm(stemOf(f.path));
    if (keys.some(k => s === k)) exact.push(f.path);
    else if (keys.some(k => k.length >= 5 && (s.endsWith(k) || s.startsWith(k)))) loose.push(f.path);
  }
  const rank = p => (/assembly|assembled/i.test(p) ? 1 : 0) + p.length / 1000;
  return [...exact.sort((a, b) => rank(a) - rank(b)), ...loose.sort((a, b) => rank(a) - rank(b))];
}

// ---------------------------------------------------------------- main
function routing(dir, buildFile, settingsText, listFiles) {
  const B = readJson(path.join(dir, buildFile));
  const prefsFile = path.join(dir, path.posix.dirname(buildFile), 'xometry.json');
  let prefs = {}; try { prefs = readJson(prefsFile); } catch {}
  const over = prefs.parts || {};
  const printer = printerFromSettings(settingsText);
  const files = listFiles(dir).filter(f => !/(^|\/)xometry\//.test(f.path)); // ignore our own copies
  const homeMat = m => { const u = String(m || '').toUpperCase(); return printer.materials.some(x => u.startsWith(x) || new RegExp('^\\s*' + x.replace(/[^A-Z0-9]/g, '.') + '\\b').test(u)); };
  const out = [];

  for (const p of B.print || []) {
    const name = p.part; if (!name) continue;
    const stl = p.stl && fs.existsSync(path.join(dir, p.stl)) ? p.stl : findFiles(files, [p.part, p.stl && stemOf(p.stl)], /\.stl$/i)[0];
    const step = p.step || findFiles(files, [p.part, p.stl && stemOf(p.stl), p.line && `${p.line}-${p.part}`], /\.(step|stp)$/i)[0];
    const sz = stl ? stlSize(path.join(dir, stl)) : null;
    const reasons = [];
    if (sz && !fitsBed(sz.size, printer.bed)) reasons.push(`too big for the ${printer.bed.join(' x ')} mm bed`);
    const mat = String(p.material || '');
    if (mat && !homeMat(mat)) reasons.push(`material ${mat.split(/\s+-\s+|;/)[0].trim()} is not printed at home`);
    else if (/reprint in|first-article/i.test(mat)) reasons.push('final part needs ' + (/reprint in ([^.;]+)/i.exec(mat) || [, 'another material'])[1].trim());
    out.push(row('print', p, name, { stl, step, model: step || stl, size: sz && sz.size, tris: sz && sz.tris, drawing: /\.pdf$/i.test(p.drawing || '') ? p.drawing : null, reasons,
      notes: [p.notes, ...arr(p.checks).map(c => 'check: ' + c)].filter(Boolean).join('; ') }));
  }

  for (const f of B.fabricate || []) {
    const name = f.part; if (!name) continue;
    if (NOT_XOMETRY.test(`${name} ${f.process || ''}`) || f.pcba_package) continue; // boards, harnesses, cut lists stay where they are
    const ff = arr(f.files).filter(x => typeof x === 'string');
    const keyNames = [name, name.split(/\s+/)[0], f.line, ...ff.map(stemOf).map(s => s.replace(/_(mm|in)$/i, ''))];
    const step = f.step || ff.find(x => /\.(step|stp)$/i.test(x)) || findFiles(files, keyNames, /\.(step|stp)$/i)[0];
    // assembly STLs sit in world position and can hold several copies of a part, so they are no good for size or upload
    const stl = ff.find(x => /\.stl$/i.test(x)) || findFiles(files, keyNames, /\.stl$/i).filter(x => !/assembl/i.test(x))[0];
    const dxf = ff.find(x => /_mm\.dxf$/i.test(x)) || ff.find(x => /\.dxf$/i.test(x)) || findFiles(files, keyNames, /\.dxf$/i)[0];
    const drawing = [f.drawing, ...ff].find(x => /\.pdf$/i.test(x || '')) || findFiles(files, keyNames, /\.pdf$/i).find(x => /draw|sheet|dwg/i.test(x));
    if (!step && !stl && !dxf) continue; // nothing Xometry could quote from
    let sz = stl ? stlSize(path.join(dir, stl)) : null;
    if (!sz && dxf) { const d = dxfSize(path.join(dir, dxf)); const t = thickness(f.material); if (d) sz = { size: [+d[0].toFixed(2), +d[1].toFixed(2), t || 0], tris: null }; }
    const reasons = [];
    const metal = METAL.test(f.material || ''), eng = ENG_PLASTIC.test(f.material || '');
    const service = SERVICE_PROCESS.test(f.process || '') || /cutting service|xometry|sendcutsend|oshcut|protolabs|machine shop/i.test(f.vendor || '');
    if ((metal || eng) && service) reasons.push(`${metal ? 'metal' : 'engineering plastic'} part that needs ${/waterjet|laser|cut/i.test(f.process || '') ? 'cutting' : 'machining'}`);
    if (/xometry/i.test(f.vendor || '')) reasons.push('the design names Xometry');
    out.push(row('fabricate', f, name, { stl, step, dxf, model: step || stl, size: sz && sz.size, tris: sz && sz.tris, drawing, reasons, files: ff,
      notes: [f.settings, f.process].filter(Boolean).join('; ') }));
  }

  function row(kind, p, name, x) {
    const o = over[name] || {};
    const auto = x.reasons.length > 0;
    const route = o.route === 'xometry' || o.route === 'home' ? o.route : auto ? 'xometry' : 'home';
    const d = defaults(kind, p);
    const upload = [x.step, x.dxf, !x.step ? x.stl : null, x.drawing].filter(Boolean);
    const warn = [];
    const proc = o.process || guessProcess(kind, p.material, p.process, x.files || [x.stl, x.dxf].filter(Boolean));
    if (/cnc|machin/i.test(proc) && !x.step) warn.push('CNC quotes need a STEP file; none found for this part');
    if (!x.step && !x.stl && !x.dxf) warn.push('no 3D or DXF file found');
    return {
      key: name, kind, part: name, line: p.line || '', qty: +(o.qty || p.qty || 1),
      design_material: p.material || '', material: o.material || p.material || '',
      process: proc, finish: o.finish || d.finish, tolerance: o.tolerance || d.tolerance,
      notes: o.notes != null ? o.notes : x.notes || '', route, auto: auto ? 'xometry' : 'home', reasons: x.reasons, overridden: !!o.route && o.route !== (auto ? 'xometry' : 'home'),
      stl: x.stl || null, step: x.step || null, dxf: x.dxf || null, drawing: x.drawing || null, model: x.model || null,
      size: x.size || null, tris: x.tris || null, upload, warn,
    };
  }
  return { printer, parts: out, prefsFile: path.posix.join(path.posix.dirname(buildFile), 'xometry.json'), updated: prefs.updated || null };
}

function savePrefs(dir, buildFile, body) {
  const f = path.join(dir, path.posix.dirname(buildFile), 'xometry.json');
  let prefs = {}; try { prefs = readJson(f); } catch {}
  prefs.about = 'Parts the Anatomy app routes to Xometry (xometry.com/quoting). route: xometry|home overrides the automatic rule; material, process, finish, tolerance, qty and notes are what goes on the quote. Claude keeps these choices when it rebuilds the package.';
  prefs.parts = prefs.parts || {};
  for (const [k, v] of Object.entries(body.parts || {})) {
    const cur = prefs.parts[k] || {};
    for (const [fk, fv] of Object.entries(v || {})) { if (fv === null || fv === '') delete cur[fk]; else cur[fk] = fv; }
    if (Object.keys(cur).length) prefs.parts[k] = cur; else delete prefs.parts[k];
  }
  prefs.updated = new Date().toISOString();
  fs.writeFileSync(f, JSON.stringify(prefs, null, 2));
  return prefs;
}

// Copy every Xometry part's upload files into build/xometry/ with a parts list, ready to drag onto the quote page.
function preparePackage(dir, buildFile, settingsText, listFiles) {
  const R = routing(dir, buildFile, settingsText, listFiles);
  const parts = R.parts.filter(p => p.route === 'xometry');
  const outRel = path.posix.join(path.posix.dirname(buildFile), 'xometry');
  const out = path.join(dir, outRel);
  fs.mkdirSync(out, { recursive: true });
  for (const e of fs.readdirSync(out)) { try { fs.unlinkSync(path.join(out, e)); } catch {} } // stale copies from an earlier run
  const csvq = s => /[",\n]/.test(String(s ?? '')) ? '"' + String(s).replace(/"/g, '""') + '"' : String(s ?? '');
  const rows = [['Part', 'Line', 'Qty', 'Process', 'Material', 'Finish', 'Tolerance', 'Size mm (X x Y x Z)', 'Size in', 'Files', 'Why Xometry', 'Notes']];
  const copied = []; const used = new Set();
  for (const p of parts) {
    const names = [];
    for (const rel of p.upload) {
      let n = path.posix.basename(rel); if (used.has(n.toLowerCase())) n = p.part.replace(/[^\w.-]+/g, '_') + '-' + n;
      used.add(n.toLowerCase());
      try { fs.copyFileSync(path.join(dir, rel), path.join(out, n)); names.push(n); copied.push(path.posix.join(outRel, n)); } catch {}
    }
    rows.push([p.part, p.line, p.qty, p.process, p.material, p.finish, p.tolerance, p.size ? p.size.join(' x ') : '', p.size ? p.size.map(v => (v / 25.4).toFixed(2)).join(' x ') : '',
      names.join(' | '), p.reasons.join('; ') || 'moved by hand', p.notes]);
  }
  fs.writeFileSync(path.join(out, 'xometry-parts.csv'), '﻿' + rows.map(r => r.map(csvq).join(',')).join('\r\n') + '\r\n');
  const md = ['# Xometry order', '', `Prepared ${new Date().toISOString().slice(0, 16).replace('T', ' ')} by the Anatomy app. Nothing has been sent to Xometry.`, '',
    '1. Open https://www.xometry.com/quoting/home/ and sign in.',
    '2. Drag the STEP (or STL/DXF) file of each part below onto the upload area. Add the PDF drawing to the same part as a technical drawing.',
    '3. For each part set the process, material, finish, tolerance and quantity from this list, then review the price and lead time yourself.', '',
    ...parts.map(p => `## ${p.part}${p.line ? ` (${p.line})` : ''}\n\n- Qty: ${p.qty}\n- Process: ${p.process}\n- Material: ${p.material}\n- Finish: ${p.finish}\n- Tolerance: ${p.tolerance}\n` +
      (p.size ? `- Size: ${p.size.map(v => v.toFixed(1)).join(' x ')} mm [${p.size.map(v => (v / 25.4).toFixed(2)).join(' x ')} in]\n` : '') +
      `- Why Xometry: ${p.reasons.join('; ') || 'moved by hand'}\n- Files: ${p.upload.map(u => path.posix.basename(u)).join(', ') || 'none found'}\n` +
      (p.warn.length ? `- Watch: ${p.warn.join('; ')}\n` : '') + (p.notes ? `- Notes: ${p.notes}\n` : ''))];
  fs.writeFileSync(path.join(out, 'XOMETRY-ORDER.md'), md.join('\n'));
  return { dir: outRel, parts: parts.length, files: copied };
}

module.exports = { routing, savePrefs, preparePackage, stlSize, fitsBed, printerFromSettings };
