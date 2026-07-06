# PARALLEL-STAGED TASK WP-0206 — Mailboxes, Recalls, and Notifications Controls

## Codex Command
Read collaboration/work_packages/pending/WP-0206_PARALLEL_STAGED_mailboxes_recalls_notifications_controls.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Design and stage safe Mailboxes, Recalls, and Notifications controls for the Office of the Steward without directly installing changes into active Office runtime files.

This package implements the WP-0118-F4 follow-up slice: Mailboxes, Recalls, and Notifications Controls. It must produce staged, reviewable artifacts under `collaboration/workstreams/WP-0206/`, including proposed UI/control metadata, proposed code or patch structure, tests or staged test plan, validation notes, and an install manifest.

These tabs should become safe human-workflow control surfaces for inspection, local acknowledgement, reply/request drafting, export, and routing while clearly distinguishing local UI/runtime state from authoritative source closure.

## Background
WP-0118 identified Mailboxes, Recalls, and Notifications as related Office workflow surfaces. Proposed verbs include opening mailbox/message/recall/notification details, inspecting source artifacts, local acknowledgement, drafting replies, routing to residents or authority paths, exporting snapshots, and creating follow-up drafts.

WP-0200 stages the shared Office action framework foundation. WP-0206 should align with the WP-0200 staged vocabulary where practical, but must not assume WP-0200 is already installed.

Because Chief Architect #4 and other workers may be touching Office UI, mailbox, recall, or notification files concurrently, WP-0206 follows the WP-0112 parallel workstream standard. This package stages proposed implementation rather than modifying active Office runtime files directly.

## Number Allocation
This package uses the temporary active authoring block assigned by the Steward to Chief Architect #3: WP-0200 through WP-0250.

Do not renumber this package based on GitHub search results.

## Scope
Create staged implementation artifacts for Mailboxes, Recalls, and Notifications controls.

In scope:

1. Inspect current Mailboxes, Recalls, and Notifications surfaces in the Office implementation.
2. Inspect existing mailbox index, collaboration message, notification router, recall, operations notification center, and acknowledgement-related modules/artifacts.
3. Stage proposed controls for Mailboxes, Recalls, and Notifications only.
4. Align action metadata with WP-0200 staged action vocabulary where practical.
5. Create staged tests or a test plan.
6. Create `collaboration/workstreams/WP-0206/install_manifest.json`.
7. Create `collaboration/work_packages/completions/WP-0206_codex_done.json`.

## Out of Scope
Do not directly modify active Office runtime files in this package.

Do not delete messages, recalls, notifications, or source artifacts.

Do not treat local acknowledgement as authoritative closure unless an existing authority route explicitly updates the authoritative source.

Do not bypass Steward authority, Chief Architect review, resident action authority, validation, governance, or merge authority.

Do not implement controls for Work Packages, Validation, Mission Control, Projects, Roadmap, Parking Lot, Residents, AI Services, Settings, Help, or About except where needed as read-only references.

Do not add cloud services, external API calls, telemetry, or remote workers.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless current repository standards require it.

## Required Staging Location
All staged artifacts must live under:

`collaboration/workstreams/WP-0206/`

Expected staged paths may include:

- `collaboration/workstreams/WP-0206/proposed/mailboxes_recalls_notifications_controls.md`
- `collaboration/workstreams/WP-0206/proposed/action_metadata.json`
- `collaboration/workstreams/WP-0206/proposed/src/estate/core/office_communications_actions.py`
- `collaboration/workstreams/WP-0206/proposed/tests/test_office_communications_actions.py`
- `collaboration/workstreams/WP-0206/install_manifest.json`
- `collaboration/workstreams/WP-0206/validation_notes.md`

## Required Controls to Stage
Stage controls for Mailboxes, Recalls, and Notifications only.

### Mailboxes
Proposed controls should include:

1. Open mailbox
   - Inspect mailbox index and source artifacts.
   - Safe read-only.

2. Inspect message
   - Open/read message content, sender, recipient, status, source path, acknowledgement requirements, and waiting state where available.
   - Safe read-only.

3. Draft reply
   - Create or preview a reply draft using existing communication bus/message conventions.
   - Steward-confirmed local mutation.
   - Does not send or mark complete without authority route.

4. Local acknowledge
   - Stage design for local acknowledgement where existing support exists.
   - Must be labeled local UI/runtime state unless authoritative source is updated through approved route.
   - Steward-confirmed local mutation.

5. Route to resident or review queue
   - Draft/queue route request through existing authority path.
   - Authority-gated.

6. Export mailbox snapshot
   - Local-only export of selected mailbox state and source references.
   - Safe read-only or generated artifact update with sensitivity warning.

### Recalls
Proposed controls should include:

1. Inspect recall
   - Open recall detail, origin/requester, lifecycle, transport, acknowledgement, timestamps, and source links.
   - Safe read-only.

2. Copy delivery command
   - Copy local command where available.
   - Copy-only by default.

3. Local acknowledge recall
   - Steward-confirmed local mutation where supported.
   - Must distinguish acknowledgement from decision/closure.

4. Request Steward decision
   - Draft/queue decision request through existing decision queue or authority route.
   - Authority-gated.

5. Export recall audit bundle
   - Local-only bundle with sensitivity warning.

### Notifications
Proposed controls should include:

1. Filter notifications
   - Safe read-only.

2. Inspect notification source
   - Open source artifact or source report.
   - Safe read-only.

3. Local acknowledge notification
   - Steward-confirmed local mutation.
   - Must label local acknowledgement semantics.

4. Bulk local acknowledge low-severity notifications, staged design only
   - Requires second confirmation, affected-item summary, audit/reversibility note.
   - Steward-confirmed local mutation.

5. Create follow-up draft
   - Draft work package, validation observation, mailbox reply, or review request from a notification.
   - Steward-confirmed local mutation or authority-gated route depending on target.

## Required Action Metadata
For each proposed control, include action metadata with:

- action ID
- label
- target tab
- target mailbox/message/recall/notification when applicable
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
- explicit local-vs-authoritative-state semantics

Use WP-0118 and WP-0200 vocabulary.

## Required Safety Rules
The staged design must enforce or describe:

1. Local acknowledgement is not source closure unless explicitly routed through authoritative source update.
2. Draft reply is not sent reply.
3. Route request is not action completion.
4. Recall acknowledgement is not recall decision unless explicitly authorized.
5. Bulk controls summarize all affected items and require second confirmation.
6. Export bundles include sensitivity warnings and remain local-only.
7. No destructive deletion controls are introduced.

## Required Install Manifest
Create:

`collaboration/workstreams/WP-0206/install_manifest.json`

The manifest must follow the WP-0112 standard and include staged artifact paths, intended final install paths, expected modified files, manual/automated install steps, validation commands, rollback notes, dependency assumptions, conflict risks, generated artifacts to ignore/review, authority/review requirements, and `staged_work_is_installed: false`.

## Conflict Surface Declaration
Expected conflict surface:

- `src/estate/core/steward_command_center.py` — likely future UI integration target
- `src/estate/core/mailbox_index.py` — possible read-only/helper reference
- `src/estate/core/collaboration_messages.py` — possible draft/reply helper reference
- `src/estate/core/notification_router.py` — possible read-only/helper reference
- `src/estate/core/operations_notification_center.py` — possible acknowledgement helper reference
- `src/estate/core/decision_queue.py` — possible decision request helper reference
- `src/estate/cli/main.py` — possible command registry reference
- `tests/test_steward_command_center.py` — likely future integration tests

Risk class: medium/high, because future install likely touches shared Office UI and communication/notification surfaces.

Packages that can run in parallel:

- Other `PARALLEL-STAGED` tab-control packages that stage under their own workstream directories.

Packages that should complete before install:

- WP-0118 complete and merged.
- WP-0200 reviewed or installed as action framework foundation.
- Any active CA4 repair touching Office UI, mailboxes, recalls, notifications, or decision queue reviewed for conflicts.

## Required Tests / Staged Tests
Provide staged tests or a test plan proving:

- Mailbox open/message inspect actions are safe read-only.
- Draft reply is a preview/local mutation and not a sent message.
- Local acknowledgement is clearly labeled as local unless authoritative update exists.
- Recall inspect/copy command actions are safe read-only.
- Recall decision request is authority-gated and not a decision.
- Notification bulk acknowledgement requires second confirmation and affected-item summary.
- Export bundles include sensitivity warning and local-only/no-upload posture.
- No deletion/destructive control is present.

## Required Validation Commands
Run or document equivalent staged validation:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0206 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0206 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If WP-0206 has no validation recipe yet because staged packages are not fully integrated into validation, document that limitation in the completion receipt.

## Required Outputs
Create or update:

- `collaboration/workstreams/WP-0206/install_manifest.json`
- staged proposed Mailboxes, Recalls, and Notifications control artifacts under `collaboration/workstreams/WP-0206/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0206_codex_done.json`

Do not install staged files into active runtime paths in this package.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0206_codex_done.json`

It must include work_package_id, codex_status, completed_at, branch, pull_request_url or reason, summary, workstream mode, staged artifact paths, install manifest path, intended install paths, conflict risks, controls staged by tab, files changed, tests/validation run, known limitations, `staged_work_is_installed: false`, `ready_for_ca_review: true`, and `merge_authority: ca_verified_auto_merge_allowed`.

## Acceptance Criteria
WP-0206 is complete when staged Mailboxes, Recalls, and Notifications control artifacts exist, every staged control has action metadata/authority classification/confirmation behavior/local-only posture, local-vs-authoritative semantics are explicit, an install manifest exists, risks are explicit, tests or staged test plan exist, completion receipt exists, and active Office runtime files are not directly installed.

## Merge Class
Class A if this package only creates staged workstream artifacts, install manifest, tests/test plan, and completion receipt.

Escalate to Class B if active runtime files are modified or the package attempts to install the controls directly.
