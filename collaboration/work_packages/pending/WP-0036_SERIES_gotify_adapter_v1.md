# SERIES TASK WP-0036 — Gotify Adapter v1

## Codex Command
Read `collaboration/work_packages/pending/WP-0036_SERIES_gotify_adapter_v1.md` and do exactly what it says.

## Mode
SERIES. Depends on WP-0035 Notification Router v1.

## Mission
Implement Gotify Adapter v1 as the first local-first Steward Recall transport adapter.

## Why This Is Next
The Notification Router must remain transport-independent, but the Estate needs one concrete local transport to prove Steward Recall end-to-end. Gotify is the selected v1 transport because it is local-first, free, and compatible with mobile push delivery without building a custom mobile app.

## Scope
Create a bounded Gotify adapter module such as:

- `src/estate/core/gotify_adapter.py`

The adapter should accept notification-router recall events and send them to a configured Gotify server.

## Configuration
Use environment variables or local config placeholders. Do not commit secrets.

Potential configuration names:

- `ESTATE_GOTIFY_URL`
- `ESTATE_GOTIFY_TOKEN`

If configuration is missing, the adapter should return a clear warning/status and not crash unrelated validation.

## Message Format
For recall events, send:

- title: `Estate Recall`
- priority: high / Gotify priority mapped from router priority
- message: concise recall message including reason, requested_by, and action

Do not send long explanations. The notification is only to recall the Steward.

## Expected Outputs
- Gotify adapter module.
- Optional CLI if consistent with existing patterns, for example:

```bash
PYTHONPATH=src python -m estate.cli.main gotify-send-test --dry-run
```

- Dry-run mode that does not contact Gotify.
- Runtime delivery report such as `runtime/notifications/gotify_delivery_report.json`.

## Behavior Requirements
- Retry once on transport failure.
- Record success/failure.
- Never expose tokens in logs or reports.
- Support dry-run validation.
- Missing config should be a warning in dry-run and a controlled failure in real send.

## Tests
Add tests for:

- dry-run send
- missing configuration
- token not exposed in output
- retry-once behavior using mocked transport
- correct mapping from router recall event to Gotify payload

## Constraints
Do not implement multiple transports. Do not add SMS/email/Telegram. Do not hard-code credentials. Do not send real notifications in tests. Do not bypass Alfred or Notification Router. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0036_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded transport adapter after CA verification. Escalate to Class B only if implementation introduces credential storage, cloud dependencies beyond Gotify push, or changes recall authority.
