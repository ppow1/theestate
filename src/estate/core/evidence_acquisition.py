"""Bounded provider-neutral acquisition for structured missing evidence."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from estate.core.autonomous_reason_execute_loop import classify_reasoning_response
from estate.core.consultation_execution import ConsultationExecutionRouter
from estate.core.consultation_store import ConsultationStore
from estate.core.grace_consultation_loop import GraceConsultationLoop


MAX_ACQUISITIONS = 3


def acquisition_count(store: ConsultationStore, logical_consultation_id: str) -> int:
    current = store.get(logical_consultation_id)
    count = 0
    for turn in store.get_turn_range(current.root_logical_id):
        count += sum(
            1 for item in store.execution_requests(turn.logical_consultation_id)
            if item.required_capability in {"repository_read", "filesystem_read", "test_inspection", "configuration_inspection", "software_engineering_readonly"}
        )
    return count


class EvidenceAcquisitionRuntime:
    def __init__(self, store: ConsultationStore, router: ConsultationExecutionRouter, *, runtime_root: str | Path = r"A:\theestate") -> None:
        self.store = store
        self.router = router
        self.runtime_root = Path(runtime_root)

    def acquire(self, logical_consultation_id: str, response: dict[str, Any]) -> dict[str, Any]:
        decision = classify_reasoning_response(response)
        if decision.classification != "MORE_REASONING_REQUIRED" or not decision.evidence_request:
            raise ValueError("structured_evidence_request_required")
        request = decision.evidence_request
        if request["consultation_id"] != logical_consultation_id:
            raise ValueError("evidence_request_consultation_mismatch")
        prior_count = acquisition_count(self.store, logical_consultation_id)
        prior = [object()] * prior_count
        if len(prior) >= MAX_ACQUISITIONS:
            raise ValueError("EVIDENCE_ACQUISITION_LIMIT_REACHED")
        # Current/previous bounded consultation evidence satisfies the request
        # only when the requested target and acceptance facts are present.
        history = self.store.latest_turns(logical_consultation_id, 5)
        serialized = "\n".join(
            str({
                "evidence": t.validation_evidence,
                "current": t.current_evidence,
                "response": (t.response or {}).get("content", "") if isinstance(t.response, dict) else t.response,
            })
            for t in history
        )
        target = str(request.get("target") or request.get("objective") or "")
        if target and target in serialized and all(str(item) in serialized for item in request["evidence_requirements"]):
            return {"status": "evidence_available_locally", "logical_consultation_id": logical_consultation_id, "evidence": {"source": "consultation_store", "summary": serialized[:4000]}}
        reservation = self.store.reserve_evidence_acquisition(
            logical_consultation_id,
            "|".join([str(request.get("target") or ""), str(request.get("objective") or ""), str(request.get("consultation_id") or "")]),
            max_acquisitions=MAX_ACQUISITIONS,
        )
        if reservation.get("status") != "reserved":
            return {"status": "evidence_acquisition_already_reserved", "logical_consultation_id": logical_consultation_id, "slot": reservation.get("slot")}
        execution = self.router.create_request(
            logical_consultation_id,
            required_capability=str(request["required_capability"]),
            dispatch_id=f"dispatch-{logical_consultation_id.replace('.', '-')}-evidence-{len(prior)+1}",
            prompt_source=str(request.get("target") or request["objective"]),
            classification="Estate Internal",
            read_scope_paths=[str(x) for x in request["allowed_scope"]],
            write_scope_paths=[],
            blocked_scope_paths=[str(x) for x in request["prohibited_scope"]],
            expected_outputs=[str(x) for x in request["evidence_requirements"]],
            validation_required=True,
            decision_reference="consultation-evidence-acquisition",
            preferred_provider=request.get("preferred_provider"),
            metadata={"purpose": "EVIDENCE_ACQUISITION", "evidence_request": request},
        )
        result = self.router.execute(execution.adapter_request_id)
        package = {
            "evidence_request": request,
            "source": "execution_provider",
            "provider_id": result.provider_id,
            "status": result.status,
            "summary": result.summary[:4000],
            "artifacts": result.artifacts,
            "result_reference": self.store.execution_request(execution.adapter_request_id).result_reference,
        }
        self.store.append_validation(logical_consultation_id, observed_result="EVIDENCE_ACQUIRED" if result.status == "completed" else "EVIDENCE_ACQUISITION_FAILED", evidence=package, status="validating" if result.status == "completed" else "continuation_required")
        if result.status != "completed":
            return {"status": "evidence_acquisition_failed", "package": package}
        continuation = ConsultationExecutionRouter(self.store, [], runtime_root=self.runtime_root).continue_from_execution(
            logical_consultation_id,
            execution.adapter_request_id,
            question="Reevaluate the consultation using the acquired bounded evidence and provide the revised conclusion.",
            continuation_reason="bounded evidence acquired for MORE_REASONING_REQUIRED",
        )
        loop = GraceConsultationLoop(store=self.store)
        loop._create_and_attach(continuation)
        self.store.set_status(continuation.logical_consultation_id, "awaiting_reasoning")
        worker = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
             r"A:\theestate\tools\start_chatgpt_mailbox_worker_canonical.ps1", "--once"],
            capture_output=True, text=True, timeout=360, check=False,
        )
        if worker.returncode != 0:
            raise RuntimeError("evidence_reevaluation_worker_failed:" + " ".join(worker.stderr.split())[:240])
        return {"status": "evidence_acquired_reevaluation_queued", "logical_consultation_id": logical_consultation_id, "continuation_id": continuation.logical_consultation_id, "execution_request_id": execution.adapter_request_id, "package": package}
