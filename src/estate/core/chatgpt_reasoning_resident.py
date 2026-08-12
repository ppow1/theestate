"""Bounded wakeup coordinator for the autonomous ChatGPT reasoning resident.

The resident owns eligibility evaluation and one-shot activation. Comms8 and
the mailbox worker remain authoritative for request lifecycle and processing.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable

from estate.core.consultation_store import ConsultationRecord, ConsultationStore


RESIDENT_STATES = {
    "CHATGPT_REASONER_IDLE",
    "CHATGPT_REASONER_WAKE_PENDING",
    "CHATGPT_REASONER_PROCESSING",
    "CHATGPT_REASONER_WAITING_FOR_EXECUTION",
    "CHATGPT_REASONER_WAITING_FOR_EVIDENCE",
    "CHATGPT_REASONER_ESCALATED",
    "CHATGPT_REASONER_ERROR",
}


def build_durable_context_package(store: ConsultationStore, logical_consultation_id: str, *, latest: int = 5) -> dict[str, Any]:
    """Build bounded context; the current Comms8 envelope carries it to ChatGPT."""
    if latest < 1 or latest > 5:
        raise ValueError("context_latest_must_be_between_1_and_5")
    current = store.get(logical_consultation_id)
    summary = store.compact_summary(current.root_logical_id)
    turns = store.latest_turns(current.root_logical_id, latest)
    executions = []
    for turn in turns:
        for link in store.execution_requests(turn.logical_consultation_id):
            executions.append({
                "turn": turn.logical_consultation_id,
                "execution_request_id": link.execution_request_id,
                "provider_id": link.provider_id,
                "status": link.status,
                "validation_status": link.validation_status,
                "result": link.result_json if isinstance(link.result_json, dict) else None,
            })
    package = {
        "logical_consultation_id": current.logical_consultation_id,
        "root_consultation_id": current.root_logical_id,
        "parent_turn": current.parent_logical_id,
        "objective": current.objective,
        "question": current.question,
        "compact_summary": summary["summary"][:4000],
        "prior_recommendation": (current.prior_context_summary or "")[:1200],
        "current_evidence": current.current_evidence,
        "execution_evidence": executions[-5:],
        "ptm": {"project_id": current.ptm_project_id, "work_item_id": current.ptm_work_item_id},
        "tags": list(current.tags),
        "status": current.status,
    }
    if isinstance(current.current_evidence, dict) and isinstance(current.current_evidence.get("second_opinion"), dict):
        package["second_opinion"] = current.current_evidence["second_opinion"]
    escalation = [item for item in store.escalations() if item.root_logical_id == current.root_logical_id]
    if escalation:
        package["escalation_state"] = escalation[-1].state
    return package


def context_digest(package: dict[str, Any]) -> str:
    return sha256(json.dumps(package, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


class ChatGPTReasoningResident:
    """Evaluate eligible consultation state and activate one mailbox worker."""

    def __init__(self, store: ConsultationStore, *, worker: AutonomousChatGPTMailboxWorker | None = None,
                 state_path: str | Path = r"A:\theestate-data\chatgpt-mailbox-worker\resident-state.json",
                 state_writer: Callable[[dict[str, Any]], None] | None = None) -> None:
        from estate.core.autonomous_chatgpt_mailbox_worker import AutonomousChatGPTMailboxWorker
        self.store = store
        self.worker = worker or AutonomousChatGPTMailboxWorker(store)
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_writer = state_writer or self._write_state

    def _write_state(self, value: dict[str, Any]) -> None:
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)

    def eligible(self) -> list[ConsultationRecord]:
        # A continuation created after escalation is eligible; an unresolved
        # root with no eligible child is intentionally quiet.
        return self.store.search(status="awaiting_reasoning")

    def context_for(self, logical_consultation_id: str) -> dict[str, Any]:
        return build_durable_context_package(self.store, logical_consultation_id)

    def wake_once(self) -> WorkerResult:
        from estate.core.autonomous_chatgpt_mailbox_worker import WorkerResult
        candidates = self.eligible()
        if not candidates:
            result = WorkerResult("EMPTY_QUEUE", reason="no_eligible_reasoning_work")
            self.state_writer({"state": "CHATGPT_REASONER_IDLE", "result": result.status})
            return result
        consultation = candidates[0]
        context = self.context_for(consultation.logical_consultation_id)
        self.state_writer({
            "state": "CHATGPT_REASONER_WAKE_PENDING",
            "logical_consultation_id": consultation.logical_consultation_id,
            "root_consultation_id": consultation.root_logical_id,
            "context_digest": context_digest(context),
        })
        self.state_writer({"state": "CHATGPT_REASONER_PROCESSING", "logical_consultation_id": consultation.logical_consultation_id})
        result = self.worker.run_once()
        if result.status in {"EXECUTION_REQUESTED"}:
            state = "CHATGPT_REASONER_WAITING_FOR_EXECUTION"
        elif result.status in {"EVIDENCE_ACQUISITION_REQUESTED"}:
            state = "CHATGPT_REASONER_WAITING_FOR_EVIDENCE"
        elif result.status in {"STEWARD_DECISION_REQUIRED", "EVIDENCE_ACQUISITION_LIMIT_REACHED"}:
            state = "CHATGPT_REASONER_ESCALATED"
        elif result.status in {"EMPTY_QUEUE", "WORKER_COMPLETE"}:
            state = "CHATGPT_REASONER_IDLE"
        elif result.status == "ERROR":
            state = "CHATGPT_REASONER_ERROR"
        else:
            state = "CHATGPT_REASONER_PROCESSING"
        self.state_writer({"state": state, "logical_consultation_id": result.logical_consultation_id, "result": result.status, "reason": result.reason})
        return result


def reasoning_wakeup_candidate(store: ConsultationStore, logical_consultation_id: str) -> dict[str, Any]:
    """State projection consumed by Grace/CME; it has no side effects."""
    record = store.get(logical_consultation_id)
    eligible = record.status == "awaiting_reasoning" and bool(record.ec8_request_id)
    return {
        "action_id": f"chatgpt-reasoning-wakeup:{record.logical_consultation_id}",
        "idempotency_key": f"chatgpt-reasoning-wakeup:{record.logical_consultation_id}",
        "permission": "delegated" if eligible else "recommendation",
        "canonical_mechanism": "ChatGPTReasoningResident.wake_once",
        "source_refs": [record.logical_consultation_id, record.ec8_request_id] if record.ec8_request_id else [record.logical_consultation_id],
        "eligible": eligible,
        "authority_refs": ["existing Grace consultation delegation"],
    }
