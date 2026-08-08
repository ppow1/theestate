"""Runtime adapter that binds OperationsScheduler to OperationsRuntime."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from estate.core.operations_runtime_service import OperationsRuntimeService
from estate.core.operations_scheduler import OperationsScheduler
from estate.diagnostics.living import reconcile


class OperationsSchedulerRuntime:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root
        self.scheduler = OperationsScheduler(root)

    def list(self) -> dict[str, Any]:
        return self.scheduler.list_jobs()

    def show(self, job: str) -> dict[str, Any]:
        return self.scheduler.describe_job(job)

    def enable(self, job: str) -> dict[str, Any]:
        return self.scheduler.set_enabled(job, True)

    def disable(self, job: str) -> dict[str, Any]:
        return self.scheduler.set_enabled(job, False)

    def trigger(self, event: str) -> dict[str, Any]:
        return self.scheduler.trigger(event)

    def run_due(self) -> dict[str, Any]:
        due = self.scheduler.acquire_due()
        results = []
        service = OperationsRuntimeService(self.root)
        for item in due:
            job = item["job"]
            lease_id = item["lease_id"]
            for _ in range(item.get("catch_up_runs", 1)):
                try:
                    if job.runtime_mode == "living-diagnostics-reconcile":
                        result = reconcile(self.scheduler.root)
                        status = "failed" if result.get("reconciliation_outcome") in {"ACCEPTED_BASELINE_MISSING", "ACCEPTED_BASELINE_INVALID"} else "completed"
                    else:
                        result = service.run_once(dry_run=False, mode=job.runtime_mode, max_audit_requests=job.max_audit_requests)
                        status = "failed" if result.get("runtime_state") == "failed" or result.get("errors") else "completed"
                    error = "; ".join(result.get("errors") or []) or None
                except Exception as exc:  # preserve scheduler state for Office visibility
                    result = {"error": str(exc)}; status = "failed"; error = str(exc)
                self.scheduler.complete(job.job_id, lease_id, status, result, error)
                self.scheduler.emit_office_event(job.job_id, status)
                results.append({"job_id": job.job_id, "status": status, "runtime_mode": job.runtime_mode, "result": result})
                break
        return {"due_count": len(due), "results": results}
