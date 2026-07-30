# Architecture

`src/browser.ts` owns all browser/session and selector behavior. `src/sync.ts` inventories first, checkpoints the index after every conversation, retries bounded transient extraction failures, and writes per-run reports. `src/storage.ts` provides normalization, SHA-256 hashing, rendering, and atomic persistence. `src/validate.ts` validates index-to-latest identity and content hashes. `src/cli.ts` exposes manual and scheduled commands.

Browser navigation emits a distinct throttle signal from HTTP 429 responses and tolerant UI-text detection. `src/throttle.ts` owns detection, exponential backoff, jitter bounds, cancellation, and pacing policy. `src/sync.ts` closes and reopens the archive browser between throttle waits, preserves the index/checkpoint, stops advancing to new conversations while limited, and records `RATE_LIMITED` metrics in the run report. Scheduled sync uses the same bounded retry window without prompting.

The exporter treats browser-context loss as a run-level boundary: it records one context failure, marks the remaining discovered items as deferred/cascading, checkpoints the next conversation, and stops. Exporter failures remain separate. Browser-evaluated callbacks must contain all runtime logic they use; `roleOf` is classified inline inside the `evaluateAll` callback rather than referencing Node scope. `src/progress.ts` writes `status/current-run.json`, emits periodic heartbeat/stall warnings, and accumulates seat-aware counters in `state/runtime-metrics.json`.

The source archive is neutral and conversation-first. Classification by repository, office, project, topic, or sensitivity is optional downstream metadata and is never an export filter.

## Conversation hydration completeness

Sidebar discovery and conversation hydration are separate flows. Sidebar discovery scrolls only a measured history container. Hydration walks semantic message-node ancestry, rejects sidebar-linked ancestors, verifies scrollable overflow and dimensions, and measures a real `scrollTop` change before using the container. The active conversation is opened near the newest content and scrolled upward in controlled DOM steps. Convergence requires stable message count, first-message hash, scroll height, near-zero top position, no loading indicator, and no newly inserted nodes for the configured stable-pass count.

Long or virtualized conversations are accumulated incrementally. Records are keyed by `data-message-id` when present, otherwise by role/content identity, deduplicated, and emitted chronologically. Completeness metadata is persisted with each export; an incomplete item is never written as a successful index revision. A stale `running` checkpoint from the defective fixed-scroll exporter invalidates its recent successful entries so resume cannot skip them.
