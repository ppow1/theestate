import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import type { ArchiveConfig, Conversation, SyncReport } from './model.js';
import { ChatGPTBrowser } from './browser.js';
import { atomicWrite, cleanId, hashConversation, loadIndex, saveIndex, renderMarkdown, renderHtml, writeReport } from './storage.js';

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

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

export async function runSync(config: ArchiveConfig, mode: 'full' | 'sync' | 'resume' = 'sync') {
  fs.mkdirSync(config.archiveRoot, { recursive: true });
  atomicWrite(path.join(config.archiveRoot, 'archive-manifest.json'), JSON.stringify({ schemaVersion: '1.0', kind: 'Estate-wide ChatGPT conversation archive', updatedAt: new Date().toISOString(), exporterVersion: '1.0.0', classification: 'Local Only' }, null, 2));
  const runId = `${new Date().toISOString().replace(/[:.]/g, '-')}-${crypto.randomUUID().slice(0, 8)}`;
  const startedAt = new Date().toISOString();
  const report: SyncReport = { runId, startedAt, counts: { new: 0, updated: 0, renamed: 0, unchanged: 0, unavailable: 0, failed: 0, resumed: mode === 'resume' ? 1 : 0, discovered: 0, processed: 0 }, ids: { new: [], updated: [], renamed: [], unchanged: [], unavailable: [], failed: [] }, errors: [] };
  const index = loadIndex(config.archiveRoot);
  let browser: ChatGPTBrowser | undefined;
  try {
    browser = await ChatGPTBrowser.open(config, false);
    const discovered = await browser.inventory();
    report.counts.discovered = discovered.length;
    const seen = new Set(discovered.map(item => item.id));
    for (const old of Object.values(index)) if (!seen.has(old.id)) { old.currentStatus = 'unavailable'; old.lastSynchronizedAt = new Date().toISOString(); report.counts.unavailable++; report.ids.unavailable.push(old.id); }
    for (const item of discovered) {
      const old = index[item.id];
      try {
        let conversation: Conversation | undefined;
        if (mode === 'full' || !old || old.currentStatus === 'unavailable' || old.title !== item.title) {
          for (let attempt = 0; attempt <= config.retryLimit; attempt++) {
            try { conversation = await browser.conversation(item); break; }
            catch (error) { if (attempt === config.retryLimit) throw error; await sleep(500 * (attempt + 1)); }
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
        report.counts.processed++; saveIndex(config.archiveRoot, index);
        atomicWrite(path.join(config.archiveRoot, 'state', 'run-state.json'), JSON.stringify({ runId, lastCompletedConversationId: item.id, mode, updatedAt: new Date().toISOString() }, null, 2));
      } catch (error) {
        report.counts.failed++; report.ids.failed.push(item.id); report.errors.push({ id: item.id, category: 'export', message: String(error) });
        index[item.id] = { ...(old || { id: item.id, title: item.title, sourceUrl: item.sourceUrl, revisionCount: 0, lastDiscoveredAt: new Date().toISOString(), lastSynchronizedAt: new Date().toISOString(), currentStatus: 'failed' }), currentStatus: 'failed', lastError: String(error) }; saveIndex(config.archiveRoot, index);
      }
    }
  } catch (error) {
    report.counts.failed++;
    report.errors.push({ category: 'browser', message: String(error) });
  } finally {
    report.endedAt = new Date().toISOString(); report.durationMs = Date.parse(report.endedAt) - Date.parse(report.startedAt); writeReport(config.archiveRoot, report); if (browser) await browser.close();
  }
  return report;
}
