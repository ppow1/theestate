// Navigate an existing authenticated ChatGPT CDP target to the canonical Live app.
(async()=>{
  const version=await fetch('http://127.0.0.1:9224/json/version').then(r=>r.json());
  const targets=await fetch('http://127.0.0.1:9224/json/list').then(r=>r.json());
  const target=targets.find(x=>x.type==='page' && /chatgpt\.com\/(c\/|plugins\/|apps\/)/.test(x.url));
  if(!target) throw Error('CHATGPT_TARGET_NOT_FOUND');
  const ws=new WebSocket(target.webSocketDebuggerUrl); let id=0;
  const pending=new Map(); ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result)}};
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject});
  const call=(method,params)=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}))});
  await call('Page.navigate',{url:'https://chatgpt.com/apps/estate-comms8-live/asdk_app_6a753722e20c81918521f393e0c46fb3'});
  await new Promise(r=>setTimeout(r,7000));
  const result=await call('Runtime.evaluate',{returnByValue:true,expression:'JSON.stringify({url:location.href,title:document.title,body:(document.body?.innerText||"").slice(0,1500)})'});
  console.log(JSON.stringify({target_url:target.url,after:JSON.parse(result.result?.value||'{}')})); ws.close();
})().catch(e=>{console.error(e.stack||e.message);process.exitCode=1});
