# SERIES TASK WP-0038 — Morning Briefing v1

## Codex Command
Read `collaboration/work_packages/pending/WP-0038_SERIES_morning_briefing_v1.md` and do exactly what it says.

## Mode
SERIES. Depends on Alfred operational briefing, local validation runner, work package records, mailbox synchronization duty, and recall audit log.

## Mission
Implement Morning Briefing v1 so the Steward can return to the Estate and receive a concise summary of overnight or away-period activity without reviewing every mailbox, board, validation report, and work package manually.

## Scope
Create a briefing generator that reads existing artifacts where present:

- Alfred operational briefing
- mailbox synchronization duty reports
- Check for Updates reports
- work package pending/completion/review records
- local operational validation reports
- Operations/Daily Board integration
- Parking Lot summary
- Recall Audit Log
- Notification Router reports

Produce:

- `runtime/briefings/morning_briefing.json`
- `operations/briefings/morning_briefing.md`

## Briefing Sections
Include at least:

- completed work
- failed or blocked work
- pending approvals
- outstanding recalls
- mailbox summary
- board changes
- validation warnings
- recommended next actions
- estimated review time

## CLI
If consistent with existing patterns, add:

```bash
PYTHONPATH=src python -m estate.cli.main morning-briefing --json
```

If a briefing command already exists, extend it rather than duplicating it.

## Behavior Requirements
- Missing optional artifacts should create warnings, not fatal errors.
- The briefing must be concise.
- Do not notify the Steward directly from this package.
- Do not modify authoritative message or work package records.

## Tests
Add tests for:

- briefing generation with representative artifacts
- missing artifact warnings
- completed work summary
- recall summary
- pending approval summary
- Markdown and JSON output generation

## Constraints
Do not create scheduling. Do not add notification transport. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`. Do not make generated briefing output authoritative.

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0038_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded briefing implementation after CA verification. Escalate to Class B only if implementation changes governance, source-of-truth policy, or notification authority.
