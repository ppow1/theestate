#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');
const {execFileSync} = require('node:child_process');
const {chromium} = require('playwright');
const {SELECTORS, firstVisible, visibleText} = require('./openwebui-operator/selectors.cjs');
const {runId, makeEvidence, writeJson, sanitizeNetwork, writeCompletion, ROOT} = require('./openwebui-operator/evidence.cjs');
const {loadScenario, matchesExpectation} = require('./openwebui-operator/scenario.cjs');
const {compareCmeClaim, readCmeState} = require('./openwebui-operator/ground_truth.cjs');

const VERSION = '0.1.0';
const DEFAULT_URL = process.env.ESTATE_OPENWEBUI_URL || 'http://127.0.0.1:8080';
const FAILURE_CLASSES = Object.freeze({
  OPENWEBUI_UNAVAILABLE: 'OPENWEBUI_UNAVAILABLE', LOGIN_REQUIRED: 'LOGIN_REQUIRED',
  RESIDENT_SURFACE_UNAVAILABLE: 'RESIDENT_SURFACE_UNAVAILABLE',
  RESIDENT_NOT_FOUND: 'RESIDENT_NOT_FOUND', COMPOSER_NOT_FOUND: 'COMPOSER_NOT_FOUND',
  SEND_FAILED: 'SEND_FAILED', STREAM_TIMEOUT: 'STREAM_TIMEOUT', RESPONSE_NOT_OBSERVED: 'RESPONSE_NOT_OBSERVED',
  PAGE_ERROR: 'PAGE_ERROR', NETWORK_ERROR: 'NETWORK_ERROR', AUTH_SESSION_EXPIRED: 'AUTH_SESSION_EXPIRED',
  MODEL_SURFACE_UNAVAILABLE: 'MODEL_SURFACE_UNAVAILABLE', UI_CHANGED: 'UI_CHANGED', UNKNOWN: 'UNKNOWN'
});

function args(argv) {
  const out = {_: []};
  for (let i = 0; i < argv.length; i++) {
    const x = argv[i];
    if (!x.startsWith('--')) { out._.push(x); continue; }
    const [key, inline] = x.slice(2).split('=', 2);
    if (inline !== undefined) out[key] = inline;
    else if (argv[i + 1] && !argv[i + 1].startsWith('--')) out[key] = argv[++i];
    else out[key] = true;
  }
  return out;
}

function gitRevision() {
  try { return execFileSync('git', ['rev-parse', 'HEAD'], {cwd: ROOT, encoding: 'utf8'}).trim(); } catch { return 'UNKNOWN'; }
}

function wait(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function openSession(options, evidence) {
  const browserErrors = [], networkErrors = [];
  let browser, context, managed = true;
  const cdp = options['connect-cdp'] || process.env.ESTATE_OPENWEBUI_CDP;
  if (cdp) {
    browser = await chromium.connectOverCDP(cdp, {timeout: Number(options['launch-timeout'] || 15000)});
    managed = false;
    context = browser.contexts()[0];
    if (!context) throw Object.assign(new Error('CDP browser has no context'), {classification: FAILURE_CLASSES.OPENWEBUI_UNAVAILABLE});
  } else {
    const profile = options.profile || path.join(ROOT, 'runtime', 'browser', 'openwebui-operator-profile');
    context = await chromium.launchPersistentContext(profile, {
      headless: options.headless === true || options.headless === 'true',
      timeout: Number(options['launch-timeout'] || 30000),
      viewport: {width: 1440, height: 1000}
    });
    browser = context;
  }
  const page = await context.newPage();
  page.on('pageerror', error => browserErrors.push({timestamp: new Date().toISOString(), type: 'pageerror', message: String(error.message || error)}));
  page.on('console', message => { if (['error', 'warning'].includes(message.type())) browserErrors.push({timestamp: new Date().toISOString(), type: message.type(), message: message.text()}); });
  page.on('requestfailed', request => networkErrors.push(sanitizeNetwork({timestamp: new Date().toISOString(), method: request.method(), url: request.url(), failure: request.failure()?.errorText || 'request_failed'})));
  page.on('response', response => { if (response.status() >= 400) networkErrors.push(sanitizeNetwork({timestamp: new Date().toISOString(), method: response.request().method(), url: response.url(), status: response.status(), failure: `HTTP_${response.status()}`})); });
  return {browser, context, page, managed, browserErrors, networkErrors, close: async () => { await page.close().catch(() => {}); if (managed) await context.close().catch(() => {}); }};
}

async function readiness(page, url) {
  try { await page.goto(url, {waitUntil: 'domcontentloaded', timeout: 15000}); }
  catch (error) { return {status: FAILURE_CLASSES.OPENWEBUI_UNAVAILABLE, error: error.message, url: page.url()}; }
  // DOMContentLoaded only proves that the Svelte shell arrived. Wait for the
  // rendered semantic surface so a healthy asset deployment is not reported
  // as empty merely because hydration is still in flight.
  await page.waitForFunction(() => {
    const body = document.body?.innerText?.trim() || '';
    return body.length > 0 || Boolean(document.querySelector('textarea, [contenteditable="true"]'));
  }, {timeout: 10000}).catch(() => {});
  const text = await visibleText(page);
  if (/sign in|log in|login/i.test(text) && !/chat|new chat/i.test(text)) return {status: FAILURE_CLASSES.LOGIN_REQUIRED, url: page.url()};
  if (!text.trim()) return {status: FAILURE_CLASSES.RESIDENT_SURFACE_UNAVAILABLE, url: page.url()};
  const composer = await firstVisible(page, SELECTORS.composer);
  const grace = /\bgrace\b/i.test(text);
  return {status: composer && grace ? 'OPENWEBUI_READY' : (grace ? 'MODEL_SURFACE_UNAVAILABLE' : 'RESIDENT_SURFACE_UNAVAILABLE'), url: page.url(), grace_visible: grace, composer_usable: Boolean(composer), title: await page.title()};
}

async function discoverResidents(page) {
  const text = await visibleText(page);
  const names = ['Grace', 'Alfred', 'Helen', 'Ingrid', 'Evelyn', 'Blue'];
  return names.filter(name => new RegExp(`\\b${name}\\b`, 'i').test(text)).map(display_name => ({display_name, visible: true}));
}

async function selectResident(page, resident) {
  const exact = page.getByText(resident, {exact: true}).first();
  if (await exact.count() && await exact.isVisible().catch(() => false)) {
    await exact.click().catch(() => {});
    await wait(250);
  }
  const text = await visibleText(page);
  if (!new RegExp(`\\b${resident}\\b`, 'i').test(text)) throw Object.assign(new Error(`Resident not visible: ${resident}`), {classification: FAILURE_CLASSES.RESIDENT_NOT_FOUND});
  const controls = (await page.locator('button').allTextContents().catch(() => [])).map(x => x.trim()).filter(Boolean);
  return {display_name: resident, ui_text_confirmed: true, visible_model_controls: controls.slice(0, 20)};
}

async function freshConversation(page, url) {
  await page.goto(url, {waitUntil: 'domcontentloaded', timeout: 15000});
  const button = await firstVisible(page, SELECTORS.newConversation);
  if (button) await button.click().catch(() => {});
  await wait(300);
  return {url: page.url(), title: await page.title(), started_at: new Date().toISOString()};
}

async function assistantTexts(page) {
  for (const selector of SELECTORS.assistant) {
    const locator = page.locator(selector);
    if (await locator.count().catch(() => 0)) {
      return (await locator.allTextContents()).map(x => x.trim()).filter(Boolean);
    }
  }
  return [];
}

async function sendTurn(page, message, options, evidence, turnNumber) {
  const composer = await firstVisible(page, SELECTORS.composer);
  if (!composer) throw Object.assign(new Error('Open WebUI composer not found'), {classification: FAILURE_CLASSES.COMPOSER_NOT_FOUND});
  const before = await assistantTexts(page);
  await page.screenshot({path: path.join(evidence.screenshots, `turn-${turnNumber}-before-send.png`), fullPage: true});
  await composer.fill(message);
  const send = await firstVisible(page, SELECTORS.send);
  if (!send) throw Object.assign(new Error('Open WebUI send control not found'), {classification: FAILURE_CLASSES.SEND_FAILED});
  await send.click();
  await page.screenshot({path: path.join(evidence.screenshots, `turn-${turnNumber}-after-send.png`), fullPage: true});
  const timeout = Number(options.timeout || 60000);
  const deadline = Date.now() + timeout;
  let latest = '';
  let stableSince = 0;
  while (Date.now() < deadline) {
    const current = await assistantTexts(page);
    if (current.length > before.length) {
      latest = current[current.length - 1];
      if (latest) {
        if (latest === (sendTurn.lastText || '')) stableSince ||= Date.now(); else { stableSince = Date.now(); sendTurn.lastText = latest; }
        const stop = await firstVisible(page, SELECTORS.stop);
        if (!stop && Date.now() - stableSince >= 900) break;
      }
    }
    const body = await visibleText(page);
    if (/something went wrong|error generating|failed to generate/i.test(body)) throw Object.assign(new Error('Open WebUI displayed a response error'), {classification: FAILURE_CLASSES.NETWORK_ERROR});
    await wait(250);
  }
  if (!latest) throw Object.assign(new Error('No new assistant response observed before timeout'), {classification: FAILURE_CLASSES.RESPONSE_NOT_OBSERVED});
  await page.screenshot({path: path.join(evidence.screenshots, `turn-${turnNumber}-final.png`), fullPage: true});
  return {turn: turnNumber, user: message, assistant: latest, completed_at: new Date().toISOString(), conversation_url: page.url()};
}

async function executeScenario(file, options) {
  const scenario = loadScenario(file);
  const evidence = makeEvidence(runId());
  const manifest = {schema_version: 'estate.openwebui.operator.v1', harness_version: VERSION, git_revision: gitRevision(), run_id: evidence.run, command: process.argv.slice(2), scenario: scenario.name, started_at: new Date().toISOString(), status: 'RUNNING', failure_class: null, evidence_dir: evidence.dir};
  writeJson(path.join(evidence.dir, 'scenario.json'), scenario);
  const session = await openSession(options, evidence);
  const turns = [];
  try {
    await session.context.tracing.start({screenshots: true, snapshots: true, sources: false});
    const url = options.url || DEFAULT_URL;
    const ready = await readiness(session.page, url);
    manifest.readiness = ready;
    if (ready.status !== 'OPENWEBUI_READY') throw Object.assign(new Error(`Readiness: ${ready.status}`), {classification: ready.status});
    const resident = await selectResident(session.page, scenario.resident);
    manifest.resident = resident;
    const conversation = scenario.fresh_conversation === false ? {url: session.page.url()} : await freshConversation(session.page, url);
    manifest.conversation = conversation;
    for (let i = 0; i < scenario.turns.length; i++) {
      const result = await sendTurn(session.page, scenario.turns[i].send, {...options, ...(scenario.timeouts || {})}, evidence, i + 1);
      const assertion = matchesExpectation(result.assistant, scenario.turns[i].expect);
      turns.push({...result, assertion});
      if (!assertion.passed) throw Object.assign(new Error(`Turn ${i + 1} semantic expectation failed`), {classification: FAILURE_CLASSES.UNKNOWN});
    }
    manifest.turns = turns;
    manifest.status = 'PASS';
    if (scenario.validator === 'cme_state') manifest.ground_truth = compareCmeClaim(turns.at(-1)?.assistant, readCmeState());
  } catch (error) {
    manifest.status = 'BLOCKED';
    manifest.failure_class = error.classification || FAILURE_CLASSES.UNKNOWN;
    manifest.error = error.message;
    await session.page.screenshot({path: path.join(evidence.screenshots, 'failure.png'), fullPage: true}).catch(() => {});
    await session.page.locator('body').innerText().then(text => fs.writeFileSync(path.join(evidence.dir, 'dom-summary.txt'), text.slice(0, 12000), 'utf8')).catch(() => {});
  } finally {
    manifest.completed_at = new Date().toISOString();
    manifest.console = session.browserErrors;
    manifest.network = session.networkErrors;
    writeJson(path.join(evidence.dir, 'console.json'), session.browserErrors);
    writeJson(path.join(evidence.dir, 'network.json'), session.networkErrors);
    if (turns.length) fs.writeFileSync(path.join(evidence.dir, 'response.txt'), turns.map(x => `Turn ${x.turn}\n${x.assistant}`).join('\n\n'), 'utf8');
    await session.context.tracing.stop({path: path.join(evidence.dir, 'trace.zip')}).catch(() => {});
    writeCompletion(evidence, manifest);
    await session.close();
  }
  console.log(JSON.stringify(manifest, null, 2));
  return manifest.status === 'PASS' ? 0 : 2;
}

async function executeConcurrent(files, options) {
  if (files.length < 2) throw new Error('concurrent requires --scenario-a and --scenario-b');
  // Independent persistent contexts make accidental conversation crossover
  // impossible. Each child run owns its own evidence and page lifecycle.
  const started = new Date().toISOString();
  const codes = await Promise.all(files.map(file => executeScenario(file, {...options, headed: options.headed, 'concurrent-parent-started': started})));
  return codes.every(code => code === 0) ? 0 : 2;
}

async function main() {
  const options = args(process.argv.slice(2));
  const command = options._[0] || 'readiness';
  if (command === 'scenario') return executeScenario(options._[1], options);
  if (command === 'concurrent') return executeConcurrent([options['scenario-a'], options['scenario-b']].filter(Boolean), options);
  if (!['readiness', 'doctor', 'chat'].includes(command)) throw new Error(`Unknown command: ${command}`);
  const evidence = makeEvidence(runId());
  const session = await openSession(options, evidence);
  const manifest = {schema_version: 'estate.openwebui.operator.v1', harness_version: VERSION, git_revision: gitRevision(), run_id: evidence.run, command: process.argv.slice(2), started_at: new Date().toISOString(), status: 'PASS', url: options.url || DEFAULT_URL};
  try {
    manifest.browser = {playwright_version: require('playwright/package.json').version, browser: process.env.PLAYWRIGHT_BROWSERS_PATH || 'managed'};
    manifest.readiness = await readiness(session.page, manifest.url);
    manifest.residents = await discoverResidents(session.page);
    if (command === 'readiness' && manifest.readiness.status !== 'OPENWEBUI_READY') manifest.status = 'BLOCKED';
    manifest.authentication = manifest.readiness.status === 'LOGIN_REQUIRED' ? 'LOGIN_REQUIRED' : 'NOT_ESTABLISHED_OR_NOT_REQUIRED';
    if (manifest.readiness.status !== 'OPENWEBUI_READY') {
      await session.page.screenshot({path: path.join(evidence.screenshots, `${command}-readiness.png`), fullPage: true}).catch(() => {});
    }
    if (command === 'chat') {
      if (manifest.readiness.status !== 'OPENWEBUI_READY') throw Object.assign(new Error(manifest.readiness.status), {classification: manifest.readiness.status});
      manifest.resident = await selectResident(session.page, options.resident || 'Grace');
      manifest.conversation = await freshConversation(session.page, manifest.url);
      const result = await sendTurn(session.page, options.message || 'Hello Grace. Please reply with a brief readiness acknowledgement.', options, evidence, 1);
      manifest.response = result;
      fs.writeFileSync(path.join(evidence.dir, 'response.txt'), result.assistant, 'utf8');
    }
    if (command === 'doctor') {
      manifest.status = manifest.readiness.status === 'OPENWEBUI_READY' ? 'PASS' : 'BLOCKED';
      manifest.recommended_activation_boundary = manifest.readiness.status === 'LOGIN_REQUIRED' ? 'AUTOMATION_PAUSED_FOR_HUMAN' : 'OPENWEBUI_SERVICE_OR_UI_BOUNDARY';
    }
  } catch (error) { manifest.status = 'BLOCKED'; manifest.failure_class = error.classification || FAILURE_CLASSES.UNKNOWN; manifest.error = error.message; await session.page.screenshot({path: path.join(evidence.screenshots, 'failure.png'), fullPage: true}).catch(() => {}); }
  finally { manifest.completed_at = new Date().toISOString(); manifest.console = session.browserErrors; manifest.network = session.networkErrors; writeJson(path.join(evidence.dir, 'console.json'), session.browserErrors); writeJson(path.join(evidence.dir, 'network.json'), session.networkErrors); writeCompletion(evidence, manifest); await session.close(); }
  console.log(JSON.stringify(manifest, null, 2));
  return manifest.status === 'PASS' ? 0 : 2;
}

if (require.main === module) main().then(code => process.exitCode = code).catch(error => { console.error(error.stack || error); process.exitCode = 1; });

module.exports = {VERSION, FAILURE_CLASSES, args, readiness, discoverResidents, selectResident, assistantTexts, matchesExpectation};
