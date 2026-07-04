# SERIES TASK WP-0106 — Resident Runtime Presence Model

## Codex Command
Read `collaboration/work_packages/pending/WP-0106_SERIES_resident_runtime_presence_model.md` and do exactly what it says.

## Mode
SERIES

## Mission
Create the resident runtime presence model that allows Alfred, Helen, and future Estate residents to appear as live local institutional residents rather than static dashboard cards or command-line-only services.

## Background
The Office of the Steward already has resident cards and a resident conversations workspace. Those surfaces make Alfred and Helen visible, but they do not yet establish a shared runtime model for presence, duty state, heartbeat, availability, mailbox awareness, or last-known operational activity.

This package creates the runtime foundation that future Alfred and Helen duty runners will use.

## Scope
Define and implement a local-first resident runtime presence model using existing Estate identity, mailbox, operations, and UI conventions.

The model should support, where existing artifacts allow:

- resident ID / personnel identity linkage
- display name and role
- office or duty assignment
- mailbox ID / mailbox path
- presence state such as offline, available, working, waiting_for_steward, degraded, or error
- current duty
- last heartbeat / last activity
- needs Steward flag
- source artifact links
- status reason / known limitation
- local runtime data file or equivalent persistent state

Integrate the model with the existing resident card framework and Office of the Steward command center where appropriate.

## Out of Scope
Do not implement autonomous Alfred or Helen duty execution in this package.

Do not implement LLM conversation or chat generation.

Do not create a cloud dependency, external identity provider, or remote service.

Do not create a new governance authority for residents.

Do not modify `estate_ledger/ledger.md` or `development/devlog.md`.

## Required Behavior
- Resident presence must be local-first and inspectable from repository/runtime artifacts.
- Missing resident data must degrade gracefully.
- Presence state must not imply authority to act.
- Resident cards should consume the presence model where practical.
- The model must support Alfred and Helen initially and future residents later.
- The model must distinguish visible presence from actual autonomous duty execution.

## Safety and Authority Constraints
- Do not grant residents new authority.
- Do not bypass Steward authorization.
- Do not bypass mailbox, Communication Bus, or validation boundaries.
- Do not store secrets.
- Do not stage broad paths.
- Preserve local-first operation.

## Required CLI / Command Surface
If consistent with existing CLI patterns, add or document local inspection commands such as:

```bash
PYTHONPATH=src python -m estate.cli.main resident-presence --json
PYTHONPATH=src python -m estate.cli.main resident-presence --resident Alfred --json
```

Use existing naming conventions if different.

## Required Artifacts
Expected artifacts may include:

- resident presence model module
- runtime resident presence/state JSON artifact
- integration with resident cards / command center
- tests for populated, missing, stale, and degraded states
- completion artifact

## Tests
Verify:

- Alfred and Helen presence can be rendered.
- Missing runtime data degrades gracefully.
- Stale heartbeat is detectable if implemented.
- Resident cards use presence data where available.
- JSON output is valid if a CLI surface is added.
- No authority-changing behavior is introduced.

## Validation Recipe Requirement
Add or update the validation recipe for WP-0106. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure future validation can evaluate this package with:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0106 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement
Create `collaboration/work_packages/completions/WP-0106_codex_done.json` with the standard completion receipt metadata, including changed files, tests run, known limitations, validation recipe status, production-readiness command status if run, and ready-for-CA-review status.

## Production Readiness Requirement
The package must be compatible with the WP-0095 production-readiness loop. Do not claim production-ready status unless receipts, validation recipe, tests, and readiness checks support it.

## Demonstration Requirements
Document exact commands run and observed output. Include a brief demonstration of Alfred and Helen presence state rendering or JSON inspection.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0106_codex_done.json`.

## Merge Class
Class A unless resident authority, governance, or autonomous execution semantics are changed; escalate to Class B if those boundaries are altered.
