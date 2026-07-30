import { describe, expect, it } from 'vitest';
import { backoffDelayMs, detectThrottleSignal, PacingController, waitForBackoff, withinRetryWindow, BackoffCancelledError } from '../src/throttle.js';

describe('ChatGPT throttle controls', () => {
  it('detects modal headings, body wording, and HTTP 429', () => {
    expect(detectThrottleSignal({ title: 'Too many requests' })?.kind).toBe('ui');
    expect(detectThrottleSignal({ text: "You're making requests too quickly. We've temporarily limited access to your conversations." })).toBeTruthy();
    expect(detectThrottleSignal({ status: 429, text: 'not needed' })?.kind).toBe('http');
    expect(detectThrottleSignal({ text: 'Your archive is ready' })).toBeUndefined();
  });

  it('uses exponential backoff, cap, and bounded jitter', () => {
    expect(backoffDelayMs(1, 300000, 1800000, 30000, 0)).toBe(300000);
    expect(backoffDelayMs(2, 300000, 1800000, 30000, 1)).toBe(630000);
    expect(backoffDelayMs(10, 300000, 1800000, 30000, 1)).toBe(1800000);
    expect(withinRetryWindow(1000, 5000, 4000)).toBeTruthy();
    expect(withinRetryWindow(1000, 5000, 5000)).toBeFalsy();
  });

  it('paces conversation openings and cooldown bursts', async () => {
    const waits: number[] = [];
    const pacing = new PacingController({ conversationOpenDelayMs: 1, burstSize: 2, burstCooldownMs: 9 });
    await pacing.beforeConversation(async ms => waits.push(ms));
    await pacing.beforeConversation(async ms => waits.push(ms));
    await pacing.beforeConversation(async ms => waits.push(ms));
    expect(waits).toContain(9);
  });

  it('supports graceful cancellation during backoff', async () => {
    let cancelled = false;
    const promise = waitForBackoff(2000, async () => { cancelled = true; }, () => cancelled);
    await expect(promise).rejects.toBeInstanceOf(BackoffCancelledError);
  });
});
