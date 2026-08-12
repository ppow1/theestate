"""Canonical composition root for ChatGPT structured execution handoff.

Provider-specific construction belongs here, at runtime composition.  The
consultation and reasoning layers continue to use the neutral router contract.
"""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
from typing import Any

from estate.core.autonomous_reason_execute_loop import AutonomousReasonExecuteLoop
from estate.core.codex_bridge import run_codex_bridge_request
from estate.core.codex_bridge_execution_provider_adapter import CodexBridgeExecutionProviderAdapter
from estate.core.consultation_execution import ConsultationExecutionRouter, ProviderBinding
from estate.core.consultation_store import ConsultationStore
from estate.core.grace_consultation_loop import GraceConsultationLoop
from estate.core.evidence_acquisition import EvidenceAcquisitionRuntime


DEFAULT_RUNTIME_ROOT = Path(r"A:\theestate")


def build_live_execution_router(store: ConsultationStore, *, runtime_root: str | Path = DEFAULT_RUNTIME_ROOT) -> ConsultationExecutionRouter:
    """Build the governed live router from the configured provider boundary."""
    root = Path(runtime_root)
    adapter = CodexBridgeExecutionProviderAdapter(
        root=root,
        bridge_runner=run_codex_bridge_request,
    )
    return ConsultationExecutionRouter(
        store,
        [ProviderBinding(adapter, frozenset({"software_engineering_test", "repository_read", "software_engineering_readonly"}))],
        runtime_root=root,
    )


def build_live_decision_handler(store: ConsultationStore, *, runtime_root: str | Path = DEFAULT_RUNTIME_ROOT):
    """Return the canonical structured-decision handoff callable."""
    router = build_live_execution_router(store, runtime_root=runtime_root)
    loop = AutonomousReasonExecuteLoop(store, router)
    evidence_runtime = EvidenceAcquisitionRuntime(store, router, runtime_root=runtime_root)

    def handle(logical_consultation_id: str, response: dict[str, Any]) -> dict[str, Any]:
        from estate.core.autonomous_reason_execute_loop import classify_reasoning_response
        decision = classify_reasoning_response(response)
        if decision.classification == "MORE_REASONING_REQUIRED" and decision.evidence_request:
            return evidence_runtime.acquire(logical_consultation_id, response)
        accepted = loop.accept_reasoning(logical_consultation_id, response)
        if accepted.get("status") != "execution_requested":
            return accepted
        execution_id = accepted["execution_request_id"]
        result = router.execute(execution_id)
        execution_evidence = {
            "execution_request_id": execution_id,
            "execution_status": result.status,
            "provider_id": result.provider_id,
            "summary": result.summary,
            "artifacts": result.artifacts,
            "validation_status": result.validation_status,
        }
        store.append_validation(
            logical_consultation_id,
            observed_result="VALIDATED" if result.status in {"completed", "dry_run_completed"} else "VALIDATION_FAILED",
            evidence=execution_evidence,
            status="validating" if result.status in {"completed", "dry_run_completed"} else "continuation_required",
        )
        continuation = None
        if result.status in {"completed", "dry_run_completed", "failed", "blocked"}:
            # Return execution evidence to the same consultation root through
            # the existing continuation contract.  CME owns the next worker
            # activation; this handler only persists the bounded handoff.
            current = store.get(logical_consultation_id)
            execution_links = store.latest_turns(current.root_logical_id, 20)
            continuation = next(
                (
                    turn for turn in execution_links
                    if turn.current_evidence
                    and turn.current_evidence.get("execution_request_id") == execution_id
                ),
                None,
            )
            if continuation is None:
                continuation_record = router.continue_from_execution(
                    logical_consultation_id,
                    execution_id,
                    question=(
                        "Evaluate the completed bounded execution evidence and state whether "
                        "the original assumption was validated or requires a revised recommendation."
                    ),
                    continuation_reason="execution_evidence_requires_reevaluation",
                )
                continuation = GraceConsultationLoop(store=store)._create_and_attach(continuation_record)
                store.set_status(continuation.logical_consultation_id, "awaiting_reasoning")
        return {
            **accepted,
            "execution_status": result.status,
            "provider_id": result.provider_id,
            "evidence": execution_evidence,
            "continuation_id": continuation.logical_consultation_id if continuation else None,
            "continuation_request_id": continuation.ec8_request_id if continuation else None,
        }

    return handle


def reevaluate_latest_execution(logical_consultation_id: str, *, store: ConsultationStore | None = None,
                                runtime_root: str | Path = DEFAULT_RUNTIME_ROOT) -> dict[str, Any]:
    """Create and process one automatic ChatGPT reevaluation turn.

    The execution request is selected from durable consultation state; no
    operator-supplied execution ID is needed.  The mailbox worker is invoked
    with its generic prompt through the canonical runtime wrapper.
    """
    store = store or ConsultationStore()
    links = store.execution_requests(logical_consultation_id)
    if not links:
        raise ValueError("consultation_execution_missing")
    link = links[-1]
    continuation = ConsultationExecutionRouter(store, [], runtime_root=runtime_root).continue_from_execution(
        logical_consultation_id,
        link.execution_request_id,
        question="Evaluate the completed bounded execution evidence and state whether the original assumption was validated or requires a revised recommendation.",
        continuation_reason="execution evidence requires ChatGPT reevaluation",
    )
    loop = GraceConsultationLoop(store=store)
    loop._create_and_attach(continuation)
    store.set_status(continuation.logical_consultation_id, "awaiting_reasoning")
    completed = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         r"A:\theestate\tools\start_chatgpt_mailbox_worker_canonical.ps1", "--once"],
        capture_output=True, text=True, timeout=360, check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("reevaluation_worker_failed:" + " ".join(completed.stderr.split())[:240])
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    readback = loop._await_result(continuation.ec8_request_id or "")
    return {
        "logical_consultation_id": continuation.logical_consultation_id,
        "ec8_request_id": continuation.ec8_request_id,
        "worker_result": result,
        "authoritative_state": readback.get("state"),
        "response_id": (readback.get("response") or {}).get("response_id"),
    }
