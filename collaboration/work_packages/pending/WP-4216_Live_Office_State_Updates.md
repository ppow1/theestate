# WP-4216 — Staged Live Office State Updates

Status: Pending
Priority: High
Owner: Chief Architect / implementation worker
Classification: Estate Internal, staged extension
Promotes: PL-0018
Authored: 2026-07-26
Base commit: `dcc81c71c1a408767e644988859f09ad64771250`

## Mission

Stage an implementation-ready, local-only live-state update coordinator for the existing Office of the Steward. Detect changes to allowlisted authoritative Estate artifacts, produce ordered deterministic update notifications, and reconcile the already-open browser without a manual page reload while preserving operator state.

This package extends the current Office. It must reuse WP-0511 refresh settings, WP-0085 Operator Activity Stream, `operations_center_settings`, `steward_command_center`, `office_command_surface`, and existing runtime/projection artifacts. It must not create a second Office shell, event feed, settings store, action bus, renderer, or web framework.

## Reconciled baseline and bounded gap

PL-0018 classification at authoring: **partially_implemented**.

- WP-0511 / PR #215 supplies persistent refresh enabled/interval settings and the functional Settings surface.
- WP-0085 / PR #92 supplies the read-only Operator Activity Stream and regenerated quiet-refresh feed.
- The existing browser timer fetches `/status.json`; `/api/office/payload` exposes limited shell metadata. These do not constitute an ordered artifact-change protocol or browser reconciliation mechanism.
- PL-0017 is already Closed through WP-0117 / PR #145.

The only gap in scope is the unified detection, notification, freshness, ordering, and browser-reconciliation layer. Production integration is deliberately deferred to a separately authorized install handoff.

## Required reading and reuse contract

Read before implementation:

- `collaboration/work_packages/pending/WP-0511_Office_Functional_Audit_and_Settings_Repair.md`
- `collaboration/work_packages/completions/WP-0511_codex_done.json`
- `collaboration/work_packages/pending/WP-0085_SERIES_operator_activity_stream.md`
- `collaboration/work_packages/completions/WP-0085_codex_done.json`
- `src/estate/core/operations_center_settings.py`
- `src/estate/core/operator_activity_stream.py`
- `src/estate/core/steward_command_center.py`
- `src/estate/core/office_command_surface.py`
- `docs/architecture/live_office_state_updates.md`

The staged coordinator consumes the effective WP-0511 `refresh.enabled` and `refresh.quiet_refresh_seconds` values. It may propose compatible fields through an install handoff, but must not maintain parallel preferences. It regenerates or consumes WP-0085 data through its public generator/projection and never creates a second activity feed. Office actions continue through the existing action endpoint/registry. Command-center panel rendering remains authoritative for Office presentation.

## Authoritative source allowlist

Create a versioned allowlist whose entries map stable `source_id` values to repository-relative paths/globs, parser/type, owning generator, affected panel IDs, and sensitivity classification. It must cover, where present:

1. operations boards, including `operations/boards/**`;
2. Parking Lot (`operations/boards/parking_lot.md`);
3. active-work and daily-board artifacts;
4. institutional mailboxes and safe mailbox projections;
5. notifications and acknowledgement projections;
6. worker, assignment, execution queue, and execution activity state;
7. validation, audit, readiness, and completion reports;
8. resident status/presence projections;
9. service health/status projections;
10. operational activity, including WP-0085 outputs;
11. runtime reports consumed by existing Office panels;
12. the canonical Office settings artifact.

Generated browser DOM, localStorage/sessionStorage, form values, cached update payloads, and client clocks are never authoritative. Runtime projections remain projections; their provenance/owning authoritative input must be retained. Directory traversal, arbitrary query-selected paths, symlink escape, secret stores, attachments, raw prompts/conversations, credentials, and unallowlisted files are forbidden.

## Change detection decision

### Primary approach: hybrid bounded polling plus generation/hash comparison

Implement the initial staged coordinator with a single server-side bounded polling scan over the allowlist. Compare stable metadata and SHA-256 hashes only after metadata changes; parse only settled files. Produce one deterministic generation snapshot and update notification. The browser polls one existing-local-server update endpoint at the effective WP-0511 interval.

This fits the repository's standard-library local HTTP server and current timer, requires no new framework/dependency, works across supported platforms, and provides deterministic tests and catch-up after browser disconnect.

### Optional accelerators and deferred transports

- A filesystem watcher may only wake the same coordinator; debounce it and retain bounded polling as recovery. Watcher unavailability degrades visibly to polling.
- SSE may be proposed by the install handoff as a local-only notification optimization, backed by the same generation log and catch-up endpoint.
- WebSockets are not justified for one-way notifications and must not be added absent new evidence.
- Long polling is an acceptable compatibility alternative but must use the same schema/order rules.
- No strategy may create a private event bus or make notification delivery authoritative.

## Staging and parallel-safety boundary

All implementation work in this package is initially confined to:

```text
collaboration/workstreams/WP-4216/
  proposed/
  fixtures/
  tests/
  integration_notes.md
  validation_notes.md
  install_manifest.json
```

The prototype may include update schemas, a fake allowlisted artifact scanner/watcher, simulated local server, browser reconciliation harness, fixtures, tests, and an exact install manifest. It must not edit production paths, including:

- `src/estate/core/steward_command_center.py`
- `src/estate/core/operations_center_settings.py`
- `src/estate/core/operator_activity_stream.py`
- `src/estate/core/office_command_surface.py`
- `src/estate/cli/main.py`
- production Office assets
- Open WebUI, Grace, Alfred, Helen, Local Compute, or Evelyn workstreams

A separate reviewed install-handoff package must own every shared/production file change, endpoint registration, and settings-schema evolution.

## Update protocol

### Snapshot

The coordinator maintains a local restart-safe snapshot:

```json
{
  "schema_version": "live-office-snapshot-v1",
  "epoch": "server-start-or-persisted-epoch-id",
  "generation": 42,
  "produced_at": "2026-07-26T12:00:00Z",
  "sources": {
    "parking_lot": {"revision": 8, "sha256": "hex", "observed_mtime_ns": 0, "state": "available"}
  }
}
```

`epoch` distinguishes reset/restart domains. `generation` is monotonically increasing within an epoch and increments only when the settled semantic source set changes. Each source revision increments on content/state transition. Timestamps are UTC RFC 3339 and never substitute for ordering.

### Update notification

```json
{
  "schema_version": "live-office-update-v1",
  "update_id": "sha256-of-canonical-content",
  "epoch": "opaque-local-epoch",
  "generation": 42,
  "previous_generation": 41,
  "produced_at": "2026-07-26T12:00:00Z",
  "affected_sources": [{"source_id": "parking_lot", "revision": 8, "sha256": "hex", "state": "available"}],
  "affected_panels": ["parking"],
  "severity": "info",
  "urgency": "normal",
  "refresh_recommendation": "incremental",
  "full_rerender_required": false,
  "diagnostics": [{"code": "burst_coalesced", "safe_message": "2 changes coalesced"}],
  "connection": {"transport": "poll", "state": "connected", "retry_after_seconds": 30},
  "freshness": {"last_successful_scan_at": "2026-07-26T12:00:00Z", "data_age_seconds": 0, "stale": false}
}
```

Canonical JSON uses sorted keys, stable source/panel ordering, UTF-8, and no volatile diagnostic ordering. `update_id` excludes transport-only retry metadata. Diagnostics expose safe codes/messages, never raw secret-bearing content or unrestricted paths.

## Ordering, truth, and reconciliation rules

- Reject an update with the current epoch and a generation lower than the last applied generation.
- Suppress exact `update_id` duplicates and same-generation replays; never advance “last successful update” for rejected data.
- A new epoch triggers snapshot comparison and safe catch-up; it does not imply that data is newer.
- Coalesce all changes inside the debounce window into one generation with sorted affected sources/panels.
- If the browser misses generations, request the current snapshot/panel payload. If the server cannot prove continuity, require a safe full rerender.
- Source deletion is a real state transition, not silently “unchanged.” Incomplete/malformed/unreadable files retain the last known-good panel data, attach diagnostics, and make freshness degraded/stale as appropriate.
- “Last checked,” “last successful scan,” “last applied update,” artifact produced-at, and computed data age are distinct. The Office must never label a failed check or notification receipt as “updated/current.”
- A partial panel update failure leaves successful panels applied, identifies failed panels, makes the view degraded, and offers safe whole-page refresh. A failed incremental renderer automatically attempts at most one safe rerender; repeated failure stops automatic attempts and remains visibly stale.

## Browser lifecycle and state preservation

1. Initial page load uses the existing command-center renderer/payload and records its epoch/generation/source revisions.
2. After DOM readiness, start exactly one update client only if WP-0511 refresh is enabled and the operator has not paused the session. Clamp cadence to the existing 5–3600 second bounds. Static/file mode reports manual-only truthfully.
3. Before applying an update, capture active tab/hash, selected navigation item, expanded/collapsed `details` and panels by stable ID, focused element and selection where safe, scroll positions, and dirty form controls.
4. Fetch only affected panel projections where the existing renderer exposes a safe stable contract. Otherwise request a safe full command-center rerender.
5. Never overwrite dirty/unsaved fields. Defer that panel, show “update available,” and let the operator apply/discard or force refresh. Preserve active tab/navigation and panel state; restore scroll relative to stable anchors, falling back to prior page offset.
6. On disconnect/offline, keep existing content, show connection state and increasing data age, use capped exponential backoff with jitter, and catch up from last applied epoch/generation. Do not clear unsaved state on reconnect.
7. Always provide manual force refresh. Whole-page reload requires operator confirmation when unsaved input exists.

## Operator controls

Extend the existing Settings/control surfaces only through the later install handoff:

- WP-0511 refresh enabled/disabled and interval remain canonical;
- session-only Pause Live Updates and Resume do not alter durable settings;
- Force Refresh bypasses cadence but not safety/allowlist rules;
- connection state, last successful scan/apply, truthful data age, stale warning, and safe diagnostics are visible;
- panel policy supports `incremental`, `defer_when_dirty`, or `whole_page`; it must not become a second settings store.

Disabled refresh performs no automatic scans requested by that browser and displays “automatic updates disabled,” not “current.” Quiet periods suppress non-urgent rendering but not correctness scans; warnings/errors may surface immediately without stealing focus.

## Performance and cadence

- Default: the WP-0511 default of 30 seconds; minimum 5, maximum 3600. Never add a conflicting default.
- Metadata scans are bounded to the allowlist. Hash only candidates with changed size/mtime/inode metadata, with periodic full verification to detect timestamp anomalies.
- Default watcher debounce/burst-coalescing window: 500 ms; configurable only in coordinator internals (100–5000 ms), not a new operator preference.
- At most one scan and one browser apply may be in flight. A pending trigger coalesces rather than queues unbounded work.
- Cap files/bytes hashed per scan and record a degraded continuation when the budget is exceeded; proposed defaults and benchmark evidence belong in `integration_notes.md`.
- Throttle non-urgent browser rendering to one apply per second. Many simultaneous changes become one generation; if affected panels exceed a documented threshold, recommend safe full rerender.
- Quiet/background tabs may reduce cadence using Page Visibility, but must catch up immediately when visible and must show honest age.

## Failure matrix

| Failure | Required behavior |
| --- | --- |
| Local server unavailable / browser offline | Preserve view and inputs; show disconnected/stale; bounded backoff; manual retry. |
| Watcher unavailable | Diagnose safely and fall back to bounded polling. |
| Malformed artifact / incomplete write | Debounce and retry settled read; retain last good data; do not advance that source revision; mark degraded. |
| Deleted source | Emit `state=deleted`; render truthful unavailable state; never reuse as current. |
| Permission failure | Emit safe diagnostic without contents; retain last good view and mark stale/degraded. |
| Dropped SSE/WebSocket if later installed | Reconnect with last generation and catch up through snapshot; polling remains recovery. |
| Stale/out-of-order/duplicate update | Reject/suppress and record diagnostic; do not change freshness success. |
| Incremental render failure | One safe fallback render, preserve dirty state, then stop loop and warn on repeated error. |
| Repeated errors | Capped backoff/circuit breaker, visible diagnostic, manual force refresh; no retry storm. |

## Security and privacy gates

Transport binds loopback by default and has no external destination, telemetry, cloud dependency, or upload. Tests must fail on non-loopback URL construction. Payloads contain stable source IDs and safe summaries, not arbitrary filesystem paths, file contents, secrets, credentials, raw mailbox bodies, private conversations, environment variables, or tokens. Resolve and verify every path remains below the Estate root and matches the versioned allowlist; reject symlink escape. Preserve the existing local-server security posture and do not imply remote authentication.

## Required staged deliverables

1. Versioned allowlist and JSON schemas for snapshot/update/connection status.
2. Deterministic fake scanner/watcher and generation coordinator.
3. Simulated local update endpoint/transport with disconnect/reconnect fixtures.
4. Browser-state reconciliation prototype/harness independent of production assets.
5. Unit/integration fixtures and tests.
6. `integration_notes.md` describing exact reuse seams, benchmarks, production endpoint proposal, limitations, and rollback.
7. `install_manifest.json` listing proposed shared-file changes with hashes and explicit install order; no automatic install.
8. `validation_notes.md` with command outputs and browser/operator checklist.

## Required tests

Tests must prove:

- one changed artifact; multiple simultaneous changes; unchanged state;
- deterministic payload and stable ordering/hash;
- out-of-order rejection and duplicate suppression;
- malformed source, partial file write, deletion, and permission failure;
- disconnected browser, capped retry, reconnect and catch-up across missed generation/restart;
- active tab/navigation, panel expansion, scroll anchor, focus, and unsaved form preservation;
- stale-view warning and truthful last-updated/data-age fields;
- debounce/coalescing, scan budgets, and browser update throttling;
- refresh disabled and configured WP-0511 interval, including one-timer enforcement;
- compatible reads from `operations_center_settings` without another store;
- compatible regeneration/consumption of WP-0085 without another feed;
- manual refresh and failed incremental-render fallback;
- allowlist/path traversal/symlink protection, payload redaction, and no external network destinations.

Tests must use temporary fixtures and simulated time/network only. They must not call providers, external networks, GPU/Ollama, ChatGPT, or Codex.

## Validation recipe and operator proof

The staged completion must record exact commands, expected counts, and results for:

```text
python -m pytest -q collaboration/workstreams/WP-4216/tests
python -m json.tool <each schema/fixture/manifest JSON>
git diff --check
```

Also run focused compatibility tests for WP-0511 settings and WP-0085 activity behavior against the staged adapter, plus a local simulated-browser test that:

1. opens an initial state;
2. edits an unsaved form and changes tab/panel/scroll state;
3. changes one allowlisted fixture;
4. observes one ordered update without full manual reload;
5. preserves all operator state;
6. disconnects, changes multiple fixtures, reconnects, and catches up;
7. makes a malformed write and displays degraded/stale truthfully.

No production browser screenshot is required for a non-installed prototype. The later install handoff must require a real local Office browser smoke test and screenshot/evidence of connection, stale, pause/resume, and preserved-state surfaces.

## Completion, lifecycle, and rollback

The implementation receipt must enumerate artifacts, tests, known limitations, no-network proof, reuse assertions, base/branch/commit, and validation evidence. It must explicitly assert:

```text
reused_wp_0511_settings: true
reused_wp_0085_activity_stream: true
new_office_shell_created: false
new_settings_store_created: false
new_action_bus_created: false
new_activity_feed_created: false
production_files_modified: false
```

Rollback for staging is removal of `collaboration/workstreams/WP-4216/`. The future install handoff must define file-by-file backup/restore, settings migration rollback, endpoint removal, timer removal, and fallback to existing manual/quiet refresh without deleting authoritative artifacts.

PL-0018 remains Promoted while this package is merely authored or staged. It may be marked Closed only after production implementation is merged, required tests pass, validation evidence exists, and a complete implementation receipt confirms reuse and truthful live behavior.

## Acceptance criteria

1. All required staged deliverables exist under the isolation boundary.
2. The allowlist spans every required authoritative source class without browser state becoming authority.
3. One ordered, deterministic generation protocol drives all detection strategies.
4. The browser prototype preserves operator state and never overwrites dirty input.
5. Freshness, failure, disconnect, restart, and partial-update states are truthful.
6. WP-0511 settings and WP-0085 activity stream are reused, not duplicated.
7. Performance, privacy, local-only, and failure tests pass.
8. No production/shared Office file is changed by the staged package.
9. A separate install handoff is authored and approved before shared integration.
10. Completion receipt and validation notes are complete; PL-0018 closure remains gated on merged production implementation.
