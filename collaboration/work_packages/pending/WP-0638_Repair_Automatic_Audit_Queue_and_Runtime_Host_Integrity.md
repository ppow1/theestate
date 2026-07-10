# WP-0638 - Repair Automatic Audit Queue and Runtime Host Integrity

Status: Proposed
Priority: Critical
Owner: Chief Architect #6
Classification: Estate Internal
Depends on: WP-0623, WP-0624, WP-0625, WP-0626, WP-0627, WP-0637

## Mission

Complete the transition from automatic merge discovery to actual automatic post-merge validation.

WP-0637 successfully established a durable Windows host that fetches `origin/main`, advances the merge-discovery cursor, evaluates candidates, and auto-admits bounded work. Live operation exposed several defects that prevent reliable end-to-end validation:

- the same existing requests are repeatedly counted as newly admitted,
- terminal or non-pending requests consume the admission limit,
- newly eligible candidates remain held while the same five stale candidates recycle,
- the audit processor starts zero audits even though admission reports five requests,
- bootstrap can create the runtime workspace from a stale local revision,
- the generated host launcher may inherit an unrelated `PYTHONPATH`,
- host status can report `host_state: stopped` while the Scheduled Task is running and heartbeat is current,
- the runtime cycle reports `stopped` for a completed bounded cycle in a way that is easily confused with host shutdown.

The repair must make the durable host fetch, admit, process, and publish validation results continuously without requiring the active checkout or manual queue intervention.

## Observed Live Evidence

The running host demonstrated:

```text
scheduled task: Running
heartbeat state: sleeping
watched remote ref: origin/main
merge cursor advancing
provider execution performed: false
dispatch execution performed: false
```

But repeated cycles also demonstrated:

```text
admitted_candidates: 5
admitted_requests: 5
queue_limit_reached: true
audits_claimed: 0
audits_started: 0
audits_completed: 0
latest_admitted_work_package: WP-0518
```

This is a queue-integrity and lifecycle-classification defect, not a remote-discovery defect.

## Required Outcome

The durable runtime must implement this complete loop:

```text
fetch origin/main
  -> discover newly reachable completed work
  -> classify candidate lifecycle state
  -> account for active queue occupancy
  -> create only missing pending requests
  -> skip terminal and already-audited candidates
  -> claim pending requests
  -> validate in cleanroom workspace
  -> publish verdict and evidence
  -> release queue capacity
  -> admit the next eligible candidates
  -> repeat
```

The loop must make forward progress across cycles.

## 1. Correct Admission Idempotency

Repair `MergeDiscoveryAdmission` so an existing request is not automatically counted as a new admission.

For every canonical candidate, determine whether there is:

- no request,
- a pending request,
- an active request,
- a terminal request,
- a failed retryable request,
- a superseded or quarantined request,
- a final verdict.

Required behavior:

- No request: create one pending request and count one new admission.
- Existing pending request: do not create another request and do not count it as newly admitted.
- Existing claimed/running request: count it as active queue occupancy, not as newly admitted.
- Existing completed/final request: classify the candidate as already audited or terminal and do not consume queue capacity.
- Existing blocked/validation-failed/workspace-failed request with a final verdict: classify as terminal unless an explicit governed retry was requested.
- Existing failed request without a final verdict: classify separately as retryable or repair-required; do not silently reuse it as a pending request.
- Superseded, ambiguous, quarantined, held, and historical candidates remain ineligible.

`admitted_candidates` and `admitted_requests` must mean newly admitted during the current cycle only.

## 2. Correct Queue Capacity Accounting

The configured limit is the maximum number of active audit requests, not the maximum number of candidates iterated.

Define active queue states explicitly, at minimum:

```text
pending
claimed
running_validation
running_ring2
```

Queue capacity must be calculated as:

```text
available_capacity = max_active_requests - current_active_requests
```

Only newly created pending requests consume available capacity.

Terminal requests must not consume capacity.

The admission summary must expose:

```text
active_request_count
pending_request_count
running_request_count
terminal_request_count
new_requests_created
existing_pending_requests
existing_active_requests
already_audited_candidates
retryable_failed_requests
available_capacity_before
available_capacity_after
queue_limit_reached
```

## 3. Ensure Same-Cycle Audit Processing

When the runtime mode is `discover-merges-and-process-audits`, requests admitted during the discovery/admission phase must be visible to the audit processor in the same cycle.

The processor must attempt up to the configured maximum after admission.

A cycle that reports newly admitted pending requests but zero claimed requests must include an explicit reason, such as:

```text
no_pending_requests
binding_not_ready
all_requests_terminal
all_requests_held
processor_fault
```

Silent zero-throughput is not acceptable.

## 4. Repair Candidate State Transitions

Canonical candidate state must reflect the actual request/verdict lifecycle.

Required candidate states include or map cleanly to:

```text
discovered
eligible
admitted
pending
running
completed
ring2_required
blocked
validation_failed
workspace_failed
already_audited
retryable_failed
manual_hold
superseded
quarantined
ambiguous
historical_backfill
```

Do not leave a terminal candidate in `admitted` indefinitely.

When a request reaches a terminal verdict, subsequent cycles must reconcile the candidate state automatically.

## 5. Repair Duplicate and Final-Verdict Detection

Use a single canonical rule for final verdicts across admission and processing.

The admission layer and processor must agree on:

- final verdict values,
- active request states,
- terminal request states,
- retryable states,
- duplicate suppression keys.

The canonical duplicate identity must include:

```text
target_id
work_package_id
canonical_discovery_id or source_commit
```

Do not create duplicate pending requests for the same canonical discovery.

Do not allow an unrelated historical verdict for the same work-package ID to suppress a legitimately newer implementation unless the source identity proves they are the same completed work item.

## 6. Repair Bootstrap Source Synchronization

Repair `OperationsRuntimeHost.bootstrap` so the external runtime workspace is always synchronized from the configured authoritative remote branch.

Required behavior:

- fetch the source repository remote,
- determine the configured remote URL,
- create or refresh the external runtime workspace,
- set its remote URL before synchronization,
- fetch `origin/main` inside the runtime workspace,
- reset or recreate the runtime workspace at the exact fetched `origin/main` revision,
- verify local runtime revision equals `origin/main`,
- fail safely if verification fails,
- never use a stale local `main` as the final runtime revision,
- never modify `A:\theestate`.

The completion result must report:

```text
source_checkout_revision
remote_main_revision
runtime_workspace_revision
runtime_matches_remote
```

## 7. Repair Generated Launcher Environment

The generated Windows launcher must define all required runtime environment explicitly.

At minimum:

```text
ESTATE_OPERATIONS_RUNTIME_ROOT
ESTATE_OPERATIONS_RUNTIME_HOST_DIR
PYTHONPATH=<runtime workspace>\src
```

The launcher must not inherit a temporary bootstrap workspace through `PYTHONPATH`.

The launcher must invoke the Python interpreter selected during installation and run from the external runtime workspace.

The launcher must include the intended automatic mode:

```text
--discover-merges
--auto-admit
--process-audits
--max-audit-requests <configured value>
```

## 8. Repair Host Status Semantics

`operations-runtime host status` must distinguish:

- Scheduled Task state,
- host process state,
- heartbeat state,
- bounded cycle state.

Required top-level fields:

```text
installed
scheduled_task_exists
scheduled_task_state
host_process_state
host_pid_alive
heartbeat_state
heartbeat_age_seconds
host_state
current_cycle_state
last_completed_cycle_state
last_completed_cycle_at
runtime_code_revision
watched_remote_ref
last_fetch_at
last_scanned_commit
blocking_fault
```

Host state rules:

- A live PID, current heartbeat, and present valid host lock means `host_state: running` even when the last bounded cycle is `stopped` or complete.
- `heartbeat_state: sleeping` means the host is alive between cycles.
- A completed bounded cycle must be represented as `completed` or equivalent in status/reporting, not confused with host shutdown.
- Stale lock and dead PID combinations must be reported explicitly.

## 9. Runtime Workspace Self-Refresh

The durable host code workspace must not remain permanently pinned to its installation revision.

Implement a safe bounded self-refresh policy before or between cycles:

- fetch `origin/main`,
- detect whether runtime code revision is behind,
- do not replace code while a validation operation is in a critical write section,
- stage the next runtime revision safely,
- restart or hand off the host deterministically,
- preserve runtime evidence and cursors outside the code workspace,
- never update from untrusted refs,
- never modify the active developer checkout.

At minimum, expose behind/ahead state and a governed refresh command if fully automatic self-restart is not safe in this package.

## 10. Preserve Authority and Safety Boundaries

This repair must not:

- invoke model providers,
- invoke execution dispatch,
- grant institutional acceptance,
- bypass Ring 2 review where required,
- modify the active developer checkout,
- create stashes,
- reset developer branches,
- treat validation as acceptance.

Provider and dispatch execution must remain false.

## Staged Implementation and Hot-File Protection

This package touches known collision-prone files, including runtime and CLI modules.

Before editing, inspect the existing staged workstream/package-install mechanism introduced by the Office workstream packages. Reuse that mechanism where practical.

Requirements:

- implement new behavior in focused modules where possible,
- avoid broad unrelated edits to `src/estate/cli/main.py`,
- avoid broad unrelated edits to shared runtime files,
- declare every shared-file modification explicitly,
- include an installation/integration manifest when the existing Estate mechanism supports it,
- sequence shared-file installation deterministically,
- do not overwrite concurrent unrelated changes,
- fail on an unexpected hot-file base revision rather than silently replacing it.

If the existing staged installer cannot safely absorb this repair, document the exact gap and make only the smallest necessary shared-file patch.

## Expected Implementation Areas

Likely touchpoints:

```text
src/estate/core/merge_discovery_admission.py
src/estate/core/merge_discovery_consolidation.py
src/estate/core/post_merge_audit_processor.py
src/estate/core/operations_runtime.py
src/estate/core/operations_runtime_host.py
src/estate/core/operations_runtime_service.py
src/estate/cli/main.py
```

Prefer extracting shared lifecycle constants and request-state classification into a focused module, for example:

```text
src/estate/core/post_merge_audit_lifecycle.py
```

Tests should include:

```text
tests/test_merge_discovery_admission.py
tests/test_post_merge_audit_processor.py
tests/test_operations_runtime.py
tests/test_operations_runtime_host.py
tests/test_merge_discovery_runtime.py
```

Documentation:

```text
docs/integration/automatic_audit_queue_and_runtime_host_integrity.md
```

## Required Tests

Tests must prove:

1. An existing pending request is not counted as newly admitted.
2. An existing running request consumes active capacity but is not newly admitted.
3. A terminal request does not consume active capacity.
4. A final verdict classifies the candidate as already audited.
5. A failed request without final verdict is classified as retryable or repair-required.
6. Duplicate pending requests are not created.
7. Five stale terminal candidates cannot permanently block newer eligible candidates.
8. New pending requests are claimed in the same runtime cycle.
9. The queue advances to later candidates after earlier requests complete.
10. Candidate state reconciles after verdict publication.
11. Zero audit throughput includes a deterministic reason.
12. Bootstrap runtime revision exactly matches fetched `origin/main`.
13. Bootstrap works when the active checkout is dirty and behind.
14. Launcher sets `PYTHONPATH` to the external runtime workspace.
15. Launcher does not reference the temporary bootstrap workspace.
16. Host status reports running for live PID plus recent heartbeat plus valid lock.
17. Sleeping heartbeat is treated as a live host state.
18. Completed bounded-cycle state is not reported as host shutdown.
19. Provider and dispatch execution remain false.
20. No active checkout modifications or stashes occur.

## Validation Recipe Requirement

This work package is not complete without a registered validation recipe.

Create the recipe before reporting completion. The following command must not return `no_recipe`:

```text
python -m estate.cli.main validate-work-package --id WP-0638 --json
```

`no_recipe` is a blocking failure for this package.

The completion receipt may not report `ready_for_ca_review: true` unless the validation recipe resolves and all required checks execute.

## Validation Commands

```powershell
Clear-Host
cd A:\theestate
python -m py_compile src\estate\core\merge_discovery_admission.py src\estate\core\post_merge_audit_processor.py src\estate\core\operations_runtime.py src\estate\core\operations_runtime_host.py
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_merge_discovery_admission.py tests/test_post_merge_audit_processor.py tests/test_operations_runtime.py tests/test_operations_runtime_host.py tests/test_merge_discovery_runtime.py --basetemp Temp/pytest-wp0638
python -m estate.cli.main validate-work-package --id WP-0638 --json
```

## Live Acceptance Demonstration

Use an external clean runtime workspace and a running Scheduled Task.

The implementation must demonstrate at least three consecutive cycles where:

```text
origin/main fetch succeeds
merge cursor advances when new commits exist
existing stale requests are not re-counted as new admissions
new eligible requests are created only within available capacity
at least one pending audit is claimed
at least one audit reaches a terminal or Ring 2-required state
queue capacity is released
later eligible work advances
host heartbeat remains current
host status reports running accurately
provider execution remains false
dispatch execution remains false
```

If validation cannot complete because a recipe is missing for an admitted work package, the request must end in a visible validation-failed/no-recipe verdict and release capacity according to governed terminal-state policy. It must not stall the queue indefinitely.

## Required Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0638_codex_done.json
```

The receipt must include:

```text
work_package_id
codex_status
branch
pull_request_url
files_changed
shared_hot_files_changed
staged_install_mechanism_used
installation_manifest_path
validation_recipe_registered
validation_status
active_checkout_modifications_performed
stashes_created
bootstrap_remote_revision
bootstrap_runtime_revision
runtime_matches_remote
launcher_pythonpath_verified
host_status_semantics_verified
existing_pending_not_readmitted
terminal_requests_excluded_from_capacity
same_cycle_processing_verified
queue_forward_progress_verified
live_cycles_observed
provider_execution_performed
dispatch_execution_performed
known_limitations
ready_for_ca_review
```

Required values:

```text
validation_recipe_registered: true
active_checkout_modifications_performed: false
stashes_created: 0
runtime_matches_remote: true
launcher_pythonpath_verified: true
existing_pending_not_readmitted: true
terminal_requests_excluded_from_capacity: true
same_cycle_processing_verified: true
queue_forward_progress_verified: true
provider_execution_performed: false
dispatch_execution_performed: false
```

## Promotion Criteria

Ready when automatic operation demonstrably progresses from remote merge detection through bounded audit processing without recycling stale admissions, the external runtime workspace matches `origin/main`, the launcher is self-contained, host status is truthful, validation recipe resolution succeeds, and the active developer checkout remains untouched.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0638_Repair_Automatic_Audit_Queue_and_Runtime_Host_Integrity.md and do exactly what it says.
```
