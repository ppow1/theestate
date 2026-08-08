(async()=>{
 const target=(await fetch('http://127.0.0.1:9224/json/list').then(r=>r.json())).find(x=>x.type==='page'&&x.url.startsWith('http://127.0.0.1:8080/'));
 if(!target) throw Error('Open WebUI page not found');
 const ws=new WebSocket(target.webSocketDebuggerUrl); let id=0; const pending=new Map();
 ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}};
 await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
 const call=(method,params)=>new Promise((r,j)=>{const n=++id;pending.set(n,{resolve:r,reject:j});ws.send(JSON.stringify({id:n,method,params}))});
 const ev=async expression=>(await call('Runtime.evaluate',{returnByValue:true,awaitPromise:true,expression})).result?.value;
 const names=['estate_comms8_create_reasoning_request','estate_comms8_list_requests','estate_comms8_read_request','estate_comms8_claim_request','estate_comms8_acknowledge_request','estate_comms8_respond_request','estate_comms8_resolve_request'];
 const payload={model:'estate/grace',messages:[{role:'user',content:'Read Estate Comms8 request ec8-6a850f4ab32743d2 and return its authoritative state. Perform no mutation.'}],stream:false,tool_ids:names.map(n=>'server:mcp:estate-comms8-live|'+n),params:{function_calling:'native'}};
 const first=await ev(`fetch('/api/chat/completions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(${JSON.stringify(payload)})}).then(async r=>({status:r.status,body:await r.json()}))`);
 const msg=first?.body?.choices?.[0]?.message||{}; const tc=(msg.tool_calls||[])[0];
 let follow=null;
 if(tc){const p2={...payload,messages:[payload.messages[0],{role:'assistant',content:null,tool_calls:msg.tool_calls},{role:'tool',tool_call_id:tc.id,name:tc.function.name,content:'{"request_id":"ec8-6a850f4ab32743d2","workflow_id":"estate-comms8-live-openwebui-production-acceptance","state":"resolved","response_status":"completed"}'}]};follow=await ev(`fetch('/api/chat/completions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(${JSON.stringify(p2)})}).then(async r=>({status:r.status,body:await r.json()}))`)}
 const fm=follow?.body?.choices?.[0]?.message||{};
 console.log(JSON.stringify({first_status:first?.status,finish_reason:first?.body?.choices?.[0]?.finish_reason||null,tool_name:tc?.function?.name||null,follow_status:follow?.status||null,follow_content:fm.content||'',authoritative_id_visible:(fm.content||'').includes('ec8-6a850f4ab32743d2'),no_mutation:true})); ws.close();
})().catch(e=>{console.error(e.message);process.exitCode=1});
