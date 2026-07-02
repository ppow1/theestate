# SERIES TASK WP-0025 — Local Operational Validation Runner

## Codex Command
Read `collaboration/work_packages/pending/WP-0025_SERIES_local_operational_validation_runner.md` and do exactly what it says.

## Mode
SERIES. Depends on the current operational reporting commands and recent mailbox/Alfred/board integrations.

## Mission
Create one local runner that regenerates the Estate's operational projections and validation surfaces after pulls, merges, or completed work packages.

## Why This Is Next
The Steward currently has to run or inspect several separate tools after each merge. The Estate needs a single local operational validation runner that refreshes the operational state and identifies warnings without making generated artifacts the source of truth.

## Scope
Add a bounded runner that invokes existing generators where available, such as:

- mailbox index / worker inbox summaries
- routing decisions
- Check for Updates reports
- Alfred operational briefing
- Operations/Daily Board integration
- capability lifecycle report
- dependency graph
- operational validation report
- work package completion/review summaries if present

## Expected Outputs
- Runtime report such as `runtime/validation/local_operational_validation_run.json`.
- Human-readable report such as `operations/validation/local_operational_validation_run.md`.
- CLI command if consistent with existing patterns, for example:

```bash
PYTHONPATH=src python -m estate.cli.main estate-validate-local --json
```

If a similar command already exists, extend it rather than creating a duplicate.

## Behavior Requirements
- Missing optional artifacts should produce warnings, not fatal errors.
- Failed sub-steps should be captured with enough detail to diagnose the failure.
- The runner should clearly separate authoritative sources from generated projections.
- The runner should not directly edit ledger or devlog.

## Tests
Add tests for:

- successful run with representative artifacts
- missing optional artifacts
- failed sub-step capture
- JSON and Markdown output generation
- no direct ledger/devlog writes

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0025_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded operational tooling after CA verification. Escalate to Class B only if implementation changes source-of-truth policy or governance.
