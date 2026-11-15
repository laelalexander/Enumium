// Model fallback chain for Anatomy runs.
//
// A run starts on the project's preferred model. If Claude Code reports that the
// model can't be used right now (usage credits used up, model not recognised by
// this Claude Code version, no access), the server resumes the same session on
// the next model in the chain, so the run carries on instead of stopping.
// Models that failed this way are skipped for a few hours, so new runs don't
// spend a failed request on them first.
//
// Override the chain with ANATOMY_MODELS="claude-fable-5-2,claude-opus-5-5,sonnet".
'use strict';

const fs = require('fs');
const path = require('path');

const DEFAULT_CHAIN = (process.env.ANATOMY_MODELS || 'claude-fable-5-2,claude-opus-5-5,opus,claude-sonnet-5-5,sonnet')
  .split(',').map(s => s.trim()).filter(Boolean);
const ALIASES = { fable: 'claude-fable-5-2' };
const SKIP_MS = 6 * 3600 * 1000;

const NAMES = { 'claude-fable-5-2': 'Fable 5.2', 'claude-opus-5-5': 'Opus 5.5', 'claude-sonnet-5-5': 'Sonnet 5.5',
  'claude-haiku-5-5': 'Haiku 5.5', opus: 'Opus', sonnet: 'Sonnet', haiku: 'Haiku' };
const isLocal = m => /^ollama:/.test(m || '');
const label = m => isLocal(m) ? m.slice(7) + ' (local)' : (NAMES[m] || m);
const OLLAMA = process.env.OLLAMA_HOST ? (/^https?:/.test(process.env.OLLAMA_HOST) ? process.env.OLLAMA_HOST : 'http://' + process.env.OLLAMA_HOST) : 'http://127.0.0.1:11434';

// User choices from Settings > Models: { localFallback: bool, localModel: 'qwen3:14b' }
function settingsFile(root) { return path.join(root, '.anatomy', 'model-settings.json'); }
function readSettings(root) {
  try { return { localFallback: false, localModel: '', ...JSON.parse(fs.readFileSync(settingsFile(root), 'utf8').replace(/^\uFEFF/, '')) }; }
  catch { return { localFallback: false, localModel: '' }; }
}
function writeSettings(root, v) {
  const cur = readSettings(root);
  const next = { localFallback: !!(v.localFallback ?? cur.localFallback), localModel: String(v.localModel ?? cur.localModel ?? '') };
  fs.mkdirSync(path.dirname(settingsFile(root)), { recursive: true });
  fs.writeFileSync(settingsFile(root), JSON.stringify(next, null, 2));
  return next;
}

// Models installed in Ollama on this PC, or null when Ollama isn't running.
async function ollamaModels() {
  try {
    const ctl = new AbortController(); const t = setTimeout(() => ctl.abort(), 2000);
    const r = await fetch(OLLAMA + '/api/tags', { signal: ctl.signal }); clearTimeout(t);
    const j = await r.json();
    return (j.models || []).map(m => ({ id: 'ollama:' + m.name, name: m.name, size: m.size,
      params: m.details && m.details.parameter_size, family: m.details && m.details.family }));
  } catch { return null; }
}

// Claude Code talks to Ollama through Ollama's Anthropic-compatible API. Every model slot
// (main, fast helper, subagents) points at the local model, since Ollama has no Claude models.
function applyLocalEnv(env, model) {
  const name = model.slice(7);
  Object.assign(env, { ANTHROPIC_BASE_URL: OLLAMA, ANTHROPIC_AUTH_TOKEN: 'ollama', ANTHROPIC_API_KEY: '',
    ANTHROPIC_DEFAULT_OPUS_MODEL: name, ANTHROPIC_DEFAULT_SONNET_MODEL: name, ANTHROPIC_DEFAULT_HAIKU_MODEL: name,
    ANTHROPIC_SMALL_FAST_MODEL: name, CLAUDE_CODE_SUBAGENT_MODEL: name, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1' });
  return env;
}
function cliModel(model) { return isLocal(model) ? model.slice(7) : model; }

// Snapshot for Settings > Models.
async function overview(root) {
  const st = readStatus(root), now = Date.now();
  const claude = [...new Set(DEFAULT_CHAIN.map(m => ALIASES[m] || m))].filter(m => /^claude-/.test(m)).map(m => {
    const s = st[m] && st[m].until > now ? st[m] : null;
    return { id: m, label: label(m), status: s ? 'skipped' : 'ready', until: s ? new Date(s.until).toISOString() : null, reason: s ? s.reason : null };
  });
  const local = await ollamaModels();
  return { claude, local: local ? local.map(m => ({ ...m, label: label(m.id),
    status: st[m.id] && st[m.id].until > now ? 'skipped' : 'ready' })) : null, settings: readSettings(root) };
}

function statusFile(root) { return path.join(root, '.anatomy', 'models.json'); }
function readStatus(root) {
  try { return JSON.parse(fs.readFileSync(statusFile(root), 'utf8').replace(/^﻿/, '')); } catch { return {}; }
}
function writeStatus(root, st) {
  try { fs.mkdirSync(path.dirname(statusFile(root)), { recursive: true }); fs.writeFileSync(statusFile(root), JSON.stringify(st, null, 2)); } catch {}
}

// Preferred model first, then the rest of the default chain, no repeats.
// A local model is added last, only when the user turned that on in Settings.
function chainFor(preferred, root) {
  const p = ALIASES[preferred] || preferred;
  const out = [];
  const set = root ? readSettings(root) : {};
  const tail = set.localFallback && set.localModel ? ['ollama:' + set.localModel] : [];
  for (const m of [p, ...DEFAULT_CHAIN, ...tail]) if (m && !out.includes(m)) out.push(m);
  return out;
}

// First model in the chain that hasn't failed recently (or the preferred one if all have).
function pickModel(root, preferred, exclude = []) {
  const st = readStatus(root), now = Date.now();
  const chain = chainFor(preferred, root).filter(m => !exclude.includes(m));
  return chain.find(m => !(st[m] && st[m].until > now)) || chain[0] || null;
}

function markUnavailable(root, model, reason, resetsAt) {
  const st = readStatus(root);
  const reset = resetsAt ? resetsAt * (resetsAt < 1e12 ? 1000 : 1) : 0;
  st[model] = { until: Math.max(Date.now() + SKIP_MS, Math.min(reset, Date.now() + 7 * 864e5)), reason, at: new Date().toISOString() };
  writeStatus(root, st);
}
function markOk(root, model) {
  const st = readStatus(root);
  if (st[model]) { delete st[model]; writeStatus(root, st); }
}
const clearSkip = markOk;

// Tracks the stream of one run and decides why it failed.
class RunWatch {
  constructor() { this.resultErr = ''; this.apiError = ''; this.status = 0; this.resetsAt = 0; this.gotAnswer = false; }
  see(ev) {
    if (ev.type === 'rate_limit_event' && ev.rate_limit_info) {
      const info = ev.rate_limit_info;
      const ts = [info.resetsAt, ...Object.values(info.unifiedWindows || {}).map(w => w && w.resetsAt)].filter(Boolean);
      if (info.status === 'rejected' && ts.length) this.resetsAt = Math.min(...ts);
    }
    if (ev.type === 'assistant' && ev.message && ev.message.model && ev.message.model !== '<synthetic>') this.gotAnswer = true;
    if (ev.type === 'result') {
      if (ev.api_error) this.apiError = String(ev.api_error);
      if (ev.api_error_status) this.status = ev.api_error_status;
      if (ev.is_error || ev.terminal_reason === 'api_error' || ev.subtype !== 'success') {
        this.resultErr = String(ev.result || (ev.errors || []).join('\n') || ev.subtype || '').trim();
      }
    }
  }
  // 'model'  : this model can't be used now, another one may work -> fall back
  // 'plan'   : the whole plan's limit is reached, every model is blocked
  // 'auth'   : needs sign-in
  // 'other'  : anything else
  kind(errTail) {
    const t = [this.apiError, this.resultErr, errTail].join('\n');
    if (/model_requires_usage_credits|spend limit|usage credits|switch to another model|unrecognized_model|model[^\n]{0,40}(not (found|available|supported)|unavailable|invalid)|invalid model|not_found_error|does not have access/i.test(t) || this.status === 404) return 'model';
    if (/session limit|weekly limit|usage limit|rate.?limit|429|resets/i.test(t)) return 'plan';
    if (/not logged in|log ?in|sign ?in|authenticat|oauth|401/i.test(t)) return 'auth';
    return 'other';
  }
  resetText() {
    if (!this.resetsAt) return '';
    const d = new Date(this.resetsAt * (this.resetsAt < 1e12 ? 1000 : 1));
    return d.toLocaleString(undefined, { weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  }
}

function reasonText(kind, model) {
  if (kind === 'model') return `${label(model)} can't be used right now (its usage credits are used up, or this Claude Code version doesn't support it)`;
  if (kind === 'plan') return `Your Claude plan's usage limit is reached`;
  return `${label(model)} stopped with an error`;
}

// The message shown when the run can't carry on. Raw details go separately.
function friendlyError(kind, watch, tried) {
  const when = watch.resetText();
  if (kind === 'model' || kind === 'plan') {
    return (tried.length > 1 ? `Anatomy tried ${tried.map(label).join(', then ')}, and none can run right now.` :
      `Your Claude usage limit is reached for ${label(tried[0])}.`) +
      (when ? ` The limit resets ${when}.` : ' It resets automatically.') +
      ' To keep going sooner, add usage credits at claude.ai/settings/usage.' +
      ' Nothing is lost: open this project and send "continue" to pick up where it stopped.';
  }
  if (kind === 'auth') return 'Claude Code needs you to sign in again. Click "Sign in" at the top of the window.';
  return 'The run stopped because of an error in Claude Code. Send "continue" to try again from where it stopped.';
}

function continuePrompt(from, to, why) {
  const local = isLocal(to) ? ' You are a local model with less capacity: do only light steps (research notes, summaries, BOM tidying, documentation, checking files). ' +
    'Do not produce CAD, drawings, PCB layouts or engineering calculations; list those as waiting for Claude in a file named WAITING-FOR-CLAUDE.md and stop when only such steps remain.' : '';
  return `Continue the anatomy run exactly where it stopped. ${why || `${label(from)} became unavailable`}, so you are now running on ${label(to)}.${local} ` +
    'Check which steps and background agents did not finish (some may have failed with an API error) and redo them. ' +
    'Keep the same quality bar and do not repeat work that is already saved in this folder.';
}

module.exports = { isLocal, cliModel, applyLocalEnv, ollamaModels, overview, readSettings, writeSettings, clearSkip, chainFor, pickModel, markUnavailable, markOk, RunWatch, friendlyError, reasonText, continuePrompt, label };
