# Automatic Audit Queue and Runtime Host Integrity

WP-0638 repairs the automatic post-merge validation loop so discovery admission is idempotent, queue capacity is based on active audit requests, and durable host status separates process health from bounded cycle completion.

## Queue lifecycle

`post_merge_audit_lifecycle.py` defines the shared active, running, terminal, retryable, and final-verdict classifications used by both admission and audit processing. Admission creates only missing pending requests. Existing pending or running requests count as active capacity, while terminal verdicts release capacity and reconcile candidates as already audited.

## Same-cycle processing

`OperationsRuntime.run_cycle(..., mode="discover-merges-and-process-audits")` runs merge discovery, auto admission, then audit processing in the same cycle. If no request is claimed after admission, the processor records a deterministic zero-throughput reason.

## Host integrity

Bootstrap fetches authoritative `origin/main`, resets the external runtime workspace to that exact revision, verifies the runtime revision matches, and reports source/runtime revisions. The generated launcher sets `ESTATE_OPERATIONS_RUNTIME_ROOT`, `ESTATE_OPERATIONS_RUNTIME_HOST_DIR`, and `PYTHONPATH` explicitly and uses automatic discovery, admission, and audit processing flags.

Host status now reports scheduled-task state, host process state, PID liveness, heartbeat state/age, current/last cycle state, runtime revision, watched remote ref, fetch cursor details, and blocking faults. A sleeping heartbeat with a live PID and valid lock is reported as a running host.

## Authority boundaries

The loop remains validation-only. Provider execution and dispatch execution remain false; validation verdicts do not grant institutional acceptance or bypass Ring 2 review.
