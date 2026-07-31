#!/usr/bin/env node
import { Command } from 'commander';
import fs from 'node:fs';
import path from 'node:path';
import { loadConfig } from './config.js';
import { runSync } from './sync.js';
import { validateArchive } from './validate.js';
import { ChatGPTBrowser } from './browser.js';
import { repairInteractiveProfilePreferences } from './profile.js';
import { atomicWrite, cleanId } from './storage.js';
import { recoverStaleRun } from './lifecycle.js';
import { writeConversationArtifacts } from './artifacts.js';

const program = new Command();
program.name('chatgpt-archive').description('Estate-wide local ChatGPT Conversation Archive').option('--config <file>', 'configuration file').option('--archive-root <path>', 'archive root override').option('--conversation-limit <n>', 'bound this run to the first N conversations').option('--quiet', 'reduce console output');
const valueAfter = (flag: string) => { const i = process.argv.indexOf(flag); return i >= 0 ? process.argv[i + 1] : undefined; };
const cfg = (cmd: any) => { const options = cmd && typeof cmd.opts === 'function' ? cmd.opts() : (cmd || {}); const archiveRoot = options.archiveRoot || program.opts().archiveRoot || valueAfter('--archive-root'); const limit = options.conversationLimit || program.opts().conversationLimit || valueAfter('--conversation-limit'); return loadConfig(options.config || program.opts().config || valueAfter('--config'), { ...(archiveRoot ? { archiveRoot } : {}), ...(limit ? { conversationLimit: Number(limit) } : {}) }); };

program.command('prepare-profile').description('Repair only the dedicated profile display state before ordinary Chrome login').action(async () => { const c = loadConfig(valueAfter('--config') || program.opts().config); repairInteractiveProfilePreferences(c.profilePath); console.log(`Profile prepared: ${c.profilePath}`); });
program.command('verify-auth').description('Verify the dedicated profile with the archive runtime after ordinary Chrome closes').action(async () => { const c = loadConfig(valueAfter('--config') || program.opts().config); const b = await ChatGPTBrowser.open(c, false); try { await b.ensureAuthenticated(); console.log(`Authenticated profile verified: ${c.profilePath}`); } finally { await b.close(); } });
for (const name of ['full', 'sync', 'resume']) program.command(name).description(`${name} archive operation`).action(async (cmd) => { const report = await runSync(cfg(cmd), name as 'full' | 'sync' | 'resume'); console.log(JSON.stringify(report, null, 2)); if (report.status === 'throttled') process.exitCode = 3; else if (report.status === 'cancelled') process.exitCode = 4; else if (report.status === 'browser-context-lost') process.exitCode = 5; else if (report.counts.failed) process.exitCode = 2; });
program.command('inventory').action(async (cmd) => { const c = cfg(cmd); const b = await ChatGPTBrowser.open(c, false); try { console.log(JSON.stringify(await b.inventoryDetailed(), null, 2)); } finally { await b.close(); } });
program.command('recover-run').description('Recover a stale running checkpoint without starting an archive').option('--run-id <id>', 'restore a previously recorded recovered run').option('--last-completed-count <n>', 'preserved completed count when repairing a historical record').option('--last-completed-id <id>', 'preserved last completed conversation ID').action(async (cmd) => { const c = cfg(cmd); const options=cmd&&typeof cmd.opts==='function'?cmd.opts():(cmd||{}); const runId=options.runId||valueAfter('--run-id'); if(runId){const record=JSON.parse(fs.readFileSync(path.join(c.archiveRoot,'state','recovered-runs',`${runId}.json`),'utf8')); const count=Number(options.lastCompletedCount||valueAfter('--last-completed-count')); const completedId=options.lastCompletedId||valueAfter('--last-completed-id'); if(Number.isFinite(count)&&count>0)record.lastCompletedCount=count; if(completedId)record.lastCompletedConversationId=completedId; atomicWrite(path.join(c.archiveRoot,'state','recovered-runs',`${runId}.json`),JSON.stringify(record,null,2)); atomicWrite(path.join(c.archiveRoot,'status','current-run.json'),JSON.stringify({runId,status:'interrupted',recoveredAt:record.detectedAt,recovery:record},null,2)); atomicWrite(path.join(c.archiveRoot,'state','run-state.json'),JSON.stringify({runId,status:'interrupted',recoveredAt:record.detectedAt,recovery:record,requeueConversationId:record.interruptedConversationId},null,2)); console.log(JSON.stringify(record,null,2)); } else console.log(JSON.stringify(recoverStaleRun(c.archiveRoot,c)||{status:'not-stale'},null,2)); });
program.command('generate-artifacts').description('Generate JSON/MHTML/PDF/validation artifacts from one complete canonical conversation').option('--conversation-id <id>', 'conversation ID').option('--conversation-json <path>', 'canonical JSON path').action(async (cmd) => { const c=cfg(cmd); const options=cmd&&typeof cmd.opts==='function'?cmd.opts():(cmd||{}); const id=options.conversationId||valueAfter('--conversation-id'); const file=options.conversationJson||valueAfter('--conversation-json')||(id?path.join(c.archiveRoot,'validation','live-conversation',`${cleanId(id)}.json`):undefined); if(!file)throw new Error('ARTIFACT_CONVERSATION_REQUIRED'); const conversation=JSON.parse(fs.readFileSync(file,'utf8')); const result=await writeConversationArtifacts(c.archiveRoot,conversation,c,'bounded-validation'); console.log(JSON.stringify({conversationId:conversation.id,artifactDirectory:path.join(c.archiveRoot,'conversations',cleanId(conversation.id)),validation:result},null,2)); });
program.command('validate').action(async (cmd) => { const c = cfg(cmd); const r = validateArchive(c.archiveRoot); console.log(JSON.stringify(r, null, 2)); if (!r.valid) process.exitCode = 2; });
program.command('diagnostics').action(async (cmd) => { const c = cfg(cmd); fs.mkdirSync(c.diagnosticsPath, { recursive: true }); const b = await ChatGPTBrowser.open(c, true); try { await b.ensureAuthenticated(); console.log(`Diagnostics succeeded: ${c.diagnosticsPath}`); } finally { await b.close(true); } });

program.command('validate-conversation').description('Validate one explicit conversation without changing the synchronization index').option('--conversation-id <id>', 'conversation ID').option('--conversation-url <url>', 'conversation URL').action(async (cmd) => {
  const c = cfg(cmd); const options = cmd && typeof cmd.opts === 'function' ? cmd.opts() : (cmd || {}); const id = options.conversationId || valueAfter('--conversation-id'); const url = options.conversationUrl || valueAfter('--conversation-url') || (id ? `https://chatgpt.com/c/${id}` : undefined);
  if (!id && !url) throw new Error('VALIDATION_CONVERSATION_REQUIRED: provide --conversation-id or --conversation-url');
  const resolvedId = id || url!.match(/\/c\/([a-zA-Z0-9-]+)/)?.[1]; if (!resolvedId) throw new Error('VALIDATION_CONVERSATION_URL_INVALID');
  const b = await ChatGPTBrowser.open(c, false); try {
    await b.ensureAuthenticated();
    const result = await b.conversation({ id: resolvedId, title: `Live validation ${resolvedId}`, sourceUrl: url! }, (s, pass, stable) => console.log(`[archive progress] phase=hydrating-conversation pass=${pass} messages=${s.count} stable=${stable}/${Math.max(c.conversationHydrationStablePasses, c.messageCountStabilityRequirement)} scrollTop=${Math.round(s.scrollTop)} scrollHeight=${s.scrollHeight} topReached=${s.topReached} virtualizationDetected=${s.virtualizationDetected}`));
    const validationDir = path.join(c.archiveRoot, 'validation', 'live-conversation'); const file = path.join(validationDir, `${cleanId(resolvedId)}.json`);
    if (result.exportMetadata?.complete) atomicWrite(file, JSON.stringify(result, null, 2));
    const first = result.messages[0]; const last = result.messages[result.messages.length - 1];
    console.log(JSON.stringify({ conversationId: result.id, title: result.title, exportMetadata: result.exportMetadata, exportedFilePath: result.exportMetadata?.complete ? file : undefined, firstMessageSummary: first?.content.map(block => block.text || '').join('\n').slice(0, 240), lastMessageSummary: last?.content.map(block => block.text || '').join('\n').slice(0, 240), messageOrder: result.messages.map(message => message.id) }, null, 2));
    if (!result.exportMetadata?.complete) process.exitCode = 2;
  } finally { await b.close(); }
});

program.parseAsync().catch(e => { console.error(e instanceof Error ? e.message : e); process.exitCode = 1; });
