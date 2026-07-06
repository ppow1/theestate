# WP-0136 AI Services TextGen Batch Log and Process Runner Repair Report

## Summary

WP-0136 repaired governed TextGen launch diagnostics by moving AI Services execution logs from a reused service-level path to a unique per-attempt log path. Each launch attempt now creates a fresh log file before process start and records that path in state, audit details, and returned execution diagnostics.

## Implementation Notes

- Added per-attempt log naming under `runtime/ai_services/logs/` with timestamp and random suffix.
- Seeded each attempt log before process start so an empty child-output attempt is still distinguishable from stale logs.
- Preserved structured Windows batch command planning and runner invocation semantics.
- Added process runner tracking for subprocess handles so diagnostics can report liveness and return codes when available.
- Expanded health failure diagnostics with service id, operation, pid, working directory, log path, current-attempt log tail, health endpoint/status/error, liveness, and exit code fields.
- Preserved health interruption handling while keeping interrupted state tied to the selected per-attempt log path.

## Validation

- `PYTHONPATH=src pytest -q tests/test_ai_services_control_plane.py` passed.
- `PYTHONPATH=src pytest -q tests/test_work_package_validation.py tests/test_production_readiness_validation.py` passed.
- `PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json` completed successfully, while continuing to report pre-existing production-readiness blockers for older work packages and WP-0136 missing recipe/receipt status before this completion artifact existed.

## Limitations

No TextGen third-party service was launched or modified. All coverage uses mocks, as required.
