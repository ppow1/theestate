# Planning Provider Framework

Status: Implemented  
Classification: Estate Internal

## Purpose

The Planning Provider Framework defines the first reusable Estate contract for planning providers. It separates planning from implementation, validation, orchestration, and Office UI work while emitting artifacts that future Steward-visible systems can consume.

## Provider Model

A provider exposes a stable `provider_id`, `display_name`, `capabilities()`, `can_handle(request)`, and `run(request)` method. The initial registry includes the deterministic local stub provider `stub.planning.echo`.

Initial capability names are `planning`, `architecture`, `governance_draft`, `work_package_draft`, and `documentation_draft`.

## Request Envelope

Requests are JSON objects with required `request_id`, `provider_id`, `requested_by`, `classification`, `planning_intent`, `prompt`, and `created_at` fields. Optional fields include worker/mailbox/work-package identifiers, context paths, allowed output paths, budget source, boundary-review flag, and metadata.

Allowed classifications are `Public`, `Estate Internal`, `Restricted`, `Steward Only`, and `Local Only`.

## Response Envelope

Responses include request/provider identity, status, start/finish timestamps, summary, optional output text, artifacts, lifecycle events, warnings, errors, classification, review requirement, validation status, and metadata.

Allowed statuses are `completed`, `queued`, `blocked`, and `failed`. Validation status defaults to `not_validated`.

## Event Envelope

Lifecycle events include event/request/provider identity, optional worker identity, event type, state, message, timestamp, classification, and metadata. Events are structured for future Office of the Steward consumption rather than terminal-only visibility.

## Runtime Artifact Locations

The runtime writer creates:

- `runtime/planning_provider/requests/<request_id>.json`
- `runtime/planning_provider/results/<request_id>.json`
- `runtime/planning_provider/events/<request_id>.jsonl`
- `runtime/planning_provider/status/latest.json`

`latest.json` summarizes current state, status, elapsed seconds, validation status, review requirement, and summary.

## CLI Example

```powershell
Clear-Host
cd A:\theestate
.\estate.bat planning-provider-run --request .\runtime\planning_provider\example_request.json
```

The command exits non-zero for invalid requests, missing providers, blocked requests, and provider failures.

## Stub Provider Example

Use provider ID `stub.planning.echo`. The stub accepts `Public`, `Estate Internal`, and `Local Only` requests. It returns deterministic text containing the planning intent, request ID, and prompt.

## Boundary Behavior

Unknown classifications are rejected during request validation. `Restricted` and `Steward Only` requests are blocked unless request metadata contains `"boundary_approved": true`. Blocked results explain the boundary reason and set `requires_review`.

## Future ChatGPT Provider Notes

A future ChatGPT provider should implement the same provider interface, preserve the classification boundary, emit lifecycle events, and write the same runtime artifacts. Live API or CLI calls should be added as an adapter, not by changing the envelope contracts.

## Future Orchestrator Notes

A future Orchestrator can select providers through the registry, submit request envelopes, monitor JSONL events, and display `latest.json` in Steward-facing activity views. Orchestration remains separate from planning provider execution.
