import fs from 'node:fs';
import path from 'node:path';
import type { DiscoveredConversation } from './model.js';
import { loadIndex, readJson } from './storage.js';

export function reconcileInventory(root: string, current: DiscoveredConversation[]) {
  const currentIds = [...new Set(current.map(x => x.id))];
  const index = loadIndex(root);
  const historical = new Set(Object.keys(index));
  const priorFiles = fs.existsSync(path.join(root, 'state')) ? fs.readdirSync(path.join(root, 'state')).filter(x => /inventory|conversation-index/i.test(x) && x.endsWith('.json')) : [];
  for (const file of priorFiles) { const value = readJson<any>(path.join(root, 'state', file), {}); const values = Array.isArray(value) ? value : value.conversations || value.ids || []; for (const item of values) historical.add(typeof item === 'string' ? item : item?.id); }
  const currentSet = new Set(currentIds);
  const previousKnownNotVisible = [...historical].filter(Boolean).filter(id => !currentSet.has(id));
  const completed = Object.values(index).filter(x => x.currentStatus === 'available').map(x => x.id);
  const pending = Object.values(index).filter(x => x.currentStatus !== 'available').map(x => x.id);
  return { currentDiscoveredIds: currentIds, discoveredThisRun: currentIds.length, totalPreviouslyKnown: historical.size, previouslyKnownNotVisible: previousKnownNotVisible, newlyDiscoveredIds: currentIds.filter(id => !historical.has(id)), duplicateIds: current.map(x => x.id).filter((id, i, a) => a.indexOf(id) !== i), malformedLinks: [], completedExportIds: completed, idsRequiringExport: pending, idsRequiringReExport: Object.values(index).filter(x => ['incomplete','failed','interrupted'].includes(x.currentStatus)).map(x => x.id), unavailableThroughUi: previousKnownNotVisible, historicalUnionCount: new Set([...historical, ...currentIds]).size };
}
