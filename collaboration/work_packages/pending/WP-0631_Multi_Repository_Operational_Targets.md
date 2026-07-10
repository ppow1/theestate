# WP-0631 - Multi-Repository Operational Targets

Status: Proposed
Priority: High
Owner: Chief Architect #6
Classification: Estate Internal
Depends on: WP-0626, WP-0629

## Mission

Generalize Background Operations and post-merge validation from the Estate repository to multiple governed repositories, beginning with Cue Mastery, without duplicating runtime infrastructure.

## Required Implementation

- Extend the existing Operational Target model with repository URL/path, base branch, workspace root, evidence root, enabled capabilities, watch profile, validation binding, and department owner.
- Support Estate and Cue Mastery as separate targets using the same discovery, cleanroom, audit, scheduler, and Office surfaces.
- Isolate cursors, workspaces, evidence, holds, and verdicts by target.
- Support enable/disable and read-only observation mode per target.
- Do not assume all repositories use Estate work-package numbering or validation recipes.

Expected files:

```text
src/estate/core/multi_repository_targets.py
src/estate/core/multi_repository_runtime.py
tests/test_multi_repository_targets.py
tests/test_multi_repository_runtime.py
docs/integration/multi_repository_operational_targets.md
```

## Acceptance

- Two repositories can be monitored concurrently without state collision.
- Failure in one target does not stop the other.
- Cue Mastery can begin in observe-only mode and later enable audits.
- Office status groups activity by repository and department.
- No new orchestrator, event bus, or audit system is introduced.
- Completion receipt: `collaboration/work_packages/completions/WP-0631_codex_done.json`.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0631_Multi_Repository_Operational_Targets.md and do exactly what it says.
```
