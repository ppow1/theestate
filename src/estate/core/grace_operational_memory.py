"""Authoritative, read-only operational memory for the Grace gateway.

This module is deliberately separate from resident prose generation.  A Grace
state query is answered from durable Estate records or explicitly reported as
unavailable; model output is never used as a source of operational facts.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from estate.core.consultation_store import ConsultationStore


DEFAULT_DATABASE = Path(r"A:\theestate-data\consultations\consultations.db")
DEFAULT_CME_STATE = Path(r"A:\theestate-data\chatgpt-mailbox-worker\cme-owner-state.json")
TERMINAL_TURN_STATES = {"response_received", "resolved", "closed"}


def is_operational_state_query(message: str) -> bool:
    """Conservative boundary for mutable/current Estate state questions."""
    text = str(message or "").lower()
    signals = (
        ("operational" in text and ("status" in text or "state" in text or "memory" in text)),
        ("most recent" in text and "consultation" in text),
        ("latest" in text and "consultation" in text),
        ("latest" in text and "root" in text),
        ("final state" in text and "consultation" in text),
        ("execution" in text and ("required" in text or "occurred" in text or "reasoning only" in text)),
        ("operational memory" in text),
        ("current cme" in text),
        ("currently blocked" in text),
        ("provenance" in text and ("record" in text or "authoritative evidence" in text or "action" in text)),
    )
    return any(signals)


def classify_operational_request(message: str) -> dict[str, Any]:
    """Classify the small gateway boundary without becoming a general planner."""
    text = str(message or "")
    lower = text.lower()
    operational = is_operational_state_query(text)
    composite_signals = (
        "did you" in lower, "actually record" in lower, "authoritative evidence" in lower,
        "provenance" in lower, "distinguish" in lower, "recommend" in lower,
        "why" in lower, "pending" in lower, "executed" in lower,
        "requested" in lower, "inference" in lower, "end your response" in lower,
        "authoritatively_completed" in lower, "pending_execution" in lower,
        "insufficient_evidence" in lower,
    )
    if not operational:
        return {"mode": "conceptual", "requires_operational_read": False, "composite": False}
    composite = any(composite_signals) or text.count("\n") >= 3
    return {"mode": "grounded_composite_reasoning" if composite else "direct_authoritative_read",
            "requires_operational_read": True, "composite": composite}


def build_composite_operational_evidence(snapshot: dict[str, Any], user_message: str) -> dict[str, Any]:
    """Create bounded, per-request evidence; never persist it as identity context."""
    return {
        "schema_version": "estate.grace.composite_evidence.v1",
        "original_request_preserved": True,
        "read_only_request": True,
        "operational_snapshot": snapshot,
        "runtime_bridge_invoked": True,
        "action_evidence": {
            "authoritative_action_available": False,
            "authoritative_read_available": bool(snapshot.get("authoritative")),
            "executed_in_current_interaction": ["authoritative operational read"] if snapshot.get("authoritative") else [],
            "recommended_in_current_interaction": [],
            "requested_in_current_interaction": ["answer the user's provenance questions"],
            "pending_in_current_interaction": ["any write/document/tag action without authoritative_action evidence"],
            "requested_action_pending": False,
            "underlying_action_status": "unproven",
            "provenance": "authoritative_read" if snapshot.get("authoritative") else "unavailable/unverified",
        },
        "user_request_sha256": hashlib.sha256(str(user_message).encode("utf-8")).hexdigest(),
    }


def composite_obligations(message: str) -> dict[str, bool]:
    lower = str(message or "").lower()
    return {
        "recording_status": "record" in lower or "document" in lower,
        "evidence": "evidence" in lower or "provenance" in lower,
        "categories": "distinguish" in lower or "executed" in lower or "requested" in lower,
        "terminal_classification": any(token in lower for token in ("authoritatively_completed", "pending_execution", "insufficient_evidence")),
    }


def composite_response_complete(response: str, message: str) -> bool:
    text = str(response or "").lower()
    obligations = composite_obligations(message)
    if obligations["recording_status"] and not ("record" in text and ("not" in text or "no" in text or "pending" in text)):
        return False
    if obligations["evidence"] and "evidence" not in text and "provenance" not in text:
        return False
    if obligations["categories"] and not all(word in text for word in ("executed", "requested", "pending")):
        return False
    if obligations["terminal_classification"] and not any(token in text for token in ("authoritatively_completed", "pending_execution", "insufficient_evidence")):
        return False
    return True


def derive_terminal_provenance_status(evidence: dict[str, Any]) -> str:
    """Select the terminal token for the underlying action, never the inquiry."""
    action = evidence.get("action_evidence") if isinstance(evidence, dict) else {}
    action = action if isinstance(action, dict) else {}
    result = action.get("authoritative_action_result")
    if isinstance(result, dict):
        provenance = str(result.get("provenance") or result.get("claim_provenance") or "")
        status = str(result.get("status") or result.get("state") or "").lower()
        if provenance == "authoritative_action" and status in {"completed", "succeeded", "recorded", "resolved", "verified"}:
            return "AUTHORITATIVELY_COMPLETED"
        if provenance == "authoritative_action" and status in {"queued", "pending", "awaiting_execution", "claimed"}:
            return "PENDING_EXECUTION"
    if action.get("requested_action_pending") is True:
        return "PENDING_EXECUTION"
    return "INSUFFICIENT_EVIDENCE"


def enforce_terminal_provenance_status(response: str, message: str, evidence: dict[str, Any]) -> str:
    """Replace model-selected terminal words with evidence-derived status."""
    if not composite_obligations(message)["terminal_classification"]:
        return str(response or "")
    status = derive_terminal_provenance_status(evidence)
    cleaned = str(response or "")
    for token in ("AUTHORITATIVELY_COMPLETED", "PENDING_EXECUTION", "INSUFFICIENT_EVIDENCE"):
        cleaned = cleaned.replace(token, "")
    return cleaned.rstrip() + "\n" + status


def render_provenance_composite(snapshot: dict[str, Any]) -> str:
    """Bounded truthful completion for the known provenance-question shape."""
    if not snapshot.get("authoritative"):
        return ("I cannot verify the operational read or any recording action. "
                "No authoritative write evidence is available. Executed: none verified. "
                "Recommended/requested: answer the provenance questions. Pending: authoritative verification. "
                "INSUFFICIENT_EVIDENCE")
    return ("1. Recording status: I did not actually record the grounding acceptance during this read-only interaction. "
            "No authoritative_action result exists.\n"
            "2. Authoritative evidence: the only completed operation here was an authoritative operational read, "
            "provenanced to consultation_store and cme_runtime. There is no authoritative evidence of a write, "
            "document update, tag, or closeout action.\n"
            "3. Unsupported claims: any earlier statement that the acceptance was recorded or documented is "
            "unverified by the available action evidence; it must not be treated as completed.\n"
            "4. Categories — executed: authoritative read only. Recommended: none. Requested: answer this "
            "provenance review; prior recording/documentation was requested. Pending: any write or documentation "
            "action requiring an authoritative_action result.\n"
            "5. Provenance: authoritative_read for the snapshot; unavailable/unverified for write completion.\n"
            "INSUFFICIENT_EVIDENCE")


def _fact(value: Any, source: str, *, authoritative: bool, unavailable: str | None = None) -> dict[str, Any]:
    result = {"value": value, "source": source, "authority": "authoritative" if authoritative else "unavailable"}
    if unavailable:
        result["unavailable_reason"] = unavailable
    return result


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _classification(record: Any) -> str | None:
    response = record.response
    if not isinstance(response, dict):
        return None
    decision = response.get("structured_decision")
    return decision.get("classification") if isinstance(decision, dict) else None


def _completed_root_summary(store: ConsultationStore) -> dict[str, Any] | None:
    records = store.search()
    by_root: dict[str, list[Any]] = {}
    for record in records:
        by_root.setdefault(record.root_logical_id, []).append(record)
    candidates: list[tuple[str, Any, list[Any]]] = []
    for root_id, turns in by_root.items():
        turns.sort(key=lambda item: item.consultation_turn_number)
        latest = turns[-1]
        # Completion is based on a durable response on the latest turn, not
        # lexical root ordering or the mutable root row's transient status.
        if latest.status not in TERMINAL_TURN_STATES or latest.response is None:
            continue
        candidates.append((latest.updated_at, latest, turns))
    if not candidates:
        return None
    _, latest, turns = max(candidates, key=lambda item: (item[0], item[1].consultation_root_id, item[1].consultation_turn_number))
    requests = []
    attempts = []
    for turn in turns:
        for request in store.execution_requests(turn.logical_consultation_id):
            requests.append(request)
            attempts.extend(store.execution_attempts(request.execution_request_id))
    return {
        "root_logical_id": latest.root_logical_id,
        "latest_turn_logical_id": latest.logical_consultation_id,
        "latest_turn_state": latest.status,
        "final_state": latest.status,
        "final_classification": _classification(latest),
        "execution_occurred": bool(requests or attempts),
        "logical_execution_request_count": len(requests),
        "physical_execution_attempt_count": len(attempts),
        "execution_request_ids": [item.execution_request_id for item in requests],
        "execution_attempt_ids": [item.execution_attempt_id for item in attempts],
        "completed_at": latest.updated_at,
    }


def read_operational_snapshot(*, database_path: str | Path = DEFAULT_DATABASE,
                              cme_state_path: str | Path = DEFAULT_CME_STATE) -> dict[str, Any]:
    """Return a bounded snapshot without writing any Estate state."""
    db_path = Path(database_path)
    state_path = Path(cme_state_path)
    provenance: dict[str, Any] = {}
    unavailable: list[str] = []
    latest: dict[str, Any] | None = None
    memory = False
    if not db_path.exists():
        reason = f"consultation database does not exist: {db_path}"
        provenance["latest_completed_consultation"] = _fact(None, "consultation_store", authoritative=False, unavailable=reason)
        provenance["operational_memory_available"] = _fact(False, "consultation_store", authoritative=False, unavailable=reason)
        unavailable.append(reason)
    else:
        try:
            store = ConsultationStore(db_path)
            # Opening the store and executing the bounded query proves both
            # reachability and schema usability.  No mutating store method is
            # called here.
            latest = _completed_root_summary(store)
            memory = True
            provenance["latest_completed_consultation"] = _fact(latest, "consultation_store", authoritative=True)
            provenance["operational_memory_available"] = _fact(True, "consultation_store", authoritative=True)
        except Exception as exc:
            reason = f"consultation store read failed: {type(exc).__name__}"
            provenance["latest_completed_consultation"] = _fact(None, "consultation_store", authoritative=False, unavailable=reason)
            provenance["operational_memory_available"] = _fact(False, "consultation_store", authoritative=False, unavailable=reason)
            unavailable.append(reason)
    if not state_path.exists():
        reason = f"CME runtime state does not exist: {state_path}"
        operational = None
        provenance["operational_state"] = _fact(None, "cme_runtime", authoritative=False, unavailable=reason)
        unavailable.append(reason)
    else:
        try:
            state = _read_json(state_path)
            operational = state.get("state")
            provenance["operational_state"] = _fact(operational, "cme_runtime", authoritative=True)
        except Exception as exc:
            reason = f"CME runtime state read failed: {type(exc).__name__}"
            operational = None
            provenance["operational_state"] = _fact(None, "cme_runtime", authoritative=False, unavailable=reason)
            unavailable.append(reason)
    return {
        "schema_version": "estate.grace.operational_memory.v1",
        "operation": "read_operational_snapshot",
        "authoritative": not unavailable,
        "operational_state": operational,
        "latest_completed_consultation": latest,
        "operational_memory_available": memory,
        "provenance": provenance,
        "unavailable": unavailable,
        "mutation_performed": False,
    }


def render_operational_snapshot(snapshot: dict[str, Any]) -> str:
    """Render only values present in the authoritative snapshot."""
    if not snapshot.get("authoritative"):
        missing = "; ".join(snapshot.get("unavailable") or ["authoritative state unavailable"])
        return f"STATE_UNAVAILABLE / unable to verify authoritative Estate operational state ({missing})."
    latest = snapshot.get("latest_completed_consultation") or {}
    execution = "execution occurred" if latest.get("execution_occurred") else "reasoning only; no execution record exists"
    return ("Authoritative Estate operational read:\n"
            f"1. Current operational status: {snapshot.get('operational_state')}.\n"
            f"2. Most recent completed consultation root: {latest.get('root_logical_id')}.\n"
            f"3. Final state: {latest.get('final_state')} (latest turn {latest.get('latest_turn_logical_id')}).\n"
            f"4. Execution: {execution}; {latest.get('logical_execution_request_count', 0)} logical request(s), "
            f"{latest.get('physical_execution_attempt_count', 0)} physical attempt(s).\n"
            f"5. Operational memory available: {snapshot.get('operational_memory_available')}.\n"
            "Source: authoritative consultation_store and cme_runtime read; no model inference or mutation was used.")
