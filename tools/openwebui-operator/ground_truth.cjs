'use strict';

const fs = require('node:fs');
const path = require('node:path');

function readJsonIfPresent(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return null; }
}

function readCmeState(root = path.resolve(__dirname, '..', '..')) {
  const candidates = [
    path.join(root, 'runtime', 'cme', 'owner-state.json'),
    'A:/theestate-data/chatgpt-mailbox-worker/cme-owner-state.json',
    'A:/theestate-data/cme-owner-state.json'
  ];
  for (const file of candidates) {
    const value = readJsonIfPresent(file);
    if (value) return {source: file, state: value.state || value.status || value.process_state || 'UNKNOWN', raw: value};
  }
  return {source: null, state: 'UNKNOWN', raw: null};
}

function compareCmeClaim(answer, truth = readCmeState()) {
  const states = ['IDLE', 'PROCESSING', 'STOPPED', 'AUTHORITATIVE_COMPLETE', 'EMPTY_QUEUE'];
  const mentioned = states.filter(s => new RegExp(`\\b${s}\\b`, 'i').test(answer || ''));
  return {authoritative: truth.state, source: truth.source, mentioned, passed: truth.state !== 'UNKNOWN' && mentioned.includes(String(truth.state).toUpperCase())};
}

module.exports = {readCmeState, compareCmeClaim};
