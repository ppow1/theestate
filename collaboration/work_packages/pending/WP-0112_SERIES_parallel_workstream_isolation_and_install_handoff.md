# SERIES TASK WP-0112 — Parallel Workstream Isolation and Install Handoff

## Codex Command
Read `collaboration/work_packages/pending/WP-0112_SERIES_parallel_workstream_isolation_and_install_handoff.md` and do exactly what it says.

## Mode
SERIES

## Mission
Create the Estate standard for parallel Codex workstreams so multiple implementation packages can be worked at the same time without colliding on the same runtime files, while still producing installable, reviewable changes that can be merged safely into the active Estate codebase.

## Background
The Estate has now authored and processed more than one hundred work packages, most of them SERIES packages. That was intentional during foundation-building because many packages touched the same core files and needed strict sequencing to avoid merge conflicts and source-of-truth ambiguity.

The Estate now needs to mature from single-fileline sequential implementation into controlled parallel execution. The Steward wants to be able to assign multiple work packages to multiple Codex workers simultaneously, especially when the work can be isolated into sidecar modules, staged artifacts, install manifests, adapters, or integration patches that do not immediately overwrite shared runtime files.

The desired outcome is not uncontrolled parallel development. The desired outcome is a repeatable pattern:

1. A Codex worker implements a feature in an isolated workstream area or clearly bounded module.
2. The worker produces an install or integration manifest.
3. Chief Architect / validation review confirms scope, conflicts, and readiness.
4. The feature is installed into the active runtime through a controlled handoff step.
5. Merge order becomes flexible where dependencies allow, rather than forcing every package to be SERIES by default.

This package creates that standard.

## Scope
Design and implement the first repository-supported standard for parallel workstream isolation and install handoff.

The standard should define:

- when a work package may be PARALLEL rather than SERIES
- how a package declares touched areas, dependency assumptions, and integration targets
- where sidecar/staging implementation artifacts may live
- how an implementation worker records install instructions
- how validation determines whether the staged work is safe to install
- how install handoff is represented for Chief Architect review
- how generated artifacts and runtime outputs are kept out of broad Git staging
- how merge conflict risk is classified before work begins
- how parallel packages declare conflicts with other packages
- how final installation into active runtime files is performed or deferred

## Out of Scope
Do not convert all existing pending work packages to PARALLEL in this package.

Do not implement a full scheduler or queue manager unless existing queue tooling already supports a small extension.

Do not change GitHub branch protection, merge authority, validation authority, or Steward authority.

Do not permit workers to bypass review by writing directly into active runtime files when a package requires installation review.

Do not create a new governance system.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless the existing repository standard explicitly requires it.

## Required Behavior
Create a durable standard or operational document that future work packages can reference when they are intended for parallel execution.

The document should cover at least these concepts:

### 1. Workstream Mode
Define allowed modes such as:

- SERIES — sequential package; may touch shared active files directly.
- PARALLEL-STAGED — parallel-safe package; implementation occurs in isolated staging/sidecar files and produces install handoff.
- PARALLEL-INDEPENDENT — parallel-safe package; touches only isolated modules/tests/docs and has no shared active-file collision.
- INSTALL-HANDOFF — package or review step that integrates staged work into active runtime files.

Use existing Estate terminology where possible.

### 2. Conflict Surface Declaration
Require future parallel packages to declare:

- expected source files touched
- expected tests touched
- expected runtime/generated artifacts
- integration target files
- known dependency packages
- packages that must complete before install
- packages that can safely run in parallel

### 3. Staging / Sidecar Location
Define a safe repository convention for staged work. Possible locations may include a new or existing path such as:

- `workstreams/WP-XXXX/`
- `operations/workstreams/WP-XXXX/`
- `collaboration/workstreams/WP-XXXX/`
- another path consistent with current Estate structure

Choose the path by inspecting existing repository conventions. Do not invent a location if an existing suitable pattern exists.

### 4. Install Manifest
Define a required install manifest format for staged parallel work. It should include:

- work package ID
- staged artifact paths
- intended final install paths
- files expected to be modified during install
- manual or automated install steps
- validation commands
- rollback notes
- dependency assumptions
- conflict risks
- generated artifacts to ignore or review carefully
- authority and review requirements

### 5. Review and Validation
Define how Chief Architect #4 or the validation stream evaluates a staged workstream before installation.

The standard should require local-first validation and should distinguish:

- staged-work validation
- install-readiness validation
- post-install validation
- production-readiness validation

### 6. Work Package Template Compatibility
Update or extend guidance so future work packages can specify parallel-staged behavior under the Codex Task Template Standard without weakening completion receipts, validation recipes, or production-readiness requirements.

## Safety and Authority Constraints
- Parallel execution must reduce merge conflicts, not hide them.
- Staged work must not be treated as installed work.
- Install handoff must not imply validation success.
- Workers must not broad-stage generated artifacts.
- Workers must not bypass Steward, Chief Architect, validation, or merge authority.
- Unknown conflict surfaces must force SERIES or INSTALL-HANDOFF review rather than silent parallelization.
- Do not weaken local-first operation.

## Required CLI / Command Surface
If repository tooling supports it, add a small local command surface to inspect parallel workstream manifests. Acceptable commands may include:

```bash
PYTHONPATH=src python -m estate.cli.main workstream inspect --id WP-XXXX --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-XXXX --json
```

If adding CLI support is too large for this package, document the command as future work and provide a manual validation recipe instead.

## Required Artifacts
Expected artifacts may include:

- durable parallel workstream standard document
- optional schema or example install manifest
- optional sample manifest for a dummy or documentation-only workstream
- updates to onboarding or Codex task template references if needed
- tests if code/CLI/schema is added
- validation recipe for WP-0112
- `collaboration/work_packages/completions/WP-0112_codex_done.json`

## Tests
Verify:

- the standard clearly distinguishes SERIES, PARALLEL-STAGED, PARALLEL-INDEPENDENT, and INSTALL-HANDOFF behavior
- the install manifest shape is documented or validated
- staged work is not treated as installed work
- conflict surface declarations are required for parallel packages
- validation distinguishes staged, install-readiness, post-install, and production-readiness checks
- completion receipt exists and records limitations
- any CLI or schema added has tests

## Validation Recipe Requirement
Add or update the validation recipe for WP-0112. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure this package can be evaluated by:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0112 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement
Create `collaboration/work_packages/completions/WP-0112_codex_done.json` with at least:

- `work_package_id`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review`
- `merge_authority`
- `validation_recipe_status`
- `production_readiness_command_status` if run
- final standard document path
- install manifest path or not-applicable reason
- CLI command surface or not-applicable reason

## Production Readiness Requirement
Run or document the equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0112 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If production readiness remains blocked because the standard has not yet been applied to active work packages, record that as an expected limitation.

## Demonstration Requirements
Document exact commands run and observed status.

If an example manifest is created, show how a future package would declare:

- parallel mode
- staged paths
- final install paths
- dependencies
- conflict risks
- validation commands
- rollback notes

## Completion Signal
Create `collaboration/work_packages/completions/WP-0112_codex_done.json` using the standard completion schema.

Set `ready_for_ca_review=true` only if the standard is durable, discoverable, validated or explicitly limited, and safe for future work packages to reference.

## Merge Class
Class A if the package only creates standards, documentation, schema, or non-invasive inspection tooling.

Escalate to Class B if it changes merge authority, validation authority, branch policy, automatic installation behavior, or permits autonomous modification of active runtime files.
