// Uses the existing authenticated Chromium CDP session; never launches a profile.
const { chromium } = require('playwright');
(async()=>{
  const browser=await chromium.connectOverCDP('http://127.0.0.1:9224');
  const pages=browser.contexts().flatMap(context=>context.pages());
  const page=pages.find(item=>/chatgpt.com\/admin\/apps/.test(item.url()));
  if(!page) throw Error('CHATGPT_ADMIN_APPS_PAGE_NOT_FOUND');
  const card=page.getByRole('button',{name:/^Estate Comms8 Live/i}).first();
  const count=await card.count();
  if(!count) throw Error('ESTATE_COMMS8_LIVE_CARD_NOT_FOUND');
  await card.scrollIntoViewIfNeeded();
  await card.click();
  await page.waitForTimeout(2500);
  const action=page.getByRole('button',{name:/^(Try in chat|Open in chat|Enable|Attach|Add to chat)$/i}).first();
  if(await action.count()) { await action.scrollIntoViewIfNeeded(); await action.click(); }
  await page.waitForTimeout(5000);
  const pagesAfter=await Promise.all(browser.contexts().flatMap(context=>context.pages()).map(async item=>({url:item.url(),title:item.url().includes('chatgpt.com')?await item.title():''})));
  console.log(JSON.stringify({marker:'UI_ATTACHMENT_ATTEMPTED',card_count:count,action_clicked:await action.count()>0,pages:pagesAfter}));
  process.exit(0);
})().catch(e=>{console.error(e.stack||e.message);process.exitCode=1});
