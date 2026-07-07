# Work Package: Operator Deck Prototype

Status: open
Classification: Estate Internal
Owner: Alfred / Chief of Staff
Requested by: Pat / Steward
Intended worker: Codex
Priority: Near-term prototype

## Mission

Build the first working prototype of the Estate Operator Deck local Windows adapter.

The prototype shall be an AutoHotkey v2 script that can be triggered by an Elgato Stream Deck, keyboard shortcut, or command-line call to activate, launch, move, or swap predefined Windows application targets.

This is not the full Estate Control Fabric. This is a narrow, reliable Windows window-control adapter that proves the target-launcher/window-swapper concept.

## Required Reading

Before implementation, read:

1. `AI_START_HERE.md`
2. `AI_HINTS.md`
3. `docs/collaboration/Estate_Collaboration_Layer_v1.md`

Relevant collaboration-layer guidance:

- GitHub is the first shared transport adapter, not the Communication Bus itself.
- Work packages should include mission, scope, do-not-touch boundaries, required reading, deliverables, acceptance criteria, and definition of done.
- Do not redesign the Estate.
- Do not create new offices or departments for this task.

## Scope

Create a small AutoHotkey v2-based prototype under:

```text
tools/operator-deck/
```

The prototype manages named targets.

A target is an operator-facing thing the Steward wants to bring forward, such as:

```text
PowerShell
ChatGPT-1
ChatGPT-2
VSCode
ComfyUI
GitHub
Codex
```

Each target should define:

```text
name
window match rule
optional launch command
preferred slot
behavior
```

## Required Behaviors

### 1. activate_or_launch

If the target window exists:

```text
bring it to foreground
move/resize it to the configured slot
activate it
```

If the target window does not exist:

```text
run the launch command
wait for the matching window to appear
move/resize it to the configured slot
activate it
```

### 2. swap

When called against a target:

```text
identify the currently active window
identify the target window
record both window rectangles
move the active window into the target window's previous rectangle
move the target window into the active window's previous rectangle
activate the target window
```

### 3. move_active

Move the currently active window to a named configured slot.

### 4. activate

Activate an existing target window without launching if missing.

## Command Interface

Support command-line style calls similar to:

```text
OperatorDeck.ahk target PowerShell
OperatorDeck.ahk target ChatGPT-1
OperatorDeck.ahk swap ChatGPT-2
OperatorDeck.ahk move-active PARK_1
OperatorDeck.ahk activate VSCode
```

This interface is required so Stream Deck buttons can call the script using an Open/System Command action without requiring a custom Stream Deck plugin.

## Configuration

Slot coordinates must be configurable.

Example slots:

```text
MAIN_WORK
PARK_1
PARK_2
PARK_3
PARK_4
```

Targets must be configurable.

Example target:

```text
PowerShell
match: ahk_exe pwsh.exe
launch: pwsh.exe
slot: MAIN_WORK
behavior: activate_or_launch
```

Example target:

```text
ChatGPT-1
match: window title or Chrome app/window identifier
launch: optional
slot: PARK_1
behavior: swap
```

Prefer a simple INI configuration file for v1 unless JSON parsing is clearly simpler and more reliable in AutoHotkey v2.

## Deliverables

Create:

```text
tools/operator-deck/OperatorDeck.ahk
tools/operator-deck/config.example.ini
tools/operator-deck/README.md
```

## README Requirements

The README must include:

```text
AutoHotkey v2 installation note
how to configure slots
how to configure targets
example Stream Deck command usage
example commands
known limitations
future expansion notes
```

## Do-Not-Touch Boundaries

Do not modify:

```text
docs/governance/
archive/
constitutional documents
existing collaboration-layer architecture
unrelated tools or services
```

Do not implement these future phases in this work package:

```text
HDMI matrix network API adapter
KVM hotkey adapter
workspace profiles
EstateBus integration
MPT/GCC service integration
dynamic Stream Deck icons
Linux control-node version
native Stream Deck plugin
GUI configuration editor
```

Do not rename or redesign Estate collaboration structures.

Do not use Q-Mastery GCC terminology in implementation or documentation for this Estate work package.

## Acceptance Criteria

The prototype is successful when:

```text
1. A command can bring PowerShell to the main work area.
2. A command can launch PowerShell if missing.
3. A command can swap the active window with a configured Chrome/ChatGPT window.
4. A command can move the active window to a configured slot.
5. Slot coordinates are configurable.
6. Targets are configurable.
7. Commands can be called externally by Stream Deck using an Open/System Command action.
8. The implementation is narrow, readable, and does not overbuild beyond the prototype.
```

## Definition of Done

This work package is done when:

```text
- all deliverables exist under tools/operator-deck/
- README documents practical usage
- example config is sufficient for Pat to adapt to a four-monitor Windows layout
- no out-of-scope integrations are implemented
- the change is ready for review in a pull request
```

## Final Instruction

Implement only the prototype described here. Prefer correctness, simplicity, and operational usefulness over architectural expansion.
