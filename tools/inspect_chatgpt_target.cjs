(async()=>{
const targets=await fetch('http://127.0.0.1:9224/json/list').then(r=>r.json());
const target=targets.find(x=>x.type==='page'&&x.url.includes('surface=work'))
  ||targets.find(x=>x.type==='page'&&/Estate Comms8/i.test(x.title));
if(!target) throw Error('work_target_missing');
const ws=new WebSocket(target.webSocketDebuggerUrl); let id=0; const pending=new Map();
ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}};
await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
const call=(method,params={})=>new Promise((r,j)=>{const n=++id;pending.set(n,{resolve:r,reject:j});ws.send(JSON.stringify({id:n,method,params}))});
const result=await call('Runtime.evaluate',{returnByValue:true,awaitPromise:true,expression:`(()=>({
 url:location.href,
 title:document.title,
 body:(document.body.innerText||'').slice(0,4000),
    inputs:[...document.querySelectorAll('textarea,input,[contenteditable="true"]')].map(x=>({tag:x.tagName,id:x.id,role:x.getAttribute('role'),aria:x.getAttribute('aria-label'),placeholder:x.getAttribute('placeholder'),contenteditable:x.getAttribute('contenteditable'),hidden:x.offsetParent===null,aria_hidden_ancestor:!!x.closest('[aria-hidden="true"]'),aria_hidden_chain:[...function*(){let n=x;while(n){if(n.hasAttribute('aria-hidden'))yield {tag:n.tagName,id:n.id,value:n.getAttribute('aria-hidden'),class:(n.className||'').toString().slice(0,160)};n=n.parentElement;}}()],disabled:x.disabled||false})),
 buttons:[...document.querySelectorAll('button')].map(x=>({text:(x.innerText||'').trim().slice(0,120),aria:x.getAttribute('aria-label'),disabled:x.disabled,hidden:x.offsetParent===null})).filter(x=>x.text||x.aria).slice(-80),
 dialogs:[...document.querySelectorAll('[role="dialog"]')].map(x=>(x.innerText||'').slice(0,1000))
}))()`});
console.log(JSON.stringify(result.result?.value||result,null,2)); ws.close();
})().catch(e=>{console.error(e.stack||e);process.exitCode=1});
