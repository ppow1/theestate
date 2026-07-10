# WP-0639 - Automatic Validation Reconciliation, Queue Drain, and Runtime-State Integrity

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-10

## Mission

Complete the automatic post-merge validation loop so every relevant merged work package is durably accounted for from merge discovery through final verdict, eligible requests drain automatically in bounded batches, and mutable runtime state never dirties the synchronized Git checkout.

WP-0639 is a repair and completion package. It must strengthen the existing systems created by WP-0621, WP-0624, WP-0625, WP-0626, WP-0627, WP-0637, and WP-0638. It must not create a second discovery service, audit queue, validator, verdict registry, scheduler, host, or Office institution.

The required result is one truthful operational chain:

```text
origin/main merge
  -> work-package identity reconciliation
  -> package-kind classification
  -> canonical discovery record
  -> admission decision with explicit reason
  -> exactly one active audit request when eligible
  -> isolated validation workspace
  -> deterministic recipe execution
  -> terminal verdict or explicit no-recipe outcome
  -> queue capacity released
  -> reconciliation ledger and Office status updated
```

## Confirmed Current State

The following behavior has been demonstrated and must be preserved:

- merge discovery can fetch and scan `origin/main`,
- automatic admission can create bounded requests,
- the Operations Runtime can claim and start audits,
- isolated audit workspaces are created outside the active checkout,
- validation reports, Ring 2 prompts, and verdict evidence are written under external Estate runtime paths,
- terminal validation failures can be published as verdicts,
- provider execution and dispatch execution remain false during validation.

The following defects remain:

1. There is no authoritative merge-to-verdict reconciliation ledger.
2. Runtime summaries cannot truthfully account for all merged work packages as discovered, staged, eligible, held, pending, running, terminal, ambiguous, or missing a recipe.
3. Older pending requests may be processed while newer packages remain unaccounted for, without a clear backlog explanation.
4. Generated background-operations extension configuration is written to `config/background_operations/extensions.json`, dirtying the synchronized runtime checkout.
5. Mutable runtime state is not consistently externalized.
6. The operations-runtime lock does not safely recover from a dead owner PID.
7. Windows host PID/status reporting can classify a running Scheduled Task host as dead or stopped.
8. Host interruption, stale locks, or generated checkout files can prevent sustained queue draining.
9. A single validation failure must never prevent later eligible requests in the same bounded batch from being attempted.
10. No durable report currently shows exact backlog, active capacity, throughput, and estimated remaining cycles.

## Scope Boundaries

### This package must

- reconcile merges, completion receipts, discovery records, requests, recipes, and verdicts,
- repair queue accounting and automatic draining,
- externalize mutable/generated runtime state,
- repair stale lock recovery and Windows host liveness reporting,
- add durable machine-readable and Office-readable status,
- prove the runtime can progress through a mixed batch containing passes, failures, staged packages, and no-recipe packages.

### This package must not

- redesign WP-0626 clean-room validation,
- move committed recipes, completion receipts, contracts, schemas, or intentionally promoted institutional reports out of the repository,
- grant institutional acceptance,
- execute providers or dispatch work,
- automatically repair failed work packages,
- create a second scheduler, queue, event bus, discovery service, validator, or verdict store,
- treat a staged-but-not-installed package as an installed runtime failure,
- hide ambiguous or missing evidence states.

## Core Requirements

### 1. Canonical validation reconciliation ledger

Add one canonical reconciliation service that joins existing evidence by:

```text
target_id
work_package_id
promoted_revision / merge_commit
completion_receipt_path
```

The ledger must include one row per relevant work package/revision with at least:

```text
schema_version
target_id
work_package_id
merge_commit
merged_at
source_reference
completion_receipt_path
completion_receipt_present
package_kind
installation_state
discovery_id
discovery_state
identity_evidence
admission_state
admission_reason
audit_id
request_state
validation_recipe_state
validation_status
verdict
verdict_path
blocking_reason
retry_eligible
first_seen_at
last_attempt_at
terminal_at
```

Supported `package_kind` values must include at minimum:

```text
installed
staged_not_installed
documentation_or_audit
planning_only
unknown
```

Supported reconciliation states must distinguish:

```text
undiscovered
discovered
ambiguous
held
ineligible
pending
claimed
running
ring2_required
passed
failed
blocked
no_recipe
already_audited
superseded
```

The ledger must be reconstructable from durable source evidence and must not depend solely on transient in-memory counters.

### 2. Truthful total accounting

Produce exact counts for the selected target and time range:

```text
merges_examined
work_packages_identified
installed_packages
staged_packages
planning_only_packages
unknown_packages
discovered
ambiguous
held
eligible
pending
running
terminal
passed
failed
blocked
no_recipe
ring2_required
already_audited
unaccounted
```

The following invariant must be enforced and reported:

```text
identified work packages
  = terminal
  + active
  + held/ineligible
  + ambiguous
  + staged/planning-only
  + explicitly unaccounted
```

A nonzero `unaccounted` count must include row-level reasons and evidence links.

### 3. Automatic queue drain

The Operations Runtime must continuously process eligible requests up to the configured `max_audit_requests` per cycle.

Required behavior:

- exactly one active request per target + work package + promoted revision,
- terminal requests do not consume active capacity,
- failed or blocked audits release capacity immediately,
- one failed audit does not stop later requests in the batch,
- later cycles continue until no eligible pending requests remain,
- retryable requests are explicit and do not silently duplicate prior terminal evidence,
- staged or planning-only packages do not occupy installed-package audit capacity,
- queue ordering is deterministic and reported,
- queue starvation is detected and surfaced.

Required status fields:

```text
active_audit_limit
active_request_count
pending_request_count
running_request_count
terminal_request_count
available_capacity_before
available_capacity_after
audits_attempted_this_cycle
audits_terminal_this_cycle
backlog_remaining
estimated_cycles_remaining
oldest_pending_age_seconds
queue_starvation_detected
zero_throughput_reason
```

### 4. Explicit no-recipe handling

A work package with no registered validation recipe must not remain indefinitely pending and must not block later work.

The runtime must publish an explicit terminal or governed non-running outcome:

```text
verdict: no_recipe
validation_status: no_recipe
production_ready: false
retry_eligible: true when a recipe is later registered
blocking_reason: validation_recipe_missing
```

This outcome is evidence, not institutional acceptance.

When a recipe is later registered, reconciliation must identify the package as retry-eligible without creating duplicate active requests.

### 5. Preserve clean-room validation

WP-0626 behavior is authoritative and must remain intact:

- never validate in `A:\theestate`,
- never validate in the synchronized host code checkout,
- use an isolated workspace under the configured external workspace root,
- write transient validation evidence under the configured external evidence root,
- leave active and synchronized code checkouts unchanged,
- preserve failed workspaces only when configured.

### 6. Externalize mutable runtime configuration and state

Generated or mutable runtime files must not be created under tracked source/config paths in the synchronized checkout.

At minimum, repair the background-operations extension runtime so it does not generate:

```text
config/background_operations/extensions.json
```

inside the runtime code checkout.

Use a configured external runtime-state root, for example:

```text
A:\EstateRuntime\host\estate-main\state\configuration\background_operations\extensions.json
```

or another canonical path derived from the existing host/runtime state configuration.

Repository content may include a committed default/template contract, but runtime-generated copies, enable/disable state, quarantine state, cursors, locks, queue state, reports, and status artifacts must be external or remain under already-ignored runtime paths that cannot dirty the synchronized checkout.

Add a runtime-write-path audit that classifies every write target as:

```text
committed_source
external_runtime_state
external_validation_evidence
external_workspace
ignored_local_runtime
invalid_checkout_write
```

Any `invalid_checkout_write` must fail validation.

### 7. Stale operations-runtime lock recovery

Repair the operations-runtime lock so an existing lock is not automatically treated as active merely because the file exists.

Required behavior:

- read and validate lock metadata,
- determine whether the owner process is alive using a Windows-compatible mechanism,
- recover a lock owned by a confirmed dead PID,
- preserve and refuse removal of a lock owned by a live process,
- record stale-lock recovery evidence,
- distinguish malformed lock, dead-owner lock, live-owner lock, and permission uncertainty,
- avoid deleting locks when liveness cannot be determined safely.

### 8. Correct Windows host liveness and status

Host status must reconcile:

```text
Scheduled Task state
host lock
PID evidence
heartbeat freshness
last completed cycle
crash/shutdown evidence
```

Do not rely only on `os.kill(pid, 0)` for Windows process liveness.

Required truthful states include:

```text
running
sleeping
starting
stopping
stopped
stale_lock_dead_pid
scheduled_task_running_pid_unverified
crashed
blocked
```

A running Scheduled Task with a fresh heartbeat and valid host lock must not be reported simply as stopped because one PID probe is unreliable.

### 9. Office-visible validation operations status

Extend the existing Office validation/operations surfaces rather than creating a new Office.

The Steward must be able to inspect:

- total packages in the reconciliation ledger,
- current audit backlog,
- active capacity,
- latest throughput,
- passes/failures/no-recipe counts,
- held and ambiguous packages with reasons,
- unaccounted packages,
- oldest pending request,
- host health and stale-lock recovery events,
- evidence links for each row.

The Office surface may request refresh, inspect evidence, acknowledge failures locally, and request governed retry through existing canonical handlers. It must not grant acceptance or perform automatic repairs.

### 10. Backward reconciliation

Provide a bounded reconciliation command that can account for a historical range without flooding the active queue.

Example:

```powershell
python -m estate.cli.main validation-reconciliation rebuild --target estate-main --since 2026-07-10T00:00:00Z --max-commits 500 --json
```

The command must:

- scan the configured watched remote ref,
- correlate completion receipts and work-package identities,
- classify staged/planning-only packages,
- join existing requests and verdicts,
- identify missing requests,
- write the ledger and summary,
- create no requests unless an explicit governed admission option is supplied.

A separate bounded admission/drain command may be added through the existing Operations Runtime seam.

## Expected Implementation

Prefer small focused modules and minimal edits to hot shared files.

Expected new files:

```text
src/estate/core/validation_reconciliation.py
src/estate/core/validation_reconciliation_runtime.py
tests/test_validation_reconciliation.py
tests/test_validation_queue_drain.py
tests/test_runtime_state_write_paths.py
docs/integration/automatic_validation_reconciliation_and_queue_drain.md
```

Expected focused integration changes:

```text
src/estate/core/merge_discovery.py
src/estate/core/merge_discovery_admission.py
src/estate/core/post_merge_audit_lifecycle.py
src/estate/core/post_merge_audit_processor.py
src/estate/core/post_merge_validation_pipeline.py
src/estate/core/operations_runtime.py
src/estate/core/operations_runtime_service.py
src/estate/core/operations_runtime_host.py
src/estate/core/background_operations_extension_runtime.py
src/estate/core/office_validation_actions.py
src/estate/core/steward_command_center.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

Avoid unnecessary edits to shared Office files. Where practical, stage integration through a focused adapter imported by the existing command surface.

## CLI Requirements

Add a focused CLI surface using the existing main CLI:

```text
validation-reconciliation rebuild
validation-reconciliation status
validation-reconciliation list
validation-reconciliation inspect <work_package_id>
validation-reconciliation admit-eligible
validation-reconciliation drain
validation-reconciliation write-path-audit
```

Commands must support JSON output and target selection.

`drain` must delegate to the canonical Operations Runtime and honor the configured bounded batch limit. It must not create a parallel processor.

## Test Requirements

Tests must prove all of the following:

1. Fifty mixed merge/package fixtures can be fully reconciled without losing rows.
2. Installed, staged, planning-only, ambiguous, already-audited, and unknown packages are classified distinctly.
3. Every identified package is represented in exactly one accounting bucket.
4. Exactly one active request exists per target + work package + promoted revision.
5. Terminal requests release capacity.
6. Five eligible audits can be attempted in one cycle when the limit is five.
7. A failed first audit does not stop the remaining four.
8. Multiple cycles drain the remaining backlog.
9. Missing recipes produce explicit `no_recipe` evidence and do not stall the queue.
10. Registering a recipe later makes the package retry-eligible without duplicating active requests.
11. Staged packages do not produce installed-package validation failures.
12. Validation workspaces and evidence remain external.
13. The synchronized runtime checkout remains clean after multiple cycles.
14. Background extension configuration is created externally, not under repository `config/`.
15. The runtime-write-path audit reports zero invalid checkout writes.
16. A dead-owner operations-runtime lock is recovered safely.
17. A live-owner lock is preserved and blocks duplicate execution.
18. Windows host status uses Scheduled Task, heartbeat, and lock evidence truthfully.
19. Provider execution remains false.
20. Dispatch execution remains false.
21. Institutional acceptance remains not granted.

## Validation Recipe

Register a WP-0639 recipe that performs focused validation without requiring live providers.

Minimum validation commands:

```powershell
Clear-Host
Set-Location A:\theestate
$env:PYTHONPATH = "A:\theestate\src"
python -m py_compile `
  src\estate\core\validation_reconciliation.py `
  src\estate\core\validation_reconciliation_runtime.py `
  src\estate\core\operations_runtime.py `
  src\estate\core\operations_runtime_host.py `
  src\estate\core\background_operations_extension_runtime.py
pytest -q `
  tests/test_validation_reconciliation.py `
  tests/test_validation_queue_drain.py `
  tests/test_runtime_state_write_paths.py `
  tests/test_merge_discovery_admission.py `
  tests/test_post_merge_audit_processor.py `
  tests/test_operations_runtime.py `
  tests/test_operations_runtime_host.py `
  --basetemp A:\EstateRuntime\temp\pytest-wp0639
python -m estate.cli.main validate-work-package --id WP-0639 --json
```

## Live Acceptance Demonstration

The live demonstration must use the external runtime host workspace and state roots. It must not validate inside `A:\theestate`.

Required preflight:

```text
branch = main
working tree = clean
HEAD = origin/main
WP-0639 merge present
runtime launcher points to external code workspace
PYTHONPATH points to external code workspace src
```

Required demonstration:

1. Rebuild a reconciliation ledger for the work packages merged on 2026-07-10.
2. Print total identified packages and every accounting bucket.
3. Show zero unaccounted packages, or explicit row-level reasons for each remaining unaccounted package.
4. Admit eligible packages without creating duplicates.
5. Run at least three bounded cycles or until backlog reaches zero.
6. Show per-cycle attempted, terminal, remaining, and zero-throughput reason fields.
7. Include at least one passing package, one validation failure, one staged package, and one no-recipe package.
8. Prove later packages are attempted after a failure.
9. Prove external verdict and workspace paths.
10. Prove both `A:\theestate` and the synchronized host code checkout remain clean.
11. Prove no generated `config/background_operations/extensions.json` exists in either checkout.
12. Prove stale-lock recovery with a synthetic dead PID lock.
13. Prove a live host is reported truthfully on Windows.

## Required Artifacts

```text
runtime/validation_reconciliation/ledger.json
runtime/validation_reconciliation/summary.json
runtime/validation_reconciliation/write_path_audit.json
operations/validation/reports/WP-0639_validation_reconciliation.md
collaboration/work_packages/completions/WP-0639_codex_done.json
```

Runtime-generated copies may be redirected to the configured external state root. Repository paths above represent the canonical logical artifact names; committed completion and promoted validation reports remain repository evidence.

## Completion Receipt Requirements

The completion receipt must record:

```text
work_package_id
implementation_commit
files_changed
validation_commands
validation_status
reconciliation_rows
unaccounted_rows
installed_count
staged_count
pending_count
terminal_count
passed_count
failed_count
blocked_count
no_recipe_count
audits_attempted_per_cycle
backlog_before
backlog_after
invalid_checkout_writes
stale_locks_recovered
active_checkout_modified
runtime_checkout_modified
provider_execution_performed
dispatch_execution_performed
institutional_acceptance_granted
```

The final three authority fields must be false.

## Promotion Criteria

WP-0639 is ready only when:

- the Estate can truthfully account for every relevant merged work package in the selected range,
- every eligible installed package is either terminal or visibly pending/running with a reason,
- the queue drains automatically in bounded batches,
- failures and no-recipe outcomes do not stall later work,
- staged packages are not misreported as installed validation failures,
- runtime and validation evidence remain external,
- generated background extension state no longer dirties the synchronized checkout,
- stale locks recover safely,
- Windows host status is truthful,
- both active and runtime code checkouts remain clean throughout the live demonstration.
