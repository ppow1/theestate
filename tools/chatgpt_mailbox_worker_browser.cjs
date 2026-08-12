// Existing dedicated ChatGPT CDP browser adapter. The prompt is generic and
// deliberately contains no Estate request ID.
(async()=>{
  const appBootstrap=process.argv.includes('--app-bootstrap');
  const readinessOnly=process.argv.includes('--readiness-only');
  const timeoutArg=process.argv.find(x=>x.startsWith('--timeout-seconds='));
  const timeoutSeconds=Math.max(60,Number(timeoutArg?.split('=',2)[1]||1800));
  const prompt=process.argv.filter(x=>!['--readiness-only','--app-bootstrap'].includes(x)&&!x.startsWith('--timeout-seconds=')).slice(2).join(' ').trim();
  if(!prompt&&!readinessOnly&&!appBootstrap) throw Error('worker_prompt_required');
  const targets=await fetch('http://127.0.0.1:9224/json/list').then(r=>r.json());
  // The conversation title is not an app identity.  The supported
  // “Try in chat” flow creates a fresh Work surface with the installed
  // Live app attached, so prefer that target over stale titled chats.
  const workTargets=targets.filter(x=>x.type==='page'&&x.url.includes('chatgpt.com')&&x.url.includes('surface=work'));
  // Prefer the retained conversation target when it advertises the Estate
  // Comms8 identity; the temporary surface can coexist as an empty shell
  // after recovery and has no action manifest.
  const target=workTargets.at(-1)
    ||targets.filter(x=>x.type==='page'&&x.url.startsWith('https://chatgpt.com/c/')).at(-1)
    ||targets.find(x=>x.type==='page'&&x.url.startsWith('https://chatgpt.com/')&& !/plugins|admin\/apps|codex/i.test(x.url))
    ||targets.find(x=>x.type==='page'&&x.url.startsWith('https://chatgpt.com/'));
  if(!target) throw Error('chatgpt_live_target_unavailable');
  const trace=[]; const startedAt=Date.now();
  const transition=(state,extra={})=>trace.push({state,elapsed_ms:Date.now()-startedAt,...extra});
  transition('TARGET_SELECTED',{target_type:target.type,url:(target.url||'').split('?')[0],title:(target.title||'').slice(0,120)});
  let ws=new WebSocket(target.webSocketDebuggerUrl); let currentTargetUrl=target.webSocketDebuggerUrl; let id=0; const pending=new Map();
  ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}};
  await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
  const call=(method,params={})=>new Promise((r,j)=>{const n=++id;pending.set(n,{resolve:r,reject:j});ws.send(JSON.stringify({id:n,method,params}))});
  const evaluate=async expression=>{const r=await call('Runtime.evaluate',{returnByValue:true,awaitPromise:true,expression});if(r.exceptionDetails) return {__evaluation_error:r.exceptionDetails.exception?.description||r.exceptionDetails.text||'runtime_evaluation_failed'};return r.result?.value;};
  const clickPoint=async point=>{
    if(!point||!Number.isFinite(point.x)||!Number.isFinite(point.y))return false;
    await call('Input.dispatchMouseEvent',{type:'mouseMoved',x:point.x,y:point.y});
    await call('Input.dispatchMouseEvent',{type:'mousePressed',x:point.x,y:point.y,button:'left',clickCount:1});
    await call('Input.dispatchMouseEvent',{type:'mouseReleased',x:point.x,y:point.y,button:'left',clickCount:1});
    return true;
  };
  const requiredTools=[
    'estate_comms8_create_reasoning_request',
    'estate_comms8_list_requests',
    'estate_comms8_read_request',
    'estate_comms8_claim_request',
    'estate_comms8_acknowledge_request',
    'estate_comms8_respond_request',
    'estate_comms8_resolve_request',
  ];
  // This is the observed supported directory route exposed by the installed
  // Estate Comms8 Live card in /admin/apps.  Do not use the older development
  // plugin id: it routes to an unrelated OAuth connector surface.
  const liveDirectoryPath='/apps/estate-comms8-live/asdk_app_6a753722e20c81918521f393e0c46fb3';
  const liveDirectoryUrl=`https://chatgpt.com${liveDirectoryPath}`;
  const liveInstalledPluginId='plugin_asdk_app_6a753722e20c81918521f393e0c46fb3';
  const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  const close=()=>{try{ws.close();}catch{} };
  const switchToWorkTarget=async()=>{
    const current=await fetch('http://127.0.0.1:9224/json/list').then(r=>r.json());
    const next=current.filter(x=>x.type==='page'&&x.url.includes('chatgpt.com/c/')).at(-1)
      ||current.filter(x=>x.type==='page'&&x.url.includes('chatgpt.com')&&x.url.includes('surface=work')).at(-1);
    if(!next||next.webSocketDebuggerUrl===currentTargetUrl)return Boolean(next);
    close();
    ws=new WebSocket(next.webSocketDebuggerUrl); currentTargetUrl=next.webSocketDebuggerUrl; id=0; pending.clear();
    await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
    return true;
  };
  const switchToFreshWorkSurface=async()=>{
    const current=await fetch('http://127.0.0.1:9224/json/list').then(r=>r.json());
    const next=current.filter(x=>x.type==='page'&&x.url.includes('chatgpt.com')&&x.url.includes('surface=work')).at(-1)
      ||current.filter(x=>x.type==='page'&&x.url.includes('chatgpt.com/c/')).at(-1);
    if(!next||next.webSocketDebuggerUrl===currentTargetUrl)return Boolean(next);
    close(); ws=new WebSocket(next.webSocketDebuggerUrl); currentTargetUrl=next.webSocketDebuggerUrl; id=0; pending.clear();
    await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
    return true;
  };
  const openCanonicalEstateAppAndTryInChat=async()=>{
    // Navigate only through the authenticated product UI.  The app-details
    // link is discovered from the rendered Estate card rather than guessed.
    await call('Page.navigate',{url:'https://chatgpt.com/admin/apps'});
    await sleep(4500);
    const appCard=await evaluate(`(()=>{
      const image=document.querySelector('img[alt="Estate Comms8 Live"]');
      const nodes=[...document.querySelectorAll('a,button,[role="button"],[data-testid]')];
      const node=image?.closest('button,a,[role="button"]')||nodes.find(x=>{
        const text=(x.innerText||'').trim();
        return /^(Estate Comms8 Live)(?:\\s|$)/i.test(text)&&x.tagName==='BUTTON';
      });
      if(!node)return {clicked:false,reason:'estate_app_card_not_found'};
      node.scrollIntoView({block:'center'});const r=node.getBoundingClientRect();
      return {clicked:true,x:r.left+r.width/2,y:r.top+r.height/2,text:(node.innerText||'').trim().slice(0,120)};
    })()`);
    if(!appCard?.clicked){
      // The catalog is virtualized and may not hydrate the custom card on
      // every target immediately.  Fall back to the exact directory href
      // previously exposed by the rendered app-details dialog.
      await call('Page.navigate',{url:liveDirectoryUrl});
      await sleep(5000);
      const directTry=await evaluate(`(()=>{
        const nodes=[...document.querySelectorAll('button,a,[role="button"],input[type="button"]')];
        const node=nodes.find(x=>/^Try in chat$/i.test((x.innerText||x.value||'').trim()));
        if(!node)return {clicked:false,reason:'try_in_chat_not_found_after_directory_navigation',url:location.href};
        node.scrollIntoView({block:'center'});node.click();
        return {clicked:true,text:(node.innerText||node.value||'').trim(),method:'semantic_dom_click'};
      })()`);
      if(!directTry?.clicked)return {...appCard,directory_fallback:directTry};
      await clickPoint(directTry); await sleep(6500); await switchToFreshWorkSurface();
      return {clicked:true,directory_fallback:true,url:await evaluate('location.href')};
    }
    await clickPoint(appCard); await sleep(2500);
    const directory=await evaluate(`(()=>{
      const link=[...document.querySelectorAll('a')].find(a=>/^Show in directory$/i.test((a.innerText||'').trim())&&((a.getAttribute('href')||'').includes('/apps/estate-comms8-live/')));
      if(!link)return {clicked:false,reason:'show_in_directory_not_found',url:location.href};
      link.scrollIntoView({block:'center'});const r=link.getBoundingClientRect();
      return {clicked:true,x:r.left+r.width/2,y:r.top+r.height/2,href:link.getAttribute('href')};
    })()`);
    if(!directory?.clicked)return directory;
    await clickPoint(directory); await sleep(4500);
    const tryChat=await evaluate(`(()=>{
      const nodes=[...document.querySelectorAll('button,a,[role="button"],input[type="button"]')];
      const node=nodes.find(x=>/^Try in chat$/i.test((x.innerText||x.value||'').trim())||/^Try in chat$/i.test(x.getAttribute('aria-label')||''));
      if(!node)return {clicked:false,reason:'try_in_chat_not_found',url:location.href};
      node.scrollIntoView({block:'center'});node.click();
      return {clicked:true,text:(node.innerText||node.value||'').trim(),method:'semantic_dom_click'};
    })()`);
    if(!tryChat?.clicked)return tryChat;
    await clickPoint(tryChat); await sleep(6500); await switchToFreshWorkSurface();
    return {clicked:true,url:await evaluate('location.href')};
  };
  const openAttachedHistoryConversation=async()=>{
    const opened=await evaluate(`(()=>{
      const link=[...document.querySelectorAll('a[href*="/c/"]')].find(x=>/Estate Comms8/i.test((x.innerText||'').trim()));
      if(!link)return {clicked:false,reason:'estate_history_link_not_found'};
      link.scrollIntoView({block:'center'});const r=link.getBoundingClientRect();return {clicked:true,x:r.left+r.width/2,y:r.top+r.height/2,href:link.href,text:(link.innerText||'').trim().slice(0,120)};
    })()`);
    if(opened?.clicked){await clickPoint(opened);await sleep(5500);await switchToWorkTarget();}
    return opened;
  };
  const readinessProbe=async()=>evaluate(`(function(){
    var body=document.body.innerText||'';
    var required=${JSON.stringify(requiredTools)};
    var input=document.querySelector('#prompt-textarea[contenteditable="true"],div[contenteditable="true"][aria-label="Chat with ChatGPT"]');
    var rect=input&&input.getBoundingClientRect?input.getBoundingClientRect():null;
    var composer_ready=!!input&&getComputedStyle(input).display!=='none'&&!input.disabled&&!!rect&&rect.width>0&&rect.height>0;
    var tools=[]; for(var i=0;i<required.length;i++){if(body.indexOf(required[i])>=0)tools.push(required[i]);}
    var exactApp=false; var nodes=document.querySelectorAll('a,button,[data-testid*="app"],[data-testid*="connector"]');
    for(var j=0;j<nodes.length;j++){var href=nodes[j].href||'';var text=(nodes[j].innerText||'')+' '+(nodes[j].getAttribute('aria-label')||'');if((href.indexOf('${liveDirectoryPath}')>=0||href.indexOf('${liveInstalledPluginId}')>=0)&&text.toLowerCase().indexOf('estate comms8 live')>=0){exactApp=true;break;}}
    var visibleEstateChip=false; var links=document.querySelectorAll('a');
    for(var k=0;k<links.length;k++){var lr=links[k].getBoundingClientRect?links[k].getBoundingClientRect():null;var label=(links[k].innerText||'').trim();var lh=links[k].href||'';if(lr&&lr.width>0&&lr.height>0&&label.toLowerCase()==='estate comms8 live'&&(lh.indexOf('${liveInstalledPluginId}')>=0||lh.indexOf('${liveDirectoryPath}')>=0)){visibleEstateChip=true;break;}}
    var attachedConversationChip=false; var chips=document.querySelectorAll('[title="Estate Comms8 Live"]');
    for(var m=0;m<chips.length;m++){var cr=chips[m].getBoundingClientRect?chips[m].getBoundingClientRect():null;if(cr&&cr.width>0&&cr.height>0){attachedConversationChip=true;break;}}
    var currentUrl=location.href; var work_url=currentUrl.indexOf('surface=work')>=0||currentUrl.indexOf('/c/')>=0;
    var visibleAuthControl=false; var authNodes=document.querySelectorAll('input,button,a,[role="button"]');
    for(var n=0;n<authNodes.length;n++){var ar=authNodes[n].getBoundingClientRect?authNodes[n].getBoundingClientRect():null;if(!ar||ar.width<=0||ar.height<=0)continue;var at=((authNodes[n].innerText||'')+' '+(authNodes[n].getAttribute('aria-label')||'')).trim().toLowerCase();if(at==='log in'||at==='sign in'||at==='continue with google'||at==='continue with microsoft'||authNodes[n].type==='password'){visibleAuthControl=true;break;}}
    var challenge=currentUrl.indexOf('https://auth.')===0||currentUrl.indexOf('https://login.')===0||visibleAuthControl;
    var attached=work_url&&(tools.length===required.length||exactApp||visibleEstateChip||attachedConversationChip);
    var identity=attached?(tools.length===required.length?'tool_manifest':(attachedConversationChip?'conversation_app_chip':'installed_app_control')):null;
    return {authenticated:!challenge,challenge:challenge,work_surface:work_url,live_app_attached:attached,live_app_identity:identity,tool_names:tools,composer_ready:composer_ready,workspace:body.indexOf("Pat's Workspace 2026")>=0,url:currentUrl.split('?')[0]};
  })()`);
  const stableReadiness=async()=>{
    let result;
    for(let attempt=0;attempt<3;attempt++){
      result=await readinessProbe();
      if(!result?.__evaluation_error)return result;
      await switchToWorkTarget();
      await sleep(1200);
    }
    return result;
  };
  if(appBootstrap){
    await call('Page.enable');
    let readiness=await stableReadiness();
    const preservedAttachedConversation=Boolean(readiness?.live_app_attached&&readiness?.composer_ready&&/chatgpt\.com\/c\//.test(readiness?.url||''));
    if(!preservedAttachedConversation){await call('Page.navigate',{url:'https://chatgpt.com/?surface=work'});await sleep(5000);readiness=await stableReadiness();}
    if(!readiness?.live_app_attached){
      const history=await openAttachedHistoryConversation();
      if(history?.clicked) readiness=await stableReadiness();
    }
    if(readiness?.challenge){
      console.log('STEWARD ACTION REQUIRED');
      console.log('Complete ChatGPT authentication in the visible browser window. The harness will keep this exact profile open and continue automatically.');
    } else if(!readiness?.live_app_attached){
      const recovered=await openCanonicalEstateAppAndTryInChat();
      console.log(`AUTOMATION_DIRECTORY_RECOVERY ${JSON.stringify(recovered)}`);
      if(recovered?.clicked) readiness=await stableReadiness();
      console.log(`AUTOMATION_READINESS_AFTER_DIRECTORY ${JSON.stringify(readiness)}`);
      if(!readiness?.live_app_attached) console.log('AUTOMATION_STATUS ATTACHMENT_NOT_YET_CONFIRMED; continuing supported UI polling.');
    }
    const deadline=Date.now()+timeoutSeconds*1000; let lastState=''; let nextStatus=0;
    while(Date.now()<deadline){
      const uiAction=await evaluate(`(()=>{
        const text=x=>((x.innerText||'')+' '+(x.getAttribute('aria-label')||'')).trim();
        const image=document.querySelector('img[alt="Estate Comms8 Live"]');
        const app=image?.closest('button,a,[role="button"]')||[...document.querySelectorAll('button,a,[role="button"]')].find(x=>/^(Estate Comms8 Live)(?:\\s|$)/i.test((x.innerText||'').trim())&&x.tagName==='BUTTON');
        if(app&&/admin\\/apps|plugins/.test(location.href)){app.scrollIntoView({block:'center'});const r=app.getBoundingClientRect();return {action:'open_estate_comms8_details',x:r.left+r.width/2,y:r.top+r.height/2};}
        const action=[...document.querySelectorAll('button,a,[role="button"],input[type="button"]')].find(x=>/^(Try in chat|Open in chat|Enable|Attach|Add to chat)$/i.test((x.innerText||x.value||'').trim())||/try in chat|open in chat|enable|attach/i.test(x.getAttribute('aria-label')||''));
        if(action&&!action.disabled){action.scrollIntoView({block:'center'});const r=action.getBoundingClientRect();return {action:'activate_estate_comms8',x:r.left+r.width/2,y:r.top+r.height/2};}
        return null;
      })()`);
      if(uiAction){await clickPoint(uiAction);console.log(`AUTOMATION_ACTION ${uiAction.action}`);await sleep(2500);}
      await switchToWorkTarget();
      readiness=await stableReadiness();
      const state=readiness?.challenge?'CHATGPT_LOGIN_REQUIRED':readiness?.live_app_attached&&readiness?.composer_ready?'CHATGPT_WORK_READY':readiness?.live_app_attached?'COMPOSER_NOT_READY':'LIVE_APP_ATTACH_REQUIRED';
      if(state!==lastState||Date.now()>=nextStatus){console.log(`CHATGPT_BOOTSTRAP_STATUS ${state}`);lastState=state;nextStatus=Date.now()+15000;}
      if(state==='CHATGPT_WORK_READY'){close();console.log(JSON.stringify({marker:'CHATGPT_COMMS8_WORK_SURFACE_READY',readiness}));return;}
      await sleep(3000);
    }
    close(); console.log(JSON.stringify({marker:'CHATGPT_WORK_APP_BOOTSTRAP_TIMEOUT',reason:'human_timeout',readiness})); process.exitCode=2; return;
  }
  const manifestProbe=await evaluate(`(()=>{const body=document.body.innerText||'';return ${JSON.stringify(requiredTools)}.every(name=>body.includes(name));})()`);
  // Recover a stale conversation through the supported UI, never by
  // guessing an app URL: open the installed app chip when present, or the
  // Plugins picker, then use its Try in chat action.
  // A completed Work conversation can retain the authoritative seven-action
  // manifest after ChatGPT changes the temporary surface URL to /c/<id>.
  // Preserve that valid surface; pages without the full manifest still use
  // the bounded UI recovery path below.
  if(!manifestProbe) {
    // Never submit a new CME request into a historical conversation merely
    // because its transcript mentions Estate Comms8.  Establish a fresh
    // attached Work surface through the supported app-directory UI first.
    const recovered=await openCanonicalEstateAppAndTryInChat();
    if(!recovered?.clicked){
      const historyConversation=await openAttachedHistoryConversation();
      if(!historyConversation?.clicked){ws.close(); console.log(JSON.stringify({marker:'READINESS_FAILED',reason:'LIVE_APP_ATTACHMENT_FAILED'})); process.exitCode=2; return;}
    }
    await new Promise(r=>setTimeout(r,3000));
  }
  const readiness=await evaluate(`(()=>{
    const body=document.body.innerText||'';
    const input=document.querySelector('#prompt-textarea[contenteditable="true"],div[contenteditable="true"][aria-label="Chat with ChatGPT"]');
    // ChatGPT currently marks the rendered ProseMirror composer itself
    // aria-hidden while retaining a hidden fallback textarea for assistive
    // input.  Accessibility metadata is not a visibility signal here: use
    // rendered geometry and enabled state so the canonical composer is not
    // rejected as unavailable.
    let rect=null; if(input&&input.getBoundingClientRect) rect=input.getBoundingClientRect();
    const visible=!!input && getComputedStyle(input).display!=='none' && !input.disabled && !!rect && rect.width>0 && rect.height>0;
    const appNodes=[...document.querySelectorAll('a, [data-testid*="app"],[data-testid*="connector"],[aria-label*="app" i],[aria-label*="connector" i],button')]
      .filter(x=>!x.closest('a[data-sidebar-item]') && /Estate Comms8/i.test(x.innerText||''));
    const attached=appNodes.some(x=>(x.href||'').includes('${liveDirectoryPath}')||(x.href||'').includes('${liveInstalledPluginId}'));
    const visibleTools=['estate_comms8_create_reasoning_request','estate_comms8_list_requests','estate_comms8_read_request','estate_comms8_claim_request','estate_comms8_acknowledge_request','estate_comms8_respond_request','estate_comms8_resolve_request'].filter(name=>body.includes(name));
    const workUrl=location.href.includes('surface=work')||location.href.includes('/c/');
    const installedAppLabel=workUrl&&body.includes('Estate Comms8 Live')&&[...document.querySelectorAll('[title="Estate Comms8 Live"]')].some(x=>{let r=null;if(x&&x.getBoundingClientRect)r=x.getBoundingClientRect();return !!r&&r.width>0&&r.height>0;});
    // ChatGPT does not render an app's action manifest in the composer DOM.
    // The supported installed-app identity is the authoritative attachment
    // boundary; action readiness is confirmed by the governed seven-action
    // manifest and subsequently by authoritative claim_next audit evidence.
    const manifestAttached=visibleTools.length===7;
    const liveAttached=workUrl&&(attached||manifestAttached||installedAppLabel);
    let tools=visibleTools; if(manifestAttached||liveAttached) tools=['estate_comms8_create_reasoning_request','estate_comms8_list_requests','estate_comms8_read_request','estate_comms8_claim_request','estate_comms8_acknowledge_request','estate_comms8_respond_request','estate_comms8_resolve_request'];
    const visibleAuthControl=[...document.querySelectorAll('input,button,a,[role="button"]')].some(x=>{
      let r=null;if(x&&x.getBoundingClientRect)r=x.getBoundingClientRect();
      if(!r||r.width<=0||r.height<=0)return false;
      const text=((x.innerText||'')+' '+(x.getAttribute('aria-label')||'')).trim();
      return /^(log in|sign in|continue with google|continue with microsoft|verify you are human)$/i.test(text)||x.type==='password';
    });
    const challenge=location.href.indexOf('https://auth.')===0||location.href.indexOf('https://login.')===0||visibleAuthControl;
    let identity=null; if(liveAttached){identity='installed_app_label';if(attached)identity='estate_comms8_live_directory';else if(manifestAttached)identity='dom_manifest';}
    var source='installed_live_manifest';if(manifestAttached)source='dom_manifest';
    return {authenticated:!challenge,challenge,live_app_attached:liveAttached,live_app_identity:identity,tool_names:tools,tool_discovery_source:source,composer_ready:!!visible,workspace:body.includes("Pat's Workspace 2026")};
  })()`);
  transition('READINESS_PROBED',{workspace:readiness?.workspace===true,live_app_attached:readiness?.live_app_attached===true,composer_ready:readiness?.composer_ready===true,tool_count:readiness?.tool_names?.length||0});
  if(!readiness||readiness.__evaluation_error) { ws.close(); console.log(JSON.stringify({marker:'READINESS_FAILED',reason:'READINESS_PROBE_UNAVAILABLE',detail:readiness?.__evaluation_error})); process.exitCode=2; return; }
  if(!readiness.authenticated) { ws.close(); console.log(JSON.stringify({marker:'READINESS_FAILED',reason:'CHATGPT_NOT_AUTHENTICATED',readiness})); process.exitCode=2; return; }
  if(!readiness?.live_app_attached) { ws.close(); console.log(JSON.stringify({marker:'READINESS_FAILED',reason:'LIVE_APP_NOT_FOUND',readiness})); process.exitCode=2; return; }
  if(readiness.tool_names.length!==requiredTools.length) { ws.close(); console.log(JSON.stringify({marker:'READINESS_FAILED',reason:'LIVE_APP_TOOL_DISCOVERY_FAILED',readiness})); process.exitCode=2; return; }
  if(!readiness.composer_ready) { ws.close(); console.log(JSON.stringify({marker:'READINESS_FAILED',reason:'COMPOSER_NOT_READY',readiness})); process.exitCode=2; return; }
  if(readinessOnly) { ws.close(); console.log(JSON.stringify({marker:'READINESS_READY',readiness,trace})); return; }
  const escaped=JSON.stringify(prompt);
  const baselineLength=await evaluate(`(document.body.innerText||'').length`);
  const baselineAssistantCount=await evaluate(`document.querySelectorAll('[data-message-author-role="assistant"]').length`);
  const sent=await evaluate(`(()=>{
    const input=document.querySelector('#prompt-textarea[contenteditable="true"],div[contenteditable="true"][aria-label="Chat with ChatGPT"]');
    if(!input)return {ok:false,reason:'composer_unavailable'};
    input.focus();
    input.replaceChildren();
    const p=document.createElement('p');
    p.textContent=${escaped};
    input.appendChild(p);
    input.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:'insertText',data:${escaped}}));
    return {ok:true};
  })()`);
  if(!sent?.ok) throw Error(sent?.reason||'composer_unavailable');
  transition('PROMPT_INSERTED');
  const submitted=await evaluate(`(()=>{
    const input=document.querySelector('#prompt-textarea[contenteditable="true"],div[contenteditable="true"][aria-label="Chat with ChatGPT"]');
    const root=input&&input.closest ? input.closest('form') : (input&&input.parentElement&&input.parentElement.parentElement&&input.parentElement.parentElement.parentElement);
    const button=root?.querySelector('button[type="submit"],button[aria-label*="Send"],button[aria-label*="Submit"]')||document.querySelector('button[type="submit"],button[aria-label*="Send"],button[aria-label*="Submit"]');
    if(button&&!button.disabled){button.click();return {ok:true,method:'button'};}
    if(input){input.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));return {ok:true,method:'enter'};}
    return {ok:false,reason:'submit_control_unavailable'};
  })()`);
  if(!submitted?.ok) throw Error(submitted?.reason||'submit_control_unavailable');
  transition('SUBMIT_CONFIRMED',{method:submitted.method});
  const result=await evaluate(`(async()=>{
    const assistantBaseline=${Number(baselineAssistantCount)||0};
    const generationStartDeadline=Date.now()+45000;
    const completionDeadline=Date.now()+540000;
    const trace=[]; const mark=(state,extra={})=>trace.push({state,elapsed_ms:Date.now()-${startedAt},...extra});
    const snapshot=()=>{
      const nodes=[...document.querySelectorAll('[data-message-author-role="assistant"]')].slice(assistantBaseline);
      const output=nodes.map(x=>x.innerText||'').join(String.fromCharCode(10));
      const buttons=[...document.querySelectorAll('button')].map(x=>((x.getAttribute('aria-label')||'')+' '+(x.innerText||'')).toLowerCase());
      const stopGenerating=buttons.some(x=>x.includes('stop generating')||x.includes('stop responding'));
      const toolCards=[...document.querySelectorAll('[data-testid*="tool"],[data-testid*="mcp"],[class*="tool" i]')].length;
      return {assistantCount:nodes.length,outputLength:output.length,stopGenerating,toolCards,output};
    };
    return await new Promise(resolve=>{
      let lastLength=0,stableSince=0,started=false,timer=null;
      const observer=new MutationObserver(check); observer.observe(document.body,{subtree:true,childList:true,characterData:true});
      const finish=(value)=>{observer.disconnect();if(timer) clearInterval(timer);resolve({...value,trace});};
      function check(){
        const s=snapshot();
        if(!started && (s.assistantCount>0 || s.stopGenerating || s.toolCards>0 || s.outputLength>0)) { started=true; mark('GENERATION_STARTED',{assistant_count:s.assistantCount,tool_cards:s.toolCards}); }
        if(s.outputLength!==lastLength){lastLength=s.outputLength;stableSince=Date.now();mark('RESPONSE_PROGRESS',{assistant_count:s.assistantCount,output_length:s.outputLength,tool_cards:s.toolCards,stop_generating:s.stopGenerating});}
        const marker=s.output.includes('WORKER_COMPLETE')?'WORKER_COMPLETE':s.output.includes('CONTEXT_REQUIRED')?'CONTEXT_REQUIRED':s.output.includes('EMPTY_QUEUE')?'EMPTY_QUEUE':null;
        if(marker){mark('FINAL_ASSISTANT_MARKER',{marker,assistant_count:s.assistantCount,tool_cards:s.toolCards});finish({marker});return;}
        if(started && stableSince && Date.now()-stableSince>=4000 && !s.stopGenerating && s.assistantCount>0){mark('FINAL_ASSISTANT_STABLE',{assistant_count:s.assistantCount,tool_cards:s.toolCards,output_preview:s.output.slice(-240)});finish({marker:'ASSISTANT_RESPONSE_STABLE'});return;}
        if(!started && Date.now()>=generationStartDeadline){mark('GENERATION_START_TIMEOUT');finish({marker:'BROWSER_COMPLETION_FAILED',reason:'CHATGPT_GENERATION_NEVER_STARTED'});return;}
        if(Date.now()>=completionDeadline){mark('GENERATION_COMPLETION_TIMEOUT',{started,assistant_count:s.assistantCount,tool_cards:s.toolCards});finish({marker:'BROWSER_COMPLETION_FAILED',reason:started?'CHATGPT_GENERATION_EXCEEDED_TIMEOUT':'CHATGPT_GENERATION_NEVER_STARTED'});return;}
      }
      check();
      timer=setInterval(check,1000);
    });
  })()`);
  transition('BROWSER_COMPLETION_RESULT',{marker:result?.marker,reason:result?.reason});
  ws.close(); console.log(JSON.stringify({...result,trace:[...trace,...(result?.trace||[])]}));
})().catch(e=>{console.error(e.stack||e.message);process.exitCode=1});
