# WP-0626 - Cleanroom Post-Merge Audit Service

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-10

## Mission

Make the automatic validation loop actually automatic.

The current loop still depends on the Steward manually clearing generated files, resolving dirty-tree state, pulling `main`, and retrying commands. That fails the purpose of Background Operations.

WP-0626 must remove the active development checkout from the audit path. Post-merge validation must run in a disposable clean workspace synchronized to the target branch, while runtime evidence is written outside the repository.

Required flow:

```text
merge discovered
  -> isolated audit workspace prepared
  -> target branch synchronized
  -> exact merged revision checked out
  -> deterministic validation executed
  -> Ring 2 evidence prepared
  -> verdict published
  -> workspace removed or archived
```

The Steward must not manage stashes, restore generated pointers, switch branches, or clean the working tree before routine audits.

## Provider Assignment Guidance

Recommended provider: `codex_cloud_web`  
Local runtime required: true for demonstration  
Do not use Codex CLI for normal implementation.

## Core Requirements

### 1. Never validate in the active checkout

`A:\theestate` is the active development checkout and may legitimately contain local work.

Automatic audits must use a separate workspace under the target's configured workspace root, for example:

```text
A:\EstateRuntime\workspaces\audit\estate-main\<audit_id>
```

Use `git worktree`, a local clone, or an equivalent isolated checkout. Prefer the simplest deterministic implementation compatible with Windows.

### 2. Synchronize without stashing

The service must:

```text
fetch configured remote when enabled
resolve origin/<base_branch>
verify requested merge/source commit is reachable
create or reset the isolated workspace to that revision
record synchronization evidence
```

It must not stash, reset, restore, clean, switch, commit, or otherwise modify the active checkout.

### 3. Externalize transient evidence

Write transient audit material outside the repository:

```text
A:\EstateValidation\reports
A:\EstateValidation\ring2
A:\EstateValidation\captures
A:\EstateValidation\handoff
A:\EstateValidation\archive
```

The root must be configurable through Operational Target configuration.

Repository content should include only committed recipes, receipts, contracts, and explicitly promoted institutional reports.

### 4. Workspace lifecycle

Implement states:

```text
requested
preparing
synchronized
validating
ring2_pending
completed
blocked
failed
cleaning
archived
```

Record:

```text
workspace_path
active_checkout_path
remote_ref
resolved_commit
base_branch
fetch_performed
workspace_method
cleanup_status
errors
warnings
```

Clean successful disposable workspaces automatically. Preserve failed workspaces only when configured for diagnosis.

### 5. Git hygiene semantics

Git hygiene findings in the active checkout must be visible but must not block an isolated audit unless they indicate repository corruption or target misconfiguration.

Separate:

```text
active_checkout_dirty
isolated_workspace_dirty
branch_sync_status
revision_reachable
```

Only isolated-workspace or synchronization failure may block automatic validation.

### 6. Bounded batch processing

One Operations Runtime cycle must process admitted requests up to `max_audit_requests`, not merely start one.

For each admitted request:

```text
prepare clean workspace
run validation
publish verdict
prepare Ring 2 artifact when required
continue until limit reached or fatal service failure occurs
```

A single failed audit must not prevent later admitted requests from being attempted.

### 7. Service integration

Background Operations / Operations Runtime should be able to perform the full loop with one command:

```powershell
python -m estate.cli.main operations-runtime run-once --discover-merges --auto-admit --process-audits --max-audit-requests 5 --json
```

No preparatory Git commands should be required from the Steward.

## Required Implementation

Expected files:

```text
src/estate/core/audit_workspace_service.py
src/estate/core/audit_workspace_runtime.py
tests/test_audit_workspace_service.py
tests/test_audit_workspace_runtime.py
docs/integration/cleanroom_post_merge_audit_service.md
```

Expected integration touchpoints:

```text
src/estate/core/post_merge_audit_processor.py
src/estate/core/post_merge_validation_pipeline.py
src/estate/core/operations_runtime.py
src/estate/core/operations_runtime_service.py
src/estate/core/operational_target_validation_binding.py
src/estate/core/steward_command_center.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

## Test Requirements

Tests must prove:

- a dirty active checkout does not block an isolated audit,
- no stash is created,
- no active-checkout files are changed,
- isolated workspace resolves the requested commit,
- validation runs from the isolated workspace,
- transient evidence is written outside the repo,
- successful workspace cleanup works,
- failed workspace retention is configurable,
- one failed audit does not stop the remaining admitted batch,
- up to five admitted audits are attempted in one cycle,
- provider and dispatch execution remain false.

## Validation

```powershell
Clear-Host
cd A:\theestate
python -m py_compile src\estate\core\audit_workspace_service.py src\estate\core\audit_workspace_runtime.py
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_audit_workspace_service.py tests/test_audit_workspace_runtime.py tests/test_post_merge_audit_processor.py tests/test_operations_runtime.py --basetemp Temp/pytest-cleanroom-audit
python -m estate.cli.main validate-work-package --id WP-0626 --json
```

## Live Demonstration

The demonstration must intentionally leave generated or harmless local changes in `A:\theestate`, then run only:

```powershell
Clear-Host
cd A:\theestate
$env:PYTHONPATH = "src"
python -m estate.cli.main operations-runtime run-once --discover-merges --auto-admit --process-audits --max-audit-requests 5 --json
```

Expected result:

```text
active checkout dirtiness is reported but not blocking
no stash is created
no branch switching occurs in A:\theestate
isolated workspaces synchronize to merged revisions
up to five audits are attempted
verdicts and Ring 2 artifacts are published externally
active checkout remains unchanged
```

## Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0626_codex_done.json
```

Report workspace method, external evidence root, audits attempted/completed/failed, active-checkout modifications performed (must be false), stashes created (must be zero), and false provider/dispatch execution values.

## Promotion Criteria

Ready when the Steward can run one Operations Runtime command from a dirty active checkout and the Estate independently synchronizes clean audit workspaces, validates the admitted batch, publishes evidence, and leaves the active checkout untouched.
