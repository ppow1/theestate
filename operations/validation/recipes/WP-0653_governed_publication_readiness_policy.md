# WP-0653 Governed Publication and Production Readiness Policy Validation Recipe

Run from the repository root:

```bash
PYTHONPATH=src pytest tests/test_operational_readiness_closure.py -q
PYTHONPATH=src python -m py_compile src/estate/core/operational_readiness_closure.py src/estate/cli/main.py src/estate/core/office_command_surface.py
PYTHONPATH=src python -m estate.cli.main operational-readiness report --json
```

Acceptance expectations:

- controller-authored canonical commits are not complete until publication is authorized, pushed, fetched, verified by upstream ancestry, and synchronized;
- local-only controller commits keep readiness active or blocked, never `operationally_ready`;
- production targets require explicit validation, live target, observation, publication, lifecycle, and acceptance policy metadata;
- institutional acceptance remains false unless separately granted by authority.
