"""Detached CME-owned execution-branch acceptance for one safe fixture."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"A:\theestate")
DATA = Path(r"A:\theestate-data")
sys.path.insert(0, str(ROOT / "src"))

from estate.core.autonomous_reason_execute_loop import (  # noqa: E402
    AutonomousReasonExecuteLoop,
    classify_reasoning_response,
)
from estate.core.chatgpt_execution_runtime import build_live_execution_router  # noqa: E402
from estate.core.consultation_store import ConsultationStore  # noqa: E402
from estate.core.continuous_momentum_engine import ChatGPTReasoningCMEOwner  # noqa: E402
from estate.core.grace_consultation_loop import (  # noqa: E402
    GraceConsultationLoop,
    _normalize_reasoning_response,
)

DB = DATA / "consultations" / "consultations.db"
STATE = DATA / "chatgpt-mailbox-worker" / "cme-owner-state.json"
LOCK = DATA / "chatgpt-mailbox-worker" / "cme-owner.lock"
FIXTURE_DIR = ROOT / "Temp" / "cme-execution-fixtures" / "full-loop-20260807"
FIXTURE = FIXTURE_DIR / "fixture.json"
INVARIANT = FIXTURE_DIR / "INVARIANT.md"
FIXTURE_MANIFEST = FIXTURE_DIR / "acceptance-manifest.json"
OBJECTIVE = (
    "Grace, verify whether the isolated acceptance fixture at "
    "Temp/cme-execution-fixtures/full-loop-20260807/fixture.json satisfies its "
    "documented invariant. If it does not, determine the appropriate bounded "
    "repair and validate it. Do not modify production."
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def launch_worker(command, **kwargs):
    env = dict(kwargs.get("env") or os.environ)
    env["ESTATE_STRUCTURED_EXECUTION_HANDOFF"] = "0"
    return subprocess.Popen(
        command,
        cwd=kwargs.get("cwd"),
        env=env,
        stdout=kwargs.get("stdout"),
        stderr=kwargs.get("stderr"),
        text=True,
    )


def prepare_fixture() -> dict:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    if not INVARIANT.exists():
        INVARIANT.write_text(
            "# Fixture invariant\n\n"
            "`fixture.json` is valid only when `actual` equals `expected` and "
            "`status` is `valid`. The initial acceptance state is intentionally "
            "invalid; repair is limited to this fixture file.\n",
            encoding="utf-8",
        )
    if not FIXTURE.exists():
        write_json(FIXTURE, {"name": "controlled-execution-branch", "actual": "incorrect", "expected": "correct", "status": "invalid"})
    fixture = read_json(FIXTURE)
    if not isinstance(fixture, dict) or fixture.get("expected") != "correct":
        raise RuntimeError("fixture_manifest_invalid")
    return fixture


def fixture_valid() -> bool:
    fixture = read_json(FIXTURE) or {}
    return fixture.get("actual") == fixture.get("expected") and fixture.get("status") == "valid"


def wait_authoritative(loop, request_id: str, timeout: float = 720) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            record = loop.read_request(request_id)
            if record.get("state") == "resolved" and record.get("response"):
                return record
        except Exception:
            pass
        time.sleep(2)
    raise TimeoutError("authoritative_timeout:" + request_id)


def sync_response(store, logical_id: str, authoritative: dict):
    current = store.get(logical_id)
    if current.response:
        return current
    response = authoritative.get("response")
    normalized = _normalize_reasoning_response(response)
    return store.append_response(
        logical_id,
        normalized,
        response_id=response.get("response_id") if isinstance(response, dict) else None,
        recommendation=normalized.get("content") if isinstance(normalized, dict) else None,
    )


def wait_worker_settled(timeout: float = 120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = read_json(STATE) or {}
        pid = state.get("pid")
        if not pid:
            return state
        try:
            os.kill(int(pid), 0)
        except (OSError, ValueError):
            return state
        time.sleep(1)
    return read_json(STATE) or {}


def reconcile_owner(owner: ChatGPTReasoningCMEOwner):
    result = owner.reconcile()
    if result.get("status") == "RUNNING":
        wait_worker_settled()
        result = owner.reconcile()
    return result


def turn_artifact(evidence: Path, label: str, consultation, decision, authoritative):
    write_json(evidence / f"reasoning-{label}.json", {
        "logical_consultation_id": consultation.logical_consultation_id,
        "request_id": consultation.ec8_request_id,
        "response_id": (authoritative.get("response") or {}).get("response_id"),
        "classification": decision.classification,
        "rationale": decision.rationale,
        "structured_decision": decision.execution or decision.evidence_request,
        "events": authoritative.get("events", []),
    })


def find_or_create_root(store: ConsultationStore, loop: GraceConsultationLoop) -> tuple[object, bool]:
    manifest = read_json(FIXTURE_MANIFEST) or {}
    existing_id = manifest.get("consultation_id")
    if existing_id:
        return store.get(existing_id), False
    for item in store.search():
        if item.root_logical_id == item.logical_consultation_id and item.objective == OBJECTIVE:
            write_json(FIXTURE_MANIFEST, {"fixture_dir": str(FIXTURE_DIR), "consultation_id": item.logical_consultation_id, "objective": OBJECTIVE})
            return item, False
    consultation = loop._allocate(OBJECTIVE, parent=None, session_id="cme-execution-fixture-20260807", ptm_project_id=None, ptm_work_item_id=None, tags=("controlled-execution-fixture",))
    consultation = loop._create_and_attach(consultation)
    write_json(FIXTURE_MANIFEST, {"fixture_dir": str(FIXTURE_DIR), "consultation_id": consultation.logical_consultation_id, "objective": OBJECTIVE})
    return consultation, True


def existing_request(store: ConsultationStore, logical_id: str, purpose: str):
    for link in store.execution_requests(logical_id):
        request = read_json(ROOT / "runtime" / "execution_adapters" / "requests" / f"{link.execution_request_id}.json") or {}
        if request.get("metadata", {}).get("purpose") == purpose:
            return link
    return None


def acquire_fixture_evidence(store, router, loop, consultation, request, evidence: Path):
    link = existing_request(store, consultation.logical_consultation_id, "EVIDENCE_ACQUISITION")
    if link is None:
        acquisition = router.create_request(
            consultation.logical_consultation_id,
            required_capability="repository_read",
            dispatch_id=f"dispatch-{consultation.logical_consultation_id.replace('.', '-')}-fixture-evidence",
            prompt_source="docs/prompts/cme_execution_fixture_readonly_20260807.md",
            classification="Estate Internal",
            read_scope_paths=["docs/prompts", "Temp/cme-execution-fixtures/full-loop-20260807"],
            write_scope_paths=[],
            blocked_scope_paths=["production", "runtime", "src"],
            expected_outputs=request["evidence_requirements"],
            validation_required=True,
            decision_reference="controlled-fixture-evidence-request",
            metadata={"purpose": "EVIDENCE_ACQUISITION", "consultation_id": consultation.logical_consultation_id, "scope": "read-only"},
        )
        result = router.execute(acquisition.adapter_request_id)
        link = store.execution_request(acquisition.adapter_request_id)
    else:
        result = type("ExistingResult", (), {
            "provider_id": link.provider_id,
            "status": link.status,
            "validation_status": link.validation_status,
            "summary": str((link.result_json or {}).get("summary") or ""),
            "artifacts": (link.result_json or {}).get("artifacts", []),
        })()
    package = {"execution_request_id": link.execution_request_id, "provider_id": result.provider_id, "status": result.status, "validation_status": result.validation_status, "summary": result.summary[:4000], "result_reference": link.result_reference, "artifacts": result.artifacts}
    write_json(evidence / "pre-execution-evidence.json", package)
    if result.status != "completed":
        raise RuntimeError("fixture_evidence_acquisition_failed:" + result.status)
    store.append_validation(consultation.logical_consultation_id, observed_result="EVIDENCE_ACQUIRED", evidence=package, status="continuation_required")
    continuations = [turn for turn in store.latest_turns(consultation.root_logical_id, 10) if turn.current_evidence and turn.current_evidence.get("execution_request_id") == link.execution_request_id]
    continuation = continuations[-1] if continuations else None
    if continuation is None:
        continuation = router.continue_from_execution(consultation.logical_consultation_id, link.execution_request_id, question="Reevaluate the isolated fixture using the acquired read-only evidence and determine whether a bounded repair is warranted.", continuation_reason="controlled_fixture_evidence_acquired")
        continuation = loop._create_and_attach(continuation)
        store.set_status(continuation.logical_consultation_id, "awaiting_reasoning")
    return continuation


def wake_and_read(owner, loop, store, consultation, evidence: Path, label: str):
    tick = owner.tick()
    authoritative = wait_authoritative(loop, consultation.ec8_request_id)
    wait_worker_settled()
    record = sync_response(store, consultation.logical_consultation_id, authoritative)
    write_json(evidence / f"reasoning-{label}-raw.json", {"logical_consultation_id": consultation.logical_consultation_id, "request_id": consultation.ec8_request_id, "response": record.response, "authoritative": authoritative})
    try:
        decision = classify_reasoning_response(record.response)
    except ValueError as exc:
        write_json(evidence / f"reasoning-{label}-invalid.json", {"error": str(exc), "response": record.response})
        raise
    turn_artifact(evidence, label, consultation, decision, authoritative)
    return record, decision, authoritative, tick


def queue_format_repair(loop, store, consultation, error: ValueError, evidence: Path):
    reason = str(error)
    if not reason.startswith(("execution_spec_", "execution_scope_", "execution_consultation_", "execution_capability_")):
        raise error
    repair = loop.create_execution_format_repair_continuation(consultation.logical_consultation_id, "EXECUTION_RECOMMENDATION_INVALID:" + reason)
    write_json(evidence / "execution-recommendation-invalid.json", {"logical_consultation_id": consultation.logical_consultation_id, "error": reason, "format_repair": repair, "execution_created": False})
    return store.get(repair["logical_consultation_id"])


def run(evidence: Path) -> int:
    evidence.mkdir(parents=True, exist_ok=True)
    store = ConsultationStore(DB)
    loop = GraceConsultationLoop(store=store)
    fixture_before = prepare_fixture()
    write_json(evidence / "fixture-preflight.json", {"fixture_dir": str(FIXTURE_DIR), "fixture": fixture_before, "invariant_valid_before": fixture_valid(), "production_mutation": False})
    consultation, created = find_or_create_root(store, loop)
    write_json(evidence / "consultation-root.json", {"consultation_id": consultation.logical_consultation_id, "request_id": consultation.ec8_request_id, "created_now": created, "objective": consultation.objective})
    if fixture_valid() and (read_json(FIXTURE_MANIFEST) or {}).get("completed"):
        write_json(evidence / "idempotent-reuse.json", {"reused": True, "reason": "fixture_acceptance_already_completed", "consultation_id": consultation.logical_consultation_id})
        write_json(evidence / "final-cme-state.json", {"state": read_json(STATE), "lock_exists": LOCK.exists(), "duplicate_tick": "not_needed_completed_reuse"})
        (evidence / "exit-code").write_text("0\n", encoding="utf-8")
        (evidence / "completion.marker").write_text("CME_EXECUTION_FIXTURE_ACCEPTANCE_COMPLETE\n", encoding="utf-8")
        return 0

    owner = ChatGPTReasoningCMEOwner(store, state_path=STATE, lock_path=LOCK, launcher=launch_worker, read_request=loop.read_request)
    router = build_live_execution_router(store, runtime_root=ROOT)
    reasoning = AutonomousReasonExecuteLoop(store, router)
    if not consultation.response:
        record, decision, authoritative, first_tick = wake_and_read(owner, loop, store, consultation, evidence, "first")
    else:
        authoritative = loop.read_request(consultation.ec8_request_id)
        record = store.get(consultation.logical_consultation_id)
        decision = classify_reasoning_response(record.response)
        first_tick = {"status": "REUSED_COMPLETED_TURN"}
        turn_artifact(evidence, "first-reused", consultation, decision, authoritative)

    current = consultation
    if decision.classification == "MORE_REASONING_REQUIRED":
        current = acquire_fixture_evidence(store, router, loop, current, decision.evidence_request, evidence)
        prior_format_repairs = [turn for turn in store.latest_turns(consultation.root_logical_id, 10) if turn.continuation_reason == "execution_recommendation_format_repair"]
        if prior_format_repairs:
            current = prior_format_repairs[-1]
        try:
            if not store.get(current.logical_consultation_id).response:
                record, decision, authoritative, second_tick = wake_and_read(owner, loop, store, current, evidence, "evidence-reevaluation")
            else:
                authoritative = loop.read_request(current.ec8_request_id)
                record = store.get(current.logical_consultation_id)
                decision = classify_reasoning_response(record.response)
                second_tick = {"status": "REUSED_COMPLETED_TURN"}
                turn_artifact(evidence, "evidence-reevaluation-reused", current, decision, authoritative)
        except ValueError as exc:
            current = queue_format_repair(loop, store, current, exc, evidence)
            record, decision, authoritative, repair_tick = wake_and_read(owner, loop, store, current, evidence, "format-repair")
    if decision.classification != "EXECUTION_RECOMMENDED":
        write_json(evidence / "bounded-outcome.json", {"classification": decision.classification, "reason": "fixture_did_not_produce_justified_execution", "consultation_id": current.logical_consultation_id})
        final_owner = reconcile_owner(owner)
        duplicate = owner.tick()
        write_json(evidence / "final-cme-state.json", {"cme_state": final_owner, "duplicate_tick": duplicate, "lock_exists": LOCK.exists(), "classification": decision.classification})
        raise RuntimeError("FIXTURE_DID_NOT_PRODUCE_JUSTIFIED_EXECUTION:" + decision.classification)

    prior_execution_links = store.execution_requests(current.logical_consultation_id)
    completed_execution = next((item for item in reversed(prior_execution_links) if item.status in {"completed", "dry_run_completed"}), None)
    accepted = ({"status": "execution_requested", "execution_request_id": completed_execution.execution_request_id, "idempotent": True}
                if completed_execution else reasoning.accept_reasoning(current.logical_consultation_id, record.response))
    execution_id = accepted["execution_request_id"]
    link = store.execution_request(execution_id)
    write_json(evidence / "execution-request.json", {"execution_request_id": execution_id, "consultation_id": current.logical_consultation_id, "provider_id": link.provider_id, "required_capability": link.required_capability, "request": read_json(ROOT / "runtime" / "execution_adapters" / "requests" / f"{execution_id}.json")})
    before = read_json(FIXTURE)
    result = router.execute(execution_id) if link.status not in {"completed", "dry_run_completed"} else type("ExistingResult", (), {"status": link.status, "provider_id": link.provider_id, "summary": (link.result_json or {}).get("summary", ""), "validation_status": link.validation_status, "artifacts": (link.result_json or {}).get("artifacts", [])})()
    link = store.execution_request(execution_id)
    after = read_json(FIXTURE)
    execution_evidence = {"execution_request_id": execution_id, "attempts": [a.__dict__ for a in store.execution_attempts(execution_id)], "provider_id": result.provider_id, "status": result.status, "validation_status": result.validation_status, "summary": result.summary[:4000], "result_reference": link.result_reference, "fixture_before": before, "fixture_after": after, "fixture_validated": fixture_valid(), "artifacts": result.artifacts}
    write_json(evidence / "execution-attempt.json", execution_evidence)
    if result.status != "completed" or not fixture_valid():
        raise RuntimeError("fixture_execution_validation_failed")
    store.append_validation(current.logical_consultation_id, observed_result="VALIDATED", evidence=execution_evidence, status="continuation_required")
    continuation = next((turn for turn in store.latest_turns(consultation.root_logical_id, 10) if turn.current_evidence and turn.current_evidence.get("execution_request_id") == execution_id), None)
    if continuation is None:
        continuation = router.continue_from_execution(current.logical_consultation_id, execution_id, question="Reevaluate the original invariant using the actual bounded repair and validation evidence, then state the current conclusion.", continuation_reason="fixture_execution_evidence_requires_reevaluation")
        continuation = loop._create_and_attach(continuation)
        store.set_status(continuation.logical_consultation_id, "awaiting_reasoning")
    if not store.get(continuation.logical_consultation_id).response:
        final_record, final_decision, final_authoritative, final_tick = wake_and_read(owner, loop, store, continuation, evidence, "final")
    else:
        final_authoritative = loop.read_request(continuation.ec8_request_id)
        final_record = store.get(continuation.logical_consultation_id)
        final_decision = classify_reasoning_response(final_record.response)
        final_tick = {"status": "REUSED_COMPLETED_TURN"}
        turn_artifact(evidence, "final-reused", continuation, final_decision, final_authoritative)
    final_owner = reconcile_owner(owner)
    duplicate = owner.tick()
    outcome = {"consultation_id": continuation.logical_consultation_id, "classification": final_decision.classification, "response_id": final_record.response_id, "authoritative": final_authoritative.get("state") == "resolved", "fixture_valid": fixture_valid()}
    write_json(evidence / "grace-outcome.json", outcome)
    write_json(evidence / "final-cme-state.json", {"cme_state": final_owner, "duplicate_tick": duplicate, "lock_exists": LOCK.exists(), "outcome": outcome})
    write_json(FIXTURE_MANIFEST, {**(read_json(FIXTURE_MANIFEST) or {}), "completed": True, "completed_at": now(), "execution_request_id": execution_id, "final_consultation_id": continuation.logical_consultation_id})
    (evidence / "exit-code").write_text("0\n", encoding="utf-8")
    (evidence / "completion.marker").write_text("CME_EXECUTION_FIXTURE_ACCEPTANCE_COMPLETE\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    evidence = Path(sys.argv[1])
    try:
        raise SystemExit(run(evidence))
    except SystemExit:
        raise
    except Exception as exc:
        write_json(evidence / "failure.json", {"error_class": type(exc).__name__, "error": str(exc)[:1000], "state": read_json(STATE), "lock": read_json(LOCK)})
        (evidence / "exit-code").write_text("1\n", encoding="utf-8")
        (evidence / "completion.marker").write_text("CME_EXECUTION_FIXTURE_ACCEPTANCE_COMPLETE\n", encoding="utf-8")
        raise
