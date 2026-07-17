# Estate Stream Deck Monitor Control Page Specification

Status: implementation specification
Date: 2026-07-16
Classification: Estate Internal
Requested by: Pat / Steward

## 1. Purpose

Define a dedicated 8-column by 4-row Stream Deck page for moving, swapping, focusing, and parking Windows application windows across the Steward's four-monitor Command Chair workstation.

This page extends the existing Estate Stream Deck plugin and the existing `tools/operator-deck/OperatorDeck.ahk` window-control prototype. It must not become a separate unrelated plugin.

## 2. Physical Page Model

The Stream Deck provides a 32-key page arranged as eight columns by four rows.

The monitor-control page is divided into four 4-column by 2-row quadrants. Each quadrant represents one physical monitor in the same relative arrangement as Windows Display Settings.

```text
+-------------------+-------------------+
| MONITOR UPPER LEFT| MONITOR UPPER RIGHT|
| 4 columns x 2 rows| 4 columns x 2 rows |
+-------------------+-------------------+
| MONITOR LOWER LEFT| MONITOR LOWER RIGHT|
| 4 columns x 2 rows| 4 columns x 2 rows |
+-------------------+-------------------+
```

Each monitor therefore owns eight physical keys. The keys are not permanently limited to eight window destinations. Their rendered meaning changes with the selected layout mode.

## 3. Layout Modes

The page shall support named layout modes. A layout mode determines which destination zones are displayed inside each monitor quadrant.

### 3.1 FREE-3 portrait mode

This is the initial priority mode for Pat's eyesight and current working style.

Each monitor is represented by three approximately equal vertical zones:

```text
LEFT | CENTER | RIGHT
```

Only three destination keys need to be visually active for that monitor. The remaining keys in the quadrant may provide monitor-level commands, mode selection, paging, or blank visual spacing.

### 3.2 FULL mode

One destination represents the full usable work area of the monitor.

### 3.3 HALF mode

Two destinations:

```text
LEFT HALF | RIGHT HALF
```

### 3.4 QUAD mode

Four destinations:

```text
TOP LEFT | TOP RIGHT
BOTTOM LEFT | BOTTOM RIGHT
```

### 3.5 EIGHT mode

Eight destination zones map one-to-one to the eight keys allocated to the monitor. This mode is available for dense parking or specialized workflows but is not the default.

## 4. Selection Model

The interaction must work with only the Stream Deck and mouse available at the Command Chair.

The plugin shall maintain a short-lived `selected window` context.

A selected window may be established by either:

1. the current foreground Windows window when a destination is pressed; or
2. a future explicit window-selection action supplied by the Estate plugin.

Version 1 uses the foreground window as the source unless a selected-window context is already active.

## 5. Required Key Gestures

The existing Estate Stream Deck gesture vocabulary should be reused where practical, but monitor movement has different semantics from service start/stop actions.

For a destination-zone key:

| Gesture | Required behavior |
|---|---|
| Single tap | Move the foreground or selected window to this zone and activate it. |
| Double tap | Swap the foreground or selected window with the principal window currently occupying this zone. If no qualifying occupant exists, perform the single-tap move. |
| Long press, approximately 1.25 seconds | Move all windows belonging to the selected application's process or configured application group to this monitor, preserving relative order where practical. |

For a monitor-level key:

| Gesture | Required behavior |
|---|---|
| Single tap | Move the foreground or selected window to the monitor's primary zone or full work area. |
| Double tap | Bring the most recently used window on that monitor to the foreground. |
| Long press | Gather all currently visible windows onto that monitor using the active layout mode. This destructive-looking operation must require a clear visual label and may require a confirmation option in settings. |

The implementation shall not overload long press with deletion, closure, or process termination.

## 6. Plugin Action Family

Add monitor-control actions to the existing Estate Stream Deck plugin. Suggested stable UUID family:

```text
com.estate.statusbridge.window.move-zone
com.estate.statusbridge.window.swap-zone
com.estate.statusbridge.window.monitor-command
com.estate.statusbridge.window.layout-mode
com.estate.statusbridge.window.restore-workspace
```

Exact UUIDs may differ if existing conventions require it, but they must remain stable once released.

### 6.1 Move Zone action settings

Each placed action instance shall store:

```json
{
  "monitorId": "monitor-1",
  "zoneId": "free3-left",
  "layoutMode": "free3",
  "singlePressAction": "move",
  "doublePressAction": "swap",
  "longPressAction": "move-application-group"
}
```

### 6.2 Monitor Command action settings

```json
{
  "monitorId": "monitor-1",
  "singlePressAction": "move-to-primary-zone",
  "doublePressAction": "focus-last-window",
  "longPressAction": "gather-visible-windows"
}
```

### 6.3 Layout Mode action settings

```json
{
  "mode": "free3"
}
```

Supported initial mode identifiers:

```text
full
half
free3
quad
eight
```

## 7. Runtime Boundary

The Stream Deck plugin is the gesture, rendering, configuration, and feedback layer.

The Windows adapter is the authority for:

- monitor discovery;
- virtual-desktop coordinates;
- DPI-aware work areas;
- foreground-window resolution;
- window matching;
- moving and resizing;
- occupant discovery;
- swapping rectangles;
- application grouping;
- workspace capture and restoration.

The plugin must invoke a stable local command interface rather than embedding Windows window-management logic directly into Stream Deck JavaScript.

Suggested command surface:

```text
EstateWindowControl.exe move-zone --monitor monitor-1 --layout free3 --zone left
EstateWindowControl.exe swap-zone --monitor monitor-1 --layout free3 --zone center
EstateWindowControl.exe move-app-group --monitor monitor-2 --layout free3
EstateWindowControl.exe gather --monitor monitor-3 --layout free3
EstateWindowControl.exe set-layout --layout free3
EstateWindowControl.exe restore-workspace --name Codex
```

AutoHotkey v2 may remain the first adapter implementation, but the command contract must not depend on Stream Deck profile internals.

## 8. Monitor Identity

Do not bind profiles only to transient monitor numbers such as `1`, `2`, `3`, and `4`.

The inventory layer shall record, when available:

- Windows display device name;
- monitor hardware identifier;
- monitor friendly name;
- current rectangle;
- work-area rectangle;
- orientation;
- DPI scaling;
- relative position;
- primary flag.

The local configuration shall map durable Estate aliases to discovered monitors:

```text
UPPER_LEFT
UPPER_RIGHT
LOWER_LEFT
LOWER_RIGHT
```

If hardware identifiers change, the adapter should attempt a geometry-based match and report that remapping needs review.

## 9. Visual Feedback

Each destination key should communicate:

- monitor quadrant through placement;
- zone shape through the icon;
- active layout mode;
- whether a window occupies the zone;
- selected-window state when applicable;
- success or failure after an action.

Minimum feedback states:

```text
idle
occupied
selected
moving
success
error
unavailable-monitor
```

Titles should be minimal because the zone geometry itself should carry most of the meaning.

## 10. Profile Generation

The implementation shall generate or update a dedicated Estate Stream Deck page rather than requiring manual creation of 32 independent actions.

The generator must:

1. discover the target 8x4 device/profile format from the current local inventory exports;
2. preserve unrelated profiles and pages;
3. preserve existing action UUIDs;
4. create one monitor-control page with four physical monitor quadrants;
5. default the page to `FREE-3` mode;
6. install icons and action settings;
7. create a backup before modifying Stream Deck profile data;
8. restart Stream Deck only when required;
9. validate all generated actions after installation.

## 11. Acceptance Scenarios

The implementation is accepted when Pat can perform all of the following using the Stream Deck and mouse:

1. Click a VS Code window with the mouse, then tap the center-zone key for another monitor and see VS Code moved and sized correctly.
2. Double tap a destination occupied by ChatGPT and see VS Code and ChatGPT exchange locations.
3. Long press a monitor destination and move the configured application group to that monitor.
4. Switch between `FREE-3`, `FULL`, `HALF`, and `QUAD` without editing files.
5. Use the page after a reboot without manually recalculating coordinates.
6. Receive a visible error state if a configured monitor is absent.
7. Return to other Estate Stream Deck pages and profiles without damage or lost actions.

## 12. Initial Scope Boundary

Version 1 shall not:

- close applications;
- terminate processes;
- move windows between Windows virtual desktops unless explicitly added later;
- depend on cloud APIs;
- require keyboard interaction for normal use;
- rewrite unrelated Stream Deck profiles;
- assume all four monitors have identical orientation, resolution, or scaling.

## 13. Relationship to Workstation Profiles

This monitor page is the manual spatial-control surface.

Named workspaces such as `CODEX`, `VS CODE`, `ESTATE`, and `COMFYUI` remain a complementary layer. A workspace action may launch and restore many windows at once, while this monitor page allows Pat to make immediate corrections and rearrangements without leaving the chair environment.
