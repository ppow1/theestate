# WP-4019 — Estate Discovery and Rediscovery Engine

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4012
Classification: Estate Internal

## Objective

Implement the local Estate discovery engine that scans approved roots, identifies services and artifacts, detects additions or removals, and republishes normalized discovery evidence into existing registries and status surfaces.

## Required Implementation

- Reuse existing discovery, service inventory, document registry, provenance, and knowledge-index mechanisms.
- Support configurable approved roots for Estate code, AI services, models, workflows, tools, and operational artifacts.
- Detect new, changed, moved, missing, and duplicate items.
- Generate stable discovery IDs from canonical paths and content metadata.
- Record source path, type, owner, capability hints, version, health evidence, classification, and last-seen time.
- Support full scan and incremental rediscovery.
- Add dry-run, diff, apply, status, and inspect CLI commands.
- Apply updates only through existing registries or catalogs; do not silently create institutional truth.
- Integrate discovery status with the knowledge index, AI service catalog, model control, and Office status surfaces.
- Add tests for move detection, duplicate detection, stale entries, ignored paths, malformed artifacts, and idempotent rediscovery.

## Deliverables

- local discovery and rediscovery service;
- versioned discovery schemas;
- CLI and existing registry integration;
- tests and local demonstration;
- `operations/validation/reports/WP-4019_estate_discovery_engine.md`;
- `collaboration/work_packages/completions/WP-4019_codex_done.json`.

## Boundaries

Do not create a second service catalog, model registry, document registry, or knowledge index. Do not scan unrestricted personal or protected paths. Do not auto-start discovered services.

## Acceptance Criteria

- approved roots can be scanned deterministically;
- additions, changes, moves, and removals are visible;
- apply is idempotent;
- existing registries receive normalized evidence;
- ignored and protected paths remain excluded;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4019_Estate_Discovery_and_Rediscovery_Engine.md and do exactly what it says.
```
