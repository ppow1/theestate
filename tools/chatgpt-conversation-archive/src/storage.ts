import fs from 'node:fs'; import path from 'node:path'; import crypto from 'node:crypto'; import type { Conversation, IndexEntry, SyncReport } from './model.js';
export const cleanId = (id: string) => id.replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 180) || 'unknown';
function canonical(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonical);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value as Record<string, unknown>)
      .filter(([key]) => key !== 'exportMetadata' && key !== 'revision')
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, item]) => [key, canonical(item)]));
  }
  return value;
}
export const normalize = (c: Conversation) => JSON.stringify(canonical(c));
export const hashConversation = (c: Conversation) => crypto.createHash('sha256').update(normalize(c)).digest('hex');
export function atomicWrite(file: string, data: string) { fs.mkdirSync(path.dirname(file), { recursive: true }); const tmp = `${file}.${process.pid}.${Date.now()}.tmp`; fs.writeFileSync(tmp, data, 'utf8'); if (fs.existsSync(file)) fs.rmSync(file); fs.renameSync(tmp, file); }
export function readJson<T>(file: string, fallback: T): T { try { return JSON.parse(fs.readFileSync(file, 'utf8')) as T; } catch { return fallback; } }
export function indexFile(root: string) { return path.join(root, 'state', 'conversation-index.json'); }
export function loadIndex(root: string): Record<string, IndexEntry> { return readJson(indexFile(root), {}); }
export function saveIndex(root: string, index: Record<string, IndexEntry>) { atomicWrite(indexFile(root), JSON.stringify(index, null, 2)); }
export function renderMarkdown(c: Conversation) { return `# ${c.title || '(untitled)'}\n\n- Conversation ID: ${c.id}\n- Source: ${c.sourceUrl}\n\n${c.messages.map((m,i)=>`## ${i+1}. ${m.role}${m.timestamp ? ` — ${m.timestamp}` : ''}\n\n${m.content.map(b=>b.type==='code' ? `\n\`\`\`${b.language||''}\n${b.text||''}\n\`\`\`` : b.text || '').join('\n')}`).join('\n\n')}`; }
export function renderHtml(c: Conversation) { const esc=(x:string)=>x.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); return `<!doctype html><meta charset="utf-8"><title>${esc(c.title)}</title><article><h1>${esc(c.title)}</h1>${c.messages.map(m=>`<section><h2>${esc(m.role)}</h2>${m.content.map(b=>b.type==='code'?`<pre><code>${esc(b.text||'')}</code></pre>`:`<p>${esc(b.text||'')}</p>`).join('')}</section>`).join('')}</article>`; }
export function writeReport(root: string, report: SyncReport) { const dir=path.join(root,'reports',report.runId); atomicWrite(path.join(dir,'summary.json'),JSON.stringify(report,null,2)); atomicWrite(path.join(dir,'summary.md'),`# ChatGPT archive run ${report.runId}\n\n- Started: ${report.startedAt}\n- Ended: ${report.endedAt||'in progress'}\n- Duration: ${report.durationMs||0} ms\n\n${Object.entries(report.counts).map(([k,v])=>`- ${k}: ${v}`).join('\n')}`); for(const k of ['new','updated','unchanged','unavailable','failed']) atomicWrite(path.join(dir,`${k}.json`),JSON.stringify(report.ids[k]||[],null,2)); return dir; }
