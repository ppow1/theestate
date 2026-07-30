import { describe, expect, it, vi } from 'vitest';
import { completeInteractiveAuthentication, type InteractiveAuthenticationBrowser } from '../src/interactive-auth.js';
import { interactiveLaunchOptions, resolveStableChromeExecutable } from '../src/browser.js';

const browser = (authenticated: boolean, available = true): InteractiveAuthenticationBrowser => ({
  isAvailable: vi.fn(async () => available),
  authenticationState: vi.fn(async () => authenticated ? 'authenticated' : 'unauthenticated'),
});

describe('interactive first-time authentication', () => {
  it('keeps the session available for manual login and verifies success afterward', async () => {
    const b = browser(false);
    b.authenticationState = vi.fn().mockResolvedValueOnce('unauthenticated').mockResolvedValueOnce('authenticated');
    const prompt = vi.fn(async () => '');
    await completeInteractiveAuthentication(b, prompt, vi.fn());
    expect(prompt).toHaveBeenCalledOnce();
    expect(b.authenticationState).toHaveBeenCalledTimes(2);
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

  it('reports a verification page distinctly after the operator confirmation', async () => {
    const b = browser(false);
    b.authenticationState = vi.fn().mockResolvedValueOnce('verification-incomplete').mockResolvedValueOnce('verification-incomplete');
    await expect(completeInteractiveAuthentication(b, vi.fn(async () => ''))).rejects.toThrow('LOGIN_VERIFICATION_INCOMPLETE');
  });

  it('uses a conventional headed desktop configuration for interactive login', () => {
    const options = interactiveLaunchOptions({ chromeExecutablePath: '', profilePath: '' } as any);
    expect(options.headless).toBe(false);
    expect(options.viewport).toEqual({ width: 1400, height: 900 });
    expect(options.deviceScaleFactor).toBe(1);
    expect(options.args).toEqual(['--window-size=1400,900', '--disable-extensions']);
    expect(options.userAgent).toBeUndefined();
    expect(resolveStableChromeExecutable()?.toLowerCase()).toContain('chrome.exe');
  });
});
