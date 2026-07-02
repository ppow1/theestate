# SERIES TASK WP-0019 — Alfred Operational Activation

## Codex Command
Read `collaboration/work_packages/pending/WP-0019_SERIES_alfred_operational_activation.md` and do exactly what it says.

## Mode
SERIES. This is implementation-phase work. It should follow WP-0014 and WP-0015 because Alfred depends on mailbox destination coverage and acknowledgement/reply flow.

## Mission
Activate Alfred as the Estate's operational coordination surface using existing implemented capabilities.

Alfred is not being redesigned. This package connects Alfred to current operational artifacts so Alfred can coordinate work, summarize state, and support the Steward with minimal additional cognitive load.

## Why This Is Next
The Estate now has mailboxes, acknowledgements, Operations Board, Steward Dashboard, lifecycle reports, dependency reports, validation reports, and Check for Updates. The next operational gain is a single coordination surface that reads those artifacts and produces actionable coordination output.

## Scope
Implement or extend Alfred runtime support so Alfred can consume existing artifacts:

- `collaboration/messages/*.json`
- mailbox/index/status outputs
- `runtime/operations/operations_board.json` if present
- `operations/steward/dashboard.md` and/or `runtime/steward/dashboard.json`
- `runtime/capabilities/capability_lifecycle_report.json`
- `runtime/dependencies/dependency_graph.json`
- `runtime/validation/operational_validation_report.json`
- `operations/boards/parking_lot.md`
- pending work packages under `collaboration/work_packages/pending/`

## Required Outputs
Add an Alfred operational briefing output such as:

- `runtime/alfred/operational_briefing.json`
- `operations/alfred/operational_briefing.md`

The briefing should include:

- active/pending work packages
- messages requiring acknowledgement
- CA review needs
- Codex-ready next commands
- blocked work
- validation candidates
- parking lot items recently relevant
- recommended next actions

## CLI
If consistent with existing CLI patterns, add or extend:

```bash
PYTHONPATH=src python -m estate.cli.main alfred-operational-briefing --json
```

If an Alfred command already exists, extend it rather than adding a duplicative command.

## Constraints
Do not create new governance. Do not make Alfred a constitutional authority. Do not let Alfred directly approve Steward-only decisions. Do not redesign the Communication Bus. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Add tests for:

- briefing generation with representative artifacts
- missing artifacts as warnings, not fatal errors
- messages requiring acknowledgement appearing in briefing
- pending work packages appearing in briefing
- Codex-ready commands appearing without executing them

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0019_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded operational integration after CA verification. Escalate to Class B only if implementation changes Alfred's authority or governance role.
