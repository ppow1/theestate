'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {matchesExpectation, loadScenario} = require('../tools/openwebui-operator/scenario.cjs');
const {safePath, sanitizeNetwork} = require('../tools/openwebui-operator/evidence.cjs');
const {compareCmeClaim} = require('../tools/openwebui-operator/ground_truth.cjs');
const {defaultProfilePath, selectedProfilePath, resolveProfilePath, PROFILE_ID, AUTH_BOOTSTRAP_COMMAND, AUTH_BOOTSTRAP_PRIVACY, authBootstrapOutcome} = require('../tools/openwebui_operator_acceptance.cjs');
const {canonicalProfilePath, PROFILE_ENV} = require('../tools/openwebui-operator/profile.cjs');
const {emitOperatorAttention, readEvents} = require('../tools/openwebui-operator/operator-attention.cjs');

test('auth bootstrap and normal acceptance share the same default profile', () => {
  assert.equal(defaultProfilePath(), canonicalProfilePath());
  assert.equal(selectedProfilePath({}), defaultProfilePath());
  assert.match(AUTH_BOOTSTRAP_COMMAND, /auth-bootstrap/);
});

test('profile resolution is independent of worktree roots and stays outside repositories', () => {
  const env = {LOCALAPPDATA: 'C:\\Users\\test\\AppData\\Local'};
  const first = canonicalProfilePath(env, 'win32');
  const second = canonicalProfilePath(env, 'win32');
  assert.equal(first, second);
  assert.equal(first, 'C:\\Users\\test\\AppData\\Local\\TheEstate\\browser\\openwebui-operator-profile');
  assert.equal(first.startsWith('A:\\theestate'), false);
  assert.equal(first.includes('theestate-ec-000221'), false);
});

test('explicit profile and environment override precedence are deterministic', () => {
  const env = {LOCALAPPDATA: 'C:\\Users\\test\\AppData\\Local', [PROFILE_ENV]: 'D:\\EstateState\\operator'};
  assert.equal(resolveProfilePath(undefined, env, 'win32'), 'D:\\EstateState\\operator');
  assert.equal(resolveProfilePath('E:\\Explicit\\operator', env, 'win32'), 'E:\\Explicit\\operator');
});

test('profile evidence is symbolic and never exposes the machine path', () => {
  const env = {LOCALAPPDATA: 'C:\\Users\\test\\AppData\\Local'};
  const evidence = require('../tools/openwebui-operator/profile.cjs').profileEvidence(undefined, env, 'win32');
  assert.equal(evidence.profile_id, PROFILE_ID);
  assert.equal(JSON.stringify(evidence).includes('C:\\Users'), false);
  assert.equal(JSON.stringify(evidence).includes('cookie'), false);
});

test('auth bootstrap privacy disables credential-bearing evidence', () => {
  assert.deepEqual(AUTH_BOOTSTRAP_PRIVACY, {
    capture_console: false, capture_network: false, tracing: false, screenshots: false, credentials_persisted: false
  });
});

test('auth bootstrap outcomes distinguish success, timeout, and cancellation', () => {
  assert.equal(authBootstrapOutcome({authenticated: true, readinessResult: {status: 'OPENWEBUI_READY'}}).classification, 'AUTH_BOOTSTRAP_COMPLETE');
  assert.equal(authBootstrapOutcome({timedOut: true}).classification, 'AUTH_BOOTSTRAP_TIMEOUT');
  assert.equal(authBootstrapOutcome({cancelled: true}).classification, 'AUTH_BOOTSTRAP_CANCELLED');
});

test('LOGIN_REQUIRED attention is deduplicated and resolves without secrets', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'estate-attention-'));
  const required = emitOperatorAttention({root, runId: 'run-1', url: 'http://127.0.0.1:8081/auth?token=secret'});
  const duplicate = emitOperatorAttention({root, runId: 'run-1', url: 'http://127.0.0.1:8081/auth?token=secret'});
  const resolved = emitOperatorAttention({root, runId: 'run-1', url: 'http://127.0.0.1:8081', status: 'resolved'});
  const events = readEvents(root);
  assert.equal(required.duplicate, false);
  assert.equal(duplicate.duplicate, true);
  assert.equal(events.length, 2);
  assert.equal(events[0].event_type, 'Operator Attention Required');
  assert.equal(events[1].event_type, 'Operator Attention Resolved');
  assert.equal(events[0].metadata.surface, 'http://127.0.0.1:8081/auth');
  assert.equal(JSON.stringify(events).includes('secret'), false);
  assert.equal(resolved.event.metadata.status, 'resolved');
});

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
