"""Grace-side autonomous Comms8 consultation delegation.

This is deliberately a narrow boundary: explicit natural-language
delegation only.  Comms8 owns transport/lifecycle, ConsultationStore owns
logical lineage, and the existing mailbox worker owns ChatGPT processing.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable

from estate.core.consultation_store import ConsultationRecord, ConsultationStore
from estate.core.consultation_escalation import instrument_escalation
from estate.core.chatgpt_reasoning_resident import build_durable_context_package
from estate.core.autonomous_reason_execute_loop import parse_reasoning_envelope
from estate.core.grace_parallel_portfolio import claim_activation, release_activation


LIVE_MCP_URL = "https://estate-comms8-live.ionoge.com/mcp"
LIVE_SECRET_PATH = Path(r"A:\theestate-data\live\comms8\secrets.env")
WORKER_MODULE = "estate.core.autonomous_chatgpt_mailbox_worker"
WORKER_PYTHON = Path(r"A:\AI\OpenWebUI\.venv\Scripts\python.exe")
WORKER_CWD = Path(r"A:\AI\OpenWebUI")
WORKER_DATA_DIR = Path(r"A:\AI\OpenWebUI\EstateCanonicalData")


def is_explicit_delegation_request(text: str) -> bool:
    """Recognize only the bounded, explicit delegation intent for this increment."""
    lowered = " ".join(str(text or "").lower().split())
    phrases = (
        "ask chatgpt",
        "get chatgpt's opinion",
        "get chatgpt’s opinion",
        "get a second opinion",
        "second opinion on this",
        "another perspective",
        "independent reasoning review",
        "independent second opinion",
        "ask for higher-level reasoning",
        "ask for higher level reasoning",
        "have chatgpt review this",
        "consult chatgpt",
    )
    return any(phrase in lowered for phrase in phrases)


def external_reasoning_claim_present(text: str) -> bool:
    """Return whether prose claims an external review actually happened."""
    lowered = " ".join(str(text or "").lower().split())
    phrases = (
        "i consulted",
        "i obtained a second opinion",
        "i initiated an external review",
        "engineering concluded",
        "chatgpt determined",
        "the external review identified",
        "higher-level reasoning found",
        "an external review found",
        "the second opinion identified",
    )
    return any(phrase in lowered for phrase in phrases)


def external_reasoning_provenance(result: dict[str, Any], request_text: str) -> dict[str, Any]:
    """Build bounded, request-correlated provenance from a loop result."""
    digest = hashlib.sha256(request_text.strip().encode("utf-8")).hexdigest()
    response = result.get("response")
    authoritative = bool(result.get("authoritative")) and bool(result.get("response_id"))
    return {
        "external_reasoning_performed": authoritative,
        "attempted": True,
        "request_fingerprint": digest,
        "consultation_root": result.get("root_logical_id") if authoritative else None,
        "consultation_turn": result.get("logical_consultation_id") if authoritative else None,
        "consultation_status": result.get("status"),
        "comms8_request_id": result.get("ec8_request_id"),
        "provider": result.get("worker") if authoritative else None,
        "response_id": result.get("response_id") if authoritative else None,
        "completion_status": "authoritative_response" if authoritative else "unavailable",
        "contribution": str(response or "")[:1200] if authoritative else None,
    }


def is_continuation_request(text: str) -> bool:
    lowered = " ".join(str(text or "").lower().split())
    return any(token in lowered for token in (
        "assume we tried", "new evidence", "what changes", "continue the consultation",
        "the recommendation failed", "the prior recommendation", "after restart",
    ))


def _text_result(value: Any) -> Any:
    if isinstance(value, list) and value and isinstance(value[0], dict) and "text" in value[0]:
        try:
            return json.loads(value[0]["text"])
        except (TypeError, json.JSONDecodeError):
            return value[0]["text"]
    return value


def _normalize_reasoning_response(response: Any) -> Any:
    if not isinstance(response, dict):
        return response
    envelope = parse_reasoning_envelope(response)
    if envelope is None:
        return response
    return {
        "content": envelope["reasoning"],
        "structured_decision": envelope["decision"],
        "response_id": response.get("response_id"),
        "raw_envelope": response.get("content"),
    }


class GraceConsultationLoop:
    """Create/continue one consultation and synchronously read its result."""

    def __init__(
        self,
        store: ConsultationStore | None = None,
        *,
        create_request: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        read_request: Callable[[str], dict[str, Any]] | None = None,
        wake_worker: Callable[[], dict[str, Any]] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.store = store or ConsultationStore()
        self.create_request = create_request or self._create_live_request
        self.read_request = read_request or self._read_live_request
        self.wake_worker = wake_worker or self._wake_existing_worker
        self.sleep = sleep

    @staticmethod
    def _secret() -> str:
        for line in LIVE_SECRET_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith("ESTATE_COMMS8_LIVE_CLIENT_SECRET="):
                return line.split("=", 1)[1]
        raise RuntimeError("live_credential_unavailable")

    def _mcp_call(self, method: str, arguments: dict[str, Any]) -> dict[str, Any]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
        completed = subprocess.run(
            [str(WORKER_PYTHON), "-m", "estate.core.grace_live_mcp_cli"],
            input=json.dumps({"method": method, "arguments": arguments}),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            env=env,
        )
        if completed.returncode != 0:
            diagnostic = " ".join(completed.stderr.split())[:240]
            raise RuntimeError("live_mcp_call_failed:" + diagnostic)
        try:
            normalized = json.loads(completed.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError("invalid_mcp_result_shape") from exc
        if not isinstance(normalized, dict):
            raise RuntimeError("invalid_mcp_result_shape")
        return normalized

    def _create_live_request(self, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._mcp_call("estate_comms8_create_reasoning_request", arguments)

    def _read_live_request(self, request_id: str) -> dict[str, Any]:
        return self._mcp_call("estate_comms8_read_request", {"request_id": request_id})

    def _wake_existing_worker(self) -> dict[str, Any]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
        env["DATA_DIR"] = str(WORKER_DATA_DIR)
        completed = subprocess.run(
            [str(WORKER_PYTHON), "-m", WORKER_MODULE, "--once"],
            capture_output=True,
            text=True,
            timeout=330,
            check=False,
            env=env,
            cwd=str(WORKER_CWD),
        )
        if completed.returncode != 0:
            diagnostic = " ".join(completed.stderr.split())[:240]
            return {"status": "ERROR", "reason": diagnostic or f"worker_exit_{completed.returncode}"}
        try:
            return json.loads(completed.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            return {"status": "ERROR", "reason": "worker_result_unavailable"}

    def _latest_candidate(self) -> ConsultationRecord | None:
        candidates: list[ConsultationRecord] = []
        for status in ("validating", "response_received", "resolved", "continuation_required", "steward_decision_required"):
            candidates.extend(self.store.search(status=status))
        return max(candidates, key=lambda item: item.updated_at, default=None)

    @staticmethod
    def _workflow_id(logical_id: str) -> str:
        return f"estate-grace-consultation-{logical_id.replace('.', '-') }"

    @staticmethod
    def _idempotency_key(logical_id: str, objective: str, attempt_number: int = 1) -> str:
        digest = hashlib.sha256(objective.encode("utf-8")).hexdigest()[:16]
        return f"{logical_id}-chatgpt-{digest}-transport-{attempt_number}"

    def _allocate(self, text: str, *, parent: ConsultationRecord | None, session_id: str | None,
                  ptm_project_id: str | None, ptm_work_item_id: str | None,
                  tags: tuple[str, ...], second_opinion_context: dict[str, Any] | None = None) -> ConsultationRecord:
        second_opinion_context = second_opinion_context or {}
        proposition = str(second_opinion_context.get("proposition") or text).strip()
        context = {
            "origin": "grace",
            "session_id": session_id,
            "question": proposition,
            "parent_turn": parent.logical_consultation_id if parent else None,
        }
        if second_opinion_context:
            context["second_opinion"] = second_opinion_context
        kwargs = dict(
            status="awaiting_reasoning",
            subject="Grace autonomous reasoning consultation",
            objective=proposition,
            question=proposition,
            current_evidence=context,
            prior_context_summary=(second_opinion_context.get("bounded_context") or
                                   ((parent.response or {}).get("content", "") if parent and isinstance(parent.response, dict) else ""))[:1200],
            continuation_reason="new evidence for unresolved objective" if parent else None,
            actor="grace",
            worker="chatgpt",
            ptm_project_id=ptm_project_id,
            ptm_work_item_id=ptm_work_item_id,
            tags=tags,
            workflow_id=None,
        )
        if parent:
            return self.store.allocate_continuation(parent.logical_consultation_id, **kwargs)
        return self.store.allocate_root(**kwargs)

    def _create_and_attach(self, consultation: ConsultationRecord, *, attempt_number: int = 1,
                           supersedes_request_id: str | None = None) -> ConsultationRecord:
        arguments = {
            "workflow_id": self._workflow_id(consultation.logical_consultation_id),
            "objective": consultation.objective or consultation.question or "",
            "input_data": {
                "consultation_id": consultation.logical_consultation_id,
                "root_consultation_id": consultation.root_logical_id,
                "parent_turn": consultation.parent_logical_id,
                "prior_context_summary": consultation.prior_context_summary,
                "current_evidence": consultation.current_evidence,
                "ptm_project_id": consultation.ptm_project_id,
                "ptm_work_item_id": consultation.ptm_work_item_id,
                "tags": list(consultation.tags),
                "question": consultation.question,
                "durable_context": build_durable_context_package(self.store, consultation.logical_consultation_id),
            },
            "idempotency_key": self._idempotency_key(consultation.logical_consultation_id, consultation.objective or "", attempt_number),
        }
        created = self.create_request(arguments)
        request_id = str(created.get("request_id") or "")
        if not request_id.startswith("ec8-") or created.get("state") != "queued":
            raise RuntimeError("comms8_create_not_queued")
        attached = self.store.attach_ec8(consultation.logical_consultation_id, request_id, arguments["workflow_id"])
        existing_attempts = self.store.transport_attempts(consultation.logical_consultation_id)
        if any(item.attempt_number == attempt_number for item in existing_attempts):
            self.store.mark_transport_attempt(consultation.logical_consultation_id, attempt_number, status="queued", request_id=request_id, worker_id="chatgpt")
        else:
            self.store.record_transport_attempt(
                consultation.logical_consultation_id,
                request_id,
                workflow_id=arguments["workflow_id"],
                status="queued",
                supersedes_request_id=supersedes_request_id,
                worker_id="chatgpt",
            )
        return attached

    def create_execution_format_repair_continuation(self, logical_consultation_id: str, reason: str) -> dict[str, Any]:
        """Queue one CME-owned reasoning turn to repair an invalid execution schema."""
        current = self.store.get(logical_consultation_id)
        existing = [item for item in self.store.latest_turns(current.root_logical_id, 10)
                    if item.parent_logical_id == logical_consultation_id
                    and item.continuation_reason == "execution_recommendation_format_repair"]
        if existing:
            item = existing[-1]
            return {"logical_consultation_id": item.logical_consultation_id, "request_id": item.ec8_request_id, "idempotent": True}
        continuation = self.store.allocate_continuation(
            logical_consultation_id,
            status="awaiting_reasoning",
            subject=current.subject,
            objective=current.objective,
            question=("Complete the EXECUTION_RECOMMENDED specification for the same bounded recommendation. "
                       "Return the canonical execution object with objective, required_capability, "
                       "allowed_scope, prohibited_scope, evidence_requirements, validation_criteria, "
                       "consultation_correlation, and write_scope when repair/write is required. "
                       "Scope fields must contain path strings only. Do not change the recommendation or execute it."),
            current_evidence={"format_repair": True, "invalid_reason": reason, "source_turn": logical_consultation_id},
            prior_context_summary=current.compact_summary,
            continuation_reason="execution_recommendation_format_repair",
            actor="CME",
            worker="chatgpt",
            workflow_id=None,
            tags=current.tags,
        )
        attached = self._create_and_attach(continuation)
        self.store.set_status(attached.logical_consultation_id, "awaiting_reasoning")
        return {"logical_consultation_id": attached.logical_consultation_id, "request_id": attached.ec8_request_id, "idempotent": False}

    def create_proposition_context_continuation(
        self, logical_consultation_id: str, *, proposition: str,
        current_recommendation: str | None = None,
        constraints: list[str] | None = None,
        requested_analysis: list[str] | None = None,
        bounded_context: str | None = None,
        source_interaction: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Repair missing second-opinion context without rewriting history."""
        current = self.store.get(logical_consultation_id)
        existing = [item for item in self.store.latest_turns(current.root_logical_id, 20)
                    if item.parent_logical_id == logical_consultation_id
                    and item.continuation_reason == "missing_persisted_proposition"]
        if existing:
            item = existing[-1]
            return {"logical_consultation_id": item.logical_consultation_id,
                    "request_id": item.ec8_request_id, "idempotent": True}
        if not str(proposition or "").strip():
            raise ValueError("proposition_required")
        second_opinion = {
            "purpose": "independent_second_opinion",
            "proposition": str(proposition).strip(),
            "current_recommendation": str(current_recommendation or "").strip() or None,
            "constraints": list(constraints or []),
            "requested_analysis": list(requested_analysis or [
                "evaluate the recommendation independently",
                "identify agreement, disagreement, missed risks, and new insight",
            ]),
            "bounded_context": str(bounded_context or "")[:3600],
            "source_interaction": source_interaction or {},
        }
        continuation = self.store.allocate_continuation(
            logical_consultation_id,
            status="awaiting_reasoning",
            subject=current.subject,
            objective=second_opinion["proposition"],
            question=("Provide an independent second opinion on the proposition below. "
                      "Evaluate Grace's recommendation, identify agreement or disagreement, "
                      "missed risks, and new insight. Do not assume execution is requested.\n\n" +
                      json.dumps(second_opinion, ensure_ascii=True, sort_keys=True)),
            current_evidence={"origin": "grace", "second_opinion": second_opinion,
                              "source_turn": logical_consultation_id},
            prior_context_summary=(current.response or {}).get("content", "")[:1200]
            if isinstance(current.response, dict) else None,
            continuation_reason="missing_persisted_proposition",
            actor="grace",
            worker="chatgpt",
            workflow_id=None,
            tags=current.tags,
        )
        attached = self._create_and_attach(continuation)
        self.store.set_status(attached.logical_consultation_id, "awaiting_reasoning")
        return {"logical_consultation_id": attached.logical_consultation_id,
                "request_id": attached.ec8_request_id, "idempotent": False}

    def recover_transport(self, logical_consultation_id: str) -> dict[str, Any]:
        """Retry one terminal transport failure without allocating a turn."""
        consultation = self.store.get(logical_consultation_id)
        if not consultation.ec8_request_id:
            raise RuntimeError("consultation_missing_transport_attempt")
        current = self.read_request(consultation.ec8_request_id)
        if current.get("response") or current.get("resolution"):
            raise RuntimeError("transport_retry_terminal_result_exists")
        if current.get("state") != "expired":
            raise RuntimeError("transport_retry_not_eligible:" + str(current.get("state")))
        attempts = self.store.transport_attempts(logical_consultation_id)
        if not attempts:
            self.store.record_transport_attempt(
                logical_consultation_id,
                consultation.ec8_request_id,
                workflow_id=consultation.workflow_id,
                status="expired",
                failure_class="wrong_worker_lease_expired",
                worker_id=(current.get("claim") or {}).get("worker_id"),
            )
        elif attempts[-1].request_id == consultation.ec8_request_id and attempts[-1].status != "expired":
            self.store.mark_transport_attempt(logical_consultation_id, attempts[-1].attempt_number, status="expired", failure_class="wrong_worker_lease_expired")
        reservation = self.store.reserve_transport_retry(
            logical_consultation_id,
            consultation.ec8_request_id,
            failure_class="wrong_worker_lease_expired",
        )
        if reservation.status == "creating":
            try:
                consultation = self._create_and_attach(
                    consultation,
                    attempt_number=reservation.attempt_number,
                    supersedes_request_id=consultation.ec8_request_id,
                )
            except Exception:
                self.store.mark_transport_attempt(logical_consultation_id, reservation.attempt_number, status="failed", failure_class="replacement_create_failed")
                raise
        replacement_id = self.store.get(logical_consultation_id).ec8_request_id
        worker_result = self.wake_worker()
        if worker_result.get("status") == "STEWARD_DECISION_REQUIRED":
            package = instrument_escalation(self.store, consultation.logical_consultation_id)
            return {
                "logical_consultation_id": consultation.logical_consultation_id,
                "root_logical_id": consultation.root_logical_id,
                "status": "steward_decision_required",
                "escalation": package,
                "authoritative": True,
                "message": "ChatGPT has exhausted the permitted autonomous evidence budget and still cannot reach a defensible conclusion. Here is what we know, what remains unknown, and the decision/evidence I need from you.",
            }
        if worker_result.get("status") == "ERROR":
            raise RuntimeError("chatgpt_worker_failed:" + str(worker_result.get("reason") or "unknown"))
        if worker_result.get("status") == "CONTEXT_REQUIRED":
            raise RuntimeError("context_required")
        resolved = self._await_result(replacement_id or "")
        response = resolved["response"]
        stored_response = _normalize_reasoning_response(response)
        self.store.append_response(logical_consultation_id, stored_response, response_id=response.get("response_id") if isinstance(response, dict) else None, recommendation=stored_response.get("content") if isinstance(stored_response, dict) else None)
        self.store.set_status(logical_consultation_id, "validating")
        self.store.mark_transport_attempt(logical_consultation_id, reservation.attempt_number, status="resolved", worker_id="chatgpt")
        return {"logical_consultation_id": logical_consultation_id, "transport_attempt": reservation.attempt_number, "ec8_request_id": replacement_id, "status": "validating", "response": response, "authoritative": True}

    def _await_result(self, request_id: str, timeout_seconds: float = 330.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            record = self.read_request(request_id)
            if record.get("state") == "resolved" and record.get("response"):
                return record
            self.sleep(2.0)
        raise TimeoutError("comms8_response_timeout")

    def delegate(self, text: str, *, session_id: str | None = None,
                 parent_logical_id: str | None = None,
                 ptm_project_id: str | None = None,
                 ptm_work_item_id: str | None = None,
                 tags: tuple[str, ...] = (),
                 second_opinion_context: dict[str, Any] | None = None) -> dict[str, Any]:
        parent = self.store.get(parent_logical_id) if parent_logical_id else None
        if parent is None and is_continuation_request(text):
            parent = self._latest_candidate()
        existing = [item for status in ("open", "awaiting_reasoning", "claimed", "reasoning", "response_received", "validating")
                    for item in self.store.search(status=status)
                    if item.objective == text.strip() and (parent is None or item.parent_logical_id == parent.logical_consultation_id)]
        consultation = max(existing, key=lambda item: item.updated_at, default=None)
        if consultation is None:
            consultation = self._allocate(text, parent=parent, session_id=session_id,
                                          ptm_project_id=ptm_project_id, ptm_work_item_id=ptm_work_item_id,
                                          tags=tags, second_opinion_context=second_opinion_context)
        if not consultation.ec8_request_id:
            try:
                consultation = self._create_and_attach(consultation)
            except Exception as exc:
                self.store.set_status(consultation.logical_consultation_id, "open")
                raise RuntimeError(f"comms8_create_failed:{type(exc).__name__}") from exc

        # The existing browser worker is a real physical reasoning resource.
        # Reserve it through the durable multi-lane projection before waking
        # the worker, so concurrent ordinary Grace requests produce an
        # explainable capacity hold instead of racing two browser activations.
        capacity_value = os.environ.get("ESTATE_REASONING_CAPACITY", "1")
        try:
            reasoning_capacity = int(capacity_value)
        except (TypeError, ValueError):
            reasoning_capacity = None
        reservation = claim_activation(
            self.store,
            root_logical_id=consultation.root_logical_id,
            continuation_logical_id=consultation.logical_consultation_id,
            worker_class="reasoning",
            provider_key="chatgpt-browser",
            idempotency_key=f"{consultation.root_logical_id}:{consultation.logical_consultation_id}:reasoning",
            capacity=reasoning_capacity,
            controller_pid=os.getpid(),
        )
        if reservation.get("status") != "RESERVED":
            return {
                "logical_consultation_id": consultation.logical_consultation_id,
                "root_logical_id": consultation.root_logical_id,
                "ec8_request_id": consultation.ec8_request_id,
                "workflow_id": consultation.workflow_id,
                "status": "HELD_CAPACITY",
                "reason": reservation.get("reason") or "reasoning capacity is already reserved",
                "authoritative": True,
                "message": "This independent Grace lane is waiting for reasoning capacity; unrelated lanes remain eligible.",
            }

        # The worker owns claim/ack/respond/resolve.  Grace only wakes it and
        # verifies the authoritative result; it never supplies the request ID.
        worker_result = self.wake_worker()
        if worker_result.get("status") == "ERROR":
            release_activation(self.store, reservation["activation_id"], reason="reasoning_worker_failed")
            raise RuntimeError("chatgpt_worker_failed:" + str(worker_result.get("reason") or "unknown"))
        if worker_result.get("status") == "CONTEXT_REQUIRED":
            release_activation(self.store, reservation["activation_id"], reason="reasoning_context_required")
            self.store.set_status(consultation.logical_consultation_id, "continuation_required")
            raise RuntimeError("context_required")
        resolved = self._await_result(consultation.ec8_request_id or "")
        response = resolved["response"]
        stored_response = _normalize_reasoning_response(response)
        self.store.append_response(
            consultation.logical_consultation_id,
            stored_response,
            response_id=response.get("response_id") if isinstance(response, dict) else None,
            recommendation=stored_response.get("content") if isinstance(stored_response, dict) else None,
        )
        self.store.set_status(consultation.logical_consultation_id, "validating")
        release_activation(self.store, reservation["activation_id"], reason="reasoning_response_received")
        content = response.get("content") if isinstance(response, dict) else str(response)
        return {
            "logical_consultation_id": consultation.logical_consultation_id,
            "root_logical_id": consultation.root_logical_id,
            "ec8_request_id": consultation.ec8_request_id,
            "workflow_id": consultation.workflow_id,
            "status": "validating",
            "response": content,
            "response_id": response.get("response_id") if isinstance(response, dict) else None,
            "worker": "chatgpt",
            "authoritative": True,
            "message": "I asked ChatGPT for a second-pass analysis and received the authoritative result. It is ready for validation.",
        }

    def escalation(self, logical_consultation_id: str) -> dict[str, Any]:
        """Return the durable Steward package without creating transport work."""
        package = instrument_escalation(self.store, logical_consultation_id)
        return {
            "logical_consultation_id": logical_consultation_id,
            "root_logical_id": package["root_consultation_id"],
            "status": "steward_decision_required",
            "escalation": package,
            "authoritative": True,
            "message": "ChatGPT has exhausted the permitted autonomous evidence budget and still cannot reach a defensible conclusion. Here is what we know, what remains unknown, and the decision/evidence I need from you.",
        }
