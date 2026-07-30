import crypto from 'node:crypto';
import type { ArchiveConfig, Message } from './model.js';

export type CompletenessStatus = 'complete' | 'incomplete' | 'timed-out' | 'container-not-found' | 'unstable' | 'extraction-failed';
export interface HydrationMetadata {
  hydrationStartedAt: string;
  hydrationEndedAt: string;
  hydrationDurationMs: number;
  hydrationPasses: number;
  stablePassesObserved: number;
  initialMessageCount: number;
  finalMessageCount: number;
  topReached: boolean;
  virtualizationDetected: boolean;
  incrementalAccumulationUsed: boolean;
  completenessStatus: CompletenessStatus;
  completenessWarnings: string[];
  containerDescription?: string;
  firstMessageHash?: string;
}
export interface HydrationSnapshot { count: number; firstMessageHash: string; scrollHeight: number; scrollTop: number; topReached: boolean; loading: boolean; nodeCount: number; virtualizationDetected: boolean; }
export const hashText = (text: string) => crypto.createHash('sha256').update(text).digest('hex');
export function snapshotStable(previous: HydrationSnapshot | undefined, current: HydrationSnapshot, tolerance: number): boolean {
  return !!previous && previous.count === current.count && previous.firstMessageHash === current.firstMessageHash && previous.scrollHeight === current.scrollHeight && Math.abs(current.scrollTop) <= tolerance && current.topReached && !current.loading && previous.nodeCount === current.nodeCount;
}
export function mergeMessages(target: Map<string, Message>, messages: Message[]): Message[] {
  for (const [index, message] of messages.entries()) {
    const text = message.content.map(block => block.text || '').join('\n').trim();
    const key = message.id || `${message.role}:${hashText(text)}:${index}`;
    if (!target.has(key)) target.set(key, { ...message, id: message.id || key });
  }
  return [...target.values()];
}
export function defaultHydrationMetadata(startedAt: string): HydrationMetadata {
  return { hydrationStartedAt: startedAt, hydrationEndedAt: startedAt, hydrationDurationMs: 0, hydrationPasses: 0, stablePassesObserved: 0, initialMessageCount: 0, finalMessageCount: 0, topReached: false, virtualizationDetected: false, incrementalAccumulationUsed: false, completenessStatus: 'extraction-failed', completenessWarnings: [] };
}
export async function hydrateConversation<T extends HydrationSnapshot>(args: {
  config: ArchiveConfig;
  readSnapshot: () => Promise<T>;
  scrollUp: () => Promise<void>;
  collect: () => Promise<Message[]>;
  report?: (snapshot: T, pass: number, stable: number) => void;
  isCancelled?: () => boolean;
}): Promise<{ snapshot: T; messages: Message[]; metadata: HydrationMetadata }> {
  const started = new Date(); const startedAt = started.toISOString(); const first = await args.readSnapshot();
  const accumulated = new Map<string, Message>(); const ordered: string[] = []; let lastBatch: Message[] = [];
  const collectBatch = (batch: Message[]) => { lastBatch = batch; const keys = batch.map((message, index) => message.id || `${message.role}:${hashText(message.content.map(block => block.text || '').join('\n').trim())}:${index}`); const unseen = keys.filter(key => !accumulated.has(key)); for (const [index, message] of batch.entries()) { const key = keys[index]; if (!accumulated.has(key)) accumulated.set(key, { ...message, id: message.id || key }); } if (unseen.length) ordered.unshift(...unseen); };
  collectBatch(await args.collect());
  let previous: T | undefined = first; let stable = 0; let pass = 0; let topReached = first.topReached; let virtualization = first.virtualizationDetected;
  while (pass < args.config.conversationHydrationMaxPasses && Date.now() - started.getTime() < args.config.conversationHydrationMaxDurationMs) {
    if (args.isCancelled?.()) throw new Error('ARCHIVE_CANCELLED_DURING_HYDRATION');
    pass++; await args.scrollUp(); await new Promise(resolve => setTimeout(resolve, args.config.conversationHydrationPollingIntervalMs));
    const current = await args.readSnapshot(); collectBatch(await args.collect());
    topReached ||= current.topReached; virtualization ||= current.virtualizationDetected;
    stable = snapshotStable(previous, current, args.config.conversationTopPositionTolerancePx) ? stable + 1 : 0;
    args.report?.(current, pass, stable); previous = current;
    if (stable >= args.config.conversationHydrationStablePasses) {
      const end = new Date(); return { snapshot: current, messages: virtualization ? ordered.map(key => accumulated.get(key)!).filter(Boolean) : lastBatch, metadata: { hydrationStartedAt: startedAt, hydrationEndedAt: end.toISOString(), hydrationDurationMs: end.getTime() - started.getTime(), hydrationPasses: pass, stablePassesObserved: stable, initialMessageCount: first.count, finalMessageCount: current.count, topReached, virtualizationDetected: virtualization, incrementalAccumulationUsed: virtualization, completenessStatus: 'complete', completenessWarnings: [] } };
    }
  }
  const end = new Date(); const timedOut = Date.now() - started.getTime() >= args.config.conversationHydrationMaxDurationMs;
  const current = previous || first;
  return { snapshot: current, messages: virtualization ? ordered.map(key => accumulated.get(key)!).filter(Boolean) : lastBatch, metadata: { hydrationStartedAt: startedAt, hydrationEndedAt: end.toISOString(), hydrationDurationMs: end.getTime() - started.getTime(), hydrationPasses: pass, stablePassesObserved: stable, initialMessageCount: first.count, finalMessageCount: current.count, topReached, virtualizationDetected: virtualization, incrementalAccumulationUsed: virtualization, completenessStatus: timedOut ? 'timed-out' : 'incomplete', completenessWarnings: [timedOut ? 'Hydration duration ceiling reached before convergence.' : 'Hydration pass ceiling reached before convergence.'] } };
}
