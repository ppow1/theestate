(async()=>{
 const fs=require('node:fs');
 const target=(await fetch('http://127.0.0.1:9224/json/list').then(r=>r.json())).find(x=>x.type==='page'&&x.url.startsWith('http://127.0.0.1:8080/'));
 if(!target)throw Error('Open WebUI page not found');
 const ws=new WebSocket(target.webSocketDebuggerUrl);let id=0;const pending=new Map();
 ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}};
 await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
 const call=(m,p)=>new Promise((r,j)=>{const n=++id;pending.set(n,{resolve:r,reject:j});ws.send(JSON.stringify({id:n,method:m,params:p}))});
 const ev=async expression=>(await call('Runtime.evaluate',{returnByValue:true,awaitPromise:true,expression})).result?.value;
 const names=['estate_comms8_create_reasoning_request','estate_comms8_list_requests','estate_comms8_read_request','estate_comms8_claim_request','estate_comms8_acknowledge_request','estate_comms8_respond_request','estate_comms8_resolve_request'];
 const payload={model:'estate/grace-grounded-test',messages:[{role:'user',content:'Use the exact Estate Comms8 Live action estate_comms8_read_request with request_id="ec8-3f24f4aadcd947c9". Return the authoritative result visibly; do not claim, acknowledge, respond, resolve, or simulate.'}],stream:false,tool_ids:names.map(n=>'server:mcp:estate-comms8-live|'+n),params:{function_calling:'native'}};
 const encoded=JSON.stringify(payload);
 const expression='fetch("/api/chat/completions",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify('+encoded+')}).then(async r=>({status:r.status,body:await r.json()}))';
 const result=await ev(expression);const msg=result?.body?.choices?.[0]?.message||{};
 const toolCall=(msg.tool_calls||[])[0];
 const follow={...payload,messages:[payload.messages[0],{role:'assistant',content:null,tool_calls:msg.tool_calls},{role:'tool',tool_call_id:toolCall?.id||'call-read',name:'estate_comms8_read_request',content:'{"request_id":"ec8-3f24f4aadcd947c9","workflow_id":"estate-comms8-live-grace-chatgpt-roundtrip-test","state":"queued"}'}]};
 const followExpr='fetch("/api/chat/completions",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify('+JSON.stringify(follow)+')}).then(async r=>({status:r.status,body:await r.json()}))';
 const followResult=await ev(followExpr);const followMsg=followResult?.body?.choices?.[0]?.message||{};
 const out={initial_status:result?.status,initial_finish_reason:result?.body?.choices?.[0]?.finish_reason||null,initial_tool_call_names:(msg.tool_calls||[]).map(x=>x.function?.name),follow_status:followResult?.status,follow_finish_reason:followResult?.body?.choices?.[0]?.finish_reason||null,follow_content:followMsg.content||'',follow_contains_request_id:(followMsg.content||'').includes('ec8-3f24f4aadcd947c9'),no_mutation:true};
 fs.mkdirSync('A:/theestate-data/openwebui-mcp-action-binding-20260807',{recursive:true});fs.writeFileSync('A:/theestate-data/openwebui-mcp-action-binding-20260807/grace-live-read-acceptance.json',JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify(out));process.exit(0)
})().catch(e=>{console.error(e.message);process.exitCode=1});
