# WP-0629 - Operational Watch Catalog and Control

Status: Proposed
Priority: High
Owner: Chief Architect #6
Classification: Estate Internal
Depends on: WP-0628

## Mission

Replace hard-coded background watches with an extensible, governed catalog that can be enabled, disabled, tuned, and inspected without editing runtime code.

## Required Implementation

- Extend existing Background Operations watch behavior rather than creating a new monitoring system.
- Define watch descriptors with identity, target, trigger, cadence, severity, action class, dependencies, enabled state, and owner.
- Support repository, validation, runtime-health, queue, service, and artifact-freshness watches.
- Allow enable/disable, temporary pause, configuration override, and dry-run evaluation.
- Persist runtime state outside the repository; keep committed default definitions in the repository.
- Emit events and Office summaries.

Expected files:

```text
src/estate/core/operational_watch_catalog.py
src/estate/core/operational_watch_runtime.py
tests/test_operational_watch_catalog.py
tests/test_operational_watch_runtime.py
docs/integration/operational_watch_catalog_and_control.md
```

## CLI

Provide commands equivalent to:

```text
operations-watch list
operations-watch show <watch>
operations-watch enable <watch>
operations-watch disable <watch>
operations-watch pause <watch>
operations-watch evaluate <watch>
```

## Acceptance

- Existing watches migrate without behavior loss.
- Watch state is inspectable and controllable.
- Disabled watches do not trigger work.
- New departmental watches can be added through descriptors.
- No watch directly performs provider execution or institutional acceptance.
- Completion receipt: `collaboration/work_packages/completions/WP-0629_codex_done.json`.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0629_Operational_Watch_Catalog_and_Control.md and do exactly what it says.
```
