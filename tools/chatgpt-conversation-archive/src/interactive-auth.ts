export interface InteractiveAuthenticationBrowser {
  isAvailable(): Promise<boolean>;
  isAuthenticated(): Promise<boolean>;
}

export async function completeInteractiveAuthentication(
  browser: InteractiveAuthenticationBrowser,
  prompt: () => Promise<string>,
  notify: (message: string) => void = console.log,
) {
  if (await browser.isAuthenticated()) return;
  if (!await browser.isAvailable()) throw new Error('AUTHENTICATION_REQUIRED: the dedicated browser was closed before login completed');

  notify('The dedicated ChatGPT browser profile is open and awaiting manual login.');
  notify('Complete login and any security challenge in that window, confirm the conversation interface is visible, then return here.');
  await prompt();

  if (!await browser.isAvailable()) throw new Error('AUTHENTICATION_REQUIRED: the dedicated browser was closed before login completed');
  if (!await browser.isAuthenticated()) throw new Error('AUTHENTICATION_REQUIRED: login was not confirmed; complete login in the dedicated browser, then run initialization again');
}
