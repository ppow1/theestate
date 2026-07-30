import { chromium, type BrowserContext, type Page } from 'playwright';
import fs from 'node:fs'; import path from 'node:path'; import { execFileSync } from 'node:child_process';
import type { ArchiveConfig, Conversation, ContentBlock, DiscoveredConversation, Message, Role } from './model.js';
const roleOf=(x:string):Role=>['user','assistant','tool','system'].includes(x)?x as Role:'unknown';
export type AuthenticationState = 'authenticated'|'unauthenticated'|'verification-incomplete';
const forbiddenSandboxArguments=['--no-sandbox','--disable-setuid-sandbox'];
export function resolveStableChromeExecutable() {
  const candidates = [
    process.env.CHATGPT_ARCHIVE_CHROME,
    path.join(process.env.ProgramW6432||'', 'Google', 'Chrome', 'Application', 'chrome.exe'),
    path.join(process.env['ProgramFiles(x86)']||'', 'Google', 'Chrome', 'Application', 'chrome.exe'),
    path.join(process.env.LOCALAPPDATA||'', 'Google', 'Chrome', 'Application', 'chrome.exe'),
  ].filter((candidate): candidate is string => Boolean(candidate));
  return candidates.find(candidate=>fs.existsSync(candidate));
}
export function interactiveLaunchOptions(config: ArchiveConfig): NonNullable<Parameters<typeof chromium.launchPersistentContext>[1]> {
  return {
    headless: false,
    executablePath: config.chromeExecutablePath || resolveStableChromeExecutable(),
    viewport: null,
    acceptDownloads: false,
    chromiumSandbox: true,
    ignoreDefaultArgs: forbiddenSandboxArguments,
    args: ['--window-size=1400,900','--window-position=50,50','--disable-extensions'],
  };
}
export function repairInteractiveProfilePreferences(profilePath:string) {
  const preferencesPath=path.join(profilePath,'Default','Preferences');
  if(!fs.existsSync(preferencesPath)) return;
  const preferences=JSON.parse(fs.readFileSync(preferencesPath,'utf8')) as any;
  const levels=preferences.partition??={};
  const perHost=levels.per_host_zoom_levels??={};
  const repair=(value:any)=>{if(!value||typeof value!=='object')return; for(const [key,child] of Object.entries(value)){if(/^(?:https?:\/\/)?(?:www\.)?(?:chatgpt\.com|openai\.com|auth\.openai\.com)$/i.test(key)) (child as any).zoom_level=0; else repair(child);}};
  repair(perHost);
  const target=(perHost.x??= {});
  for(const host of ['chatgpt.com','openai.com','auth.openai.com']) target[host]={...(target[host]??{}),zoom_level:0};
  if(preferences.browser?.window_placement) delete preferences.browser.window_placement;
  const temporary=`${preferencesPath}.tmp-${process.pid}`;
  fs.writeFileSync(temporary,JSON.stringify(preferences)); fs.renameSync(temporary,preferencesPath);
}
export function effectiveChromeCommandLines(profilePath:string):string[] {
  if(process.platform!=='win32') return [];
  const query="$p=Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { $_.CommandLine -like ('*' + $env:CHATGPT_ARCHIVE_PROFILE_QUERY + '*') } | Select-Object -ExpandProperty CommandLine; if($p){$p | ConvertTo-Json -Compress}";
  const output=execFileSync('powershell.exe',['-NoProfile','-Command',query],{encoding:'utf8',env:{...process.env,CHATGPT_ARCHIVE_PROFILE_QUERY:profilePath.replace(/\\/g,'/')}}).trim();
  if(!output) return [];
  const parsed=JSON.parse(output) as string|string[];
  return Array.isArray(parsed)?parsed:[parsed];
}
export function setInteractiveWindowBounds(profilePath:string) {
  if(process.platform!=='win32') return;
  const source="Add-Type @'\nusing System; using System.Runtime.InteropServices; public static class Win32 { [DllImport(\"user32.dll\")] public static extern bool ShowWindow(IntPtr h, int n); [DllImport(\"user32.dll\")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags); }\n'@; $p=Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { $_.CommandLine -like ('*' + $env:CHATGPT_ARCHIVE_PROFILE_QUERY + '*') -and $_.CommandLine -notlike '*--type=*' } | Select-Object -First 1; if(-not $p){throw 'interactive Chrome window was not found'}; $h=(Get-Process -Id $p.ProcessId).MainWindowHandle; if($h -eq 0){throw 'interactive Chrome window handle was not available'}; [Win32]::ShowWindow($h,9)|Out-Null; [Win32]::SetWindowPos($h,[IntPtr]::Zero,50,50,1400,900,20)|Out-Null";
  execFileSync('powershell.exe',['-NoProfile','-Command',source],{encoding:'utf8',env:{...process.env,CHATGPT_ARCHIVE_PROFILE_QUERY:profilePath.replace(/\\/g,'/')}});
}
export function interactiveWindowBounds(profilePath:string) {
  if(process.platform!=='win32') return undefined;
  const source="Add-Type @'\nusing System; using System.Runtime.InteropServices; public struct RECT { public int Left; public int Top; public int Right; public int Bottom; } public static class Win32 { [DllImport(\"user32.dll\")] public static extern bool GetWindowRect(IntPtr h, out RECT r); }\n'@; $p=Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { $_.CommandLine -like ('*' + $env:CHATGPT_ARCHIVE_PROFILE_QUERY + '*') -and $_.CommandLine -notlike '*--type=*' } | Select-Object -First 1; if(-not $p){throw 'interactive Chrome window was not found'}; $h=(Get-Process -Id $p.ProcessId).MainWindowHandle; $r=New-Object RECT; [Win32]::GetWindowRect($h,[ref]$r)|Out-Null; [pscustomobject]@{left=$r.Left;top=$r.Top;width=$r.Right-$r.Left;height=$r.Bottom-$r.Top}|ConvertTo-Json -Compress";
  return JSON.parse(execFileSync('powershell.exe',['-NoProfile','-Command',source],{encoding:'utf8',env:{...process.env,CHATGPT_ARCHIVE_PROFILE_QUERY:profilePath.replace(/\\/g,'/')}}).trim());
}
export function assertInteractiveWindowBounds(profilePath:string) { const bounds=interactiveWindowBounds(profilePath); if(bounds && (bounds.width<1200||bounds.width>1600||bounds.height<750||bounds.height>1050)) throw new Error(`INTERACTIVE_BROWSER_WINDOW_SIZE_INVALID: ${bounds.width}x${bounds.height}`); return bounds; }
export function assertNoForbiddenSandboxArguments(profilePath:string) {
  const lines=effectiveChromeCommandLines(profilePath);
  const violations=lines.flatMap(line=>forbiddenSandboxArguments.filter(argument=>line.includes(argument)));
  if(violations.length) throw new Error(`INTERACTIVE_BROWSER_UNSAFE_ARGUMENTS: ${[...new Set(violations)].join(', ')}`);
  return lines;
}
export class ChatGPTBrowser {
  private constructor(private context: BrowserContext, private page: Page, private config: ArchiveConfig) {}
  static async open(config: ArchiveConfig, diagnostics=false, interactive=false) { fs.mkdirSync(config.profilePath,{recursive:true}); if(interactive) { if(effectiveChromeCommandLines(config.profilePath).length) throw new Error('PROFILE_IN_USE: close any existing dedicated Chrome window before initialization'); repairInteractiveProfilePreferences(config.profilePath); } const options=interactive?interactiveLaunchOptions(config):{headless:config.headless,executablePath:config.chromeExecutablePath||undefined,viewport:{width:1440,height:1000},acceptDownloads:false}; const context=await chromium.launchPersistentContext(config.profilePath,options); try { if(interactive) { assertNoForbiddenSandboxArguments(config.profilePath); setInteractiveWindowBounds(config.profilePath); assertInteractiveWindowBounds(config.profilePath); } } catch(error) { await context.close(); throw error; } const page=context.pages()[0]||await context.newPage(); page.setDefaultTimeout(config.timeoutMs); if(diagnostics) await context.tracing.start({screenshots:true,snapshots:true,sources:false}); return new ChatGPTBrowser(context,page,config); }
  async close(diagnostics=false) { if(diagnostics) { fs.mkdirSync(this.config.diagnosticsPath,{recursive:true}); await this.context.tracing.stop({path:path.join(this.config.diagnosticsPath,`trace-${Date.now()}.zip`)}); } await this.context.close(); }
  async isAvailable() { return !this.page.isClosed(); }
  async authenticationState():Promise<AuthenticationState> { if (this.page.isClosed()) return 'unauthenticated'; await this.page.goto('https://chatgpt.com/',{waitUntil:'domcontentloaded'}); const body=(await this.page.locator('body').innerText().catch(()=>'')); if (/verifying you are human|checking your browser|challenge-platform|cf-chl/i.test(body)||/\/cdn-cgi\/challenge-platform|\/challenge\//i.test(this.page.url())) return 'verification-incomplete'; if (/log in|sign up/i.test(body)) return 'unauthenticated'; const interfaceElements=await this.page.locator('main,textarea,[contenteditable="true"],a[href*="/c/"]').count(); return interfaceElements>0?'authenticated':'unauthenticated'; }
  async isAuthenticated() { return (await this.authenticationState())==='authenticated'; }
  async ensureAuthenticated() { const state=await this.authenticationState(); if(state==='verification-incomplete') throw new Error('LOGIN_VERIFICATION_INCOMPLETE: complete the legitimate browser verification in the dedicated profile, then retry'); if(state!=='authenticated') throw new Error('AUTHENTICATION_REQUIRED: authenticate the dedicated Chrome profile, then retry'); }
  async inventory():Promise<DiscoveredConversation[]> { await this.ensureAuthenticated(); const found=new Map<string,DiscoveredConversation>(); let stable=0; for(let i=0;i<100 && stable<4;i++){ const links=await this.page.locator('a[href*="/c/"]').evaluateAll(as=>as.map(a=>({href:(a as HTMLAnchorElement).href,title:(a.textContent||'').trim()}))); const before=found.size; for(const l of links){const m=l.href.match(/\/c\/([a-zA-Z0-9-]+)/); if(m) found.set(m[1],{id:m[1],title:l.title||l.title||l.href.split('/').pop()||'(untitled)',sourceUrl:l.href});} stable=found.size===before?stable+1:0; await this.page.mouse.wheel(0,2500); await this.page.waitForTimeout(250); } return [...found.values()].slice(0,this.config.conversationLimit||Infinity); }
  async conversation(item:DiscoveredConversation):Promise<Conversation>{ await this.page.goto(item.sourceUrl,{waitUntil:'domcontentloaded'}); await this.page.waitForTimeout(500); for(let i=0;i<30;i++){await this.page.mouse.wheel(0,2000); await this.page.waitForTimeout(100); } const messages=await this.page.locator('[data-message-author-role]').evaluateAll(nodes=>nodes.map((n:any)=>{const role=roleOf(n.getAttribute('data-message-author-role')||'unknown'); const codeNodes=Array.from(n.querySelectorAll('pre code')) as any[]; const blocks=codeNodes.map((x:any):ContentBlock=>({type:'code',text:x.textContent||'',language:(x.className||'').replace(/^language-/,'')})); const text=(n.innerText||'').trim(); if(!blocks.length&&text) blocks.push({type:'text',text}); return {role,content:blocks} as Message;})); const usable=messages.length?messages:await this.page.locator('main article').evaluateAll(as=>as.map((n:any)=>({role:'unknown' as Role,content:[{type:'text',text:(n.innerText||'').trim()}]})).filter((m:any)=>m.content[0].text)); return {schemaVersion:'1.0',id:item.id,title:item.title||'(untitled)',sourceUrl:item.sourceUrl,messages:usable,exportMetadata:{exportedAt:new Date().toISOString(),exporterVersion:'1.0.0',complete:usable.length > 0,limitations:usable.length?[]:['No semantic message roles exposed by the interface; preserved visible article text as unknown role']},metadata:{extraction:'Playwright layered DOM selectors'}}; }
}
