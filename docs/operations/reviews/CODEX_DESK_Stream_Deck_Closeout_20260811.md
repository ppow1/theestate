# Codex Desk / Stream Deck Workspace Closeout

**Date:** 2026-08-11  
**Status:** Physically accepted and closed  
**Scope:** Operator Deck CODEX DESK control, C1/C2/C3 interactive Codex seats, C1/C2/C3 automation Chromium surfaces, C1/C2/C3 interactive ChatGPT Chrome surfaces, gesture dispatch, shutdown/reuse behavior, seat verification, and physical window geometry.

## Executive Summary

The Codex Desk effort began as a small Operator Deck convenience: one control that could bring up three Codex seats in a predictable place. It evolved into a 3x3 operational workspace with three distinct roles per seat:

- **Top 25%:** C1/C2/C3 interactive Codex terminals.
- **Middle 25%:** C1/C2/C3 isolated Chromium automation surfaces intended for future Playwright-driven ChatGPT reasoning interactions.
- **Bottom 50%:** C1/C2/C3 interactive Chrome app-mode ChatGPT windows.

The final Stream Deck contract is:

- **1 press:** top Codex row only.
- **2 presses:** middle Chromium row only.
- **3 presses:** bottom interactive ChatGPT row only.
- **4 presses:** all nine windows.
- **Long press:** cleanly shut down the complete managed Codex Desk.

Final physical acceptance was performed by Patricia after the last geometry correction. All requested windows loaded, all windows closed, and the windows were in the correct locations. Repeated invocation behaved correctly enough to close this effort and move on to the next integration task.

The implementation required substantially more iteration than expected because three independent classes of state were interacting:

1. Stream Deck action-registration and gesture dispatch;
2. browser/terminal lifecycle and identity;
3. Windows DPI/monitor coordinate systems.

The most important lesson is that **numeric window geometry was repeatedly internally consistent while physically wrong**. Final acceptance required an independent screenshot from Patricia's normal screen-capture workflow rather than a screenshot generated from the same coordinate assumptions used by the placement code.

---

## Final Accepted Design

### Seat columns

The logical columns are C1, C2, and C3. Each column carries a consistent operator meaning across all three rows.

### Top row — interactive Codex

Each seat launches an independent Codex session with its own `CODEX_HOME`:

- C1 -> `A:\AI\CodexProfiles\C1`
- C2 -> `A:\AI\CodexProfiles\C2`
- C3 -> `A:\AI\CodexProfiles\C3`

The interactive launch contract is explicit and does not rely on defaults:

- model: `gpt-5.6-luna`
- sandbox: `danger-full-access`
- approval: `never`
- working directory: `A:\theestate`

Each new session receives a one-time `/status` transaction only after the seat-owned TUI is judged ready. The final status implementation focuses the exact console HWND, injects `/status`, verifies that the text arrived, refocuses the same HWND, sends Return independently, and verifies that the resulting status/session/limits panel actually appears. Reused sessions receive no additional injected input.

The Windows titles remain seat-correlated (`C1-CODEX`, `C2-CODEX`, `C3-CODEX`) so Estate seat identity remains visible outside the Codex TUI.

### Middle row — automation Chromium

Each seat owns a distinct persistent automation profile root. These are separate from Patricia's interactive Chrome profiles and are intended for future Playwright/automation use.

The middle row is deliberately an automation identity surface, not Patricia's normal browsing environment. The lifecycle contract is one active owner per seat/profile. Clean shutdown is required before Playwright or another owner opens the same persistent profile.

The visible browser surface is app-mode and intentionally minimal.

### Bottom row — interactive ChatGPT Chrome

The interactive profiles were physically proven and mapped as:

- C1 -> Chrome `Profile 3`
- C2 -> Chrome `Profile 4`
- C3 -> Chrome `Profile 5`

The final visible surface uses Chrome app mode so the normal tab strip, bookmarks bar, and address bar do not consume the limited bottom-row height.

The persistent ChatGPT "workspace member hit a limit" banner is intentionally **not** part of this closeout. Its cosmetic suppression was parked separately rather than allowing scope creep into the Codex Desk acceptance work.

---

## Stream Deck Gesture Contract

The original implementation simply launched a shell once per physical press. A single press produced one command window; two presses produced two stacked command windows; three presses produced three; long press launched another shell instead of shutting down the desk.

The accepted gesture dispatcher now interprets the physical control as a single managed action:

| Gesture | Result |
| --- | --- |
| 1 press | `Mode Top` |
| 2 presses | `Mode Middle` |
| 3 presses | `Mode Bottom` |
| 4 presses | `Mode All` |
| Long press | `StopAll` |

The implemented gesture timing was approximately:

- multi-click aggregation window: **400 ms**
- long-press threshold: **1.25 s**

The click-count interpretation belongs in the Stream Deck/plugin action path rather than spawning a separate shell per click.

---

## What Worked

### Explicit seat homes and launch flags

Resolving `CODEX_HOME` from the Estate seat configuration and passing the model/sandbox/approval flags explicitly eliminated ambiguity between C1/C2/C3 and prevented Codex defaults from silently selecting Sol or a weaker permission mode.

### Separate interactive and automation identities

Keeping Patricia's Chrome profiles separate from the automation Chromium roots was the correct boundary. No authentication state was copied into the automation profiles.

### App-mode browser surfaces

App mode was the right presentation model for the constrained workspace. It removed browser chrome that otherwise consumed meaningful vertical space.

### Graceful Chromium lifecycle

The initial Chromium implementation left profiles marked `Crashed` and displayed Restore Pages because only the visible HWND was being closed while hidden/secondary browser windows and processes remained alive. The repaired lifecycle closes all top-level windows owned by the seat profile, waits for the profile-owned process tree to exit, and preserves a clean `Normal` profile exit state.

This also established the useful rule that a persistent automation profile has one active owner at a time.

### Fast concurrent StopAll

An early long-press shutdown took more than 45 seconds and still left the top Codex row alive. The final shutdown performs independent row shutdowns concurrently and identifies Codex terminals through the exact seat launcher process rather than broad `pwsh.exe`/`conhost.exe` matching.

Successful later measurements were roughly 1-2 seconds total rather than tens of seconds.

### `/status` as authoritative session verification

Transient launcher text was not useful because Codex redraws the terminal immediately after startup. `/status` is a stronger check because the running Codex session itself reports its account/session/limit state.

The final implementation does not merely type `/status`; it verifies the text arrived, sends Return separately, and verifies that the status panel appeared.

### Independent physical screenshot acceptance

This was the decisive acceptance improvement. Codex-generated screenshots and `GetWindowRect` telemetry repeatedly agreed with the implementation while Patricia could plainly see the windows straddling monitor boundaries. The final successful fix was accepted using Patricia's independently supplied screenshot.

---

## What Did Not Work

### Treating numeric rectangles as physical truth

This was the most persistent failure. Several iterations reported the same apparently correct rectangles while the windows were visibly compressed, shifted, or split across monitor seams.

Examples of reported-but-not-physically-correct target rectangles included:

- C1: `(2560,-706) 853x720`
- C2: `(3413,-706) 853x720`
- C3: `(4266,-706) 854x720`

Those numbers were internally consistent with the wrong coordinate assumptions. They were not sufficient acceptance evidence.

### Repeated DPI compensation patches

Several repairs attempted to normalize or compensate Chrome geometry after launch. These could make one direct test pass while the real Stream Deck-triggered path still failed. Repeated offsets, double-scaling corrections, and post-placement compensation were symptoms rather than the root fix.

### Normalizing a physical PMv2 monitor to 96-DPI logical dimensions

The final geometry root cause was clear: a physical **3840x2160** per-monitor-v2 display was being normalized to **2560x1440**, then PMv2-aware windows were placed using those smaller logical coordinates. This produced the characteristic ~2/3 scaling/compression and apparent movement between physical monitor regions.

The final repair retained the authoritative physical monitor rectangles for PMv2 placement.

The accepted physical work area was reported as approximately:

- device: `DISPLAY1`
- physical work area: `(3840,-2139)` through `(7680,21)`
- column widths: `1280 / 1280 / 1280`
- row heights: `540 / 540 / 1080`

This physical map replaced the erroneous 96-DPI normalization layer.

### Self-generated screenshot acceptance

A screenshot cropped or resolved using the same faulty coordinate model is not independent evidence. Codex at one point visually classified its own screenshot as correct while Patricia was watching the physical windows remain split between monitors.

The acceptance process was changed so Codex stopped moving windows, requested `READY FOR PATRICIA SCREENSHOT`, and waited for a screenshot captured independently by Patricia.

### Blind `/status` timing

A fixed 750 ms delay after discovering `codex.exe` was not a reliable readiness test. It could inject into model-selection, MCP startup/recovery, or another modal state.

The final readiness guard detects prompt/readiness evidence and rejects startup/modal signatures before status injection.

### Assuming typed `/status` meant executed `/status`

An intermediate implementation successfully injected `/status` text but did not reliably submit Return. This was exposed physically: the command remained at the prompt until Patricia manually pressed Enter.

The final status helper treats the operation as a complete transaction and verifies the resulting panel.

### Using the visible console text as persistent seat identity

Launcher identity text appeared briefly and disappeared when Codex repainted the TUI. Persistent seat identification belongs outside the TUI (window title), while `/status` provides authoritative session information inside the TUI.

### Reinstalling a reduced Stream Deck plugin bundle

One gesture-repair deployment regressed the entire Stream Deck surface. Existing profile UUIDs remained bound, but registrations/status handlers were missing or mismatched. The result was widespread red `ERR` buttons, generic GPU `HEALTH` tiles, and broken Voice/Operator Deck actions.

The recovery restored the known-good full action/status surface, including GPU ring gauges, Voice, UNDO/CLEAR/SELECT, and monitor placement actions, while preserving the new Codex Desk action.

This established a critical deployment rule: **do not reinstall a reduced plugin registry over an active profile whose UUIDs depend on the full action surface.**

---

## Key Failure / Repair Chronology

The following commits represent the main evolution. Some intermediate work occurred between these commits, but these are the important landmarks captured during acceptance.

| Commit | Purpose / result |
| --- | --- |
| `3e522c4595f810c90e0f393a981db32d474cdef8` | Independent C1/C2/C3 Codex terminals and physical top-row placement. |
| `01dbd9c7c29010a3f58e71af67c9a285f2e31dc1` | Explicit Luna, full sandbox, and approval-never launch flags. |
| `e2f9d47b136ee2f93520420295210cfe9f68943c` | Initial interactive Chrome seat mapping. |
| `9cb347caa7e0f37b2dd40ca746da700f698c5c56` | Proven Chrome profile identity verification and reuse. |
| `5a855fc4d1d59a2af112c3bf9f3ecfbc3553fa6c` | Chrome app-mode bottom surfaces. |
| `9e82e290a5f3bbfdd764208cdbfcaaf271301af4` | Isolated C1/C2/C3 Chromium automation identities. |
| `beb613fe44bb4f48a2632294388a793da87071a8` | Clean Chromium lifecycle; Restore Pages regression removed. |
| `79a3f3d23a0f1c3eceb0fd3e1f02b3ca84c3f62c` | Restored Chromium app-mode presentation. |
| `720d7ca91d0b589bd8071eae58ccc013c49815c5` | Replaced visible Chrome-for-Testing surface with standard Chrome while preserving automation roots. |
| `e3751ad6` | Initial Stream Deck 1/2/3/4/long gesture wiring. |
| `202afa2d` | Restored the full Stream Deck action/status surface after reduced-registry regression. |
| `8fb5f426670f3e15f44733c20c038ee0e24cf2bb` | Bottom-row geometry and StopAll repair attempt; exposed continuing DPI issues. |
| `dfd03bb54a8bb876f908f51f2273c8f0b4417d2e` | Idempotence and fast concurrent shutdown; improved seat-owned Codex process identification. |
| `a0aae9bf2db06f4781f9820dc286d3521a4a8c2b` | Additional Chrome placement stabilization attempt; direct tests passed but physical Stream Deck acceptance still failed. |
| `a46c6db2fbc453e0d7e1b0fb0ced7ff8bb74a944` | `/status` injection attempt plus early Stream Deck-path DPI correction; physical placement still failed. |
| `7beae373` | PMv2/canonical monitor-map attempt and improved Codex readiness detection; physical acceptance still exposed coordinate mismatch. |
| `d39a2198` | Made `/status` submission authoritative: text verification, independent Return via SendInput, and resulting panel verification. |
| `9107d97f` | Final geometry fix: retain physical PMv2 monitor rectangles rather than normalizing 3840x2160 to 2560x1440. Independent Patricia screenshot passed. |

Commit IDs above are retained as an engineering chronology, not as an assertion that every intermediate commit was individually acceptable. Several were intentionally superseded after physical testing exposed failures that automated validation had missed.

---

## Physical Acceptance Record

Final physical verification by Patricia established that:

- the CODEX DESK button loaded the intended windows;
- all nine windows appeared in their intended locations;
- the complete workspace closed successfully using the long-press action;
- shutdown performance was no longer excessively slow;
- the final geometry matched the intended 3x3 organization;
- the final accepted geometry was confirmed using Patricia's independent screenshot rather than the launcher's own screenshot/coordinate calculations.

This closes the Codex Desk construction effort. Future changes should be treated as separate Estate Changes rather than reopening or rewriting this history.

---

## Lessons / Do Not Repeat

1. **Physical acceptance outranks internally consistent geometry telemetry.** If the operator sees a window crossing a monitor seam, the geometry is wrong even if `GetWindowRect` returns the expected numbers.

2. **Do not validate a coordinate model using evidence generated by the same coordinate model.** A cropped screenshot produced from the same faulty monitor assumptions is not independent validation.

3. **Keep PMv2 physical coordinates physical.** Do not normalize a physical monitor to 96-DPI logical dimensions and then use those values for PMv2-aware placement.

4. **Resolve monitor topology once per workspace reconstruction.** Rows/applications should consume one canonical physical monitor map rather than calculating separate coordinate systems for terminal, Chromium, and Chrome.

5. **Gesture interpretation belongs in the Stream Deck action path.** Do not model multi-click behavior by launching one command process per click.

6. **Ordinary `Mode All` is reconstructive, not destructive.** Healthy windows should be discovered, verified, reused, and repositioned if necessary. Restart behavior belongs only to explicit restart/stop paths.

7. **Persistent browser profiles need clean ownership and shutdown semantics.** One active owner per automation profile; cleanly close the full browser process/window set rather than only the visible HWND.

8. **Do not treat process existence as TUI readiness.** `codex.exe` existing does not mean Codex is ready for `/status`.

9. **Do not treat typed input as submitted input.** A successful `/status` transaction includes Return and verified resulting output.

10. **Do not use transient TUI text for persistent operator identity.** Seat correlation belongs in persistent window identity; runtime status belongs in `/status`.

11. **Never deploy a reduced plugin action registry over an active full profile.** Existing UUID bindings may survive while handlers disappear, producing `ERR`/`?` failures across unrelated controls.

12. **Do not allow adjacent improvements to expand the acceptance scope.** Cosmetic banner suppression, visible Grace execution observers, and screenshot ergonomics were parked rather than mixed into the Codex Desk closeout.

---

## Parked Follow-On Work

The following ideas were intentionally excluded from this closeout:

- ChatGPT workspace-limit banner suppression in the interactive app surfaces.
- Optional visible observer mode for Grace-dispatched Codex Bridge executions.
- Operator Deck quadrant-based screenshot/snipping workflow.
- Grace parallelism and concurrent reasoning/execution scheduling.
- Codex-task completion / attention-required integration into the Estate notification path.

The next immediate engineering step after this closeout is to wire a bounded Codex task into the existing Estate attention/notification path before returning to Grace parallelism.

---

## Closeout Decision

**CLOSED / ACCEPTED.**

The CODEX DESK Stream Deck control is physically usable and has passed final operator acceptance for startup, layout, and shutdown. The implementation should now be frozen except for separately scoped defects or enhancements.
