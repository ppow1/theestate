# Stream Deck Maintenance and Repair Guide

This guide is the durable handoff for Riverview and Estate Stream Deck work. The live installed configuration is runtime truth; the companion `STREAM_DECK_CURRENT_INVENTORY.json` and this guide are captured snapshots and become stale after manual Stream Deck edits.

## Safe starting procedure

1. Read this guide and the current inventory.
2. Verify repository roots, branch/HEAD, and unrelated worktree changes in both repositories.
3. Re-inventory `C:\\Users\\wille\\AppData\\Roaming\\Elgato\\StreamDeck\\ProfilesV3` before editing.
4. Confirm the target profile/device and distinguish active pages from unused/default page directories.
5. Back up the complete installed tree before direct profile/plugin modification. Use a timestamped directory under `C:\\Users\\wille\\AppData\\Roaming\\Elgato\\StreamDeck-Backups`.
6. Make the smallest change, restart Stream Deck only if required, validate manifests, inspect logs, and perform physical acceptance where the task claims button behavior.

## Native Stream Deck architecture

Stream Deck 7.5.1.22901 stores native profiles below `ProfilesV3`. Each physical profile is a UUID-named `.sdProfile` directory containing a top-level `manifest.json` and `Profiles\\<page UUID>\\manifest.json` files. The top-level manifest carries the display name, native profile UUID, device model/UUID, version, and `Pages.Current`, `Pages.Default`, and `Pages.Pages`. Page manifests contain controller actions keyed by manifest coordinates such as `0,0` through `7,3`; these are column,row coordinates on the observed 8x4 deck.

Installed plugins are under `C:\\Users\\wille\\AppData\\Roaming\\Elgato\\StreamDeck\\Plugins`. Riverview’s installed plugin is `C:\\Users\\wille\\AppData\\Roaming\\Elgato\\StreamDeck\\Plugins\\com.riverview.operator.sdPlugin`; repository source is `A:\\Riverview\\repo\\tools\\powershell\\stream_deck\\riverview-native-plugin`.

An action has a native action UUID, optional plugin UUID, settings, title/state, and coordinate. Profile navigation and page navigation are separate native actions:

- Profile navigation: plugin `com.elgato.streamdeck.profile.rotate`, action `com.elgato.streamdeck.profile.rotate`, settings `ProfileUUID`, `PageIndex`, and `DeviceUUID`.
- Page navigation: `com.elgato.streamdeck.page.previous`, `com.elgato.streamdeck.page.next`, `com.elgato.streamdeck.page.goto`, and `com.elgato.streamdeck.page.indicator`.

A Switch Profile action targets one explicit profile UUID. “Previous” and “next” are labels/conventions, not built-in ring semantics. A ring is created by assigning targets so NEXT(i)=i+1 with N->1 and PREVIOUS(i)=i-1 with 1->N. Validate both directions and do not confuse page actions with profile actions.

## Riverview native plugin lifecycle

The installed plugin is `com.riverview.operator`. Its WebSocket session is launched by Stream Deck with runtime arguments including the port, plugin UUID, and register event. Registration must use the runtime `args.pluginUUID`; an earlier implementation hard-coded `com.riverview.operator`, which prevented action lifecycle routing. The plugin must register correctly before `willAppear`, `keyDown`, and `keyUp` can be trusted.

The useful lifecycle evidence is:

- `willAppear`: action is visible; initialize/render status.
- `keyDown`: physical press begins.
- `keyUp`: physical press ends.
- gesture classification: single/double/long based on timing.
- wrapper run: selected control/gesture is launched and output is captured.
- status refresh: re-read the authoritative boundary after appearance and after action completion, with bounded periodic refresh where practical.

Installed diagnostics:
- `C:\\Users\\wille\\AppData\\Roaming\\Elgato\\StreamDeck\\Plugins\\com.riverview.operator.sdPlugin\\riverview-native-events.log`
- `C:\\Users\\wille\\AppData\\Roaming\\Elgato\\StreamDeck\\Plugins\\com.riverview.operator.sdPlugin\\riverview-native-plugin.log`
- `C:\\Users\\wille\\AppData\\Roaming\\Elgato\\StreamDeck\\Plugins\\com.riverview.operator.sdPlugin\\riverview-native-runs.log`

Use events for lifecycle/press evidence, plugin log for startup/registration/runtime errors, and runs for child-process executable/arguments/PID/stdout/stderr/exit evidence.

## PowerShell execution and window hygiene

The verified PowerShell 7 executable is `C:\\Program Files\\PowerShell\\7\\pwsh.exe`. Stream Deck plugins should use an absolute executable path, not a bare `pwsh.exe`, because Stream Deck’s environment may not inherit the interactive PATH. Use deterministic script paths and pass arguments as an explicit array.

Runtime and Quest actions must run in the background without blank PowerShell, cmd, or Terminal windows. Prefer a verified hidden `ProcessStartInfo`/CreateNoWindow or equivalent while retaining durable diagnostics. Do not hide failure evidence: capture executable, arguments, child PID, stdout, stderr, exit code, signal, and timestamps in plugin-owned logs.

## RIVERVIEW RUNTIME button boundary

The RIVERVIEW RUNTIME button means the Riverview Operator HTTP server, not aggregate Riverview Supervisor health, CME, Comms5, Relay, Spatial, or every managed service.

Authoritative boundary:
- page: `http://127.0.0.1:18082/`
- health: `http://127.0.0.1:18082/health`

Status mapping:
- GREEN / RUNNING: the Operator HTTP server is reachable and healthy.
- YELLOW / STARTING or ERROR: startup/stop was requested or the port responds but health is not healthy yet.
- RED / STOPPED: nothing responds correctly on the Operator endpoint.

Single press is idempotent ensure/start and verifies health. Double press ensures start then opens/raises the Operator page. Long press stops only the Operator HTTP server through its canonical start/stop path; it does not stop all Riverview services. Startup can take roughly 30–45 seconds in observed acceptance, so the button should show STARTING and poll health before converging to RUNNING. Launches must be hidden/background.

## QUEST DEV

Quest Dev means “show the Quest screen copy.” The authoritative launcher is `A:\\Riverview\\repo\\runtime\\quest-observability\\Quest-LeftEyeMirror.ps1`. Single press ensures an authorized Quest transport, launches or raises the Riverview-owned mirror, and verifies the visible window. Long press stops only the Riverview-owned mirror and should not disconnect reusable wireless ADB merely because screen copy stopped.

Observed acceptance evidence included wireless endpoint `192.168.1.159:5555` and service `adb-1WMHHB67ZF1473 _adb._tcp 192.168.1.159:5555`. These are historical diagnostic observations only and must never be hard-coded. Current discovery must inspect authorized devices, current mDNS services including `_adb._tcp` and `_adb-tls-connect._tcp`, current IP/port, and verify shell identity.

Status semantics:
- GREEN / LIVE: the actual Riverview-owned scrcpy process/window exists.
- YELLOW / ADB or USB: Quest transport is authorized/reachable but mirror is not running.
- YELLOW / BLOCKED: Quest is visible but unauthorized or only partially usable.
- RED / OFF: no usable Quest is discovered.

Critical invariant: ADB connected is not the same as mirror live. Mirror status must use the owned `scrcpy.exe`/window identity, title `Riverview Quest Live View`, and command line when needed. Do not infer LIVE from the last button press or ADB alone.

## QUEST CAST

Quest Cast remains a deliberately bounded BLOCKED capability until a verified Meta casting automation mechanism is available. A clean Riverview BLOCKED result is different from a Stream Deck/plugin failure.

## Estate four-service controls: CORE / RGW / OFFICE / WEBUI

These four controls are service-scoped controls, not one aggregate start/restart surface.

| Button | Action UUID | Service ownership | Current single-press command | Long press |
|---|---|---|---|---|
| CORE | `com.estate.statusbridge.surfaces.start` | `ollama`, `resident_gateway`, `open_webui` | `A:\\AI\\Tools\\EstateStreamDeckMVP\\Core\\Start-EstateCore.cmd` | none on this action |
| RGW | `com.estate.statusbridge.resident_gateway.start` | `resident_gateway` | `A:\\AI\\Tools\\EstateStreamDeckMVP\\Core\\Start-ResidentGateway.cmd` | `Stop-ResidentGateway.cmd` |
| OFFICE | `com.estate.statusbridge.office.start` | `office` only | `A:\\theestate\\tools\\streamdeck\\estate-service-runtime\\Core\\Start-Office.cmd` | `Stop-Office.cmd` in the same repository-owned runtime directory |
| WEBUI | `com.estate.statusbridge.open_webui.start` | `open_webui` | `A:\\AI\\Tools\\EstateStreamDeckMVP\\Core\\Start-OpenWebUI.cmd` | `Stop-OpenWebUI.cmd` |

The action definitions are maintained in `tools/streamdeck/estate-status-bridge/src/actions.js`; the installed action definitions are generated from that source. The four actions use `kind=serviceControl`, `operation=start`, and exact `serviceIds` shown above. The plugin classifies a short press as single when no double-press command is defined; a press held for approximately 1.25 seconds uses the configured long-press command. These semantics must not be inferred from button labels.

The legitimate service boundary is:

- CORE owns the three required Core services listed above.
- RGW owns the Resident Gateway on `127.0.0.1:11435`.
- OFFICE owns the Office of the Steward on `127.0.0.1:8765`.
- WEBUI owns Open WebUI on `127.0.0.1:8080` (or its configured alternate port).

OFFICE currently has no declared service dependency in the canonical runtime configuration. Its ensure operation must therefore inspect only `office`, start it if stopped, and leave healthy Core/RGW/WEBUI processes alone. The repository-owned `Start-Office.ps1` uses `Start-EstateServiceProcess`, including the per-service start mutex and owned-port checks. `Stop-Office.ps1` uses `Stop-EstateServiceProcess -AllOwnedInstances` for Office only; it does not call `Stop-All`, `Stop-EstateCore`, or `RestartAll`.

### Incident evidence and repair

Before this repair, OFFICE pointed to `A:\\AI\\Tools\\EstateStreamDeckMVP\\Core\\Start-Office.cmd`, which called the legacy `09-Start-Office.ps1` and the broad `Estate-Service-Control.ps1 -Action Office` controller. Static inspection of that controller shows that its `Office` branch calls its local `Start-Office` helper and does not explicitly call `Stop-All` or `RestartAll`; those operations are separate action branches. The retained Stream Deck diagnostics show long, overlapping governed-runtime status probes, including `READY`, `PORT_OCCUPIED`, and timeout samples, but do not contain a durable Office command-execution record proving that the Office branch killed Core. Therefore the exact historical Core teardown cannot be certified from retained evidence as direct Office process churn; the visible extended state changes were at least partly status/probe churn, and any unretained process churn is unproven.

The bounded repair removes the unsafe legacy seam from the OFFICE button: its start and long-press stop now target the repository-owned per-service wrappers above. This provides an idempotent Office-only mutex/ownership boundary and prevents a healthy Core/RGW/WEBUI service from being stopped merely because Office is being ensured. The canonical runtime source files had three captured shell-output lines at their beginnings; those lines were removed because they made the shared library unparsable when the new wrapper loaded it.

### Non-destructive validation performed

With Core/RGW/WEBUI healthy, the new Office start wrapper returned `already_running` without changing Office or any other service. A bounded Office-only stop/start test recorded these unaffected listener PIDs before and after:

- Ollama / Core, port 11434: PID `21520` before and after.
- Resident Gateway / RGW, port 11435: PID `42340` before and after.
- Open WebUI / WEBUI, port 8080: PID `30504` before and after.
- Office was stopped and then restarted independently; its new listener PID was `51120`.

After restart, `http://127.0.0.1:11435/v1/models`, `http://127.0.0.1:8765/`, and `http://127.0.0.1:8080/` all returned HTTP 200. The four key colors are computed from the exact `serviceIds` and governed status probe: green only when every owned target is healthy, yellow for partial/degraded state, and red when no owned target is healthy. OFFICE is not green merely because Core is healthy.

Do not use the old Office controller for future repairs. Before a physical test, verify the installed plugin contains the new `actions.js` path, then test the physical OFFICE press while recording listener PIDs. A successful physical acceptance still requires Pat to confirm that starting Office leaves healthy Core/RGW/WEBUI running and that the Office website refreshes.

## Backups and diagnostics

Back up the complete installed Stream Deck tree before direct modification. The established backup location is `C:\\Users\\wille\\AppData\\Roaming\\Elgato\\StreamDeck-Backups`. Preserve the Estate profile and unrelated profiles/plugins. Keep repository-side repair/configuration separate from machine-local generated state.

When diagnosing a button, prove the boundary in order: profile/page action binding; plugin launch and WebSocket registration; `willAppear`; `keyDown/keyUp`; gesture classification; absolute PowerShell executable; child process; wrapper output; status re-read; physical button/window result. Do not claim success from repository tests or a running process alone.

## Current ring snapshot and audit

The captured inventory records six physical profiles. At capture, the ring is intended to be:

- Windows Shutdown Menu XL
- Riverview
- Roku2
- WinToolsXL
- Estate Operations v0.5 Plugin
- Default Profile

Use the UUIDs and actual target edges in the inventory, not display names alone. Audit every active page for exactly one profile previous and one profile next where the profile follows the common navigation convention. Validate target existence, single-cycle traversal in both directions, inverse composition, and that PAGE LEFT/RIGHT remain page actions. If Pat manually moves a button, re-inventory before repair.

## Freshness rule

The installed configuration is authoritative because Pat manually changed button placement. This document and the machine-readable inventory are evidence captured on 2026-08-24T10:09:49-04:00; they must not be treated as live truth after subsequent manual editing.
