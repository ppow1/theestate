# Operational Readiness Closure Controller v1

WP-0650 is implemented by `estate.core.operational_readiness_closure` as the single canonical controller inside the existing Estate Operations Runtime. It consumes merge/work-package evidence, operational target metadata, validation recipes, activation ledger state, and existing Office command actions.

## State transition table

`merged`/`assessment_required` assess target state; policy-authorized blockers move to `remediation_in_progress`; unsafe or unhandled blockers move to `blocked_manual_intervention`, `blocked_authority_required`, or `blocked_unsafe_action`; clean cases move through `live_validation_required`, `observation_required`, `observation_in_progress`, and finally `operationally_ready`. Retry exhaustion moves to `failed_bounded_retries`. Institutional acceptance is not granted by the controller.

## Remediation handlers

| Handler | Preconditions | Safety behavior |
| --- | --- | --- |
| `fast_forward_checkout` | Target policy authorizes it; checkout is clean, correct branch, and upstream/base branch are declared. | Fetches and `merge --ff-only`; never force resets, rewrites history, or discards work. |
| `create_declared_runtime_directories` | Target metadata declares runtime directories and target policy authorizes the handler. | Creates only declared directories under the Estate root. |
| `update_activation_ledger` | Target activation requirement declares ledger evidence and policy authorizes the handler. | Appends evidence to the existing Estate Feature Activation Ledger; no duplicate inventory is created. |

## CLI

Use `PYTHONPATH=src python -m estate.cli.main operational-readiness ...` with actions: `intake`, `list`, `show`, `process-one`, `cycle`, `pause`, `resume`, `acknowledge`, `status`, and `report`. All actions support JSON output.

## Office actions

Existing Office command-surface handlers are provided for list, process, pause, resume, and acknowledge. They call the canonical controller directly and write `operations/steward/operational_readiness_closure.md` for accessible Steward visibility.

## Validation recipe

Run `PYTHONPATH=src python -m pytest tests/test_operational_readiness_closure.py` followed by `PYTHONPATH=src python -m estate.cli.main operational-readiness report --json`.
