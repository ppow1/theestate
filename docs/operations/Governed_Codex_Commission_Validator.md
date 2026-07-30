# Governed Codex Commission Validator

The template and validator prepare a bounded request for the registered
`codex.execution.cli` provider. They validate the request before execution;
they do not create lifecycle records, authorize work, enqueue Dispatch, invoke
Codex, change the repository, merge, or grant institutional acceptance.

## Use the template

Copy [`Governed_Codex_Commission_Request.template.json`](templates/Governed_Codex_Commission_Request.template.json)
to a local working file and replace every `<REQUIRED: ...>` placeholder with
current canonical records. Do not copy placeholder text into authorization or
decision fields. Populate the exact repository-relative output paths before
execution.

The request must identify the Grace objective and capability inquiry, Helen
assessment, authoritative PTM dependency/readiness, Dispatch handoff, provider
and adapter, current source commit, evidence freshness window, bounded sandbox,
read/write/prohibited scopes, acceptance criteria, validation commands, and all
authorization references.

The profile, approval policy, and any live execution confirmation remain
operator-supplied authority records. This validator does not create or grant
them. Bypass flags, cloud execution, and full-access sandbox requests are
always rejected.

## Preview validation

Run the read-only validator from the repository root:

```powershell
CLS
pwsh -NoProfile -File .\scripts\Validate-GovernedCodexCommission.ps1 `
  -RequestPath .\commission-request.json
```

For machine-readable output:

```powershell
pwsh -NoProfile -File .\scripts\Validate-GovernedCodexCommission.ps1 `
  -RequestPath .\commission-request.json -Json
```

Exit code `0` means the request passed this structural and boundary
validation. Nonzero means the request is blocked; the output lists every
detected error. Malformed JSON is a parse failure and returns a distinct
nonzero exit code. The validator always reports `provider_invoked=false` and
`lifecycle_mutated=false`.

## What validation does not authorize

Successful local validation is not authorization, provider selection,
execution, Engineering completion, merge, readiness, or institutional
acceptance, and it never enables auto-merge. The operator must still route the request through the canonical
Grace → Helen → PTM → Engineering → Dispatch → provider → validation → Grace
lifecycle. A catalog entry marked `implemented` is not proof of current
qualification, health, availability, capacity, or authorization.

Only `read-only` and `workspace-write` are accepted. `danger-full-access`,
bypass flags, unrestricted shell authority, automatic merge authority, and
autonomous institutional-acceptance authority are rejected. Expected outputs
must be repository-relative, exact, free of `..` traversal, and inside an
authorized write scope. `.git` and `archive` are prohibited by default;
authorized runtime evidence paths are allowed only when the canonical
implementation requires them and the request scopes them explicitly.

## Illustrative valid request

The following is illustrative only. IDs, timestamps, and digests are not live
authorization or execution evidence:

```json
{
  "commission_id": "EXAMPLE-commission-001",
  "grace_objective_id": "EXAMPLE-grace-objective-001",
  "capability_inquiry_id": "EXAMPLE-capinq-001",
  "helen_assessment_reference": "EXAMPLE-helen-assessment.json",
  "ptm_dependency_reference": "EXAMPLE-ptm-dependency-001",
  "dispatch_id": "EXAMPLE-dispatch-001",
  "provider_id": "codex.execution.cli",
  "adapter_id": "codex-cli-execution-adapter",
  "adapter_version": "1.0.0",
  "requested_capabilities": ["documentation_draft"],
  "classification": "Estate Internal",
  "repository_root": ".",
  "source_commit": "EXAMPLE-40-character-source-commit",
  "sandbox_mode": "workspace-write",
  "codex_provider_profile": "EXAMPLE-approved-profile",
  "approval_policy": "never",
  "bypass_flags": [],
  "cloud_allowed": false,
  "cloud_apply_requested": false,
  "cloud_dispatch_requested": false,
  "danger_full_access_requested": false,
  "authorized_read_paths": ["docs/operations", "src"],
  "authorized_write_paths": ["docs/operations/example-output/Runbook.md"],
  "prohibited_paths": [".git", "archive", "runtime"],
  "exact_expected_outputs": ["docs/operations/example-output/Runbook.md"],
  "acceptance_criteria": ["exact artifact exists", "receipt validates"],
  "validation_commands": ["git diff --check"],
  "timeout_seconds": 180,
  "cancellation_state": "not_requested",
  "steward_authorization_reference": "EXAMPLE-steward-authorization",
  "traffic_controller_authorization_reference": "EXAMPLE-traffic-authorization",
  "decision_reference": "EXAMPLE-decision",
  "boundary_review_reference": "EXAMPLE-boundary-review",
  "evidence": {
    "observed_at": "EXAMPLE-observed-at",
    "expires_at": "EXAMPLE-expires-at",
    "qualification_references": ["EXAMPLE-qualification.json"],
    "health_references": ["EXAMPLE-health.json"],
    "availability_references": ["EXAMPLE-availability.json"],
    "capacity_references": ["EXAMPLE-capacity.json"],
    "authorization_references": ["EXAMPLE-authorization.json"]
  },
  "unrestricted_shell_authority": false,
  "automatic_merge_authority": false,
  "autonomous_institutional_acceptance_authority": false
}
```

## Common failures

| Failure | Correction |
|---|---|
| Provider or adapter mismatch | Use the canonical catalog identity and registered adapter version. |
| Unsupported capability | Limit the request to the five supported capabilities and obtain Helen evidence for each. |
| Expired evidence | Refresh qualification, health, availability, capacity, and authorization evidence. |
| Output outside write scope | Declare the exact repository-relative output and authorize only its bounded scope. |
| `.git`, `archive`, or traversal path rejected | Remove the prohibited or escaping path; never broaden the scope. |
| Missing authorization or decision reference | Obtain the current Steward, Traffic Controller, decision, and boundary references. |
| Cancellation requested | Keep the request blocked and create a new authorized attempt only after cancellation is cleared. |
| Validation passes but execution is not authorized | Continue through Grace, Helen, PTM, Engineering, and Dispatch; validation alone has no execution authority. |

## Canonical references

- Validator: [`Validate-GovernedCodexCommission.ps1`](../../scripts/Validate-GovernedCodexCommission.ps1)
- Template: [`Governed_Codex_Commission_Request.template.json`](templates/Governed_Codex_Commission_Request.template.json)
- Provider catalog: [`config/providers/catalog.json`](../../config/providers/catalog.json)
- Canonical adapter: [`codex_bridge_execution_provider_adapter.py`](../../src/estate/core/codex_bridge_execution_provider_adapter.py)
- Capability lifecycle: [`engineering_capability_enablement.py`](../../src/estate/core/engineering_capability_enablement.py)
- Schemas: [`schemas/engineering`](../../schemas/engineering/)
- Tests: [`test_governed_codex_commission_validator.py`](../../tests/operations/test_governed_codex_commission_validator.py), [`test_codex_cli_execution_adapter.py`](../../tests/test_codex_cli_execution_adapter.py), and [`test_engineering_capability_enablement.py`](../../tests/test_engineering_capability_enablement.py)
- Existing operator lifecycle: [`Governed_Codex_Engineering_Quick_Start.md`](Governed_Codex_Engineering_Quick_Start.md)
