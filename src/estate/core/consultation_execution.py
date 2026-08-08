"""Provider-neutral execution integration for consultation turns.

The consultation layer owns correlation only.  Concrete providers remain
behind ``ExecutionProviderAdapter`` and physical attempts remain tracked by
``ExecutionAttemptRuntime``.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from estate.core.consultation_store import ConsultationStore
from estate.core.execution_attempt_runtime import ExecutionAttemptRuntime
from estate.core.execution_provider_adapter import ExecutionProviderAdapter, ExecutionProviderAdapterRequest, ExecutionProviderAdapterResult
from estate.core.execution_provider_adapter_runtime import write_adapter_request, write_adapter_result, write_status_artifacts


@dataclass(frozen=True)
class ProviderBinding:
    adapter: ExecutionProviderAdapter
    capabilities: frozenset[str]


class ConsultationExecutionRouter:
    """Route a neutral consultation execution request to injected adapters.

    This is intentionally an in-process selection seam, not a second
    provider registry.  The Estate can replace the bindings with its
    existing routing evidence without changing consultation records.
    """

    def __init__(self, store: ConsultationStore, bindings: Iterable[ProviderBinding], *, runtime_root: str | Path) -> None:
        self.store = store
        self.bindings = tuple(bindings)
        self.runtime_root = Path(runtime_root)
        self.request_root = self.runtime_root / "runtime" / "consultation_execution" / "requests"

    def _select(self, required_capability: str, preferred_provider: str | None = None) -> ProviderBinding:
        candidates = [binding for binding in self.bindings if required_capability in binding.capabilities]
        if preferred_provider:
            candidates = [binding for binding in candidates if binding.adapter.provider_id == preferred_provider]
        if not candidates:
            raise ValueError("no_execution_provider_for_required_capability")
        return candidates[0]

    def create_request(self, logical_consultation_id: str, *, required_capability: str,
                       dispatch_id: str, prompt_source: str, classification: str,
                       read_scope_paths: list[str], write_scope_paths: list[str] | None = None,
                       blocked_scope_paths: list[str] | None = None,
                       expected_outputs: list[str] | None = None,
                       validation_required: bool = True, decision_reference: str | None = None,
                       preferred_provider: str | None = None, metadata: dict[str, Any] | None = None) -> ExecutionProviderAdapterRequest:
        binding = self._select(required_capability, preferred_provider)
        request = ExecutionProviderAdapterRequest.create(
            adapter_request_id=f"exec-{uuid4().hex[:12]}",
            dispatch_id=dispatch_id,
            provider_id=binding.adapter.provider_id,
            provider_type=binding.adapter.provider_type,
            prompt_source=prompt_source,
            classification=classification,
            read_scope_paths=read_scope_paths,
            write_scope_paths=write_scope_paths or [],
            blocked_scope_paths=blocked_scope_paths or [],
            expected_outputs=expected_outputs or [],
            validation_required=validation_required,
            decision_reference=decision_reference,
            metadata={**(metadata or {}), "consultation_id": logical_consultation_id, "required_capability": required_capability},
        )
        self.request_root.mkdir(parents=True, exist_ok=True)
        write_adapter_request(request, root=self.runtime_root)
        self.store.attach_execution_request(
            logical_consultation_id,
            request.adapter_request_id,
            dispatch_id=dispatch_id,
            provider_id=request.provider_id,
            provider_type=request.provider_type,
            required_capability=required_capability,
            status="queued",
        )
        return request

    def execute(self, execution_request_id: str) -> ExecutionProviderAdapterResult:
        link = self.store.execution_request(execution_request_id)
        request = ExecutionProviderAdapterRequest.from_dict(json.loads((self.runtime_root / "runtime" / "execution_adapters" / "requests" / f"{execution_request_id}.json").read_text(encoding="utf-8")))
        binding = next((item for item in self.bindings if item.adapter.provider_id == request.provider_id and item.adapter.provider_type == request.provider_type), None)
        if binding is None:
            self.store.update_execution_request(execution_request_id, status="failed")
            raise ValueError("execution_provider_binding_missing")
        attempts = self.store.execution_attempts(execution_request_id)
        if attempts and attempts[-1].status == "completed":
            raise ValueError("execution_request_already_completed")
        self.store.update_execution_request(execution_request_id, status="running")
        attempt_runtime = ExecutionAttemptRuntime(root=self.runtime_root)
        lease = attempt_runtime.acquire_lease(
            dispatch_id=request.dispatch_id,
            adapter_request_id=request.adapter_request_id,
            provider_id=request.provider_id,
            provider_type=request.provider_type,
            metadata={"source": "consultation_execution_router", "consultation_id": link.logical_consultation_id},
        )
        attempt_id = lease["attempt"]["execution_attempt_id"]
        self.store.record_execution_attempt(execution_request_id, attempt_id, provider_id=request.provider_id, status="running")
        self.store.update_execution_request(execution_request_id, current_attempt_id=attempt_id)
        try:
            result = binding.adapter.submit(request)
            result_path = write_adapter_result(result, root=self.runtime_root)
            write_status_artifacts(result, root=self.runtime_root)
            attempt_status = "completed" if result.status == "completed" else "failed"
            attempt_runtime.complete_attempt(attempt_id, status=attempt_status, result_reference=str(result_path))
            self.store.record_execution_attempt(execution_request_id, attempt_id, provider_id=request.provider_id, status=attempt_status, result_reference=str(result_path))
            self.store.update_execution_request(
                execution_request_id,
                status=result.status,
                result=result.to_dict(),
                result_reference=str(result_path),
                validation_status=result.validation_status,
            )
            return result
        except Exception:
            attempt_runtime.complete_attempt(attempt_id, status="failed")
            self.store.record_execution_attempt(execution_request_id, attempt_id, provider_id=request.provider_id, status="failed")
            self.store.update_execution_request(execution_request_id, status="failed")
            raise

    def continue_from_execution(self, logical_consultation_id: str, execution_request_id: str, *,
                                question: str, continuation_reason: str) -> Any:
        """Allocate a new reasoning turn only when execution evidence changes the problem."""
        link = self.store.execution_request(execution_request_id)
        if link.logical_consultation_id != logical_consultation_id:
            raise ValueError("execution_consultation_mismatch")
        if link.status not in {"completed", "failed", "blocked"}:
            raise ValueError("execution_result_not_terminal")
        evidence = {
            "execution_request_id": execution_request_id,
            "execution_status": link.status,
            "execution_provider_id": link.provider_id,
            "execution_result_reference": link.result_reference,
            "execution_result": link.result_json,
        }
        return self.store.allocate_continuation(
            logical_consultation_id,
            question=question,
            continuation_reason=continuation_reason,
            current_evidence=evidence,
            prior_context_summary=self.store.compact_summary(logical_consultation_id)["summary"],
        )
