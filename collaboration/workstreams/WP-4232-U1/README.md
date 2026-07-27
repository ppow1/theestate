# WP-4232-U1 — Governed local provider admission and completion lifecycle

This package extends the merged Grace Momentum runtime at its existing public
command/query boundary. It registers one in-process deterministic SHA-256
adapter and persists admission, Dispatch, provider result, reconciliation,
Engineering validation, Grace receipt, completion, stop, rollback, replay, and
idempotency records under the runtime’s governed root.

The adapter has no subprocess, network, egress, spend, filesystem, or machine-
state capability. It is available only in `governed_local_test` mode after
Engineering admission and a complete readiness projection. Fixture and shadow
continue to suppress provider effects. The separately gated final WP-4232
bounded-live input was not executed.

Run the real-runtime evidence pass:

```powershell
$env:PYTHONPATH = 'src'
$env:PYTHONDONTWRITEBYTECODE = '1'
python -c "from estate.core.wp4232_u1_acceptance import WP4232U1Acceptance; WP4232U1Acceptance('collaboration/workstreams/WP-4232-U1').run()"
```

The resulting `acceptance_evidence.json` is produced from loopback clients and
the merged Open WebUI/Estate UI consumers. It uses a package-specific test
input, not the final WP-4232 acceptance string.
