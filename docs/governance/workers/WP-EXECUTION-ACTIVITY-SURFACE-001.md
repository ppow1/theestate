# WP-EXECUTION-ACTIVITY-SURFACE-001 - Execution Activity Surface and Office Visibility

Status: Proposed
Priority: High
Owner: Chief Architect / Steward
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Office of the Steward, Alfred, Helen, future Operations/Orchestrator, execution providers
Classification: Estate Internal
Created: 2026-07-08

## Codex Command

Read this work package and do exactly what it says.

Do not create a new Office.

Do not build a full orchestrator.

Do not replace existing Office of the Steward architecture.

Do not assume only one worker is active.

Do not hide execution status in terminal-only output.

## Assignment Notation

The Steward may use seat-assignment shorthand such as:

```text
A2C1 = Assigned to Codex Seat 1
A2C2 = Assigned to Codex Seat 2
A2C3 = Assigned to Codex Seat 3
```

`C1`, `C2`, and `C3` refer to Codex Chrome/profile/seat designations associated with ChatGPT Business plan seats. These labels are operational profile labels, not credentials. They may be stored in runtime status and audit artifacts as profile labels, but no secret auth paths or tokens may be stored in repository artifacts.

## Mission

Implement the first shared Execution Activity Surface so execution-provider activity can be observed by the Office of the Steward without inspecting terminal windows.

This package connects the provider-event concept to a practical local implementation:

```text
execution provider runtime events
-> local execution activity records
-> current activity snapshot
-> CLI/report output
-> Office of the Steward visibility hook
```

The goal is not to build the final orchestrator. The goal is to make asynchronous worker activity visible, structured, auditable, and ready for Office consumption.

## Background

The Codex Bridge implementation package requires lifecycle events and status snapshots under `runtime/codex_bridge/`.

The Estate also now has an architectural requirement that execution providers must support operational visibility:

```text
governed dispatch -> visible activity -> structured events -> auditable result -> Steward-visible decision state
```

This package implements the shared activity layer that can consume provider events from Codex Bridge first, then later from ChatGPT CLI, Ollama workers, validation workers, and other providers.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/collaboration/Local_Execution_Adapter_Protocol_v1.md
docs/architecture/execution_provider_operational_visibility_requirements.md
docs/architecture/execution_provider_codex_cli_mapping.md
docs/governance/workers/WP-CODEX-BRIDGE-IMPLEMENTATION.md
```

If any file is missing locally, record that in the implementation report and continue with the available canonical files.

## Scope

Implement a local activity surface that supports:

1. A normalized execution activity event model.
2. A normalized current activity snapshot model.
3. Local ingestion of provider events from runtime paths.
4. Aggregation across multiple concurrent workers/providers.
5. A machine-readable current activity artifact.
6. A human-readable activity report.
7. A CLI command or documented Python entry point.
8. Tests that do not require live Codex, OpenAI, ChatGPT, or Ollama calls.
9. A minimal Office of the Steward integration hook, if the existing Office code has a clear pattern for local JSON/status consumption.

## Out Of Scope

This package must not:

- implement the full orchestrator
- implement worker scheduling
- implement provider dispatch
- implement Codex Bridge internals beyond adapting to its emitted event/status shapes if present
- implement ChatGPT CLI integration
- create a new Office
- change Alfred, Helen, or Ingrid authority
- commit live runtime logs
- store credentials, auth paths, tokens, or secrets
- require network access

## Required Runtime Paths

Use local runtime storage by default.

Suggested paths:

```text
runtime/execution_activity/events.jsonl
runtime/execution_activity/current.json
runtime/execution_activity/report.md
```

Provider-specific sources may include:

```text
runtime/codex_bridge/events.jsonl
runtime/codex_bridge/current.json
```

If existing repository conventions use a different runtime/status location, follow the existing convention and explain the choice in the implementation report.

## Event Model

Create or support normalized event records with these fields where available:

```json
{
  "event_id": "evt_...",
  "request_id": "req_...",
  "work_package_id": "WP-...",
  "source": "codex_bridge",
  "worker_label": "Codex Bridge",
  "provider": "codex-cli-openai",
  "profile_label": "A2C3",
  "state": "Running",
  "event_type": "execution_started",
  "timestamp": "2026-07-08T00:00:00Z",
  "elapsed_seconds": 0,
  "classification": "Estate Internal",
  "budget_source": "ChatGPT Business Seat 3",
  "validation_status": "not_started",
  "attention_required": false,
  "summary": "Execution started."
}
```

Required event types include:

- `job_accepted`
- `execution_started`
- `checkpoint_reached`
- `waiting_for_approval`
- `validation_started`
- `validation_passed`
- `validation_failed`
- `commit_created`
- `result_returned`
- `execution_complete`
- `execution_failed`
- `policy_denied`

The implementation may tolerate unknown future event types, but must preserve them without crashing.

## Current Activity Snapshot Model

Create or support a current activity snapshot that can answer:

- What is currently running?
- What completed recently?
- What is blocked?
- What requires Steward attention?
- Which workers/providers are idle or unknown?
- Which providers are saturated, if known?

Minimum snapshot shape:

```json
{
  "generated_at": "2026-07-08T00:00:00Z",
  "source": "runtime/execution_activity/events.jsonl",
  "active": [],
  "blocked": [],
  "attention_required": [],
  "recently_completed": [],
  "failed": [],
  "providers": [],
  "warnings": []
}
```

Each activity item should include:

- request id
- work package id
- worker label
- provider
- profile label, such as `A2C3`, when available
- current assignment
- current state
- elapsed time
- estimated completion, if known
- budget source, if known
- security classification
- validation status
- last event
- attention required
- summary

## Ingestion Requirements

The implementation should ingest:

1. Normalized events already present in `runtime/execution_activity/events.jsonl`.
2. Provider events from `runtime/codex_bridge/events.jsonl`, if present.
3. Provider current snapshot from `runtime/codex_bridge/current.json`, if present.

Missing runtime files should not fail the command. They should produce warnings and an empty/partial report.

Do not read secrets or provider auth stores.

Do not export raw prompts or raw stdout/stderr into committed files.

## Office of the Steward Hook

If the existing Office of the Steward command surface has a clear local JSON/status loading pattern, add a small integration hook that reads the generated current activity artifact.

Acceptable minimal forms include:

- a CLI command that the Office can call later
- a generated JSON path documented for Office consumption
- a small status card/panel if the existing command center architecture makes that low-risk

Do not perform a large UI rewrite.

Do not create a duplicate dashboard if the existing Office command center can absorb the surface.

## Expected Artifacts

Create or update only paths justified by the existing codebase.

Expected implementation artifacts:

```text
src/estate/core/execution_activity.py
tests/test_execution_activity.py
docs/integration/execution_activity_surface_usage.md
```

If CLI structure supports it cleanly, add one or more commands such as:

```text
python -m estate.cli.main execution-activity --json
python -m estate.cli.main execution-activity-report
```

If CLI wiring is not straightforward, provide a documented Python entry point and defer CLI wiring to a follow-up package.

## Test Requirements

Tests must cover:

- parsing JSONL activity events
- tolerating unknown event types
- handling missing runtime files without failure
- aggregating active, blocked, attention-required, failed, and recently completed items
- preserving profile labels such as `A2C3`
- generating `current.json`
- generating `report.md`
- redacting or excluding secrets/auth paths
- avoiding live network calls
- deterministic output ordering for stable tests

## Validation Recipe Requirement

If the Estate validation framework supports package-specific recipes, add a local validation recipe for this package.

At minimum, document or run:

```powershell
pytest tests/test_execution_activity.py
python -m estate.cli.main validation-production-readiness --json
```

Do not require live Codex, OpenAI, ChatGPT, Ollama, or GitHub network access.

## Implementation Report Requirements

The completion report must state:

- files created or changed
- tests run
- runtime artifacts generated
- whether Office integration was implemented or deferred
- how Codex Bridge events/status can feed this surface
- known limitations
- whether any live provider calls were skipped

## Acceptance Criteria

This package is complete when:

- a normalized execution activity model exists
- multiple provider/worker records can be aggregated
- current activity JSON can be generated locally
- a human-readable activity report can be generated locally
- missing provider runtime files produce warnings, not hard failures
- profile labels such as `A2C3` are preserved as operational labels
- tests pass without network or live provider access
- no secrets are stored in repository artifacts
- Office of the Steward has at least a documented consumption path
- a completion receipt exists if Codex executes this package

## Known Limitations To Preserve

Preserve these limitations unless separately resolved:

- Provider saturation may be unknown until provider-specific quota reporting exists.
- Codex `/status` remains interactive unless separately automated.
- ChatGPT CLI status is not defined yet.
- Final Office UI presentation may require a separate Office work package.
- This package does not decide whether an Operations Office is required.

## Completion Signal

If implemented by Codex, create:

```text
collaboration/work_packages/completions/WP-EXECUTION-ACTIVITY-SURFACE-001_codex_done.json
```

The receipt must include files changed, tests run, runtime artifacts generated, Office integration status, known limitations, and skipped live-provider calls.
