"""Detached live Grace reason/execute/observe/reason acceptance.

The first interaction is an ordinary-language HTTP request to Grace.  All
consultation, execution, provider, and reevaluation records are discovered
from the durable stores; this driver only advances the existing CME owner.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
import sys
import urllib.request
from uuid import uuid4

ROOT = Path(r"A:\theestate")
DATA = Path(r"A:\theestate-data")
GATEWAY = "http://127.0.0.1:11435/v1/chat/completions"
DB = DATA / "consultations" / "consultations.db"
STATE = DATA / "chatgpt-mailbox-worker" / "cme-owner-state.json"
LOCK = DATA / "chatgpt-mailbox-worker" / "cme-owner.lock"
FIXTURE = ROOT / "Temp" / "cme-execution-fixtures" / "full-loop-20260807" / "fixture.json"

sys.path.insert(0, str(ROOT / "src"))

from estate.core.autonomous_reason_execute_loop import classify_reasoning_response  # noqa: E402
from estate.core.consultation_store import ConsultationStore  # noqa: E402
from estate.core.continuous_momentum_engine import ChatGPTReasoningCMEOwner  # noqa: E402
from estate.core.grace_consultation_loop import GraceConsultationLoop  # noqa: E402


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def gateway(payload: dict) -> dict:
    request = urllib.request.Request(
        GATEWAY,
        json.dumps(payload).encode("utf-8"),
        {"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=720) as response:
        return json.loads(response.read())


def content(body: dict) -> str:
    choice = (body.get("choices") or [{}])[0]
    message = choice.get("message") or choice.get("delta") or {}
    return str(message.get("content") or "")


def records_for_session(store: ConsultationStore, session_id: str):
    return [
        item for item in store.search()
        if getattr(item, "session_id", None) == session_id
        or (item.current_evidence or {}).get("session_id") == session_id
    ]


def settle_root(store: ConsultationStore, loop: GraceConsultationLoop, root_id: str, evidence: Path) -> dict:
    """Advance only eligible same-root turns through the existing CME owner."""
    owner = ChatGPTReasoningCMEOwner(store, state_path=STATE, lock_path=LOCK, read_request=loop.read_request)
    activations = []
    for _ in range(12):
        turns = store.latest_turns(root_id, 20)
        current = turns[-1]
        authoritative = loop.read_request(current.ec8_request_id) if current.ec8_request_id else {}
        if current.status not in {"awaiting_reasoning", "open", "claimed", "reasoning"}:
            if authoritative.get("state") == "resolved" and authoritative.get("response"):
                # A completed turn may have an automatically queued same-root
                # continuation; the next loop iteration will select it.
                pending = [turn for turn in turns if turn.status == "awaiting_reasoning"]
                if not pending:
                    break
        started = owner.tick()
        activations.append({"started": started, "state": json.loads(STATE.read_text()) if STATE.exists() else None})
        if started.get("status") == "STARTED":
            deadline = time.monotonic() + 720
            while time.monotonic() < deadline:
                result = owner.reconcile()
                activations[-1]["reconcile"] = result
                if result.get("status") in {"COMPLETE", "ERROR", "ESCALATED"}:
                    break
                time.sleep(2)
        elif started.get("status") in {"ERROR", "ESCALATED"}:
            break
        time.sleep(1)
    final_turns = store.latest_turns(root_id, 20)
    final = final_turns[-1]
    final_request = loop.read_request(final.ec8_request_id) if final.ec8_request_id else {}
    write(evidence / "cme-activations.json", activations)
    return {
        "turns": [
            {
                "logical_consultation_id": turn.logical_consultation_id,
                "parent_logical_id": turn.parent_logical_id,
                "status": turn.status,
                "request_id": turn.ec8_request_id,
                "response_id": turn.response_id,
                "continuation_reason": turn.continuation_reason,
                "current_evidence": turn.current_evidence,
            }
            for turn in final_turns
        ],
        "final_request": final_request,
        "final_cme_state": json.loads(STATE.read_text()) if STATE.exists() else None,
        "lock_exists": LOCK.exists(),
    }


def run(evidence: Path) -> int:
    evidence.mkdir(parents=True, exist_ok=True)
    store = ConsultationStore(DB)
    loop = GraceConsultationLoop(store=store)
    session_id = "grace-e2e-execution-" + uuid4().hex[:12]
    prompt = (
        f"This is a fresh bounded acceptance run {session_id}. "
        "Grace, verify whether the controlled acceptance fixture at "
        "Temp/cme-execution-fixtures/full-loop-20260807/fixture.json satisfies "
        "its documented invariant. If needed, ask for higher-level reasoning "
        "before acting. "
        "If technical verification is justified, arrange the smallest safe "
        "fixture-only verification or correction, validate the actual result, "
        "and report what was truly proven. Do not modify production."
    )
    request = {"model": "estate/grace", "messages": [{"role": "user", "content": prompt}], "metadata": {"session_id": session_id}, "stream": False}
    write(evidence / "steward-request.json", {"session_id": session_id, "prompt": prompt, "gateway": GATEWAY, "recorded_at": now()})
    before_ids = {item.logical_consultation_id for item in records_for_session(store, session_id)}
    first = gateway(request)
    write(evidence / "grace-intake-response.json", first)
    after = records_for_session(store, session_id)
    roots = {item.root_logical_id for item in after if item.logical_consultation_id not in before_ids}
    if len(roots) != 1:
        raise RuntimeError(f"ordinary_grace_intake_root_correlation_failed:{sorted(roots)}")
    root_id = next(iter(roots))
    write(evidence / "consultation-lineage-before-settle.json", {
        "session_id": session_id,
        "root_logical_id": root_id,
        "new_turn_ids": sorted(item.logical_consultation_id for item in after if item.logical_consultation_id not in before_ids),
        "gateway_external_reasoning": (first.get("estate") or {}).get("external_reasoning"),
    })

    settled = settle_root(store, loop, root_id, evidence)
    write(evidence / "settled-lineage.json", settled)
    turns = store.latest_turns(root_id, 20)
    execution_links = []
    for turn in turns:
        execution_links.extend(store.execution_requests(turn.logical_consultation_id))
    if not execution_links:
        raise RuntimeError("ordinary_grace_path_created_no_execution_request")
    execution = execution_links[-1]
    attempts = store.execution_attempts(execution.execution_request_id)
    request_path = ROOT / "runtime" / "execution_adapters" / "requests" / f"{execution.execution_request_id}.json"
    result_path = Path(execution.result_reference) if execution.result_reference else None
    write(evidence / "execution-provenance.json", {
        "execution_request": execution.__dict__,
        "adapter_request": json.loads(request_path.read_text(encoding="utf-8")) if request_path.exists() else None,
        "attempts": [attempt.__dict__ for attempt in attempts],
        "result": json.loads(result_path.read_text(encoding="utf-8")) if result_path and result_path.exists() else None,
    })
    latest = store.latest_turns(root_id, 20)[-1]
    final_request = loop.read_request(latest.ec8_request_id) if latest.ec8_request_id else {}
    if execution.provider_id != "codex-cli-openai" or execution.status not in {"completed", "dry_run_completed"}:
        raise RuntimeError(f"execution_provider_or_status_invalid:{execution.provider_id}:{execution.status}")
    if not attempts or not result_path or not result_path.exists():
        raise RuntimeError("durable_execution_evidence_missing")

    final_prompt = (
        "Now give the Steward the final grounded report for the verification "
        "you arranged. Clearly distinguish the initial belief, the technical "
        "recommendation, what was authorized, what was actually done, the "
        "evidence produced, the reevaluation conclusion, remaining uncertainty, "
        "and whether further action is required. Do not claim anything not shown "
        "by the completed verification."
    )
    final_body = gateway({
        "model": "estate/grace",
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": content(first)},
            {"role": "user", "content": final_prompt},
        ],
        "metadata": {"session_id": session_id},
        "stream": False,
    })
    write(evidence / "grace-final-synthesis.json", final_body)
    write(evidence / "final-acceptance.json", {
        "classification": "GRACE_END_TO_END_REASON_EXECUTE_OBSERVE_REASON_READY",
        "session_id": session_id,
        "root_logical_id": root_id,
        "execution_request_id": execution.execution_request_id,
        "provider_id": execution.provider_id,
        "attempt_ids": [attempt.execution_attempt_id for attempt in attempts],
        "final_turn_id": latest.logical_consultation_id,
        "final_request_id": latest.ec8_request_id,
        "final_response_id": (final_request.get("response") or {}).get("response_id"),
        "fixture": json.loads(FIXTURE.read_text(encoding="utf-8")),
        "final_grace_response": content(final_body),
        "cme": settled.get("final_cme_state"),
        "lock_exists": settled.get("lock_exists"),
    })
    (evidence / "exit-code").write_text("0\n", encoding="utf-8")
    (evidence / "completion.marker").write_text("GRACE_END_TO_END_REASON_EXECUTE_OBSERVE_REASON_COMPLETE\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    run_dir = Path(sys.argv[1])
    try:
        raise SystemExit(run(run_dir))
    except Exception as exc:
        write(run_dir / "failure.json", {"error_class": type(exc).__name__, "error": str(exc), "recorded_at": now()})
        (run_dir / "exit-code").write_text("1\n", encoding="utf-8")
        (run_dir / "completion.marker").write_text("GRACE_END_TO_END_REASON_EXECUTE_REASON_FAILED\n", encoding="utf-8")
        raise
