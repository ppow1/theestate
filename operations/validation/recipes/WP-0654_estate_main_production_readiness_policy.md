# WP-0654 Validation Recipe — estate-main Production Readiness Policy

Run from the repository root with `PYTHONPATH=src`.

1. `PYTHONPATH=src pytest -q tests/test_operational_readiness_closure.py`
2. `PYTHONPATH=src pytest -q tests/test_operational_targets.py tests/test_operational_targets_runtime.py tests/test_operational_target_resolution.py tests/test_operational_readiness_closure.py`
3. `PYTHONPATH=src python -m py_compile src/estate/core/operational_readiness_closure.py src/estate/core/operational_targets.py src/estate/core/operational_targets_runtime.py src/estate/cli/main.py`
4. `PYTHONPATH=src python -m estate.cli.main operational-readiness report --json`
5. Live Windows acceptance must be run on the configured Windows Estate environment; Linux-only simulation is not sufficient for production closure.
