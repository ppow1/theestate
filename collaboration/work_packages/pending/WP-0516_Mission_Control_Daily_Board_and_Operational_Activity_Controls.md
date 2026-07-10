# WP-0516 - Mission Control, Daily Board, and Operational Activity Controls

Status: Proposed
Priority: High
Owner: Chief Architect #5
Classification: Estate Internal

## Mission

Convert Mission Control, Daily Board, and Operational Activity from high-level views into working command surfaces.

## Required Controls

- refresh live operational state;
- open active item details;
- acknowledge attention items;
- route to the controlling workspace;
- record existing operations decisions;
- request briefings;
- promote or defer actionable items through canonical mechanisms;
- open related evidence and artifacts;
- filter by state, owner, priority, and attention requirement.

## Boundaries

Reuse existing Operations Manager, Traffic Controller, briefing, notification, and activity runtimes. Do not create a second operations queue, event system, or authority layer. Recommendations remain evidence, not decisions.

## Functional Standard

Every control must invoke a canonical handler, produce durable evidence or a legitimate state change, refresh the relevant payload, and render a truthful completed, blocked, or failed result.

## Testing

Prove browser-to-handler-to-state-to-render behavior for refresh, acknowledgement, routing, operations decisions, briefing requests, defer/promotion, artifact opening, and filtering.

## Acceptance Criteria

1. Mission Control and Daily Board support real operational actions.
2. Attention items can be acknowledged and routed.
3. Operations decisions use existing governed contracts.
4. Evidence links and failures are visible.
5. No display-only element is mislabeled as a control.
6. Focused tests and WP-0516 validation pass.

## Completion Receipt

```text
collaboration/work_packages/completions/WP-0516_codex_done.json
```

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0516_Mission_Control_Daily_Board_and_Operational_Activity_Controls.md and do exactly what it says.
```
