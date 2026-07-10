# WP-0628 - Unified Background Scheduler

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-10

## Mission

Replace competing background loops with one governed scheduler that coordinates Estate services, dependencies, retries, concurrency, and cycle ownership.

WP-0627 provides the persistent Operations Runtime service. WP-0628 must provide the scheduling substrate beneath it.

## Provider Assignment Guidance

Recommended provider: `codex_cloud_web`  
Local runtime required: true for demonstration  
Do not use Codex CLI for routine implementation.

## Required Behavior

The scheduler must register and coordinate existing services such as:

- merge discovery
- automatic admission
- post-merge audit
- validation
- Ring 2 preparation
- mailbox synchronization
- operational-target checks
- Git hygiene observation
- Office status refresh
- resident and department duties when later enabled

Each scheduled service must expose:

```text
service_id
enabled
paused
priority
cadence_seconds
event_triggers
depends_on
max_concurrency
timeout_seconds
retry_limit
backoff_seconds
last_started_at
last_completed_at
next_eligible_at
last_result
health
```

## Scheduling Semantics

Support:

- interval-based eligibility
- event-triggered eligibility
- dependency-aware execution
- priority ordering
- bounded concurrency
- per-service timeout
- retry with backoff
- failure isolation
- starvation prevention
- duplicate-run suppression
- persistent scheduler state
- graceful shutdown

A failure in one service must not stop unrelated eligible services.

The scheduler must not become an execution provider, routing authority, dispatch queue, or institutional acceptance layer.

## Cycle Ownership

Every Operations Runtime cycle must receive a scheduler cycle ID.

Every service run must record:

```text
scheduler_cycle_id
service_run_id
trigger_reason
started_at
finished_at
result
artifacts
warnings
errors
```

## Office Contract

Expose stable callable functions, status artifacts, input contracts, and truthful result contracts for CA5 WP-0516, WP-0520, and WP-0521.

Required controls:

- scheduler status
- run eligible services now
- pause scheduler
- resume scheduler
- inspect service run
- inspect blocked dependency

Required status fields:

- scheduler_state
- active_runs
- eligible_services
- blocked_services
- unhealthy_services
- next_wake
- latest_cycle
- latest_failures

## Expected Artifacts

- `src/estate/core/background_scheduler.py`
- `src/estate/core/background_scheduler_runtime.py`
- `tests/test_background_scheduler.py`
- `tests/test_background_scheduler_runtime.py`
- `docs/integration/unified_background_scheduler.md`

Expected integration touchpoints:

- `src/estate/core/operations_runtime_daemon.py`
- `src/estate/core/operations_runtime.py`
- `src/estate/core/background_operations_runtime.py`
- `src/estate/core/steward_command_center.py`
- `src/estate/cli/main.py`
- `src/estate/core/work_package_validation.py`

## CLI Requirements

Add commands equivalent to:

```powershell
python -m estate.cli.main background-scheduler status --json
python -m estate.cli.main background-scheduler run-eligible --json
python -m estate.cli.main background-scheduler pause --json
python -m estate.cli.main background-scheduler resume --json
python -m estate.cli.main background-scheduler service-show --service-id merge-discovery --json
```

Follow existing CLI conventions if names differ.

## Test Requirements

Tests must prove:

- interval and event eligibility
- dependency ordering
- bounded concurrency
- retries and backoff
- timeout handling
- duplicate suppression
- failure isolation
- starvation prevention
- persistent state recovery
- truthful Office status
- no provider, dispatch, routing, or acceptance authority is introduced

## Validation

```powershell
Clear-Host
cd A:\theestate
python -m py_compile src\estate\core\background_scheduler.py src\estate\core\background_scheduler_runtime.py
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_background_scheduler.py tests/test_background_scheduler_runtime.py tests/test_operations_runtime_daemon.py --basetemp Temp/pytest-background-scheduler
python -m estate.cli.main validate-work-package --id WP-0628 --json
```

## Live Demonstration

Demonstrate one scheduler cycle with multiple eligible services where:

- dependencies run in order
- unrelated services continue after one failure
- concurrency limits are honored
- state survives restart
- Office status shows real scheduler posture

## Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0628_codex_done.json
```

Report registered services, dependency edges, cycle results, failures isolated, retries performed, concurrency observed, provider execution performed (false), and dispatch execution performed (false).

## Promotion Criteria

Ready when one scheduler reliably coordinates the Estate's background services without duplicate loops, hidden authority, or Steward micromanagement.
