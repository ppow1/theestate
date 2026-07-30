import { execFileSync, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const toolRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const scriptRoot = path.join(toolRoot, 'scripts');
const unrelatedCwd = fs.existsSync('A:\\theestate-wp4233') ? 'A:\\theestate-wp4233' : path.parse(toolRoot).root;
const powershell = process.platform === 'win32' ? 'powershell.exe' : 'pwsh';

describe('operator launchers', () => {
  it('validate successfully from an unrelated current directory', () => {
    const output = execFileSync(
      powershell,
      ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(scriptRoot, 'Validate-ChatGPTConversationArchive.ps1')],
      { cwd: unrelatedCwd, encoding: 'utf8' },
    );
    expect(output).toContain('"valid": true');
  });

  it('keeps non-interactive sync prompt-free and returns authentication promptly', () => {
    const result = spawnSync(process.execPath, [path.join(toolRoot, 'dist', 'cli.js'), 'sync', '--config', path.join(toolRoot, 'config.example.json'), '--quiet'], {
      cwd: unrelatedCwd,
      encoding: 'utf8',
      timeout: 15000,
    });
    expect(result.status).not.toBe(0);
    expect(`${result.stdout}\n${result.stderr}`).toContain('AUTHENTICATION_REQUIRED');
    expect(result.error).toBeUndefined();
  });

  it.each([
    'Initialize-ChatGPTConversationArchive.ps1',
    'Run-ChatGPTConversationArchiveFull.ps1',
    'Run-ChatGPTConversationArchiveSync.ps1',
    'Validate-ChatGPTConversationArchive.ps1',
  ])('resolves paths relative to the script in %s', (scriptName) => {
    const script = fs.readFileSync(path.join(scriptRoot, scriptName), 'utf8');
    expect(script).toContain('$PSScriptRoot');
    expect(script).toContain('Set-Location -LiteralPath $ToolRoot');
    expect(script).toContain('$ConfigPath');
  });
});
