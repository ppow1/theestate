# Engineering Capability Enablement — Current-State Reconciliation

Status: Historical discovery baseline. Runtime implementation is authored by
PR #496; this document records the pre-implementation reconciliation and is not
itself the runtime source of truth.
Date: 2026-07-30
Baseline: `main` at `2ae9b37c2f1c88bd8d09491a715ae69a838530c3` (PR #495)

## Scope and authority

This document reconciles the existing Grace, Helen, provider, capability,
health, Dispatch, PTM/orchestrator, adapter, validation, and acceptance
surfaces before a first concrete Engineering execution adapter is implemented.
It does not register a provider, modify live runtime state, or authorize
execution. The canonical reuse rules in
`docs/architecture/engineering_department_canonical_reuse_map.md` control.

## Findings

| Area | Existing authoritative or active surface | Current truth | Gap requiring a governed extension |
|---|---|---|---|
| Grace objective | `src/estate/core/grace_operations_runtime.py`, `runtime/operations/grace/` | Grace can create objectives, actions, checkpoints, dependencies, blockers, transitions, and closures. | No generic capability-decomposition record or deterministic resumption link. |
| Grace/Helen/Engineering composition | `src/estate/core/grace_helen_engineering_composition.py`, `runtime/grace_helen_engineering/` | Capability requests, Helen determinations, commissions, authorizations, validations, completions, and Grace receipts exist. | Capability-absent creates a `capability_development` record only; no worker specification, enabling project, dependency, or re-evaluation lifecycle is enforced. |
| Helen workforce | `src/estate/core/helen_workforce.py`, `runtime/workforce_development/` | Helen can record staffing/capability requests, assessments, evidence, and operational dispositions. | Records do not model worker identity, qualification version, health freshness, availability lease, authorization scope, or capability claim reconciliation as separate facts. |
| Worker assignments | `src/estate/core/worker_assignments.py` and `worker_assignment_runtime.py` | Assignment records distinguish worker, role, provider, state, outputs, and validation requirement. | There is no canonical join from a qualified worker identity to a capability-specific qualification and an enabling-project result. |
| Capability registry | `config/providers/catalog.json`, `src/estate/core/provider_catalog.py`, `provider_capabilities.py`; `data/registry/capabilities.json` is older inventory | The provider catalog is the current provider/capability descriptor source; the data registry is a separate legacy resource inventory. | The distinction and cross-reference must be explicit; neither should be silently overwritten by a new registry. |
| Capability lifecycle | `src/estate/core/capability_lifecycle.py`, `estate_capability_registry.py`, `capability_gap_report.py` | Lifecycle reporting and gap reporting are derived, read-only projections. | No authoritative capability inquiry, gap, specification, registration, or re-evaluation record. |
| Provider health/capacity | `src/estate/core/provider_health.py`, `provider_capacity.py`, Engineering health/capacity runtimes | Canonical health/capacity records are intended sources; current checkout has catalog status but no current `runtime/providers/health` or capacity evidence. | Helen must classify missing/stale evidence as uncertain, not available; freshness/expiry policy must be package-defined. |
| Routing recommendation | `provider_routing_recommendations.py`, `provider_routing_recommendations_runtime.py`, `engineering_provider_routing_runtime.py` | Recommendations are advisory and separate from selection, reservation, Dispatch, and execution. | No capability-gap flow that carries recommendation evidence into a worker specification or enabling project. |
| Reservation/scheduling | `governed_provider_scheduler.py`, PTM/orchestrator schedule runtime | Multiple active surfaces exist; canonical reuse map flags scheduler duplication risk. | Gate B must name PTM/orchestrator eligibility and scheduler reservation precedence before automation. |
| Dispatch | `src/estate/core/execution_dispatch.py` and handoff runtime | Dispatch is the provider-neutral execution boundary and stores dependencies, scope, validation, and state. | Enabling-project dependency and resumed original project linkage are not standardized. |
| Adapter contract | `execution_provider_adapter.py`, runtime helper, Codex and ComfyUI adapters | Provider-neutral request/result contract and dry-run adapter exist. | Registration, concrete submit authorization, live receipt, artifact, cancellation, and health evidence are not unified. |
| Engineering worker | `external/engineering_worker_runtime/` | Generic worker lifecycle exists and fails closed for unregistered adapters. | It must consume a registered adapter descriptor/result contract once an adapter is approved. |
| Validation/acceptance | Existing package recipes, validation reports, PTM, PR, Chief Architect and Steward decisions | Completion, validation, engineering acceptance, readiness, and institutional acceptance are distinct. | Enablement must prove registration and re-evaluation without claiming institutional acceptance. |

## Important conflicts and stale evidence

1. `config/providers/catalog.json` uses stable provider IDs such as
   `comfyui.local.image`, while `data/registry/providers.json` uses older
   resource IDs such as `PRV-000003`. The latter is not a safe replacement for
   the provider catalog.
2. `data/registry/capabilities.json` describes installed resources such as
   ComfyUI and GPU, while `config/providers/catalog.json` describes executable
   provider capabilities. They answer different questions and must be linked,
   not merged by convention.
3. The checkout contains catalog status but no current provider health/capacity
   runtime artifacts. Provider availability is therefore not proven by catalog
   status.
4. `CAMPAIGN-0670` packages WP-0671/WP-0672 cover intake and routing, while
   CAMPAIGN-0681 packages WP-0695/WP-0697 cover Helen request integration and
   operational projection. These packages overlap the requested lifecycle and
   must be reconciled before a new package ID is assigned.
5. Existing `engineering_lifecycle_slice.py` and
   `engineering_campaign_operations.py` contain explicit fixture behavior.
   They are evidence of seams, not proof of a production capability-enablement
   lifecycle.

## Present capability answer

Helen can currently record an evidence-backed request and disposition, but the
repository does not provide a canonical query that simultaneously proves:

- a named worker identity;
- a qualification for the requested capability and version;
- current health;
- current availability or reservation;
- authorization for the specific classification and scope.

The truthful answer for a capability with missing or stale evidence is
`capability_unknown`, not `qualified_and_available`.

## Reconciliation conclusion

The next implementation should extend the existing
`GraceHelenEngineeringComposition`, `HelenWorkforceStore`, provider catalog,
provider health/capacity, PTM/orchestrator, Dispatch, adapter, and validation
seams. It should add only correlation records and adapters for:

`inquiry -> assessment -> gap -> specification -> enabling project -> dependency -> registration -> re-evaluation -> resumption`.

No new registry, scheduler, queue, acceptance authority, or direct Grace-to-
provider route is justified.
