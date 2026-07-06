# PARALLEL-STAGED TASK WP-0205 — Mission Control, Projects, and Roadmap Controls

## Codex Command
Read collaboration/work_packages/pending/WP-0205_PARALLEL_STAGED_mission_control_projects_roadmap_controls.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Design and stage safe Mission Control, Projects, and Roadmap controls for the Office of the Steward without directly installing changes into active Office runtime files.

This package implements the WP-0118-F8 follow-up slice: Mission Control, Projects, and Roadmap Controls. It must produce staged, reviewable artifacts under `collaboration/workstreams/WP-0205/`, including proposed UI/control metadata, proposed code or patch structure, tests or staged test plan, validation notes, and an install manifest.

These tabs should become planning and coordination control surfaces that let the Steward inspect sources, refresh derived summaries, convert warnings or roadmap candidates into drafts, and request prioritization/review without making summaries authoritative.

## Background
WP-0118 identified Mission Control, Projects, and Roadmap as related Office surfaces that summarize operational state and future planning. Their proposed verbs include source inspection, refresh, warning-to-draft, review request, evidence inspection, work-package proposal drafting, roadmap snapshot export, and prioritization review request.

WP-0200 stages the shared Office action framework foundation. WP-0205 should align with the WP-0200 staged vocabulary where practical, but must not assume WP-0200 is already installed.

Because Chief Architect #4 and other workers may be touching Office UI concurrently, WP-0205 follows the WP-0112 parallel workstream standard. This package stages proposed implementation rather than modifying active Office runtime files directly.

## Number Allocation
This package uses the temporary active authoring block assigned by the Steward to Chief Architect #3: WP-0200 through WP-0250.

Do not renumber this package based on GitHub search results.

## Scope
Create staged implementation artifacts for Mission Control, Projects, and Roadmap controls.

In scope:

1. Inspect current Mission Control, Projects, and Roadmap surfaces in the Office implementation.
2. Inspect source artifacts used by those surfaces, including work package pipeline, operations board, dependency graph, roadmap, capability summaries, and generated runtime reports where applicable.
3. Stage proposed controls for Mission Control, Projects, and Roadmap only.
4. Align action metadata with WP-0200 staged action vocabulary where practical.
5. Create staged tests or a test plan.
6. Create `collaboration/workstreams/WP-0205/install_manifest.json`.
7. Create `collaboration/work_packages/completions/WP-0205_codex_done.json`.

## Out of Scope
Do not directly modify active Office runtime files in this package.

Do not make Mission Control, Projects, or Roadmap summaries authoritative sources of truth.

Do not approve, assign, execute, merge, validate, or close work packages from these tabs.

Do not change canonical lifecycle states.

Do not implement controls for Work Packages, Validation, Mailboxes, Parking Lot, Residents, AI Services, Settings, Help, or About except where needed as read-only references.

Do not add cloud services, external API calls, telemetry, or remote workers.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless current repository standards require it.

## Required Staging Location
All staged artifacts must live under:

`collaboration/workstreams/WP-0205/`

Expected staged paths may include:

- `collaboration/workstreams/WP-0205/proposed/mission_projects_roadmap_controls.md`
- `collaboration/workstreams/WP-0205/proposed/action_metadata.json`
- `collaboration/workstreams/WP-0205/proposed/src/estate/core/office_planning_actions.py`
- `collaboration/workstreams/WP-0205/proposed/tests/test_office_planning_actions.py`
- `collaboration/workstreams/WP-0205/install_manifest.json`
- `collaboration/workstreams/WP-0205/validation_notes.md`

## Required Controls to Stage
Stage controls for Mission Control, Projects, and Roadmap only.

### Mission Control
Proposed controls should include:

1. Refresh Mission Control payload
   - Safe local generated-artifact update after confirmation.
   - Must report output paths.

2. Inspect source lane
   - Open/read source artifacts behind a Mission Control lane or warning.
   - Safe read-only.

3. Open source artifact
   - Show local source path and link/open affordance.
   - Safe read-only.

4. Create follow-up draft from warning
   - Draft a work-package proposal or validation observation from a warning.
   - Steward-confirmed local mutation.
   - Must not automatically create executable work.

5. Request Chief Architect review
   - Draft/queue review request through existing authority route.
   - Authority-gated.
   - Must not mark review complete.

### Projects
Proposed controls should include:

1. Inspect active project/work package
   - Open pending/completion/source artifacts.
   - Safe read-only.

2. Open dependency evidence
   - Inspect dependency graph or pipeline source evidence.
   - Safe read-only.

3. Copy next-action command
   - Copy command where known.
   - Copy-only by default.

4. Create blocker note draft
   - Steward-confirmed local mutation.
   - Does not change canonical state unless routed through approved transition.

5. Request review or prioritization
   - Authority-gated request.
   - Does not mark approved.

### Roadmap
Proposed controls should include:

1. Inspect roadmap evidence
   - Safe read-only.

2. Draft work-package proposal from roadmap item
   - Steward-confirmed local mutation.
   - Proposal only; not executable authority.

3. Export roadmap snapshot
   - Safe read-only or generated artifact update with output-path reporting.

4. Request prioritization review
   - Authority-gated request.

5. Mark local review note, staged design only
   - Local UI/runtime marker only, clearly not canonical roadmap closure.

## Required Action Metadata
For each proposed control, include action metadata with:

- action ID
- label
- target tab
- target lane/project/roadmap item when applicable
- description
- action class
- authority/safety class
- confirmation requirement
- reads artifacts
- writes artifacts
- command hook or handler reference
- expected output paths
- failure behavior
- local-only/no-upload guarantee
- explicit statement that summaries remain non-authoritative

Use WP-0118 and WP-0200 vocabulary.

## Required Safety Rules
The staged design must enforce or describe:

1. Summary surfaces are not sources of truth.
2. Warning-to-draft creates drafts/proposals only.
3. Review or prioritization request is not approval.
4. Local blocker notes do not change canonical status unless routed through approved transition.
5. Refresh controls report generated artifact paths and do not silently mutate source authority.
6. Copy-command controls are safer than execute-command controls.

## Required Install Manifest
Create:

`collaboration/workstreams/WP-0205/install_manifest.json`

The manifest must follow the WP-0112 standard and include staged artifact paths, intended final install paths, expected modified files, manual/automated install steps, validation commands, rollback notes, dependency assumptions, conflict risks, generated artifacts to ignore/review, authority/review requirements, and `staged_work_is_installed: false`.

## Conflict Surface Declaration
Expected conflict surface:

- `src/estate/core/steward_command_center.py` — likely future UI integration target
- `src/estate/core/steward_dashboard.py` — possible read-only/helper reference
- `src/estate/core/operations_board.py` — possible read-only/helper reference
- `src/estate/core/dependency_graph.py` — possible read-only/helper reference
- `src/estate/core/assignment_queue.py` — possible read-only/helper reference
- `src/estate/cli/main.py` — possible command registry reference
- `tests/test_steward_command_center.py` — likely future integration tests

Risk class: medium/high, because future install likely touches shared Office UI and planning summary surfaces.

Packages that can run in parallel:

- Other `PARALLEL-STAGED` tab-control packages that stage under their own workstream directories.

Packages that should complete before install:

- WP-0118 complete and merged.
- WP-0200 reviewed or installed as action framework foundation.
- Any active CA4 repair touching Office UI or planning surfaces reviewed for conflicts.

## Required Tests / Staged Tests
Provide staged tests or a test plan proving:

- Mission Control inspect/open actions are safe read-only.
- Mission Control refresh requires confirmation and reports output paths.
- Warning-to-draft creates draft/proposal only.
- Projects blocker note does not change canonical work package status.
- Roadmap proposal draft does not grant execution authority.
- Review/prioritization request is authority-gated and not approval.
- Export snapshot includes local-only/no-upload posture.

## Required Validation Commands
Run or document equivalent staged validation:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0205 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0205 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If WP-0205 has no validation recipe yet because staged packages are not fully integrated into validation, document that limitation in the completion receipt.

## Required Outputs
Create or update:

- `collaboration/workstreams/WP-0205/install_manifest.json`
- staged proposed Mission Control, Projects, and Roadmap control artifacts under `collaboration/workstreams/WP-0205/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0205_codex_done.json`

Do not install staged files into active runtime paths in this package.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0205_codex_done.json`

It must include work_package_id, codex_status, completed_at, branch, pull_request_url or reason, summary, workstream mode, staged artifact paths, install manifest path, intended install paths, conflict risks, controls staged by tab, files changed, tests/validation run, known limitations, `staged_work_is_installed: false`, `ready_for_ca_review: true`, and `merge_authority: ca_verified_auto_merge_allowed`.

## Acceptance Criteria
WP-0205 is complete when staged Mission Control, Projects, and Roadmap control artifacts exist, every staged control has action metadata/authority classification/confirmation behavior/local-only posture, summaries remain non-authoritative, an install manifest exists, risks are explicit, tests or staged test plan exist, completion receipt exists, and active Office runtime files are not directly installed.

## Merge Class
Class A if this package only creates staged workstream artifacts, install manifest, tests/test plan, and completion receipt.

Escalate to Class B if active runtime files are modified or the package attempts to install the controls directly.
