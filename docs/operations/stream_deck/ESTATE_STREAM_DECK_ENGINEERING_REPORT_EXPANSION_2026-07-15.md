# Estate Stream Deck Engineering Report — Detailed Expansion

Status: Canonical engineering expansion  
Date: 2026-07-15  
Classification: Estate Internal  
Originator: Pat / Steward  
Companion document: `docs/operations/stream_deck/ESTATE_STREAM_DECK_ENGINEERING_REPORT_2026-07-15.md`

## 1. Purpose and Relationship to the Main Report

This document expands the canonical Estate Stream Deck engineering report with the detailed chronology, architectural decisions, implementation failures, repairs, button behavior, inventory references, and durable lessons learned during the 2026-07-14 through 2026-07-15 implementation session.

It exists as a companion rather than a replacement because the existing canonical report is already large and complete enough to preserve the first-pass architecture. This expansion adds the detailed engineering narrative and exact failure patterns requested by the Steward.

The two documents together form the current canonical Stream Deck engineering record.

## 2. Final Operational Outcome

The Stream Deck plugin itself is operational.

Verified plugin state during the work:

- Plugin UUID: `com.estate.statusbridge`
- Version at the start of the work: `0.2.0`
- Manifest actions originally registered: 17
- Plugin installs and loads
- Stream Deck recognizes registered actions
- Buttons render
- Status values update
- Repository status works
- Validation status works
- Readiness status works
- Runtime status works
- Safe Sync action executes
- Health action executes
- Start and Stop controls execute

The principal engineering shift was recognizing that plugin packaging was no longer the problem. Once packaging, manifest metadata, launcher behavior, and profile generation were corrected, the remaining work belonged to the operational launcher layer.

## 3. Approved Operational Architecture

### 3.1 Estate Core

The Estate Core consists of exactly three required services:

1. Ollama, acting as provider
2. Resident Gateway
3. Open WebUI

Core health must report only these three services:

```text
CORE 0/3
CORE 1/3
CORE 2/3
CORE 3/3
```

The previous style of runtime count such as `5/6` was rejected because it mixed required services with optional applications.

### 3.2 Optional Operational Surfaces

The following are independent and do not affect Core health:

- Office of the Steward
- TextGen
- SillyTavern
- ComfyUI
- Engineering Runtime
- voice-development tools
- future optional services

### 3.3 Standard Button Gesture Model

The final interaction vocabulary is:

| Gesture | Action |
|---|---|
| Single tap | Ensure service is running; do not open browser |
| Double tap | Ensure service is running, wait for health, then open web interface |
| Long press, approximately 1.25 seconds | Stop the service |
| Button status | Show current service or Core condition |

Double-tap browser behavior was implemented for SillyTavern, TextGen, and ComfyUI.

Long-press stop behavior was implemented for:

- Resident Gateway
- Office of the Steward
- Open WebUI
- SillyTavern
- TextGen
- ComfyUI

## 4. Authoritative Paths

### 4.1 Estate repository

```text
A:\theestate
```

GitHub repository:

```text
ppow1/theestate
```

### 4.2 Plugin source

```text
A:\AI\Tools\EstateStreamDeckPlugin
```

### 4.3 Installed plugin

```text
%APPDATA%\Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin
```

Observed expanded location:

```text
C:\Users\wille\AppData\Roaming\Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin
```

### 4.4 Operational scripts

```text
A:\AI\Tools\EstateStreamDeckMVP\Core
```

### 4.5 Stream Deck inventory

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

Generated counts:

```text
All inventoried actions: 415
Plugin UUIDs: 20
Estate profile actions: 107
```

These exports remain the authoritative detailed source for later page consolidation and redesign.

## 5. Detailed Engineering Chronology

### Phase 1 — Plugin Packaging and Registration

The plugin initially appeared generally broken. The underlying action model was not the primary failure.

The decisive plugin-level repairs were:

1. Correct plugin launcher
2. Correct `RequiredPlugins` format
3. Correct generated profile format
4. Preserve action UUIDs
5. Verify registration of all actions

#### Correct launcher

The installed plugin must launch through:

```text
bin\EstateStatusBridge.cmd
```

Direct Node launch was replaced with a stable CMD entry point.

#### RequiredPlugins correction

Incorrect conceptual structure:

```json
{
  "RequiredPlugins": [
    {
      "UUID": "com.estate.statusbridge"
    }
  ]
}
```

Correct structure:

```json
{
  "RequiredPlugins": [
    "com.estate.statusbridge"
  ]
}
```

This repair resolved the Stream Deck error:

```text
Unable to identify plugin
```

#### Profile generation repair

Generated profiles previously contained unresolved placeholders or invalid metadata. The profile generator was corrected so the profile imported successfully and referenced the real plugin UUID.

#### Registration result

After packaging and manifest repairs, 17 actions registered and were recognized by Stream Deck.

At that point, the plugin framework was treated as stable unless new evidence showed a regression.

### Phase 2 — Operational MVP and Core Definition

The operational MVP was established under:

```text
A:\AI\Tools\EstateStreamDeckMVP\Core
```

Initial scripts included:

```text
Start-EstateCore
Stop-EstateCore
Restart-EstateCore
Start-Ollama
Start-ResidentGateway
Start-OpenWebUI
Get-EstateCoreHealth
Estate-Service-Config
```

The approved semantics became:

- Start Estate starts only Ollama, Resident Gateway, and Open WebUI
- Stop Estate stops only the Core session
- Restart Estate performs stop, verifies shutdown, starts once, and verifies health
- Office, TextGen, SillyTavern, and ComfyUI remain independent

### Phase 3 — Missing Shared Library

The first direct Core button tests failed because the wrappers dot-sourced a file that did not exist:

```text
A:\AI\Tools\EstateStreamDeckMVP\Core\Estate-Service-Lib.ps1
```

Observed error pattern:

```text
The term 'A:\AI\Tools\EstateStreamDeckMVP\Core\Estate-Service-Lib.ps1' is not recognized
```

Follow-on function errors included:

```text
Stop-EstateCore is not recognized
Restart-EstateCore is not recognized
Get-EstateCoreHealthData is not recognized
```

The reason was simple: the wrappers were a matched set whose shared implementation library had been omitted.

The library was created and validated. Required functions included:

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

After creation, health reported:

```text
CORE 3/3
```

### Phase 4 — Process Ownership Corrections

#### Resident Gateway versus Office collision

The first ownership matcher accepted generic command fragments. Because both Resident Gateway and Office used:

```text
python.exe -m estate.cli.main
```

Resident Gateway matching incorrectly included the Office of the Steward process.

The Resident Gateway signature was narrowed to service-specific evidence:

```text
resident-gateway
--port 11435
```

The Office signature remained distinct:

```text
steward-command-center
--port 8765
```

After correction, Resident Gateway matching contained only the gateway process.

#### Open WebUI child listener

Open WebUI launched a small process chain. The listener on port 8080 was a Python child process whose command line included:

```text
A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe
```

The original matcher classified the listener as foreign because it expected `open-webui.exe` as the executable name.

The signature was corrected to recognize the Open WebUI Python listener based on combined process name, executable information, command line, and expected port.

After correction:

- the listener appeared under `ownedPortProcesses`
- `foreignPortProcesses` was empty
- Office remained outside Resident Gateway ownership

### Phase 5 — Stop Process Race

Stopping an Open WebUI process caused related child or parent processes to exit automatically. The stop loop then attempted to stop a PID that no longer existed.

Observed error:

```text
Cannot find a process with the process identifier 40984
```

This was not a failed shutdown. It was a process-tree race during successful teardown.

The stop implementation was changed to:

1. Recheck whether each PID exists before stopping
2. Treat an already-absent PID as `already_exited`
3. Recheck after a failed stop call
4. Treat disappearance during shutdown as `exited_during_shutdown`
5. Verify service health and port state after the process loop

This made process-tree shutdown idempotent and tolerant of normal child-process exits.

### Phase 6 — Stream Deck Visibility and Missing Command Lines

When invoked from Stream Deck, Windows process inspection sometimes returned:

- PID
- process name
- listener port

but omitted:

- executable path
- command line

Resident Gateway was then misclassified as foreign even though the port and PID were correct.

The ownership model was adjusted so that when command-line details are unavailable, a listener can be accepted only when:

1. the process/path evidence matches the expected service family when available; and
2. the process owns one of the service's explicitly assigned ports.

This fallback is narrower than treating every listener on the port as owned.

### Phase 7 — Privilege Mismatch

A Resident Gateway process had been started from an elevated context. Stream Deck ran normally and could identify the process but could not terminate it.

Observed error:

```text
Cannot stop process "python (...)" because of the following error: Access is denied
```

The elevated process was stopped from an Administrator PowerShell session. The service was then restarted from the same ordinary user context as Stream Deck.

Durable rule:

> Services controlled by Stream Deck should be launched under the same Windows user and privilege level as the Stream Deck plugin.

Do not start an Estate-managed service from an elevated console unless the control layer is also intentionally elevated.

### Phase 8 — Ollama Machine State versus Estate State

Stop Core successfully terminated the Ollama PID it had targeted, but the Ollama desktop or tray manager respawned a server process. The health display therefore still showed one green Core segment.

The Steward clarified the required architecture:

- The Estate owns the process it starts, not every Ollama process on the machine
- If Ollama is already available when Start Core runs, it may be treated as an external dependency
- Stop Core ends the Estate Core session
- A system-managed or automatically respawned Ollama process must not keep the Estate Core bar active after the session is stopped

This created the required distinction between:

```text
Machine availability
```

and:

```text
Estate session activity
```

A future runtime registry should record whether a service was Estate-started or externally available.

### Phase 9 — ComfyUI Integration

ComfyUI was added as an optional service.

Service definition:

```text
Service ID: comfyui
Port: 8188
Health: http://127.0.0.1:8188/
Python: A:\AI\envs\comfyui_server_py311\Scripts\python.exe
Main: A:\AI\ComfyUI\ComfyUI_Server\main.py
Working directory: A:\AI\ComfyUI\ComfyUI_Server
Core: no
```

Arguments included:

```text
--listen 127.0.0.1
--port 8188
--input-directory A:\AI\Input
--output-directory A:\AI\Output
```

The Stream Deck button correctly detected an existing healthy ComfyUI service and returned:

```text
result: already_running
state: READY
```

This confirmed idempotent short-press behavior.

Automatic page injection did not locate the active Estate page. The action was nevertheless registered and was added manually from the plugin action list.

### Phase 10 — Long-Press Stop

The original plugin fired commands on `keyDown` only. Long-press behavior required separate handling for:

- `keyDown`
- `keyUp`
- press timer
- cancellation of normal tap after long press

Approved threshold:

```text
approximately 1.25 seconds
```

Required behavior:

1. Key down starts a timer
2. Holding beyond threshold runs the stop command
3. Long-press release must not run the start command
4. Short release runs start

### Phase 11 — Windows `-File` Quoting Failure

The first generated stop wrapper failed with:

```text
Processing -File 'A:\AI\Tools\EstateStreamDeckMVP\Core\Stop-EstateService.ps1 -ServiceId textgen' failed because the file does not have a '.ps1' extension
```

The incorrect wrapper quoted the script path and parameter as one filename:

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Stop-EstateService.ps1 -ServiceId textgen"
```

Windows PowerShell interpreted this entire value as the filename:

```text
Stop-EstateService.ps1 -ServiceId textgen
```

Correct wrapper:

```cmd
@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Stop-EstateService.ps1" -ServiceId textgen %*
exit /b %ERRORLEVEL%
```

Critical rule:

> Quote only the script path after `-File`. Pass PowerShell script parameters as separate command-line arguments outside the filename quotes.

The same pattern was applied to all service wrappers.

### Phase 12 — Double Tap

Double tap was added for SillyTavern, TextGen, and ComfyUI.

Approved behavior:

```text
Single tap: start only
Double tap: start, wait for health, open browser
Long press: stop
```

The double-tap window was approximately 400 milliseconds.

The first release is delayed briefly. If no second tap arrives, normal start executes. If a second tap arrives, the pending single-tap action is cancelled and start-and-open executes.

Browser URLs:

```text
SillyTavern: http://127.0.0.1:8000/
TextGen:     http://127.0.0.1:7860/
ComfyUI:     http://127.0.0.1:8188/
```

The browser opens only after the service reports healthy.

## 6. Service and Button Inventory

### 6.1 Core controls

| Control | Purpose |
|---|---|
| Start Estate | Start Ollama, Resident Gateway, and Open WebUI only |
| Stop Estate | End the Estate Core session and stop owned Core processes |
| Restart Estate | Clean Core stop followed by one verified start |
| Health | Report only `CORE 0/3` through `CORE 3/3` |

### 6.2 Individual service controls

| Button | Single Tap | Double Tap | Long Press | Core |
|---|---|---|---|---|
| RGW | Start Resident Gateway | Not standardized during this session | Stop Resident Gateway | Yes |
| OFFICE | Start Office of the Steward | Not standardized during this session | Stop Office | No |
| WEBUI | Start Open WebUI | Not standardized during this session | Stop Open WebUI | Yes |
| SILLY | Start SillyTavern | Start and open `http://127.0.0.1:8000/` | Stop SillyTavern | No |
| TEXT | Start TextGen | Start and open `http://127.0.0.1:7860/` | Stop TextGen | No |
| COMFY | Start ComfyUI | Start and open `http://127.0.0.1:8188/` | Stop ComfyUI | No |

### 6.3 Known operational wrapper files

```text
Start-EstateCore.cmd
Stop-EstateCore.cmd
Restart-EstateCore.cmd
Get-EstateCoreHealth.cmd
Start-Ollama.cmd
Start-ResidentGateway.cmd
Start-OpenWebUI.cmd
Start-EstateService.ps1
Stop-EstateService.ps1
Start-EstateServiceAndOpen.ps1
Start-ComfyUI.cmd
Stop-ComfyUI.cmd
Stop-ResidentGateway.cmd
Stop-Office.cmd
Stop-OpenWebUI.cmd
Stop-SillyTavern.cmd
Stop-TextGen.cmd
Start-SillyTavern-And-Open.cmd
Start-TextGen-And-Open.cmd
Start-ComfyUI-And-Open.cmd
```

### 6.4 Local inventory requirement

The complete 415-action inventory is not reproduced line by line in this report because the local CSV and JSON exports are the exact source. Any future redesign must inspect:

```text
A:\AI\Tools\EstateStreamDeckPlugin\inventory\profiles.csv
A:\AI\Tools\EstateStreamDeckPlugin\inventory\actions.csv
A:\AI\Tools\EstateStreamDeckPlugin\inventory\plugin-usage.csv
A:\AI\Tools\EstateStreamDeckPlugin\inventory\*.json
```

Do not redesign all pages from screenshots or memory when these exports are available.

## 7. Architectural Decision Records

### ADR-SD-001 — Stream Deck is an operational console

The Stream Deck is not merely an application launcher. Buttons represent operational state and invoke a shared service-management layer.

Consequences:

- status is dynamic
- launchers are idempotent
- health is verified
- stop behavior is ownership-aware
- future details and metrics can extend the same model

### ADR-SD-002 — Core is exactly three services

Core is Ollama, Resident Gateway, and Open WebUI. Optional surfaces do not alter Core health.

### ADR-SD-003 — Estate ownership differs from machine ownership

The Estate may use an already-running external dependency without assuming authority over every matching machine process.

### ADR-SD-004 — Launchers must be idempotent

Before start:

1. Check health
2. Check assigned ports
3. Inspect PID, executable, and command line when available
4. Do not launch duplicates
5. Report `already_running` when appropriate

### ADR-SD-005 — Standard gesture vocabulary

Single tap starts, double tap starts and opens, long press stops.

### ADR-SD-006 — Browser launch follows health

Do not open a service web page until its health endpoint responds.

### ADR-SD-007 — Canonical service configuration

Each service record should define:

- service ID
- display name
- Core classification
- ports
- health URLs
- command
- arguments
- working directory
- environment
- ownership signatures

### ADR-SD-008 — CMD wrappers are stable entry points

Stream Deck invokes CMD wrappers that call PowerShell with explicit execution policy and correct argument separation.

### ADR-SD-009 — Validate before deployment

Generated artifacts must be validated before Stream Deck restart.

PowerShell validation:

```powershell
[System.Management.Automation.Language.Parser]::ParseFile(...)
```

Node validation:

```text
node --check <file>
```

### ADR-SD-010 — Inventory drives future redesign

The existing CSV and JSON inventory is the authoritative evidence for profile consolidation.

## 8. Engineering Lessons Learned

### LL-SD-001 — The plugin was not fundamentally broken

Packaging, launcher, manifest, and profile errors created broad failure symptoms. The underlying action architecture survived.

### LL-SD-002 — Stream Deck packaging errors are misleading

A malformed launcher, manifest, profile, or `RequiredPlugins` field can all surface as plugin-identification failures.

### LL-SD-003 — Preserve stable UUIDs

Once actions are recognized by profiles, UUID stability is essential. Fix behavior without arbitrarily renaming actions.

### LL-SD-004 — Separate plugin engineering from operational engineering

Once actions register and execute, service behavior belongs in the operational layer. Do not repeatedly reopen settled plugin packaging.

### LL-SD-005 — Quote script paths, not script-plus-arguments

Incorrect:

```cmd
-File "%~dp0Stop-EstateService.ps1 -ServiceId textgen"
```

Correct:

```cmd
-File "%~dp0Stop-EstateService.ps1" -ServiceId textgen
```

### LL-SD-006 — Validate generated files before use

Every PowerShell and JavaScript modification should be syntax-checked before deployment.

### LL-SD-007 — Back up before every patch

Use timestamped backups before modifying:

- PowerShell
- CMD
- JavaScript
- JSON
- manifests
- profile files

### LL-SD-008 — Installers must be idempotent

An installer must detect:

- already configured
- already patched
- already registered
- already present

It should not depend solely on finding one exact old text block.

### LL-SD-009 — Large one-shot installers are fragile

The initial installer combined service configuration, JavaScript changes, manifests, wrappers, profile editing, validation, and restart. One formatting failure interrupted the entire sequence.

Future changes should prefer numbered, single-purpose, idempotent patches with validation and rollback.

### LL-SD-010 — Health is more meaningful than PID existence

A process may exist while the service is unusable. READY requires a successful health check.

### LL-SD-011 — Ports alone do not prove ownership

Port ownership is evidence, not complete identity. Use executable and command-line evidence when available.

### LL-SD-012 — Process trees require race-tolerant shutdown

Stopping one process may terminate others. Already-exited children are normal shutdown outcomes, not errors.

### LL-SD-013 — Privilege level is part of process ownership

A normal Stream Deck plugin cannot necessarily terminate a service started from an elevated console.

### LL-SD-014 — Machine availability and Estate session state must remain distinct

A system-managed Ollama process can remain available after the Estate Core session is stopped. The Core indicator should still become inactive.

### LL-SD-015 — Health displays should reflect architecture, not application count

`CORE 3/3` communicates readiness. `5/6` communicates an arbitrary runtime count.

### LL-SD-016 — Gesture consistency reduces operational complexity

A uniform tap/double-tap/hold model makes optional services predictable.

### LL-SD-017 — Profile automation must be verified against the real active profile

The ComfyUI action registered successfully, but automatic active-page injection did not locate the page. Manual placement was required.

Do not report profile modification complete unless the actual active profile has been fetched or visibly verified.

### LL-SD-018 — PowerShell execution policy should be scoped, not weakened globally

Unsigned local installers were run with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File <script>
```

This affects only the launched PowerShell process and avoids permanently weakening machine policy.

### LL-SD-019 — GitHub completion claims require fetch verification

A successful write call is not sufficient proof that a large file is complete. Fetch the file after writing, inspect beginning and ending content, and verify the blob SHA.

### LL-SD-020 — Do not infer success from a section heading alone

Installer output such as:

```text
=== ADD COMFY TO ACTIVE PAGE ===
```

without an explicit success record did not prove the page was modified.

### LL-SD-021 — The local inventory must remain accessible

The inventory contains details that cannot be reconstructed reliably from screenshots or chat memory.

## 9. Troubleshooting Reference

| Symptom | Likely Cause | Corrective Direction |
|---|---|---|
| `Unable to identify plugin` | Launcher, manifest, `RequiredPlugins`, or profile metadata | Verify packaging before redesigning code |
| Missing `Estate-Service-Lib.ps1` | Incomplete operational script set | Restore or create the shared library |
| Office appears as Resident Gateway | Ownership signature too generic | Require service-specific command fragments and port |
| Open WebUI listener appears foreign | Listener is Python child | Match command line and process chain |
| Cannot find PID during shutdown | Process exited because related process stopped | Recheck and classify as already exited |
| Access denied stopping service | Privilege mismatch | Stop elevated process from elevated shell, then relaunch normally |
| `-File ... does not have a .ps1 extension` | Script arguments included inside filename quotes | Quote only the script path |
| Unsigned script blocked | Execution policy | Use process-scoped `-ExecutionPolicy Bypass` |
| ComfyUI starts but button reports `already_running` | Service was already healthy | Correct idempotent result |
| ComfyUI action registered but not visible | Active profile not automatically modified | Drag action manually or patch verified active profile |
| One Core bar remains after Stop Core | External or respawned Ollama | Separate Estate session state from machine availability |
| Browser opens before service is ready | No health wait | Poll health before opening URL |

## 10. Validation Checklist

### Plugin validation

- Plugin folder exists under Stream Deck Plugins
- `EstateStatusBridge.cmd` is the launcher
- Plugin UUID is `com.estate.statusbridge`
- Manifest parses
- Registered actions appear in Stream Deck
- Node files pass `node --check`

### Core validation

- Health reports only three services
- Start Core results in `CORE 3/3`
- Repeated Start Core does not create duplicates
- Stop Core ends the Estate Core session
- Restart Core performs one stop and one start
- Optional services remain independent

### Service-button validation

For SillyTavern, TextGen, and ComfyUI:

1. Single tap starts without opening browser
2. Double tap starts and opens the correct URL
3. Long press stops the service
4. Long-press release does not restart it
5. Repeated single tap reports `already_running`

For RGW, Office, and WebUI:

1. Single tap starts
2. Long press stops
3. Ownership does not cross service boundaries

### Inventory validation

Confirm continued access to:

```text
profiles.csv
actions.csv
plugin-usage.csv
JSON exports
```

## 11. Remaining Work and Parking Lot

The detailed operational view concept was captured as:

```text
PL-0033 — Stream Deck Operational Details View
```

It may later show:

- PID
- uptime
- port
- health endpoint
- Git commit
- active models
- queue depth
- VRAM
- CPU and memory
- recent errors
- last restart

Capture does not authorize implementation.

Other remaining work includes:

- authoritative Estate Core session registry
- exact service ownership records
- safe and documented Sync behavior
- consolidation of all Stream Deck pages using the inventory exports
- repository-backed preservation of selected inventory outputs if approved
- replacement of large all-in-one installers with numbered patches

## 12. Durable Operating Principles

1. Do not redesign a plugin that has already been proven operational without new evidence.
2. Core health must reflect the approved architecture.
3. Optional applications must remain independently controllable.
4. Every launcher must be idempotent.
5. Health checks are authoritative for readiness.
6. Ownership must be positively established before stop.
7. Process-tree shutdown must tolerate related processes exiting first.
8. Stream Deck and managed services should use compatible privilege levels.
9. Quote Windows script paths correctly and pass parameters separately.
10. Validate PowerShell and JavaScript before deployment.
11. Back up files before modification.
12. Verify profile changes against the real active profile.
13. Verify GitHub writes by fetching and reading the result.
14. Preserve access to the inventory exports.
15. Park deferred ideas instead of silently implementing them.

## 13. Verification Marker

This exact final marker is intentionally included to detect truncation during repository verification:

```text
END-OF-ESTATE-STREAM-DECK-ENGINEERING-EXPANSION-2026-07-15
```
