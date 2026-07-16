# Estate PTM Budget Cost Approval and Reconciliation Contract

## Authority and scope

This implementation-ready planning contract satisfies FIN-PTM-001 for future financial projection files. It extends the frozen CORE-PTM-003B financial projection without creating local financial authority decisions or a second governance path.

## Financial item

```yaml
financial_item:
  financial_item_id: string
  project_id: string | null
  task_id: string | null
  budget_ref: object | null
  cost_ref: object | null
  approval_refs: [object]
  reconciliation_refs: [object]
  amount: number | null
  currency: string
  cost_category: estimate | requested | approved_budget | actual | variance | avoided_cost
  authority_refs: [object]
  source_event_ids: [string]
  warnings: [string]
```

## Estimate, request, approval, and actual records

- Estimates record expected amount, range, basis, provider/lane option, and confidence.
- Requests record requested amount, purpose, requester, and required approval authority.
- Approvals record approver authority, approved cap, conditions, expiration, and source evidence.
- Actuals record imported provider cost, telemetry-derived local cost, or accepted manual actual with source references.

## Routing comparison

Routing comparisons may compare Codex, approved provider, and local compute cost models only as advisory evidence:

```yaml
routing_cost_comparison:
  comparison_id: string
  task_id: string
  options:
    - lane_ref: object
      estimated_amount: number | null
      currency: string
      confidence_label: observed | telemetry_derived | estimated | unknown
      basis_refs: [object]
  recommendation: string | null
  advisory_only: true
  warnings: [string]
```

Traffic Controller, Operations, Steward, Chief Architect, and budget gates retain their existing authority boundaries.

## Reconciliation rules

- Reconciliation links estimates, requests, approvals, actuals, and accepted work evidence.
- Variance is actual minus approved budget when both are known.
- Unknown actuals remain unknown; projections must not infer actual spend from estimates.
- Local cost avoidance is reported only when both baseline and local-cost basis are documented.
- Reconciled records preserve all source events and approval refs.

## Boundary rules

- No financial projection grants spend authority.
- No local financial authority decisions are introduced.
- No production PTM code is authorized by this contract.
- No second dispatch queue, second registry, second scheduler, or new governance authority is introduced.
