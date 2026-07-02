# SERIES TASK WP-0031 — Transport Adapter Evaluation

## Codex Command
Read `collaboration/work_packages/pending/WP-0031_SERIES_transport_adapter_evaluation.md` and do exactly what it says.

## Mode
SERIES. Documentation/research implementation. Depends on existing Communication Bus, mailbox, Alfred, and work package artifacts.

## Mission
Evaluate candidate transport adapters for Estate communication while preserving the Communication Bus as the institutional messaging model.

## Why This Is Next
Operational use exposed friction with GitHub as live transport, inability to directly observe Codex task completion, and possible prior mailbox patterns from Q Mastery/MPT. The Estate needs a disciplined transport adapter evaluation before committing to GitHub, Gmail, local broker, Gotify, or MPT-style approaches.

## Scope
Create an evaluation document such as:

- `docs/collaboration/Transport_Adapter_Evaluation_v1.md`

Evaluate at least:

- GitHub repository files
- local filesystem / local broker
- Gmail/email adapter
- Gotify notification adapter
- Q Mastery / MPT-style mailbox connector pattern
- future Codex task status adapter if API access becomes available

## Evaluation Criteria
For each adapter, assess:

- local-first compatibility
- ability to preserve structured messages
- auditability
- worker accessibility
- Steward approval friction
- ability to support autonomous operation
- ability to support completion/status detection
- security/credential implications
- cost/dependency profile
- suitability for v1/v2/future use

## Required Architectural Position
The document must explicitly preserve this distinction:

- Communication Bus = institutional messaging model
- Transport Adapter = mechanism used to move or surface messages

Do not recommend replacing the Communication Bus with any transport.

## Expected Outputs
- Transport Adapter Evaluation v1 document.
- Recommendation matrix.
- Short recommendation for near-term transport priorities.
- Parking Lot entry or future-work note for Codex API/task status adapter if appropriate.

## Constraints
Do not implement transports in this package. Do not add credentials. Do not call external services. Do not create new governance. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Validation
Documentation review only unless code is added. Ensure all referenced repository paths exist where claimed.

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0031_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A for bounded evaluation documentation. Escalate to Class B only if implementation adds transports, credentials, or changes Communication Bus architecture.
