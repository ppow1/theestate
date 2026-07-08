# WP-EXECUTION-DISPATCH-QUEUE-001 - Provider-Agnostic Execution Dispatch Queue

Status: Proposed
Priority: High
Owner: Chief Architect / Steward
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Office of the Steward, Alfred, Helen, future Operations/Orchestrator, execution providers
Classification: Estate Internal
Created: 2026-07-08

## Codex Command

Read this work package and do exactly what it says.

Do not build the full orchestrator.

Do not dispatch live external provider calls by default.

Do not create a new Office.

Do not bypass Ingrid/security boundaries.

Do not assume only one worker or provider exists.

## Assignment Notation

The Steward may assign implementation work using shorthand such as:

```text
A2C1 = Assigned to Codex Seat 1
A2C2 = Assigned to Codex Seat 2
A2C3 = Assigned to Codex Seat 3
```

These are operational profile labels. Preserve them in queue/status/audit artifacts as labels only.

## Mission

Implement the first provider-agnostic Execution Dispatch Queue.

This queue is the missing operational layer between work packages and execution providers:

```text
work package / assignment
-> dispatch request
-> queue state
-> provider selection metadata
-> visible execution status
-> provider bridge invocation later
```

The goal is not to create the final Orchestrator. The goal is to create a local, testable, provider-neutral queue that can hold planned work, preserve assignment/provider intent, expose current queue state to the Office of the Steward, and prepare clean handoff into execution providers such as Codex Bridge.

## Background

The Estate now has:

- a Codex Bridge implementation for bounded provider execution
- an Execution Activity Surface that aggregates provider/runtime activity
- Office of the Steward visibility hooks for execution activity

The next missing piece is a dispatch queue that represents pending and active work before provider execution.

Without a queue, work remains trapped in human memory, terminal commands, or one-off package handoffs. With a queue, Alfred/future Operations/future Orchestrator can reason over pending work without immediately executing it.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/collaboration/Local_Execution_Adapter_Protocol_v1.md
docs/architecture/execution_provider_operational_visibility_requirements.md
docs/architecture/execution_provider_codex_cli_mapping.md
docs/integration/execution_activity_surface_usage.md
docs/integration/codex_bridge_usage.md
```

If any file is missing locally, record it in the implementation report and continue with available canonical files.

## Scope

Implement a local execution dispatch queue that supports:

1. A normalized dispatch request model.
2. A normalized queue item model.
3. Queue persistence under local runtime storage.
4. Enqueue, list, inspect, update-state, cancel, and complete operations.
5. Provider/profile labels such as `codex-cli-openai`, `codex-cli-ollama`, `A2C3`, and `local-ollama`.
6. Work package id and prompt/source path references.
7. Security classification and allowed provider metadata.
8. Priority and dependency fields.
9. Human attention flags.
10. Status export into the Execution Activity Surface or compatible current-status artifact.
11. A dry-run handoff shape suitable for Codex Bridge without invoking live Codex.
12. Tests that do not require live provider calls.

## Out Of Scope

This package must not:

- implement final scheduling intelligence
- auto-select providers using complex policy
- invoke live providers by default
- implement ChatGPT CLI integration
- implement Codex Cloud
- implement multi-seat auto-rotation
- create a new Office
- modify Alfred/Helen/Ingrid authority
- commit live runtime queue files

## Runtime Paths

Use local runtime storage by default.

Suggested paths:

```text
runtime/execution_dispatch/queue.json
runtime/execution_dispatch/events.jsonl
runtime/execution_dispatch/current.json
runtime/execution_dispatch/report.md
```

The repository should not commit live runtime queue state unless a deliberate evidence artifact is created separately.

## Dispatch Request Model

Create or support a dispatch request with fields such as:

```json
{
  "dispatch_id": "dispatch_001",
  "work_package_id": "WP-EXAMPLE",
  "title": "Human-readable task title",
  "requested_by": "Steward",
  "assigned_worker": "Codex Worker",
  "provider": "codex-cli-openai",
  "profile_label": "A2C3",
  "classification": "Estate Internal",
  "priority": "High",
  "state": "Queued",
  "prompt_source": "docs/governance/workers/WP-EXAMPLE.md",
  "allowed_read_paths": [],
  "allowed_write_paths": [],
  "allowed_providers": [],
  "forbidden_providers": [],
  "dependencies": [],
  "validation_commands": [],
  "attention_required": false,
  "created_at": "2026-07-08T00:00:00Z",
  "updated_at": "2026-07-08T00:00:00Z"
}
```

Support state values at minimum:

- `Queued`
- `Waiting`
- `Ready`
- `Running`
- `Blocked`
- `Awaiting Approval`
- `Validation`
- `Completed`
- `Failed`
- `Cancelled`

## Queue Operations

Implement operations equivalent to:

- create/enqueue a dispatch item
- list all items
- list by state
- inspect one item
- update state
- mark blocked with reason
- mark attention required
- cancel item
- complete item with result reference
- generate current queue snapshot
- generate human-readable queue report

If CLI wiring is straightforward, expose commands such as:

```text
python -m estate.cli.main execution-dispatch enqueue --file <request.json>
python -m estate.cli.main execution-dispatch list --json
python -m estate.cli.main execution-dispatch inspect <dispatch_id> --json
python -m estate.cli.main execution-dispatch update-state <dispatch_id> --state Running
python -m estate.cli.main execution-dispatch cancel <dispatch_id>
python -m estate.cli.main execution-dispatch-report
```

If CLI wiring is not straightforward, implement documented Python entry points and defer full CLI wiring to a follow-up package.

## Provider Handoff

Create a dry-run provider handoff shape for Codex Bridge.

For a queued item targeting `codex-cli-openai` or `codex-cli-ollama`, the dispatch layer should be able to produce a bridge request object or file compatible with the Codex Bridge request model, but it must not call live Codex by default.

The handoff should preserve:

- dispatch id
- work package id
- prompt source
- provider
- profile label
- sandbox
- classification
- allowed read paths
- allowed write paths
- validation commands

## Visibility Integration

The dispatch queue must produce Office-visible state.

At minimum, generate:

```text
runtime/execution_dispatch/current.json
runtime/execution_dispatch/report.md
```

The current snapshot should answer:

- What is queued?
- What is ready?
- What is running?
- What is blocked?
- What requires Steward attention?
- Which providers/profiles are assigned future work?
- Which work packages are waiting on dependencies?

If the existing Office of the Steward command center has a clear pattern for adding panels/status fields, add a minimal integration hook for execution dispatch. Do not rewrite the Office UI.

## Event Emission

The dispatch queue should write structured events to:

```text
runtime/execution_dispatch/events.jsonl
```

Required event types:

- `dispatch_enqueued`
- `dispatch_ready`
- `dispatch_started`
- `dispatch_blocked`
- `dispatch_awaiting_approval`
- `dispatch_cancelled`
- `dispatch_completed`
- `dispatch_failed`
- `dispatch_handoff_prepared`

Events should include:

- event id
- dispatch id
- work package id
- provider
- profile label
- state
- timestamp
- attention required
- summary

## Expected Artifacts

Create or update only paths justified by the existing codebase.

Expected implementation artifacts:

```text
src/estate/core/execution_dispatch.py
tests/test_execution_dispatch.py
docs/integration/execution_dispatch_queue_usage.md
```

Likely integration touchpoints, if clean and low-risk:

```text
src/estate/cli/main.py
src/estate/core/steward_command_center.py
src/estate/core/operator_activity_stream.py
src/estate/core/work_package_validation.py
```

## Test Requirements

Tests must cover:

- enqueueing a dispatch request
- listing queued items
- inspecting a dispatch item
- updating state
- cancelling an item
- blocking an item with a reason
- preserving `A2C3` and other profile labels
- rejecting missing classification
- generating current queue snapshot
- generating human-readable queue report
- producing dispatch events
- preparing a Codex Bridge dry-run handoff without live Codex execution
- Office command center integration if implemented
- deterministic output ordering
- no live provider calls

## Validation Recipe Requirement

If the Estate validation framework supports package-specific recipes, add a local validation recipe for this package.

At minimum, document or run:

```powershell
pytest -q tests/test_execution_dispatch.py
python -m estate.cli.main execution-dispatch list --json
python -m estate.cli.main validation-production-readiness --json
```

Do not require live Codex, OpenAI, ChatGPT, Ollama, GitHub, or browser access.

## Implementation Report Requirements

The completion report must state:

- files created or changed
- tests run
- runtime artifacts generated
- CLI commands added or deferred
- Office integration added or deferred
- how dispatch queue state feeds visibility
- how provider handoff works without live execution
- known limitations
- skipped live-provider calls

## Acceptance Criteria

This package is complete when:

- dispatch request and queue item models exist
- queue operations work locally
- queue state is persisted under runtime storage
- dispatch events are emitted
- current queue JSON is generated
- human-readable queue report is generated
- provider/profile labels such as `A2C3` are preserved
- Codex Bridge dry-run handoff can be prepared without live execution
- tests pass without network/provider calls
- Office of the Steward has at least a documented or minimal consumption path
- a completion receipt exists if Codex executes this package

## Known Limitations To Preserve

Preserve these limitations unless separately resolved:

- This is not the full Orchestrator.
- This does not decide final scheduling policy.
- This does not perform live provider execution by default.
- Provider saturation and quota data may remain unknown.
- ChatGPT CLI dispatch shape is not finalized.
- Final Operations Office authority remains an architectural question for Steward review.

## Completion Signal

If implemented by Codex, create:

```text
collaboration/work_packages/completions/WP-EXECUTION-DISPATCH-QUEUE-001_codex_done.json
```

The receipt must include files changed, tests run, runtime artifacts generated, Office integration status, provider handoff behavior, known limitations, and skipped live-provider calls.
