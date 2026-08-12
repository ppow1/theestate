(async()=>{
  const v=await fetch('http://127.0.0.1:9224/json/version').then(r=>r.json());
  const ws=new WebSocket(v.webSocketDebuggerUrl); let id=0; const pending=new Map();
  ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}};
  await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
  const call=(method,params={},sid)=>new Promise((r,j)=>{const n=++id;pending.set(n,{resolve:r,reject:j});const msg={id:n,method,params};if(sid)msg.sessionId=sid;ws.send(JSON.stringify(msg))});
  const target=(await call('Target.getTargets')).targetInfos.find(x=>x.type==='page'&&x.url.startsWith('http://127.0.0.1:8080/'));
  const sid=(await call('Target.attachToTarget',{targetId:target.targetId,flatten:true})).sessionId;
  const expression=`(async()=>{
    const fresh=document.querySelector('#new-chat-button,[aria-label="New Chat"],#sidebar-new-chat-button');
    if(fresh) fresh.click();
    await new Promise(r=>setTimeout(r,1200));
    const picker=document.querySelector('[aria-label="Available Tools"]');
    if(picker) picker.click(); await new Promise(r=>setTimeout(r,500));
    return {url:location.href,body:(document.body.innerText||'').slice(-7000),controls:[...document.querySelectorAll('button,[role="button"],input')].map(x=>({text:(x.innerText||'').trim(),aria:x.getAttribute('aria-label'),title:x.getAttribute('title'),id:x.id,type:x.type,checked:x.checked})).filter(x=>x.text||x.aria||x.title||x.type)};
  })()`;
  const out=(await call('Runtime.evaluate',{returnByValue:true,awaitPromise:true,expression},sid)).result.value;
  console.log(JSON.stringify(out)); ws.close();
})().catch(e=>{console.error(e.stack||e.message);process.exitCode=1});
