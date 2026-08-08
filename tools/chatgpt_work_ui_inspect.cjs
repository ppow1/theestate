// Read-only semantic inspector for the existing authenticated ChatGPT CDP session.
(async()=>{
  const clickEstate=process.argv.includes('--click-estate');
  const diagnoseEstate=process.argv.includes('--diagnose-estate');
  const navigateWork=process.argv.includes('--navigate-work');
  const clickPlugins=process.argv.includes('--click-plugins');
  const navigateConversation=process.argv.includes('--navigate-conversation');
  const inspectAppLabel=process.argv.includes('--inspect-app-label');
  const inspectComposer=process.argv.includes('--inspect-composer');
  const clickPlus=process.argv.includes('--click-plus');
  const clickConnect=process.argv.includes('--click-connect');
  const attachApp=process.argv.includes('--attach-app');
  const navigateLivePlugin=process.argv.includes('--navigate-live-plugin');
  const navigateAdmin=process.argv.includes('--navigate-admin');
  const navigateLiveDirectory=process.argv.includes('--navigate-live-directory');
  const clickTry=process.argv.includes('--click-try');
  const targets=await (await fetch('http://127.0.0.1:9224/json/list')).json();
  const target=targets.find(x=>x.type==='page'&&x.url.includes('chatgpt.com')&&(navigateWork || /admin\/apps|plugins|surface=work|\/c\//.test(x.url)));
  if(!target) throw Error('CHATGPT_TARGET_NOT_FOUND');
  const ws=new WebSocket(target.webSocketDebuggerUrl); let id=0; const pending=new Map();
  ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result)}};
  await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
  if (navigateWork || navigateConversation || navigateLivePlugin || navigateAdmin || navigateLiveDirectory) {
    const url=navigateLiveDirectory
      ? 'https://chatgpt.com/apps/estate-comms8-live/asdk_app_6a753722e20c81918521f393e0c46fb3'
      : navigateAdmin
        ? 'https://chatgpt.com/admin/apps'
        : navigateLivePlugin
          ? 'https://chatgpt.com/plugins/plugin_asdk_app_6a727af28db8819188d92bdfd52a950c'
          : navigateConversation
            ? 'https://chatgpt.com/c/6a77314a-9f28-83ea-bced-1cbd2f5035e6'
            : 'https://chatgpt.com/?surface=work';
    const n=++id;
    await new Promise((resolve,reject)=>{
      pending.set(n,{resolve,reject});
      ws.send(JSON.stringify({id:n,method:'Page.navigate',params:{url}}));
    });
    await new Promise(r=>setTimeout(r,6000));
  }
  if (clickPlugins) { const n=++id; await new Promise((resolve,reject)=>{pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method:'Runtime.evaluate',params:{returnByValue:true,expression:`(()=>{const x=[...document.querySelectorAll('button,[role="button"],a')].find(x=>/^Plugins$/i.test((x.innerText||'').trim()));if(!x)return 'not_found';x.click();return 'clicked'})()`}}));}); await new Promise(r=>setTimeout(r,4000)); }
  const expression=clickTry ? `(()=>{const x=[...document.querySelectorAll('button,a,[role="button"]')].find(x=>/^Try in chat$/i.test((x.innerText||'').trim()));if(!x)return JSON.stringify({clicked:false,reason:'try_in_chat_not_found'});x.scrollIntoView({block:'center'});x.click();return JSON.stringify({clicked:true,action:'try_in_chat'})})()` : attachApp ? `(()=>{const x=document.querySelector('#composer-plus-btn,[data-testid="composer-plus-btn"]');if(!x)return JSON.stringify({clicked:false,reason:'composer_plus_not_found'});x.click();setTimeout(()=>{const c=[...document.querySelectorAll('button,a,[role="button"]')].find(x=>/^Connect$/i.test((x.innerText||'').trim()));if(c)c.click();},500);return JSON.stringify({clicked:true,action:'plus_then_connect'})})()` : (clickPlus||clickConnect) ? `(()=>{const x=document.querySelector('#composer-plus-btn,[data-testid="composer-plus-btn"]');if(!x)return JSON.stringify({clicked:false,reason:'composer_plus_not_found'});if(${clickConnect?'true':'false'}){const c=[...document.querySelectorAll('button,a,[role="button"]')].find(x=>/^Connect$/i.test((x.innerText||'').trim()));if(!c)return JSON.stringify({clicked:false,reason:'connect_not_found'});c.click();return JSON.stringify({clicked:true,action:'connect'});}x.click();return JSON.stringify({clicked:true,action:'plus'})})()` : inspectComposer ? `(()=>{const input=document.querySelector('#prompt-textarea[contenteditable="true"],div[contenteditable="true"][aria-label="Chat with ChatGPT"]');return {url:location.href,input:input?.outerHTML?.slice(0,3000),ancestor:input?.parentElement?.parentElement?.parentElement?.parentElement?.outerHTML?.slice(0,12000),nearby:[...document.querySelectorAll('button,[role="button"],a')].map(x=>({text:(x.innerText||'').trim().slice(0,160),aria:x.getAttribute('aria-label'),testid:x.getAttribute('data-testid'),html:x.outerHTML.slice(0,800)})).filter(x=>{const r=x.getBoundingClientRect?.();return r&&r.width>0&&r.height>0&&r.bottom>input?.getBoundingClientRect?.().top-200})}})()` : inspectAppLabel ? `(()=>({url:location.href,nodes:[...document.querySelectorAll('*')].filter(x=>(x.children.length===0)&&/Estate Comms8 Live/i.test((x.innerText||'').trim())).slice(0,20).map(x=>({tag:x.tagName,text:(x.innerText||'').trim(),html:x.parentElement?.outerHTML?.slice(0,1800)}))}))()` : (clickEstate||diagnoseEstate) ? `(()=>{const image=document.querySelector('img[alt="Estate Comms8 Live"]');const app=image?.closest('button,a,[role="button"]')||[...document.querySelectorAll('button,a,[role="button"]')].find(x=>/Estate Comms8 Live/i.test(x.innerText||''));if(!app)return JSON.stringify({clicked:false,reason:'app_card_not_found'});app.scrollIntoView({block:'center'});app.click();return JSON.stringify({clicked:true,text:(app.innerText||'').trim().slice(0,200),url:location.href})})()` : `(()=>({url:location.href,title:document.title,body:(document.body.innerText||'').slice(0,12000),links:[...document.querySelectorAll('a')].map(x=>({text:(x.innerText||'').trim().slice(0,160),href:x.href})).filter(x=>x.text||x.href),app_candidates:[...document.querySelectorAll('button,[role="button"],a')].filter(x=>/Estate Comms8 Live/i.test(x.innerText||'')).slice(0,5).map(x=>({tag:x.tagName,text:(x.innerText||'').trim().slice(0,300),html:x.outerHTML.slice(0,1000)})),buttons:[...document.querySelectorAll('button,[role="button"]')].map(x=>({text:(x.innerText||'').trim().slice(0,160),aria:x.getAttribute('aria-label'),testid:x.getAttribute('data-testid'),disabled:!!x.disabled})).filter(x=>x.text||x.aria||x.testid)}))()`;
  const result=await new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method:'Runtime.evaluate',params:{returnByValue:true,expression}}));});
  if (clickEstate || diagnoseEstate || clickPlus || clickConnect || attachApp || clickTry) { await new Promise(r=>setTimeout(r, 3000)); const follow=await new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method:'Runtime.evaluate',params:{returnByValue:true,expression:`(()=>({url:location.href,body:(document.body.innerText||'').slice(0,8000),dialogs:[...document.querySelectorAll('[role="dialog"]')].map(x=>({text:x.innerText||'',html:x.outerHTML.slice(0,16000)})),controls:[...document.querySelectorAll('button,a,[role="button"],input')].map(x=>({tag:x.tagName,text:(x.innerText||x.value||'').trim().slice(0,160),aria:x.getAttribute('aria-label'),href:x.href||null,disabled:!!x.disabled})).filter(x=>/try in chat|open in chat|enable|attach|add to chat|estate comms8|app|connect/i.test((x.text||'')+' '+(x.aria||'')))}))()`}}));}); console.log(JSON.stringify({target:{title:target.title,url:target.url},ui:result.result?.value,follow:follow.result?.value},null,2)); } else console.log(JSON.stringify({target:{title:target.title,url:target.url},ui:result.result?.value},null,2)); ws.close();
})().catch(e=>{console.error(e.stack||e.message);process.exitCode=1});
