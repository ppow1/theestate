# CAMPAIGN-0681 — Protected Gate G1 Durable Checkpoint

- Campaign: `CAMPAIGN-0681 — Estate Operationalization`
- Checkpoint date: `2026-07-17`
- Branch: `campaign/0681-estate-operationalization`
- Gate: `G1 — Canonical and authority freeze`
- State: `reached; awaiting protected Chief Architect review; not released`
- Checkpoint HEAD before this checkpoint is added: `2445c2838694d53c10042be06a21549d72714009`
- Working tree before checkpoint creation: clean (`git status --porcelain` returned no output)

## Completed bounded commits

| Kind | Commit | Scope |
|---|---|---|
| authorized prerequisite repair | `6bc80477c113b2b69ec29f3c4dd2b3448c160d2b` | repair only the service-health and capability-registry CLI root precedence |
| WP-0688 | `abe8db0ddbf910e10668e8b5a13ba33d7bca07a8` | current-state, canonical-reuse and authority maps; gap/conflict register and failure checkpoint |
| WP-0689 | `739977d53662d05150b5d323e30289e2671fa7c9` | normalized operational state/event schema, transition/replay contract, fixtures, tests and receipt |
| WP-0690 | `2445c2838694d53c10042be06a21549d72714009` | authority-aware action taxonomy, schema, evaluator, office-boundary tests and receipt |

The WP-0690 commit will be amended only to include this required checkpoint; its
final commit identity supersedes the pre-checkpoint identity above without creating
a second WP-0690 package commit.

## Validation ledger

| Package / repair | Exact command | Exit | Result |
|---|---|---:|---|
| repair | `python -m pytest -q tests/test_service_health_registry.py::test_service_health_registry_cli tests/test_estate_capability_registry.py::test_estate_capability_registry_cli` | 0 | 2 passed in 0.96s |
| repair / WP-0688 affected subsystem | `python -m pytest -q tests/test_operational_events.py tests/test_operational_campaign_runtime.py tests/test_execution_dispatch.py tests/test_helen_workforce.py tests/test_grace_operations_runtime.py tests/test_mailbox_index.py tests/test_work_package_validation.py tests/test_service_health_registry.py tests/test_estate_capability_registry.py tests/test_office_decision_support.py` | 0 | 80 passed in 26.67s |
| WP-0688 | `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0688` | 0 | package validation passed |
| WP-0689 focused | `python -m pytest -q tests/test_operational_transition_contract.py tests/test_operational_events.py tests/test_operational_status.py` | 0 | 28 passed in 1.24s |
| WP-0689 affected subsystem | `python -m pytest -q tests/test_operational_transition_contract.py tests/test_operational_events.py tests/test_operational_status.py tests/test_operational_campaign_runtime.py tests/test_codex_campaign_execution.py tests/test_work_package_validation.py` | 0 | 67 passed in 24.13s |
| WP-0689 schemas | `python -m json.tool schemas/operations/estate_operational_event_v1.schema.json > $null` and `python -m json.tool schemas/operations/estate_operational_projection_v1.schema.json > $null` | 0 | both schema documents parsed |
| WP-0689 | `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0689` | 0 | package validation passed |
| WP-0690 focused | `python -m pytest -q tests/test_operational_action_taxonomy.py tests/test_operational_transition_contract.py` | 0 | 35 passed in 0.12s |
| WP-0690 affected subsystem | `python -m pytest -q tests/test_operational_action_taxonomy.py tests/test_operational_transition_contract.py tests/test_office_decision_support.py tests/test_execution_dispatch.py tests/test_grace_operations_runtime.py tests/test_helen_workforce.py tests/test_mailbox_index.py tests/test_resident_authority.py tests/test_work_package_validation.py` | 0 | 104 passed in 27.53s |
| WP-0690 schema | `python -m json.tool schemas/operations/estate_operational_action_v1.schema.json > $null` | 0 | schema document parsed |
| WP-0690 initial validator | `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0690` | 1 | validator required `## Required Work`; the existing `## Scope` heading was renamed without changing content |
| WP-0690 corrected validator | `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0690` | 0 | package validation passed |
| all packages / final checkpoint | `pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0688; pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0689; pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0690; git diff --check` | 0 | all three package validators passed; no whitespace errors |

Validation runs generated repository projections as test side effects. Each was
verified against the clean starting state and restored; the transient scheduler
status artifact was removed. No test was weakened, skipped, deleted, or marked
expected-failure.

## G1 evidence and unresolved review

The required G1 evidence is present:

- canonical reuse map and current-state inventory;
- office-authority map and conflict/duplication register;
- versioned operational state, event, transition and replay contract;
- authority-aware action taxonomy and deterministic evaluation surface;
- independently readable receipts and bounded commits for WP-0688 through WP-0690.

G1 release remains a protected Chief Architect decision. This checkpoint records
package completion evidence only and does not express architectural acceptance,
gate release, merge, deployment, institutional acceptance, staffing, spending,
disclosure, or campaign closure.

## Resume boundary

Completed packages: `WP-0688`, `WP-0689`, `WP-0690`.

Active gate: `G1`, awaiting Chief Architect review.

Next permitted action: present this checkpoint, the three completion receipts, the
four bounded commit identities, and the gap/conflict register to the Chief Architect
for an explicit G1 decision. Do not execute WP-0691 or any later package until a
durable G1 release is recorded through the protected authority lane.
