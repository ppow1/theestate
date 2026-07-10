# WP-0507 - Execution Attempt Lease, Cancellation, and Recovery

Status: Proposed
Priority: High
Owner: Chief Architect #5
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Traffic Controller / Operations Manager, Execution Dispatch Queue, Codex Live Execution Gate, Execution Provider Adapter Contract, Execution Result Reconciliation, Audit / Validation, Office of the Steward
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is bounded repository implementation work that adds attempt identity, locking, cancellation, stale-attempt recovery, and operational status around the existing live execution path. It should not require live provider execution, local GPU access, Codex CLI capacity, or network-dependent tests.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Implementation and deterministic validation should be possible from repository context using injected clocks, fake process handles, temporary runtime roots, and fake provider runners. A later Steward-local smoke test may exercise the real process lifecycle, but it is not required for baseline completion.
```

Capacity note:

```text
Use Codex Cloud/Web. Do not use Codex CLI for implementation or deterministic validation.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create new offices, registries, queues, providers, event systems, or command surfaces unless explicitly required.

Do not perform live provider calls in deterministic tests.

Do not introduce automatic retry loops, automatic workspace repair, or autonomous execution.

Write deterministic tests and validation evidence so local validation can confirm the result.
```

## Mission

Implement execution-attempt control around the governed live provider path so the Estate can prevent duplicate execution, expose a stable attempt identity, request cancellation, detect abandoned or stale attempts, and recover operational state without silently rerunning provider work.

WP-0506 establishes the explicit Steward-authorized live Codex execution gate. WP-0507 must make that execution path operationally manageable once a real attempt begins.

The package should answer these practical questions:

```text
Is this dispatch already executing?
Which attempt owns the execution lease?
When was the attempt last observed alive?
Has cancellation been requested?
Did the process exit cleanly, fail, or disappear?
May the dispatch be retried, and who must authorize that retry?
```

## Background

The execution chain now includes:

```text
Authorized Dispatch Item
        |
        v
Governed Dispatch-to-Adapter Handoff
        |
        v
Concrete Execution Provider Adapter
        |
        v
Steward-Authorized Live Execution Gate
        |
        v
Provider Execution Attempt
        |
        v
Result Reconciliation
```

A live provider call introduces operational risks that deterministic dry-run infrastructure does not have:

- duplicate starts;
- stale lock files;
- interrupted local processes;
- cancellation requests;
- unclear ownership after UI or terminal failure;
- ambiguous retry safety;
- result arrival after cancellation;
- provider completion without reconciliation.

This package must solve those operational mechanics without creating scheduling or autonomous retry authority.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/Institutional_Operations_Doctrine.md
docs/integration/execution_dispatch_to_adapter_handoff.md
docs/integration/codex_bridge_execution_provider_adapter.md
docs/integration/execution_result_reconciliation.md
docs/integration/steward_authorized_live_codex_execution.md
src/estate/core/execution_dispatch.py
src/estate/core/execution_provider_adapter.py
src/estate/core/execution_adapter_handoff_runtime.py
src/estate/core/codex_bridge_execution_provider_adapter.py
src/estate/core/codex_live_execution_gate.py
src/estate/core/execution_result_reconciliation_runtime.py
src/estate/core/operations_runtime_service.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

If WP-0506 files are not yet present locally, record that and implement against the expected gate contract while avoiding speculative changes to unrelated modules.

## Scope

This package must implement:

1. A stable execution-attempt record model.
2. One active execution lease per dispatch item.
3. Atomic or safely guarded lease acquisition.
4. Lease ownership by execution-attempt ID, dispatch ID, adapter request ID, provider ID, process ID when available, and approved workspace commit.
5. Heartbeat/status updates for active attempts.
6. Explicit cancellation-request artifacts.
7. Cooperative cancellation handling through an injectable process-control seam.
8. Stale-attempt detection using configurable time thresholds and process-observation evidence.
9. Recovery inspection that distinguishes stale, abandoned, completed-but-unreconciled, failed, cancelled, and still-running attempts.
10. Explicit retry eligibility evidence without automatically starting a retry.
11. Release of active leases on clean completion, confirmed failure, or confirmed cancellation.
12. Protection against late results from superseded or cancelled attempts.
13. CLI commands for status, cancel-request, inspect-recovery, release-stale, and retry-eligibility.
14. Office-readable summary artifacts using existing activity/status surfaces where practical.
15. Focused deterministic tests.
16. Integration documentation.
17. A work-package validation recipe and completion receipt.

## Out Of Scope

This package must not:

- call a live provider in tests;
- automatically retry provider execution;
- automatically start a second execution attempt;
- authorize retry;
- schedule work;
- select providers;
- assign workers;
- create a second Dispatch Queue;
- create a provider registry;
- create a new event system;
- create a new office;
- automatically kill arbitrary operating-system processes;
- use unrestricted PID termination without ownership verification;
- automatically stash, reset, clean, or repair the repository;
- auto-merge or auto-accept provider output;
- equate cancellation with rollback;
- equate provider completion with validation or institutional acceptance;
- modify Background Operations ownership;
- modify Traffic Controller authority;
- modify Steward authority.

## Architectural Boundaries

This package must preserve:

```text
Runtime computes.
Operations conducts.
Traffic Controller constrains.
Execution Providers implement.
Steward governs.
```

Package-specific boundary note:

```text
A lease prevents duplicate execution; it does not authorize execution.
A cancellation request expresses governed operator intent; it does not prove the provider stopped.
Retry eligibility is evidence; it is not retry authorization.
```

## Execution Attempt Record

Define a record containing at least:

```text
execution_attempt_id
dispatch_id
adapter_request_id
provider_id
provider_type
work_package_id
execution_authorization_id
workspace_commit
state
started_at
last_heartbeat_at
finished_at
process_id
process_identity
lease_owner
lease_acquired_at
lease_expires_at
cancellation_requested
cancellation_requested_at
cancellation_requested_by
cancellation_reason
provider_call_started
provider_call_finished
result_reference
reconciliation_reference
supersedes_attempt_id
superseded_by_attempt_id
retry_eligible
retry_reason
metadata
```

Use explicit states such as:

```text
prepared
starting
running
cancellation_requested
cancelled
completed
failed
stale
abandoned
completed_unreconciled
superseded
```

Adjust names to existing conventions if needed, but preserve the distinctions.

## Lease Requirements

The lease mechanism must:

- allow only one active attempt for a dispatch item;
- reject a second acquisition when a non-stale active lease exists;
- record attempt and process identity;
- use atomic file creation or another deterministic local guard where practical;
- detect malformed lease artifacts;
- never silently overwrite an active lease;
- permit stale release only through an explicit command and evidence check;
- preserve prior attempt artifacts after release;
- record who or what released a stale lease and why.

Do not use a global lock that unnecessarily blocks unrelated dispatch items.

## Heartbeat Requirements

Heartbeat behavior must:

- update only the matching active attempt;
- reject heartbeat updates from a different attempt;
- preserve monotonic lifecycle state;
- record timestamps deterministically through an injectable clock in tests;
- avoid implying that a process is alive solely because a file exists;
- support an observer result such as `process_alive`, `process_missing`, or `process_unknown`.

## Cancellation Requirements

Cancellation must be two-stage:

1. Record a cancellation request.
2. Attempt cooperative process cancellation only through an explicit process-control seam that verifies attempt/process ownership.

The system must distinguish:

```text
cancellation requested
cancellation signal sent
provider confirmed cancelled
process exited after cancellation
cancellation failed
result arrived after cancellation request
```

Tests must use a fake process controller. Do not terminate real processes.

## Recovery Requirements

Recovery inspection must classify attempts conservatively:

```text
running and healthy
running but heartbeat stale
process missing and no result
result exists but reconciliation missing
cancellation requested but outcome unknown
confirmed failed
confirmed cancelled
completed and reconciled
stale lease safe for explicit release
manual review required
```

The runtime must not automatically rerun work.

The runtime may produce retry-eligibility evidence containing:

```text
retry_eligible
blocking_reasons
required_authorization
prior_attempt_id
prior_result_reference
workspace_commit_match
provider_side_effect_risk
manual_review_required
```

## Late Result Protection

When a result arrives for a cancelled, stale, abandoned, or superseded attempt:

- preserve the result artifact;
- do not discard evidence;
- do not overwrite the current active attempt;
- mark the result as late or superseded;
- require reconciliation to identify the exact attempt;
- surface human attention when side effects may have occurred.

## Expected Artifacts

Create a focused runtime module, preferably:

```text
src/estate/core/execution_attempt_runtime.py
```

Create focused tests, preferably:

```text
tests/test_execution_attempt_runtime.py
```

Create integration documentation:

```text
docs/integration/execution_attempt_lease_cancellation_recovery.md
```

Create completion receipt:

```text
collaboration/work_packages/completions/WP-0507_codex_done.json
```

Add deterministic validation recipe for:

```text
WP-0507
```

Likely integration touchpoints:

```text
src/estate/core/codex_live_execution_gate.py
src/estate/core/execution_result_reconciliation_runtime.py
src/estate/core/execution_dispatch.py
src/estate/core/execution_activity.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

Modify only what is necessary.

## Runtime Artifacts

Use the existing execution-adapter runtime tree:

```text
runtime/execution_adapters/attempts/<execution_attempt_id>.json
runtime/execution_adapters/leases/<dispatch_id>.json
runtime/execution_adapters/cancellations/<execution_attempt_id>.json
runtime/execution_adapters/recovery/<execution_attempt_id>.json
runtime/execution_adapters/status/attempts_summary.json
runtime/execution_adapters/reports/<execution_attempt_id>_attempt.md
```

Do not create a parallel top-level execution subsystem.

Do not commit live runtime outputs unless explicitly required as evidence.

## CLI Surface

Add a minimal deliberate CLI surface such as:

```text
python -m estate.cli.main execution-attempt status --dispatch-id <id> --json
python -m estate.cli.main execution-attempt cancel-request --dispatch-id <id> --attempt-id <id> --reason <text> --json
python -m estate.cli.main execution-attempt inspect-recovery --dispatch-id <id> --json
python -m estate.cli.main execution-attempt release-stale --dispatch-id <id> --attempt-id <id> --confirm-stale-release --json
python -m estate.cli.main execution-attempt retry-eligibility --dispatch-id <id> --json
```

Exact command names may be adjusted to repository conventions.

The stale-release command must require an explicit confirmation flag.

No retry-start command is required in this package.

## Activity and Office Visibility

Use existing surfaces to expose at least:

```text
execution_attempt_started
execution_attempt_heartbeat
execution_cancellation_requested
execution_cancellation_signal_sent
execution_attempt_cancelled
execution_attempt_failed
execution_attempt_stale
execution_attempt_abandoned
execution_attempt_completed_unreconciled
execution_attempt_recovered
execution_retry_review_required
```

Do not create a duplicate activity feed.

Office-readable summaries should show:

- active attempt count;
- stale attempt count;
- cancellation-requested count;
- completed-unreconciled count;
- attempts requiring human attention;
- lease owner and age;
- last heartbeat;
- retry eligibility without an execution control button unless separately authorized.

## Test Requirements

Tests must cover:

- first lease acquisition succeeds;
- duplicate active lease acquisition is blocked;
- independent dispatch items may hold independent leases;
- malformed lease blocks safely;
- matching heartbeat succeeds;
- mismatched heartbeat is rejected;
- stale heartbeat classification;
- process alive, missing, and unknown observer states;
- cancellation request persistence;
- fake cooperative cancellation success;
- fake cancellation failure;
- cancellation request without provider-stop confirmation;
- clean completion releases lease;
- failed completion releases lease;
- stale release requires explicit confirmation;
- non-stale release is blocked;
- retry eligibility evidence generation;
- no automatic retry;
- late result preservation for cancelled/superseded attempt;
- idempotent repeated status/recovery inspection;
- no real process termination;
- no live provider, network, GPU, Ollama, ChatGPT, or Codex CLI calls.

## Validation Rings

### Ring 0 - Static / Structural Validation

Verify module, tests, documentation, completion receipt, and validation recipe exist.

### Ring 1 - Deterministic Test Validation

Likely commands:

```text
python -m py_compile src/estate/core/execution_attempt_runtime.py
pytest -q tests/test_execution_attempt_runtime.py tests/test_codex_live_execution_gate.py tests/test_execution_result_reconciliation_runtime.py
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0507 --json
```

All process and provider behavior must use fakes.

### Ring 2 - Local Reasoning Review

After merge, local Ring 2 review should inspect:

- WP-0507;
- changed files;
- deterministic test results;
- validation report;
- completion receipt;
- sample attempt, lease, cancellation, and recovery artifacts;
- duplicate-execution protection;
- cancellation semantics;
- retry authority boundary;
- late-result handling;
- duplicate-system risk.

## Completion Receipt Requirements

The completion receipt must include:

```text
work_package_id
status
owner
files_reviewed
files_created
files_modified
validation_commands_run
validation_results
attempt_states_implemented
lease_strategy
heartbeat_strategy
cancellation_strategy
recovery_classifications
retry_eligibility_fields
late_result_strategy
live_provider_calls_made
real_processes_terminated
fake_process_controller_used
automatic_retry_implemented
dispatch_behavior_modified
provider_adapter_behavior_modified
live_execution_gate_behavior_modified
reconciliation_behavior_modified
activity_surface_behavior_modified
authorization_behavior_modified
institutional_acceptance_behavior_modified
runtime_artifacts_written
known_limitations
ready_for_ca_review
```

The receipt must explicitly state:

```text
live_provider_calls_made: false
real_processes_terminated: false
fake_process_controller_used: true
automatic_retry_implemented: false
authorization_behavior_modified: false
institutional_acceptance_behavior_modified: false
```

## Acceptance Criteria

This package is complete when:

1. A dispatch item cannot have two active execution attempts.
2. Attempt ownership and lease state are durable and inspectable.
3. Heartbeats and process observation distinguish healthy, stale, missing, and unknown conditions.
4. Cancellation is explicit, cooperative, and auditable.
5. No arbitrary process termination occurs.
6. Stale release requires explicit confirmation and evidence.
7. Retry eligibility is reported without automatic retry or authorization.
8. Late results are preserved without corrupting the current attempt.
9. Existing Dispatch, live execution gate, provider adapter, reconciliation, Activity, Audit, and Validation systems remain canonical.
10. No live provider call occurs in deterministic tests.
11. Focused tests pass.
12. WP-0507 validation passes.
13. Completion receipt exists and is ready for Chief Architect review.
14. No new office, registry, queue, provider, event system, or competing execution path is created.

## Steward / Chief Architect Note

This is a CA5 500-series implementation package.

WP-0506 allows explicitly authorized live provider execution.
WP-0507 makes those live attempts operationally safe enough to observe, cancel, recover, and retry deliberately without duplicate execution or hidden autonomous behavior.
