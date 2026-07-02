# SERIES TASK WP-0014 — Mailbox Index Regeneration and Destination Coverage Fix

## Steward Command
Open `collaboration/work_packages/pending/WP-0014_SERIES_mailbox_destination_coverage.md` in `ppow1/theestate` and execute the directions inside.

## Mode
SERIES. Do after WP-0013 is merged or rebase from latest `main`.

## Mission
Fix mailbox/index/inbox summary generation so generated mailbox views reflect all valid institutional destinations present in `collaboration/messages/*.json`.

## Why This Is Next
Operational use showed CA4 messages existed as authoritative message files but were not visible in generated inbox summaries. The source of truth is sound; the projection is incomplete.

## Scope
- Inspect existing mailbox/index/routing generation code and docs.
- Support destination forms at minimum: `office.*`, `employee.*`, `mailbox.*`, `worker.*`, and direct known mailbox IDs if registry-backed.
- Use registry sources if present: `data/registry/personnel.json`, `data/registry/mailboxes.json`, `data/registry/residents.json`.
- Regenerate or update status outputs without making them authoritative.
- Preserve individual message JSON files as source of truth.

## Expected Outputs
- Updated mailbox/index generation logic.
- Updated/added tests for office and employee destinations.
- Updated docs if mailbox destination behavior is documented.
- Generated summaries should include CA4 destinations when messages exist.

## Constraints
Do not redesign the Communication Bus. Do not create final identity governance. Do not make generated indexes authoritative. Do not edit ledger/devlog.

## Validation
Run relevant tests and, if available:
`PYTHONPATH=src python -m estate.cli.main worker-inboxes --json`
`PYTHONPATH=src python -m estate.cli.main mailbox-index --json`

## Codex Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0014_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded implementation. CA verification may authorize merge under prior Steward roadmap approval.
