# ChatGPT archive throttling troubleshooting

## `RATE_LIMITED`

This means ChatGPT returned HTTP 429 or displayed a temporary conversation-access restriction. The archive stops advancing, closes browser activity, waits using the configured backoff, and retries within `retryWindowMs`. It is not an authentication failure and does not indicate archive corruption.

For an unattended run, wait for the bounded retry window. If it expires, the command exits with code 3 and the report records `status: "throttled"`. Run `resume` later; do not restart a full archive unless specifically required.

For an interactive full archive, Ctrl+C cancels the wait safely. The completed conversation index and run checkpoint remain intact. Do not hammer refreshes or lower pacing values to work around the restriction.

If the account is still limited after the retry window, wait and run the normal command later. Do not bypass ChatGPT protections or change VPN, proxy, endpoint, privacy, or DNS security controls.

## Browser-context loss or large failure cascades

The run report distinguishes `trueExportFailures`, `browserContextFailures`, and `cascadingDeferredItems`. A closed Playwright page/context/browser is recorded once and stops the run; remaining discovered conversations are deferred, not reported as independent export failures. Inspect `A:\AI\Archives\ChatGPT\status\current-run.json`, `state\run-state.json`, and the run report, then run `resume` after the browser condition is corrected.

The exporter evaluates message roles inside the page callback. A `ReferenceError` such as `roleOf is not defined` is an exporter defect and should be reported as one true export failure; it must not be allowed to turn subsequent closed-page errors into hundreds of independent failures.
