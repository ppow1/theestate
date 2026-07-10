# WP-0622 - Operational Target Resolution and Validation Binding

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-09

## Mission

Repair and strengthen operational target resolution so the automatic post-merge validation pipeline can resolve the Estate target correctly and scale to CueMastery and future repositories without hard-coded target assumptions.

The first live WP-0621 demonstration failed cleanly with:

```text
unknown target estate
```

The registry currently defines the Estate target as:

```text
estate-main
```

while the demonstration path emits:

```text
estate
```

WP-0622 must fix this immediate mismatch and establish a durable target-resolution and validation-binding layer for all future Operational Targets.

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is repository implementation work across Operational Targets, Post-Merge Audit, CLI, runtime configuration, tests, documentation, and validation recipes. It should be implemented by Codex Cloud/Web and locally demonstrated after merge.
```

Local runtime required:

```text
false for implementation; true for end-to-end demonstration
```

Capacity note:

```text
Do not use Codex CLI for normal implementation. No live provider execution is required.
```

## Architectural Position

Operational requests should reference targets through a stable identity and resolution contract.

The system must support:

```text
canonical target IDs
human-friendly aliases
repository full names
local paths
Codex environment names
future department-owned target names
```

All of these should resolve to one canonical Operational Target record.

The resolver must not create duplicate targets, silently invent target configuration, or bypass target enablement and capability checks.

## Immediate Repair

The demonstration command:

```powershell
python -m estate.cli.main post-merge-audit demonstrate --work-package WP-0620 --pr 199 --json
```

must resolve to the canonical Estate target and proceed past target lookup.

Acceptable approaches include:

```text
change demonstration default target from estate to estate-main
```

and/or:

```text
register estate as a stable alias for estate-main
```

The durable implementation should do both where appropriate: emit canonical IDs internally and support aliases at external boundaries.

## Required Scope

Implement:

1. Canonical Operational Target Resolver.
2. Alias support for Operational Targets.
3. Validation binding model for Git/validation/audit-capable targets.
4. Resolution by target ID, alias, repository full name, local path, and environment name where configured.
5. Ambiguity detection.
6. Disabled/paused/retired/blocked target enforcement.
7. Capability enforcement for validation and audit requests.
8. Demonstration default repair.
9. CLI commands to resolve and inspect bindings.
10. Office/background status visibility for target resolution failures.
11. Deterministic tests and documentation.

## Canonical Target Requirements

Each target should support fields such as:

```text
target_id
aliases
repository_full_name
local_path
base_branch
validation_root
workspace_root
capabilities
watch_state
validation_profile
environment_names
metadata
```

The existing `estate-main` target remains canonical.

Required initial alias mapping:

```text
estate -> estate-main
theestate -> estate-main
ppow1/theestate -> estate-main
```

CueMastery should be representable with aliases such as:

```text
cue-mastery
CueMastery
```

but must remain an import candidate until its repository/local configuration is explicitly completed.

## Target Resolution Contract

Add a result model containing:

```text
requested_identifier
resolved
canonical_target_id
resolution_method
target
warnings
errors
```

Allowed resolution methods:

```text
canonical_id
alias
repository_full_name
local_path
environment_name
not_found
ambiguous
```

Resolution rules:

1. Exact canonical ID wins.
2. Exact normalized alias may resolve.
3. Exact repository full name may resolve.
4. Normalized local path may resolve.
5. Exact configured environment name may resolve.
6. Multiple matches must return `ambiguous`; never choose silently.
7. Unknown identifiers must return structured `not_found` evidence.

## Validation Binding Contract

For a target to participate in automatic post-merge validation, require:

```text
canonical target exists
target state permits processing
git capability exists
validation capability exists
audit capability exists
local_path or workspace source is configured
base_branch is configured
workspace_root is configured
validation_root is configured
```

Return a binding result with:

```text
ready
canonical_target_id
repository_full_name
source_path
base_branch
workspace_root
validation_root
missing_requirements
warnings
```

Do not start validation when the binding is incomplete.

## Request Normalization

When a post-merge audit request is created or claimed:

```text
resolve target identifier
write canonical_target_id
retain requested_target_identifier for audit history
write target_resolution_method
write target_binding_status
```

Persist canonical target IDs in request state after successful resolution.

## Demonstration Repair

Update `PostMergeAuditProcessor.demonstrate` so it:

- defaults to `estate-main`, or
- resolves the alias `estate` before writing the request,
- records the canonical target ID,
- and proceeds into the WP-0621 validation pipeline.

The repaired demonstration should no longer fail with `unknown target estate`.

## CLI Requirements

Add commands using repository conventions. Suggested commands:

```powershell
python -m estate.cli.main operational-targets resolve --target estate --json
python -m estate.cli.main operational-targets binding --target estate-main --json
python -m estate.cli.main operational-targets aliases --json
python -m estate.cli.main post-merge-audit demonstrate --work-package WP-0620 --pr 199 --json
```

If actual CLI style differs, follow existing conventions and document the real commands.

## Office / Background Status

Expose:

```text
latest_target_resolution
latest_target_resolution_status
latest_target_resolution_method
latest_target_binding_ready
latest_target_binding_gaps
unresolved_target_requests
ambiguous_target_requests
```

## Out of Scope

Do not:

```text
create a second target registry
create a new dispatch queue
execute providers
execute dispatch work
perform network discovery of repositories
silently enable import candidates
invent missing CueMastery paths
merge or commit code automatically
create Steward acceptance
```

## Expected Artifacts

Expected files:

```text
src/estate/core/operational_target_resolution.py
src/estate/core/operational_target_validation_binding.py
tests/test_operational_target_resolution.py
tests/test_operational_target_validation_binding.py
docs/integration/operational_target_resolution_and_validation_binding.md
```

Expected integration touchpoints:

```text
src/estate/core/operational_targets.py
src/estate/core/operational_targets_runtime.py
src/estate/core/post_merge_audit_processor.py
src/estate/core/post_merge_validation_pipeline.py
src/estate/core/steward_command_center.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

## Test Requirements

Tests must cover:

- `estate-main` resolves by canonical ID,
- `estate` resolves to `estate-main`,
- `theestate` resolves to `estate-main`,
- `ppow1/theestate` resolves to `estate-main`,
- canonical ID wins over alias,
- ambiguous aliases fail safely,
- unknown target returns structured not-found result,
- paused/disabled/retired/blocked targets cannot bind for validation,
- import candidate cannot bind until configured and enabled,
- missing validation/audit/git capability blocks binding,
- missing local path or base branch blocks binding,
- audit request preserves requested identifier and canonical ID,
- demonstration no longer returns `unknown target estate`,
- successful target resolution proceeds into validation pipeline,
- Office/background status exposes resolution/binding state,
- provider execution remains false,
- dispatch execution remains false.

## Validation Rings

### Ring 0

```powershell
Clear-Host
cd A:\theestate
Test-Path src\estate\core\operational_target_resolution.py
Test-Path src\estate\core\operational_target_validation_binding.py
Test-Path tests\test_operational_target_resolution.py
Test-Path tests\test_operational_target_validation_binding.py
Test-Path docs\integration\operational_target_resolution_and_validation_binding.md
python -m py_compile src\estate\core\operational_target_resolution.py
python -m py_compile src\estate\core\operational_target_validation_binding.py
```

### Ring 1

```powershell
Clear-Host
cd A:\theestate
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_operational_target_resolution.py tests/test_operational_target_validation_binding.py tests/test_post_merge_audit_processor.py tests/test_post_merge_validation_pipeline.py --basetemp Temp/pytest-operational-target-resolution
python -m estate.cli.main operational-targets resolve --target estate --json
python -m estate.cli.main operational-targets binding --target estate-main --json
python -m estate.cli.main validate-work-package --id WP-0622 --json
```

### Ring 2

Review whether the resolver establishes stable canonical identity, prevents ambiguous or disabled target execution, supports future multi-repository expansion, and preserves existing authority boundaries.

### Ring 3

Use only if Ring 1 and Ring 2 are insufficient.

### Ring 4

Chief Architect / Steward acceptance confirms target aliases and validation bindings are now stable enough for automatic multi-target background operations.

## Demonstration Requirement

After merge, run:

```powershell
Clear-Host
cd A:\theestate
git pull --ff-only origin main
python -m estate.cli.main operational-targets resolve --target estate --json
python -m estate.cli.main operational-targets binding --target estate-main --json
python -m estate.cli.main post-merge-audit demonstrate --work-package WP-0620 --pr 199 --json
python -m estate.cli.main post-merge-audit status --json
```

Expected result:

```text
estate resolves to estate-main
target binding is ready
demonstration proceeds past target lookup
standard validation executes
Ring 2 prompt is generated
verdict artifact is written
no provider or dispatch execution occurs
```

## Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0622_codex_done.json
```

Receipt must include:

```text
provider_execution_performed: false
dispatch_execution_performed: false
canonical_estate_target: estate-main
aliases_registered
demonstration_work_package
demonstration_target_resolution
demonstration_verdict
```

## Promotion Criteria

Ready when aliases resolve safely, validation bindings enforce capabilities and state, the demonstration proceeds past target lookup into the automatic validation pipeline, deterministic tests pass, production readiness is true, Ring 2 recommends Chief Architect review, and no provider or dispatch execution occurs.
