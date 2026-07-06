# PARALLEL-STAGED TASK WP-0209 — Resident Conversation Controls

## Codex Command
Read collaboration/work_packages/pending/WP-0209_PARALLEL_STAGED_resident_conversation_controls.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Design and stage safe Resident Conversation controls for the Office of the Steward without directly installing changes into active Office runtime files.

This package implements the WP-0118-F6 follow-up slice: Resident Conversation Controls. It must produce staged, reviewable artifacts under `collaboration/workstreams/WP-0209/`, including proposed UI/control metadata, proposed code or patch structure, tests or staged test plan, validation notes, and an install manifest.

The Alfred, Helen, and Resident Conversations surfaces should become safe resident interaction controls for starting sessions, opening transcripts, exporting transcripts, drafting promotions of outcomes, and requesting redaction/forget actions while preserving the Resident Action Authority Boundary.

## Background
WP-0118 identified Alfred, Helen, and Resident Conversations as related resident-facing Office surfaces. Proposed verbs include start conversation, inspect resident surface, copy duty/status commands, queue Alfred request, inspect job, start/open/export sessions, redact/forget with audit, and draft promotion of outcomes.

WP-0200 stages the shared Office action framework foundation. WP-0209 should align with the WP-0200 staged vocabulary where practical, but must not assume WP-0200 is already installed.

Because Chief Architect #4 and other workers may be touching Office UI or resident interaction files concurrently, WP-0209 follows the WP-0112 parallel workstream standard. This package stages proposed implementation rather than modifying active Office runtime files directly.

## Number Allocation
This package uses the temporary active authoring block assigned by the Steward to Chief Architect #3: WP-0200 through WP-0250.

Do not renumber this package based on GitHub search results.

## Scope
Create staged implementation artifacts for Resident Conversation controls.

In scope:

1. Inspect current Alfred, Helen, and Resident Conversations surfaces in the Office implementation.
2. Inspect resident interaction, resident presence, conversation sessions, authority boundaries, Alfred duty, Helen duty, and resident chat modules/artifacts.
3. Stage proposed controls for Alfred, Helen, and Resident Conversations only.
4. Align action metadata with WP-0200 staged action vocabulary where practical.
5. Create staged tests or a test plan.
6. Create `collaboration/workstreams/WP-0209/install_manifest.json`.
7. Create `collaboration/work_packages/completions/WP-0209_codex_done.json`.

## Out of Scope
Do not directly modify active Office runtime files in this package.

Do not grant residents new authority.

Do not let Alfred, Helen, or any resident silently execute work packages, validate institutionally, merge, hire/fire, mutate governance, mutate personnel records, or bypass Steward/Chief Architect authority.

Do not implement direct AI model backend assignment unless already present as an inspect/copy-only surface.

Do not delete conversation history. Redaction/forget controls must be designed as auditable local mutations only where existing support exists.

Do not implement controls for Work Packages, Validation, Mission Control, Parking Lot, Mailboxes, AI Services, Settings, Help, or About except where needed as read-only references.

Do not add cloud services, external API calls, telemetry, or remote workers.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless current repository standards require it.

## Required Staging Location
All staged artifacts must live under:

`collaboration/workstreams/WP-0209/`

Expected staged paths may include:

- `collaboration/workstreams/WP-0209/proposed/resident_conversation_controls.md`
- `collaboration/workstreams/WP-0209/proposed/action_metadata.json`
- `collaboration/workstreams/WP-0209/proposed/src/estate/core/office_resident_actions.py`
- `collaboration/workstreams/WP-0209/proposed/tests/test_office_resident_actions.py`
- `collaboration/workstreams/WP-0209/install_manifest.json`
- `collaboration/workstreams/WP-0209/validation_notes.md`

## Required Controls to Stage
Stage controls for Alfred, Helen, and Resident Conversations only.

### Alfred
Proposed controls should include:

1. Start Alfred conversation
   - Create/open resident interaction session where supported.
   - Steward-confirmed local mutation.

2. Inspect Alfred resident surface
   - Show capabilities, authority categories, implementation status, and source artifacts.
   - Safe read-only.

3. Copy Alfred duty/status commands
   - Copy command text only.
   - Safe read-only.

4. Queue Alfred request
   - Draft/queue request through existing Alfred request path.
   - Steward-confirmed local mutation or authority-gated depending on target.
   - Does not execute work packages.

5. Inspect Alfred job/request
   - Safe read-only.

6. Cancel/retry job, staged design only
   - Only through existing Alfred policy surface and future confirmation.
   - Authority-gated.

### Helen
Proposed controls should include:

1. Inspect Helen resident surface
   - Safe read-only.

2. Copy Helen duty/status/authority commands
   - Copy-only.
   - Safe read-only.

3. Start Helen conversation, if supported
   - Steward-confirmed local mutation.

4. Draft HR/onboarding request
   - Steward-confirmed draft or authority-gated route depending on target.
   - Must not mutate personnel records directly.

### Resident Conversations
Proposed controls should include:

1. Start session
   - Steward-confirmed local mutation.

2. Open transcript
   - Safe read-only.

3. Export transcript
   - Local-only export with sensitivity warning.
   - Safe read-only or generated artifact update after confirmation.

4. Redact/forget with audit, staged design only
   - Steward-confirmed local mutation where existing support exists.
   - Must record audit reason and preserve auditability.

5. Draft promotion of outcome
   - Draft work-package proposal, validation follow-up, review request, or decision candidate from a conversation outcome.
   - Draft/proposal only.
   - Authority-gated where appropriate.

6. Inspect authority boundary
   - Show resident authority check result for selected action.
   - Safe read-only.

## Required Action Metadata
For each proposed control, include action metadata with:

- action ID
- label
- target tab/resident/session when applicable
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
- explicit resident authority boundary statement

Use WP-0118 and WP-0200 vocabulary.

## Required Safety Rules
The staged design must enforce or describe:

1. Resident conversation is not institutional decision-making by itself.
2. Residents may converse, inspect, summarize, draft, or request only within authority boundaries.
3. Queueing a resident request is not execution authority.
4. Conversation outcome promotion creates drafts/proposals only unless routed through approved authority.
5. Redaction/forget requires confirmation, reason, and audit trail.
6. Transcript exports include sensitivity warning and remain local-only.
7. Alfred/Helen controls must not silently execute work packages or mutate governance/personnel state.

## Required Install Manifest
Create:

`collaboration/workstreams/WP-0209/install_manifest.json`

The manifest must follow the WP-0112 standard and include staged artifact paths, intended final install paths, expected modified files, manual/automated install steps, validation commands, rollback notes, dependency assumptions, conflict risks, generated artifacts to ignore/review, authority/review requirements, and `staged_work_is_installed: false`.

## Conflict Surface Declaration
Expected conflict surface:

- `src/estate/core/steward_command_center.py` — likely future UI integration target
- `src/estate/core/resident_interaction.py` — possible helper reference or future integration target
- `src/estate/core/resident_conversation_sessions.py` — possible helper reference
- `src/estate/core/resident_authority.py` — possible authority helper reference
- `src/estate/core/resident_presence.py` — possible presence helper reference
- `src/estate/core/alfred.py` — possible request/job helper reference
- `src/estate/core/alfred_duty.py` — possible duty helper reference
- `src/estate/core/helen_duty.py` — possible duty helper reference
- `src/estate/cli/main.py` — possible command registry reference
- `tests/test_resident_interaction.py` — likely future test reference
- `tests/test_steward_command_center.py` — likely future integration tests

Risk class: medium/high, because future install likely touches shared Office UI and resident interaction surfaces.

Packages that can run in parallel:

- Other `PARALLEL-STAGED` tab-control packages that stage under their own workstream directories.

Packages that should complete before install:

- WP-0118 complete and merged.
- WP-0200 reviewed or installed as action framework foundation.
- Any active CA4 repair touching Office UI, Alfred/Helen, or resident interaction surfaces reviewed for conflicts.

## Required Tests / Staged Tests
Provide staged tests or a test plan proving:

- Inspect resident surface and authority boundary are safe read-only.
- Copy duty/status commands are copy-only.
- Start session requires Steward-confirmed local mutation.
- Queue resident request does not execute work packages.
- Transcript export includes sensitivity warning and local-only/no-upload posture.
- Redact/forget requires confirmation, reason, and audit trail.
- Outcome promotion is draft/proposal only and authority-gated where appropriate.

## Required Validation Commands
Run or document equivalent staged validation:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0209 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0209 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If WP-0209 has no validation recipe yet because staged packages are not fully integrated into validation, document that limitation in the completion receipt.

## Required Outputs
Create or update:

- `collaboration/workstreams/WP-0209/install_manifest.json`
- staged proposed Resident Conversation control artifacts under `collaboration/workstreams/WP-0209/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0209_codex_done.json`

Do not install staged files into active runtime paths in this package.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0209_codex_done.json`

It must include work_package_id, codex_status, completed_at, branch, pull_request_url or reason, summary, workstream mode, staged artifact paths, install manifest path, intended install paths, conflict risks, controls staged by resident/tab, files changed, tests/validation run, known limitations, `staged_work_is_installed: false`, `ready_for_ca_review: true`, and `merge_authority: ca_verified_auto_merge_allowed`.

## Acceptance Criteria
WP-0209 is complete when staged Resident Conversation control artifacts exist, every staged control has action metadata/authority classification/confirmation behavior/local-only posture, resident authority boundaries are explicit, an install manifest exists, risks are explicit, tests or staged test plan exist, completion receipt exists, and active Office runtime files are not directly installed.

## Merge Class
Class A if this package only creates staged workstream artifacts, install manifest, tests/test plan, and completion receipt.

Escalate to Class B if active runtime files are modified or the package attempts to install the controls directly.
