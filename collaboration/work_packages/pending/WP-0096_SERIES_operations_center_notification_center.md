# SERIES TASK WP-0096 — Operations Center Notification Center

## Codex Command
Read `collaboration/work_packages/pending/WP-0096_SERIES_operations_center_notification_center.md` and do exactly what it says.

## Mode

SERIES

## Mission
Implement the Operations Center Notification Center as the centralized Steward-facing surface for reviewing operational notifications from existing Estate systems without creating a parallel notification source.

## Background

This work package remains a pending backlog item. WP-0102 added this background section to align the file with the Codex Task Template Standard while preserving the original mission and scope.

## Scope
Build on the Operations Center Layout Framework, Status Bar, Operator Activity Stream, Service Health Registry, Validation Metrics, Mission Control, mailbox events, HR events, and existing Notification Center concepts.

The Notification Center should aggregate existing notification-like artifacts where available, including:

- service health warnings
- validation observations and defects
- worker/runtime alerts
- Mission Control recommendations
- mailbox or HR notices
- Steward recall state
- operations readiness warnings
- completion/review-ready signals

The interface should support:

- read/unread or acknowledged/unacknowledged state where appropriate
- severity levels
- filtering by source/subsystem
- links to authoritative artifacts
- quiet refresh
- integration with the Operations Center Status Bar
- integration with the Operator Activity Stream

## Behavior Requirements
- The Notification Center is an aggregator, not the authoritative source.
- Do not fabricate notifications.
- Missing upstream data should show as unavailable, not fail.
- Notifications must link back to source artifacts where available.
- Acknowledgment state must not mutate authoritative source events unless an existing convention already supports that.
- Respect operator verbosity and filter settings where available.
- Preserve Steward authority boundaries and recall semantics.

## Constraints
Do not create a new notification transport. Do not send external notifications. Do not duplicate Gotify or recall behavior. Do not bypass existing Notification Router semantics. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify aggregation from available sources, missing-source handling, severity filtering, acknowledgment behavior, status bar integration, activity stream integration, source-link integrity, and quiet refresh behavior.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0096_codex_done.json` using the standard completion schema.


## WP-0102 Template Retrofit Notice

This section was added by WP-0102 as a mechanical template retrofit. It preserves the original mission and scope above. This pending package remains authored and queued; it is not implemented, validated, operationally validated, approved, or institutionalized by this retrofit.

## Out of Scope

- Do not change the original mission or core scope of WP-0096.
- Do not treat this pending package as already implemented or validated.
- Do not modify `estate_ledger/ledger.md` or `development/devlog.md` unless a future package explicitly authorizes it.
- Do not change governance authority, validation authority, merge authority, or automatic approval behavior.

## Required Behavior

- Execute the original package behavior described above when this package is later implemented.
- Preserve local-first operation unless the Steward explicitly authorizes networked behavior.
- Leave auditable evidence for every check, limitation, and generated artifact.
- Report known limitations explicitly instead of implying production readiness.

## Safety and Authority Constraints

- Do not change governance authority.
- Do not change validation authority.
- Do not automatically approve work packages.
- Do not modify `estate_ledger/ledger.md`.
- Do not modify `development/devlog.md`.
- Do not weaken Git safety behavior.
- Do not stage broad paths.
- Preserve local-first operation unless explicitly authorized.

## Required CLI / Command Surface

Use the command surfaces already named in this package. If implementation changes introduce or alter CLI behavior, document exact command names and acceptable local-first alternatives in the completion receipt.

## Required Artifacts

- Implement the artifacts already specified by this pending package.
- Create `collaboration/work_packages/completions/WP-0096_codex_done.json`.
- Add or update the registered validation recipe for `WP-0096` unless this file explicitly states that the recipe is not applicable.

## Validation Recipe Requirement

Add or update the validation recipe for WP-0096. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure future validation can evaluate this package with:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0096 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement

Create `collaboration/work_packages/completions/WP-0096_codex_done.json` with at least:

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
- validation recipe status or not-applicable rationale
- production readiness command status if run
- final command surfaces or Steward commands when applicable

Missing receipt metadata blocks production-readiness status under the WP-0095 validation standard.

## Production Readiness Requirement

This package must remain compatible with the production-readiness validation loop. When practical, run or document the equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0096 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If readiness remains blocked by intentionally pending work, missing external dependencies, or a documented recipe exception, record that limitation in the completion receipt rather than claiming readiness.

## Demonstration Requirements

Document the exact commands run and observed status in the completion receipt. Include evidence for implementation-time checks, validation recipe behavior where applicable, and production-readiness compatibility.

## Merge Class
Class A unless notification authority, external delivery, or recall semantics are changed; escalate to Class B if governance semantics are altered.
