"""Bounded autonomous ChatGPT mailbox worker for Estate Comms8."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Callable

from estate.core.consultation_store import ConsultationRecord, ConsultationStore
from estate.core.autonomous_reason_execute_loop import classify_reasoning_response, parse_reasoning_envelope
from estate.core.chatgpt_worker_runtime import validate_worker_runtime
from estate.core.evidence_acquisition import acquisition_count, MAX_ACQUISITIONS
from estate.core.consultation_escalation import instrument_escalation
from estate.core.grace_parallel_portfolio import list_activations, mark_activation_active, release_activation


WORKER_ID = "chatgpt"
DEFAULT_STATE_PATH = Path(r"A:\theestate-data\chatgpt-mailbox-worker\worker-state.json")
DEFAULT_BROWSER_DIAGNOSTIC_PATH = Path(r"A:\theestate-data\chatgpt-mailbox-worker\browser-diagnostics.json")
DEFAULT_BROWSER_SCRIPT = Path(__file__).resolve().parents[3] / "tools" / "chatgpt_mailbox_worker_browser.cjs"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _lease_active(claim: dict[str, Any] | None) -> bool:
    if not claim or not claim.get("lease_expires_at"):
        return False
    try:
        expires = datetime.fromisoformat(str(claim["lease_expires_at"]).replace("Z", "+00:00"))
    except ValueError:
        return True
    return expires > datetime.now(timezone.utc)


def generic_worker_prompt() -> str:
    return (
        "Use Estate Comms8 Live. Claim the next eligible reasoning request. "
        "Use worker_id=chatgpt for every lifecycle operation. "
        "Process ONLY the returned request. Read it, acknowledge it, reason "
        "from its consultation envelope, respond, and resolve it using only "
        "authoritative Estate Comms8 tools. If no eligible request exists, "
        "return EMPTY_QUEUE. Do not create another request, do not process "
        "more than one request, do not use a supplied request ID, and do not "
        "retry after authoritative completion. If the supplied context is "
        "insufficient, return CONTEXT_REQUIRED rather than guessing. Return "
        "one complete JSON response object containing human-readable `reasoning` "
        "and a `decision` object classified as INFORMATION_ONLY, "
        "EXECUTION_RECOMMENDED, STEWARD_DECISION_REQUIRED, or MORE_REASONING_REQUIRED. "
        "For EXECUTION_RECOMMENDED, include only the bounded provider-neutral "
        "execution specification required by the Estate. It is invalid unless "
        "the `execution` object contains objective, required_capability, "
        "allowed_scope, prohibited_scope, evidence_requirements, "
        "validation_criteria, consultation_correlation, and write_scope for "
        "any repair/write/update action. Scope fields are path-only bounded "
        "lists; put action instructions in objective/evidence_requirements. Use a registered "
        "capability such as software_engineering_test, repository_read, or "
        "software_engineering_readonly; never provide a provider identity. "
        "Allowed and prohibited scopes must be explicit bounded lists, and "
        "validation_criteria must be deterministic. Never fabricate a "
        "provider identity or include secrets. For MORE_REASONING_REQUIRED, "
        "when specific missing evidence is needed, include an evidence_request "
        "object with objective, evidence_type or target when useful, "
        "required_capability, allowed_scope, prohibited_scope, "
        "evidence_requirements, and consultation_correlation. Do not encode "
        "a missing-evidence need only in prose. At the end return exactly "
        "WORKER_COMPLETE after successful resolution."
    )


def reserved_worker_prompt(logical_consultation_id: str, ec8_request_id: str) -> str:
    """Bind one CME reservation to the existing browser worker turn."""
    return (
        f"Use Estate Comms8 Live and process ONLY the CME-reserved consultation "
        f"logical_consultation_id={logical_consultation_id}, request_id={ec8_request_id}. "
        f"Call estate_comms8_claim_request with request_id={ec8_request_id}, worker_id=chatgpt, "
        "lease_seconds=900 exactly, then read, "
        "acknowledge, reason, respond, and resolve only that request with worker_id=chatgpt. "
        "Do not call claim_next, do not process any other request, and do not create another request. "
        "If context is insufficient, return CONTEXT_REQUIRED rather than guessing. Return one complete "
        "JSON response with reasoning and a decision classified as INFORMATION_ONLY, "
        "EXECUTION_RECOMMENDED, STEWARD_DECISION_REQUIRED, or MORE_REASONING_REQUIRED. "
        "For EXECUTION_RECOMMENDED include objective, required_capability, allowed_scope, "
        "prohibited_scope, evidence_requirements, validation_criteria, consultation_correlation, "
        "and write_scope. For MORE_REASONING_REQUIRED include an explicit evidence_request when needed. "
        "Return exactly WORKER_COMPLETE after successful resolution."
    )


@dataclass(frozen=True)
class WorkerResult:
    status: str
    logical_consultation_id: str | None = None
    ec8_request_id: str | None = None
    reason: str | None = None


class AutonomousChatGPTMailboxWorker:
    """Process at most one awaiting consultation per activation."""

    def __init__(self, store: ConsultationStore, *, state_path: str | Path = DEFAULT_STATE_PATH,
                 browser_script: str | Path = DEFAULT_BROWSER_SCRIPT,
                 browser_runner: Callable[[str | Path, str], dict[str, Any]] | None = None,
                 read_request: Callable[[str], dict[str, Any]] | None = None,
                 decision_handler: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
                 format_repair_handler: Callable[[str, str], dict[str, Any]] | None = None) -> None:
        self.store = store
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.browser_script = Path(browser_script)
        self.browser_runner = browser_runner or self._run_browser
        self.read_request = read_request or self._read_live_request
        self.decision_handler = decision_handler
        self.format_repair_handler = format_repair_handler

    def _write_state(self, state: str, **extra: Any) -> None:
        payload = {"worker_id": WORKER_ID, "state": state, "updated_at": _now(), **extra}
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.state_path)

    def bounded_local_context(self, root_id: int | str, *, latest: int = 5) -> dict[str, Any]:
        """Return bounded consultation context without consulting GitHub."""
        if latest < 1 or latest > 20:
            raise ValueError("latest must be between 1 and 20")
        summary = self.store.compact_summary(root_id)
        turns = self.store.latest_turns(root_id, latest)
        return {
            "root_consultation_id": summary["root_consultation_id"],
            "summary": summary["summary"],
            "turns": [
                {
                    "logical_consultation_id": turn.logical_consultation_id,
                    "question": turn.question,
                    "response": turn.response,
                    "observed_result": turn.observed_result,
                    "validation_evidence": turn.validation_evidence,
                    "status": turn.status,
                }
                for turn in turns
            ],
        }

    @staticmethod
    def _missing_reasoning_subject(consultation: ConsultationRecord, decision: Any) -> bool:
        """Keep absent proposition/context out of the evidence adapter path."""
        request = getattr(decision, "evidence_request", None)
        if not isinstance(request, dict) or request.get("allowed_scope"):
            return False
        evidence = consultation.current_evidence if isinstance(consultation.current_evidence, dict) else {}
        second_opinion = evidence.get("second_opinion")
        proposition = (second_opinion or {}).get("proposition") if isinstance(second_opinion, dict) else None
        question = str(consultation.question or "").lower()
        if proposition or (consultation.question and "second opinion on this" not in question):
            return False
        return str(request.get("evidence_type") or "").lower() in {"consultation_materials", "reasoning_context"}

    @staticmethod
    def _raw_missing_reasoning_subject(consultation: ConsultationRecord, normalized: dict[str, Any]) -> bool:
        evidence = consultation.current_evidence if isinstance(consultation.current_evidence, dict) else {}
        second_opinion = evidence.get("second_opinion")
        if isinstance(second_opinion, dict) and second_opinion.get("proposition"):
            return False
        question = str(consultation.question or "").lower()
        if "second opinion on this" not in question:
            return False
        decision = normalized.get("structured_decision") if isinstance(normalized, dict) else None
        request = decision.get("evidence_request") if isinstance(decision, dict) else None
        return isinstance(request, dict) and not request.get("allowed_scope") and str(request.get("evidence_type") or "").lower() in {"consultation_materials", "reasoning_context"}

    def _persist_reasoning_response(self, consultation: ConsultationRecord, record: dict[str, Any]) -> WorkerResult | None:
        response = record["response"]
        envelope = parse_reasoning_envelope(response)
        normalized = response
        if envelope is not None:
            normalized = {
                "content": envelope["reasoning"],
                "structured_decision": envelope["decision"],
                "response_id": response.get("response_id") if isinstance(response, dict) else None,
                "raw_envelope": response.get("content") if isinstance(response, dict) else None,
            }
        self.store.append_response(
            consultation.logical_consultation_id,
            normalized,
            response_id=(response or {}).get("response_id") if isinstance(response, dict) else None,
            recommendation=normalized.get("content") if isinstance(normalized, dict) else None,
        )
        if envelope is not None:
            try:
                decision = classify_reasoning_response(normalized)
            except ValueError as exc:
                if self._raw_missing_reasoning_subject(consultation, normalized):
                    self.store.set_status(consultation.logical_consultation_id, "continuation_required")
                    self._write_state("WAITING_FOR_RESPONSE", reason="missing_persisted_proposition", logical_consultation_id=consultation.logical_consultation_id)
                    return WorkerResult("CONTEXT_REQUIRED", consultation.logical_consultation_id, consultation.ec8_request_id, "missing_persisted_proposition")
                if str(exc).startswith("evidence_request_") and acquisition_count(self.store, consultation.logical_consultation_id) >= MAX_ACQUISITIONS:
                    package = instrument_escalation(self.store, consultation.logical_consultation_id)
                    self._write_state("STEWARD_DECISION_REQUIRED", reason="EVIDENCE_ACQUISITION_LIMIT_REACHED", logical_consultation_id=consultation.logical_consultation_id)
                    return WorkerResult("STEWARD_DECISION_REQUIRED", consultation.logical_consultation_id, consultation.ec8_request_id, package["decision_or_evidence_needed"])
                reason = "EXECUTION_DECISION_INVALID:" + str(exc)
                if "execution_spec_" in str(exc) and self.format_repair_handler is not None:
                    try:
                        repair = self.format_repair_handler(consultation.logical_consultation_id, reason)
                    except Exception as repair_exc:
                        self._write_state("ERROR", reason=reason + ":format_repair_failed:" + type(repair_exc).__name__, logical_consultation_id=consultation.logical_consultation_id)
                        return WorkerResult("EXECUTION_DECISION_INVALID", consultation.logical_consultation_id, consultation.ec8_request_id, reason)
                    self._write_state("WAITING_FOR_RESPONSE", reason="execution_recommendation_format_repair", logical_consultation_id=consultation.logical_consultation_id, continuation_id=repair.get("logical_consultation_id"))
                    return WorkerResult("FORMAT_REPAIR_REQUESTED", consultation.logical_consultation_id, consultation.ec8_request_id, repair.get("logical_consultation_id"))
                self._write_state("ERROR", reason=reason, logical_consultation_id=consultation.logical_consultation_id)
                return WorkerResult("EXECUTION_DECISION_INVALID", consultation.logical_consultation_id, consultation.ec8_request_id, str(exc))
            if decision.classification in {"EXECUTION_RECOMMENDED", "MORE_REASONING_REQUIRED"} and (decision.classification == "EXECUTION_RECOMMENDED" or decision.evidence_request):
                if self._missing_reasoning_subject(consultation, decision):
                    self.store.set_status(consultation.logical_consultation_id, "continuation_required")
                    self._write_state("WAITING_FOR_RESPONSE", reason="missing_persisted_proposition", logical_consultation_id=consultation.logical_consultation_id)
                    return WorkerResult("CONTEXT_REQUIRED", consultation.logical_consultation_id, consultation.ec8_request_id, "missing_persisted_proposition")
                if self.decision_handler is None:
                    reason = "execution_decision_handler_unavailable" if decision.classification == "EXECUTION_RECOMMENDED" else "evidence_acquisition_handler_unavailable"
                    self._write_state("ERROR", reason=reason, logical_consultation_id=consultation.logical_consultation_id)
                    return WorkerResult("DECISION_HANDLER_UNAVAILABLE", consultation.logical_consultation_id, consultation.ec8_request_id)
                try:
                    handoff = self.decision_handler(consultation.logical_consultation_id, normalized)
                except ValueError as exc:
                    if str(exc) == "EVIDENCE_ACQUISITION_LIMIT_REACHED":
                        package = instrument_escalation(self.store, consultation.logical_consultation_id)
                        self._write_state("STEWARD_DECISION_REQUIRED", reason=str(exc), logical_consultation_id=consultation.logical_consultation_id)
                        return WorkerResult("STEWARD_DECISION_REQUIRED", consultation.logical_consultation_id, consultation.ec8_request_id, package["decision_or_evidence_needed"])
                    self._write_state("ERROR", reason="EXECUTION_DECISION_INVALID:" + str(exc), logical_consultation_id=consultation.logical_consultation_id)
                    return WorkerResult("EXECUTION_DECISION_INVALID", consultation.logical_consultation_id, consultation.ec8_request_id, str(exc))
                if handoff.get("status") == "execution_requested":
                    self._write_state("WAITING_FOR_RESPONSE", reason="execution_requested", logical_consultation_id=consultation.logical_consultation_id, execution_request_id=handoff.get("execution_request_id"))
                    return WorkerResult("EXECUTION_REQUESTED", consultation.logical_consultation_id, consultation.ec8_request_id, handoff.get("execution_request_id"))
                if handoff.get("status", "").startswith("evidence_") or handoff.get("status") == "evidence_acquired_reevaluation_queued":
                    self._write_state("WAITING_FOR_RESPONSE", reason=handoff.get("status"), logical_consultation_id=consultation.logical_consultation_id, continuation_id=handoff.get("continuation_id"))
                    return WorkerResult("EVIDENCE_ACQUISITION_REQUESTED", consultation.logical_consultation_id, consultation.ec8_request_id, handoff.get("continuation_id"))
        self.store.set_status(consultation.logical_consultation_id, "resolved")
        return None

    def _run_browser(self, script: str | Path, prompt: str) -> dict[str, Any]:
        try:
            completed = subprocess.run(["node", str(script), prompt], capture_output=True, text=True, timeout=600, check=False)
        except subprocess.TimeoutExpired as exc:
            diagnostic = {"failure_class": "CHATGPT_GENERATION_EXCEEDED_TIMEOUT", "source": "python_browser_runner", "timeout_seconds": 600, "stdout_present": bool(exc.stdout), "stderr_present": bool(exc.stderr)}
            DEFAULT_BROWSER_DIAGNOSTIC_PATH.parent.mkdir(parents=True, exist_ok=True)
            DEFAULT_BROWSER_DIAGNOSTIC_PATH.write_text(json.dumps(diagnostic, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            raise RuntimeError("CHATGPT_GENERATION_EXCEEDED_TIMEOUT") from exc
        try:
            result = json.loads(completed.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as exc:
            if completed.returncode != 0:
                raise RuntimeError(f"chatgpt_browser_failed:{completed.returncode}") from exc
            raise RuntimeError("chatgpt_browser_invalid_result") from exc
        if not isinstance(result, dict):
            raise RuntimeError("chatgpt_browser_invalid_result")
        if result.get("trace") is not None:
            DEFAULT_BROWSER_DIAGNOSTIC_PATH.parent.mkdir(parents=True, exist_ok=True)
            DEFAULT_BROWSER_DIAGNOSTIC_PATH.write_text(json.dumps({
                "marker": result.get("marker"),
                "reason": result.get("reason"),
                "trace": result.get("trace"),
            }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if result.get("marker") == "BROWSER_COMPLETION_FAILED":
            diagnostic = {key: result.get(key) for key in ("marker", "reason", "trace") if result.get(key) is not None}
            DEFAULT_BROWSER_DIAGNOSTIC_PATH.parent.mkdir(parents=True, exist_ok=True)
            DEFAULT_BROWSER_DIAGNOSTIC_PATH.write_text(json.dumps(diagnostic, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if completed.returncode != 0 and result.get("marker") != "READINESS_FAILED":
            raise RuntimeError(f"chatgpt_browser_failed:{completed.returncode}")
        return result

    def _read_live_request(self, request_id: str) -> dict[str, Any]:
        import asyncio
        import sys
        sys.path.insert(0, r"A:\AI\OpenWebUI\.venv\Lib\site-packages")
        from open_webui.utils.mcp.client import MCPClient

        secret_path = Path(r"A:\theestate-data\live\comms8\secrets.env")
        secret = next(line.split("=", 1)[1] for line in secret_path.read_text().splitlines() if line.startswith("ESTATE_COMMS8_LIVE_CLIENT_SECRET="))

        async def read() -> dict[str, Any]:
            client = MCPClient()
            await client.connect("https://estate-comms8-live.ionoge.com/mcp", headers={"Authorization": "Bearer " + secret})
            result = await client.call_tool("estate_comms8_read_request", {"request_id": request_id})
            await client.disconnect()
            if isinstance(result, list) and result and isinstance(result[0], dict) and "text" in result[0]:
                result = json.loads(result[0]["text"])
            return result

        return asyncio.run(read())

    def run_once(self) -> WorkerResult:
        self._write_state("CHECKING_QUEUE")
        reserved_logical_id = os.environ.get("ESTATE_RESERVED_CONTINUATION_ID")
        candidates = self.store.search(status="awaiting_reasoning")
        if reserved_logical_id:
            candidates = [item for item in candidates if item.logical_consultation_id == reserved_logical_id]
        if not candidates:
            self._write_state("IDLE", result="EMPTY_QUEUE")
            return WorkerResult("EMPTY_QUEUE", reason="no_awaiting_reasoning_consultation")

        reservations = {
            item.continuation_logical_id: item
            for item in list_activations(self.store, states={"RESERVED", "LAUNCHING", "ACTIVE"})
        }
        reserved_candidates = [item for item in candidates if item.logical_consultation_id in reservations]
        # A direct legacy worker tick may have no portfolio reservation; keep
        # the historical fallback, while a reserved live lane is authoritative
        # and prevents the worker from claiming another root's request.
        consultation = (reserved_candidates or candidates)[0]
        if reserved_logical_id and consultation.logical_consultation_id != reserved_logical_id:
            self._write_state("ERROR", reason="reserved_lane_not_found", logical_consultation_id=reserved_logical_id)
            return WorkerResult("ERROR", reserved_logical_id, reason="reserved_lane_not_found")
        activation = reservations.get(consultation.logical_consultation_id)
        if activation and activation.state == "RESERVED":
            mark_activation_active(self.store, activation.activation_id, worker_pid=os.getpid())
        if not consultation.ec8_request_id:
            self._write_state("ERROR", reason="consultation_missing_ec8_request_id", logical_consultation_id=consultation.logical_consultation_id)
            return WorkerResult("ERROR", consultation.logical_consultation_id, reason="consultation_missing_ec8_request_id")

        self._write_state("PROCESSING", logical_consultation_id=consultation.logical_consultation_id)
        try:
            # Recovery guard: a browser/CDP process may submit the generic
            # instruction and complete Comms8 after this worker process has
            # timed out or lost its completion marker.  Reconcile that
            # authoritative result before ever activating ChatGPT again.
            current = self.read_request(consultation.ec8_request_id)
            claim = current.get("claim") or {}
            if claim.get("worker_id") and _lease_active(claim):
                reason = ("active_foreign_lease:" + str(claim.get("worker_id"))) if claim.get("worker_id") != WORKER_ID else "active_lease_in_progress"
                self._write_state("ERROR", reason=reason, logical_consultation_id=consultation.logical_consultation_id)
                return WorkerResult("ERROR", consultation.logical_consultation_id, consultation.ec8_request_id, reason)
            if current.get("state") == "resolved" and current.get("response"):
                handoff = self._persist_reasoning_response(consultation, current)
                if handoff is not None:
                    return handoff
                for attempt in self.store.transport_attempts(consultation.logical_consultation_id):
                    if attempt.request_id == consultation.ec8_request_id:
                        self.store.mark_transport_attempt(consultation.logical_consultation_id, attempt.attempt_number, status="resolved", worker_id="chatgpt")
                self._write_state("STOPPED", result="WORKER_COMPLETE", logical_consultation_id=consultation.logical_consultation_id, ec8_request_id=consultation.ec8_request_id, recovery=True)
                if activation:
                    release_activation(self.store, activation.activation_id, reason="worker_complete")
                return WorkerResult("WORKER_COMPLETE", consultation.logical_consultation_id, consultation.ec8_request_id)
            prompt = reserved_worker_prompt(consultation.logical_consultation_id, consultation.ec8_request_id) if reserved_logical_id else generic_worker_prompt()
            browser_result = self.browser_runner(self.browser_script, prompt)
            marker = browser_result.get("marker")
            if marker == "READINESS_FAILED":
                reason = str(browser_result.get("reason") or "chatgpt_readiness_failed")
                self._write_state("ERROR", reason=reason, logical_consultation_id=consultation.logical_consultation_id)
                return WorkerResult("ERROR", consultation.logical_consultation_id, consultation.ec8_request_id, reason)
            if marker == "EMPTY_QUEUE":
                self._write_state("ERROR", reason="chatgpt_empty_queue", logical_consultation_id=consultation.logical_consultation_id)
                return WorkerResult("ERROR", consultation.logical_consultation_id, consultation.ec8_request_id, "chatgpt_empty_queue")
            if marker == "CONTEXT_REQUIRED":
                self.store.set_status(consultation.logical_consultation_id, "continuation_required")
                self._write_state("WAITING_FOR_RESPONSE", reason="CONTEXT_REQUIRED", logical_consultation_id=consultation.logical_consultation_id)
                return WorkerResult("CONTEXT_REQUIRED", consultation.logical_consultation_id, consultation.ec8_request_id)
            if marker == "BROWSER_COMPLETION_FAILED":
                reason = str(browser_result.get("reason") or "CHATGPT_BROWSER_COMPLETION_FAILED")
                self._write_state("ERROR", reason=reason, diagnostic=browser_result.get("trace"), logical_consultation_id=consultation.logical_consultation_id)
                return WorkerResult("ERROR", consultation.logical_consultation_id, consultation.ec8_request_id, reason)
            if marker not in {"WORKER_COMPLETE", "ASSISTANT_RESPONSE_STABLE"}:
                self._write_state("ERROR", reason="chatgpt_completion_marker_missing", logical_consultation_id=consultation.logical_consultation_id)
                return WorkerResult("ERROR", consultation.logical_consultation_id, consultation.ec8_request_id, "chatgpt_completion_marker_missing")

            self._write_state("WAITING_FOR_RESPONSE", logical_consultation_id=consultation.logical_consultation_id)
            # Browser stability and Comms8 resolution are separate boundaries.
            # ChatGPT may still be completing a tool call after the UI surface
            # stops changing, so give the authoritative lifecycle a bounded
            # polling window before declaring completion unproven.
            record = self.read_request(consultation.ec8_request_id)
            deadline = time.monotonic() + 180
            while (
                record.get("state") not in {"resolved", "expired"}
                and time.monotonic() < deadline
            ):
                time.sleep(2)
                record = self.read_request(consultation.ec8_request_id)
            if record.get("state") != "resolved" or not record.get("response"):
                self._write_state("ERROR", reason="authoritative_comms8_completion_not_proven", logical_consultation_id=consultation.logical_consultation_id)
                return WorkerResult("ERROR", consultation.logical_consultation_id, consultation.ec8_request_id, "authoritative_comms8_completion_not_proven")
            handoff = self._persist_reasoning_response(consultation, record)
            if handoff is not None:
                return handoff
            for attempt in self.store.transport_attempts(consultation.logical_consultation_id):
                if attempt.request_id == consultation.ec8_request_id:
                    self.store.mark_transport_attempt(consultation.logical_consultation_id, attempt.attempt_number, status="resolved", worker_id="chatgpt")
            self._write_state("STOPPED", result="WORKER_COMPLETE", logical_consultation_id=consultation.logical_consultation_id, ec8_request_id=consultation.ec8_request_id)
            if activation:
                release_activation(self.store, activation.activation_id, reason="worker_complete")
            return WorkerResult("WORKER_COMPLETE", consultation.logical_consultation_id, consultation.ec8_request_id)
        except Exception as exc:
            self._write_state("ERROR", reason=type(exc).__name__ + ":" + str(exc), logical_consultation_id=consultation.logical_consultation_id)
            return WorkerResult("ERROR", consultation.logical_consultation_id, consultation.ec8_request_id, str(exc))
        finally:
            # A physical worker owns the activation only for the duration of
            # this bounded turn.  Handoffs, validation errors, and failures
            # must all release the reservation so unrelated lanes can move.
            if activation:
                release_activation(self.store, activation.activation_id, reason="worker_exit")

    def watch(self, *, interval_seconds: float = 2.0, max_seconds: float = 300.0) -> WorkerResult:
        """Boundedly activate on consultation-store changes.

        SQLite has no Estate-wide notification bus yet, so this uses bounded
        mtime polling rather than an unbounded browser or Comms8 polling loop.
        """
        deadline = time.monotonic() + max_seconds
        observed_mtime = self.store.path.stat().st_mtime_ns if self.store.path.exists() else 0
        while time.monotonic() < deadline:
            current_mtime = self.store.path.stat().st_mtime_ns if self.store.path.exists() else 0
            if current_mtime != observed_mtime or self.store.search(status="awaiting_reasoning"):
                observed_mtime = current_mtime
                result = self.run_once()
                if result.status != "EMPTY_QUEUE":
                    return result
            time.sleep(max(0.1, interval_seconds))
        self._write_state("STOPPED", result="WATCH_TIMEOUT")
        return WorkerResult("WATCH_TIMEOUT", reason="bounded_activation_timeout")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Estate Comms8 autonomous ChatGPT mailbox worker")
    parser.add_argument("--once", action="store_true", help="perform one bounded activation")
    parser.add_argument("--watch", action="store_true", help="boundedly watch for awaiting consultations")
    parser.add_argument("--interval-seconds", type=float, default=2.0)
    parser.add_argument("--max-seconds", type=float, default=300.0)
    args = parser.parse_args()
    if not args.once and not args.watch:
        parser.error("choose --once or --watch")
    runtime = validate_worker_runtime(require_cdp=False)
    if not runtime["ok"]:
        print(json.dumps({"status": "ERROR", "reason": "runtime_preflight_failed:" + ",".join(runtime["errors"]), "runtime": runtime["checks"]}, sort_keys=True))
        raise SystemExit(1)
    store = ConsultationStore()
    decision_handler = None
    format_repair_handler = None
    if os.getenv("ESTATE_STRUCTURED_EXECUTION_HANDOFF", "1") == "1":
        from estate.core.chatgpt_execution_runtime import build_live_decision_handler
        from estate.core.grace_consultation_loop import GraceConsultationLoop
        decision_handler = build_live_decision_handler(store)
        format_repair_handler = lambda logical_id, reason: GraceConsultationLoop(store=store).create_execution_format_repair_continuation(logical_id, reason)
    worker = AutonomousChatGPTMailboxWorker(store, decision_handler=decision_handler, format_repair_handler=format_repair_handler)
    result = worker.run_once() if args.once else worker.watch(interval_seconds=args.interval_seconds, max_seconds=args.max_seconds)
    print(json.dumps(result.__dict__, sort_keys=True))
