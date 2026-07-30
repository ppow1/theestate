# `codex.execution.cli` Adapter Operations

Status: Implemented on the recovery branch; not yet merged or institutionally accepted.

## Scope

The adapter supports bounded repository work, documentation drafting, test
execution, code review, and structured work products inside an explicitly
authorized Estate worktree. It does not claim CAD, calibrated image
measurement, physical inspection, mechanical certification, unrestricted shell
execution, or institutional acceptance.

The canonical provider descriptor is `config/providers/catalog.json`. The
concrete adapter is `CodexCliExecutionProviderAdapter` in
`src/estate/core/codex_bridge_execution_provider_adapter.py`; the invocation
mechanism remains the existing bounded `codex exec` bridge.

## Admission and authorization

Dispatch must provide a decision reference, boundary review reference, explicit
read/write scopes, `workspace-write` only when needed, and declared
`expected_outputs`. The adapter rejects missing outputs, output paths outside
the repository root, prohibited paths, missing CLI execution, failed process
status, and missing provider evidence. The live execution gate additionally
requires Steward/traffic-controller authorization and a valid workspace state.

## Evidence

The adapter preserves bridge lifecycle events and audit records, writes a
provider receipt under `runtime/engineering_adapter_receipts/`, hashes every
declared artifact, and returns the receipt as an artifact reference. Provider
completion is not Engineering validation or institutional acceptance.

## Health, qualification, and revocation

`codex_cli_capability_discovery.py` performs metadata-only executable discovery
and records the observed version/help surface. It does not mutate the provider
catalog or claim execution readiness. Helen must use fresh qualification,
health, availability, and authorization evidence before declaring the worker
available. Revocation is represented by the existing authorization and provider
status mechanisms; no adapter-local registry is permitted.

## Failure and recovery

Missing executable, authentication failure, unsupported interactive-only mode,
timeout, cancellation, nonzero exit, missing output, invalid digest, or
prohibited path produces a non-completed result and requires review/retry under
the existing Dispatch and validation lifecycle. No automatic merge, acceptance,
or retry is performed by the adapter.
