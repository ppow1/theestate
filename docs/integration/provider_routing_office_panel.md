# Provider Routing Office Panel

Status: Implemented for WP-0615  
Classification: Estate Internal

## Purpose

The provider routing Office panel turns WP-0614 recommendation artifacts into an Office-readable status payload for the Office of the Steward and Traffic Controller / Operations Manager.

The payload is advisory evidence only. It is not a movement decision, schedule, dispatch, assignment, approval, or provider execution.

## Source Artifacts

The loader reads existing provider routing artifacts, especially:

```text
runtime/provider_routing/status/latest.json
runtime/provider_routing/status/summary.json
runtime/provider_routing/recommendations/<recommendation_id>.json
runtime/provider_routing/reports/<recommendation_id>.md
```

The panel implementation lives in:

```text
src/estate/core/provider_routing_office_panel.py
```

## Panel Payload Fields

The Office payload includes:

```text
available
stale
advisory_only
latest_recommendation_id
recommended_provider
alternate_providers
provider_rationale
capacity_note
local_runtime_required
human_review_required
boundary_review_required
validation_rings_required
not_recommended
source_artifact
work_package_id
classification
safe_summary
warnings
errors
updated_at
```

`advisory_only` is always `true`. The warnings always include the statement that provider routing evidence is not a movement decision and that Traffic Controller / Operations Manager decides movement.

## Safe Summary Behavior

For ordinary Estate Internal recommendations, the safe summary includes the work package, recommended provider, and a short rationale summary.

For sensitive classifications such as `Sensitive`, `Private`, `Restricted`, `Steward Only`, or `Local Only`, the safe summary redacts rationale details and only exposes recommendation metadata suitable for Office status review.

## Empty and Error States

Missing, empty, malformed, or non-object artifacts produce an unavailable panel payload with:

- `available: false`
- `advisory_only: true`
- safe warnings and errors
- no provider execution or live calls

Stale artifacts are available but flagged with `stale: true` and a warning to request fresh evidence before movement decisions.

## Optional Runtime Panel Artifacts

If a local panel summary artifact is needed, the writer can emit:

```text
runtime/provider_routing/office_panel/latest.json
runtime/provider_routing/office_panel/summary.json
```

These are local status artifacts and should not be committed unless a work package explicitly requires evidence.

## Boundary Notes

The panel does not implement routing policy, schedule work, dispatch work, assign workers, execute providers, call Codex CLI, call ChatGPT CLI, call Ollama, call GPUs, call live network services, create a provider catalog, create a dispatch queue, create an event system, create an Office, or make recommendations into decisions.

The accepted boundary remains:

```text
Planning may propose.
Routing may recommend.
Traffic Controller / Operations Manager decides movement.
Future mechanical coordination layers apply approved movement rules.
Dispatch queues hold candidate work.
Execution provider adapters perform provider handoff.
Audit and Validation produce evidence.
Chief Architect / Steward accepts institutional truth.
```
