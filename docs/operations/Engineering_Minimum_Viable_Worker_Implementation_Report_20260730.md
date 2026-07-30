# Engineering Minimum Viable Worker Implementation Report

## Scope

This implementation replaces the receipt-only completion path with a generic
Engineering lifecycle behind the existing Grace, Helen, Dispatch, and
external-runtime seams.

## Changed surfaces

- `external/engineering_worker_runtime/engineering_worker_runtime.py`
  implements commission interpretation, durable planning, capability-based
  provider selection, adapter invocation, receipt/artifact persistence,
  commission-specific validation, retry history, and truthful terminal states.
- `external/engineering_worker_runtime/runtime_manifest.json` documents the
  worker-result contract and lifecycle states.
- `src/estate/core/local_engineering_department.py` packages generic
  commissions, loads worker results, and prevents Dispatch completion unless
  worker evidence is schema-valid and commission validation passed.
- `src/estate/core/grace_operations_runtime.py` leaves Grace-originated
  Engineering Dispatch provider-neutral; Engineering owns provider selection.
- `src/estate/core/execution_adapter_handoff_runtime.py` accepts a generic
  Engineering handoff without fabricating a provider adapter request.
- `src/estate/core/grace_helen_engineering_composition.py` requires artifact,
  provider-receipt, and passed validation evidence before completion records.
- Tests cover image-shaped and non-image commissions through the same generic
  worker path, provider capability selection, blocked providers, retry history,
  provider-neutral Dispatch, and authority boundaries.

## Truthful semantics

Exit code zero means only that the worker process returned normally. A
commission is `completed` only when a provider receipt, artifact references,
and passed commission-specific validation are present. Missing adapters,
missing capabilities, provider failures, and validation failures produce
`blocked` or `failed` results.

Engineering records `institutional_acceptance_granted: false`; Chief Architect
and Steward acceptance remain outside the worker.

## Validation performed

- Focused worker, Grace/Helen, Dispatch, Open WebUI workflow, and local
  department tests: **32 passed**.
- Broader provider/Dispatch/adapter suite: **104 passed**.
- Python compilation: **passed**.
- `git diff --check`: **passed**.
- Production-source search for bicycle-specific logic: **no matches**.
- Full repository suite: started but did not complete within the practical
  validation window; it was stopped as a test-only process. It is not claimed
  as passing.

## Runtime synchronization

The canonical runtime is the repository copy. After review, synchronize the
machine-installed runtime with:

```powershell
CLS
Set-Location A:\theestate-wp4233
.\scripts\Sync-EngineeringWorkerRuntime.ps1
```

No live provider execution or production commissioning was performed by this
implementation task.

## Remaining limitations

The current source catalog contains provider descriptors whose concrete live
adapters are not all registered in the external worker. Those selections fail
closed rather than claiming completion. A production image or code commission
still requires a separately registered, authorized adapter and its provider
receipt/artifact validation evidence.
