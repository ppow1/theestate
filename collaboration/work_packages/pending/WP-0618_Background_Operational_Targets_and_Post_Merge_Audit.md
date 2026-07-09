# WP-0618 - Background Operational Targets and Post-Merge Audit Function

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-09

## Mission

Extend WP-0617 Background Operations into a configurable, multi-target operational monitoring function.

This package must implement the foundation for Background Operations to watch and manage operational targets such as repositories, environments, services, and future department-owned systems. Git hygiene and post-merge audit are the first required capabilities, but the architecture must be expandable for CueMastery, Engineering Department repositories, infrastructure targets, AI services, and future Estate-managed operational targets.

The goal is not another ad hoc tool. The goal is a background Estate function with a real control surface.

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is repository implementation work touching background operations, target registry, Git hygiene, post-merge audit, CLI, Office status, tests, and documentation. It should be implemented by Codex Cloud/Web. It must not require live provider execution, Codex CLI, Ollama, or network access in deterministic tests.
```

Local runtime required:

```text
false for implementation; true for operational use after merge
```

Capacity note:

```text
Do not use Codex CLI unless Cloud/Web cannot complete the package. Validate locally with deterministic tests and Ring 2 review.
```

## Architectural Position

This is an Estate function implemented by tools.

Estate functions:

```text
Operational Target Registry
Background Watch Control Surface
Git Hygiene Watch
Post-Merge / Post-Promotion Audit
Validation Evidence Routing
Office-visible Verdict Reporting
```

Tools used by those functions:

```text
git fetch / status / worktree / clean clone
work-package validation recipes
production-readiness validator
Ring 2 local GPU review prompt
Office/background status artifacts
```

## Core Principle

```text
Background Operations watches registered operational targets, not just one repository.
```

An operational target may be:

```text
git repository
Codex environment
local workspace
service
infrastructure node
AI service
model library
Engineering project
future department system
```

Git monitoring is only the first target capability.

## Problem

Current post-merge validation is too manual. Audits are slowed by stale local main, wrong branch, unstaged runtime files, untracked review folders, stash accumulation, and repeated pull/retry loops.

At the same time, the Estate is expanding beyond `ppow1/theestate`. CueMastery and future Engineering Department work will need similar background monitoring, validation, and verdict workflows.

The system needs a registry and control surface so the Steward or authorized staff can decide which targets are watched, paused, imported, retired, or excluded.

## Required Scope

Implement:

1. Operational Target Registry model.
2. Operational Target Watch Control model.
3. Control surface payload and CLI commands to list, enable, disable, pause, resume, import, retire, and inspect targets.
4. Target capability model for Git, validation, audit, build, deploy, service-health, and future capabilities.
5. Git hygiene watcher for registered Git-capable targets.
6. Post-merge / post-promotion audit request model.
7. Clean validation workspace policy for audit-capable targets.
8. Validation evidence root configuration outside the active repository.
9. Post-merge audit verdict model.
10. Background Operations integration so watches create governed requests.
11. Office / command-center summary fields.
12. Deterministic tests and documentation.

## Initial Targets

The implementation should support registering targets like:

```text
estate-main
cue-mastery
ionoge-vps
ionoge-site
```

Only `estate-main` must be fully wired in v1 if repository information for the others is incomplete. The others must be representable as registered or importable targets without hardcoding assumptions.

## Target Registry Fields

Each operational target should support fields such as:

```text
target_id
display_name
target_type
owner_department
repository_full_name
local_path
base_branch
validation_root
workspace_root
watch_enabled
watch_state
capabilities
acceptance_authority
office_surface
classification
metadata
```

Allowed watch states:

```text
enabled
paused
disabled
retired
import_candidate
blocked
```

## Control Surface Requirements

Provide a real control surface through CLI and Office payloads.

Required commands, using repository naming style as appropriate:

```powershell
python -m estate.cli.main operational-targets list --json
python -m estate.cli.main operational-targets show --target estate-main --json
python -m estate.cli.main operational-targets enable --target estate-main --json
python -m estate.cli.main operational-targets pause --target estate-main --json
python -m estate.cli.main operational-targets disable --target estate-main --json
python -m estate.cli.main operational-targets import-candidate --target cue-mastery --json
python -m estate.cli.main operational-targets status --json
```

If existing CLI conventions require different names, follow repository convention and document actual commands.

Control surface must expose:

```text
available targets
watched targets
paused targets
blocked targets
import candidates
last watch cycle
latest audit verdict per target
latest Git hygiene issue per target
```

No fake controls. Every exposed control must call a real handler.

## Git Hygiene Requirements

For Git-capable targets, Background Operations should detect and report:

```text
local main behind origin/main
local main ahead of origin/main
wrong branch
detached HEAD
dirty validation workspace
untracked runtime evidence inside source repo
missing completion receipt
missing validation recipe
production-ready but Ring 2 missing
Ring 2 complete but Steward acceptance missing
```

The active developer tree must not be repaired automatically. It may be reported. Stashes are emergency recovery only and must not be part of normal audit flow.

## Validation Evidence Root Requirements

Transient operational evidence must not dirty the Estate repo.

Define configurable validation output roots. Suggested default:

```text
A:\EstateRuntime\validation
```

or, if using CA5's narrower proposed root:

```text
A:\EstateValidation
```

Support structure such as:

```text
reports
ring2
captures
handoff
archive
```

Inside `A:\theestate`, keep source code, work packages, validation recipes, completion receipts, committed validation contracts, and curated accepted validation reports only.

Runtime validation attempts, Ring 2 folders, local GPU review attempts, large captures, temporary logs, and copy/paste handoff bundles should go outside the repo unless explicitly promoted.

## Post-Merge Audit Requirements

For audit-capable targets, implement:

```text
merge or local promotion detected
  -> background audit request created
  -> clean validation workspace prepared
  -> expected branch/commit/files verified
  -> deterministic validation run
  -> production readiness checked
  -> Ring 2 prompt prepared or run when explicitly enabled
  -> final verdict artifact written
  -> Office/background status updated
```

The clean validation workspace should use a configured worktree or clone path rather than the active developer tree.

Suggested default:

```text
A:\EstateRuntime\workspaces\audit\<target_id>
```

Tests must use temporary paths.

## Post-Merge Audit Verdicts

Allowed verdicts:

```text
accepted
accepted_with_notes
ring2_required
needs_repair
blocked
not_merged
workspace_failed
validation_failed
```

Verdict fields should include:

```text
audit_id
target_id
work_package_id
source_kind
source_reference
verdict
merge_or_promotion_verified
validation_workspace_clean
validation_workspace_on_expected_branch
expected_files_present
deterministic_validation_status
production_ready
receipt_status
ring2_status
ring2_verdict
provider_execution_performed
dispatch_execution_performed
blocking_reasons
non_blocking_findings
artifacts
created_at
metadata
```

## Background Operations Integration

Add or extend WP-0617 watches for:

```text
operational_target_watch_needed
git_hygiene_review_needed
post_merge_audit_needed
validation_evidence_root_drift
ring2_review_needed
steward_acceptance_needed
```

Watches may create governed requests and status artifacts. They must not approve, merge, execute providers, or create institutional acceptance.

## Office / Command Center Integration

Expose summary fields such as:

```text
operational_targets_available
watched_targets_count
paused_targets_count
blocked_targets_count
import_candidates_count
latest_git_hygiene_issue
latest_post_merge_audit_verdict
latest_target_requiring_attention
validation_evidence_root
warnings
```

## Out of Scope

Do not implement provider execution, autonomous code repair, automatic merging, automatic commits, destructive cleanup, a new provider registry, a new dispatch queue, a new Office, or a competing event system.

This package may observe and request. It may not become authority.

## Expected Artifacts

Expected files:

```text
src/estate/core/operational_targets.py
src/estate/core/operational_targets_runtime.py
src/estate/core/post_merge_audit.py
src/estate/core/post_merge_audit_runtime.py
tests/test_operational_targets.py
tests/test_operational_targets_runtime.py
tests/test_post_merge_audit.py
tests/test_post_merge_audit_runtime.py
docs/integration/background_operational_targets_and_post_merge_audit.md
```

Integration touchpoints if clean:

```text
src/estate/cli/main.py
src/estate/core/background_operations.py
src/estate/core/background_operations_runtime.py
src/estate/core/steward_command_center.py
src/estate/core/work_package_validation.py
src/estate/core/production_readiness_validation.py
```

## Runtime Artifacts

Use paths such as:

```text
runtime/operational_targets/registry.json
runtime/operational_targets/status/latest.json
runtime/operational_targets/status/summary.json
runtime/post_merge_audit/requests/<audit_id>.json
runtime/post_merge_audit/verdicts/<audit_id>.json
runtime/post_merge_audit/verdicts/<audit_id>.md
runtime/post_merge_audit/ring2_prompts/<audit_id>.md
```

Transient evidence should default outside the repo under the configured validation evidence root.

## Test Requirements

Tests must cover:

- target registration,
- list/show/status control surface,
- enable/pause/disable/retire state transitions,
- import candidate representation,
- active tree dirty state reported but not stashed,
- validation workspace dirty state blocks audit,
- expected files missing blocks audit,
- validation recipe pass produces accepted or ring2_required verdict,
- production readiness false blocks acceptance,
- Ring 2 prompt generation works without Ollama,
- validation evidence root defaults outside active repo,
- background watch creates post_merge_audit_needed request,
- Office summary exposes targets and audit status,
- no provider execution occurs,
- no dispatch execution occurs.

## Validation Rings

### Ring 0 - Static / Structural Validation

```powershell
Clear-Host
cd A:\theestate
Test-Path src\estate\core\operational_targets.py
Test-Path src\estate\core\operational_targets_runtime.py
Test-Path src\estate\core\post_merge_audit.py
Test-Path src\estate\core\post_merge_audit_runtime.py
Test-Path docs\integration\background_operational_targets_and_post_merge_audit.md
python -m py_compile src\estate\core\operational_targets.py
python -m py_compile src\estate\core\operational_targets_runtime.py
python -m py_compile src\estate\core\post_merge_audit.py
python -m py_compile src\estate\core\post_merge_audit_runtime.py
```

### Ring 1 - Deterministic Test Validation

```powershell
Clear-Host
cd A:\theestate
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_operational_targets.py tests/test_operational_targets_runtime.py tests/test_post_merge_audit.py tests/test_post_merge_audit_runtime.py --basetemp Temp/pytest-operational-targets-post-merge-audit
python -m estate.cli.main validate-work-package --id WP-0618 --json
```

Expected evidence:

```text
runtime/validation/work_packages/WP-0618_validation.json
operations/validation/reports/WP-0618_validation.md
collaboration/work_packages/completions/WP-0618_codex_done.json
```

### Ring 2 - Local GPU Reasoning Review

Reviewer questions:

```text
Does WP-0618 make Git hygiene and post-merge audit a background Estate function rather than an ad hoc tool?
Does it support multiple operational targets, including future CueMastery/Engineering targets?
Does it include a real enable/pause/disable/import/retire control surface?
Does it keep transient validation evidence out of the source repo by default?
Does it avoid normal-use stash accumulation?
Does it preserve Chief Architect / Steward acceptance?
Does it avoid provider execution and dispatch execution?
Is it ready for Chief Architect review?
```

### Ring 3 - CLI Escalation Validation

Use only if Ring 1 and Ring 2 are insufficient.

### Ring 4 - Institutional Acceptance

Chief Architect / Steward acceptance confirms the target registry, control surface, Git hygiene, validation evidence root, and post-merge audit function are now part of Background Operations.

## Completion Receipt Requirements

Create:

```text
collaboration/work_packages/completions/WP-0618_codex_done.json
```

Receipt must include validator-accepted fields:

```text
work_package_id
provider
codex_status
completed_at
branch
summary
files_changed
tests_run
validation_commands_run
known_limitations
ready_for_ca_review
pull_request_url or pull_request_not_applicable_reason
merge_authority or merge_authority_equivalent
provider_execution_performed
dispatch_execution_performed
```

## Promotion Criteria

Ready when Ring 0 passes, Ring 1 passes, production readiness is true, Ring 2 recommends Chief Architect review, multi-target registration works, enable/pause/disable controls work, transient evidence defaults outside the repo, and one final audit verdict artifact is produced.

## Completion Signal

Create the completion receipt and report validation evidence paths.
