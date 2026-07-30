# Minimum Viable Engineering Worker

Status: implemented on `recovery/grace-engineering-operational-activation`.

## Lifecycle

Engineering receives a provider-neutral commission through the existing
Dispatch queue. The worker records `received`, creates a durable plan
(`planned`), selects a registered provider from declared capabilities, invokes
its registered adapter (`executing`), records `validation_required`, and then
ends as `completed`, `blocked`, or `failed`. A normal process exit is not a
commission completion signal.

The worker result is `estate.engineering.worker-result.v2` and must preserve:

- interpreted commission;
- execution plan;
- provider selection and rationale;
- provider receipt;
- artifact/work-product references;
- commission-specific validation checks;
- retry history;
- final Engineering disposition.

Institutional acceptance remains outside Engineering. The result records
`institutional_acceptance_granted: false`.

## Ownership

Grace owns the objective and requests the generic commission. Dispatch owns
transport and handoff state. Helen owns staffing evidence. Engineering owns
interpretation, planning, capability matching, provider selection, execution,
and validation. Provider adapters own provider receipts. Chief Architect and
Steward retain acceptance authority.

Grace-originated commissions intentionally leave `provider` empty in Dispatch.
The handoff record is written under
`runtime/execution_dispatch/handoffs/<dispatch>_engineering_commission.json`.

## Provider contract

The package carries a provider capability catalog. A provider must declare all
required commission capabilities and an available/implemented status. The
worker does not infer provider identity from the subject or artifact wording.
Providers without a registered concrete adapter fail closed as `blocked`.
The deterministic local artifact adapter is test infrastructure and is named
explicitly in its receipt; it is not an external model or image-generation
claim.

## Local synchronization

The repository copy under `external/engineering_worker_runtime` is canonical.
After reviewing this branch, materialize it with:

```powershell
CLS
Set-Location A:\theestate-wp4233
.\scripts\Sync-EngineeringWorkerRuntime.ps1
```

The sync script copies the canonical worker, launcher, and manifest to
`A:\AI\Tools\EngineeringWorkerRuntime`. It does not authorize a live run,
provider execution, or institutional acceptance.

## Validation

Focused generic worker and lifecycle tests:

```powershell
CLS
Set-Location A:\theestate-wp4233
$env:PYTHONPATH='src'
python -m pytest -q tests/test_engineering_worker_runtime.py tests/test_local_engineering_department.py tests/test_grace_helen_engineering_composition.py tests/test_openwebui_engineering_workflow.py
```

The bicycle is acceptance-test input only. Removing that test must not alter
worker selection, lifecycle, receipt, artifact, or validation behavior.
