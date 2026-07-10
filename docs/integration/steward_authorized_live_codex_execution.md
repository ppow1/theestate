# Steward-Authorized Live Codex Execution Gate

Status: Implemented for WP-0506  
Classification: Estate Internal

## Purpose

The live execution gate is the explicit Estate-owned boundary that decides whether the real local Codex Bridge runner may be attached to an already-authorized Codex Bridge Execution Provider Adapter request.

The gate verifies authority; it does not create authority. Provider execution is not validation, merge approval, or institutional acceptance.

## Required authority chain

Live execution requires all of the following evidence to match:

- an existing Execution Dispatch Queue item in `Ready` state;
- an existing dispatch `handoff_reference` pointing to a valid adapter request;
- a matching live execution authorization record;
- a decision reference;
- a Traffic Controller authorization reference;
- a Steward approval reference;
- a matching provider, profile, sandbox, work package, dispatch id, and adapter request id;
- a clean and matching workspace when required;
- an available local Codex binary;
- an explicit execute confirmation flag.

The confirmation flag expresses operator intent only. It is not authorization by itself.

## CLI

Preview never calls the provider:

```bash
python -m estate.cli.main codex-live-execution preview --dispatch-id <id> --authorization <path> --json
```

Execute requires deliberate confirmation:

```bash
python -m estate.cli.main codex-live-execution execute --dispatch-id <id> --authorization <path> --confirm-live-execution --json
```

Status and report commands read durable execution evidence:

```bash
python -m estate.cli.main codex-live-execution status --dispatch-id <id> --json
python -m estate.cli.main codex-live-execution report --dispatch-id <id>
```

## Runtime artifacts

The gate writes under the existing execution-adapter runtime tree:

```text
runtime/execution_adapters/authorizations/<execution_authorization_id>.json
runtime/execution_adapters/executions/<dispatch_id>.json
runtime/execution_adapters/results/<adapter_request_id>.json
runtime/execution_adapters/reports/<adapter_request_id>_live_execution.md
runtime/execution_adapters/status/latest.json
runtime/execution_adapters/status/summary.json
```

The gate does not create a parallel top-level execution subsystem.

## Workspace safety

The gate records the current commit and dirty-tree state. A dirty workspace blocks live execution when `workspace_clean_required` is true unless the authorization record contains an explicit Steward-approved dirty-workspace exception in metadata.

The gate never stashes, resets, cleans, repairs, merges, or auto-accepts provider output.

## Dispatch behavior

On an approved execute operation, the dispatch item is moved to `Running` immediately before the single provider call. Pre-call failures do not call the provider. Result reconciliation and closure remain outside this gate.
