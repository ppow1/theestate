# WP-4019 Estate Discovery and Rediscovery Engine Validation Report

## Summary

Implemented the local Estate discovery engine as a bounded, local-only projection over configured approved roots. The engine scans Estate code, AI service manifests, model-control artifacts, workflows, tools, operational artifacts, registries, and documentation; it detects additions, changes, moves, removals/stale entries, duplicates, ignored paths, protected paths, and unreadable/malformed artifacts.

## Implemented Surfaces

- `src/estate/core/estate_discovery_engine.py` — discovery/rediscovery service, versioned evidence payloads, diffing, status, inspect, and apply.
- `config/discovery/approved_roots.json` — configurable approved-root policy.
- `schemas/discovery/estate_discovery_v1.schema.json` — versioned discovery evidence schema.
- `estate-discovery` CLI commands:
  - `scan`
  - `dry-run`
  - `diff`
  - `apply`
  - `status`
  - `inspect`
- Existing registry/status integrations on apply:
  - AI service catalog rediscovery
  - Estate model-control rediscovery
  - Estate knowledge-index incremental update
  - Office service status board regeneration

## Boundary Compliance

- The engine scans only approved roots.
- Protected/private path parts are excluded.
- Ignored operational/cache paths are excluded.
- Discovery evidence is explicitly marked as a local projection, not institutional truth.
- Apply updates existing generated registries/status surfaces only; it does not create a second service catalog, model registry, document registry, or knowledge index.
- No discovered service is auto-started.

## Validation Commands

- `python -m pytest tests/test_estate_discovery_engine.py`
- `python -m pytest tests/test_estate_discovery_engine.py tests/test_estate_knowledge_index.py tests/test_ai_services_control_plane.py tests/test_model_control.py tests/test_service_status_board.py`
- `PYTHONPATH=src python -m estate.cli.main estate-discovery apply`
- `PYTHONPATH=src python -m estate.cli.main estate-discovery status`

## Current Demonstration Artifacts

- `runtime/discovery/estate_discovery_evidence.json`
- `runtime/discovery/estate_discovery_state.json`
- `runtime/discovery/estate_discovery_status.json`

## Result

WP-4019 acceptance criteria are satisfied for deterministic approved-root scanning, additions/changes/moves/removals visibility, idempotent apply, normalized evidence publication into existing registries/status surfaces, ignored/protected path exclusion, and focused tests.
