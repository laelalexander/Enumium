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
const label = m => NAMES[m] || m;

function statusFile(root) { return path.join(root, '.anatomy', 'models.json'); }
function readStatus(root) {
  try { return JSON.parse(fs.readFileSync(statusFile(root), 'utf8').replace(/^﻿/, '')); } catch { return {}; }
}
function writeStatus(root, st) {
  try { fs.mkdirSync(path.dirname(statusFile(root)), { recursive: true }); fs.writeFileSync(statusFile(root), JSON.stringify(st, null, 2)); } catch {}
}

// Preferred model first, then the rest of the default chain, no repeats.
function chainFor(preferred) {
  const p = ALIASES[preferred] || preferred;
  const out = [];
  for (const m of [p, ...DEFAULT_CHAIN]) if (m && !out.includes(m)) out.push(m);
  return out;
}

// First model in the chain that hasn't failed recently (or the preferred one if all have).
function pickModel(root, preferred, exclude = []) {
  const st = readStatus(root), now = Date.now();
  const chain = chainFor(preferred).filter(m => !exclude.includes(m));
  return chain.find(m => !(st[m] && st[m].until > now)) || chain[0] || null;
}

function markUnavailable(root, model, reason) {
  const st = readStatus(root);
  st[model] = { until: Date.now() + SKIP_MS, reason, at: new Date().toISOString() };
  writeStatus(root, st);
}
function markOk(root, model) {
  const st = readStatus(root);
  if (st[model]) { delete st[model]; writeStatus(root, st); }
}

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

function continuePrompt(from, to) {
  return `Continue the anatomy run exactly where it stopped. ${label(from)} became unavailable, so you are now running on ${label(to)}. ` +
    'Check which steps and background agents did not finish (some may have failed with an API error) and redo them. ' +
    'Keep the same quality bar and do not repeat work that is already saved in this folder.';
}

module.exports = { chainFor, pickModel, markUnavailable, markOk, RunWatch, friendlyError, reasonText, continuePrompt, label };
