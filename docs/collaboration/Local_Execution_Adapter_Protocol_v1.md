# Local Execution Adapter Protocol v1

Status: Version 1 Infrastructure Pattern
Short Name: LEAP v1
Owner: Chief Architect
Operational Coordinator: Alfred / Chief of Staff
Boundary Authority: Privacy and Boundary Office
Classification: Estate Internal

## Purpose

The Local Execution Adapter Protocol provides one reusable pattern for executing authoritative local Estate capabilities from Collaboration Layer requests.

GitHub carries intent.

The local Estate performs local-only authority work.

GitHub carries approved non-private result state back to the institution.

Audit Worker v1 is the first implementation of this pattern.

## Core Principle

Architect a protocol once. Implement adapters many times.

The Estate should not invent a different request and result lifecycle for every local capability.

Protocols stay stable.
Adapters specialize.

## Constitutional Position

LEAP is not a new Office.

It is an implementation pattern for the Collaboration Layer and Communication Bus.

Existing Office ownership remains:

- Alfred owns routing and orchestration.
- The relevant capability owner owns the local authority work.
- Privacy and Boundary Office owns outbound classification and promotion.
- Audit validates where appropriate.
- Steward remains final authority for reserved decisions.

## Canonical Flow

1. Worker creates request.
2. Request enters pending queue.
3. Local adapter claims request.
4. Adapter validates request.
5. Adapter executes local authoritative command.
6. Adapter captures result.
7. Adapter publishes approved non-private result.
8. Adapter archives request.
9. Other workers read result from repository.

## Lifecycle

Every adapter follows this lifecycle:

- pending
- active
- validate
- execute
- capture
- publish
- archive
- failed

Only the execute step changes by adapter type.

## Generic Request Fields

- request_id
- adapter
- requested_by
- work_package_id
- target_commit
- priority
- classification
- reason
- requested_at
- expected_checks
- promotion_context
- parameters

## Generic Result Fields

- request_id
- adapter
- status
- local_commit
- branch
- started_at
- finished_at
- command_run
- exit_code
- summary
- warnings
- errors
- artifacts
- history_drift_detected
- follow_up_required
- classification

## Adapter Families

Initial adapter family:

- audit

Future adapter families may include:

- discovery
- inventory
- ollama
- comfyui
- whisper
- python
- alfred
- local_4090

## Privacy Rule

Local execution may produce private or Local Only material.

Adapters must not publish private local artifact details unless classified and approved.

Result files should contain enough information for institutional coordination without leaking private local-only content.

## History Rule

Adapters and routine workers must not directly edit:

- estate_ledger/ledger.md
- development/devlog.md

History drift may be reported.

History repair must use the approved history queue and drain workflow.

## Audit Adapter v1

Audit Adapter v1 runs:

    .\estate.bat audit

It publishes:

- pass / fail / error status
- branch
- commit SHA
- timestamps
- exit code
- summary
- full audit output where safe
- history drift indicator

## Future Automation

The manual one-shot worker is intentionally first.

Later LEAP workers may become scheduled tasks, local watchers, or Alfred-controlled executors once the pattern is stable.
