'use strict';

// Keep UI knowledge in one place. Open WebUI changes its generated classes
// frequently, so selectors prefer accessible names and semantic attributes.
const SELECTORS = Object.freeze({
  composer: [
    'textarea[placeholder*="message" i]',
    'textarea[aria-label*="message" i]',
    '[contenteditable="true"][role="textbox"]',
    '[contenteditable="true"]'
  ],
  send: [
    '#send-message-button[type="submit"]',
    'form button[type="submit"]:not(#generate-message-pair-button)',
    'button[aria-label*="send" i]',
    'button[title*="send" i]'
  ],
  stop: [
    'button[aria-label*="stop" i]',
    'button[title*="stop" i]'
  ],
  newConversation: [
    'a[href="/"]',
    'a[href$="/"]',
    'button[aria-label*="new chat" i]',
    'button[title*="new chat" i]'
  ],
  assistant: [
    '[data-message-author-role="assistant"]',
    '[data-role="assistant"]',
    '[class~="chat-assistant"]',
    '#response-content-container',
    'article[data-message-id]'
  ],
  user: [
    '[data-message-author-role="user"]',
    '[data-role="user"]'
  ],
  modelPicker: [
    'button[aria-label*="model" i]',
    'button[title*="model" i]',
    '[data-testid*="model" i]'
  ]
});

async function firstVisible(page, candidates) {
  for (const selector of candidates) {
    const locator = page.locator(selector);
    const count = await locator.count().catch(() => 0);
    for (let i = 0; i < count; i++) {
      if (await locator.nth(i).isVisible().catch(() => false)) return locator.nth(i);
    }
  }
  return null;
}

async function visibleText(page) {
  return (await page.locator('body').innerText().catch(() => '')) || '';
}

module.exports = {SELECTORS, firstVisible, visibleText};
