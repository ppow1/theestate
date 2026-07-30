import type { AuthenticationState } from './browser.js';
export interface InteractiveAuthenticationBrowser {
  isAvailable(): Promise<boolean>;
  authenticationState(): Promise<AuthenticationState>;
}

export async function completeInteractiveAuthentication(
  browser: InteractiveAuthenticationBrowser,
  prompt: () => Promise<string>,
  notify: (message: string) => void = console.log,
) {
  if (await browser.authenticationState()==='authenticated') return;
  if (!await browser.isAvailable()) throw new Error('AUTHENTICATION_REQUIRED: the dedicated browser was closed before login completed');

  notify('The dedicated ChatGPT browser profile is open and awaiting manual login.');
  notify('Complete login and any security challenge in that window, confirm the conversation interface is visible, then return here.');
  await prompt();

  if (!await browser.isAvailable()) throw new Error('AUTHENTICATION_REQUIRED: the dedicated browser was closed before login completed');
  const state=await browser.authenticationState();
  if (state==='verification-incomplete') throw new Error('LOGIN_VERIFICATION_INCOMPLETE: complete the browser verification in the dedicated profile, then run initialization again');
  if (state!=='authenticated') throw new Error('AUTHENTICATION_REQUIRED: login was not confirmed; complete login in the dedicated browser, then run initialization again');
}
