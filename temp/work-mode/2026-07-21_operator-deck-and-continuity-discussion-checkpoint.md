# Temporary Work Mode Discussion Checkpoint — Operator Deck and Continuity

Date: 2026-07-21  
Status: Temporary discussion checkpoint  
Classification: Estate Internal  
Canonical: No  
Implementation authority: None  
Promotion authority: None

## Purpose

Preserve the conclusions, evidence, constraints, and open questions developed during a ChatGPT Work mode discussion so later work can resume without depending on the conversation context window.

This file is a save point only. It does not amend a work package, authorize implementation, promote recovered material, or supersede repository evidence.

## 1. Work Mode, ChatGPT, and Codex

The discussion distinguished three operating surfaces:

- Standard ChatGPT is primarily conversational and is useful for architectural reasoning, canon development, drafting, and interactive exploration.
- ChatGPT Work mode is an agentic managed workspace that can inspect supplied files, use approved tools, run multi-step assignments, create artifacts, and continue toward an outcome within an active turn.
- Codex is optimized for sustained software-engineering work against a codebase, especially when local repository access, builds, tests, and Git operations are required.

Work mode and Codex share usage limits/credits. Work mode does not currently expose a direct dispatcher that can launch a separate Codex task, monitor it, and submit the next dependent assignment automatically.

The Codex CLI is capable locally but has proved materially more expensive in the Steward's actual usage than cloud work. Therefore recurring deterministic Estate processes should not invoke Codex CLI unnecessarily.

## 2. Continuity, Renewal, Reflection, and Ingestion

The Steward operates three long-running architect conversations. Context-window exhaustion is mitigated through:

- renewal packages that capture current assignment, state, decisions, lessons, blockers, artifacts, and next actions;
- reflection packages that load critical prior lessons and current state into the successor architect;
- periodic restart based on time, latency, or observed context degradation.

The proposed ingestion engine remains a strong concept, but it should be understood as a local continuity and artifact-ingestion system rather than only an MHTML parser.

Recommended division:

1. Architect chats produce explicit marked artifact blocks.
2. A local deterministic engine ingests them.
3. The engine writes review-only artifacts, manifests, hashes, diagnostics, and continuity records.
4. Reflection packages are assembled from accepted renewal state and selected durable lessons.
5. GitHub is excluded from the critical persistence path.
6. Repository placement and publication occur only through a separate explicitly approved process.

Future marked blocks should use stable textual identifiers such as:

```text
*************** ESTATE-BLOCK START ***************
SCHEMA: estate-block/v1
ARCHITECT: chief
TYPE: runtime-canon
WORK-PACKAGE: WP-5003
TARGET: supporting/runtime_canons/WP-5003.md
DISPOSITION: REVIEW-ONLY

[body]

!!!!!!!!!!!!!!! ESTATE-BLOCK END !!!!!!!!!!!!!!!
WORK-PACKAGE: WP-5003
```

The parser should rely on `ESTATE-BLOCK START` and `ESTATE-BLOCK END`, not an exact punctuation count.

Plain UTF-8 text or Markdown should be preferred for deterministic future captures. MHTML remains valuable as supporting evidence and a forensic fallback.

## 3. MHTML Recovery Evidence

The uploaded recovery archive was inspected directly. The five authoritative MHTML files contain:

- 102 rendered messages;
- 25 assistant messages;
- seven HTML MIME representations;
- complete WP-4111 and WP-4112 canon bodies in `tab4.mhtml`.

Known calibration messages:

- WP-4111: `bb605e81-9828-4e36-a536-eb0339053adb`
- WP-4112: `6a46eb57-8e36-474a-ae7e-05a7be6e5b90`

Both have plain, non-Markdown titles, substantive bodies, and matching explicit closing sentences.

A structural extractor failed because it incremented message-capture depth for arbitrary HTML start tags, including void elements that do not produce matching end callbacks. It therefore swallowed later role-bearing messages. A second defect required Markdown `#` headings and rejected the preserved plain headings.

For WP-4116 through WP-4126, the supplied five MHTML files preserve assignment, scope, title, sequence, and status references, but not the substantive canon bodies. This does not prove that the canons were never written. It means their bodies are not recoverable from the supplied MHTML bytes. Browser-page virtualization is the likely explanation: a saved MHTML preserves materialized rendered DOM, not necessarily the entire server-side conversation history.

## 4. Repository Projects Reviewed

Two related efforts were identified.

### 4.1 Operator Deck / Window Swapper

Authoritative named work package:

`collaboration/work_packages/pending/WP-Operator-Deck-Prototype.md`

Existing repository implementation:

- `tools/operator-deck/OperatorDeck.ahk`
- `tools/operator-deck/config.example.ini`
- `tools/operator-deck/README.md`

The AutoHotkey v2 prototype already supports:

- activate an existing target;
- launch a missing target;
- move the active window to a configured slot;
- swap active and target window rectangles;
- externally callable commands;
- configurable targets and static monitor-slot rectangles.

The remaining work is primarily workstation-specific calibration, reliable target matching, diagnostics, acceptance testing, and preparation for multiple physical control adapters.

### 4.2 Estate Stream Deck Plugin

Relevant pending work packages include:

- WP-0548 — Estate Stream Deck Status Bridge — Local CLI Build
- WP-0549 — Estate Stream Deck Control Actions and Profile Generator
- WP-0550 — Stream Deck Register All Control Actions

Repository evidence reports:

- installed plugin version 0.2.0;
- 17 manifest/profile action UUIDs;
- unresolved profile actions reporting `Unable to identify plugin`;
- a likely runtime defect where `plugin.js` registers only the original six actions instead of the complete `ACTION_LIST`.

The expected plugin source paths were not available through the inspected GitHub revision. Authoritative local state likely exists under:

- `A:\AI\Tools\EstateStreamDeckPlugin`
- `%APPDATA%\Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin`

The local build source, installed source, generated profile, logs, and repository source must be reconciled before that project resumes.

## 5. Relationship Between Operator Deck and Stream Deck

These are not independent projects.

- Operator Deck is the device-neutral window and workspace control engine.
- Stream Deck is one physical input/output adapter and profile surface.
- Additional macro controllers, the gaming mouse, keyboard shortcuts, command-line calls, and possible future spatial interfaces are other adapters.

The Stream Deck should not contain authoritative window-management logic. It should invoke logical actions and display state.

## 6. Four-Monitor and 32-Key Model

The Steward uses four 55-inch 4K monitors. A default quadrant model provides sixteen operational slots:

- M1-TL, M1-TR, M1-BL, M1-BR
- M2-TL, M2-TR, M2-BL, M2-BR
- M3-TL, M3-TR, M3-BL, M3-BR
- M4-TL, M4-TR, M4-BL, M4-BR

Slot geometry must use the Windows monitor work area rather than assuming the full 3840×2160 bounds. It must account for:

- taskbar reservation and position;
- auto-hide behavior;
- display scaling/DPI;
- negative virtual desktop coordinates;
- monitor identity;
- reserved margins;
- app, normal, full-screen, or kiosk presentation modes.

A candidate Stream Deck interaction:

1. Press an occupied slot to select its window.
2. Display selected state visibly.
3. Press a destination slot.
4. Swap if occupied or move if empty.
5. Clear selection.
6. Provide cancel and one-level undo.

Saved layouts may later represent active environments such as Estate development, architect conversations, Codex review, ComfyUI rendering, and Stream Deck engineering.

## 7. Logical Action and Adapter Direction

Operator Deck should expose device-neutral logical actions such as:

- `window.focus`
- `window.select`
- `window.move`
- `window.swap`
- `window.place_target`
- `layout.capture`
- `layout.apply`
- `layout.undo`
- `mode.select`
- `notification.acknowledge`
- `dictation.toggle`
- `capture.region`
- `capture.record_region`
- `clipboard.copy`
- `clipboard.paste`
- `clipboard.history`

Input adapters may include:

- Stream Deck;
- Redragon gaming mouse;
- Koolertron macro controller;
- AI-KSEN controller;
- keyboard hotkeys;
- command line;
- test simulator;
- future voice or Quest/AR/VR adapter.

Output adapters may include:

- Stream Deck icons and state borders;
- LEDs and RGB;
- AI-KSEN LCD;
- desktop notifications;
- CLI JSON;
- future spatial overlays.

AR/VR/Quest support is not presently specified in the repository. Only extension hooks should be preserved now. No Quest implementation should be inferred or started without a later concrete workflow.

## 8. Command Chair Hardware

Repository evidence identifies:

- Koolertron 9-key mechanical controller with two programmable knobs and LED backlighting;
- AI-KSEN 3-key controller with encoder, LCD, and RGB;
- Redragon gaming mouse with approximately 12–16 programmable buttons;
- Stream Deck with 32 keys.

The physical devices have different capabilities and must not be forced into one gesture model.

### Stream Deck

Preserve:

- single press;
- double press;
- configurable long press, currently approximately three to four seconds;
- long-release suppression;
- dynamic status display.

Canonical service-control pattern:

- single: start service;
- double: start service and open its interface;
- long: stop service and close its associated interface.

### Gaming mouse

The Redragon mouse currently supplies single-click programmable actions only.

Voice Typing and Snipping Tool are mapped to physically adjacent mouse buttons and are frequently confused. They should be reassigned to physically separated buttons after the complete current mouse mapping is inventoried. Existing muscle memory should be preserved wherever practical.

The mouse can initiate dictation or capture while another device displays state.

### Rotary controls

Model:

- encoder delta positive;
- encoder delta negative;
- encoder press;
- optional long press only if the hardware and adapter reliably support it.

Meanings should be mode-dependent rather than hardwired globally.

## 9. Browser Presentation

Dedicated Estate web surfaces should normally use a browser application/PWA-style window rather than a true locked-down kiosk.

Desired launch modes:

- normal;
- app;
- full-screen;
- kiosk;
- existing-window.

Application mode removes tabs, address bar, bookmarks, and most browser chrome while preserving a manageable window with normal minimize, maximize, close, and quadrant placement.

True kiosk mode should be reserved for genuinely dedicated surfaces because it may conflict with multi-window quadrant management.

## 10. Stream Deck State Presentation

Existing Stream Deck status bars should be retained but corrected.

A progress bar should not imply measured progress when the underlying state is categorical. Preferred service states:

- OFF
- STARTING
- ONLINE
- ONLINE_WITH_INTERFACE
- STOPPING
- ERROR
- UNKNOWN

Possible visual language:

- gray: off or unknown;
- pulsing/animated: transitional;
- green: online;
- blue: online with interface open;
- amber: stopping or review;
- red: error;
- border/ring: selected window slot.

## 11. Windows Voice Typing Friction

Windows Voice Typing is invoked with `Win+H`. Its floating toolbar does not have a documented supported pin-to-coordinate setting.

Recommended near-term experiment:

1. Separate Voice Typing and Snipping Tool buttons physically on the Redragon mouse.
2. Build a local Voice Typing status probe.
3. Detect toolbar presence.
4. Prefer UI Automation inspection to distinguish ready, listening, stopped, and error states if the exact Windows build exposes reliable accessibility state.
5. Display dictation state on a Stream Deck key, LED/LCD surface, or fixed desktop indicator.
6. Test toolbar repositioning as an optional workaround, not as the authoritative status mechanism.

An optimistic toggle bit is insufficient because state can drift when Windows refuses to start, focus is not in a text field, the microphone fails, or the toolbar is closed elsewhere.

## 12. Recommended Starting Sequence

The preferred first active project remains Operator Deck, but the first step is not an immediate rewrite of the AutoHotkey file.

Recommended sequence:

1. Preserve this checkpoint.
2. Inventory the actual four-monitor topology and scaling.
3. Inventory current application windows and launch methods.
4. Inventory all Stream Deck profiles and gesture bindings.
5. Inventory the full Redragon mouse mapping and model/software version.
6. Inspect the arrived Koolertron and AI-KSEN hardware and configuration capabilities.
7. Define logical action and state-event schemas.
8. Build the Voice Typing state probe as a small high-value first slice.
9. Calibrate the sixteen-slot monitor model.
10. Add diagnostics, state output, and test hooks to Operator Deck.
11. Implement and validate focus, move, swap, place, cancel, and undo.
12. Build the Stream Deck window-control profile against the stable command/state contract.
13. Add macro-controller adapters only according to physically verified capabilities.
14. Reconcile the separate Stream Deck plugin source/build/install states before resuming WP-0550.
15. Preserve Quest/AR/VR adapter hooks without implementing an undefined headset workflow.

## 13. Constraints

- Do not redesign the Estate globally.
- Do not modify pending work-package definitions during exploratory implementation.
- Do not couple Estate logic directly to one hardware vendor.
- Do not assume all devices support single/double/long gestures.
- Do not fabricate device capabilities.
- Do not claim local installation or validation without local evidence.
- Do not make GitHub the critical runtime persistence path.
- Do not automatically promote recovered conversation artifacts.
- Keep local deterministic processing free of recurring model-token costs wherever possible.

## 14. Resume Point

On resumption:

1. Read this checkpoint.
2. Re-read the current Operator Deck, Stream Deck, and Command Chair repository artifacts.
3. Confirm whether the Steward wants planning/inventory only or authorizes implementation.
4. Request or obtain the local hardware/software inventory required for the selected first slice.
5. Preserve evidence and report observed state before changing implementation.
