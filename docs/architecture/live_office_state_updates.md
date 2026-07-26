# Live Office State Updates — Bounded Architecture Decision

Status: Proposed for staged proof by WP-4216
Date: 2026-07-26
Decision scope: PL-0018 missing synchronization layer only

## Context

The Office already has a standard-library local HTTP server and command-center renderer, a persistent WP-0511 refresh enabled/interval setting, a browser timer that reads `/status.json`, an existing Office action surface, and the WP-0085 read-only Operator Activity Stream. Those capabilities must remain controlling. What is absent is one ordered contract connecting changes in allowlisted authoritative artifacts to truthful, state-preserving updates in an already-open browser.

## Decision

Use a **hybrid coordinator with bounded server-side polling, generation/hash comparison, and one browser polling endpoint** for the first implementation. An optional filesystem watcher may wake that same coordinator after debounce; bounded polling remains recovery. SSE can later optimize delivery without changing schemas or authority. WebSockets are rejected for the initial one-way requirement, and no new web framework is justified.

The coordinator owns detection/order only. Existing generators continue to own projections; `steward_command_center` continues to own rendering; `office_command_surface` continues to own actions; `operations_center_settings` continues to own cadence/enabled settings; and WP-0085 continues to own the single activity aggregation feed.

## Data flow

```text
allowlisted authoritative artifacts and existing projections
  -> bounded metadata scan / optional watcher wake
  -> settled read + generation/hash comparison
  -> deterministic local update notification
  -> existing local server endpoint
  -> browser reconciliation adapter
  -> existing panel renderer or safe full rerender
```

Browser DOM and cached client state are never fed back as Estate truth. Browser state is captured only to preserve the operator experience during reconciliation.

## Authority and source classes

The versioned allowlist maps stable IDs to repository-relative paths, owning generators, parsers, panel IDs, and privacy classifications. It covers operations boards/Parking Lot, active work/daily board, mailboxes, notifications, worker/assignment state, validation/readiness, resident status, service health, operational activity, runtime reports, and Office settings. Missing or malformed sources remain explicit; generated projections carry provenance. Unallowlisted paths, symlink escapes, secrets, attachments, raw conversations, and arbitrary file requests are rejected.

## Consistency model

A restart-distinguishing epoch and monotonic generation establish order. Stable source revisions and SHA-256 hashes identify content/state. Canonical notification hashes suppress duplicates. The browser rejects lower generations, catches up after gaps, and requests a safe snapshot/full render when continuity cannot be proven. Burst changes coalesce into one sorted generation. Timestamps communicate observation and age but never decide ordering.

“Last checked,” “last successful scan,” “last applied,” and source-produced time are separate. Failed reads retain last-known-good presentation with degraded/stale indicators; they never advance a truthful freshness claim.

## Reconciliation policy

Incremental replacement is permitted only for panels with a stable existing render contract. Otherwise the coordinator recommends a safe full rerender. Before either path, the adapter captures stable IDs for active tab/navigation, expanded panels, focus, dirty forms, and scroll anchors. Dirty inputs are never overwritten; affected panels defer and surface an update-available choice. Disconnects preserve the view, expose age/status, back off, and catch up without losing client state. Manual refresh remains available.

## Cadence and resource bounds

Use the WP-0511 30-second default and 5–3600-second bounds. Allow only one scan/apply in flight. Default watcher debounce and burst coalescing is 500 ms; browser non-urgent application is capped at once per second. Metadata gates hashing, periodic full verification catches metadata anomalies, and file/byte budgets turn excess work into a visible degraded continuation. Background throttling must catch up on visibility.

## Failure and security posture

Watcher failure falls back to polling. Incomplete writes receive settled-read retries. Deleted files create explicit transitions. Permission/parser/render failures retain last-known-good state and show safe diagnostics. Repeated failures use capped backoff/circuit breaking without retry storms.

All transport binds loopback by default. There is no telemetry, cloud dependency, automatic upload, provider call, or external destination. Payloads contain stable IDs, hashes, revisions, panels, freshness, and sanitized diagnostics—not arbitrary paths or source contents.

## Alternatives considered

| Strategy | Disposition | Reason |
| --- | --- | --- |
| Browser reload timer only | Reject | Disrupts operator state and cannot identify/order changed sources. |
| Browser reads repository files | Reject | Exposes arbitrary local data and makes authority/privacy boundaries unsafe. |
| Filesystem watcher only | Reject | Platform/dependency and missed-event behavior require recovery scanning. |
| SSE | Defer as optimization | Good one-way delivery, but does not replace detection, persistence, or catch-up. |
| WebSocket | Reject initially | Bidirectional protocol is unnecessary and increases complexity. |
| Long polling | Compatible fallback | May carry the same schema, but offers no initial advantage over bounded polling. |
| New frontend/backend framework | Reject | Existing architecture can host the bounded endpoint and reconciliation adapter. |

## Integration and rollback boundary

WP-4216 first proves the coordinator, schemas, fake server/watcher, and reconciliation harness only under `collaboration/workstreams/WP-4216/`. A separate install handoff must enumerate reviewed changes to existing production modules/assets. Staging rollback deletes that isolated directory. Production rollback must restore shared files/settings and fall back to the current manual/quiet refresh behavior without touching authoritative artifacts.
