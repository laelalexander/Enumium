// Design Studio back end: what the 3D design editor reads (assembly, parameters, materials), where it saves
// the user's edits, how an edit set becomes a new revision of the project, and the Blender hand-off.
//
// Nothing here changes a project's own files. Edits are saved in <project>/.anatomy/design/, and "Rebuild"
// makes a NEW project (rev B, rev C, ...) that the anatomy skill regenerates from the edits, so the completed
// version stays exactly as it was.
'use strict';
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const SKIP_DIR = new Set(['.anatomy', '.tools', '.venv', 'venv', 'env', 'node_modules', '__pycache__', '.git', '.pio', '.claude', '.mypy_cache', '.pytest_cache']);
const readJson = f => JSON.parse(fs.readFileSync(f, 'utf8').replace(/^\uFEFF/, ''));

function walk(dir, test, maxDepth = 8) {
  const out = [];
  (function go(rel, depth) {
    if (depth > maxDepth || out.length > 400) return;
    let ents = []; try { ents = fs.readdirSync(path.join(dir, rel), { withFileTypes: true }); } catch { return; }
    for (const e of ents) {
      if (SKIP_DIR.has(e.name)) continue;
      const r = rel ? rel + '/' + e.name : e.name;
      if (e.isDirectory()) go(r, depth + 1); else if (test(r, e.name)) out.push(r);
    }
  })('', 0);
  return out;
}
const depth = p => p.split('/').length;

// ---------------------------------------------------------------- parameters
// The skill keeps every dimension in one parameter file (e.g. hx1_params.py). Top-level constants with a plain
// number, a tuple of numbers or a one-line dict of numbers are editable; anything computed is shown as derived.
const NUM = String.raw`-?\d+(?:\.\d+)?(?:e-?\d+)?`;
const RE_NUM = new RegExp(`^${NUM}$`, 'i');
const RE_TUPLE = new RegExp(`^[\\(\\[]\\s*(${NUM}\\s*,\\s*)*${NUM}\\s*,?\\s*[\\)\\]]$`, 'i');
function splitComment(s) { // value part and trailing # comment, ignoring # inside quotes
  let q = null;
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (q) { if (c === q) q = null; continue; }
    if (c === '"' || c === "'") q = c; else if (c === '#') return [s.slice(0, i).trim(), s.slice(i + 1).trim()];
  }
  return [s.trim(), ''];
}
function parseValue(v) {
  v = v.replace(/,\s*$/, '');
  if (RE_NUM.test(v)) return { type: 'number', value: Number(v) };
  if (RE_TUPLE.test(v)) return { type: 'tuple', value: v.replace(/[()[\]\s]/g, '').split(',').filter(Boolean).map(Number) };
  const d = v.match(/^\{(.*)\}$/);
  if (d) {
    const ent = d[1].split(',').map(s => s.trim()).filter(Boolean).map(s => s.match(new RegExp(`^["']([^"']+)["']\\s*:\\s*(${NUM})$`, 'i')));
    if (ent.length && ent.every(Boolean)) return { type: 'dict', value: Object.fromEntries(ent.map(m => [m[1], Number(m[2])])) };
  }
  return null;
}
function parseParams(text) {
  const out = []; let section = '';
  const lines = text.split(/\r?\n/);
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const h = line.match(/^#\s*-{3,}\s*(.+?)\s*-{3,}\s*$/); if (h) { section = h[1]; continue; }
    const m = line.match(/^([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)\s*=\s*(.+)$/);
    if (!m || /^(import|from|def|class)\b/.test(line)) continue;
    const names = m[1].split(',').map(s => s.trim());
    const [val, comment] = splitComment(m[2]);
    if (/^["'[{(]?$/.test(val) && !val.endsWith(')') && !val.endsWith('}') && !val.endsWith(']')) continue; // multi-line literal
    const tag = ((comment.match(/\[([a-z]+)[^\]]*\]/i) || [])[1] || '').toLowerCase();
    const note = comment.replace(/^\[[^\]]+\]\s*/, '');
    if (/["']/.test(val)) continue; // names and labels are not dimensions
    if (names.length > 1) { // A, B = 1.0, 2.0
      const vals = val.split(',').map(s => s.trim());
      names.forEach((n, k) => { const pv = parseValue(vals[k] || ''); out.push({ name: n, line: i + 1, section, tag, note, expr: vals[k] || '', ...(pv || { type: 'derived' }) }); });
      continue;
    }
    const pv = parseValue(val);
    if (!pv && /^["']/.test(val)) continue; // strings are not dimensions
    if (!pv && !/[A-Z_]{2,}|\d/.test(val)) continue;
    out.push({ name: names[0], line: i + 1, section, tag, note, expr: val, ...(pv || { type: 'derived' }) });
  }
  return out;
}
function findParams(dir) {
  const files = walk(dir, (r, n) => /(^|_)(params|parameters)\.(py|json)$/i.test(n) && !/(^|\/)(build|print|gcode|sim)\//i.test(r))
    .sort((a, b) => depth(a) - depth(b)).slice(0, 6);
  return files.map(f => {
    try {
      if (f.endsWith('.json')) {
        const j = readJson(path.join(dir, f));
        const items = Object.entries(j).map(([name, v]) => {
          if (typeof v === 'number') return { name, type: 'number', value: v, section: '', tag: '', note: '' };
          if (Array.isArray(v) && v.every(x => typeof x === 'number')) return { name, type: 'tuple', value: v, section: '', tag: '', note: '' };
          if (v && typeof v === 'object' && typeof v.value === 'number') return { name, type: 'number', value: v.value, section: v.group || '', tag: v.source || '', note: v.note || v.description || '' };
          return null;
        }).filter(Boolean);
        return { file: f, items };
      }
      return { file: f, items: parseParams(fs.readFileSync(path.join(dir, f), 'utf8')) };
    } catch (e) { return { file: f, items: [], error: e.message }; }
  }).filter(p => p.items.length);
}

// ---------------------------------------------------------------- assembly + materials
function findAssembly(dir) {
  const a = walk(dir, (r, n) => n === 'assembly.json' && !/scale_model|print|build\//i.test(r)).sort((x, y) => depth(x) - depth(y));
  const b = a.length ? a : walk(dir, (r, n) => n === 'assembly.json').sort((x, y) => depth(x) - depth(y));
  return b[0] || null;
}
// Material text per mesh file: parts.json next to the meshes, then the BOM line's spec (bom/lines.json or bom.csv).
function materialHints(dir, asmPath, parts) {
  const base = asmPath ? path.posix.dirname(asmPath) : '';
  const hints = {};
  try {
    const pj = readJson(path.join(dir, base, 'parts.json'));
    for (const [k, v] of Object.entries(pj || {})) if (v && typeof v === 'object') hints[k] = [v.material, v.category, v.name].filter(Boolean).join(' · ');
  } catch {}
  let lines = null;
  const lj = walk(dir, (r, n) => n === 'lines.json' && /bom/i.test(r)).sort((x, y) => depth(x) - depth(y))[0];
  if (lj) try { lines = readJson(path.join(dir, lj)); } catch {}
  const byLine = new Map((Array.isArray(lines) ? lines : []).map(l => [String(l.line || '').trim(), l]));
  for (const p of parts || []) {
    const l = byLine.get(String(p.line || '').trim());
    const extra = l ? [l.description, l.key_spec, l.mpn_or_standard, l.manufacturer].filter(Boolean).join(' · ') : '';
    const stem = String(p.file || '').replace(/\.[^.]+$/, '');
    hints[p.file] = [hints[p.file] || hints[stem] || '', extra].filter(Boolean).join(' · ');
  }
  return hints;
}

// ---------------------------------------------------------------- edits
const designDir = dir => path.join(dir, '.anatomy', 'design');
const editsFile = dir => path.join(designDir(dir), 'edits.json');
function loadEdits(dir) { try { return readJson(editsFile(dir)); } catch { return null; } }
function saveEdits(dir, edits) {
  fs.mkdirSync(designDir(dir), { recursive: true });
  edits.saved = new Date().toISOString();
  fs.writeFileSync(editsFile(dir), JSON.stringify(edits, null, 1));
  return edits;
}

function info(dir) {
  const asm = findAssembly(dir);
  let assembly = null;
  if (asm) try { assembly = readJson(path.join(dir, asm)); } catch (e) { assembly = { error: e.message }; }
  const meshes = asm ? [] : walk(dir, (r, n) => /\.(stl|glb|obj|3mf)$/i.test(n) && !/(^|\/)(print|gcode|build|slic\w*|plates?)\//i.test(r)).slice(0, 200);
  const parts = assembly && Array.isArray(assembly.parts) ? assembly.parts : meshes.map(m => ({ file: m, name: path.posix.basename(m).replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ') }));
  return {
    assembly: asm, base: asm ? (path.posix.dirname(asm) === '.' ? '' : path.posix.dirname(asm) + '/') : '',
    units: (assembly && assembly.units) || 'mm', up: (assembly && assembly.up) || 'Z', parts,
    params: findParams(dir), hints: materialHints(dir, asm, parts), edits: loadEdits(dir),
    blender: !!findBlender(), renders: listRenders(dir), engineering: engineeringInfo(dir),
  };
}

// ---------------------------------------------------------------- the edit set, written for the skill
function editsMarkdown(meta, id, e) {
  const L = [];
  const f1 = v => Math.round(v * 10) / 10;
  L.push(`# Design edits for ${meta.title || id}`, '', `Made in the Anatomy design editor on ${new Date().toISOString().slice(0, 16).replace('T', ' ')} against project \`${id}\`. Units: mm, degrees. Coordinates are the assembly's world frame (${e.up || 'Z'} up).`, '');
  if (e.global && (e.global.notes || e.global.style || e.global.detail || e.global.autoStyle)) {
    L.push('## Overall direction', '');
    if (e.global.autoStyle) L.push('- **No more boxes:** restyle every square, boxy or low-detail part, not only the ones listed below: fillets on every edge, curved and drafted surfaces where they make sense, and the real manufacturer shape for every bought part (references/industrial-design.md).');
    if (e.global.style) L.push(`- Styling language: **${e.global.style}**`);
    if (e.global.detail) L.push(`- Detail level: **${e.global.detail}**`);
    if (e.global.targetGrade) L.push(`- **Engineering grade target: ${e.global.targetGrade}** for every precision and structural part (references/precision-engineering.md): feature-based CAD with real holes and fillets, datums, ISO fits, GD&T, finish, material and process, DFM${/verified/i.test(e.global.targetGrade) ? ', FEA margins, tolerance stack-ups and an inspection plan' : ''}. Bought parts get the vendor STEP. Record it all in prototype/mechanical/engineering.json and run tools/eng/check_engineering.py until the evidence supports the grade. Blender shapes are concept intent only.`);
    if (e.global.notes) L.push('', e.global.notes);
    L.push('');
  }
  const params = Object.entries(e.params || {});
  if (params.length) {
    L.push('## Parameter changes', '', '| File | Parameter | Was | Now |', '|---|---|---|---|');
    for (const [k, p] of params) L.push(`| ${p.file} | \`${k}\` | ${JSON.stringify(p.from)} | **${JSON.stringify(p.to)}** |`);
    L.push('');
  }
  const parts = Object.entries(e.parts || {});
  if (parts.length) {
    L.push('## Part changes', '');
    for (const [file, p] of parts) {
      const t = [];
      if (p.removed) t.push('**Remove this part** from the design (and the BOM, drawings, G-code and assembly).');
      if (p.translate && p.translate.some(v => Math.abs(v) > 0.05)) t.push(`Move by [${p.translate.map(f1).join(', ')}] mm (X, Y, Z).`);
      if (p.rotate && p.rotate.some(v => Math.abs(v) > 0.05)) t.push(`Rotate by [${p.rotate.map(f1).join(', ')}] deg about X, Y, Z through the part's bounding-box centre [${(p.center || []).map(f1).join(', ')}].`);
      if (p.scale && p.scale.some(v => Math.abs(v - 1) > 0.0005)) t.push(`Scale by [${p.scale.map(v => Math.round(v * 1000) / 1000).join(', ')}] (X, Y, Z) about its centre: change the driving dimensions, do not just scale the mesh. New overall size ≈ [${(p.size || []).map((s, k) => f1(s * p.scale[k])).join(', ')}] mm.`);
      if (p.material) t.push(`Material / finish: **${p.material}**${p.color ? ` (colour ${p.color})` : ''}.`);
      else if (p.color) t.push(`Colour ${p.color}.`);
      if (p.styles && p.styles.length) t.push(`Styling: ${p.styles.join('; ')}.`);
      if (p.mesh) t.push(`Sculpted in Blender: match the shape in \`${p.mesh}\` (mesh in the part's local frame, mm, centred on the part's centre). Rebuild it as real CAD, do not ship the mesh.`);
      if (p.engineer) t.push(`**Engineer this part to grade ${p.engineer}** (references/precision-engineering.md)${p.partClass ? ` as a ${p.partClass} part` : ''}.`);
      else if (p.partClass) t.push(`Class: ${p.partClass}.`);
      if (p.note) t.push(`Note: ${p.note}`);
      if (!t.length) continue;
      L.push(`### ${p.name || file}`, '', `File \`${file}\`${p.line ? `, BOM line ${p.line}` : ''}.`, '', ...t.map(s => '- ' + s), '');
    }
  }
  return L.join('\n');
}

function nextRevision(listProjects, rootId) {
  const used = new Set(listProjects().filter(p => p.revisionRoot === rootId || p.id === rootId).map(p => p.revision).filter(Boolean));
  for (let c = 98; c < 123; c++) { const L = String.fromCharCode(c).toUpperCase(); if (!used.has(L)) return L; } // B..Z
  return 'Z' + Date.now() % 1000;
}

// Copy the project into the new revision folder: sources, models, drawings and docs. Leaves out the run log,
// virtual environments and caches (the revision may run the original's tools, read-only).
const COPY_SKIP = new Set(['.anatomy', '.venv', 'venv', 'env', 'node_modules', '__pycache__', '.git', '.pio', '.mypy_cache', '.pytest_cache', '.tools', 'CLAUDE.md']);
async function copyProject(src, dst, onProgress) {
  let n = 0;
  async function go(rel) {
    const ents = await fs.promises.readdir(path.join(src, rel), { withFileTypes: true }).catch(() => []);
    await fs.promises.mkdir(path.join(dst, rel), { recursive: true });
    for (const e of ents) {
      if (!rel && COPY_SKIP.has(e.name)) continue;
      if (rel && (e.name === '__pycache__' || e.name === 'node_modules' || e.name === '.venv')) continue;
      const r = rel ? path.join(rel, e.name) : e.name;
      if (e.isDirectory()) await go(r);
      else if (e.isFile()) { await fs.promises.copyFile(path.join(src, r), path.join(dst, r)).catch(() => {}); if (++n % 200 === 0 && onProgress) onProgress(n); }
    }
  }
  await go('');
  return n;
}

// ---------------------------------------------------------------- Blender
function findBlender() {
  if (process.env.ANATOMY_BLENDER && fs.existsSync(process.env.ANATOMY_BLENDER)) return process.env.ANATOMY_BLENDER;
  if (process.platform !== 'win32') return null;
  const roots = [process.env.ProgramFiles, process.env['ProgramFiles(x86)'], process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'Programs')].filter(Boolean);
  const hits = [];
  for (const r of roots) {
    const bf = path.join(r, 'Blender Foundation');
    let ds = []; try { ds = fs.readdirSync(bf); } catch {}
    for (const d of ds) { const exe = path.join(bf, d, 'blender.exe'); if (fs.existsSync(exe)) hits.push(exe); }
  }
  // Steam install
  for (const s of ['C:\\Program Files (x86)\\Steam\\steamapps\\common\\Blender\\blender.exe']) if (fs.existsSync(s)) hits.push(s);
  hits.sort((a, b) => b.localeCompare(a, undefined, { numeric: true })); // newest version first
  return hits[0] || null;
}
function listRenders(dir) {
  const d = path.join(designDir(dir), 'renders');
  let fsn = []; try { fsn = fs.readdirSync(d).filter(n => /\.png$/i.test(n)); } catch {}
  return fsn.sort().reverse().slice(0, 20).map(n => '.anatomy/design/renders/' + n);
}
const blenderJobs = new Map(); // dir -> { proc, log, mode, out, started }
function runBlender(dir, mode, opts, cleanEnv) {
  const exe = findBlender();
  if (!exe) throw new Error('Blender was not found on this PC. Install Blender (blender.org) and try again.');
  const cur = blenderJobs.get(dir);
  if (mode === 'render' && cur && cur.mode === 'render' && cur.proc) throw new Error('A render is already running.');
  const dd = designDir(dir);
  fs.mkdirSync(path.join(dd, 'renders'), { recursive: true });
  const script = path.join(__dirname, 'blender', 'anatomy_blender.py');
  const glb = path.join(dd, 'scene.glb');
  const stamp = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
  const out = path.join(dd, 'renders', `render-${stamp}.png`);
  const args = mode === 'render' ? ['-b', '--factory-startup', '--python', script, '--'] : ['--python', script, '--'];
  args.push(glb, mode, out, path.join(dd, 'blender-return.json'), path.join(dd, 'sculpt'), String(opts.samples || 160), String(opts.width || 1920), String(opts.height || 1080), path.join(dd, 'scene.blend'));
  const job = { mode, log: '', out: mode === 'render' ? '.anatomy/design/renders/' + path.basename(out) : null, started: Date.now(), done: false, code: null };
  const proc = spawn(exe, args, { cwd: dd, env: cleanEnv(), windowsHide: mode === 'render', detached: mode !== 'render' });
  job.proc = proc;
  proc.stdout.on('data', d => { job.log = (job.log + d).slice(-20000); });
  proc.stderr.on('data', d => { job.log = (job.log + d).slice(-20000); });
  proc.on('close', code => { job.done = true; job.code = code; job.proc = null; });
  proc.on('error', e => { job.done = true; job.code = -1; job.log += '\n' + e.message; job.proc = null; });
  if (mode !== 'render') proc.unref();
  blenderJobs.set(dir + '|' + mode, job);
  return { ok: true, mode, out: job.out };
}
function blenderStatus(dir) {
  const r = blenderJobs.get(dir + '|render');
  const ret = path.join(designDir(dir), 'blender-return.json');
  let back = null; try { back = readJson(ret); back.mtime = fs.statSync(ret).mtimeMs; } catch {}
  const progress = r && r.log ? ((r.log.match(/Sample (\d+)\/(\d+)/g) || []).pop() || '') : '';
  return {
    render: r ? { running: !r.done, code: r.code, out: r.out, ok: r.done && r.code === 0 && fs.existsSync(path.join(dir, r.out)), progress, tail: r.done && r.code ? r.log.slice(-1500) : '' } : null,
    blenderReturn: back, renders: listRenders(dir), installed: !!findBlender(),
  };
}

// ---------------------------------------------------------------- engineering grade (references/precision-engineering.md)
const ENG_TOOLS = [path.join(__dirname, 'eng-tools'), path.join(__dirname, '..', 'tools', 'eng')].find(d => fs.existsSync(path.join(d, 'check_engineering.py')));
function engineeringInfo(dir) {
  const eng = walk(dir, (r, n) => n === 'engineering.json' && !/scale_model/i.test(r)).sort((a, b) => depth(a) - depth(b))[0] || null;
  let records = null; if (eng) try { records = readJson(path.join(dir, eng)).parts || null; } catch {}
  // The app's own check result (hidden folder) wins over a report the run wrote, when it is newer.
  const cands = [path.join(designDir(dir), 'engineering-report.json')];
  if (eng) cands.push(path.join(dir, path.posix.dirname(eng), 'engineering-report.json'));
  let report = null, at = 0;
  for (const c of cands) try { const st = fs.statSync(c); if (st.mtimeMs > at) { report = readJson(c); at = st.mtimeMs; } } catch {}
  return { file: eng, records, report, reportAt: at || null, tools: !!ENG_TOOLS };
}
// A Python that has build123d: the project's venv, any other project's venv, then python on PATH.
let pyCache = null;
function findCadPython(dir, root) {
  const { execFileSync } = require('child_process');
  const ok = py => { try { execFileSync(py, ['-c', 'import build123d'], { timeout: 60000, windowsHide: true, stdio: 'ignore' }); return true; } catch { return false; } };
  const venv = d => [path.join(d, '.venv', 'Scripts', 'python.exe'), path.join(d, '.venv', 'bin', 'python')].find(p => fs.existsSync(p));
  const own = venv(dir); if (own && ok(own)) return own;
  if (pyCache && ok(pyCache)) return pyCache;
  let ents = []; try { ents = fs.readdirSync(root, { withFileTypes: true }).filter(e => e.isDirectory()); } catch {}
  for (const e of ents) { const p = venv(path.join(root, e.name)); if (p && ok(p)) return (pyCache = p); }
  for (const p of process.platform === 'win32' ? ['python', 'py'] : ['python3', 'python']) if (ok(p)) return (pyCache = p);
  return null;
}
function runPy(py, args, cwd, cleanEnv, timeoutMs) {
  return new Promise(resolve => {
    let out = '', err = '';
    const p = spawn(py, args, { cwd, env: cleanEnv(), windowsHide: true });
    const k = setTimeout(() => { try { p.kill(); } catch {} }, timeoutMs);
    p.stdout.on('data', d => { out += d; }); p.stderr.on('data', d => { err = (err + d).slice(-4000); });
    p.on('close', code => { clearTimeout(k); resolve({ code, out, err }); });
    p.on('error', e => { clearTimeout(k); resolve({ code: -1, out, err: e.message }); });
  });
}
// Exact features of a part's STEP (holes, fillets, chamfers, faces), cached by file time.
async function stepFeatures(dir, root, rel, cleanEnv) {
  if (!ENG_TOOLS) throw new Error('The engineering tools are not installed with the app.');
  const f = path.resolve(dir, rel); if (!f.startsWith(dir + path.sep) || !fs.existsSync(f)) throw new Error('STEP file not found: ' + rel);
  const cdir = path.join(designDir(dir), 'features'); fs.mkdirSync(cdir, { recursive: true });
  const cf = path.join(cdir, rel.replace(/[\/:]/g, '_') + '.json');
  const mt = fs.statSync(f).mtimeMs;
  try { const c = readJson(cf); if (c._mtime === mt) return c; } catch {}
  const py = findCadPython(dir, root); if (!py) throw new Error('No Python with build123d was found on this PC.');
  const r = await runPy(py, [path.join(ENG_TOOLS, 'step_features.py'), f], dir, cleanEnv, 180000);
  if (r.code !== 0) throw new Error('Could not measure the STEP: ' + (r.err || r.out).slice(-600));
  const j = JSON.parse(r.out); j._mtime = mt; j.file = rel;
  fs.writeFileSync(cf, JSON.stringify(j));
  return j;
}
// Run the grade check without touching the project: a starting record is made in the hidden design folder
// when the project has no engineering.json yet.
async function gradeCheck(dir, root, cleanEnv) {
  if (!ENG_TOOLS) throw new Error('The engineering tools are not installed with the app.');
  const py = findCadPython(dir, root); if (!py) throw new Error('No Python with build123d was found on this PC.');
  const dd = designDir(dir); fs.mkdirSync(dd, { recursive: true });
  let eng = engineeringInfo(dir).file ? path.join(dir, engineeringInfo(dir).file) : null;
  if (!eng) {
    const asm = findAssembly(dir); if (!asm) throw new Error('The project has no assembly.json to grade.');
    eng = path.join(dd, 'engineering.init.json');
    const r0 = await runPy(py, [path.join(ENG_TOOLS, 'check_engineering.py'), '--init', path.join(dir, asm), '--root', dir, '--out', eng], dir, cleanEnv, 120000);
    if (r0.code !== 0) throw new Error((r0.err || r0.out).slice(-600));
  }
  const out = path.join(dd, 'engineering-report.json');
  const r = await runPy(py, [path.join(ENG_TOOLS, 'check_engineering.py'), eng, '--root', dir, '--json', out, '--out', path.join(dd, 'engineering-report.md')], dir, cleanEnv, 900000);
  if (!fs.existsSync(out)) throw new Error('The check did not finish: ' + (r.err || r.out).slice(-600));
  const rep = readJson(out);
  try { rep.records = readJson(eng).parts; } catch {}
  rep.provisional = !engineeringInfo(dir).file;
  fs.writeFileSync(out, JSON.stringify(rep));
  return rep;
}

module.exports = { engineeringInfo, stepFeatures, gradeCheck, info, saveEdits, loadEdits, editsMarkdown, nextRevision, copyProject, designDir, runBlender, blenderStatus, findBlender, parseParams };
