# Governed Provider Scheduler

WP-0541 adds a file-backed scheduling coordinator at `runtime/engineering_scheduler/`.

The scheduler consumes existing worker assignment, provider health, provider capacity, and routing recommendation evidence. It does not replace provider routing, provider registry, Dispatch, execution sessions, or the Traffic Controller authority path.

## Commands

- `engineering-scheduler enqueue --assignment-id <id>` adds an approved worker assignment idempotently.
- `engineering-scheduler recommend --json` explains eligible and excluded assignments.
- `engineering-scheduler reserve --ttl-minutes 30 --json` creates a bounded reservation lease.
- `engineering-scheduler release --assignment-id <id>` marks work as ready for the existing Dispatch path.
- `engineering-scheduler defer --assignment-id <id> --reason <reason>` records bounded retry/deferment evidence.
- `engineering-scheduler pause|resume --reason <reason>` controls emergency scheduling posture.
- `engineering-scheduler exclude-provider|include-provider --provider-id <id> --reason <reason>` records reversible provider exclusions.
- `engineering-scheduler explain --assignment-id <id> --json` provides assignment-level decision rationale.
- `engineering-scheduler report` writes Office-consumable report artifacts.

## Authority boundary

Reservations are capacity holds only. Every release records `dispatch_required: true`; the existing Dispatch runtime remains the only execution release path.
