export function isBrowserContextLoss(error: unknown): boolean {
  return /target page, context or browser has been closed|browser has been closed|context has been closed|target closed|page has been closed|browser disconnected/i.test(String(error));
}
