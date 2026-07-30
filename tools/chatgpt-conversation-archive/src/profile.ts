import fs from 'node:fs';
import path from 'node:path';

export function repairInteractiveProfilePreferences(profilePath:string) {
  const preferencesPath=path.join(profilePath,'Default','Preferences');
  if(!fs.existsSync(preferencesPath)) return;
  const preferences=JSON.parse(fs.readFileSync(preferencesPath,'utf8')) as any;
  const partition=preferences.partition??={};
  const perHost=partition.per_host_zoom_levels??={};
  const repair=(value:any)=>{if(!value||typeof value!=='object')return; for(const [key,child] of Object.entries(value)){if(/^(?:https?:\/\/)?(?:www\.)?(?:chatgpt\.com|openai\.com|auth\.openai\.com)$/i.test(key)) (child as any).zoom_level=0; else repair(child);}};
  repair(perHost);
  const target=(perHost.x??= {});
  for(const host of ['chatgpt.com','openai.com','auth.openai.com']) target[host]={...(target[host]??{}),zoom_level:0};
  if(preferences.browser?.window_placement) delete preferences.browser.window_placement;
  const temporary=`${preferencesPath}.tmp-${process.pid}`;
  fs.writeFileSync(temporary,JSON.stringify(preferences)); fs.renameSync(temporary,preferencesPath);
}
