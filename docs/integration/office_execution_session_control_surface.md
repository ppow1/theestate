# Office Execution Session Control Surface

WP-0510 adds an **Execution Control** workspace to the Office of the Steward. The workspace uses the existing Office action endpoint and `office_command_surface.execute_office_action(...)` dispatcher; it does not introduce another command bus, provider path, registry, queue, or web framework.

## Controls

The workspace registers real controls for:

- execution-session preview, start, resume, status, and report generation;
- execution-attempt cancellation request, recovery inspection, retry-eligibility inspection, and explicit stale-lease release;
- result-reconciliation inspection, reconciliation, and reconciliation report generation.

Each control calls the canonical runtime directly:

- `ExecutionSessionController.preview/start/resume/status/report`
- `ExecutionAttemptRuntime.request_cancellation/inspect_recovery/retry_eligibility/release_stale`
- `inspect_reconciliation/reconcile_result/format_reconciliation_report`

## Authority and safety behavior

- Preview performs no provider call.
- Start requires dispatch ID, authorization path, and explicit live-execution confirmation.
- Missing authorization evidence remains blocked by the existing gate.
- Resume preserves ambiguous duplicate-provider-call protection.
- Cancellation records a durable cancellation request but does not claim the provider stopped.
- Retry eligibility writes/updates review evidence but does not start or authorize retry.
- Stale lease release requires explicit confirmation and existing stale-safe recovery evidence.
- Reconciliation is idempotent and keeps institutional acceptance at `not_granted`.

## Browser behavior

The Office renders labeled fields for required IDs and paths rather than requiring source edits. It disables the submitted button while the local request is in flight, renders the returned `OfficeActionResult` JSON, distinguishes outcomes with result classes, and reloads after successful state-changing actions so changed artifacts are visible immediately.

## Validation recipe

Run:

```bash
python -m py_compile src/estate/core/office_command_surface.py src/estate/core/steward_command_center.py
pytest -q tests/test_office_execution_session_controls.py tests/test_office_command_surface.py tests/test_steward_command_center.py tests/test_execution_session_controller.py tests/test_execution_attempt_runtime.py tests/test_execution_result_reconciliation_runtime.py
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0510 --json
```

All provider execution in deterministic validation uses fakes. No live Codex CLI, network, GPU, Ollama, or ChatGPT provider call is required.
