# Orchestrator Runtime Core

Status: Implemented  
Classification: Estate Internal

## Purpose

The Orchestrator Runtime Core runs one bounded local orchestration cycle. It reads scheduled work, validates dispatch eligibility against governance and provider evidence, creates dispatch records, updates Office-readable status artifacts, and emits operational events when the shared event feed is available.

This package coordinates work. It does **not** execute providers, invoke Codex, call ChatGPT, run browser automation, create workers, or install a daemon.

## Runtime State Model

`OrchestratorRuntimeState` records the cycle id, timestamps, mode (`dry_run` or `single_cycle`), lifecycle state, item counts, warning/error lists, event count, and metadata. Latest status is written to:

- `runtime/orchestrator/runtime/status/latest.json`
- `runtime/orchestrator/runtime/status/summary.md`
- `runtime/orchestrator/runtime/cycles/<cycle_id>.json`

## Dispatch Record Model

`DispatchRecord` records a governed handoff candidate with provider, assignment, schedule, intake, classification, paths, outputs, validation requirement, boundary/decision references, and blocked/deferred reasons. Allowed dispatch states are:

- `pending_dispatch`
- `blocked`
- `deferred`
- `cancelled`

Provider execution states such as running or completed are intentionally not dispatch states.

## Cycle Behavior

A cycle:

1. Loads `runtime/orchestrator/schedule/status/queue.json` when available.
2. Loads provider catalog, provider health, provider capacity, and assignment board artifacts when available.
3. Evaluates scheduled items only.
4. Creates pending, blocked, or deferred dispatch records in single-cycle mode.
5. Writes queue and runtime status artifacts.
6. Emits operational events through the shared operational event feed when possible.
7. Prints a concise summary and exits.

If no schedule queue exists, the cycle exits cleanly with a no-work warning. Malformed upstream artifacts are reported in runtime errors or warnings.

## Runtime Artifact Locations

- `runtime/orchestrator/runtime/status/latest.json`
- `runtime/orchestrator/runtime/status/summary.md`
- `runtime/orchestrator/runtime/cycles/`
- `runtime/orchestrator/dispatch/pending/`
- `runtime/orchestrator/dispatch/blocked/`
- `runtime/orchestrator/dispatch/deferred/`
- `runtime/orchestrator/dispatch/completed/`
- `runtime/orchestrator/dispatch/status/queue.json`

## CLI Examples

```powershell
Clear-Host
cd A:\theestate
.\estate.bat orchestrator-cycle --dry-run
.\estate.bat orchestrator-cycle --single
.\estate.bat orchestrator-dispatch-list
```

## Eligibility Rules

Pending dispatch requires scheduled state, approval evidence, valid classification, provider identity or type, an active compatible provider catalog entry, available provider health/capacity, compatible assignment state, and required work package path evidence when applicable.

Blocked dispatches are created for missing approval, missing boundary review, invalid classification, blocked/deprecated providers, provider capability or classification conflicts, blocked assignments, and missing required work package paths.

Deferred dispatches are created for unknown provider catalog, unknown provider health or capacity, unavailable assignment evidence, unknown provider identity, and busy/saturated/quota-limited provider capacity where safe queueing should wait for better evidence.

Every blocked or deferred dispatch includes a reason.

## Relationships

- **Intake:** The runtime consumes schedule records that originated from approved intake and preserves intake references.
- **Decisions:** Approval and decision references are preserved on dispatch records.
- **Scheduling:** The runtime reads scheduled queue artifacts; it does not replace the scheduler.
- **Provider catalog:** Catalog entries determine whether provider IDs/types, capabilities, status, and classification ceilings are compatible.
- **Provider health:** Health records prevent dispatch to blocked, offline, out-of-quota, saturated, or unknown providers.
- **Provider capacity:** Capacity records defer work when capacity is unknown, busy, saturated, or quota-limited.
- **Assignments:** Assignment IDs are checked when present. Terminal, blocked, or unavailable assignment states prevent unsafe dispatch.
- **Operational events:** Dispatch outcomes emit compatibility events using the shared operational event feed when available.

## Non-Execution Boundary

The Orchestrator creates durable dispatch records only. Execution providers own provider-specific running, completed, failed, result, and validation execution records.
