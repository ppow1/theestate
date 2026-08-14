// Estate-owned bounded Riverview doorbell bridge.
// Version: 1.0.0 | 2026-08-14
//
// This is the only Estate browser operation exposed to Riverview.  It owns
// the fixed target, fixed wake text, and fixed DOM interaction.  It accepts
// no prompt, selector, URL, script, navigation, or page-content input.

const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const BRIDGE_VERSION = '1.0.0';
const OPERATION = 'ring_riverview_doorbell';
const FIXED_WAKE_TEXT = 'Riverview doorbell v1: inspect the Riverview MCP mailbox.';
const DEFAULT_CONFIG = 'A:\\theestate-data\\chatgpt-mailbox-worker\\riverview-doorbell.json';
const DEFAULT_JOURNAL = 'A:\\theestate-data\\chatgpt-mailbox-worker\\riverview-doorbell-evidence.json';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function configPath() { return process.env.RIVERVIEW_DOORBELL_CONFIG || DEFAULT_CONFIG; }
function journalPath() { return process.env.RIVERVIEW_DOORBELL_JOURNAL || DEFAULT_JOURNAL; }
function now() { return new Date().toISOString(); }
function targetRef(id) { return `target-sha256:${crypto.createHash('sha256').update(id).digest('hex')}`; }
function safeResult(input, status, failureClass, evidenceRef, startedAt, completedAt, attemptId) {
  return { attempt_id: attemptId, request_id: input.request_id, correlation_id: input.correlation_id,
    bridge_version: BRIDGE_VERSION, designated_target_ref: input.target_ref, started_at: startedAt,
    completed_at: completedAt, status, failure_class: failureClass || null, evidence_ref: evidenceRef || null };
}
function fail(input, failureClass, startedAt, attemptId) {
  return safeResult(input, 'failed', failureClass, null, startedAt, now(), attemptId);
}
function readJson(file, fallback) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch (error) {
    if (error.code === 'ENOENT') return fallback;
    throw error;
  }
}
function writeJsonAtomic(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, `${JSON.stringify(value, null, 2)}\n`, { encoding: 'utf8', flag: 'wx' });
  fs.renameSync(tmp, file);
}
function loadConfig() {
  const config = readJson(configPath(), null);
  if (!config || typeof config.conversation_id !== 'string' || !/^[0-9a-f-]{36}$/i.test(config.conversation_id)) {
    throw new Error('RIV-PLY-0002: designated target configuration missing or invalid');
  }
  return { conversation_id: config.conversation_id.toLowerCase() };
}
function validateInput(input) {
  if (!input || input.operation !== OPERATION) throw new Error('RIV-PLY-0002: operation denied');
  const keys = Object.keys(input).sort().join(',');
  if (keys !== 'correlation_id,operation,request_id,timeout_seconds') throw new Error('RIV-PLY-0002: bridge input contains unsupported fields');
  if (!UUID.test(input.request_id) || !UUID.test(input.correlation_id)) throw new Error('RIV-PLY-0002: request identity is invalid');
  if (!Number.isInteger(input.timeout_seconds) || input.timeout_seconds < 1 || input.timeout_seconds > 120) throw new Error('RIV-PLY-0002: timeout is outside the bounded range');
}
async function listExactTarget(conversationId) {
  const response = await fetch('http://127.0.0.1:9224/json/list');
  if (!response.ok) throw new Error('RIV-PLY-0003: CDP target listing unavailable');
  return selectExactTarget(await response.json(), conversationId);
}
function selectExactTarget(targets, conversationId) {
  const pages = targets.filter(item => {
    try { return item.type === 'page' && new URL(item.url).pathname === `/c/${conversationId}` && item.webSocketDebuggerUrl; }
    catch { return false; }
  });
  if (pages.length === 0) throw new Error('RIV-PLY-0005: designated target absent');
  if (pages.length > 1) throw new Error('RIV-PLY-0006: designated target is ambiguous');
  return pages[0];
}
function cdp(target, timeoutMs) {
  const ws = new WebSocket(target.webSocketDebuggerUrl); let nextId = 0; const pending = new Map();
  ws.onmessage = event => { const message = JSON.parse(event.data); const waiter = pending.get(message.id); if (!waiter) return; pending.delete(message.id); message.error ? waiter.reject(new Error(message.error.message)) : waiter.resolve(message.result); };
  const opened = new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = () => reject(new Error('RIV-PLY-0004: authenticated session unavailable')); });
  const call = (method, params = {}) => new Promise((resolve, reject) => { const id = ++nextId; const timer = setTimeout(() => { pending.delete(id); reject(new Error('RIV-PLY-0009: browser interaction timed out')); }, timeoutMs); pending.set(id, { resolve: value => { clearTimeout(timer); resolve(value); }, reject: error => { clearTimeout(timer); reject(error); } }); try { ws.send(JSON.stringify({ id, method, params })); } catch (error) { clearTimeout(timer); pending.delete(id); reject(error); } });
  return { ws, opened, call };
}
const READINESS_SCRIPT = `(()=>{const b=document.body?.innerText||'';const blocked=/log in|sign in|verify you are human|captcha|something went wrong/i.test(b);const e=document.querySelector('#prompt-textarea[contenteditable="true"],div[contenteditable="true"][aria-label="Chat with ChatGPT"]');const r=e?.getBoundingClientRect?.();return {authenticated:!blocked,composer:!!e&&!!r&&r.width>0&&r.height>0&&!e.disabled};})()`;
const RING_SCRIPT = `(()=>{const input=document.querySelector('#prompt-textarea[contenteditable="true"],div[contenteditable="true"][aria-label="Chat with ChatGPT"]');if(!input)return 'composer_unavailable';input.focus();input.replaceChildren();const p=document.createElement('p');p.textContent=${JSON.stringify(FIXED_WAKE_TEXT)};input.appendChild(p);input.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:${JSON.stringify(FIXED_WAKE_TEXT)}}));const form=input.closest('form');const button=form?.querySelector('button[type="submit"],button[aria-label*="Send" i],button[aria-label*="Submit" i]');if(button&&!button.disabled){button.click();return 'submitted';}input.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));return 'submitted';})()`;
async function preflight() {
  const result = { bridge_version: BRIDGE_VERSION, operation: OPERATION, browser_runtime: false, cdp_available: false, authenticated_session: false, designated_target_configured: false, exact_target_resolvable: false, fixed_action_available: true, ready: false };
  let config; try { config = loadConfig(); result.designated_target_configured = true; } catch { return result; }
  try { const target = await listExactTarget(config.conversation_id); result.browser_runtime = true; result.cdp_available = true; result.exact_target_resolvable = !!target; const connection = cdp(target, 5000); await connection.opened; const probe = await connection.call('Runtime.evaluate', { returnByValue: true, expression: READINESS_SCRIPT }); result.authenticated_session = probe?.result?.value?.authenticated === true && probe?.result?.value?.composer === true; connection.ws.close(); } catch { /* metadata-only fail-closed result */ }
  result.ready = Object.values(result).every((value, index) => index < 0 || value) && result.designated_target_configured && result.exact_target_resolvable && result.authenticated_session;
  return result;
}
async function ring(input) {
  validateInput(input); const startedAt = now(); const attemptId = crypto.randomUUID(); const config = loadConfig(); input.target_ref = targetRef(config.conversation_id);
  const journal = readJson(journalPath(), {}); const prior = journal[`${input.request_id}:${input.correlation_id}`];
  if (prior && prior.status === 'succeeded') return { ...prior, status: 'already_succeeded' };
  const target = await listExactTarget(config.conversation_id); const connection = cdp(target, input.timeout_seconds * 1000); await connection.opened;
  const probe = await connection.call('Runtime.evaluate', { returnByValue: true, expression: READINESS_SCRIPT });
  if (probe?.result?.value?.authenticated !== true) throw new Error('RIV-PLY-0004: authentication/session check failed');
  if (probe?.result?.value?.composer !== true) throw new Error('RIV-PLY-0007: composer unavailable');
  const action = await connection.call('Runtime.evaluate', { returnByValue: true, expression: RING_SCRIPT }); connection.ws.close();
  if (action?.result?.value !== 'submitted') throw new Error('RIV-PLY-0008: fixed wake action unavailable');
  const result = safeResult(input, 'succeeded', null, `estate://riverview-doorbell/${attemptId}`, startedAt, now(), attemptId); journal[`${input.request_id}:${input.correlation_id}`] = result; writeJsonAtomic(journalPath(), journal); return result;
}
async function main() {
  try { if (process.argv.includes('--preflight')) { console.log(JSON.stringify(await preflight())); return; } if (!process.argv.includes('--ring')) throw new Error('RIV-PLY-0002: named operation required'); const input = JSON.parse(await new Promise((resolve, reject) => { let value = ''; process.stdin.on('data', chunk => { value += chunk; }); process.stdin.on('end', () => resolve(value)); process.stdin.on('error', reject); })); console.log(JSON.stringify(await ring(input))); }
  catch (error) { console.log(JSON.stringify({ operation: OPERATION, bridge_version: BRIDGE_VERSION, status: 'failed', failure_class: String(error.message).split(':')[0] || 'RIV-PLY-0002' })); process.exitCode = 2; }
}
if (require.main === module) main();

module.exports = { BRIDGE_VERSION, FIXED_WAKE_TEXT, OPERATION, selectExactTarget, validateInput };
