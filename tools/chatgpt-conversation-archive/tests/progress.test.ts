import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { ProgressReporter, updateRuntimeMetrics } from '../src/progress.js';
import { isBrowserContextLoss } from '../src/failures.js';
import type { ArchiveConfig, SyncReport } from '../src/model.js';

const config = (root: string): ArchiveConfig => ({ archiveRoot: root, profilePath: path.join(root, 'profile'), headless: true, retryLimit: 1, timeoutMs: 1000, diagnosticsPath: path.join(root, 'diagnostics'), concurrency: 1, nonInteractive: true, conversationLimit: 1, exportMarkdown: true, exportHtml: true, backoffBaseMs: 1, backoffMaxMs: 4, backoffJitterMs: 0, retryWindowMs: 10, backoffResetAfterMs: 5, conversationOpenDelayMs: 0, paginationDelayMs: 0, burstSize: 2, burstCooldownMs: 0, progressHeartbeatMs: 5, stallWarningMs: 1, runtimeSeat: 'test-seat' });
const report = (status: string): SyncReport => ({ runId: 'run-1', startedAt: new Date().toISOString(), status, counts: { discovered: 1, processed: 0, failed: 1 }, ids: { failed: [] }, errors: [], accounting: { trueExportFailures: 1, browserContextFailures: 0, cascadingDeferredItems: 0 }, metrics: { totalRequests: 2, totalActions: 3, conversationsOpened: 1, throttlingEvents: 0, http429Responses: 0, uiThrottleDetections: 0, retryCount: 0, recoveredThrottleEpisodes: 0, exhaustedThrottleEpisodes: 0, totalBackoffMs: 0 } });

describe('progress and failure accounting', () => {
  it('writes heartbeat progress and stall warnings', async () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'archive-progress-'));
    const p = new ProgressReporter(root, config(root), 'run-1', 'full', new Date().toISOString());
    p.start(); p.update({ discovered: 2, processed: 1, currentConversationId: 'c1' }); await new Promise(resolve => setTimeout(resolve, 10)); p.heartbeat();
    const warningState = JSON.parse(fs.readFileSync(path.join(root, 'status', 'current-run.json'), 'utf8'));
    expect(warningState.heartbeatSequence).toBeGreaterThan(1); expect(warningState.stallWarning).toContain('No exporter progress'); p.finish('browser-context-lost', report('browser-context-lost'));
    const state = JSON.parse(fs.readFileSync(path.join(root, 'status', 'current-run.json'), 'utf8')); expect(state.status).toBe('browser-context-lost');
    fs.rmSync(root, { recursive: true, force: true });
  });

  it('accumulates seat-aware runtime metrics', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'archive-metrics-')); const c = config(root); updateRuntimeMetrics(root, c, report('failed')); updateRuntimeMetrics(root, c, report('failed'));
    const metrics = JSON.parse(fs.readFileSync(path.join(root, 'state', 'runtime-metrics.json'), 'utf8')); expect(metrics.seats['test-seat'].runs).toBe(2); expect(metrics.seats['test-seat'].trueExportFailures).toBe(2); fs.rmSync(root, { recursive: true, force: true });
  });

  it('recognizes browser-context loss separately from exporter errors', () => {
    expect(isBrowserContextLoss('locator: Target page, context or browser has been closed')).toBe(true);
    expect(isBrowserContextLoss('ReferenceError: roleOf is not defined')).toBe(false);
  });
});
