# Check for Updates v1

Status: Implemented local-first synchronization mechanism  
Classification: Estate Internal

## Purpose

Check for Updates generates a role-aware briefing before a worker, office occupant, or implementation agent continues work. It answers: what changed that this actor needs to know now?

This is not onboarding. Onboarding teaches the Estate from the beginning; Check for Updates refreshes awareness of relevant changes in local Estate artifacts.

## Actor-Aware Synchronization

The command normalizes supported actor names and selects update categories relevant to the caller. Supported initial categories are:

- `office.chief_architect`, `office.chief_architect_1`, `office.chief_architect_2`, `office.chief_architect_3`
- `alfred`
- `worker.audit`
- `worker.implementation`
- `worker.documentation`
- `worker.discovery`
- `steward`
- `general`

Obvious aliases such as `ca2`, `audit`, and `implementation` are normalized. This does not create new offices or permanent identity governance.

## Temporary Visibility Placeholder

The current implementation uses a conservative placeholder visibility model only so reports can filter categories before HR/security governance exists:

- `general` receives `public` material.
- implementation, documentation, audit, discovery workers, Alfred, and Chief Architect actors receive `estate_internal` material.
- `steward` receives `restricted` visibility.

This is not final security clearance policy. Helen/HR, Ingrid/boundary governance, or future authorized governance may replace this model. The command must not be treated as authoritative access control.

## Input Sources

The mechanism scans local artifacts when present:

- `Architecture/ADR/**/*.md`
- `docs/governance/**/*.md`
- `docs/collaboration/**/*.md`
- `docs/operations/**/*.md`
- `operations/**/*.md`
- `collaboration/messages/*.json`
- `collaboration/status/*.json`
- `runtime/collaboration/events/events.jsonl`
- `runtime/operations/operations_board.json`
- `runtime/capabilities/capability_lifecycle_report.json`
- `runtime/dependencies/dependency_graph.json`
- `runtime/validation/operational_validation_report.json`
- `archive/institutional_memory/**/*.md`

Missing artifacts and malformed JSON/JSONL are warnings, not fatal errors.

## Outputs

Each run writes:

- `runtime/updates/check_updates_latest.json`
- `operations/updates/check_updates_latest.md`

Parent directories are created as needed.

## CLI Usage

```bash
PYTHONPATH=src python -m estate.cli.main check-updates
PYTHONPATH=src python -m estate.cli.main check-updates --actor office.chief_architect_2
PYTHONPATH=src python -m estate.cli.main check-updates --actor alfred
PYTHONPATH=src python -m estate.cli.main check-updates --actor worker.audit
PYTHONPATH=src python -m estate.cli.main check-updates --actor worker.implementation
PYTHONPATH=src python -m estate.cli.main check-updates --actor office.chief_architect_2 --json
```

## Message Handling

Mailbox handling is intentionally simple. Messages in `collaboration/messages/*.json` are surfaced when `destination`, `to`, `recipient`, or `target` exactly matches the normalized actor or actor family. This does not redesign mailbox identity resolution.

## Limitations and Open Questions

- Visibility filtering is a temporary placeholder, not HR/security policy.
- Actor normalization is intentionally small and not permanent identity governance.
- The command points to relevant artifacts; it is not a fixed universal reading checklist.
- It does not promote capabilities, create lifecycle states, redefine onboarding, or alter the Collaboration Layer.
- Future governance should decide final clearance levels, HR authority, and permanent actor classification.
