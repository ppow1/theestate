import { execFileSync, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const toolRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const scriptRoot = path.join(toolRoot, 'scripts');
const unrelatedCwd = fs.existsSync('A:\\theestate-wp4233') ? 'A:\\theestate-wp4233' : path.parse(toolRoot).root;
const powershell = process.platform === 'win32' ? 'powershell.exe' : 'pwsh';

describe('operator launchers', () => {
  it('validate successfully from an unrelated current directory', () => {
    const archiveRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'chatgpt-archive-validate-'));
    try {
      const output = execFileSync(
        powershell,
        ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(scriptRoot, 'Validate-ChatGPTConversationArchive.ps1')],
        { cwd: unrelatedCwd, encoding: 'utf8', env: { ...process.env, CHATGPT_ARCHIVE_ROOT: archiveRoot } },
      );
      expect(output).toContain('"valid": true');
    } finally { fs.rmSync(archiveRoot, { recursive: true, force: true }); }
  });

  it('keeps non-interactive sync prompt-free and returns authentication promptly', () => {
    const result = spawnSync(powershell, ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', path.join(scriptRoot, 'Run-ChatGPTConversationArchiveSync.ps1')], {
      cwd: unrelatedCwd,
      encoding: 'utf8',
      timeout: 30000,
    });
    expect(result.status).not.toBe(0);
    expect(`${result.stdout}\n${result.stderr}`).toContain('AUTHENTICATION_REQUIRED');
    expect(result.error).toBeUndefined();
  }, 40000);

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
    expect(script).toContain('Get-ArchiveBrowserWindows');
    expect(script).toContain('Test-ArchiveProfileLocksReleased');
    expect(script).toContain('Close the dedicated Chrome window now');
  });

  it('keeps browser-evaluated callbacks free of Node outer-scope role helpers', () => {
    const source = fs.readFileSync(path.join(toolRoot, 'src', 'browser.ts'), 'utf8');
    expect(source).not.toContain('roleOf(');
    expect(source).toContain("['user','assistant','tool','system'].includes(roleText)");
  });

  it('matches handed-off Chrome processes by normalized profile path and selects the top-level window', () => {
    const helper = path.join(scriptRoot, 'Archive-ChatGPTConversationArchiveLifecycle.ps1').replace(/'/g, "''");
    const command = `. '${helper}'; $profile='A:\\AI\\Tools\\ChatGPTConversationArchive\\profile'; $quoted='chrome.exe --user-data-dir='+[char]34+$profile+[char]34+' --type=renderer'; $forward='chrome.exe --user-data-dir='+$profile.Replace('\\','/')+' --window-size=1400,900'; $other='chrome.exe --user-data-dir=A:/other/profile'; $fake=@([pscustomobject]@{ProcessId=101;CommandLine=$quoted;MainWindowHandle=0},[pscustomobject]@{ProcessId=202;CommandLine=$forward;MainWindowHandle=77},[pscustomobject]@{ProcessId=303;CommandLine=$other;MainWindowHandle=88}); $matched=@(Get-ArchiveProfileProcesses -ProfilePath $profile -Processes $fake); $main=@(Get-ArchiveMainBrowserProcesses -ProfilePath $profile -Processes $fake); $windows=@(Get-ArchiveBrowserWindows -ProfilePath $profile -Processes $fake); [pscustomobject]@{matched=$matched.Count;main=$main.Count;mainPid=$main[0].ProcessId;windowPid=$windows[0].ProcessId}|ConvertTo-Json -Compress`;
    const output = execFileSync(powershell, ['-NoProfile', '-Command', command], { encoding: 'utf8' });
    expect(JSON.parse(output)).toEqual({ matched: 2, main: 1, mainPid: 202, windowPid: 202 });
  });

  it('detects profile-lock release independently of browser process state', () => {
    const helper = path.join(scriptRoot, 'Archive-ChatGPTConversationArchiveLifecycle.ps1').replace(/'/g, "''");
    const command = `. '${helper}'; $profile=Join-Path ([IO.Path]::GetTempPath()) ('archive-lock-test-'+[guid]::NewGuid()); New-Item -ItemType Directory -Path $profile|Out-Null; New-Item -ItemType File -Path (Join-Path $profile 'SingletonLock')|Out-Null; $locked=Test-ArchiveProfileLocksReleased $profile; (Get-Item -LiteralPath (Join-Path $profile 'SingletonLock')).Delete(); $released=Test-ArchiveProfileLocksReleased $profile; (Get-Item -LiteralPath $profile).Delete(); [pscustomobject]@{locked=$locked;released=$released}|ConvertTo-Json -Compress`;
    const output = execFileSync(powershell, ['-NoProfile', '-Command', command], { encoding: 'utf8' });
    expect(JSON.parse(output)).toEqual({ locked: false, released: true });
  });
});
