# SERIES TASK WP-0022 — Check for Updates v2 Mailbox Integration

## Codex Command
Read `collaboration/work_packages/pending/WP-0022_SERIES_check_for_updates_v2_mailbox_integration.md` and do exactly what it says.

## Mode
SERIES. Depends on WP-0021 Personnel Identity and Mailbox Resolver.

## Mission
Extend Check for Updates so it uses the personnel/mailbox resolver and surfaces mailbox obligations clearly for the actor requesting updates.

## Why This Is Next
Check for Updates is now the synchronization command for long-lived Estate workers. With personnel identity and mailboxes active, the command must reliably show assigned messages, acknowledgement requirements, and relevant operational state for the actor.

## Scope
Update existing Check for Updates implementation, likely under:

- `src/estate/core/check_updates.py`
- `src/estate/cli/main.py`
- tests for check updates

Integrate with the resolver from WP-0021 if available.

The report should include:

- canonical actor identity if resolvable
- mailbox ID if resolvable
- employee ID if resolvable
- messages addressed to the actor, office, employee, mailbox, or worker aliases
- messages requiring acknowledgement
- replies or thread references if available
- warnings for ambiguous or unresolved identity

## Expected Outputs
- Updated JSON report for Check for Updates.
- Updated Markdown report for Check for Updates.
- Tests for CA3, CA4, Alfred, Helen, implementation worker, and general actor cases.
- Documentation update if needed.

## Constraints
Do not create final security clearance policy. Do not create HR authority. Do not redesign Check for Updates or the Communication Bus. Missing registry data must be warnings, not fatal errors. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Validation
Run:

```bash
PYTHONPATH=src python -m estate.cli.main check-updates --actor office.chief_architect_3 --json
PYTHONPATH=src python -m estate.cli.main check-updates --actor office.chief_architect_4 --json
PYTHONPATH=src python -m estate.cli.main check-updates --actor alfred --json
PYTHONPATH=src pytest -q tests/test_check_updates.py
```

Adjust test command if test names differ.

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0022_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded integration after CA verification. Escalate to Class B only if implementation changes identity authority, HR authority, or security/clearance rules.
