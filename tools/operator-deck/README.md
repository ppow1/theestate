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
```

Command behavior:

- `target <TargetName>`: If the target window exists, bring it forward, move it to the configured slot, and activate it. If missing, run `launch`, wait for the matching window, move it, and activate it.
- `swap <TargetName>`: Swap the currently active window rectangle with the target window rectangle, then activate the target.
- `move-active <SlotName>`: Move the currently active window to a configured slot.
- `activate <TargetName>`: Activate an existing target window without launching if it is missing.

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
