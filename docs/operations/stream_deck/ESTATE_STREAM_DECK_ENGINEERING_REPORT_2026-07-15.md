# Estate Stream Deck Engineering Report

Status: Canonical engineering capture, first complete pass  
Date: 2026-07-15  
Classification: Estate Internal  
Originator: Pat / Steward  
Prepared from: live implementation work, observed runtime output, plugin inspection, operational scripts, and Stream Deck inventory summaries

## 1. Purpose

This report captures the engineering history, current architecture, operational model, button inventory, troubleshooting record, and lessons learned required to rebuild, operate, and extend the Estate Stream Deck integration.

The report exists because a substantial portion of the working knowledge was developed interactively while repairing the plugin, operational scripts, process ownership model, health semantics, and button gestures. That knowledge must not remain only in chat history.

This document is intended to be useful to:

- the Steward;
- the Chief Architect;
- future Estate workers maintaining the Stream Deck plugin;
- workers rebuilding the plugin or Stream Deck profile after loss or migration;
- workers extending the Estate operational control layer;
- auditors distinguishing verified behavior from proposed future work.

## 2. Executive Summary

The Estate Stream Deck project crossed two distinct engineering phases.

### Phase A: plugin infrastructure repair

The plugin initially appeared broadly broken, but the underlying design was sound. The major plugin failures were caused by packaging, launch, manifest, and profile-format problems rather than a failed plugin concept.

The decisive repairs were:

- launching the plugin through `EstateStatusBridge.cmd` instead of launching Node directly;
- correcting `RequiredPlugins` metadata from an object array to a UUID string array;
- repairing generated Stream Deck profile data so unresolved placeholders were not emitted;
- preserving action UUIDs while repairing registration;
- restoring the plugin runtime so all 17 manifest actions registered and were recognized by Stream Deck.

After those corrections, the plugin loaded, installed, registered actions, rendered keys, updated status, and executed commands. From that point onward, the remaining problems belonged to the operational launcher layer rather than plugin packaging.

### Phase B: operational launcher engineering

The operational model was clarified and approved:

The Estate Core consists of exactly three required services:

1. Ollama, as provider;
2. Resident Gateway;
3. Open WebUI.

Everything else is optional and must not affect Core health.

Optional surfaces include:

- Office of the Steward;
- TextGen;
- SillyTavern;
- ComfyUI;
- Engineering Runtime;
- voice-development tools;
- other future services.

The approved Core display is:

```text
CORE 0/3
CORE 1/3
CORE 2/3
CORE 3/3
```

The previous runtime-style display such as `5/6` was rejected because it mixed required and optional services.

The operational layer was rebuilt around idempotent launchers, explicit ports, health URLs, process ownership checks, and separate Start, Stop, Restart, and Health behavior.

The final button interaction standard developed during this work is:

| Gesture | Meaning |
|---|---|
| Single tap | Ensure the service is running; do not open the browser |
| Double tap | Ensure the service is running, wait for health, then open its web interface |
| Long press, approximately 1.25 seconds | Stop the service |
| Status rendering | Show current service or Core state |

This gesture model is implemented for SillyTavern, TextGen, and ComfyUI, and long-press stop support was added for Resident Gateway, Office, Open WebUI, SillyTavern, TextGen, and ComfyUI.

## 3. Authoritative and Operational Locations

### Estate repository

```text
A:\theestate
```

GitHub repository:

```text
ppow1/theestate
```

### Plugin source

```text
A:\AI\Tools\EstateStreamDeckPlugin
```

### Installed Stream Deck plugin

```text
%APPDATA%\Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin
```

Typical expanded path:

```text
C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin
```

### Operational launcher layer

```text
A:\AI\Tools\EstateStreamDeckMVP\Core
```

### Stream Deck inventory exports

```text
A:\AI\Tools\EstateStreamDeckPlugin\inventory
```

Known inventory artifacts:

```text
profiles.csv
actions.csv
plugin-usage.csv
JSON exports
```

The inventory summary generated before the operational redesign reported:

- 415 actions across inventoried Stream Deck material;
- 20 plugin UUIDs;
- 107 actions in the Estate profile.

These local exports are the authoritative source for complete button-by-button inventory and must remain accessible during any profile consolidation or redesign.

## 4. Plugin Identity and Current Status

Plugin UUID:

```text
com.estate.statusbridge
```

Version during this work:

```text
0.2.0
```

Manifest action count:

```text
17
```

Known-good plugin behaviors after infrastructure repair:

- plugin installs;
- plugin loads;
- 17 actions register;
- Stream Deck recognizes the actions;
- buttons render;
- status updates render;
- repository status works;
- validation status works;
- readiness status works;
- runtime status works;
- Safe Sync executes;
- health executes;
- Start and Stop buttons execute.

The plugin should not be redesigned unless new evidence shows a plugin regression. The engineering priority is service control and workflow semantics.

## 5. Core Operational Philosophy

### Core definition

Core means only:

- Ollama;
- Resident Gateway;
- Open WebUI.

Core does not include:

- Office of the Steward;
- TextGen;
- SillyTavern;
- ComfyUI;
- Engineering Runtime;
- voice-development tooling;
- other optional applications.

### Core controls

#### Start Estate

Starts only:

1. Ollama;
2. Resident Gateway;
3. Open WebUI.

The start operation is idempotent. If a required service is already healthy, the launcher returns `already_running` and does not create a duplicate.

#### Stop Estate

Stops Core services in reverse dependency order:

1. Open WebUI;
2. Resident Gateway;
3. Ollama when appropriate under the ownership/session model.

Optional applications must not be stopped by Stop Estate.

#### Restart Estate

Performs a clean Core stop, verifies shutdown, starts Core once, and verifies final health.

#### Health

Health reports only the three Core services.

## 6. Estate Session State Versus Machine Availability

A major architectural clarification occurred around Ollama.

The machine may run Ollama for reasons unrelated to the current Estate Core session. Therefore, a machine-level Ollama process answering on port 11434 is not sufficient by itself to keep the Estate Core indicator active after Stop Estate.

The correct distinction is:

### Machine availability

Answers questions such as:

- Is an Ollama server reachable?
- Is the provider available externally?
- Which PID owns port 11434?

### Estate session state

Answers questions such as:

- Did Start Estate activate the provider requirement for this Estate session?
- Did the Estate launch the process, or adopt an already-running external dependency?
- Has Stop Estate ended the Estate Core session?

After Stop Estate, the Core display should show `CORE 0/3` even if an unrelated or automatically respawned Ollama process remains available to the machine.

The future runtime-state registry should record fields similar to:

```json
{
  "service": "ollama",
  "coreActive": true,
  "ownership": "external",
  "pid": 45008,
  "startedByEstate": false
}
```

or:

```json
{
  "service": "ollama",
  "coreActive": true,
  "ownership": "estate",
  "pid": 24100,
  "startedByEstate": true
}
```

On Stop Estate, `coreActive` becomes false in both cases. Only an Estate-owned PID should be terminated.

## 7. Service Configuration

The operational service configuration is maintained in:

```text
A:\AI\Tools\EstateStreamDeckMVP\Core\Estate-Service-Config.ps1
```

### Ollama

```text
Service ID: ollama
Port: 11434
Health: http://127.0.0.1:11434/api/tags
Command: ollama serve
Core: yes
```

Expected ownership evidence includes `ollama` and the `serve` command.

### Resident Gateway

```text
Service ID: resident_gateway
Port: 11435
Health: http://127.0.0.1:11435/v1/models
Command: C:\Python314\python.exe -m estate.cli.main resident-gateway start --host 127.0.0.1 --port 11435
Working directory: A:\theestate
PYTHONPATH: A:\theestate\src
Core: yes
```

The launcher should display the current Git commit, launch once, poll `/v1/models`, verify the resident catalog, and display READY.

### Open WebUI

```text
Service ID: open_webui
Primary port: 8080
Secondary observed/configured port: 3000
Health: http://127.0.0.1:8080/
Command: A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe serve --host 127.0.0.1 --port 8080
Working directory: A:\AI\OpenWebUI
Core: yes
```

Open WebUI may have a process chain involving `open-webui.exe` and one or more Python child processes. The actual listener observed on port 8080 was a Python child whose command line contained the Open WebUI executable path.

### Office of the Steward

```text
Service ID: office
Port: 8765
Health: http://127.0.0.1:8765/
Command: C:\Python314\python.exe -m estate.cli.main steward-command-center --serve --host 127.0.0.1 --port 8765
Working directory: A:\theestate
Core: no
```

### SillyTavern

```text
Service ID: sillytavern
Port: 8000
Health: http://127.0.0.1:8000/
Command: C:\Program Files\nodejs\node.exe server.js
Working directory: A:\AI\SillyTavern
Core: no
```

### TextGen

```text
Service ID: textgen
Ports: 7860, 5000, 5005, 7861
Primary UI health: http://127.0.0.1:7860/
API health candidate: http://127.0.0.1:5000/v1/models
Launcher: A:\AI\TextGen\textgen-4.9\textgen.bat --no-electron
Working directory: A:\AI\TextGen\textgen-4.9
Core: no
```

The old TextGen button failed because it used an obsolete launcher. The approved command is:

```text
textgen.bat --no-electron
```

### ComfyUI

```text
Service ID: comfyui
Port: 8188
Health: http://127.0.0.1:8188/
Python: A:\AI\envs\comfyui_server_py311\Scripts\python.exe
Main: A:\AI\ComfyUI\ComfyUI_Server\main.py
Working directory: A:\AI\ComfyUI\ComfyUI_Server
Core: no
```

The ComfyUI launcher includes:

```text
--listen 127.0.0.1
--port 8188
--input-directory A:\AI\Input
--output-directory A:\AI\Output
```

The service also uses A-drive cache and temporary locations.

## 8. Button Inventory

### 8.1 Inventory system

The complete existing Stream Deck inventory is stored locally under:

```text
A:\AI\Tools\EstateStreamDeckPlugin\inventory
```

The report must preserve access to:

- `profiles.csv` for profile-level records;
- `actions.csv` for action-level records;
- `plugin-usage.csv` for plugin UUID use;
- JSON exports for exact nested profile reconstruction.

The generated counts were:

```text
All inventoried actions: 415
Plugin UUIDs: 20
Estate profile actions: 107
```

The complete inventory contents were not copied into the Estate repository during this session. They remain required evidence for the later page consolidation and redesign effort. A future governed work package should copy or regenerate those exports into a durable repository location if institutional policy permits.

### 8.2 Known current Estate page

The working Estate page observed during this session includes the following visible controls:

#### Repository and validation row

- Sync;
- Repo status;
- Validation;
- Readiness.

Observed states included `Dirty`, validation state, and readiness state.

#### Core operations row

- Start Core;
- Stop Core;
- Restart Core;
- Health.

#### Individual service row

- Resident Gateway, displayed as RGW;
- Office;
- WebUI;
- Silly;
- Text;
- Comfy.

ComfyUI was added manually by dragging the registered `Start ComfyUI` action from the plugin action list because automatic active-profile injection did not locate the current page manifest.

### 8.3 Button semantics

#### Core buttons

| Button | Tap behavior | Double tap | Long press |
|---|---|---|---|
| Start Core | Start Ollama, Resident Gateway, Open WebUI | not currently assigned | not currently assigned |
| Stop Core | Stop Core only | not assigned | not assigned |
| Restart Core | Clean Core stop and start | not assigned | not assigned |
| Health | Report Core session state only | not assigned | not assigned |

#### Individual service buttons

| Button | Single tap | Double tap | Long press |
|---|---|---|---|
| RGW | Ensure Resident Gateway is running | not yet standardized to browser behavior | Stop Resident Gateway |
| Office | Ensure Office is running | not yet standardized to browser behavior | Stop Office |
| WebUI | Ensure Open WebUI is running | not yet standardized to browser behavior | Stop Open WebUI |
| Silly | Start SillyTavern only | Start, wait for health, open `http://127.0.0.1:8000/` | Stop SillyTavern |
| Text | Start TextGen only | Start, wait for health, open `http://127.0.0.1:7860/` | Stop TextGen |
| Comfy | Start ComfyUI only | Start, wait for health, open `http://127.0.0.1:8188/` | Stop ComfyUI |

The gesture timing implemented during this work was approximately:

```text
Double-tap window: 400 ms
Long-press threshold: 1250 ms
```

A long press must suppress the later key-up event so that stopping a service does not immediately trigger a normal start.

## 9. Plugin Event Model

The plugin originally executed actions on `keyDown` only.

To support long press and double tap, the event handler was expanded to process both:

```text
keyDown
keyUp
```

The handler maintains per-button context for:

- current press;
- long-press timer;
- whether long press already fired;
- pending first tap;
- double-tap timer.

### Long press sequence

1. `keyDown` records the press.
2. A 1250 ms timer begins.
3. If the key remains down through the threshold, the pending tap is canceled.
4. The button displays STOPPING.
5. The service-specific stop command executes.
6. `keyUp` does nothing further because the press was marked as long-triggered.

### Single and double tap sequence

1. First short release starts a 400 ms double-tap window.
2. If no second tap arrives, the normal start command executes.
3. If a second tap arrives, the single-tap timer is canceled.
4. The start-and-open command executes.
5. The start-and-open PowerShell script waits until the service is healthy before opening the browser.

The deliberate consequence is that a single tap is delayed by roughly 400 ms while the plugin waits to see whether a second tap follows.

## 10. Operational Script Architecture

The operational wrappers load a shared PowerShell library:

```text
Estate-Service-Lib.ps1
```

The principal functions include:

```text
Get-EstateService
Get-EstateServiceRuntimeStatus
Start-EstateServiceProcess
Stop-EstateServiceProcess
Start-EstateCore
Stop-EstateCore
Restart-EstateCore
Get-EstateCoreHealthData
```

The shared library is loaded with:

```powershell
. (Join-Path $PSScriptRoot "Estate-Service-Lib.ps1")
```

A deployment initially omitted this library entirely, which caused every wrapper to fail with errors such as:

```text
The term 'A:\AI\Tools\EstateStreamDeckMVP\Core\Estate-Service-Lib.ps1' is not recognized
```

and then secondary errors because expected functions were never defined.

The missing library was created and syntax-validated before button testing resumed.

## 11. Idempotency Requirements

Every service launcher must be idempotent.

Before starting:

1. Check the health URL.
2. Check expected TCP ports.
3. Identify listener PID.
4. Read executable and command line when available.
5. Determine whether the listener belongs to the intended service.
6. Return `already_running` when healthy.
7. Do not create duplicate servers.
8. If a stale owned process exists, stop it before one clean launch.
9. If a foreign process owns the port, report the PID, executable, and command line rather than killing it.

Before stopping:

1. Identify only the intended service.
2. Stop only positively matched processes or an explicitly owned listener.
3. Verify health endpoint failure and port release.
4. Return `already_stopped` when appropriate.

Before restarting:

1. Perform a clean stop.
2. Verify shutdown.
3. Start once.
4. Verify health.

## 12. Process Ownership Lessons

### 12.1 Generic fragments are unsafe

An early Resident Gateway matcher accepted any process containing the generic fragment:

```text
estate.cli.main
```

That incorrectly matched both Resident Gateway and Office of the Steward.

The corrected Resident Gateway signature requires service-specific evidence such as:

```text
resident-gateway
--port 11435
```

The Office signature uses:

```text
steward-command-center
--port 8765
```

### 12.2 Open WebUI listener ownership

Open WebUI may launch a process chain. The executable that initially starts may not be the same process that listens on port 8080.

Observed chain elements included:

- `open-webui.exe`;
- virtual-environment Python;
- a Python listener whose command line included the Open WebUI executable path.

The listener must not be classified as foreign merely because its executable is `python.exe`.

### 12.3 Process-chain race during stop

Stopping one member of a process tree may cause related children to exit automatically. The first stop implementation treated a later `Cannot find a process with the process identifier` message as a fatal error.

Correct behavior:

- recheck whether the process still exists;
- if it disappeared during shutdown, record `already_exited` or `exited_during_shutdown`;
- continue the stop operation;
- judge success by final service health and port state, not by whether every originally enumerated PID accepted a direct Stop-Process call.

### 12.4 Stream Deck process metadata can be incomplete

Under the Stream Deck-launched PowerShell context, `Win32_Process` sometimes returned:

- PID;
- process name;
- parent PID;

but returned null for:

- executable path;
- command line.

For an explicitly assigned service port, the system may accept ownership when:

1. the listener owns an expected service port;
2. available path or process-name evidence is compatible;
3. there is no conflicting foreign evidence.

This fallback enabled correct ComfyUI recognition on port 8188 when the listener metadata was incomplete.

### 12.5 Privilege mismatch

A process started from an elevated shell could not be stopped from the normal Stream Deck process context, producing:

```text
Access is denied
```

The immediate resolution was:

1. stop the elevated Resident Gateway from an elevated PowerShell session;
2. verify port 11435 was free;
3. restart the service through Stream Deck so the service and controller shared the same user and privilege level.

Operational rule:

> Services controlled by Stream Deck should be launched by Stream Deck or another process running under the same Windows user and privilege level.

## 13. Windows CMD and PowerShell Quoting Lessons

The most important wrapper bug was caused by placing the script path and script arguments inside the same quoted token.

### Incorrect

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Stop-EstateService.ps1 -ServiceId textgen"
```

Windows PowerShell interpreted the entire quoted string as the filename. It therefore reported that the supplied file did not have a `.ps1` extension because it believed the filename was:

```text
Stop-EstateService.ps1 -ServiceId textgen
```

### Correct

```cmd
@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Stop-EstateService.ps1" -ServiceId textgen %*
exit /b %ERRORLEVEL%
```

The closing quote must appear immediately after the actual `.ps1` path. Parameters must be separate command-line tokens.

The same rule applies to start-and-open wrappers:

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-EstateServiceAndOpen.ps1" -ServiceId comfyui -Url "http://127.0.0.1:8188/" %*
```

## 14. PowerShell Execution Policy Lesson

Running an unsigned script directly with `&` failed under the machine's current policy:

```text
The file ... is not digitally signed. You cannot run this script on the current system.
```

The accepted one-process invocation was:

```powershell
CLS

powershell.exe `
    -NoProfile `
    -ExecutionPolicy Bypass `
    -File "A:\AI\Tools\EstateStreamDeckPlugin\scripts\Install-Estate-LongPress-ComfyUI.ps1"
```

`-ExecutionPolicy Bypass` applies only to the new PowerShell process and does not permanently change the system policy.

## 15. PowerShell Parser and Installer Lessons

### 15.1 Do not pipe directly from a `foreach` statement

This form caused:

```text
An empty pipe element is not allowed
```

Incorrect:

```powershell
foreach ($Candidate in $Candidates) {
    [pscustomobject]@{ ... }
} | Format-Table
```

Correct:

```powershell
$CandidateResults = foreach ($Candidate in $Candidates) {
    [pscustomobject]@{ ... }
}

$CandidateResults | Format-Table
```

### 15.2 Regex-based function replacement is risky

A regex replacement intended to replace one PowerShell function damaged the shared library and produced multiple parser errors, including missing parentheses, unexpected tokens, incomplete hash literals, and unmatched braces.

Safer approaches:

- restore a known-good backup first;
- use the PowerShell AST to locate exact function extents;
- replace only the exact function span;
- parse the complete file immediately after writing;
- automatically restore the backup if parsing fails.

### 15.3 Exact-text installer patches are formatting-sensitive

The initial ComfyUI installer looked for an exact TextGen block and appended a ComfyUI block. After the configuration was manually repaired and reformatted, the installer's exact-text check failed even though ComfyUI was already configured.

Correct idempotency test:

```powershell
if ($CurrentServiceConfig -match '(?m)^\s*comfyui\s*=\s*@\{') {
    Write-Host "[SKIP] ComfyUI service already configured."
}
else {
    # perform insertion
}
```

Installers should test semantic presence where practical rather than exact formatting.

### 15.4 Validate every generated artifact

Required validation includes:

- PowerShell parser validation for every `.ps1` file;
- `node --check` for every changed JavaScript file;
- manifest JSON parsing;
- existence tests for every wrapper target;
- wrapper-content validation ensuring the quote closes after `.ps1`;
- action UUID registration checks;
- profile-update verification rather than assuming the page changed.

## 16. Stream Deck Profile Lessons

### 16.1 Automatic profile injection may not locate the active page

The installer attempted to locate a page manifest containing the TextGen action and add ComfyUI at position `6,1`. It reported:

```text
No active Estate profile page was changed.
```

The plugin action was nevertheless registered correctly. The working resolution was to drag `Start ComfyUI` manually from the Estate plugin action list into the empty slot next to Text.

The lesson is:

- action registration and page placement are separate concerns;
- a plugin can be correct even when the active profile page is not automatically modified;
- installer success must not claim page modification unless an explicit `[OK]` profile update was produced and verified.

### 16.2 Preserve action UUIDs

Action UUIDs are stable identifiers used by existing Stream Deck profiles. They must not be casually renamed during plugin repair.

The ComfyUI action used:

```text
com.estate.statusbridge.comfyui.start
```

### 16.3 RequiredPlugins format

The old profile metadata used an object structure similar to:

```json
{
  "RequiredPlugins": [
    {
      "UUID": "com.estate.statusbridge"
    }
  ]
}
```

The corrected form was:

```json
{
  "RequiredPlugins": [
    "com.estate.statusbridge"
  ]
}
```

This correction resolved the Stream Deck `Unable to identify plugin` failure.

## 17. Plugin Packaging Lessons

### Correct launcher

The plugin must launch through:

```text
bin\EstateStatusBridge.cmd
```

rather than launching Node directly.

The launcher provides the correct Windows execution context and argument flow expected by Stream Deck.

### Profile generation

Generated profiles must not contain unresolved placeholders. Profile imports were repaired only after generation emitted concrete values and correct plugin metadata.

### Registration verification

A valid package is not proven by successful file copy. Verification requires observing that Stream Deck registers all expected actions. The known-good count was 17.

## 18. Health Semantics and Display

Health must answer the question:

> Is the required Estate Core session active?

It must not answer:

> How many optional applications happen to be running on the machine?

The three Core segments correspond to:

1. provider requirement;
2. Resident Gateway;
3. Open WebUI.

Optional services require independent indicators such as:

```text
OFFICE
TEXTGEN
SILLY
COMFY
VOICE
ENG
```

Recommended individual states:

```text
OFF
STARTING
READY
STOPPING
ERROR
```

## 19. Start-and-Open Behavior

The double-tap feature uses a generic PowerShell script:

```text
Start-EstateServiceAndOpen.ps1
```

Its behavior is:

1. load the service library;
2. resolve the service by ID;
3. call the idempotent start function;
4. poll service health until ready or timeout;
5. open the configured browser URL;
6. return JSON describing `start_and_open`.

Current browser targets:

```text
SillyTavern: http://127.0.0.1:8000/
TextGen:     http://127.0.0.1:7860/
ComfyUI:     http://127.0.0.1:8188/
```

## 20. Safe Sync and Repository Status

The Estate page includes repository status and Sync controls. The repository status correctly showed `Dirty` when the local checkout contained changes.

The Sync button was intentionally not tested blindly because its behavior regarding dirty working trees, stashes, local generated files, pull conflicts, and overwrite policy had not yet been confirmed.

This concern is already represented institutionally by the Parking Lot item addressing local Git synchronization friction.

Before treating Sync as production-safe, the exact implementation must be reviewed for:

- whether it performs fetch, pull, merge, rebase, or reset;
- whether it creates a stash;
- whether it restores the stash automatically;
- how it handles untracked files;
- how it handles generated/runtime files;
- whether it can overwrite local work;
- how it reports conflicts;
- whether the button state distinguishes safe completion from partial completion.

## 21. Backup and Recovery Practices

Every modification script should create a timestamped backup under:

```text
A:\AI\Tools\EstateStreamDeckPlugin\backups
```

Examples created during this work included backup directories for:

- long-press and ComfyUI installation;
- long-press wrapper repair;
- double-tap installation.

The shared service library and configuration also received timestamped `.backup-*` or `.failed-*` copies before risky edits.

Required recovery behavior:

1. back up before writing;
2. write one logical change;
3. parse or syntax-check;
4. restore automatically on validation failure;
5. report the backup path.

## 22. Troubleshooting Matrix

| Symptom | Likely cause | Corrective action |
|---|---|---|
| `Unable to identify plugin` | Incorrect `RequiredPlugins` shape or packaging | Use UUID strings and correct CMD launcher |
| Actions do not appear | Manifest registration or installed runtime mismatch | Verify manifest, installed `bin` files, restart Stream Deck, confirm action count |
| Wrapper reports file has no `.ps1` extension | Script path and parameters placed inside one quoted filename | Close quote immediately after `.ps1`; pass parameters separately |
| Unsigned script cannot run | PowerShell execution policy | Run a new PowerShell process with `-ExecutionPolicy Bypass -File ...` |
| Missing `Estate-Service-Lib.ps1` | Incomplete operational deployment | Restore or create shared library before testing wrappers |
| Resident Gateway stop tries to stop Office | Ownership matcher used generic `estate.cli.main` fragment | Require `resident-gateway` and port-specific evidence |
| Open WebUI listener marked foreign | Listener is Python child rather than launcher executable | Match full command-line evidence containing Open WebUI path and port |
| Stop fails because PID vanished | Related process exited after parent or sibling was stopped | Recheck PID and treat disappearance as successful shutdown progress |
| Stop fails with Access Denied | Service started at higher privilege than Stream Deck | Stop elevated process elevated; relaunch through Stream Deck at matching privilege |
| Core remains 1/3 after Stop due to Ollama respawn | Health based solely on machine endpoint | Separate Estate session state from external machine availability |
| Comfy action registered but no key appears | Active profile page not automatically found | Drag action manually or explicitly locate and patch correct page manifest |
| PowerShell parser reports incomplete hash literal after installer | Incorrect block insertion or fragile text replacement | Restore backup, write a complete known-good configuration, parse before continuing |
| `foreach` followed by pipe causes parser error | Direct statement piping unsupported in that form | Assign loop output to a variable, then pipe the variable |
| Installer says expected block not found after manual repair | Exact-text idempotency check is formatting-dependent | Test for semantic service presence with regex or parsed structure |

## 23. Validation Checklist

### Plugin validation

- [ ] Installed plugin directory exists.
- [ ] `EstateStatusBridge.cmd` is the configured launcher.
- [ ] Manifest UUID is `com.estate.statusbridge`.
- [ ] Manifest contains the expected action set.
- [ ] Stream Deck recognizes all 17 registered actions.
- [ ] No unresolved profile placeholders remain.
- [ ] Stream Deck restarts without plugin errors.

### Core validation

- [ ] Health reports `CORE 0/3` when the Estate session is stopped.
- [ ] Start Core launches only Ollama requirement, Resident Gateway, and Open WebUI.
- [ ] Start Core reaches `CORE 3/3`.
- [ ] Running Start Core a second time returns `already_running` and creates no duplicates.
- [ ] Stop Core leaves Office, TextGen, SillyTavern, and ComfyUI unchanged.
- [ ] Restart Core performs one clean cycle and returns to `CORE 3/3`.

### Individual-service validation

For each managed service:

- [ ] Single tap starts or returns `already_running`.
- [ ] No duplicate listener is created.
- [ ] Long press displays HOLD or STOPPING and stops the intended service.
- [ ] Key release after long press does not restart the service.
- [ ] Stop verifies health failure and port release.
- [ ] Foreign processes are not terminated.

### Double-tap validation

For SillyTavern, TextGen, and ComfyUI:

- [ ] Single tap starts only.
- [ ] Double tap starts or adopts existing healthy service.
- [ ] Browser opens only after service health succeeds.
- [ ] Long press still takes precedence over tap handling.

### ComfyUI validation

- [ ] Port 8188 responds.
- [ ] Single tap while running returns `already_running`.
- [ ] Long press stops the port listener.
- [ ] Double tap opens `http://127.0.0.1:8188/`.

## 24. Current Known Limitations

1. The full 415-action inventory remains in local CSV and JSON exports and is not embedded in this report.
2. Automatic active-page insertion did not locate the current Estate page; ComfyUI was added manually.
3. The complete semantics of the Sync button still require review before it is considered production-safe.
4. The runtime registry discussed during engineering is not yet the authoritative implementation.
5. Core session state and machine availability still need a durable state model to prevent external provider processes from affecting Core display.
6. Double-tap browser behavior is currently standardized for SillyTavern, TextGen, and ComfyUI; Resident Gateway, Office, and WebUI can be considered separately.
7. Rich service-details views were intentionally parked and are not authorized for implementation merely because they were captured.

## 25. Parking Lot Reference

The proposed future Stream Deck operational details view was captured as:

```text
PL-0033 — Stream Deck Operational Details View
```

It proposes richer service information such as PID, port, uptime, current model, queue depth, VRAM, commit, resident count, latency, and recent errors.

The idea is parked. Capture does not authorize implementation.

## 26. Recommended Next Work Packages

The following should be considered as separate, governed work rather than ad hoc edits:

1. Archive or regenerate the complete Stream Deck inventory into a repository-approved durable location.
2. Audit and document Safe Sync behavior, including dirty-tree and stash policy.
3. Implement the Estate runtime/session registry for service ownership and Core-active state.
4. Consolidate the current 107-action Estate profile using the inventory rather than manual page-by-page reconstruction.
5. Add automated tests for wrapper quoting, action registration, long press, double tap, and profile generation.
6. Convert one-shot installers into small, numbered, idempotent patches with logs and rollback.

## 27. Engineering Principles Established

The most important durable principles from this work are:

### Do not confuse plugin infrastructure with service behavior

Once packaging and registration were repaired, further failures belonged to launchers, health checks, process ownership, or button semantics.

### Core must remain small and meaningful

A Core indicator is useful only when it represents required architecture rather than every optional application.

### Health is not ownership

A responding port proves availability. It does not by itself prove that the Estate owns the process or that the service belongs to the active Estate session.

### Stop only what can be positively identified

Never kill every `python.exe`, `node.exe`, or `cmd.exe`. Use service-specific command fragments, expected paths, ports, parent relationships, and recorded state.

### Idempotency is mandatory

Every start operation must be safe to press repeatedly.

### Windows quoting must be explicit

Quote the script path only. Pass PowerShell parameters outside the script-path quotes.

### Validate claims

A file copy is not a working plugin. A commit is not a working local checkout. A parsed script is not a healthy service. Every layer requires its own verification.

### Preserve working UUIDs and profiles

Do not redesign stable identifiers or settled page structure without evidence and an intentional work package.

## 28. Conclusion

The Estate Stream Deck plugin is no longer fundamentally a plugin-engineering problem. The plugin package loads, registers actions, renders state, and executes operational commands.

The significant engineering achievement was the transition from a fragile collection of launch buttons into a defined operational control model:

- three-service Core;
- independent optional surfaces;
- idempotent launchers;
- explicit health endpoints;
- process ownership safeguards;
- single-tap start;
- double-tap start-and-open;
- long-press stop;
- status-driven keys.

The implementation path was difficult and exposed multiple defects in installer design, quoting, parser safety, process discovery, privilege alignment, and profile modification. Those failures are recorded here so future workers do not repeat them.

The next phase should focus on durable runtime state, Safe Sync verification, inventory-backed profile consolidation, and automated regression testing—not a redesign of the working plugin framework.
