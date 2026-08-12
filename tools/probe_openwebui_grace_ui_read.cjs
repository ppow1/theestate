(async()=>{
 const v=await fetch('http://127.0.0.1:9224/json/version').then(r=>r.json());
 const ws=new WebSocket(v.webSocketDebuggerUrl); let id=0; const pending=new Map();
 ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}};
 await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
 const call=(method,params={},sessionId=null)=>new Promise((r,j)=>{const n=++id;pending.set(n,{resolve:r,reject:j});const msg={id:n,method,params};if(sessionId)msg.sessionId=sessionId;ws.send(JSON.stringify(msg))});
 const targets=(await call('Target.getTargets')).targetInfos||[];
 const t=targets.find(x=>x.type==='page'&&x.url.startsWith('http://127.0.0.1:8080/'));
 if(!t) throw Error('Open WebUI target not found');
 const sid=(await call('Target.attachToTarget',{targetId:t.targetId,flatten:true})).sessionId;
 const run=async expression=>(await call('Runtime.evaluate',{returnByValue:true,awaitPromise:true,expression},sid)).result?.value;
 const result=await run(`(async()=>{
   const sleep=ms=>new Promise(r=>setTimeout(r,ms));
   window.__estateTrace=[]; const origFetch=window.fetch.bind(window); window.fetch=async(...args)=>{const req=args[0],opt=args[1]||{};let meta={url:String(req),method:opt.method||'GET'};if(opt.body&&typeof opt.body==='string'){try{const b=JSON.parse(opt.body);meta.body={model:b.model,stream:b.stream,tool_choice:b.tool_choice,tool_ids:b.tool_ids,tools:Array.isArray(b.tools)?b.tools.map(x=>x.function?.name||x.name||x.type):null,message_roles:Array.isArray(b.messages)?b.messages.map(x=>({role:x.role,tool_calls:Array.isArray(x.tool_calls)?x.tool_calls.map(t=>t.function?.name):null})):null}}catch{}}const res=await origFetch(...args);const clone=res.clone();clone.text().then(t=>{let q={url:String(req),response_status:res.status,content_type:res.headers.get('content-type')};try{const b=JSON.parse(t);q.response={keys:Object.keys(b),error:b.error||null,choices:(b.choices||[]).map(c=>({finish_reason:c.finish_reason,role:c.message?.role,tool_calls:(c.message?.tool_calls||[]).map(x=>x.function?.name),content_present:!!c.message?.content}))}}catch{q.response_text_prefix=t.slice(0,300)}window.__estateTrace.push(q)});window.__estateTrace.push(meta);return res};
   const click=s=>{const e=document.querySelector(s);if(!e) throw Error('missing '+s);e.click()};
   click('#new-chat-button'); await sleep(700);
   click('#model-selector-0-button'); await sleep(300);
   const selector=document.querySelector('[aria-label="Select Grace model"]'); if(!selector) throw Error('Grace model option not found'); selector.click(); await sleep(700);
   const input=document.querySelector('#chat-input'); if(!input) throw Error('missing chat input');
   input.focus(); document.execCommand('insertText',false,'Use the Estate Comms8 Live MCP tool estate_comms8_read_request now. Read request ID: ec8-6a850f4ab32743d2. Return only the authoritative MCP result. Perform no mutation.'); input.dispatchEvent(new Event('input',{bubbles:true})); await sleep(300);
   click('#send-message-button'); await sleep(12000);
   const texts=[...document.querySelectorAll('.chat-assistant,[id^="message-"]')].slice(-8).map(e=>({text:(e.innerText||'').slice(0,2000),html:(e.outerHTML||'').slice(0,500)}));
   const body=(document.body.innerText||'').slice(-6000);
   return {url:location.href,body,texts,trace:window.__estateTrace};
 })().catch(e=>({error:e.message}))`);
 console.log(JSON.stringify(result)); ws.close();
})().catch(e=>{console.error(e.stack||e.message);process.exitCode=1});
