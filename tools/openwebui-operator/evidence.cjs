'use strict';

const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const ROOT = path.resolve(__dirname, '..', '..');
const EVIDENCE_ROOT = path.join(ROOT, 'runtime', 'evidence', 'openwebui-operator');

function runId() {
  const stamp = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 17);
  return `openwebui-operator-${stamp}-${crypto.randomBytes(4).toString('hex')}`;
}

function makeEvidence(run) {
  const dir = path.join(EVIDENCE_ROOT, run);
  fs.mkdirSync(path.join(dir, 'screenshots'), {recursive: true});
  return {run, dir, screenshots: path.join(dir, 'screenshots')};
}

function writeJson(file, value) {
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n', 'utf8');
}

function safePath(urlValue) {
  try {
    const u = new URL(urlValue);
    return `${u.origin}${u.pathname}`;
  } catch {
    return String(urlValue || '').replace(/[?].*$/, '');
  }
}

function sanitizeNetwork(entry) {
  return {
    timestamp: entry.timestamp || new Date().toISOString(),
    method: entry.method,
    url: safePath(entry.url),
    status: entry.status,
    failure: entry.failure
  };
}

function writeCompletion(evidence, manifest) {
  writeJson(path.join(evidence.dir, 'manifest.json'), manifest);
  fs.writeFileSync(path.join(evidence.dir, 'completion.marker'),
    `ESTATE_OPENWEBUI_OPERATOR_COMPLETE\n${new Date().toISOString()}\n`, 'utf8');
}

module.exports = {ROOT, EVIDENCE_ROOT, runId, makeEvidence, writeJson, safePath, sanitizeNetwork, writeCompletion};
