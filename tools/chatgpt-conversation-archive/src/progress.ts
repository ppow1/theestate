import os from 'node:os';
import path from 'node:path';
import type { ArchiveConfig, SyncReport } from './model.js';
import { atomicWrite, readJson } from './storage.js';

export interface ProgressState { runId: string; mode: string; status: string; startedAt: string; lastHeartbeatAt: string; heartbeatSequence: number; discovered: number; processed: number; currentConversationId?: string; currentConversationTitle?: string; counts: Record<string, number>; accounting?: SyncReport['accounting']; metrics?: SyncReport['metrics']; hydration?: Record<string, unknown>; stallWarning?: string; }

export class ProgressReporter {
  private state: ProgressState;
  private timer?: NodeJS.Timeout;
  private lastMeaningfulProgress = Date.now();
  constructor(private readonly root: string, private readonly config: ArchiveConfig, runId: string, mode: string, startedAt: string) {
    this.state = { runId, mode, status: 'running', startedAt, lastHeartbeatAt: startedAt, heartbeatSequence: 0, discovered: 0, processed: 0, counts: {} };
  }
  private write() { this.state.lastHeartbeatAt = new Date().toISOString(); this.state.heartbeatSequence++; try { atomicWrite(path.join(this.root, 'status', 'current-run.json'), JSON.stringify(this.state, null, 2)); } catch (error) { console.warn(`ARCHIVE_PROGRESS_WRITE_DEFERRED: ${String(error)}`); } }
  start() { this.write(); this.timer = setInterval(() => this.heartbeat(), this.config.progressHeartbeatMs); this.timer.unref?.(); }
  heartbeat() { const stalled = Date.now() - this.lastMeaningfulProgress >= this.config.stallWarningMs; this.state.stallWarning = stalled ? `No exporter progress for ${Math.round((Date.now() - this.lastMeaningfulProgress) / 1000)} seconds` : undefined; this.write(); console.log(`[archive heartbeat] status=${this.state.status} discovered=${this.state.discovered} processed=${this.state.processed}${this.state.currentConversationId ? ` current=${this.state.currentConversationId}` : ''}${this.state.stallWarning ? ` WARNING=${this.state.stallWarning}` : ''}`); }
  update(patch: Partial<ProgressState>) { this.state = { ...this.state, ...patch }; this.lastMeaningfulProgress = Date.now(); this.write(); if (patch.hydration) { const h=patch.hydration as any; console.log(`[archive progress] phase=hydrating-conversation item=${h.item}/${h.total} pass=${h.pass} messages=${h.messages} previousMessages=${h.previousMessages} stable=${h.stable}/${h.requiredStable} scrollTop=${h.scrollTop} scrollHeight=${h.scrollHeight} elapsedMs=${h.elapsedMs} topReached=${h.topReached} virtualizationDetected=${h.virtualizationDetected}`); } else console.log(`[archive progress] ${this.state.processed}/${this.state.discovered} processed${this.state.currentConversationId ? `; ${this.state.currentConversationId}` : ''}`); }
  finish(status: string, report: SyncReport) { if (this.timer) clearInterval(this.timer); this.state = { ...this.state, status, processed: report.counts.processed || 0, discovered: report.counts.discovered || 0, counts: report.counts, accounting: report.accounting, metrics: report.metrics, stallWarning: undefined }; this.write(); }
}

export function updateRuntimeMetrics(root: string, config: ArchiveConfig, report: SyncReport) {
  const file = path.join(root, 'state', 'runtime-metrics.json');
  const current = readJson<any>(file, { schemaVersion: '1.0', updatedAt: undefined, seats: {} });
  const seat = config.runtimeSeat || `${os.hostname()}\${os.userInfo().username}`;
  const prior = current.seats[seat] || { runs: 0, totalRequests: 0, totalActions: 0, conversationsOpened: 0, trueExportFailures: 0, browserContextFailures: 0, cascadingDeferredItems: 0, openAiThrottleEpisodes: 0, http429Responses: 0, uiThrottleDetections: 0, throttleRetries: 0, recoveredThrottleEpisodes: 0, exhaustedThrottleEpisodes: 0, cumulativeThrottleWaitingMs: 0 };
  const m = report.metrics || { totalRequests: 0, totalActions: 0, conversationsOpened: 0, throttlingEvents: 0, http429Responses: 0, uiThrottleDetections: 0, retryCount: 0, recoveredThrottleEpisodes: 0, exhaustedThrottleEpisodes: 0, totalBackoffMs: 0 };
  const a = report.accounting || { trueExportFailures: 0, browserContextFailures: 0, cascadingDeferredItems: 0 };
  current.seats[seat] = { runs: prior.runs + 1, totalRequests: prior.totalRequests + m.totalRequests, totalActions: prior.totalActions + m.totalActions, conversationsOpened: prior.conversationsOpened + m.conversationsOpened, trueExportFailures: prior.trueExportFailures + a.trueExportFailures, browserContextFailures: prior.browserContextFailures + a.browserContextFailures, cascadingDeferredItems: prior.cascadingDeferredItems + a.cascadingDeferredItems, openAiThrottleEpisodes: prior.openAiThrottleEpisodes + m.throttlingEvents, http429Responses: prior.http429Responses + m.http429Responses, uiThrottleDetections: prior.uiThrottleDetections + m.uiThrottleDetections, throttleRetries: prior.throttleRetries + m.retryCount, recoveredThrottleEpisodes: prior.recoveredThrottleEpisodes + m.recoveredThrottleEpisodes, exhaustedThrottleEpisodes: prior.exhaustedThrottleEpisodes + m.exhaustedThrottleEpisodes, cumulativeThrottleWaitingMs: prior.cumulativeThrottleWaitingMs + m.totalBackoffMs };
  current.updatedAt = new Date().toISOString(); current.lastRun = { runId: report.runId, status: report.status, seat };
  atomicWrite(file, JSON.stringify(current, null, 2));
}
