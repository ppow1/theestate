# PARALLEL-STAGED TASK WP-0208 — Daily Board and Parking Lot Controls

## Codex Command
Read collaboration/work_packages/pending/WP-0208_PARALLEL_STAGED_daily_board_parking_lot_controls.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Design and stage safe Daily Board and Parking Lot controls for the Office of the Steward without directly installing changes into active Office runtime files.

This package implements the WP-0118-F5 follow-up slice: Daily Board and Parking Lot Controls. It must produce staged, reviewable artifacts under `collaboration/workstreams/WP-0208/`, including proposed UI/control metadata, proposed code or patch structure, tests or staged test plan, validation notes, and an install manifest.

The Daily Board and Parking Lot should become safe Steward workflow surfaces for refreshing board state, opening source items, drafting notes, marking local review state, and promoting Parking Lot or blocked/review items into proposed work-package drafts while preserving proposal-only semantics.

## Background
WP-0118 identified Daily Board and Parking Lot as related Office surfaces. Proposed verbs include refresh board, open source item, mark locally reviewed, draft daily note, promote blocked/review item to request, inspect parking-lot item, promote to proposed work-package draft, archive local duplicate, and request review.

WP-0200 stages the shared Office action framework foundation. WP-0208 should align with the WP-0200 staged vocabulary where practical, but must not assume WP-0200 is already installed.

Because Chief Architect #4 and other workers may be touching Office UI, board, or parking-lot files concurrently, WP-0208 follows the WP-0112 parallel workstream standard. This package stages proposed implementation rather than modifying active Office runtime files directly.

## Number Allocation
This package uses the temporary active authoring block assigned by the Steward to Chief Architect #3: WP-0200 through WP-0250.

Do not renumber this package based on GitHub search results.

## Scope
Create staged implementation artifacts for Daily Board and Parking Lot controls.

In scope:

1. Inspect current Daily Board and Parking Lot surfaces in the Office implementation.
2. Inspect existing morning briefing, daily board, active work, parking lot, and board integration artifacts/modules.
3. Stage proposed controls for Daily Board and Parking Lot only.
4. Align action metadata with WP-0200 staged action vocabulary where practical.
5. Create staged tests or a test plan.
6. Create `collaboration/workstreams/WP-0208/install_manifest.json`.
7. Create `collaboration/work_packages/completions/WP-0208_codex_done.json`.

## Out of Scope
Do not directly modify active Office runtime files in this package.

Do not convert Parking Lot items into executable work packages without Steward review and proper authority route.

Do not mark underlying work packages, blocked items, or review items complete from these tabs.

Do not delete Parking Lot entries or board entries.

Do not implement controls for Work Packages, Validation, Mission Control, Mailboxes, Residents, AI Services, Settings, Help, or About except where needed as read-only references.

Do not add cloud services, external API calls, telemetry, or remote workers.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless current repository standards require it.

## Required Staging Location
All staged artifacts must live under:

`collaboration/workstreams/WP-0208/`

Expected staged paths may include:

- `collaboration/workstreams/WP-0208/proposed/daily_board_parking_lot_controls.md`
- `collaboration/workstreams/WP-0208/proposed/action_metadata.json`
- `collaboration/workstreams/WP-0208/proposed/src/estate/core/office_board_actions.py`
- `collaboration/workstreams/WP-0208/proposed/tests/test_office_board_actions.py`
- `collaboration/workstreams/WP-0208/install_manifest.json`
- `collaboration/workstreams/WP-0208/validation_notes.md`

## Required Controls to Stage
Stage controls for Daily Board and Parking Lot only.

### Daily Board
Proposed controls should include:

1. Refresh Daily Board
   - Regenerate or refresh board integration artifacts where an existing safe generator exists.
   - Safe local generated-artifact update after confirmation.
   - Must report output paths.

2. Open source item
   - Open/read the local source artifact behind a priority, waiting item, blocked item, or review-required item.
   - Safe read-only.

3. Mark locally reviewed
   - Local UI/runtime review marker only.
   - Steward-confirmed local mutation.
   - Must clearly state it does not close the underlying item.

4. Draft daily note
   - Draft a local note from board state.
   - Steward-confirmed local mutation.

5. Promote blocked/review item to request draft
   - Draft a review request, validation observation, or work-package proposal from a blocked/review item.
   - Steward-confirmed local mutation or authority-gated route depending on target.
   - Draft/proposal only.

### Parking Lot
Proposed controls should include:

1. Inspect Parking Lot item
   - Open/read item detail, source board, category, priority, owner, status, and promotion conditions.
   - Safe read-only.

2. Promote to proposed work-package draft
   - Create a proposed work-package draft from a selected Parking Lot item.
   - Steward-confirmed local mutation.
   - Must not make it executable or assigned by default.

3. Archive local duplicate, staged design only
   - Stage design for duplicate marking only where a local marker exists.
   - Requires confirmation and source/destination summary.
   - Must not delete source entries.

4. Request review
   - Draft/queue a review request through existing authority route.
   - Authority-gated.
   - Does not mark approved.

5. Export Parking Lot snapshot
   - Local-only snapshot with source references and sensitivity warning.

## Required Action Metadata
For each proposed control, include action metadata with:

- action ID
- label
- target tab
- target board item or parking-lot item when applicable
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
- explicit draft/proposal-only semantics where applicable

Use WP-0118 and WP-0200 vocabulary.

## Required Safety Rules
The staged design must enforce or describe:

1. Promotion creates drafts/proposals only unless later authority route explicitly accepts them.
2. Local review markers do not close underlying board or work-package items.
3. Archive/duplicate marking is not deletion.
4. Refresh controls report generated artifact paths.
5. Review requests are not approvals.
6. Export bundles include sensitivity warnings and remain local-only.

## Required Install Manifest
Create:

`collaboration/workstreams/WP-0208/install_manifest.json`

The manifest must follow the WP-0112 standard and include staged artifact paths, intended final install paths, expected modified files, manual/automated install steps, validation commands, rollback notes, dependency assumptions, conflict risks, generated artifacts to ignore/review, authority/review requirements, and `staged_work_is_installed: false`.

## Conflict Surface Declaration
Expected conflict surface:

- `src/estate/core/steward_command_center.py` — likely future UI integration target
- `src/estate/core/daily_board_integration.py` — possible read-only/helper reference
- `src/estate/core/morning_briefing.py` — possible read-only/helper reference
- `src/estate/core/operations_board.py` — possible read-only/helper reference
- `operations/boards/daily_board.md` — source reference; do not mutate unless staged design explicitly declares local draft only
- `operations/boards/active_work.md` — source reference
- `operations/boards/parking_lot.md` — source reference; do not mutate directly in this package
- `src/estate/cli/main.py` — possible command registry reference
- `tests/test_steward_command_center.py` — likely future integration tests

Risk class: medium/high, because future install likely touches shared Office UI and board surfaces.

Packages that can run in parallel:

- Other `PARALLEL-STAGED` tab-control packages that stage under their own workstream directories.

Packages that should complete before install:

- WP-0118 complete and merged.
- WP-0200 reviewed or installed as action framework foundation.
- Any active CA4 repair touching Office UI, boards, parking lot, or work package proposal generation reviewed for conflicts.

## Required Tests / Staged Tests
Provide staged tests or a test plan proving:

- Daily Board refresh requires confirmation and reports output paths.
- Open source item and inspect Parking Lot item are safe read-only.
- Local review marker does not close underlying item.
- Promotion to work-package draft is proposal-only and not executable.
- Review request is authority-gated and not approval.
- Duplicate/archive design does not delete source entries.
- Export snapshot includes sensitivity warning and local-only/no-upload posture.

## Required Validation Commands
Run or document equivalent staged validation:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0208 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0208 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If WP-0208 has no validation recipe yet because staged packages are not fully integrated into validation, document that limitation in the completion receipt.

## Required Outputs
Create or update:

- `collaboration/workstreams/WP-0208/install_manifest.json`
- staged proposed Daily Board and Parking Lot control artifacts under `collaboration/workstreams/WP-0208/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0208_codex_done.json`

Do not install staged files into active runtime paths in this package.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0208_codex_done.json`

It must include work_package_id, codex_status, completed_at, branch, pull_request_url or reason, summary, workstream mode, staged artifact paths, install manifest path, intended install paths, conflict risks, controls staged by tab, files changed, tests/validation run, known limitations, `staged_work_is_installed: false`, `ready_for_ca_review: true`, and `merge_authority: ca_verified_auto_merge_allowed`.

## Acceptance Criteria
WP-0208 is complete when staged Daily Board and Parking Lot control artifacts exist, every staged control has action metadata/authority classification/confirmation behavior/local-only posture, proposal-only semantics are explicit, an install manifest exists, risks are explicit, tests or staged test plan exist, completion receipt exists, and active Office runtime files are not directly installed.

## Merge Class
Class A if this package only creates staged workstream artifacts, install manifest, tests/test plan, and completion receipt.

Escalate to Class B if active runtime files are modified or the package attempts to install the controls directly.
