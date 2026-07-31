import fs from 'node:fs';
import path from 'node:path';
import { atomicWrite, readJson } from './storage.js';
import type { ArchiveConfig } from './model.js';

export interface RecoveryRecord { schemaVersion: '1.0'; runId: string; detectedAt: string; staleHeartbeatAgeMs: number; previousPid?: number; previousParentPid?: number; lastCompletedConversationId?: string; lastCompletedCount?: number; interruptedConversationId?: string; interruptedItem?: number; recoveryDisposition: 'interrupted-requeued'; previousStatus: string; }

function processExists(pid: unknown): boolean {
  if (typeof pid !== 'number' || pid <= 0) return false;
  try { process.kill(pid, 0); return true; } catch { return false; }
}

export function recoverStaleRun(root: string, config: ArchiveConfig): RecoveryRecord | undefined {
  const file = path.join(root, 'status', 'current-run.json');
  const state = readJson<any>(file, undefined);
  if (!state || state.status !== 'running') return undefined;
  const heartbeat = Date.parse(state.lastHeartbeatAt || state.updatedAt || state.startedAt || '');
  const age = Number.isFinite(heartbeat) ? Math.max(0, Date.now() - heartbeat) : Number.POSITIVE_INFINITY;
  const ownerAlive = processExists(state.pid) || processExists(state.ownerPid);
  const stale = !ownerAlive || age >= (config.staleRunHeartbeatThresholdMs || 300000);
  if (!stale) return undefined;
  const priorState = readJson<any>(path.join(root, 'state', 'run-state.json'), {});
  const record: RecoveryRecord = { schemaVersion: '1.0', runId: state.runId || 'unknown', detectedAt: new Date().toISOString(), staleHeartbeatAgeMs: age, previousPid: state.pid || state.ownerPid, previousParentPid: state.parentPid, lastCompletedConversationId: state.lastCompletedConversationId || priorState.lastCompletedConversationId, lastCompletedCount: state.processed || priorState.processed, interruptedConversationId: state.currentConversationId || state.nextConversationId, interruptedItem: state.hydration?.item, recoveryDisposition: 'interrupted-requeued', previousStatus: state.status };
  atomicWrite(path.join(root, 'state', 'recovered-runs', `${record.runId}.json`), JSON.stringify(record, null, 2));
  atomicWrite(file, JSON.stringify({ ...state, status: 'interrupted', recoveredAt: record.detectedAt, recovery: record }, null, 2));
  atomicWrite(path.join(root, 'state', 'run-state.json'), JSON.stringify({ ...readJson<any>(path.join(root, 'state', 'run-state.json'), {}), status: 'interrupted', recoveredAt: record.detectedAt, recovery: record, requeueConversationId: record.interruptedConversationId }, null, 2));
  return record;
}

export function writeTerminalRunState(root: string, patch: Record<string, unknown>) {
  const file = path.join(root, 'state', 'run-state.json');
  atomicWrite(file, JSON.stringify({ ...readJson<any>(file, {}), ...patch, updatedAt: new Date().toISOString() }, null, 2));
}
