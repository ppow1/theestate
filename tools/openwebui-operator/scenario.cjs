'use strict';

const fs = require('node:fs');
const path = require('node:path');
const YAML = require('yaml');

function loadScenario(file) {
  const source = fs.readFileSync(path.resolve(file), 'utf8');
  const value = path.extname(file).toLowerCase() === '.json' ? JSON.parse(source) : YAML.parse(source);
  if (!value || typeof value !== 'object') throw new Error('Scenario must be an object');
  if (!value.name) throw new Error('Scenario requires name');
  if (!value.resident) throw new Error('Scenario requires resident');
  if (!Array.isArray(value.turns) || value.turns.length === 0) throw new Error('Scenario requires turns');
  for (const [i, turn] of value.turns.entries()) {
    if (!turn || typeof turn.send !== 'string' || !turn.send.trim()) throw new Error(`Turn ${i + 1} requires send text`);
  }
  return value;
}

function matchesExpectation(text, expect = {}) {
  const normalized = String(text || '').toLowerCase();
  const any = (expect.contains_any || []).map(String).some(x => normalized.includes(x.toLowerCase()));
  const all = (expect.contains_all || []).map(String).every(x => normalized.includes(x.toLowerCase()));
  const absent = (expect.not_contains || []).map(String).every(x => !normalized.includes(x.toLowerCase()));
  return {passed: (!expect.contains_any || any) && all && absent, contains_any: any, contains_all: all, not_contains: absent};
}

module.exports = {loadScenario, matchesExpectation};
