# End-to-End Execution Chain Demonstration

Status: Implemented for WP-0509  
Classification: Estate Internal

## Purpose

This demonstration proves the existing CA5 execution-provider chain as one deterministic operational path. It starts with a synthetic but authorized `Ready` dispatch item, runs session preview, validates handoff and authorization, acquires an execution lease, invokes an injected fake provider exactly once, persists the provider result, reconciles it back to Dispatch, publishes activity and session evidence, and verifies that institutional acceptance remains `not_granted`.

## Boundary

The demonstration is mechanical evidence only. It does not create a new queue, provider registry, event system, office, session controller, attempt runtime, reconciliation runtime, authorization authority, retry behavior, merge behavior, or institutional acceptance path.

The deterministic command never calls Codex CLI, ChatGPT, Ollama, GPU, subprocess provider execution, or the network. The provider seam is satisfied by an injected fake bridge runner.

## CLI

```bash
PYTHONPATH=src python -m estate.cli.main execution-chain demonstrate --json
```

The command uses an isolated temporary Estate root by default and writes evidence under that temporary root, including:

```text
runtime/execution_adapters/demonstrations/<demonstration_id>.json
runtime/execution_adapters/reports/<demonstration_id>_end_to_end.md
runtime/execution_adapters/results/<adapter_request_id>.json
runtime/execution_adapters/reconciliation/<dispatch_id>.json
runtime/execution_adapters/sessions/<session_id>.json
runtime/execution_activity/current.json
```

## Required Successful Evidence

A passing deterministic run reports:

```text
provider_call_count: 1
live_provider_called: false
fake_provider_runner_used: true
final_dispatch_state: Validation
lease_released: true
institutional_acceptance_state: not_granted
```

Preview evidence must show no provider call. Repeated status, report, and resume-safe inspection must not invoke the fake provider again.

## Failure Fixture Coverage

The focused tests also cover an invalid authorization fixture and a failed fake-provider response. The invalid authorization is blocked before provider invocation. The failed provider response is still persisted for review and reconciled as failed evidence.
