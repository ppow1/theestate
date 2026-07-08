# WP-EXECUTION-PROVIDER-ROUTING-001 - SUPERSEDED

Status: Superseded
Priority: None
Owner: Chief Architect / Steward
Classification: Estate Internal
Created: 2026-07-08
Superseded: 2026-07-08

## Superseded By

```text
docs/governance/workers/WP-EXECUTION-PROVIDER-ROUTING-RECOMMENDATIONS-001.md
```

## Reason

This package was paused before execution because the original title and wording used `routing policy` language that could imply autonomous scheduling, dispatch, assignment, or provider choice before the Estate has finalized those boundaries.

Chief Architect #5 and Chief Architect #6 agreed that this layer should be framed as recommendation metadata only.

The replacement package uses the safer title:

```text
Execution Provider Routing Recommendations
```

The replacement package explicitly states that it:

- does not schedule work
- does not dispatch work
- does not assign workers
- does not execute providers
- does not implement autonomous provider choice
- does not replace the Traffic Controller / Operations Manager
- does not replace future mechanical coordination layers
- does not bypass Steward, Ingrid, Audit, or Validation

## Instruction

Do not execute this superseded package.

Use the replacement package instead.
