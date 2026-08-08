// Bounded recovery of the existing ChatGPT tab to its prior conversation.
// This only restores a browser target; it does not submit a prompt.
(async()=>{
  const targets=await fetch('http://127.0.0.1:9224/json/list').then(r=>r.json());
  const target=targets.find(x=>x.type==='page'&&x.url==='https://chatgpt.com/plugins')
    ||targets.find(x=>x.type==='page'&&x.url.startsWith('https://chatgpt.com/'));
  if(!target) throw Error('chatgpt_target_unavailable');
  const ws=new WebSocket(target.webSocketDebuggerUrl); let id=0; const pending=new Map();
  ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}};
  await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
  const call=(method,params={})=>new Promise((r,j)=>{const n=++id;pending.set(n,{resolve:r,reject:j});ws.send(JSON.stringify({id:n,method,params}))});
  const history=await call('Page.getNavigationHistory');
  const entries=(history.entries||[]).filter(x=>/^https:\/\/chatgpt\.com\/c\//.test(x.url));
  if(!entries.length) throw Error('chatgpt_conversation_history_unavailable');
  const tools=['estate_comms8_create_reasoning_request','estate_comms8_list_requests','estate_comms8_read_request','estate_comms8_claim_request','estate_comms8_acknowledge_request','estate_comms8_respond_request','estate_comms8_resolve_request'];
  let selected=null, current=null;
  for(const entry of [...entries].reverse()) {
    await call('Page.navigateToHistoryEntry',{entryId:entry.id});
    await new Promise(r=>setTimeout(r,1500));
    const probe=await call('Runtime.evaluate',{returnByValue:true,expression:`(()=>{const b=document.body.innerText||'';return {url:location.href,tools:${JSON.stringify(tools)}.filter(x=>b.includes(x)).length}})()`});
    const value=probe.result?.value||{};
    if(value.tools===tools.length){selected=entry;current=value;break;}
  }
  if(!selected) {
    await call('Page.navigate',{url:'https://chatgpt.com/?surface=work'});
    await new Promise(r=>setTimeout(r,7000));
    const probe=await call('Runtime.evaluate',{returnByValue:true,expression:`(()=>{const b=document.body.innerText||'';return {url:location.href,tools:${JSON.stringify(tools)}.filter(x=>b.includes(x)).length}})()`});
    const value=probe.result?.value||{};
    if(value.tools!==tools.length) throw Error('chatgpt_comms8_work_target_not_found');
    current=value;
  }
  await new Promise(r=>setTimeout(r,2000));
  console.log(JSON.stringify({marker:'CHATGPT_WORK_TARGET_RECOVERED',target_url:current.url,history_entry_id:selected.id,history_candidates:entries.length,tool_count:current.tools}));
  ws.close();
})().catch(e=>{console.error(e.stack||e);process.exitCode=1});
