# Operations / Execution Integration Findings

Status: completed with findings
Date: 2026-07-10
Work package: WP-0612

## Current architecture as implemented

The repository implements a layered operations chain:

1. **Traffic Controller / Operations Manager** records operational posture, recommendations, and durable movement decisions under `runtime/operations/control/*`.
2. **Orchestrator intake, decisions, scheduler, and runtime core** convert approved intake into scheduled work and then pre-provider dispatch records under `runtime/orchestrator/*`.
3. **Execution Dispatch Queue** stores provider-neutral execution intent under `runtime/execution_dispatch/*`.
4. **Execution Provider Adapter Contract / Codex Bridge Adapter** translates adapter requests into provider-specific requests under `runtime/execution_adapters/*` and `runtime/codex_bridge/*`.
5. **Execution Activity Surface** aggregates execution-provider lifecycle visibility under `runtime/execution_activity/*`.
6. **Office panels/hooks** read summaries and current snapshots rather than owning runtime truth.

## Confirmed coherent chain

The major boundaries are preserved:

- Traffic Controller / Operations Manager does not replace Orchestrator.
- Orchestrator Runtime Core stops at dispatch records and does not execute providers.
- Execution Dispatch Queue does not schedule or auto-select providers.
- Codex Bridge is available behind an adapter seam in the current checkout.
- Office surfaces consume local artifacts and do not become execution authority.

## Duplicate mechanisms

| Area | Finding | Severity | Recommendation |
| --- | --- | --- | --- |
| Event feeds | `runtime/operations/events/`, `runtime/execution_dispatch/events.jsonl`, `runtime/execution_activity/events.jsonl`, and Codex Bridge event logs coexist. | medium | Define event hierarchy and aggregation rules. |
| Dispatch queues | Orchestrator dispatch records and Execution Dispatch Queue records both use dispatch/queue terminology. | high | Add canonical state mapping and handoff package. |
| Provider identity | Provider catalog, provider routing, Codex Bridge, adapter profiles, health, and capacity all carry provider identity. | high | Provider catalog should be identity/capability source of truth. |
| CLI naming | Flat Orchestrator/provider commands coexist with grouped execution/adapter commands. | low | Document current names; add aliases only in a later package. |
| Validation/audit portability | Audit internals assume `.estate.bat`, which fails in Linux shell. | medium | Repair audit command portability separately. |

## Conflict risks

1. A consumer may mistake Orchestrator dispatch records for executable provider queue items.
2. Provider routing or adapter logic may drift from provider catalog if catalog ownership is not made explicit.
3. Office panels may imply authority if action controls are not clearly limited to decision-record creation.
4. Event aggregation may double-count lifecycle events unless each feed has a scoped meaning.
5. Audit receipts can look inconsistent when Linux audit runs fail Windows wrapper checks.

## Required repair packages

1. **Operations/Execution Handoff Consolidation Repair**: define and test how Orchestrator dispatch records become execution dispatch items and adapter requests.
2. **Provider Catalog Source-of-Truth Repair**: make provider catalog the canonical identity/capability authority and require routing, bridge, health, and capacity to reference it.
3. **Event Feed Scope Repair**: document operational events vs provider lifecycle events and update reports to identify source feed and event scope.
4. **Audit Portability Repair**: make `audit` use the active Python entry point on POSIX systems rather than `.estate.bat`.

## Recommended next implementation package

Recommend **Consolidation Repair** next. Do not add routing policy, priority policy, scheduling policy, or autonomous execution until the Orchestrator-dispatch to Execution-dispatch/adapter seam is explicit and provider catalog ownership is settled.

## Execution Provider Adapter Contract recommendation

The **Execution Provider Adapter Contract is architecturally the right seam** between execution dispatch/handoff records and provider-specific adapters. However, because this checkout already contains adapter-contract and Codex Bridge adapter artifacts, the safest next dispatch is not another adapter implementation package; it is a consolidation package that locks down the handoff mapping and source-of-truth rules. After that repair, provider routing recommendations can safely consume catalog, health, capacity, assignment, and adapter evidence without bypassing the adapter boundary.
