# Estate Operator Deck Prototype

This folder contains the first narrow prototype of the Estate Operator Deck local Windows adapter. It is an AutoHotkey v2 script intended to be called by an Elgato Stream Deck Open/System Command action, a keyboard shortcut, or a direct command-line call.

The prototype manages named Windows application targets. It can activate an existing window, launch a missing window, move windows into configured slots, and swap the active window with a configured target window.

## Install AutoHotkey v2

Install AutoHotkey v2 from the official AutoHotkey site. This script uses v2 syntax and starts with `#Requires AutoHotkey v2.0`; it will not run correctly on AutoHotkey v1.

After installation, `.ahk` files can normally be run directly from Explorer, PowerShell, Windows Terminal, or a Stream Deck Open/System Command action.

## Configuration file

1. Copy `config.example.ini` to `config.ini` in this same folder.
2. Edit `config.ini` for the local Windows workstation.
3. Leave `config.example.ini` in place as a reference template.

If `config.ini` does not exist, `OperatorDeck.ahk` falls back to `config.example.ini` so the prototype remains inspectable and runnable for review.

## Configure slots

Slots live in the `[Slots]` section. Each slot uses this format:

```ini
SLOT_NAME=x,y,width,height
```

Example:

```ini
MAIN_WORK=0,0,1920,1080
PARK_1=1920,0,1280,720
PARK_2=1920,720,1280,720
PARK_3=-1280,0,1280,720
PARK_4=-1280,720,1280,720
```

Notes:

- Coordinates are Windows virtual desktop coordinates.
- Negative `x` or `y` values are valid when a monitor sits left of or above the primary monitor.
- Use AutoHotkey Window Spy, Windows display settings, or PowerToys FancyZones to identify useful rectangles.
- A four-monitor layout can be represented by adding or adjusting named slots; no script changes are required.

## Configure targets

Targets live in sections named `[Target:<name>]`. Each target should define:

```ini
[Target:PowerShell]
match=ahk_exe pwsh.exe
launch=pwsh.exe
slot=MAIN_WORK
behavior=activate_or_launch
```

Fields:

- `match`: AutoHotkey window match rule, such as `ahk_exe pwsh.exe`, `ChatGPT ahk_exe chrome.exe`, or another title/executable/class rule.
- `launch`: Optional command or URL to run when the target is missing.
- `slot`: Named slot where `target` commands place the window.
- `behavior`: Documentation for the intended target behavior. The command line chooses the action for this prototype.

Chrome, ChatGPT, and PWA windows may need specific titles, Chrome app identifiers, or profile-specific launch commands on Pat's workstation. Adjust `match` and `launch` until Window Spy and `OperatorDeck.ahk activate <name>` identify the intended window reliably.

## Commands

Run commands from this folder or call the script by full path:

```powershell
.\OperatorDeck.ahk target PowerShell
.\OperatorDeck.ahk target ChatGPT-1
.\OperatorDeck.ahk swap ChatGPT-2
.\OperatorDeck.ahk move-active PARK_1
.\OperatorDeck.ahk activate VSCode
.\OperatorDeck.ahk dictation-toggle
```

Command behavior:

- `target <TargetName>`: If the target window exists, bring it forward, move it to the configured slot, and activate it. If missing, run `launch`, wait for the matching window, move it, and activate it.
- `swap <TargetName>`: Swap the currently active window rectangle with the target window rectangle, then activate the target.
- `move-active <SlotName>`: Move the currently active window to a configured slot.
- `activate <TargetName>`: Activate an existing target window without launching if it is missing.
- `dictation-toggle`: Send Windows `Win+H` to toggle Voice Typing. This command is device-neutral at the CLI boundary and may be called by Stream Deck, a keyboard, the mouse software, or another adapter.

## Stream Deck usage

Use a Stream Deck **Open** or **System Command** action. Point it at AutoHotkey or the `.ahk` file and pass the command arguments.

Example command target:

```text
C:\Path\To\tools\operator-deck\OperatorDeck.ahk target PowerShell
```

Example buttons:

```text
C:\Path\To\tools\operator-deck\OperatorDeck.ahk target PowerShell
C:\Path\To\tools\operator-deck\OperatorDeck.ahk swap ChatGPT-2
C:\Path\To\tools\operator-deck\OperatorDeck.ahk move-active PARK_1
C:\Path\To\tools\operator-deck\OperatorDeck.ahk activate VSCode
```

If the Stream Deck action has separate fields for application and arguments, use the script path as the application and put `target PowerShell`, `swap ChatGPT-2`, or similar text in the arguments field.

## Known limitations

- Windows only.
- Requires AutoHotkey v2.
- Matching Chrome tabs, PWAs, and multiple ChatGPT windows can be fragile until workstation-specific match rules are tuned.
- The script does not manage workspace profiles, dynamic icons, KVMs, HDMI matrices, services, or network APIs.
- The prototype uses static configured rectangles and does not discover monitor layouts automatically.
- If a launched app opens slowly or restores a previous session with a different title, increase `DefaultWaitSeconds` or refine the target `match` rule.

## Future expansion notes

Future work may add richer target discovery, profile-aware commands, workspace profiles, service integration, dynamic Stream Deck feedback, or other adapters. Those are intentionally outside this prototype. This version stays focused on a readable local window-control adapter that proves the target launcher and window swapper concept.


## Device-neutral action and state contracts

The `contracts/` schemas define the small boundary between physical controls and Operator Deck capabilities. A Stream Deck, gaming mouse, keyboard, rotary control, command line, or later spatial adapter emits the same action request shape. Device-specific gesture handling stays in its adapter:

- Stream Deck controls may emit `single`, `double`, or `long`.
- The Redragon mouse currently emits `single` only.
- A long-press adapter must suppress the release click so shutdown-style actions do not also trigger the single-click action.
- State observations use `off`, `ready`, `listening`, `error`, or `unknown`, with an explicit confidence and evidence list.

These contracts are an interface seam, not a new service or native Stream Deck plugin. The existing AutoHotkey commands remain unchanged.

## Voice Typing surface calibration

`Inspect-VoiceTypingSurface.ps1` is a read-only Windows diagnostic. It inventories visible candidate windows and their top-level UI Automation names, writes a JSON state observation, prints it, and copies it to the clipboard. It does not move the Voice Typing toolbar, press `Win+H`, or claim a reliable listening state without observable evidence.

Run it while Voice Typing is off, ready, and actively listening so the three reports can be compared:

```powershell
CLS
Set-Location A:\theestate\tools\operator-deck
.\Inspect-VoiceTypingSurface.ps1
```

The default report path is `tools/operator-deck/runtime/voice-typing-surface.json`. That runtime output is workstation evidence and should remain local; do not commit it. Paste each clipboard report back for selector calibration. Until that calibration is complete, `unknown` and low-confidence results are expected and honest.


### Calibration result

Calibration on the Steward's Windows 11 workstation established this read-only signal:

- Package record: `MicrosoftWindows.Client.CBS_cw5n1h2txyewy`
- `LastUsedTimeStart > 0` and `LastUsedTimeStop = 0`: `listening`, high confidence.
- A nonzero `LastUsedTimeStop`: `off`, high confidence.
- Other active microphone records, including long-lived `svchost.exe` entries, are excluded.

The paired listening/off observations were confirmed on 2026-07-21. Raw workstation reports remain local-only. The current contract intentionally treats an idle-but-visible toolbar as `off`; a distinct `ready` state requires a separate supported signal.


## Voice Typing status publisher

After calibration, use `Get-VoiceTypingStatus.ps1` for normal operation. It reads only the calibrated CBS microphone record and atomically publishes `runtime/voice-typing-status.json`. The calibration inspector is not required during routine use.

One-shot status:

```powershell
CLS
Set-Location A:\theestate\tools\operator-deck
.\Get-VoiceTypingStatus.ps1
```

Continuous publication, sampled twice per second until `Ctrl+C`:

```powershell
CLS
Set-Location A:\theestate\tools\operator-deck
.\Get-VoiceTypingStatus.ps1 -Watch -IntervalMilliseconds 500
```

Adapters should read the published JSON and render its `state` rather than reimplementing Windows detection. Suggested presentation is red or unlit for `off`, green or pulsing for `listening`, and amber for `unknown` or an execution error. The publisher writes only on-machine runtime state; it does not press `Win+H`, move the toolbar, or control dictation.


### Continuous validation

Continuous polling was validated on 2026-07-21 with the visible Microsoft Voice Typing toolbar. The publisher observed `OFF -> LISTENING -> OFF`, with high confidence for every transition. No raw screenshot or workstation report is committed.


## Calibrated four-monitor layout

The example configuration now carries the workstation-validated 16-quadrant layout:

| Logical monitor | Windows device | Wall position | Work area |
|---|---|---|---|
| M1 | DISPLAY4 | upper left | 3840 × 2160 |
| M2 | DISPLAY1 | upper right | 3840 × 2160 |
| M3 | DISPLAY3 | lower left, primary | 3840 × 2076 after the 84-pixel taskbar |
| M4 | DISPLAY2 | lower right | 3840 × 2160 |

All monitors report 175% effective scaling. Slots use observed Windows virtual-desktop coordinates, including the small 5–6 pixel alignment offsets and negative upper-row coordinates. Existing `MAIN_WORK` and `PARK_*` names remain as compatibility aliases.

Before copying these slots into an existing local `config.ini`, preserve any locally tuned target matches and launch commands. The calibrated `config.example.ini` is review evidence; it does not automatically overwrite local configuration.


## Exact runtime window binding

The workstation inventory found multiple simultaneous Chrome windows with identical `ChatGPT - Google Chrome` titles and the same executable. Static AutoHotkey title rules cannot distinguish them. Bind a logical target to the currently active window instead:

```powershell
CLS
Set-Location A:\theestate\tools\operator-deck
.\OperatorDeck.ahk bind ChatGPT-1
.\OperatorDeck.ahk bind ChatGPT-2
```

A physical control can call `bind` without changing desktop focus. For keyboard testing from PowerShell, start a delay and click the intended window before it expires:

```powershell
CLS
Set-Location A:\theestate\tools\operator-deck
Start-Sleep -Seconds 5
.\OperatorDeck.ahk bind ChatGPT-1
```

Bindings live under ignored `runtime/window-bindings.ini`. A binding records the HWND, process name, title, and PID. Operator Deck validates that the handle still belongs to the recorded process before using it; stale bindings are deleted and normal configured matching resumes. Remove a binding with `OperatorDeck.ahk unbind <TargetName>`.

Bound minimized windows are restored before activation or swapping, preventing the synthetic `-32000,-32000` minimized rectangle from corrupting placement.


## Bound target placement

Use `place <TargetName> <SlotName>` to put an exact bound window into any calibrated quadrant:

```powershell
CLS
Set-Location A:\theestate\tools\operator-deck
.\OperatorDeck.ahk place ChatGPT-1 M1_TOP_LEFT
.\OperatorDeck.ahk place ChatGPT-2 M4_BOTTOM_RIGHT
```

This separates window identity from destination. A control surface can therefore devote one group of buttons to logical windows and another group to the 16 monitor quadrants. The adapter restores a minimized target, places it using the selected work-area rectangle, and activates it. `activate` intentionally restores the window's prior normal rectangle without assigning a quadrant; use `place` when deterministic geometry is required.


## Two-step control-surface placement

Operator Deck can hold one temporary window selection between physical button presses.

Select a configured/bound target:

```text
OperatorDeck.ahk select ChatGPT-1
```

Or select whichever window is active without requiring a configured target:

```text
OperatorDeck.ahk select-active
```

Then place that selection with a quadrant button:

```text
OperatorDeck.ahk place-selected M4_BOTTOM_RIGHT
```

The temporary selection stores HWND, PID, title, and process under ignored runtime state. It is validated before use and cleared after successful placement, after an invalid-window failure, or by `clear-selection`. A 32-key surface can therefore reserve controls for window/target selection and controls for destination quadrants without encoding every source/destination combination.


## Context-sensitive quadrant buttons

Map each of the 16 quadrant controls to `slot <SlotName>`. The same command changes behavior according to selection state:

1. With no selection, it selects the visible non-minimized window having the greatest overlap with that quadrant.
2. With a valid selection, it moves the selected window into the pressed quadrant and clears selection.

Example two-button sequence:

```text
OperatorDeck.ahk slot M3_TOP_LEFT
OperatorDeck.ahk slot M2_BOTTOM_RIGHT
```

The first press selects the principal window in the primary monitor's upper-left quadrant. The second moves it to the upper-right monitor's lower-right quadrant. Named-target selection remains available for minimized windows and ambiguous overlapping layouts.


## Movement undo

`OperatorDeck.ahk undo` restores the rectangle of every window affected by the most recent move or swap. Single-window placement records one window; swap records both windows as one transaction. Undo validates each HWND and PID before changing anything and fails closed if a recorded window is stale. The record is cleared after successful restoration, so this prototype intentionally provides one-step undo.
