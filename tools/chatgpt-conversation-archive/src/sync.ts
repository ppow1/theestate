import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import type { ArchiveConfig, Conversation, SyncReport } from './model.js';
import { ChatGPTBrowser } from './browser.js';
import { atomicWrite, cleanId, hashConversation, loadIndex, saveIndex, renderMarkdown, renderHtml, writeReport } from './storage.js';
import { backoffDelayMs, BackoffCancelledError, ThrottleError, waitForBackoff, withinRetryWindow } from './throttle.js';
import { isBrowserContextLoss } from './failures.js';
import { ProgressReporter, updateRuntimeMetrics } from './progress.js';

const sleep = (ms: number): Promise<void> => new Promise(resolve => setTimeout(resolve, ms));

function writeRevision(root: string, conversation: Conversation, hash: string, previous?: string) {
  const revisionId = crypto.randomUUID();
  const dir = path.join(root, 'conversations', cleanId(conversation.id), 'revisions', revisionId);
  conversation.revision = { revisionId, contentHash: hash, previousRevisionId: previous };
  atomicWrite(path.join(dir, 'conversation.json'), JSON.stringify(conversation, null, 2));
  atomicWrite(path.join(dir, 'conversation.md'), renderMarkdown(conversation));
  atomicWrite(path.join(dir, 'conversation.html'), renderHtml(conversation));
  const latest = path.join(root, 'conversations', cleanId(conversation.id));
  atomicWrite(path.join(latest, 'latest.json'), JSON.stringify(conversation, null, 2));
  atomicWrite(path.join(latest, 'latest.md'), renderMarkdown(conversation));
  atomicWrite(path.join(latest, 'latest.html'), renderHtml(conversation));
  atomicWrite(path.join(latest, 'metadata.json'), JSON.stringify({ id: conversation.id, title: conversation.title, sourceUrl: conversation.sourceUrl }, null, 2));
  return revisionId;
}

type Operation<T> = () => Promise<T>;

export async function runSync(config: ArchiveConfig, mode: 'full' | 'sync' | 'resume' = 'sync') {
  fs.mkdirSync(config.archiveRoot, { recursive: true });
  atomicWrite(path.join(config.archiveRoot, 'archive-manifest.json'), JSON.stringify({ schemaVersion: '1.0', kind: 'Estate-wide ChatGPT conversation archive', updatedAt: new Date().toISOString(), exporterVersion: '1.0.0', classification: 'Local Only' }, null, 2));
  const runId = `${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomUUID().slice(0, 8)}`;
  const startedAt = new Date().toISOString();
  const report: SyncReport = { runId, startedAt, endedAt: undefined, durationMs: undefined, status: 'running', counts: { new: 0, updated: 0, renamed: 0, unchanged: 0, unavailable: 0, failed: 0, deferred: 0, resumed: mode === 'resume' ? 1 : 0, discovered: 0, processed: 0 }, ids: { new: [], updated: [], renamed: [], unchanged: [], unavailable: [], failed: [] }, errors: [], accounting: { trueExportFailures: 0, browserContextFailures: 0, cascadingDeferredItems: 0 }, metrics: { totalRequests: 0, totalActions: 0, conversationsOpened: 0, throttlingEvents: 0, http429Responses: 0, uiThrottleDetections: 0, retryCount: 0, recoveredThrottleEpisodes: 0, exhaustedThrottleEpisodes: 0, totalBackoffMs: 0 } };
  const progress = new ProgressReporter(config.archiveRoot, config, runId, mode, startedAt);
  progress.start();
  const index = loadIndex(config.archiveRoot);
  let lastCompletedConversationId: string | undefined;
  let browser: ChatGPTBrowser | undefined;
  const throttleStarted = Date.now();
  let throttleEvents = 0;
  let lastThrottleAt = 0;
  let metricSnapshot = { totalRequests: 0, actions: 0, conversationsOpened: 0, http429Responses: 0, uiThrottleDetections: 0 };
  const syncMetrics = () => { if (!browser || !report.metrics) return; const m = browser.getMetrics(); const delta = (value: number, previous: number) => value >= previous ? value - previous : value; report.metrics.totalRequests += delta(m.totalRequests, metricSnapshot.totalRequests); report.metrics.totalActions += delta(m.actions, metricSnapshot.actions); report.metrics.conversationsOpened += delta(m.conversationsOpened, metricSnapshot.conversationsOpened); report.metrics.http429Responses += delta(m.http429Responses, metricSnapshot.http429Responses); report.metrics.uiThrottleDetections += delta(m.uiThrottleDetections, metricSnapshot.uiThrottleDetections); metricSnapshot = { totalRequests: m.totalRequests, actions: m.actions, conversationsOpened: m.conversationsOpened, http429Responses: m.http429Responses, uiThrottleDetections: m.uiThrottleDetections }; report.metrics.throttlingEvents = throttleEvents; };
  const waitForThrottle = async (delayMs: number) => {
    report.metrics!.totalBackoffMs += delayMs;
    console.warn(`RATE_LIMITED: ChatGPT temporarily limited conversation access. Waiting ${Math.ceil(delayMs / 60000)} minute(s).`);
    if (!config.nonInteractive && process.stdin.isTTY) console.warn('Interactive full archive: press Ctrl+C to cancel safely; completed work is checkpointed.');
    let cancelled = false;
    const cancel = () => { cancelled = true; };
    process.once('SIGINT', cancel);
    try { await waitForBackoff(delayMs, sleep, () => cancelled); } finally { process.removeListener('SIGINT', cancel); }
  };
  let activeThrottleEpisode = false;
  const runWithThrottleRetry = async <T>(operation: Operation<T>): Promise<T> => {
    while (true) {
      try { const result = await operation(); if (activeThrottleEpisode) { report.metrics!.recoveredThrottleEpisodes++; activeThrottleEpisode = false; } if (throttleEvents && Date.now() - lastThrottleAt >= config.backoffResetAfterMs) throttleEvents = 0; return result; }
      catch (error) {
        if (!(error instanceof ThrottleError)) throw error;
        if (!activeThrottleEpisode) { throttleEvents++; activeThrottleEpisode = true; }
        lastThrottleAt = Date.now();
        const delay = backoffDelayMs(throttleEvents, config.backoffBaseMs, config.backoffMaxMs, config.backoffJitterMs);
        if (!withinRetryWindow(Date.now() - throttleStarted, config.retryWindowMs, delay)) { report.metrics!.exhaustedThrottleEpisodes++; throw error; }
        report.metrics!.retryCount++;
        syncMetrics();
        if (browser) { await browser.close().catch(() => undefined); browser = undefined; }
        await waitForThrottle(delay);
        browser = await ChatGPTBrowser.open(config, false);
      }
    }
  };
  try {
    browser = await ChatGPTBrowser.open(config, false);
    const discovered = await runWithThrottleRetry(() => browser!.inventory());
    report.counts.discovered = discovered.length;
    progress.update({ discovered: discovered.length, counts: report.counts, metrics: report.metrics, accounting: report.accounting });
    const seen = new Set(discovered.map(item => item.id));
    for (const old of Object.values(index)) if (!seen.has(old.id)) { old.currentStatus = 'unavailable'; old.lastSynchronizedAt = new Date().toISOString(); report.counts.unavailable++; report.ids.unavailable.push(old.id); }
    let stopAfterContextLoss = false;
    for (let itemIndex = 0; itemIndex < discovered.length; itemIndex++) {
      const item = discovered[itemIndex];
      progress.update({ currentConversationId: item.id, currentConversationTitle: item.title, discovered: discovered.length, processed: report.counts.processed, counts: report.counts, metrics: report.metrics, accounting: report.accounting });
      const old = index[item.id];
      try {
        let conversation: Conversation | undefined;
        if (mode === 'full' || !old || old.currentStatus === 'unavailable' || old.title !== item.title) {
          for (let attempt = 0; attempt <= config.retryLimit; attempt++) {
            try { conversation = await runWithThrottleRetry(() => browser!.conversation(item)); break; }
            catch (error) { if (error instanceof ThrottleError || attempt === config.retryLimit) throw error; await sleep(500 * (attempt + 1)); }
          }
        }
        if (!conversation) { if (old) { old.currentStatus = 'unchanged'; old.lastSynchronizedAt = new Date().toISOString(); report.counts.unchanged++; report.ids.unchanged.push(item.id); } continue; }
        const hash = hashConversation(conversation);
        const changed = !old || old.contentHash !== hash;
        const renamed = !!old && old.title !== item.title && !changed;
        if (!changed && !renamed) { report.counts.unchanged++; report.ids.unchanged.push(item.id); }
        else {
          const revisionId = changed ? writeRevision(config.archiveRoot, conversation, hash, old?.lastSuccessfulRevisionId) : old?.lastSuccessfulRevisionId;
          index[item.id] = { id: item.id, title: item.title, sourceUrl: item.sourceUrl, firstArchivedAt: old?.firstArchivedAt || new Date().toISOString(), lastDiscoveredAt: new Date().toISOString(), lastSuccessfulExportAt: changed ? new Date().toISOString() : old?.lastSuccessfulExportAt, lastSynchronizedAt: new Date().toISOString(), contentHash: hash, revisionCount: (old?.revisionCount || 0) + (changed ? 1 : 0), currentStatus: 'available', lastSuccessfulRevisionId: revisionId || old?.lastSuccessfulRevisionId };
          const bucket = changed ? (old ? 'updated' : 'new') : 'renamed'; report.counts[bucket]++; report.ids[bucket].push(item.id);
        }
        report.counts.processed++; lastCompletedConversationId = item.id; saveIndex(config.archiveRoot, index);
        atomicWrite(path.join(config.archiveRoot, 'state', 'run-state.json'), JSON.stringify({ runId, lastCompletedConversationId: item.id, mode, updatedAt: new Date().toISOString(), status: 'running' }, null, 2));
      } catch (error) {
        if (error instanceof ThrottleError) {
          report.status = 'throttled'; report.errors.push({ id: item.id, category: 'rate-limit', message: error.message });
          atomicWrite(path.join(config.archiveRoot, 'state', 'run-state.json'), JSON.stringify({ runId, lastCompletedConversationId, nextConversationId: item.id, mode, updatedAt: new Date().toISOString(), status: 'throttled' }, null, 2));
          throw error;
        }
        if (isBrowserContextLoss(error)) {
          report.accounting!.browserContextFailures++;
          const deferred = discovered.length - itemIndex - 1;
          report.accounting!.cascadingDeferredItems += deferred;
          report.counts.deferred += deferred;
          report.errors.push({ id: item.id, category: 'browser-context', message: String(error) });
          report.status = 'browser-context-lost'; stopAfterContextLoss = true;
          atomicWrite(path.join(config.archiveRoot, 'state', 'run-state.json'), JSON.stringify({ runId, lastCompletedConversationId, nextConversationId: item.id, deferredItems: deferred, mode, updatedAt: new Date().toISOString(), status: report.status }, null, 2));
        } else {
          report.counts.failed++; report.accounting!.trueExportFailures++; report.ids.failed.push(item.id); report.errors.push({ id: item.id, category: 'export', message: String(error) });
          index[item.id] = { ...(old || { id: item.id, title: item.title, sourceUrl: item.sourceUrl, revisionCount: 0, lastDiscoveredAt: new Date().toISOString(), lastSynchronizedAt: new Date().toISOString(), currentStatus: 'failed' }), currentStatus: 'failed', lastError: String(error) }; saveIndex(config.archiveRoot, index);
        }
      }
      syncMetrics(); progress.update({ processed: report.counts.processed, counts: report.counts, metrics: report.metrics, accounting: report.accounting });
      if (stopAfterContextLoss) break;
    }
    if (report.status === 'running') report.status = 'completed';
  } catch (error) {
    if (error instanceof ThrottleError) { report.status = 'throttled'; report.errors.push({ category: 'rate-limit', message: error.message }); }
    else if (error instanceof BackoffCancelledError) { report.status = 'cancelled'; report.errors.push({ category: 'rate-limit', message: error.message }); }
    else if (isBrowserContextLoss(error)) { report.status = 'browser-context-lost'; report.accounting!.browserContextFailures++; report.errors.push({ category: 'browser-context', message: String(error) }); }
    else { report.status = 'failed'; report.counts.failed++; report.accounting!.trueExportFailures++; report.errors.push({ category: 'browser', message: String(error) }); }
  } finally {
    syncMetrics(); report.endedAt = new Date().toISOString(); report.durationMs = Date.parse(report.endedAt) - Date.parse(report.startedAt); if (!report.status || report.status === 'running') report.status = 'completed'; writeReport(config.archiveRoot, report); updateRuntimeMetrics(config.archiveRoot, config, report); progress.finish(report.status, report); if (browser) await browser.close().catch(() => undefined);
  }
  return report;
}
