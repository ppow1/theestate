# ChatGPT archive throttling troubleshooting

## `RATE_LIMITED`

This means ChatGPT returned HTTP 429 or displayed a temporary conversation-access restriction. The archive stops advancing, closes browser activity, waits using the configured backoff, and retries within `retryWindowMs`. It is not an authentication failure and does not indicate archive corruption.

For an unattended run, wait for the bounded retry window. If it expires, the command exits with code 3 and the report records `status: "throttled"`. Run `resume` later; do not restart a full archive unless specifically required.

For an interactive full archive, Ctrl+C cancels the wait safely. The completed conversation index and run checkpoint remain intact. Do not hammer refreshes or lower pacing values to work around the restriction.

If the account is still limited after the retry window, wait and run the normal command later. Do not bypass ChatGPT protections or change VPN, proxy, endpoint, privacy, or DNS security controls.

## Incomplete or timed-out hydration

Inspect the conversation's `exportMetadata.hydration` and `status/current-run.json`. The diagnostic includes the marked container selector, scroll position, scroll height, semantic message count, last count/height changes, loading indicators, and virtualization state. `topReached: true` alone is not sufficient. Increase the duration or pass ceiling only when the bounded run shows legitimate long-conversation progress; never treat reaching a ceiling as success.

## Interrupted legacy run

If `state/run-state.json` is still `status: "running"`, the next run writes `state/invalidated-run.json` and marks recent successful entries from that run `currentStatus: "incomplete"`. They are re-exported even in sync mode. The current conversation is never checkpointed as complete on Ctrl+C.

## Browser-context loss or large failure cascades

The run report distinguishes `trueExportFailures`, `browserContextFailures`, and `cascadingDeferredItems`. A closed Playwright page/context/browser is recorded once and stops the run; remaining discovered conversations are deferred, not reported as independent export failures. Inspect `A:\AI\Archives\ChatGPT\status\current-run.json`, `state\run-state.json`, and the run report, then run `resume` after the browser condition is corrected.

The exporter evaluates message roles inside the page callback. A `ReferenceError` such as `roleOf is not defined` is an exporter defect and should be reported as one true export failure; it must not be allowed to turn subsequent closed-page errors into hundreds of independent failures.

## Inventory totals and stale recovery

`discoveredThisRun` is only the current UI scan. `historicalUnionCount` is the monotonic union of the current scan, the archive index, and prior inventory snapshots. A scan of 168 must not remove IDs from an earlier 325-ID inventory. Inspect `previouslyKnownNotVisible`, `newlyDiscoveredIds`, `idsRequiringReExport`, and `unavailableThroughUi` in the reconciliation report.

On startup, a stale `running` checkpoint becomes `interrupted` and is retained in `state/recovered-runs/`; its current conversation is requeued while verified completed exports remain reusable. Use `generate-artifacts --conversation-id <id>` for a bounded artifact repair. Inspect `manifest.json` and `validation.json`; JSON, MHTML, and PDF are all required.

Bounded validation must not use `full` or `resume`:

```powershell
node A:\AI\Tools\ChatGPTConversationArchive\dist\cli.js inventory --config A:\AI\Tools\ChatGPTConversationArchive\config.bounded-inventory.json
node A:\AI\Tools\ChatGPTConversationArchive\dist\cli.js generate-artifacts --config A:\AI\Tools\ChatGPTConversationArchive\config.example.json --conversation-id <explicit-id>
```

The eventual resumed Seat 1 operation is:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File A:\AI\Tools\ChatGPTConversationArchive\scripts\Run-ChatGPTConversationArchiveSync.ps1
```
