/* Anatomy twin loader (classic script, put it before the app's module script; no dependencies).
 *
 *   <script src="twinload.js" data-title="Opening the XYZ digital twin" data-sub="3D model, behaviour model and tests"
 *           data-entry="app.js"></script>
 *
 * Shows a loading screen with real, staged progress and ends either on the running twin or on a plain-language error
 * with a Try again button - never a blank page:
 *   engine - three.js and the twin's code, downloaded byte by byte by walking the static imports from data-entry
 *            (bare specifiers resolved through the page's import map), then the entry module is started;
 *   data   - design data the app fetches (json, csv, txt ...), counted automatically;
 *   model  - 3D model files the app fetches (glb, gltf, stl, obj, 3mf, bin), with bytes of total;
 *   scene  - building the scene; ends when the app calls TwinLoad.done(), or by itself once a canvas is drawn and
 *            nothing has been downloading for a moment (for apps that do not call it).
 * The app may also drive it: TwinLoad.stage(key, text), .progress(f, text, right), .indeterminate(text), .done(), .fail(msg).
 * Every URL is relative to the page, so the twin works from any sub-path on plain static hosting (Anatomy Hub, a file
 * server, the twin's own server). Without data-entry it only shows the screen and tracks downloads; the page then
 * loads its own scripts as usual.
 */
(function () {
  'use strict';
  if (window.TwinLoad && window.TwinLoad.__anatomy) return;
  var me = document.currentScript || {};
  var ds = me.dataset || {};
  var TITLE = ds.title || 'Opening the digital twin';
  var SUB = ds.sub || '3D model, behaviour model and controls';
  var ENTRY = ds.entry || '';
  var STALL = (+ds.stall || 40) * 1000;          // no progress for this long while loading -> error
  var AUTO_DONE = ds.autodone !== 'off';
  var STAGES = [['engine', ds.engine || '3D engine and twin code', 40], ['data', ds.data || 'Design data', 10],
    ['model', ds.model || '3D model', 40], ['scene', ds.scene || 'Building the scene', 10]];

  var css = '#twinLoad{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;background:rgba(14,16,20,.94);color:#eef0f2;font:13px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;transition:opacity .35s}' +
    '#twinLoad.gone{opacity:0;pointer-events:none}#twinLoad .lbox{width:min(480px,92vw);background:#1b1e24;border:1px solid #363b45;border-radius:10px;padding:22px 24px;box-shadow:0 10px 40px #0008}' +
    '#twinLoad .lt{font-size:17px;font-weight:700}#twinLoad .ls{color:#99a1ad;margin:2px 0 14px}#twinLoad .lbar{height:10px;border-radius:6px;background:#2c313a;overflow:hidden}' +
    '#twinLoad .lbar i{display:block;height:100%;width:0;background:#3b8beb;border-radius:6px;transition:width .2s}#twinLoad .lbar.ind i{width:30%!important;animation:twlInd 1.2s ease-in-out infinite}#twinLoad .lbar.bad i{background:#d64545;width:100%!important;animation:none}' +
    '@keyframes twlInd{0%{margin-left:-30%}100%{margin-left:100%}}' +
    '#twinLoad .lpct{display:flex;justify-content:space-between;gap:12px;color:#c4cad3;font-variant-numeric:tabular-nums;margin:6px 0 10px}#twinLoad .lpct span:first-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
    '#twinLoad ol{list-style:none;margin:0;padding:0}#twinLoad li{padding:3px 0 3px 22px;position:relative;color:#7f8896}#twinLoad li:before{content:"\\25CB";position:absolute;left:2px}' +
    '#twinLoad li.on{color:#eef0f2;font-weight:600}#twinLoad li.on:before{content:"\\25D0";color:#3b8beb}#twinLoad li.ok{color:#c4cad3}#twinLoad li.ok:before{content:"\\2713";color:#3fb950}#twinLoad li.bad{color:#f0883e}#twinLoad li.bad:before{content:"\\2715"}' +
    '#twinLoad .lerr{display:none;margin-top:12px;padding:10px 12px;border-radius:6px;background:#3a1717;color:#ffdcdc;white-space:pre-wrap;word-break:break-word}' +
    '#twinLoad .lerr button{margin-top:10px;font:inherit;color:#fff;background:#2f6fd0;border:0;border-radius:6px;padding:6px 14px;cursor:pointer}';
  var root, q;
  function mount() {
    if (root) return;
    var st = document.createElement('style'); st.textContent = css; (document.head || document.documentElement).appendChild(st);
    root = document.createElement('div'); root.id = 'twinLoad'; root.setAttribute('role', 'status'); root.setAttribute('aria-live', 'polite');
    root.innerHTML = '<div class="lbox"><div class="lt"></div><div class="ls"></div><div class="lbar"><i></i></div><div class="lpct"><span class="lnow">Starting…</span><span class="lval"></span></div><ol>' +
      STAGES.map(function (s) { return '<li data-k="' + s[0] + '"></li>'; }).join('') + '</ol><div class="lerr"></div></div>';
    root.querySelector('.lt').textContent = TITLE; root.querySelector('.ls').textContent = SUB;
    STAGES.forEach(function (s) { root.querySelector('li[data-k="' + s[0] + '"]').textContent = s[1]; });
    (document.body || document.documentElement).appendChild(root);
    q = function (s) { return root.querySelector(s); };
  }
  if (document.body) mount(); else document.addEventListener('DOMContentLoaded', mount);

  var weight = {}, before = {}, acc = 0, order = {};
  STAGES.forEach(function (s, i) { weight[s[0]] = s[2]; before[s[0]] = acc; acc += s[2]; order[s[0]] = i; });
  var cur = null, finished = false, failed = false, lastMove = Date.now();
  function li(k) { return root && q('li[data-k="' + k + '"]'); }
  function kb(n) { return n >= 1048576 ? (n / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(n / 1024)) + ' KB'; }
  function bar(f) {
    if (!root) return 0; q('.lbar').classList.remove('ind');
    var p = cur ? before[cur] + weight[cur] * Math.max(0, Math.min(1, f || 0)) : 0; q('.lbar i').style.width = p + '%'; return p;
  }
  function setNow(t, right) { if (!root) return; if (t) q('.lnow').textContent = t; if (right != null) q('.lval').textContent = right; }

  var L = window.TwinLoad = {
    __anatomy: true,
    stage: function (k, text) {
      if (failed || finished) return; mount(); lastMove = Date.now();
      if (!(k in order)) { setNow(text || k); return; }
      if (cur && order[k] < order[cur]) { setNow(text); return; }          // never go backwards
      STAGES.forEach(function (s) { if (cur !== null && order[s[0]] < order[k] && li(s[0]) && li(s[0]).className !== 'ok') li(s[0]).className = 'ok'; });
      if (cur && cur !== k && li(cur)) li(cur).className = 'ok';
      cur = k; if (li(k)) li(k).className = 'on'; var p = bar(0); setNow(text || (li(k) && li(k).textContent) || k, Math.round(p) + ' %');
    },
    progress: function (f, text, right) { if (failed || finished) return; lastMove = Date.now(); var p = bar(f); setNow(text, right != null ? right : Math.round(p) + ' %'); },
    indeterminate: function (text) { if (failed || finished) return; lastMove = Date.now(); if (root) q('.lbar').classList.add('ind'); setNow(text, ''); },
    done: function () {
      if (failed || finished) return; finished = true; L.finished = true; mount();
      STAGES.forEach(function (s) { if (li(s[0])) li(s[0]).className = 'ok'; });
      q('.lbar').classList.remove('ind'); q('.lbar i').style.width = '100%'; setNow('Ready', '100 %');
      setTimeout(function () { root.classList.add('gone'); setTimeout(function () { root.remove(); }, 400); }, 250);
    },
    fail: function (msg) {
      if (failed || finished) return; failed = true; L.failed = true; mount();
      var text = String(msg && msg.message || msg || 'Unknown error').replace(/^Uncaught (\w*Error: )?/, '');
      if (/^script error\.?$/i.test(text)) text = 'The twin\'s code stopped with an error the browser did not show in detail ("Script error.").';
      // name the file behind it: the last download that failed (wrong address, missing on this server, or a server error)
      if (badFiles.length) text += '\n\nFile that failed to load: ' + badFiles.slice(-3).map(function (b) { return rel(b.url) + ' (' + b.why + ')'; }).join(', ') + '.' +
        (badFiles.some(function (b) { return /HTTP 404/.test(b.why); }) && location.protocol !== 'file:' ? '\nIf the twin was opened through its own server, that server may be an old copy still running: close it (or restart Anatomy) and open the simulator again.' : '');
      else if (/JSON/.test(text)) text += '\n\nA data file came back as something other than JSON (usually an error page from the server).';
      console.error('[twin] could not start:', msg, badFiles);
      if (cur && li(cur)) li(cur).className = 'bad'; q('.lbar').classList.remove('ind'); q('.lbar').classList.add('bad'); setNow('Could not start', '');
      var e = q('.lerr'); e.style.display = 'block';
      e.textContent = text + '\n\nCheck your connection and try again. If it keeps failing, some of the twin\'s files are missing or out of date on this server: re-sync the project from the Anatomy app on your PC.';
      var b = document.createElement('button'); b.textContent = 'Try again'; b.onclick = function () { location.reload(); };
      e.appendChild(document.createElement('br')); e.appendChild(b); L.lastError = text;
    },
    // fetch with byte progress reported on the current (or given) stage
    fetch: function (url, opts) { return window.fetch(url, opts); },
    // register the assembled model (a three.js Object3D) so checks can see how it stands: TwinLoad.model(root, THREE)
    // (same as setting window.TwinModel = { object: root, THREE } yourself)
    model: function (obj, THREE) { window.TwinModel = { object: obj, THREE: THREE }; }
  };

  // ---- failures before the twin is up land on the error screen
  addEventListener('error', function (e) {
    if (finished) return; var t = e.target;
    if (t && t !== window && t.tagName) {
      if (t.tagName === 'SCRIPT') L.fail('Could not load ' + rel(t.src) + '.'); else console.warn('[twin] missing file:', t.href || t.src);
      return;
    }
    // "Script error." is all the browser says when it hides the details; give a real error (a rejected import or
    // promise usually follows within a moment) the chance to report first.
    var msg = (e.error && e.error.message) || e.message || '';
    if (!e.filename && (!msg || /^script error\.?$/i.test(msg))) { setTimeout(function () { L.fail(e.error || 'Script error.'); }, 400); return; }
    L.fail((e.error || msg || 'Script error') + (e.filename ? '\n(in ' + rel(e.filename) + (e.lineno ? ', line ' + e.lineno : '') + ')' : ''));
  }, true);
  addEventListener('unhandledrejection', function (e) { if (!finished) L.fail(e.reason); });
  var watchdog = setInterval(function () {
    if (finished || failed) return clearInterval(watchdog);
    if (inflight > 0 && Date.now() - lastMove < STALL * 2) return;      // a slow download still counts as progress
    if (Date.now() - lastMove > STALL) L.fail('The twin did not finish starting (no progress for ' + Math.round(STALL / 1000) + ' seconds while at: ' + ((li(cur) && li(cur).textContent) || 'starting') + ').');
  }, 1000);

  var base = document.baseURI, badFiles = [];
  function rel(u) { var b = base.replace(/[?#].*$/, '').replace(/[^/]*$/, ''); return String(u).indexOf(b) === 0 ? String(u).slice(b.length) : String(u); }

  // ---- count downloads the app makes while loading (fetch; three.js loaders use fetch)
  var inflight = 0, bytes = { data: [0, 0], model: [0, 0] };
  var MODEL = /\.(glb|gltf|stl|obj|3mf|bin|ply|fbx|drc|ktx2|hdr|exr)(\?|#|$)/i, CODE = /\.(m?js|css|html?)(\?|#|$)/i;
  var ofetch = window.fetch && window.fetch.bind(window);
  if (ofetch) window.fetch = function (input, init) {
    var url = typeof input === 'string' ? input : (input && input.url) || String(input);
    var abs; try { abs = new URL(url, base).href; } catch (e) { abs = url; }
    var p = ofetch(input, init);
    if (!finished && !failed) p.then(function (r) { if (!r.ok) badFiles.push({ url: abs, why: 'HTTP ' + r.status + (r.statusText ? ' ' + r.statusText : '') }); },
      function () { badFiles.push({ url: abs, why: 'network request failed' }); });
    if (finished || failed || booting) return p;
    var kind = MODEL.test(url) ? 'model' : CODE.test(url) ? null : 'data';
    if (!kind) return p;
    if (!cur || order[cur] <= order[kind]) L.stage(kind);
    inflight++;
    var B = bytes[kind];
    return p.then(function (r) {
      if (!r.ok || !r.body || !r.body.getReader || typeof ReadableStream === 'undefined') { inflight--; return r; }
      var tot = +r.headers.get('content-length') || 0; B[1] += tot; var got = 0;
      var name = rel(r.url || url).split('?')[0].split('/').pop();
      var rd = r.body.getReader();
      var stream = new ReadableStream({
        pull: function (c) {
          return rd.read().then(function (x) {
            if (x.done) { inflight--; if (!tot) B[1] += got; c.close(); return; }
            got += x.value.length; B[0] += x.value.length;
            if (cur === kind && !finished && !failed) L.progress(B[1] ? B[0] / Math.max(B[1], B[0]) : 0.5, (kind === 'model' ? 'Downloading the 3D model – ' : 'Loading design data – ') + name, kb(B[0]) + (B[1] ? ' / ' + kb(Math.max(B[1], B[0])) : ''));
            c.enqueue(x.value);
          }, function (e) { inflight--; c.error(e); });
        },
        cancel: function (why) { inflight--; return rd.cancel(why); }
      });
      return new Response(stream, { status: r.status, statusText: r.statusText, headers: r.headers });
    }, function (e) { inflight--; throw e; });
  };

  // ---- auto-finish for apps that never call TwinLoad.done(): a drawn canvas and a quiet network
  var started = false, quietSince = 0;
  function autoDone() {
    if (!AUTO_DONE || finished || failed) return;
    var c = null, a = 0; var cs = document.querySelectorAll('canvas');
    for (var i = 0; i < cs.length; i++) { var r = cs[i].getBoundingClientRect(); if (r.width * r.height > a) { a = r.width * r.height; c = cs[i]; } }
    if (started && c && a > 20000 && inflight === 0) {
      if (!quietSince) quietSince = Date.now();
      if (cur !== 'scene') L.stage('scene');
      if (Date.now() - quietSince > 1200) return L.done();
    } else quietSince = 0;
    setTimeout(autoDone, 300);
  }

  // ---- engine stage: walk the static import graph from data-entry with byte progress, then start it
  var booting = false;
  function importMap() {
    var s = document.querySelector('script[type="importmap"]'); var m = {};
    try { m = JSON.parse(s.textContent).imports || {}; } catch (e) {}
    return Object.keys(m).sort(function (a, b) { return b.length - a.length; }).map(function (k) { return [k, m[k]]; });
  }
  function resolve(spec, from) {
    if (/^(\.{0,2}\/|[a-z]+:)/i.test(spec)) return new URL(spec, from).href;
    var M = importMap();
    for (var i = 0; i < M.length; i++) { var k = M[i][0]; if (spec === k || (k.charAt(k.length - 1) === '/' && spec.indexOf(k) === 0)) return new URL(M[i][1] + spec.slice(k.length), base).href; }
    return null;                                                    // unknown bare specifier: the browser will report it
  }
  function importsOf(src) {
    var re = /^\s*(?:import|export)\b[^'"`;]*?from\s*['"]([^'"]+)['"]|^\s*import\s*['"]([^'"]+)['"]/gm, out = [], m;
    while ((m = re.exec(src))) out.push(m[1] || m[2]); return out;
  }
  function get(url, onBytes) {
    return ofetch(url).then(function (r) {
      if (!r.ok) throw new Error('Could not load ' + rel(url) + ' (HTTP ' + r.status + (r.statusText ? ' ' + r.statusText : '') + ').');
      var tot = +r.headers.get('content-length') || 0;
      if (!r.body || !r.body.getReader) return r.text().then(function (t) { onBytes(t.length, tot); return t; });
      var rd = r.body.getReader(), chunks = [], dec = new TextDecoder();
      return (function pump() { return rd.read().then(function (x) { if (x.done) { chunks.push(dec.decode()); return chunks.join(''); } onBytes(x.value.length, tot); chunks.push(dec.decode(x.value, { stream: true })); return pump(); }); })();
    }, function () { throw new Error('Could not load ' + rel(url) + ': the network request failed (offline, or the server refused it).'); });
  }
  function walk(entry) {
    var seen = {}, got = 0, total = 0;
    return new Promise(function (resolveAll, rejectAll) {
      var queue = [entry], active = 0, stopped = false;
      function next() {
        if (stopped) return;
        while (active < 6 && queue.length) {
          var u = queue.shift(); if (seen[u]) continue; seen[u] = 1; active++;
          (function (u) {
            var counted = false;
            get(u, function (n, tot) { if (!counted) { counted = true; total += tot; } got += n; L.progress(total ? got / Math.max(total, got) * Math.min(1, Object.keys(seen).length / (Object.keys(seen).length + queue.length + active)) : 0.3, 'Downloading the 3D engine and twin code – ' + rel(u).split('/').pop(), kb(got)); })
              .then(function (src) {
                importsOf(src).forEach(function (s) { var r = resolve(s, u); if (r && !seen[r]) queue.push(r); });
                active--; if (!queue.length && !active) resolveAll(); else next();
              }, function (err) { stopped = true; rejectAll(err); });
          })(u);
        }
        if (!queue.length && !active) resolveAll();
      }
      next();
    });
  }
  function start() {
    mount();
    if (location.protocol === 'file:' && ENTRY) return L.fail('This twin has to be opened from a web server, not straight from the file (browsers block ES modules on file:// pages). Open it from Anatomy on your PC or from the Anatomy Hub.');
    L.stage('engine');
    if (!ENTRY) { started = true; addEventListener('load', function () { autoDone(); }); return; }
    if (!HTMLScriptElement.supports || !HTMLScriptElement.supports('importmap')) return L.fail('This browser is too old for the twin (it needs ES modules and import maps). Use a current Chrome, Edge, Firefox or Safari.');
    booting = true;
    var entry = new URL(ENTRY, base).href;
    walk(entry).then(function () {
      booting = false;
      L.stage('data', 'Starting the twin code…');
      // import() rather than a <script type=module>: a failure then arrives as the real Error (message, file),
      // not as the browser's muted "Script error.".
      if (window.TWIN_NO_IMPORT !== true) {
        // a module whose top level keeps awaiting (e.g. a live loop) never settles: start watching for the drawn scene anyway
        setTimeout(function () { if (!started && !failed) { started = true; autoDone(); } }, 3000);
        import(entry).then(function () { if (!started) { started = true; autoDone(); } }, function (e) {
          L.fail(e && e.message ? e.message + (e.stack && /\.m?js:\d+/.test(e.stack) ? '\n(in ' + rel((e.stack.match(/(https?:[^\s)]+\.m?js):(\d+)/) || [, ''])[1]) + ')' : '') : e);
        });
      } else {
        var s = document.createElement('script'); s.type = 'module'; s.src = ENTRY;
        s.onerror = function () { L.fail('The twin code (' + ENTRY + ' or one of the files it imports) failed to load.'); };
        s.onload = function () { started = true; autoDone(); };
        document.body.appendChild(s);
      }
    }, function (e) { booting = false; L.fail(e); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
