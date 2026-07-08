# Orchestrator Scheduling Skeleton

Status: Implemented  
Classification: Estate Internal

## Purpose

The Orchestrator scheduling skeleton moves approved intake records into local scheduling artifacts. It creates scheduled, deferred, or blocked records and status snapshots. It does **not** execute providers, invoke Codex, call ChatGPT, start workers, or run jobs.

## Schedule Record Model

Schedule records contain identity, timestamps, scheduling actor, state, priority, classification, optional work package and assignment references, optional provider requirements, required capabilities, path boundaries, expected outputs, validation and boundary-review flags, approval/decision references, blocked/deferred reasons, artifact paths, and metadata.

Allowed states are `scheduled`, `deferred`, `blocked`, and `cancelled`. Allowed priorities and classifications reuse the Orchestrator intake contract values.

## Eligibility Rules

A record is scheduled only when the intake exists, is approved or explicitly schedule-eligible, has a valid classification, has completed required boundary review, preserves validation expectations, has no obvious allowed/forbidden path conflict, and has compatible provider catalog evidence when a provider is requested.

A record is blocked when intake is missing, rejected, needs revision, lacks approval, has invalid classification, lacks required boundary review, has a work-package source without a work package path, has obvious path conflicts, or has provider requirements that conflict with catalog evidence.

A record is deferred when the intake is otherwise valid but provider availability cannot be determined, the requested provider is unavailable, catalog evidence is unavailable, or deferral is explicitly requested.

## Runtime Artifact Paths

Runtime directories are created on demand:

- `runtime/orchestrator/schedule/scheduled/`
- `runtime/orchestrator/schedule/deferred/`
- `runtime/orchestrator/schedule/blocked/`
- `runtime/orchestrator/schedule/status/latest.json`
- `runtime/orchestrator/schedule/status/queue.json`

## CLI Examples

```powershell
Clear-Host
cd A:\theestate
.\estate.bat orchestrator-schedule --intake-id <id>
.\estate.bat orchestrator-schedule --request <path-to-json>
.\estate.bat orchestrator-schedule --intake-id <id> --defer
.\estate.bat orchestrator-schedule-list
```

## Intake Decisions

Scheduling reads the existing intake queue and recognizes approved intake decisions from Office decision metadata. It preserves approval and decision references on schedule records where present.

## Provider Catalog

When `config/providers/catalog.json` is available, provider IDs, provider type, capabilities, status, and classification ceiling are checked. If catalog evidence is unavailable, otherwise valid provider-dependent requests are deferred rather than executed or failed.

## Operational Events

Scheduling emits shared operational events through the operational event/status helpers when available. If event writing fails, the schedule artifact remains authoritative and records a compatibility warning.

## Boundary Statement

Restricted and Steward Only records preserve boundary and approval metadata. Sensitive summaries are not printed unless metadata marks them safe. This skeleton schedules only; providers execute in later packages.
