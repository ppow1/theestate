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

  it('launches manual login as ordinary Chrome without Playwright control arguments', () => {
    const script = fs.readFileSync(path.join(scriptRoot, 'Initialize-ChatGPTConversationArchive.ps1'), 'utf8');
    expect(script).toContain("$ChromePath = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'");
    expect(script).toContain('Start-Process -FilePath $ChromePath');
    expect(script).toContain('--user-data-dir=');
    expect(script).toContain('--window-size=1400,900');
    expect(script).toContain('--window-position=50,50');
    expect(script).toContain('--disable-extensions');
    expect(script).toContain('https://chatgpt.com/');
    expect(script).not.toContain('--remote-debugging-pipe');
    expect(script).not.toContain('--remote-debugging-port');
    expect(script).not.toContain('ChatGPTBrowser.open');
    expect(script).toContain('prepare-profile');
    expect(script).toContain('verify-auth');
    expect(script).toContain('Wait-Process -Id $Chrome.Id');
    expect(script).toContain('Close the dedicated Chrome window now');
  });
});
