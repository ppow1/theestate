# Background Operations Event Runtime

Status: Implemented for WP-0617  
Classification: Estate Internal

## Purpose

The background operations runtime gives the Estate a deterministic event-driven coordination loop. It observes durable local artifacts, evaluates standing watches, and creates governed request/status artifacts for human or institutional review.

It is not a daemon, scheduler, provider executor, routing policy, movement authority, dispatch queue, provider registry, new Office, or character/resident identity system.

## Runtime Flow

```text
events/state change/time tick
  -> standing watch evaluation
  -> background operation event
  -> governed background operation request
  -> Office-readable status/report
```

The runtime prepares requests only. Traffic Controller / Operations Manager remains the movement decision layer, dispatch queues remain the work-holding seam, and execution provider adapters remain the provider handoff seam.

## Models

Implementation lives in:

```text
src/estate/core/background_operations.py
src/estate/core/background_operations_runtime.py
```

Models include:

- `BackgroundOperationEvent`
- `BackgroundOperationWatch`
- `BackgroundOperationRequest`

Requests carry `requires_human_review` and `requires_boundary_review` flags. Resident, character, persona, identity, continuity, private, or sensitive subjects are flagged for review rather than acted on.

## Initial Watches

The default watch set includes:

```text
pending_routing_recommendation_watch
missing_ring2_review_watch
stale_validation_artifact_watch
provider_capacity_warning_watch
worker_assignment_gap_watch
pending_movement_decision_watch
```

Cooldowns prevent repeated duplicate requests.

## Runtime Artifacts

Local artifacts are written under:

```text
runtime/background_operations/events.jsonl
runtime/background_operations/requests/<request_id>.json
runtime/background_operations/status/latest.json
runtime/background_operations/status/summary.json
runtime/background_operations/reports/latest.md
runtime/background_operations/watches.json
```

Compatible operational feed events are also appended through the existing operational event helper when background events are created. If that helper is unavailable, the background runtime still writes its own local event artifact and continues without provider execution.

## CLI

```bash
python -m estate.cli.main background-operations cycle --json
python -m estate.cli.main background-operations watches --json
python -m estate.cli.main background-operations requests --json
python -m estate.cli.main background-operations status --json
python -m estate.cli.main background-operations report
```

The CLI is deterministic and performs no live provider, GPU, network, dispatch execution, Codex CLI, ChatGPT CLI, or Ollama calls.

## Office Integration

The Office command center status bar exposes background operations fields when generated:

```text
background_operations_available
active_watches_count
generated_requests_count
blocked_requests_count
stale_validation_count
ring2_review_needed_count
pending_movement_decision_count
provider_capacity_warning_count
worker_assignment_gap_count
latest_background_request
latest_background_event
background_operations_warnings
```

These are status fields only; no fake controls or unsupported verbs are added.

## Boundary Rules

- Background operations can create events, requests, status, and reports.
- Background operations cannot approve movement, execute providers, mutate dispatch execution, or create institutional truth.
- Routing recommendations remain advisory until Traffic Controller / Operations Manager records a movement decision.
- Provider handoff remains governed by the Execution Provider Adapter Contract.
- Resident/persona-sensitive subjects require review and are not acted on autonomously.
