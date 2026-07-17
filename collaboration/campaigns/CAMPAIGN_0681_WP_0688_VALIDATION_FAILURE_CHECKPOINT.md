# CAMPAIGN-0681 — WP-0688 Validation-Failure Checkpoint

- **Campaign / checkpoint:** `CAMPAIGN-0681 / WP-0688 affected-subsystem validation`
- **Prepared by / at:** `Codex / 2026-07-17T20:06:00Z`
- **Branch:** `campaign/0681-estate-operationalization`
- **Authorization base / current HEAD:** `75f70f358f1cf10596845a719cc553eeb320c49f` / `75f70f358f1cf10596845a719cc553eeb320c49f`
- **Outcome:** `fail_closed`
- **Authority requested:** Chief Architect repair-scope decision; this checkpoint grants no completion, gate release, acceptance, merge, deployment, spending, staffing, or disclosure authority.

## Campaign state

| Field | Value |
|---|---|
| completed packages | none |
| active package | `WP-0688` |
| dependency state | WP-0688 has no package dependency; G0 prerequisites passed in the one required preflight |
| gate state | before G1; G1 not reached or released |
| validation state | affected-subsystem suite failed: 78 passed, 2 failed |
| retry state | full targeted suite executed once; two failing tests rerun once in isolation with the same failures |
| failure state | pre-existing CLI root-selection isolation failures; no WP-0688 runtime file was changed |
| escalation state | stopped under manifest `validation_failure: stop_and_checkpoint` policy |
| protected decisions pending | authorize a bounded repair or identify an already-authorized canonical successor; later package execution remains prohibited |
| next permitted action | Chief Architect authorizes/assigns repair of the canonical CLI root-selection behavior, then WP-0688 validation resumes from this branch |

## Work present but not completed

The four WP-0688 repository-assessment deliverables are present in the working tree:

- `docs/architecture/estate_operational_current_state_map.md`
- `docs/architecture/estate_operational_canonical_reuse_map.md`
- `docs/architecture/estate_operational_authority_map.md`
- `operations/departments/engineering/CAMPAIGN_0681_gap_and_conflict_register.md`

No WP-0688 completion receipt or package commit was created because validation did
not pass. WP-0689 and WP-0690 were not started.

## Exact validation evidence

| Exact command | Exit | Result |
|---|---:|---|
| `python -m pytest -q tests/test_operational_events.py tests/test_operational_campaign_runtime.py tests/test_execution_dispatch.py tests/test_helen_workforce.py tests/test_grace_operations_runtime.py tests/test_mailbox_index.py tests/test_work_package_validation.py tests/test_service_health_registry.py tests/test_estate_capability_registry.py tests/test_office_decision_support.py` | 1 | 78 passed, 2 failed in 29.27s |
| `python -m pytest -q tests/test_service_health_registry.py::test_service_health_registry_cli tests/test_estate_capability_registry.py::test_estate_capability_registry_cli` | 1 | 2 failed in 0.95s; failures reproduced independently |

### Failure 1

`test_service_health_registry_cli` expected
`<tmp>/runtime/services/service_health_registry.json`, but it did not exist after the
CLI completed. `src/estate/core/service_health_registry.py` selects `ESTATE_ROOT`
when it exists instead of using the subprocess working directory.

### Failure 2

`test_estate_capability_registry_cli` expected one fixture capability but observed
six repository capabilities. `src/estate/core/estate_capability_registry.py` uses
the same repository-first root selection.

The test run generated repository reports as side effects of this root leakage.
Those generated changes and the untracked scheduler status artifact were removed;
only the four WP-0688 deliverables and this checkpoint remain.

## Recovery boundary

WP-0688 explicitly prohibits operational runtime changes. Repairing either CLI in
the WP-0688 commit would broaden package scope and mix a pre-existing subsystem fix
with the canonical inventory. Resume only after a separately authorized repair or
an authoritative ruling that names an already-approved repair lane. On resume, run
the complete affected suite, create the completion receipt with exact results, run
the package validator and `git diff --check`, then create the single bounded
WP-0688 commit only if all required validation passes.
