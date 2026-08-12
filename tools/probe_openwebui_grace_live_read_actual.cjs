(async()=>{
  const target=(await fetch('http://127.0.0.1:9224/json/list').then(r=>r.json())).find(x=>x.type==='page'&&x.url.startsWith('http://127.0.0.1:8080/'));
  if(!target) throw Error('Open WebUI page not found');
  const ws=new WebSocket(target.webSocketDebuggerUrl); let id=0; const pending=new Map();
  ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}};
  await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
  const call=(method,params)=>new Promise((r,j)=>{const n=++id;pending.set(n,{resolve:r,reject:j});ws.send(JSON.stringify({id:n,method,params}))});
  const evaluate=async expression=>(await call('Runtime.evaluate',{returnByValue:true,awaitPromise:true,expression})).result?.value;
  const names=['estate_comms8_create_reasoning_request','estate_comms8_list_requests','estate_comms8_read_request','estate_comms8_claim_request','estate_comms8_acknowledge_request','estate_comms8_respond_request','estate_comms8_resolve_request'];
  const payload={model:'estate/grace',messages:[{role:'user',content:'Use Estate Comms8 Live and call estate_comms8_read_request with request_id="ec8-6a850f4ab32743d2". Return only the authoritative result. Perform no mutation.'}],stream:true,tool_ids:names.map(n=>'server:mcp:estate-comms8-live|'+n),params:{function_calling:'native'}};
  const result=await evaluate(`fetch('/api/chat/completions',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(${JSON.stringify(payload)})}).then(async r=>({status:r.status,body:await r.text()}))`);
  console.log(JSON.stringify({status:result?.status,bytes:(result?.body||'').length,has_native_tool_call:(result?.body||'').includes('estate_comms8_read_request'),has_authoritative_id:(result?.body||'').includes('ec8-6a850f4ab32743d2'),body_prefix:(result?.body||'').slice(0,2500)}));
  ws.close();
})().catch(e=>{console.error(e.stack||e.message);process.exitCode=1});
