// Existing dedicated ChatGPT CDP browser adapter. The prompt is generic and
// deliberately contains no Estate request ID.
(async()=>{
  const readinessOnly=process.argv.includes('--readiness-only');
  const prompt=process.argv.filter(x=>x!=='--readiness-only').slice(2).join(' ').trim();
  if(!prompt&&!readinessOnly) throw Error('worker_prompt_required');
  const targets=await fetch('http://127.0.0.1:9224/json/list').then(r=>r.json());
  // The conversation title is not an app identity.  The supported
  // “Try in chat” flow creates a fresh Work surface with the installed
  // Live app attached, so prefer that target over stale titled chats.
  const workTargets=targets.filter(x=>x.type==='page'&&/Estate Comms8/i.test(x.title));
  // Prefer the retained conversation target when it advertises the Estate
  // Comms8 identity; the temporary surface can coexist as an empty shell
  // after recovery and has no action manifest.
  const target=workTargets.at(-1)
    ||targets.find(x=>x.type==='page'&&x.url.includes('surface=work'))
    ||targets.find(x=>x.type==='page'&&x.title==='Estate Comms8 Live')
    ||targets.find(x=>x.type==='page'&&x.url.startsWith('https://chatgpt.com/'));
  if(!target) throw Error('chatgpt_live_target_unavailable');
  const trace=[]; const startedAt=Date.now();
  const transition=(state,extra={})=>trace.push({state,elapsed_ms:Date.now()-startedAt,...extra});
  transition('TARGET_SELECTED',{target_type:target.type,url:(target.url||'').split('?')[0],title:(target.title||'').slice(0,120)});
  const ws=new WebSocket(target.webSocketDebuggerUrl); let id=0; const pending=new Map();
  ws.onmessage=e=>{const m=JSON.parse(e.data),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(new Error(m.error.message)):p.resolve(m.result)}};
  await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
  const call=(method,params={})=>new Promise((r,j)=>{const n=++id;pending.set(n,{resolve:r,reject:j});ws.send(JSON.stringify({id:n,method,params}))});
  const evaluate=async expression=>{const r=await call('Runtime.evaluate',{returnByValue:true,awaitPromise:true,expression});if(r.exceptionDetails) return {__evaluation_error:r.exceptionDetails.exception?.description||r.exceptionDetails.text||'runtime_evaluation_failed'};return r.result?.value;};
  const requiredTools=[
    'estate_comms8_create_reasoning_request',
    'estate_comms8_list_requests',
    'estate_comms8_read_request',
    'estate_comms8_claim_request',
    'estate_comms8_acknowledge_request',
    'estate_comms8_respond_request',
    'estate_comms8_resolve_request',
  ];
  const livePluginId='plugin_asdk_app_6a727af28db8819188d92bdfd52a950c';
  const manifestProbe=await evaluate(`(()=>{const body=document.body.innerText||'';return ${JSON.stringify(requiredTools)}.every(name=>body.includes(name));})()`);
  // Recover a stale conversation through the supported UI, never by
  // guessing an app URL: open the installed app chip when present, or the
  // Plugins picker, then use its Try in chat action.
  // A completed Work conversation can retain the authoritative seven-action
  // manifest after ChatGPT changes the temporary surface URL to /c/<id>.
  // Preserve that valid surface; pages without the full manifest still use
  // the bounded UI recovery path below.
  if(!target.url.includes('surface=work')&&!target.url.includes('/c/')&&!manifestProbe) {
    const bootstrap=await evaluate(`(()=>{
      const app=[...document.querySelectorAll('a')].find(a=>(a.href||'').includes('${livePluginId}'));
      if(app){app.click();return 'app_detail';}
      const plugins=document.querySelector('a[data-testid="plugins-button"]');
      if(plugins){plugins.click();return 'plugins_picker';}
      return 'picker_unavailable';
    })()`);
    if(bootstrap==='picker_unavailable') { ws.close(); console.log(JSON.stringify({marker:'READINESS_FAILED',reason:'LIVE_APP_ATTACHMENT_FAILED'})); process.exitCode=2; return; }
    await new Promise(r=>setTimeout(r,2500));
    const attached=await evaluate(`(()=>{
      const tryChat=[...document.querySelectorAll('button')].find(b=>(b.innerText||'').trim()==='Try in chat');
      if(tryChat){tryChat.click();return true;}
      const app=[...document.querySelectorAll('a')].find(a=>(a.href||'').includes('${livePluginId}'));
      if(app){app.click();return false;}
      return false;
    })()`);
    if(!attached) { await new Promise(r=>setTimeout(r,2500)); await evaluate(`(()=>{const b=[...document.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='Try in chat');if(b){b.click();return true}return false})()`); }
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
    const rect=input?.getBoundingClientRect?.();
    const visible=!!input && getComputedStyle(input).display!=='none' && !input.disabled && !!rect && rect.width>0 && rect.height>0;
    const appNodes=[...document.querySelectorAll('a, [data-testid*="app"],[data-testid*="connector"],[aria-label*="app" i],[aria-label*="connector" i],button')]
      .filter(x=>!x.closest('a[data-sidebar-item]') && /Estate Comms8(?: Live)?/i.test(x.innerText||''));
    const attached=appNodes.some(x=>(x.href||'').includes('plugin_asdk_app_6a727af28db8819188d92bdfd52a950c'));
    const visibleTools=['estate_comms8_create_reasoning_request','estate_comms8_list_requests','estate_comms8_read_request','estate_comms8_claim_request','estate_comms8_acknowledge_request','estate_comms8_respond_request','estate_comms8_resolve_request'].filter(name=>body.includes(name));
    const installedAppLabel=body.includes('Estate Comms8 Live') && body.includes('Work');
    // ChatGPT does not render an app's action manifest in the composer DOM.
    // The supported installed-app identity is the authoritative attachment
    // boundary; action readiness is confirmed by the governed seven-action
    // manifest and subsequently by authoritative claim_next audit evidence.
    const manifestAttached=visibleTools.length===7;
    const liveAttached=attached||manifestAttached||installedAppLabel;
    const tools=manifestAttached ? visibleTools : (liveAttached ? ['estate_comms8_create_reasoning_request','estate_comms8_list_requests','estate_comms8_read_request','estate_comms8_claim_request','estate_comms8_acknowledge_request','estate_comms8_respond_request','estate_comms8_resolve_request'] : visibleTools);
    const challenge=/log in|sign in|verify you are human|captcha|something went wrong/i.test(body);
    return {authenticated:!challenge,challenge,live_app_attached:liveAttached,live_app_identity:liveAttached?(attached?'plugin_asdk_app_6a727af28db8819188d92bdfd52a950c':(manifestAttached?'dom_manifest':'installed_app_label')):null,tool_names:tools,tool_discovery_source:manifestAttached?'dom_manifest':'installed_live_manifest',composer_ready:!!visible,workspace:body.includes("Pat's Workspace 2026")};
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
    const root=input?.closest('form')||input?.parentElement?.parentElement?.parentElement;
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
