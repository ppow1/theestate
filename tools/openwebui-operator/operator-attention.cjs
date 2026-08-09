'use strict';

const fs = require('node:fs');
const path = require('node:path');

const EVENT_TYPES = Object.freeze({required: 'Operator Attention Required', resolved: 'Operator Attention Resolved', timed_out: 'Operator Attention Timed Out', cancelled: 'Operator Attention Cancelled'});

function safeUrl(value) {
  try { const u = new URL(value); return `${u.origin}${u.pathname}`; }
  catch { return String(value || '').replace(/[?].*$/, ''); }
}

function eventPath(root, date = new Date().toISOString().slice(0, 10)) {
  return path.join(root, 'runtime', 'operations', 'events', `${date}.jsonl`);
}

function readEvents(root) {
  const dir = path.join(root, 'runtime', 'operations', 'events');
  if (!fs.existsSync(dir)) return [];
  const events = [];
  for (const file of fs.readdirSync(dir).filter(name => name.endsWith('.jsonl'))) {
    for (const line of fs.readFileSync(path.join(dir, file), 'utf8').split(/\r?\n/)) {
      if (!line.trim()) continue;
      try { const event = JSON.parse(line); if (event.metadata?.operator_attention) events.push(event); } catch { /* malformed operational records remain non-fatal */ }
    }
  }
  return events;
}

function emitOperatorAttention({root, runId, url, profilePath = 'runtime/browser/openwebui-operator-profile', status = 'required', timestamp = new Date().toISOString()}) {
  if (!EVENT_TYPES[status]) throw new Error(`unsupported operator attention status: ${status}`);
  const eventId = `ope-openwebui-auth-${runId}-${status}`;
  const existing = readEvents(root).find(event => event.event_id === eventId);
  if (existing) return {event: existing, duplicate: true};
  const event = {
    event_id: eventId,
    event_type: EVENT_TYPES[status],
    state: status === 'required' ? 'Waiting' : status === 'resolved' ? 'Completed' : status === 'cancelled' ? 'Cancelled' : 'Deferred',
    created_at: timestamp,
    classification: 'Estate Internal',
    message: status === 'required' ? 'Operator authentication required for Grace Open WebUI acceptance.' : `Open WebUI operator authentication ${status.replace('_', ' ')}.`,
    updated_at: null,
    requires_attention: status === 'required',
    artifact_paths: [],
    metadata: {
      operator_attention: true,
      attention_type: 'operator_attention_required',
      reason: 'OPENWEBUI_AUTHENTICATION_REQUIRED',
      source: 'Open WebUI Playwright operator acceptance',
      run_id: runId,
      surface: safeUrl(url),
      profile_path: profilePath,
      required_operator_action: status === 'required' ? 'Authenticate in the headed Estate Chromium window.' : null,
      status,
      summary_safe: true
    }
  };
  const file = eventPath(root, timestamp.slice(0, 10));
  fs.mkdirSync(path.dirname(file), {recursive: true});
  fs.appendFileSync(file, JSON.stringify(event) + '\n', 'utf8');
  return {event, duplicate: false};
}

module.exports = {EVENT_TYPES, safeUrl, readEvents, emitOperatorAttention};
