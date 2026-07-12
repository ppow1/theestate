# WP-0650 Validation Recipe

1. `PYTHONPATH=src python -m pytest tests/test_operational_readiness_closure.py`
2. `PYTHONPATH=src python -m estate.cli.main operational-readiness report --json`
3. `PYTHONPATH=src python -m estate.cli.main operations-runtime run-once --operational-readiness --json`

The tests use temporary repositories, deterministic local metadata, and fake validation commands. They do not modify production Scheduled Tasks, credentials, providers, or live runtime services.
