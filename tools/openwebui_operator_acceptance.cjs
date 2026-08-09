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
const {emitOperatorAttention} = require('./openwebui-operator/operator-attention.cjs');

const VERSION = '0.1.0';
const DEFAULT_URL = process.env.ESTATE_OPENWEBUI_URL || 'http://127.0.0.1:8080';
const DEFAULT_AUTH_BOOTSTRAP_TIMEOUT = 30 * 60;
const AUTH_BOOTSTRAP_COMMAND = 'node tools/openwebui_operator_acceptance.cjs auth-bootstrap';
const AUTH_BOOTSTRAP_PRIVACY = Object.freeze({capture_console: false, capture_network: false, tracing: false, screenshots: false, credentials_persisted: false});
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

async function waitForRenderedSurface(page, timeout = 10000) {
  await page.waitForFunction(() => {
    const body = document.body?.innerText?.trim() || '';
    return body.length > 0 || Boolean(document.querySelector('textarea, [contenteditable="true"]'));
  }, {timeout}).catch(() => {});
}

function defaultProfilePath() {
  return path.join(ROOT, 'runtime', 'browser', 'openwebui-operator-profile');
}

async function openSession(options, evidence) {
  const browserErrors = [], networkErrors = [];
  const capture = options.capture !== false;
  let browser, context, managed = true;
  const cdp = options['connect-cdp'] || process.env.ESTATE_OPENWEBUI_CDP;
  if (cdp) {
    browser = await chromium.connectOverCDP(cdp, {timeout: Number(options['launch-timeout'] || 15000)});
    managed = false;
    context = browser.contexts()[0];
    if (!context) throw Object.assign(new Error('CDP browser has no context'), {classification: FAILURE_CLASSES.OPENWEBUI_UNAVAILABLE});
  } else {
    const profile = options.profile || defaultProfilePath();
    context = await chromium.launchPersistentContext(profile, {
      headless: options.headless === true || options.headless === 'true',
      timeout: Number(options['launch-timeout'] || 30000),
      viewport: {width: 1440, height: 1000}
    });
    browser = context;
  }
  const page = await context.newPage();
  if (capture) {
    page.on('pageerror', error => browserErrors.push({timestamp: new Date().toISOString(), type: 'pageerror', message: String(error.message || error)}));
    page.on('console', message => { if (['error', 'warning'].includes(message.type())) browserErrors.push({timestamp: new Date().toISOString(), type: message.type(), message: message.text()}); });
    page.on('requestfailed', request => networkErrors.push(sanitizeNetwork({timestamp: new Date().toISOString(), method: request.method(), url: request.url(), failure: request.failure()?.errorText || 'request_failed'})));
    page.on('response', response => { if (response.status() >= 400) networkErrors.push(sanitizeNetwork({timestamp: new Date().toISOString(), method: response.request().method(), url: response.url(), status: response.status(), failure: `HTTP_${response.status()}`})); });
  }
  return {browser, context, page, managed, browserErrors, networkErrors, close: async () => { await page.close().catch(() => {}); if (managed) await context.close().catch(() => {}); }};
}

async function readiness(page, url, {navigate = true} = {}) {
  try { if (navigate) await page.goto(url, {waitUntil: 'domcontentloaded', timeout: 15000}); }
  catch (error) { return {status: FAILURE_CLASSES.OPENWEBUI_UNAVAILABLE, error: error.message, url: page.url()}; }
  // DOMContentLoaded only proves that the Svelte shell arrived. Wait for the
  // rendered semantic surface so a healthy asset deployment is not reported
  // as empty merely because hydration is still in flight.
  await waitForRenderedSurface(page);
  const text = await visibleText(page);
  if (/sign in|log in|login/i.test(text) && !/chat|new chat/i.test(text)) return {status: FAILURE_CLASSES.LOGIN_REQUIRED, url: page.url()};
  if (!text.trim()) return {status: FAILURE_CLASSES.RESIDENT_SURFACE_UNAVAILABLE, url: page.url()};
  const composer = await firstVisible(page, SELECTORS.composer);
  const residents = await discoverResidents(page);
  const grace = residents.some(item => item.display_name === 'Grace') || /\bgrace\b/i.test(text);
  return {status: composer && grace ? 'OPENWEBUI_READY' : (grace ? 'MODEL_SURFACE_UNAVAILABLE' : (composer ? FAILURE_CLASSES.RESIDENT_NOT_FOUND : 'RESIDENT_SURFACE_UNAVAILABLE')), url: page.url(), grace_visible: grace, composer_usable: Boolean(composer), residents, title: await page.title()};
}

async function isAuthenticatedSurface(page, result) {
  if (result.status === FAILURE_CLASSES.LOGIN_REQUIRED) return false;
  const text = await visibleText(page);
  if (/sign in to open webui|enter your password|don't have an account/i.test(text)) return false;
  return Boolean(await firstVisible(page, SELECTORS.composer)) || /new chat|chat history|open webui/i.test(text);
}

async function ensureAuthenticatedSession(options, session, evidence, url) {
  let ready = await readiness(session.page, url);
  if (ready.status !== FAILURE_CLASSES.LOGIN_REQUIRED) return {session, readiness: ready, credential_flow: false};
  const attention = emitOperatorAttention({root: ROOT, runId: evidence.run, url, profilePath: path.relative(ROOT, options.profile || defaultProfilePath())});
  await session.close();
  const bootstrapCode = await authBootstrap({...options, url, profile: options.profile || defaultProfilePath()});
  const status = bootstrapCode === 0 ? 'resolved' : (bootstrapCode === 130 ? 'cancelled' : 'timed_out');
  const resolution = emitOperatorAttention({root: ROOT, runId: evidence.run, url, profilePath: path.relative(ROOT, options.profile || defaultProfilePath()), status});
  if (bootstrapCode !== 0) return {session: null, readiness: {status: status === 'timed_out' ? 'AUTH_BOOTSTRAP_TIMEOUT' : 'AUTH_BOOTSTRAP_CANCELLED'}, credential_flow: true, attention, resolution};
  session = await openSession({...options, profile: options.profile || defaultProfilePath()}, evidence);
  ready = await readiness(session.page, url);
  return {session, readiness: ready, credential_flow: true, attention, resolution};
}

function authBootstrapOutcome({cancelled = false, timedOut = false, readinessResult = null, authenticated = false} = {}) {
  if (cancelled) return {status: 'CANCELLED', classification: 'AUTH_BOOTSTRAP_CANCELLED', exitCode: 130};
  if (timedOut) return {status: 'BLOCKED', classification: 'AUTH_BOOTSTRAP_TIMEOUT', exitCode: 2};
  if (authenticated) return {status: 'PASS', classification: 'AUTH_BOOTSTRAP_COMPLETE', exitCode: 0, final_readiness: readinessResult};
  return {status: 'BLOCKED', classification: readinessResult?.status || FAILURE_CLASSES.UNKNOWN, exitCode: 2, final_readiness: readinessResult};
}

async function authBootstrap(options) {
  const evidence = makeEvidence(runId());
  const profile = options.profile || defaultProfilePath();
  const url = options.url || DEFAULT_URL;
  const timeoutSeconds = Math.max(60, Number(options.timeout || DEFAULT_AUTH_BOOTSTRAP_TIMEOUT));
  const manifest = {
    schema_version: 'estate.openwebui.auth-bootstrap.v1',
    harness_version: VERSION,
    git_revision: gitRevision(),
    run_id: evidence.run,
    command: process.argv.slice(2),
    profile_path: profile,
    url: (() => { try { const u = new URL(url); return `${u.origin}${u.pathname}`; } catch { return String(url).split('?')[0]; } })(),
    started_at: new Date().toISOString(),
    status: 'RUNNING',
    privacy: AUTH_BOOTSTRAP_PRIVACY
  };
  const session = await openSession({...options, headed: true, headless: false, capture: false}, evidence);
  let cancelled = false;
  const onSignal = () => { cancelled = true; };
  process.once('SIGINT', onSignal);
  console.log('OPENWEBUI AUTHENTICATION REQUIRED');
  console.log('Complete login in the opened browser window.');
  console.log('This window uses the dedicated Estate Playwright operator profile.');
  console.log('The harness will continue automatically when the authenticated Open WebUI surface is detected.');
  console.log(`Profile: ${profile}`);
  try {
    await session.page.goto(url, {waitUntil: 'domcontentloaded', timeout: 15000});
    const started = Date.now();
    let lastReport = 0;
    let finalReadiness = null;
    while (!cancelled && Date.now() - started < timeoutSeconds * 1000) {
      finalReadiness = await readiness(session.page, url, {navigate: false});
      const authenticated = await isAuthenticatedSurface(session.page, finalReadiness);
      if (authenticated) {
        manifest.readiness = finalReadiness;
        manifest.authenticated_surface = true;
        Object.assign(manifest, authBootstrapOutcome({readinessResult: finalReadiness, authenticated}));
        break;
      }
      const elapsed = Math.floor((Date.now() - started) / 1000);
      if (elapsed - lastReport >= 15) {
        console.log(`Waiting for authenticated Open WebUI surface (${elapsed}s elapsed; Ctrl+C to cancel).`);
        lastReport = elapsed;
      }
      await wait(2000);
    }
    if (cancelled) Object.assign(manifest, authBootstrapOutcome({cancelled}));
    else if (manifest.status === 'RUNNING') Object.assign(manifest, authBootstrapOutcome({timedOut: true, readinessResult: finalReadiness}));
  } catch (error) {
    manifest.status = 'BLOCKED';
    manifest.classification = error.classification || FAILURE_CLASSES.UNKNOWN;
    manifest.error = error.message;
  } finally {
    process.removeListener('SIGINT', onSignal);
    manifest.completed_at = new Date().toISOString();
    writeCompletion(evidence, manifest);
    await session.close();
  }
  console.log(JSON.stringify({status: manifest.status, classification: manifest.classification, run_id: evidence.run, evidence_dir: evidence.dir}, null, 2));
  return manifest.exitCode ?? (manifest.status === 'PASS' ? 0 : 2);
}

async function discoverResidents(page) {
  const names = ['Grace', 'Alfred', 'Helen', 'Ingrid', 'Evelyn', 'Blue'];
  const picker = await firstVisible(page, SELECTORS.modelPicker);
  if (!picker) {
    const text = await visibleText(page);
    return names.filter(name => new RegExp(`\\b${name}\\b`, 'i').test(text)).map(display_name => ({display_name, visible: true, source: 'page_text'}));
  }
  const expanded = await picker.getAttribute('aria-expanded').catch(() => null);
  if (expanded !== 'true') await picker.click().catch(() => {});
  await page.waitForFunction(() => Boolean(document.querySelector('[role="option"], [role="listbox"]')), {timeout: 3000}).catch(() => {});
  const result = [];
  for (const display_name of names) {
    const exact = page.getByText(display_name, {exact: true});
    let visible = false;
    for (let i = 0; i < await exact.count().catch(() => 0); i++) visible ||= await exact.nth(i).isVisible().catch(() => false);
    if (visible) result.push({display_name, visible: true, source: 'model_picker'});
  }
  if (expanded !== 'true') await page.keyboard.press('Escape').catch(() => {});
  return result;
}

async function selectResident(page, resident) {
  const picker = await firstVisible(page, SELECTORS.modelPicker);
  if (!picker) throw Object.assign(new Error('Open WebUI model picker not found'), {classification: FAILURE_CLASSES.MODEL_SURFACE_UNAVAILABLE});
  if (await picker.getAttribute('aria-expanded').catch(() => null) !== 'true') await picker.click();
  await page.waitForFunction(() => Boolean(document.querySelector('[role="option"], [role="listbox"]')), {timeout: 3000}).catch(() => {});
  const exact = page.getByText(resident, {exact: true});
  let option = null;
  for (let i = 0; i < await exact.count().catch(() => 0); i++) {
    if (await exact.nth(i).isVisible().catch(() => false)) { option = exact.nth(i); break; }
  }
  if (!option) throw Object.assign(new Error(`Resident not visible in model picker: ${resident}`), {classification: FAILURE_CLASSES.RESIDENT_NOT_FOUND});
  await option.click();
  await page.waitForFunction((expected) => (document.querySelector('button[aria-label*="selected model" i]')?.getAttribute('aria-label') || '').toLowerCase().includes(expected.toLowerCase()), resident, {timeout: 5000}).catch(() => {});
  const selected_control = await picker.getAttribute('aria-label').catch(() => null);
  if (!selected_control || !selected_control.toLowerCase().includes(resident.toLowerCase())) throw Object.assign(new Error(`Resident selection was not confirmed: ${resident}`), {classification: FAILURE_CLASSES.MODEL_SURFACE_UNAVAILABLE});
  // Read back the authenticated catalog through the same browser origin. This
  // is correlation evidence only; it never creates or mutates model state.
  const catalog = await page.evaluate(async () => {
    try {
      const response = await fetch('/api/models');
      if (!response.ok) return null;
      return await response.json();
    } catch { return null; }
  }).catch(() => null);
  const models = Array.isArray(catalog?.data) ? catalog.data : (Array.isArray(catalog) ? catalog : []);
  const selected_model_catalog_entry = models.find(model => {
    const text = `${model.id || ''} ${model.name || ''} ${model.meta?.title || ''}`.toLowerCase();
    return text.includes(resident.toLowerCase()) && !text.includes('grounded-test');
  });
  const canonical_model_catalog_entry = resident === 'Grace'
    ? models.find(model => model.id === 'estate/grace-grounded-test')
    : null;
  const selectedMeta = selected_model_catalog_entry?.info?.meta || selected_model_catalog_entry?.meta || {};
  const canonicalInfo = canonical_model_catalog_entry?.info || canonical_model_catalog_entry || {};
  return {
    display_name: resident,
    ui_text_confirmed: true,
    selected_control,
    selection_source: 'model_picker_aria_label',
    selected_model_catalog_entry: selected_model_catalog_entry ? {
      id: selected_model_catalog_entry.id || null,
      name: selected_model_catalog_entry.name || null,
      owned_by: selected_model_catalog_entry.owned_by || null,
      resident_id: selectedMeta.resident_id || selectedMeta.residentId || null,
      resident_gateway_capable: selectedMeta.resident_gateway_capable ?? null
    } : null,
    canonical_model_catalog_entry: canonical_model_catalog_entry ? {
      id: canonical_model_catalog_entry.id || null,
      name: canonical_model_catalog_entry.name || null,
      owned_by: canonical_model_catalog_entry.owned_by || null,
      base_model_id: canonicalInfo.base_model_id || null
    } : null
  };
}

async function freshConversation(page, url) {
  await page.goto(url, {waitUntil: 'domcontentloaded', timeout: 15000});
  await waitForRenderedSurface(page);
  const button = await firstVisible(page, SELECTORS.newConversation);
  if (button) await button.click().catch(() => {});
  await waitForRenderedSurface(page, 10000);
  return {url: page.url(), title: await page.title(), started_at: new Date().toISOString()};
}

async function assistantTexts(page) {
  for (const selector of SELECTORS.assistant) {
    const locator = page.locator(selector);
    if (await locator.count().catch(() => 0)) {
      const texts = (await locator.allTextContents()).map(x => x.trim()).filter(Boolean);
      if (texts.length) return texts;
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
    // Open WebUI can mount an empty assistant container before streaming and
    // then fill that same node. Compare content, not only node counts.
    const newTexts = current.filter(text => text && !before.includes(text));
    if (newTexts.length) {
      latest = newTexts[newTexts.length - 1];
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
  const shared = options._sharedSession || null;
  let baseSession = shared || await openSession(options, evidence);
  const ownsSession = !shared;
  let session = baseSession;
  let authInfo = null;
  const pageForSession = ownsSession ? baseSession.page : await baseSession.context.newPage();
  session = ownsSession ? baseSession : {
    ...baseSession,
    page: pageForSession,
    browserErrors: [],
    networkErrors: [],
    close: async () => { await page.close().catch(() => {}); }
  };
  if (shared && options.capture !== false) {
    page.on('pageerror', error => session.browserErrors.push({timestamp: new Date().toISOString(), type: 'pageerror', message: String(error.message || error)}));
    page.on('console', message => { if (['error', 'warning'].includes(message.type())) session.browserErrors.push({timestamp: new Date().toISOString(), type: message.type(), message: message.text()}); });
    page.on('requestfailed', request => session.networkErrors.push(sanitizeNetwork({timestamp: new Date().toISOString(), method: request.method(), url: request.url(), failure: request.failure()?.errorText || 'request_failed'})));
    page.on('response', response => { if (response.status() >= 400) session.networkErrors.push(sanitizeNetwork({timestamp: new Date().toISOString(), method: response.request().method(), url: response.url(), status: response.status(), failure: `HTTP_${response.status()}`})); });
  }
  const turns = [];
  try {
    if (ownsSession) {
      authInfo = await ensureAuthenticatedSession(options, session, evidence, options.url || DEFAULT_URL);
      session = authInfo.session;
      if (authInfo.credential_flow) manifest.authentication_bootstrap = {credential_flow: true, attention_event_id: authInfo.attention?.event.event_id, resolution_event_id: authInfo.resolution?.event.event_id, profile_path: path.relative(ROOT, options.profile || defaultProfilePath())};
      if (!session) throw Object.assign(new Error(authInfo.readiness.status), {classification: authInfo.readiness.status});
    }
    const page = session.page;
    if (ownsSession) await session.context.tracing.start({screenshots: true, snapshots: true, sources: false});
    const url = options.url || DEFAULT_URL;
    const ready = authInfo?.readiness || await readiness(page, url);
    manifest.readiness = ready;
    if (ready.status !== 'OPENWEBUI_READY') throw Object.assign(new Error(`Readiness: ${ready.status}`), {classification: ready.status});
    const conversation = scenario.fresh_conversation === false ? {url: page.url()} : await freshConversation(page, url);
    manifest.conversation = conversation;
    const resident = await selectResident(page, scenario.resident);
    manifest.resident = resident;
    for (let i = 0; i < scenario.turns.length; i++) {
      const result = await sendTurn(page, scenario.turns[i].send, {...options, ...(scenario.timeouts || {})}, evidence, i + 1);
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
    if (!authInfo?.credential_flow) {
      await session?.page?.screenshot({path: path.join(evidence.screenshots, 'failure.png'), fullPage: true}).catch(() => {});
      await session?.page?.locator('body').innerText().then(text => fs.writeFileSync(path.join(evidence.dir, 'dom-summary.txt'), text.slice(0, 12000), 'utf8')).catch(() => {});
    }
  } finally {
    manifest.completed_at = new Date().toISOString();
    manifest.console = session?.browserErrors || [];
    manifest.network = session?.networkErrors || [];
    writeJson(path.join(evidence.dir, 'console.json'), manifest.console);
    writeJson(path.join(evidence.dir, 'network.json'), manifest.network);
    if (turns.length) fs.writeFileSync(path.join(evidence.dir, 'response.txt'), turns.map(x => `Turn ${x.turn}\n${x.assistant}`).join('\n\n'), 'utf8');
    if (ownsSession && session) await session.context.tracing.stop({path: path.join(evidence.dir, 'trace.zip')}).catch(() => {});
    writeCompletion(evidence, manifest);
    if (ownsSession && session) await session.close();
  }
  console.log(JSON.stringify(manifest, null, 2));
  return manifest.status === 'PASS' ? 0 : 2;
}

async function executeConcurrent(files, options) {
  if (files.length < 2) throw new Error('concurrent requires --scenario-a and --scenario-b');
  // Chromium locks a persistent user-data directory. Share one authenticated
  // context and use independent pages so concurrent acceptance never corrupts
  // the operator profile or silently falls back to a second auth state.
  const started = new Date().toISOString();
  const sharedEvidence = makeEvidence(runId());
  let sharedSession = await openSession(options, sharedEvidence);
  try {
    const authInfo = await ensureAuthenticatedSession(options, sharedSession, sharedEvidence, options.url || DEFAULT_URL);
    sharedSession = authInfo.session;
    if (!sharedSession) return 2;
    const codes = await Promise.all(files.map(file => executeScenario(file, {
      ...options,
      headed: options.headed,
      'concurrent-parent-started': started,
      _sharedSession: sharedSession
    })));
    return codes.every(code => code === 0) ? 0 : 2;
  } finally {
    if (sharedSession) await sharedSession.close();
  }
}

async function main() {
  const options = args(process.argv.slice(2));
  const command = options._[0] || 'readiness';
  if (command === 'auth-bootstrap') return authBootstrap(options);
  if (command === 'scenario') return executeScenario(options._[1], options);
  if (command === 'concurrent') return executeConcurrent([options['scenario-a'], options['scenario-b']].filter(Boolean), options);
  if (!['readiness', 'doctor', 'chat'].includes(command)) throw new Error(`Unknown command: ${command}`);
  const evidence = makeEvidence(runId());
  let session = await openSession(options, evidence);
  let authInfo = null;
  const manifest = {schema_version: 'estate.openwebui.operator.v1', harness_version: VERSION, git_revision: gitRevision(), run_id: evidence.run, command: process.argv.slice(2), started_at: new Date().toISOString(), status: 'PASS', url: options.url || DEFAULT_URL};
  try {
    manifest.browser = {playwright_version: require('playwright/package.json').version, browser: process.env.PLAYWRIGHT_BROWSERS_PATH || 'managed'};
    authInfo = await ensureAuthenticatedSession(options, session, evidence, manifest.url);
    session = authInfo.session;
    if (authInfo.credential_flow) manifest.authentication_bootstrap = {credential_flow: true, attention_event_id: authInfo.attention?.event.event_id, resolution_event_id: authInfo.resolution?.event.event_id, profile_path: path.relative(ROOT, options.profile || defaultProfilePath())};
    if (!session) throw Object.assign(new Error(authInfo.readiness.status), {classification: authInfo.readiness.status});
    manifest.readiness = authInfo.readiness;
    manifest.residents = await discoverResidents(session.page);
    if (command === 'readiness' && manifest.readiness.status !== 'OPENWEBUI_READY') manifest.status = 'BLOCKED';
    manifest.authentication = manifest.readiness.status === 'LOGIN_REQUIRED' ? 'LOGIN_REQUIRED' : 'NOT_ESTABLISHED_OR_NOT_REQUIRED';
    if (manifest.readiness.status !== 'OPENWEBUI_READY' && !authInfo.credential_flow) {
      await session.page.screenshot({path: path.join(evidence.screenshots, `${command}-readiness.png`), fullPage: true}).catch(() => {});
    }
    if (command === 'chat') {
      if (manifest.readiness.status !== 'OPENWEBUI_READY') throw Object.assign(new Error(manifest.readiness.status), {classification: manifest.readiness.status});
      manifest.conversation = await freshConversation(session.page, manifest.url);
      manifest.resident = await selectResident(session.page, options.resident || 'Grace');
      const result = await sendTurn(session.page, options.message || 'Hello Grace. Please reply with a brief readiness acknowledgement.', options, evidence, 1);
      manifest.response = result;
      fs.writeFileSync(path.join(evidence.dir, 'response.txt'), result.assistant, 'utf8');
    }
    if (command === 'doctor') {
      manifest.status = manifest.readiness.status === 'OPENWEBUI_READY' ? 'PASS' : 'BLOCKED';
      manifest.recommended_activation_boundary = manifest.readiness.status === 'LOGIN_REQUIRED' ? 'AUTOMATION_PAUSED_FOR_HUMAN' : 'OPENWEBUI_SERVICE_OR_UI_BOUNDARY';
      if (manifest.readiness.status === 'LOGIN_REQUIRED') manifest.recommended_command = AUTH_BOOTSTRAP_COMMAND;
    }
  } catch (error) { manifest.status = 'BLOCKED'; manifest.failure_class = error.classification || FAILURE_CLASSES.UNKNOWN; manifest.error = error.message; if (!authInfo?.credential_flow) await session?.page?.screenshot({path: path.join(evidence.screenshots, 'failure.png'), fullPage: true}).catch(() => {}); }
  finally { manifest.completed_at = new Date().toISOString(); manifest.console = session?.browserErrors || []; manifest.network = session?.networkErrors || []; writeJson(path.join(evidence.dir, 'console.json'), manifest.console); writeJson(path.join(evidence.dir, 'network.json'), manifest.network); writeCompletion(evidence, manifest); if (session) await session.close(); }
  console.log(JSON.stringify(manifest, null, 2));
  return manifest.status === 'PASS' ? 0 : 2;
}

if (require.main === module) main().then(code => process.exitCode = code).catch(error => { console.error(error.stack || error); process.exitCode = 1; });

module.exports = {VERSION, FAILURE_CLASSES, DEFAULT_AUTH_BOOTSTRAP_TIMEOUT, AUTH_BOOTSTRAP_COMMAND, AUTH_BOOTSTRAP_PRIVACY, args, defaultProfilePath, readiness, isAuthenticatedSurface, authBootstrapOutcome, ensureAuthenticatedSession, discoverResidents, selectResident, assistantTexts, matchesExpectation};
