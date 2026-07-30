import { describe, expect, it, vi } from 'vitest';
import { completeInteractiveAuthentication, type InteractiveAuthenticationBrowser } from '../src/interactive-auth.js';

const browser = (authenticated: boolean, available = true): InteractiveAuthenticationBrowser => ({
  isAvailable: vi.fn(async () => available),
  isAuthenticated: vi.fn(async () => authenticated),
});

describe('interactive first-time authentication', () => {
  it('keeps the session available for manual login and verifies success afterward', async () => {
    const b = browser(false);
    b.isAuthenticated = vi.fn().mockResolvedValueOnce(false).mockResolvedValueOnce(true);
    const prompt = vi.fn(async () => '');
    await completeInteractiveAuthentication(b, prompt, vi.fn());
    expect(prompt).toHaveBeenCalledOnce();
    expect(b.isAuthenticated).toHaveBeenCalledTimes(2);
  });

  it('returns a clear error when the operator closes the browser', async () => {
    const b = browser(false, false);
    await expect(completeInteractiveAuthentication(b, vi.fn(async () => ''))).rejects.toThrow('dedicated browser was closed');
  });

  it('returns a clear error when Enter is pressed before authentication', async () => {
    const b = browser(false);
    await expect(completeInteractiveAuthentication(b, vi.fn(async () => ''))).rejects.toThrow('login was not confirmed');
  });

  it('does not prompt an already authenticated profile', async () => {
    const b = browser(true);
    const prompt = vi.fn(async () => '');
    await completeInteractiveAuthentication(b, prompt, vi.fn());
    expect(prompt).not.toHaveBeenCalled();
  });
});
