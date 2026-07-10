# WP-0637 - Activate Merge-Gated Runtime Host and Windows Autostart

Status: Proposed
Priority: Critical
Owner: Chief Architect #6
Classification: Estate Internal
Depends on: WP-0623, WP-0624, WP-0625, WP-0626, WP-0627

## Mission

Make GitHub change detection and post-merge validation actually automatic on the Steward workstation.

The runtime must react only to eligible completed work that is reachable from the configured watched branch, not merely to files appearing in `collaboration/work_packages/pending`.

The local Estate checkout may be behind, dirty, or actively in use. That must not prevent the automatic runtime from fetching the remote branch, identifying newly merged work, preparing isolated validation workspaces, and publishing evidence.

## Required Behavior

The watched-target loop for `estate-main` must perform:

```text
fetch remote metadata
  -> resolve origin/main
  -> compare origin/main with durable merge-discovery cursor
  -> inspect only commits newly reachable from origin/main
  -> correlate work-package identity
  -> require completion receipt and implementation evidence
  -> reject pending-only architecture commits from audit admission
  -> suppress already-audited, held, ambiguous, superseded, or quarantined work
  -> validate eligible work in cleanroom workspaces
  -> publish durable verdicts and Ring 2 handoff evidence
  -> advance cursor only after durable processing state is recorded
```

## 1. Merge-Gated Eligibility

A work package is eligible for automatic post-merge audit only when all required conditions are true:

- The source commit is reachable from the configured remote base branch, normally `origin/main`.
- The work-package identity is unambiguous.
- A completion receipt exists in `collaboration/work_packages/completions`.
- The receipt identifies the same work package.
- The commit includes implementation, validation, documentation, or completion evidence beyond a pending work-package assignment alone.
- The work package has not already been audited successfully or otherwise terminally classified.
- It is not held, superseded, quarantined, or ambiguous.

A commit that only adds or edits a file under `collaboration/work_packages/pending` must be classified as planning metadata and must not create an audit request.

Directory location alone must never be treated as proof of merge completion.

## 2. Remote-Branch Source of Truth

Automatic discovery must use the configured watched remote branch as source of truth.

For `estate-main`:

```text
repository: ppow1/theestate
remote: origin
base branch: main
watched ref: origin/main
```

The active checkout branch, dirtiness, stash state, and local `main` position must not determine whether newly merged remote work can be discovered.

The runtime may report:

```text
active_checkout_dirty
local_main_behind_origin_main
```

but those findings must not block remote discovery or cleanroom validation.

## 3. Real Windows Autostart

Repair `operations-runtime host install` so it performs the Windows installation instead of merely writing a manifest.

On Windows it must:

- Create or update a Scheduled Task named `Estate Operations Runtime Host`.
- Use the exact Python interpreter and Estate root required to run the installed CLI.
- Set required environment variables or invoke a generated launcher script.
- Start at user logon by default.
- Run without requiring an open terminal.
- Verify task creation after installation.
- Return the actual installed task state.
- Support idempotent reinstall.
- Remove the Scheduled Task during uninstall.
- Verify removal.

Do not require administrator privileges unless Windows itself requires them for the selected task settings. Prefer the least-privileged working task configuration.

## 4. Bootstrap From a Behind or Dirty Checkout

Provide a bootstrap command that can be run from an older local checkout and installs a runtime launcher based on a clean remote-backed workspace.

Preferred behavior:

```text
operations-runtime bootstrap --target estate-main
```

The bootstrap must:

- fetch `origin/main`,
- create or refresh a dedicated runtime code workspace outside `A:\theestate`,
- use that workspace for the durable host,
- install autostart,
- start the host,
- verify heartbeat,
- leave `A:\theestate` untouched.

Recommended runtime code root:

```text
A:\EstateRuntime\host\estate-main\current
```

## 5. Host CLI Compatibility

The following commands must be present and functional in the installed runtime workspace:

```text
operations-runtime bootstrap --target estate-main
operations-runtime host install
operations-runtime host uninstall
operations-runtime host start
operations-runtime host stop
operations-runtime host restart
operations-runtime host status
operations-runtime host run-foreground
```

`host install` must create the actual Windows task.

`host status` must report:

```text
installed
scheduled_task_exists
scheduled_task_state
host_state
pid
heartbeat_age_seconds
runtime_code_revision
watched_remote_ref
last_fetch_at
last_scanned_commit
last_processed_work_package
last_verdict
blocking_fault
```

## 6. Continuous Remote Polling

The durable host must periodically fetch the watched remote branch before merge discovery.

Default interval may remain bounded and configurable.

Each cycle must be independent of the active checkout and use:

```text
remote branch state
cleanroom audit workspaces
external runtime evidence
```

A fetch failure must be recorded and retried later without destroying the prior cursor.

## 7. Cursor and Replay Safety

The merge-discovery cursor must represent the last durably processed remote commit, not merely the local checkout revision.

The runtime must:

- avoid skipping commits after interruption,
- avoid duplicating completed audit requests,
- preserve the cursor when fetch or processing fails before durable state is written,
- recover safely after reboot.

## Required Implementation

Expected touchpoints:

```text
src/estate/core/operations_runtime_host.py
src/estate/core/operations_runtime_service.py
src/estate/core/merge_discovery.py
src/estate/core/merge_discovery_runtime.py
src/estate/core/merge_discovery_admission.py
src/estate/core/operational_targets_runtime.py
src/estate/cli/main.py
tests/test_operations_runtime_host.py
tests/test_merge_discovery.py
tests/test_merge_discovery_runtime.py
tests/test_merge_discovery_admission.py
tests/test_operations_runtime.py
docs/integration/merge_gated_runtime_host_activation.md
```

A small PowerShell launcher may be generated under the external runtime root when required for reliable Scheduled Task invocation.

## Test Requirements

Tests must prove:

- pending-only work-package commits are not admitted,
- a completed work package on `origin/main` is admitted,
- local `main` behind `origin/main` does not block discovery,
- a dirty active checkout does not block discovery or validation,
- the durable cursor advances from remote branch history,
- duplicate audits are suppressed,
- failed fetch does not corrupt or advance the cursor,
- bootstrap creates an external runtime code workspace,
- Windows install executes the Scheduled Task creation command,
- install verifies the task exists,
- uninstall executes task deletion and verifies removal,
- start produces a live heartbeat,
- provider and dispatch execution remain false.

Use mocks for Windows task commands in deterministic tests. Include one guarded local integration demonstration for the real workstation.

## Validation

```powershell
Clear-Host
cd A:\theestate
python -m py_compile src\estate\core\operations_runtime_host.py src\estate\core\merge_discovery.py src\estate\core\merge_discovery_runtime.py src\estate\core\merge_discovery_admission.py
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_operations_runtime_host.py tests/test_merge_discovery.py tests/test_merge_discovery_runtime.py tests/test_merge_discovery_admission.py tests/test_operations_runtime.py --basetemp Temp/pytest-runtime-activation
python -m estate.cli.main validate-work-package --id WP-0637 --json
```

## Live Workstation Demonstration

The implementation is not complete until the following can be demonstrated from an active, potentially dirty and behind checkout:

```powershell
Clear-Host
cd A:\theestate
$env:PYTHONPATH = "src"
python -m estate.cli.main operations-runtime bootstrap --target estate-main --json
```

Expected result:

```text
origin/main fetched
external runtime code workspace prepared
Windows Scheduled Task installed and verified
host started
heartbeat live
watched ref origin/main
active checkout unchanged
pending-only commits ignored for audit admission
eligible completed merges detected automatically
```

Then verify:

```powershell
Clear-Host
cd A:\theestate
$env:PYTHONPATH = "src"
python -m estate.cli.main operations-runtime host status --json
```

## Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0637_codex_done.json
```

The receipt must report:

```text
remote_ref_used
runtime_code_workspace
scheduled_task_name
scheduled_task_installed
scheduled_task_verified
host_started
heartbeat_verified
active_checkout_modifications_performed
pending_only_commits_suppressed
eligible_completed_work_detected
provider_execution_performed
 dispatch_execution_performed
```

Both provider and dispatch execution values must be false.

## Promotion Criteria

Ready when one bootstrap command installs and starts the runtime from an external clean workspace, the host continuously watches `origin/main`, pending-only planning commits do not create audits, completed merged work does, and `A:\theestate` remains untouched.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0637_Activate_Merge_Gated_Runtime_Host_and_Windows_Autostart.md and do exactly what it says.
```
