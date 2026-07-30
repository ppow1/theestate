export type ThrottleSignal = { kind: 'ui' | 'http'; evidence: string };

export class ThrottleError extends Error {
  readonly code = 'RATE_LIMITED';
  constructor(public readonly signal: ThrottleSignal) {
    super(`RATE_LIMITED: ChatGPT temporarily limited conversation access (${signal.evidence})`);
    this.name = 'ThrottleError';
  }
}

export class BackoffCancelledError extends Error {
  readonly code = 'BACKOFF_CANCELLED';
  constructor() { super('BACKOFF_CANCELLED: operator cancelled the throttle wait; completed work remains checkpointed'); }
}

export function detectThrottleSignal(input: { status?: number; text?: string; title?: string }): ThrottleSignal | undefined {
  if (input.status === 429) return { kind: 'http', evidence: 'HTTP 429 Too Many Requests' };
  const text = `${input.title || ''}\n${input.text || ''}`.replace(/\s+/g, ' ').trim();
  if (!text) return undefined;
  const normalized = text.toLocaleLowerCase();
  const heading = /(too many requests|rate limit|rate limited|throttled)/i.test(normalized);
  const body = /(requests? (are )?too (quick|fast)|temporarily (limited|restricted)|conversation (access|history).{0,50}(limited|restricted|unavailable)|try again (in|later)|protect your data|please wait.*(minute|few))/i.test(normalized);
  return heading || body ? { kind: 'ui', evidence: text.slice(0, 240) } : undefined;
}

export function backoffDelayMs(eventNumber: number, baseMs: number, maximumMs: number, jitterMs: number, random = Math.random()): number {
  const exponential = Math.min(maximumMs, baseMs * (2 ** Math.max(0, eventNumber - 1)));
  const jitter = Math.floor(Math.max(0, Math.min(1, random)) * Math.max(0, jitterMs));
  return Math.min(maximumMs, exponential + jitter);
}

export function withinRetryWindow(elapsedMs: number, retryWindowMs: number, delayMs: number): boolean {
  return elapsedMs + delayMs <= retryWindowMs;
}

export async function waitForBackoff(delayMs: number, sleep: (ms: number) => Promise<void>, isCancelled: () => boolean): Promise<void> {
  let remaining = Math.max(0, delayMs);
  while (remaining > 0) { if (isCancelled()) throw new BackoffCancelledError(); const step = Math.min(1000, remaining); await sleep(step); remaining -= step; }
  if (isCancelled()) throw new BackoffCancelledError();
}

export class PacingController {
  private lastConversationAt = 0;
  private burst = 0;
  constructor(private readonly config: { conversationOpenDelayMs: number; burstSize: number; burstCooldownMs: number }) {}
  async beforeConversation(wait: (ms: number) => Promise<void>): Promise<void> {
    const now = Date.now();
    const gap = this.lastConversationAt ? this.config.conversationOpenDelayMs - (now - this.lastConversationAt) : 0;
    if (gap > 0) await wait(gap);
    if (this.burst >= this.config.burstSize) { await wait(this.config.burstCooldownMs); this.burst = 0; }
    this.lastConversationAt = Date.now();
    this.burst++;
  }
}
