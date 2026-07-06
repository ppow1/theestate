# REPAIR TASK WP-0205 — Repository Boundary, Generated Artifact Tracking, and Ingrid Security Posture

## Codex Command

Read `collaboration/work_packages/pending/WP-0205_REPAIR_repository_boundary_generated_artifact_tracking_and_ingrid_security_posture.md` and do exactly what it says.

## Mode

REPAIR. Repository hygiene / generated artifact boundary / security posture repair.

## Mission

Stop normal local Estate operation from dirtying the Git working tree with live generated projections, while preserving authored source files and deliberate institutional evidence.

The immediate operational symptom is that the Steward repeatedly has to stash generated files before pulling merged GitHub work. The deeper institutional problem is that the repository currently contains too much live Estate state. As the Estate grows, local runtime data, resident conversations, approvals, model inventory, operational status, validation rollups, snapshots, and other sensitive or environment-specific outputs must not be casually shared to GitHub.

This repair must establish a basic source-vs-runtime boundary now, before Ingrid is fully online. Ingrid is the intended future guardian for privacy, clearance, boundaries, and external crossings; this task must prepare a repository posture compatible with that office.

## Background / Observed Evidence

Recent local runs showed `git status --short` becoming dirty after ordinary Office and validation activity. The dirty files were generated/runtime projections, not source edits, including:

- `runtime/steward/command_center.html`
- `runtime/search/institutional_search_index.json`
- `runtime/work_packages/assignment_queue.json`
- `runtime/validation/production_readiness_report.json`
- `runtime/validation/validation_coverage_manifest.json`
- `runtime/validation/work_packages/latest.json`
- `operations/work_packages/assignment_queue.md`
- `operations/steward/decision_queue.md`
- `operations/validation/production_readiness_report.md`
- `operations/validation/validation_coverage_manifest.md`
- `operations/validation/reports/WP-0200_validation.md`
- `operations/validation/reports/WP-0201_validation.md`
- `operations/validation/reports/WP-0202_validation.md`
- `operations/capabilities/capability_dependency_visualization.md`
- `operations/notifications/operations_notification_center.md`

Observed diffs included generated timestamps, local Alfred conversation history, local image attachment references, local AI model inventory, Steward approval records, validation rollups, search index counts, path-format churn, work-package queue count changes, and current runtime status.

That confirms the failure mode:

1. Git tracks live generated projections.
2. Normal local Estate operation rewrites those projections.
3. `git pull --rebase` refuses to proceed because tracked files are dirty.
4. Repeated stashing becomes necessary.
5. The stash problem is therefore a repository-boundary/security signal, not just a Git inconvenience.

## Institutional Principle

The GitHub repository should contain source, authored institutional contracts, governance documents, tests, install manifests, staged work products, and deliberate completion evidence.

The GitHub repository should not become the default transport for live local Estate state, resident conversation history, local runtime indexes, transient validation pointers, local AI inventory, approvals, local attachment references, or regenerated dashboards.

Sensitive or environment-specific local state must be local-first. A future backup/export strategy may exist, but ordinary GitHub rollout must not depend on committing live state.

## Required Work

### 1. Inventory tracked generated artifacts

Create a concise inventory of tracked generated artifacts and classify each into one of these categories:

- `source_or_authored_contract` — keep tracked.
- `completion_evidence` — keep tracked only when deliberately produced for a work package.
- `staged_install_artifact` — keep tracked under `collaboration/workstreams/...` or equivalent.
- `live_runtime_projection` — stop tracking; regenerate locally.
- `local_sensitive_state` — stop tracking; treat as local/private.
- `review_required` — do not change automatically; explain why.

The inventory must include at minimum the files listed in Background / Observed Evidence and representative tracked files under `runtime/`.

Suggested output:

- `operations/repository/WP-0205_generated_artifact_tracking_inventory.md`

### 2. Update repository ignore policy

Update `.gitignore` so newly generated live runtime/projection files stay out of Git by default.

The existing `.gitignore` already contains `runtime/`, but that does not stop already-tracked files from being modified. Preserve or strengthen that rule. Add explicit comments documenting why runtime/live projections are local-only.

Do not ignore authored source, work packages, governance docs, tests, staged workstream manifests, or completion receipts.

### 3. Stop tracking live runtime projections

Use Git removal-from-index semantics for files classified as `live_runtime_projection` or `local_sensitive_state`:

- remove them from Git tracking without deleting the Steward's local working files when possible;
- in a repository commit this will appear as file deletions, but local generation must still be able to recreate them;
- do not delete authored source files or completion evidence.

Candidate paths to stop tracking unless the inventory proves otherwise:

- `runtime/steward/command_center.html`
- `runtime/search/institutional_search_index.json`
- `runtime/work_packages/assignment_queue.json`
- `runtime/validation/work_packages/latest.json`
- `runtime/validation/production_readiness_report.json`
- `runtime/validation/validation_coverage_manifest.json`
- `runtime/residents/authority_decisions.jsonl`
- local runtime conversation/session/attachment material under `runtime/resident_interactions/` and `runtime/resident_conversations/`, except deliberate work-package evidence reports if needed.

Be conservative for historical `runtime/.../WP-xxxx_report.json` evidence. If those are completion evidence, keep them or explicitly document why they should be moved later rather than removed now.

### 4. Separate committed reports from local rollups

Review `operations/` generated markdown projections.

Candidate files causing routine dirty state:

- `operations/work_packages/assignment_queue.md`
- `operations/steward/decision_queue.md`
- `operations/validation/production_readiness_report.md`
- `operations/validation/validation_coverage_manifest.md`
- `operations/validation/reports/WP-0200_validation.md`
- `operations/validation/reports/WP-0201_validation.md`
- `operations/validation/reports/WP-0202_validation.md`
- `operations/capabilities/capability_dependency_visualization.md`
- `operations/notifications/operations_notification_center.md`

Do not blindly remove all `operations/` files. Some operations documents are intended human-readable institutional records. Classify them.

If a file is a live rollup/dashboard generated every run, stop tracking it or move future output to a local ignored path.

If a file is deliberate evidence for a specific work package, keep it tracked.

### 5. Make normal rollout simple again

After the repair, normal local workflow should return to the simple path:

```powershell
CLS
Set-Location A:\theestate
git status --short
git pull
```

Normal Office serving, Alfred chat, validation checks, search index refresh, assignment queue regeneration, and snapshot generation should not cause `git status --short` to show tracked modifications that block a pull.

### 6. Add a security note for Ingrid's future office

Add a short security/boundary note explaining:

- GitHub is an external crossing.
- Live Estate state and resident conversations are increasingly sensitive.
- Ingrid's future role should own/approve the external-sharing posture for runtime data.
- Until Ingrid is fully operational, default to local-only for live runtime projections and sensitive state.

Suggested output:

- `docs/security/Repository_Boundary_and_Local_Runtime_State_v1.md`

### 7. Validation

Run local validation sufficient to prove the repository boundary repair did not break source or Office generation.

At minimum:

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests -q
python -m estate.cli.main steward-command-center --serve --host 127.0.0.1 --port 8765
```

If full tests are too slow, run the focused tests that cover Command Center generation, search/index generation, validation/report generation, and resident interaction behavior. Record exactly what was run.

Also perform this operational check:

```powershell
git status --short
# generate/serve Office and run validation/search/assignment queue commands that previously dirtied the tree
git status --short
```

The second status should not show tracked modifications for live generated projections. If untracked ignored runtime files exist, that is acceptable and should be documented.

## Constraints

- Do not remove source code.
- Do not remove authored work packages.
- Do not remove completion receipts.
- Do not remove staged workstream install manifests.
- Do not commit live Alfred conversation history as source.
- Do not commit local image attachments or local resident interaction attachments.
- Do not introduce a new backup system in this task.
- Do not redesign Ingrid's office. Only add the repository-boundary posture that Ingrid will later own/refine.
- Do not treat `git stash` as the durable fix.
- Do not assume `.gitignore` alone fixes already-tracked files.

## Expected Outputs

- Updated `.gitignore` with clear local-runtime comments.
- Inventory/classification report under `operations/repository/` or another existing suitable operations path.
- Security/boundary note under `docs/security/` or another suitable existing docs path.
- Git index cleanup for files classified as live runtime projections/local sensitive state.
- Tests/validation results recorded in the completion receipt.
- Completion artifact:
  `collaboration/work_packages/completions/WP-0205_codex_done.json`

## Acceptance Criteria

- A clean checkout can pull new GitHub work without needing to stash regenerated Office/runtime projections.
- Ordinary local Office use does not dirty tracked runtime projection files.
- The repository no longer treats live resident/Office/runtime state as normal source material.
- Completion evidence and authored institutional contracts remain protected.
- The repair explicitly recognizes GitHub as an external crossing and prepares for Ingrid's future security stewardship.

## Completion Signal

Before finishing, create `collaboration/work_packages/completions/WP-0205_codex_done.json` with:

- `work_package_id`: `WP-0205`
- `codex_status`: `done`
- `completed_at`
- `branch`
- `pull_request_url_or_not_applicable_reason`
- `merge_authority_or_equivalent`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review`: true

## Merge Class

Class B. This changes repository tracking posture and external-boundary behavior. Chief Architect review required before merge.
