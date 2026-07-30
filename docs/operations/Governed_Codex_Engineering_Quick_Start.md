# Governed Codex Engineering Quick Start

This is an operator runbook for the registered provider `codex.execution.cli`.
It is for Engineering operators, Traffic Controller / Dispatch operators,
Helen, Grace, validators, and reviewers who prepare or inspect one bounded
repository commission. The repository implementation is the source of truth;
this page does not create a second queue, registry, scheduler, validator, or
acceptance path.

## What is admitted

The catalog advertises these capabilities for this provider:

`repository_implementation`, `code_review`, `documentation_draft`,
`test_execution`, and `bounded_repository_work`.

Admission is narrow. Institutional acceptance, when separately granted, is
only for the explicitly governed scope and evidence of that commission. It
does not grant unrestricted shell execution, unbounded filesystem access,
automatic merge, autonomous institutional acceptance, or any unregistered
capability. The adapter is not a CAD, calibrated-measurement, physical
inspection, or general-purpose execution authority.

Provider implementation is not the same thing as qualification, health,
availability, capacity, authorization, provider selection, Dispatch,
validation, Engineering completion, or institutional acceptance. Each must
have its own current record and authority.

## Lifecycle: do not skip a gate

1. **Grace** records the approved, generic objective, requested outcome,
   constraints, acceptance criteria, authority boundaries, required evidence,
   and escalation target. Grace does not choose or execute the provider.
2. **PTM** supplies the canonical package/dependency and readiness identity.
   Do not substitute a local note or a fabricated dependency reference.
3. **Helen** verifies the capability inquiry, worker/provider registration,
   qualification, fresh health, availability, capacity, staffing fit, and
   authorization evidence. A catalog entry alone is not availability.
4. **Engineering** interprets the commission, classifies required
   capabilities, writes a durable plan, selects the registered provider using
   current evidence, defines commission-specific validation, and declares the
   bounded worktree scopes.
5. **Dispatch** creates or admits the provider-neutral item. It must be
   `Ready`, carry a handoff reference, decision and boundary-review
   references, classification, provider identity, scopes, and exact expected
   outputs. Handoff preparation is not execution.
6. **Provider gate / adapter** checks matching Steward and Traffic Controller
   authorization, approved profile, sandbox, clean or explicitly excepted
   workspace, executable availability, and the operator’s explicit live
   confirmation. Only then may the adapter make the single provider call.
7. **Provider** returns a result. The adapter verifies every declared output,
   computes SHA-256 values, and writes a provider receipt. A zero exit code by
   itself is not completion.
8. **Engineering** validates the artifact against the commission’s criteria,
   preserves the plan, result, receipt, artifact references, validation, and
   retry history, and reports `completed`, `blocked`, or `failed` truthfully.
9. **Dispatch reconciliation** records the result and normally advances a
   successful validation-required item to `Validation`; failed or blocked
   work remains attention-requiring. It does not accept the work.
10. **Grace** receives the completion or blocker report. Chief Architect and,
    where required, Steward separately decide engineering/institutional
    acceptance. Merge and post-merge readiness are separate downstream gates.

## Preconditions and fresh evidence

Before submission, confirm all of the following in the current evidence
window:

- the catalog entry is `implemented` (or another explicitly admitted status),
  and the adapter resolves as `codex-cli-execution-adapter` version `1.0.0`;
- the requested capabilities are registered and Helen evidence says
  `qualified`, `healthy`, `available`, and `authorized`, with provider,
  adapter, `observed_at`, `expires_at`, and evidence references matching this
  commission;
- PTM dependency/readiness is canonical, satisfied, current, and linked to
  the same Grace objective and package;
- Dispatch is `Ready` and its handoff request matches the authorization;
- the operator has a decision reference, boundary-review reference, Traffic
  Controller authorization, Steward approval, approved Codex profile, and
  explicit execute confirmation;
- sandbox is `read-only` or `workspace-write`; `danger-full-access` and bypass
  flags are prohibited. `workspace-write` requires explicit approved write
  paths;
- read paths, write paths, blocked paths, classification, timeout/cancellation
  behavior, and validation commands are explicit; and
- every expected output is an exact repository-relative path. Never rely on a
  filename the provider might choose. The operator must declare exact output
  paths before execution.

Preview is safe and does not call the provider:

```powershell
python -m estate.cli.main codex-live-execution preview `
  --dispatch-id <dispatch-id> --authorization <authorization.json> --json
```

Execute only after preview is clear and the existing authority records match:

```powershell
python -m estate.cli.main codex-live-execution execute `
  --dispatch-id <dispatch-id> --authorization <authorization.json> `
  --confirm-live-execution --json
```

## Complete example: bounded documentation commission

The following is an illustrative request, not live run evidence. Every ID,
path, timestamp, and digest is a placeholder explicitly marked `EXAMPLE`.
The actual commission wrapper appends the real artifact and provider-receipt
SHA-256 values after validation; do not copy these example hashes into a
record.

```json
{
  "commission_id": "EXAMPLE-commission-doc-001",
  "grace_objective_id": "EXAMPLE-grace-obj-001",
  "ptm_package_id": "EXAMPLE-WP-DOC-001",
  "dispatch_id": "EXAMPLE-dispatch-doc-001",
  "adapter_request_id": "EXAMPLE-adapter-doc-001",
  "provider_id": "codex.execution.cli",
  "capability": "documentation_draft",
  "classification": "Estate Internal",
  "sandbox": "workspace-write",
  "read_scope_paths": ["docs/operations", "src/estate/core"],
  "write_scope_paths": ["docs/operations/example-output"],
  "blocked_scope_paths": [".git", "runtime", "archive"],
  "expected_outputs": ["docs/operations/example-output/Runbook.md"],
  "acceptance_criteria": [
    "the exact declared file exists",
    "the file is Markdown and contains the requested operator procedure",
    "provider receipt exists and names the same dispatch and artifact",
    "artifact SHA-256 is recorded and independently verified"
  ],
  "decision_reference": "EXAMPLE-decision-doc-001",
  "boundary_review_reference": "EXAMPLE-boundary-doc-001",
  "example_artifact_sha256": "EXAMPLE-64-hex-artifact-digest",
  "example_provider_receipt_sha256": "EXAMPLE-64-hex-receipt-digest"
}
```

The wrapper supplies the prompt/work-package source, current Helen/PTM/
Dispatch evidence, authorization, and validation recipe; runs preview; then
executes only with explicit confirmation. On success, expected records include
the adapter request and result under `runtime/execution_adapters/`, the live
execution decision/report, Engineering plan and validation records, Dispatch
events/reconciliation, and a receipt under
`runtime/engineering_adapter_receipts/<adapter_request_id>.json`.

The provider receipt is `estate.provider-receipt.v1` and includes provider and
adapter identity/version, Dispatch and request IDs, times, exit code, status,
command, each artifact path, and its SHA-256. Record both the artifact digest
and the receipt-file digest after validation. The receipt proves provider
execution/evidence integrity; it does not prove merge, acceptance, or
institutional truth.

## Fail closed

Stop and preserve the evidence if any gate is missing or contradictory:

- stale, expired, missing, conflicting, or unauthorized Helen/PTM/provider
  evidence: `blocked`;
- missing executable/authentication, unavailable or saturated capacity,
  unsupported adapter, timeout, cancellation, non-zero result, missing
  declared output, path escape, invalid digest, or receipt failure: `blocked`
  or `failed`, never `completed`;
- dirty or wrong workspace, mismatched IDs/profile/sandbox/scopes, non-`Ready`
  Dispatch, missing confirmation, or missing approval: blocked before the
  provider call (`live_provider_called: false` where applicable);
- validation failure: retain the attempt and report `failed`; a retry is a new
  bounded, recorded attempt; and
- merge, post-merge, readiness, Chief Architect, or Steward decisions missing:
  do not infer them from a provider result or test pass.

The adapter does not auto-retry, merge, clean/stash/reset the workspace, or
grant acceptance. Escalate to the named authority and use the existing
Dispatch/validation recovery path.

## Authority and filesystem boundary

The adapter may read only authorized scopes and may write only the declared
write scope inside the repository. `runtime`, `.git`, `archive`, and any
overlapping prohibited path must not be an output scope. `workspace-write` is
not a license to write elsewhere. The gate records workspace commit/dirty
state, and authorization expiry/revocation remains authoritative.

Traffic Controller decides movement; Dispatch owns the handoff; Engineering
owns technical interpretation, selection, execution evidence, and
commission-specific validation; Helen owns workforce/capability readiness;
Grace owns operational objective and completion coordination; Chief Architect
and Steward retain their distinct acceptance authority.

## Troubleshooting

| Symptom | Check / action |
|---|---|
| Provider not selected | Confirm the catalog capability set, Helen qualification, fresh health/availability/capacity, PTM dependency, and authorization all match. |
| Preview is blocked | Read the gate errors; reconcile Dispatch state, IDs, profile, sandbox, scopes, decision references, workspace commit, and executable availability. |
| `missing declared artifact` | Fix the commission’s exact output path or the bounded prompt; do not mark success manually. |
| `artifact outside authorized repository root` | Replace the path with a repository-relative path inside the approved write scope. |
| Receipt absent or digest mismatch | Preserve result and artifact, mark blocked/failed, and rerun validation only through the governed retry path. |
| Provider unavailable or quota-limited | Record `blocked`, refresh health/capacity evidence, and let Engineering/Traffic Controller decide a new bounded route. |
| Validation fails | Keep all attempts and reports; repair or re-scope under authority, then create a new attempt. |
| Operator expects merge or acceptance | Stop: provider completion, Engineering validation, merge, post-merge readiness, and institutional acceptance are separate records and decisions. |

## Canonical sources and evidence

- Implementation: [`codex_bridge_execution_provider_adapter.py`](../../src/estate/core/codex_bridge_execution_provider_adapter.py), [`codex_live_execution_gate.py`](../../src/estate/core/codex_live_execution_gate.py), and [`execution_provider_adapter_runtime.py`](../../src/estate/core/execution_provider_adapter_runtime.py).
- Worker contract and lifecycle: [`engineering_worker_runtime.py`](../../external/engineering_worker_runtime/engineering_worker_runtime.py) and [`runtime_manifest.json`](../../external/engineering_worker_runtime/runtime_manifest.json).
- Provider catalog: [`config/providers/catalog.json`](../../config/providers/catalog.json).
- Capability and selection schemas: [`schemas/engineering`](../../schemas/engineering/), especially [`provider_selection_v1.schema.json`](../../schemas/engineering/provider_selection_v1.schema.json), [`capability_assessment_v1.schema.json`](../../schemas/engineering/capability_assessment_v1.schema.json), and [`capability_registration_result_v1.schema.json`](../../schemas/engineering/capability_registration_result_v1.schema.json).
- Focused tests: [`test_codex_cli_execution_adapter.py`](../../tests/test_codex_cli_execution_adapter.py), [`test_engineering_worker_runtime.py`](../../tests/test_engineering_worker_runtime.py), [`test_engineering_capability_enablement.py`](../../tests/test_engineering_capability_enablement.py), and [`test_engineering_provider_routing_runtime.py`](../../tests/test_engineering_provider_routing_runtime.py).
- Adapter acceptance evidence: [`engineering_codex_adapter_local_acceptance_20260730.md`](engineering_codex_adapter_local_acceptance_20260730.md) (disposable local evidence; not institutional acceptance).
- Merged/post-merge governance evidence: [`CAMPAIGN_0670_ACCEPTANCE_PACKAGE.md`](../../collaboration/campaigns/CAMPAIGN_0670_ACCEPTANCE_PACKAGE.md) and [`automatic_post_merge_validation_pipeline.md`](../integration/automatic_post_merge_validation_pipeline.md). These preserve the required merge/post-merge evidence chain and explicitly do not infer acceptance; consult the current recorded verdict before acting.
