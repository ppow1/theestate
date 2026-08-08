'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {matchesExpectation, loadScenario} = require('../tools/openwebui-operator/scenario.cjs');
const {safePath, sanitizeNetwork} = require('../tools/openwebui-operator/evidence.cjs');
const {compareCmeClaim} = require('../tools/openwebui-operator/ground_truth.cjs');

test('scenario expectations are semantic and bounded', () => {
  assert.equal(matchesExpectation('CME is IDLE and healthy', {contains_any: ['IDLE']}).passed, true);
  assert.equal(matchesExpectation('CME is IDLE', {contains_all: ['PROCESSING']}).passed, false);
  assert.equal(matchesExpectation('CME is IDLE', {not_contains: ['FAILED']}).passed, true);
});

test('scenario parser accepts YAML and rejects missing turns', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'estate-openwebui-'));
  const file = path.join(dir, 'scenario.yaml');
  fs.writeFileSync(file, 'name: smoke\nresident: Grace\nturns:\n  - send: Hello\n', 'utf8');
  assert.equal(loadScenario(file).turns[0].send, 'Hello');
  fs.writeFileSync(file, 'name: broken\nresident: Grace\n', 'utf8');
  assert.throws(() => loadScenario(file), /requires turns/);
});

test('network evidence removes query strings and sensitive request detail', () => {
  assert.equal(safePath('http://127.0.0.1:8080/api/chat?token=secret'), 'http://127.0.0.1:8080/api/chat');
  const record = sanitizeNetwork({method: 'POST', url: 'http://x/chat?secret=1', status: 500});
  assert.equal(record.method, 'POST');
  assert.equal(record.url, 'http://x/chat');
  assert.equal(record.status, 500);
  assert.match(record.timestamp, /T/);
});

test('ground truth comparison is read-only and fails closed when unknown', () => {
  assert.equal(compareCmeClaim('The current state is IDLE', {state: 'IDLE', source: 'fixture'}).passed, true);
  assert.equal(compareCmeClaim('The current state is IDLE', {state: 'UNKNOWN', source: null}).passed, false);
});
