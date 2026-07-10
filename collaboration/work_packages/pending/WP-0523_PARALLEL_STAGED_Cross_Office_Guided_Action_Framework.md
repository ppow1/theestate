# WP-0523 - Cross-Office Guided Action Framework

## Codex Command
Read collaboration/work_packages/pending/WP-0523_PARALLEL_STAGED_Cross_Office_Guided_Action_Framework.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Create a staged framework for guided multi-step Office actions such as validate -> review -> promote, while preserving each existing authority gate and avoiding direct edits to shared active Office files.

## Required Capabilities
- declarative workflow steps;
- required inputs, confirmations, preconditions, and evidence links;
- resume after interruption;
- truthful blocked/failed/completed states;
- no hidden authorization or automatic approval;
- step-by-step audit evidence;
- safe cancellation before irreversible steps;
- reusable browser contract for guided workflows.

## Staging Requirements
Create under `collaboration/workstreams/WP-0523/`:

```text
install_manifest.json
staged/office_guided_actions.py
staged/test_office_guided_actions.py
guided_action_contract.md
validation_notes.md
rollback_notes.md
```

Do not modify shared active Office files. WP-0531 performs installation.

## Conflict Surface
Expected final targets include a dedicated guided-action runtime, Office action registration, UI rendering hooks, tests, and docs. Declare all shared integration targets in the manifest.

## Validation
Prove deterministic step progression, interruption/resume, authority preservation, idempotency, cancellation, and evidence generation using fake handlers.

## Completion Receipt
Create `collaboration/work_packages/completions/WP-0523_codex_done.json` and explicitly state that staged work is not installed work.
