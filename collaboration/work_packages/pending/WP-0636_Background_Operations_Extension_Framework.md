# WP-0636 - Background Operations Extension Framework

Status: Proposed
Priority: High
Owner: Chief Architect #6
Classification: Estate Internal
Depends on: WP-0629, WP-0631, WP-0634

## Mission

Make Background Operations safely extensible so future departments and repositories can register watches, jobs, target adapters, evidence processors, and Office summaries without expanding one monolithic runtime module.

## Required Implementation

- Define extension contracts for watch providers, scheduled jobs, operational targets, evidence processors, status contributors, and lifecycle hooks.
- Discover extensions from explicit committed configuration; do not execute arbitrary files found on disk.
- Validate extension identity, version, capabilities, dependencies, classification, and enabled state.
- Isolate extension failure so one module cannot stop the runtime.
- Support enable, disable, inspect, validate, and dry-run.
- Keep Traffic Controller, dispatch, provider adapters, validation, and acceptance boundaries unchanged.

Expected files:

```text
src/estate/core/background_operations_extensions.py
src/estate/core/background_operations_extension_runtime.py
tests/test_background_operations_extensions.py
tests/test_background_operations_extension_runtime.py
docs/integration/background_operations_extension_framework.md
```

## Acceptance

- Built-in Estate and Cue Mastery monitoring can be expressed through the extension contracts.
- Extensions cannot bypass canonical handlers or authority boundaries.
- Invalid or failing extensions are quarantined and reported.
- Extension state appears in the Office control surface.
- Deterministic tests, validation recipe, and completion receipt pass.
- Completion receipt: `collaboration/work_packages/completions/WP-0636_codex_done.json`.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0636_Background_Operations_Extension_Framework.md and do exactly what it says.
```
