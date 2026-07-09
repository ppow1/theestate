# Operations / Execution Integration Findings

Status: Completed with consolidation recommended
Work package: WP-0612
Classification: Estate Internal

## Current Architecture as Implemented

The local operations/execution wave currently implements a staged operational chain:

1. Planning/provider request artifacts are written under `runtime/planning_provider`.
2. Orchestrator intake stores requests and queue state under `runtime/orchestrator/intake`.
3. Intake decisions and scheduling move approved work into `runtime/orchestrator/schedule`.
4. Orchestrator Runtime Core runs a bounded cycle and writes dispatch records under `runtime/orchestrator/dispatch`.
5. Traffic Controller / Operations Manager inspects intake, schedule, dispatch, assignments, and provider health under `runtime/operations/control` without executing provider work.
6. Execution Dispatch Queue stores provider-adapter queue items under `runtime/execution_dispatch`.
7. Codex Bridge acts as a bounded provider-specific adapter shell under `runtime/codex_bridge` when explicitly invoked or when a handoff is prepared.
8. Execution Activity normalizes execution/Codex visibility under `runtime/execution_activity`.
9. Office panels currently read operations status/control artifacts, not provider execution directly.

## Confirmed Coherent Chain

The following links are coherent:

- Orchestrator intake, scheduling, runtime cycle, and dispatch records are internally compatible.
- Operations Manager remains distinct from Orchestrator; it reviews and records decisions but does not dispatch providers.
- Orchestrator Runtime Core stops before provider execution.
- Codex Bridge is not coupled directly to Orchestrator; it is adapter-like and reachable through explicit bridge requests or Execution Dispatch handoff preparation.
- Worker Assignment Board preserves A2C/assignment labels and related provider/seat/profile metadata without observed hardcoded seat limits.

## Duplicate Mechanisms

| Area | Duplicate mechanism | Finding |
| --- | --- | --- |
| Provider catalog | `data/registry/providers.json` and `config/providers/catalog.json` | Operational provider execution should standardize on `config/providers/catalog.json`; legacy registry should be documented or synchronized. |
| Dispatch queues | `runtime/orchestrator/dispatch/status/queue.json` and `runtime/execution_dispatch/queue.json` | Distinct layers, but names overlap and need an adapter-boundary mapping contract. |
| Events/activity | `runtime/operations/status/*`, `runtime/execution_activity/*`, `runtime/codex_bridge/*/events.jsonl` | Distinct scopes, but consumer guidance is required. |
| Provider health/capacity | Health and capacity records share `runtime/providers/health/records` | Functional but semantically crowded. |
| Provider CLI naming | Legacy `providers` and operational `providers-list/show/find` | Operational commands are clearer; legacy command remains a naming risk. |

## Conflict Risks

1. Future implementers may connect Orchestrator directly to Codex Bridge, bypassing the Execution Provider Adapter Contract.
2. Future implementers may treat Execution Dispatch Queue as a replacement for Orchestrator dispatch rather than the next layer after an adapter contract.
3. Scheduling and assignment may diverge from provider health/capacity if no authoritative capacity-consumption contract is introduced.
4. Office visibility may split between Operational Activity and Execution Activity unless read-only integration rules are documented.
5. Linux validation remains noisy because the broad audit command assumes `.estate.bat` Windows command shapes.

## Required Repair Packages

Recommended next package: **Consolidation Repair**.

Minimum repair scope:

- Declare operational provider catalog source of truth and legacy registry relationship.
- Document the transformation boundary from `OrchestratorDispatchRecord` to `ExecutionDispatchRequest`.
- Document event feed scopes: operational lifecycle, provider execution lifecycle, normalized execution activity.
- Clarify provider health/capacity namespaces and how future scheduling may consume them without implementing policy.
- Repair broad audit command portability or document platform-specific validation commands.

## Recommended Next Implementation Package

The next implementation package should be:

**Consolidation Repair: Operations / Execution Boundary and Source-of-Truth Repair**

It should be documentation/schema/test focused. It should not add provider execution, routing policy, scheduling priority policy, or new Office features.

## Execution Provider Adapter Contract Dispatch Recommendation

The Execution Provider Adapter Contract is **not safe to dispatch immediately next**. The chain is close, and the correct connection point is clear, but duplicate dispatch/provider/event mechanisms need a consolidation repair first so the adapter contract does not accidentally bless ambiguous sources of truth.

Future adapter contract connection point:

```text
runtime/orchestrator/dispatch/status/queue.json
  -> Execution Provider Adapter Contract mapping
  -> runtime/execution_dispatch/queue.json
  -> provider-specific adapter handoff, such as runtime/execution_dispatch/handoffs/*_codex_bridge_request.json
```
