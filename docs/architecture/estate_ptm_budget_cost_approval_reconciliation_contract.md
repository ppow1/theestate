# Estate PTM Budget Cost Approval and Reconciliation Contract

Status: Draft implementation-preparation artifact for PTM-05 Gate C/D
Campaign: PTM-05 — Scheduling utilization financials and KPIs
Package: FIN-PTM-001
Date: 2026-07-16

## Authority and scope

This implementation-ready planning contract satisfies FIN-PTM-001 for future financial projection files. It refines, but does not redefine, the frozen CORE-PTM-003B financial projection fields: `financial_item_id`, `project_id`, `task_id`, `budget_ref`, `cost_ref`, `approval_refs`, `reconciliation_refs`, `amount`, `currency`, `cost_category`, `authority_refs`, `source_event_ids`, and `warnings`.

The contract is source-backed by the accepted PTM baseline, the PTM parallel campaign plan, the dependency manifest entry requiring FIN-PTM-001 to follow CORE-PTM-003B, WP-0659 financial-boundary guidance, and the KPI/financial/utilization catalog. It is documentation-only and does not authorize production PTM code, mutate authoritative source records, grant budget authority, approve spend, select a provider, create local financial authority decisions, create a second dispatch queue, create a second registry, create a second scheduler, or introduce a new governance authority.

## Shared financial projection envelope

Future financial projection records MUST use the shared PTM projection envelope from CORE-PTM-003A/003B. The `aggregate_type` for these records is `financial`, and the `aggregate_id` is the canonical `financial_item_id` minted under the canonical financial-item namespace.

```yaml
financial_projection_record:
  envelope: ptm_projection_record
  financial_item_id: string
  project_id: string | null
  task_id: string | null
  budget_ref: object | null
  cost_ref: object | null
  approval_refs: [object]
  reconciliation_refs: [object]
  amount: number | null
  currency: string
  cost_category: estimate | requested_budget | approved_budget | authorized_spend | committed_cost | actual_cost | accepted_cost | forecast_at_completion | variance | remaining_budget | contingency | avoided_cost
  authority_refs: [object]
  source_event_ids: [string]
  warnings: [string]
```

### Field requirements

| Field | Requirement |
| --- | --- |
| `financial_item_id` | Stable canonical ID for the financial aggregate; it is not a budget decision or payment authorization. |
| `project_id` / `task_id` | Explicit links to source-backed PTM project/task aggregates; at least one SHOULD be present for current-state records unless the financial item is a portfolio-level reserve. |
| `budget_ref` | Source reference to the budget request, approved cap, reserve, or budget gate evidence when known. |
| `cost_ref` | Source reference to provider charge, telemetry-derived local cost, manual actual, or accepted cost evidence when known. |
| `approval_refs` | Source-backed approval, waiver, or denial references. Empty means no approval evidence is present and MUST NOT be interpreted as approval. |
| `reconciliation_refs` | Source-backed reconciliation report, calculation, or review references. Empty means not reconciled. |
| `amount` | Decimal amount for the category. Unknown amounts remain `null`; projections MUST NOT copy an estimate into an actual. |
| `currency` | ISO 4217 currency code where money is involved; use `N/A` only for non-money advisory records such as pure compute-hour comparisons. |
| `cost_category` | Closed category defining how the amount may be interpreted; categories may not be overloaded. |
| `authority_refs` | References proving who may request, approve, authorize, or accept the category. They preserve authority evidence; they do not create authority. |
| `source_event_ids` | Ordered event IDs supporting the projected value. Current-state records require at least one supporting event. |
| `warnings` | Missing approval, stale evidence, cross-source conflict, unknown currency, manual actual, or authority-boundary warnings. |

## Estimate, request, approval, authorization, actual, and acceptance records

Financial projection builders MAY expose typed records derived from the shared financial projection. These typed records are deterministic read models only.

### Estimate record

```yaml
financial_estimate:
  financial_item_id: string
  estimate_id: string
  project_id: string | null
  task_id: string | null
  amount_low: number | null
  amount_expected: number | null
  amount_high: number | null
  currency: string
  provider_or_lane_option: string | null
  basis_label: observed | telemetry_derived | catalog_rate | human_estimate | unknown
  confidence_label: high | medium | low | unknown
  basis_refs: [object]
  source_event_ids: [string]
  warnings: [string]
```

Estimates record expected amount, range, basis, provider/lane option, confidence, and source evidence. Estimates are advisory until connected to a separate budget request, approval, and spend authorization.

### Budget request record

```yaml
budget_request:
  financial_item_id: string
  request_id: string
  requested_amount: number | null
  currency: string
  purpose: string
  requester_ref: object
  required_approval_authority_refs: [object]
  linked_estimate_ids: [string]
  status: draft | submitted | withdrawn | denied | approved | superseded
  source_event_ids: [string]
  warnings: [string]
```

Requests record requested amount, purpose, requester, and required approval authority. A submitted request is not approval and does not make Dispatch ready.

### Budget approval and spend authorization record

```yaml
budget_approval:
  financial_item_id: string
  approval_id: string
  request_id: string | null
  approver_authority_refs: [object]
  approved_cap: number | null
  currency: string
  conditions: [string]
  expires_at: string | null
  approval_status: approved | denied | expired | revoked | superseded
  spend_authorization_ref: object | null
  source_event_ids: [string]
  warnings: [string]
```

Approvals record approver authority, approved cap, conditions, expiration, and source evidence. Spend authorization is separate from approval when existing gates require both. Helen and Grace do not approve budgets under this contract.

### Actual and accepted cost record

```yaml
actual_cost_record:
  financial_item_id: string
  actual_id: string
  amount: number | null
  currency: string
  actual_source_type: provider_import | telemetry_derived_local_compute | subscription_allocation | electricity_allocation | storage_allocation | manual_actual | other
  cost_center_ref: object | null
  accepted_cost_ref: object | null
  accepted_work_refs: [object]
  source_refs: [object]
  source_event_ids: [string]
  warnings: [string]
```

Actuals record imported provider cost, telemetry-derived local cost, allocation-derived cost, or accepted manual actual with source references. Accepted cost requires accepted work evidence or an explicit authority reference; incurred cost alone is not institutional acceptance.

## Routing cost comparison

Routing comparisons may compare Codex, approved provider, and local compute cost models only as advisory evidence. They do not select a lane, assign work, override dispatch readiness, or authorize spend.

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
      capacity_or_schedule_refs: [object]
      budget_gate_refs: [object]
  recommendation: string | null
  advisory_only: true
  source_event_ids: [string]
  warnings: [string]
```

Provider recommendations remain advisory evidence. Traffic Controller, Operations, Steward, Chief Architect, dispatch readiness gates, and existing budget gates retain their authority boundaries.

## Reconciliation rules

1. Reconciliation links estimates, requests, approvals, authorizations, committed costs, actuals, accepted work, and accepted cost evidence by explicit IDs or source references.
2. Variance is `actual_cost - approved_budget` when both are known. If approved budget is absent, publish `variance` as unknown with a warning rather than comparing to an estimate.
3. Forecast variance is `forecast_at_completion - approved_budget` when both are known.
4. Remaining budget is `approved_budget - committed_cost - actual_cost` when all participating values share currency and allocation scope.
5. Unknown actuals remain unknown; projections MUST NOT infer actual spend from estimates, provider selection, dispatch state, or elapsed time.
6. Local cost avoidance is reported only when both baseline external cost and local-cost basis are documented and comparable.
7. Subscription, electricity, storage, licensing, hardware depreciation, oversight time, rework, failed-branch cost, materials, and miscellaneous allocations MUST preserve allocation method and source reference.
8. Reconciled records preserve all source events, approval references, warnings, and conflicting source evidence.
9. A reconciliation projection is not acceptance of work, approval of spend, or correction of authoritative source records.

## Authority and boundary rules

- No financial projection grants spend authority, approval authority, dispatch authority, validation acceptance, or merge authority.
- No local financial authority decisions are introduced; Codex-only routing is preserved for this cycle.
- Helen and Grace may view or summarize financial state only when future UI packages expose it; they may not approve budgets unless a separate accepted authority change says so.
- Budget approval, spend authorization, Traffic Controller/Operations routing, Steward/Chief Architect acceptance, and Dispatch readiness remain separate gates.
- Missing approval evidence MUST fail closed by leaving approval unknown/absent and emitting a warning.
- No production PTM code is authorized by this contract.
- No second dispatch queue, second registry, second scheduler, or new governance authority is introduced.

## Validation expectations for future implementation

Future implementation and TEST-PTM packages should validate this contract with fixtures proving:

- financial projections replay deterministically from the same event inputs;
- estimates, requests, approvals, authorizations, actuals, and accepted costs remain distinct;
- missing approval evidence does not become approval;
- unknown actual cost remains unknown and does not copy estimated cost;
- variance calculations require compatible currency and scope;
- routing comparisons are marked advisory-only and cannot make Dispatch ready;
- Helen/Grace budget approvals are rejected or rendered as warnings unless separate authority evidence exists;
- reconciliation output preserves source-event IDs, source references, and warnings.

## Gate C/D handoff notes

FIN-PTM-001 may run in parallel with scheduling after CORE-PTM-003B, and KPI-PTM-001 remains downstream of FIN-PTM-001 for final financial-efficiency formulas. Gate C/D review should confirm that schedule readiness, utilization, KPI, dispatch readiness, and financial reconciliation consumers all use explicit source references instead of inferring approval, spend, actual cost, or acceptance.
