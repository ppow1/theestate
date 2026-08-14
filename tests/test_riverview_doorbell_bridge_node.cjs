const test = require('node:test');
const assert = require('node:assert/strict');
const { FIXED_WAKE_TEXT, OPERATION, selectExactTarget, validateInput } = require('../tools/riverview_doorbell_bridge.cjs');

const conversationId = '00000000-0000-4000-8000-000000000000';
const page = id => ({ type: 'page', url: `https://chatgpt.com/c/${id}`, webSocketDebuggerUrl: 'ws://local' });

test('exact target selection accepts one configured conversation only', () => {
  assert.equal(selectExactTarget([page(conversationId)], conversationId).url, page(conversationId).url);
  assert.throws(() => selectExactTarget([], conversationId), /RIV-PLY-0005/);
  assert.throws(() => selectExactTarget([page(conversationId), page(conversationId)], conversationId), /RIV-PLY-0006/);
  assert.throws(() => selectExactTarget([page('11111111-1111-4111-8111-111111111111')], conversationId), /RIV-PLY-0005/);
});

test('public input contains no browser instruction fields', () => {
  const valid = { operation: OPERATION, request_id: conversationId, correlation_id: '11111111-1111-4111-8111-111111111111', timeout_seconds: 30 };
  assert.doesNotThrow(() => validateInput(valid));
  assert.throws(() => validateInput({ ...valid, prompt: FIXED_WAKE_TEXT }), /unsupported fields/);
  assert.throws(() => validateInput({ ...valid, selector: '#composer' }), /unsupported fields/);
});
