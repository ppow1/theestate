# WP-4028 — Local AI Service Supervision and Recovery

Status: Pending
Workstream Mode: PARALLEL-STAGED
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Classification: Estate Internal

## Objective

Stage local supervision and recovery for resident-facing AI services such as Ollama, TextGen, Open WebUI, and the Estate resident gateway.

## Conflict Surface

Expected integration targets:

- AI service control modules;
- background operations runtime;
- resident gateway status;
- `src/estate/cli/main.py`;
- Office AI Services and resident surfaces.

Conflict risk: high.

## Staged Paths

Use only `collaboration/workstreams/WP-4028/` for source, tests, fake service runners, integration notes, and `install_manifest.json`.

## Required Implementation

Stage:

- service health checks;
- dependency ordering;
- approved start, stop, restart, and status plans;
- occupied-port detection;
- stale-process detection;
- bounded recovery policy;
- startup timeout and cold-load handling;
- diagnostics and logs metadata;
- service-specific recovery hints;
- resident-impact reporting;
- Office-safe control payloads.

Reuse existing AI Services, background operations, approval, audit, and Office action systems.

## Boundaries

Do not create a second service registry, scheduler, event loop, or approval path. Do not auto-start services during deterministic tests. Do not add cloud dependencies.

## Acceptance Criteria

- service and dependency states are truthful;
- recovery actions remain approval-bound;
- occupied ports and stale processes are diagnosable;
- failure does not fabricate resident availability;
- staged tests pass using fake runners;
- manifest is complete and marks work uninstalled.

## Required Install Handoff

WP-4031 installs shared AI-service, CLI, runtime, and Office integrations.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4028_Local_AI_Service_Supervision_and_Recovery.md and do exactly what it says.
```
