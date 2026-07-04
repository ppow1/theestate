# Parallel Workstream Isolation and Install Handoff Standard v1

## Purpose

This standard defines how future Estate work packages may run in parallel without colliding on shared runtime files. Parallel work is safe only when it is isolated, reviewable, locally validated, and installed through an explicit handoff instead of silently overwriting active runtime files.

## Transition Boundary

- WP-0097 through WP-0111 remain governed by their authored SERIES instructions unless individually revised by a later explicit package.
- WP-0112 creates this standard and does not retroactively alter earlier package obligations.
- Work packages authored after WP-0112 should declare workstream mode and conflict surface when parallel execution is applicable.
- Older pending packages may be converted only by an explicit retrofit package that names the affected work package IDs.
- Validation and Chief Architect review should not reject older packages merely because they predate this standard.

## Workstream Modes

- `SERIES`: sequential package; may touch shared active files directly when authorized by its package.
- `PARALLEL-STAGED`: parallel-safe package; implementation occurs in isolated staging or sidecar files and produces an install handoff manifest. Staged work is not installed work.
- `PARALLEL-INDEPENDENT`: parallel-safe package; touches only isolated modules, tests, or documents and has no shared active-file collision.
- `INSTALL-HANDOFF`: package or review step that integrates staged work into active runtime files after Chief Architect or validation review.

Unknown conflict surfaces force `SERIES` or `INSTALL-HANDOFF` review. Parallel execution must reduce merge conflicts, not hide them.

## Required Conflict Surface Declaration

Every future `PARALLEL-STAGED`, `PARALLEL-INDEPENDENT`, or `INSTALL-HANDOFF` package must declare:

- expected source files touched;
- expected tests touched;
- expected runtime or generated artifacts;
- integration target files;
- known dependency packages;
- packages that must complete before install;
- packages that can safely run in parallel;
- conflict risk class: `none`, `low`, `medium`, `high`, or `unknown`.

## Staging and Sidecar Location

Use `collaboration/workstreams/WP-XXXX/` for staged parallel workstream artifacts. This keeps work beside existing collaboration work packages and away from active runtime outputs. A staged directory may include prototypes, sidecar modules, sample data, install manifests, validation notes, or generated evidence explicitly intended for review.

Workers must not broad-stage generated artifacts. Runtime outputs under `runtime/` remain generated evidence unless a package explicitly says they are canonical source artifacts.

## Install Manifest

A `PARALLEL-STAGED` package must create `collaboration/workstreams/WP-XXXX/install_manifest.json` before completion. The manifest must include:

```json
{
  "work_package_id": "WP-XXXX",
  "workstream_mode": "PARALLEL-STAGED",
  "staged_artifact_paths": ["collaboration/workstreams/WP-XXXX/..."],
  "intended_final_install_paths": ["src/estate/..."],
  "files_expected_to_be_modified_during_install": ["src/estate/..."],
  "manual_install_steps": ["Review manifest", "Apply patch", "Run validation"],
  "automated_install_steps": [],
  "validation_commands": ["PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-XXXX --json"],
  "rollback_notes": "Revert the install commit or restore listed files.",
  "dependency_assumptions": ["WP-YYYY complete before install"],
  "conflict_risks": [{"path": "src/estate/...", "risk": "medium", "reason": "shared integration target"}],
  "generated_artifacts_to_ignore_or_review": ["runtime/..."],
  "authority_and_review_requirements": ["Chief Architect review required before install"],
  "staged_work_is_installed": false
}
```

Install handoff must not imply validation success. Final installation into active runtime files is performed only by the authorized install package or reviewer-directed handoff.

## Review and Validation

Chief Architect #4 or the validation stream evaluates staged work locally first:

1. **Staged-work validation** confirms staged artifacts, manifest completeness, declared paths, and local smoke checks.
2. **Install-readiness validation** confirms dependencies, conflict risks, generated artifact handling, rollback notes, and authority requirements.
3. **Post-install validation** runs after active runtime files are modified by an authorized handoff.
4. **Production-readiness validation** runs the reusable Estate readiness loop and does not rely on live GitHub metadata.

## Codex Task Template Extension

Future parallel work packages extend the Codex Task Template Standard with these sections:

- `Workstream Mode`;
- `Conflict Surface`;
- `Staged Paths`;
- `Install Manifest`;
- `Install Readiness Criteria`;
- `Parallel-Safe Packages`;
- `Required Install Handoff`.

Completion receipts, validation recipes, demonstration requirements, generated artifact handling, and production-readiness requirements remain mandatory unless explicitly marked not applicable with rationale.

## Work Package Number Allocation

Work package numbers must not be allocated from stale GitHub search results. A number is owned by its allocation block before it is owned by GitHub search visibility. Gaps are acceptable when numbers are reserved but unused.

Recommended deterministic allocation blocks:

| Range | Owner / Use |
| --- | --- |
| WP-0001 through WP-0999 | Legacy and current sequential Estate backlog |
| WP-1000 through WP-1999 | Steward and active Chief Architect planning |
| WP-2000 through WP-2999 | Chief Architect #4 validation stream |
| WP-3000 through WP-3999 | Chief Architect #5 continuation stream |
| WP-4000 through WP-5999 | Resident runtime implementation streams |
| WP-6000 through WP-6999 | Third-party or temporary parallel Codex workers |
| WP-7000 through WP-7999 | Emergency repair and hotfix planning |
| WP-8000 through WP-8999 | Future parking and reserved experiments |
| WP-9000 through WP-9999 | Reserved for Steward reassignment |

The local-first allocation ledger is `collaboration/work_packages/work_package_range_ledger.json`. Future authors identify their assigned block by reading that file, not by asking GitHub search for the next number. Temporary allocations must record owner, range, purpose, status, assigned_at, and notes.

## Manual Validation Recipe

For a staged workstream, reviewers should run:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-XXXX --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

WP-0112 provides local inspection commands: `PYTHONPATH=src python -m estate.cli.main workstream inspect --id WP-XXXX --json`, `PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-XXXX --json`, and `PYTHONPATH=src python -m estate.cli.main work-package-ranges --json`. These commands inspect manifests and allocation blocks only; they do not change merge, install, validation, or Steward authority.
