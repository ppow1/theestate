# Execution Provider Boundary Review After Background Operations Merge Wave

Status: Complete for WP-0501  
Owner: Chief Architect #5  
Classification: Estate Internal  
Created: 2026-07-09

## Executive verdict

The reviewed WP-0614, WP-0615, WP-0617, WP-0618, and WP-0619 merge wave preserves the accepted Estate execution-provider boundary.

CA5 execution-provider ownership remains focused on provider-neutral recommendations, dispatch queue seams, and adapter handoff contracts. CA6 Background Operations remains an observing and request-producing lane. No reviewed artifact grants Background Operations routing authority, dispatch authority, worker-assignment authority, provider execution authority, autonomous approval authority, or institutional truth acceptance authority.

## Files reviewed

Required reading reviewed:

- `AI_START_HERE.md`
- `AI_HINTS.md`
- `docs/governance/Estate_Manual.md`
- `docs/governance/workers/templates/Codex_Work_Package_Template_v1.md`
- `docs/integration/execution_provider_adapter_contract.md`
- `docs/integration/provider_routing_recommendations.md`
- `docs/integration/provider_routing_office_panel.md`
- `docs/integration/background_operations_event_runtime.md`
- `docs/integration/background_operational_targets_and_post_merge_audit.md`
- `docs/integration/operations_runtime_service_loop.md`
- `collaboration/work_packages/completions/WP-0614_codex_done.json`
- `collaboration/work_packages/completions/WP-0615_codex_done.json`
- `collaboration/work_packages/completions/WP-0617_codex_done.json`
- `collaboration/work_packages/completions/WP-0618_codex_done.json`
- `collaboration/work_packages/completions/WP-0619_codex_done.json`

Additional implementation surfaces reviewed for targeted boundary evidence:

- `src/estate/core/provider_routing_recommendations.py`
- `src/estate/core/provider_routing_recommendations_runtime.py`
- `src/estate/core/provider_routing_office_panel.py`
- `src/estate/core/background_operations.py`
- `src/estate/core/background_operations_runtime.py`
- `src/estate/core/operational_targets.py`
- `src/estate/core/operational_targets_runtime.py`
- `src/estate/core/post_merge_audit.py`
- `src/estate/core/post_merge_audit_runtime.py`
- `src/estate/core/operations_runtime.py`
- `src/estate/core/operations_runtime_service.py`
- `src/estate/core/execution_provider_adapter.py`
- `src/estate/core/execution_provider_adapter_runtime.py`
- `src/estate/core/execution_dispatch.py`
- `src/estate/core/work_package_validation.py`
- Relevant focused test files listed in the WP-0501 validation report.

Missing required files: none.

## Relevant merged packages

| Package | Lane reviewed | Boundary result |
| --- | --- | --- |
| WP-0614 | Provider Routing Recommendations | Advisory recommendation evidence only; no scheduling, dispatch, assignment, provider calls, Orchestrator mutation, or live execution. |
| WP-0615 | Office Provider Routing Recommendations Panel | Visibility-only Office payload; `advisory_only` remains the core status flag and no movement decision is created. |
| WP-0617 | Background Operations Event Runtime | Background Operations observes and creates governed requests/status; it is not a provider, queue, scheduler, routing authority, or dispatch actor. |
| WP-0618 | Operational Targets and Post-Merge Audit | Operational target and audit artifacts produce deterministic evidence; they do not approve, merge, repair, dispatch, execute providers, or accept truth. |
| WP-0619 | Operations Runtime Service Loop | Bounded service loop observes, evaluates, requests, reports, writes heartbeat/status, and exits/sleeps; it does not approve, dispatch, execute, repair, stash, merge, or accept. |

## Execution-provider boundary map

The CA5 execution-provider stack remains:

1. Provider routing recommendations produce provider-fit evidence.
2. Traffic Controller / Operations Manager decides movement outside the recommendation layer.
3. Execution Dispatch Queue remains the provider-agnostic candidate-work holding seam.
4. Execution Provider Adapter Contract remains the provider-neutral handoff seam from dispatch records to provider adapters.
5. Deterministic dry-run adapter validation remains explicitly non-live and records `live_provider_called: false`.

This stack preserves the accepted boundary: planning may propose, routing may recommend, movement is decided by Traffic Controller / Operations Manager, dispatch queues hold candidate work, execution provider adapters perform provider handoff, audit and validation produce evidence, and Chief Architect / Steward accepts institutional truth.

## Background Operations boundary map

The CA6 Background Operations stack remains:

1. Background Operations evaluates watches.
2. Background Operations creates local events, governed requests, status, and reports.
3. Operational Targets provide target state and hygiene evidence.
4. Post-Merge Audit produces audit requests, verdicts, and Ring 2 prompt artifacts.
5. Operations Runtime runs bounded cycles that call observation/request/reporting helpers.

This stack does not become a provider adapter, execution queue, movement-decision layer, worker-assignment authority, routing authority, or institutional acceptance layer.

## Provider recommendation boundary check

WP-0614 remains advisory. Its documentation states that a recommendation is evidence for a Traffic Controller / Operations Manager decision and not a decision, schedule, dispatch, assignment, or provider execution. Its runtime metadata records recommendation-only behavior and no dispatch or Orchestrator mutation. Its completion receipt reports no live provider, GPU, network, dispatch queue execution, or Orchestrator runtime mutation.

Verdict: pass.

## Provider Office panel boundary check

WP-0615 remains a visibility surface. The panel reads existing provider routing artifacts and emits Office-readable status. It reports `advisory_only: true`, includes warnings that provider routing evidence is not a movement decision, and does not create recommendations, movement decisions, dispatches, assignments, approvals, providers, or live calls.

Verdict: pass.

## Dispatch Queue non-overlap check

The Execution Dispatch Queue remains separate from Background Operations. Existing dispatch CLI and runtime surfaces are still under the execution dispatch/orchestrator lanes. Background Operations creates request artifacts and status artifacts, but does not enqueue execution dispatch records, mutate dispatch execution, or replace the dispatch queue.

Verdict: pass.

## Provider Adapter Contract non-overlap check

The Execution Provider Adapter Contract remains the provider execution handoff seam. Background Operations and Operations Runtime documentation refer to the adapter contract as the downstream handoff seam but do not call adapters for live execution. The deterministic dry-run adapter remains local validation only and blocks real provider submission.

Verdict: pass.

## Audit / Validation / Acceptance separation check

Post-merge audit creates requests, verdicts, findings, Ring 2 prompts, and evidence metadata. Validation recipes and validation reports produce deterministic evidence. Neither audit nor validation accepts institutional truth; acceptance remains Chief Architect / Steward authority.

Verdict: pass.

## Runtime artifact and Office visibility check

Runtime and Office surfaces distinguish status, advisory evidence, validation evidence, audit evidence, warnings, and review requirements. The Office provider panel exposes recommendation status as advisory-only. Steward command center status fields expose Background Operations counts and latest artifacts as status, not controls that execute movement.

Verdict: pass.

## Duplicate-system risk check

No duplicate CA5 provider registry, dispatch queue, event feed, provider catalog, or office was introduced by this package or identified in the reviewed merge wave. Background Operations writes its own local event/request/status/report artifacts and may append compatible operational feed events, but it does not define a competing execution-provider event system or dispatch queue.

Verdict: pass.

## Findings

No blocking boundary findings were identified.

Non-blocking observations:

1. The WP-0618 completion receipt lists `runtime/validation/work_packages/latest.json` as changed. This is runtime validation evidence and should remain treated as transient evidence, not durable package implementation content.
2. Future external validation evidence roots should keep transient validation evidence outside source-controlled implementation paths where possible, consistent with the WP-0618 documentation direction.

## Required follow-up packages

No required follow-up packages are needed for boundary repair.

Optional future follow-up:

- Create a dedicated validation-evidence-root hardening package if the Steward wants stronger enforcement that generated runtime validation artifacts are externalized or consistently ignored.

## CA5 recommendation to Chief Architect / Steward

CA5 recommends accepting the execution-provider boundary posture of the reviewed merge wave. WP-0614 and WP-0615 remain advisory and visibility-only. WP-0617, WP-0618, and WP-0619 preserve the no-provider-execution, no-dispatch-authority, no-worker-assignment, no-routing-authority, and no-autonomous-acceptance boundaries. No live provider calls were required or made for this review.
