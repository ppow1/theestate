"""Persist the final Grace presentation from authoritative root-12 evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.consultation_store import ConsultationStore
from estate.core.resident_interaction import process_chat


DATA = Path(r"A:\theestate-data")
SESSION = "grace-e2e-execution-41563810c8f7"
ROOT = "12.00"
FINAL = "12.04"
EXECUTION = "exec-f16799a5439b"


def main() -> int:
    output = Path(sys.argv[1])
    store = ConsultationStore(DATA / "consultations" / "consultations.db")
    final = store.get(FINAL)
    if final.root_logical_id != ROOT or final.status != "resolved":
        raise ValueError("root12_not_authoritatively_resolved")
    response = final.response if isinstance(final.response, dict) else {}
    decision = response.get("structured_decision") if isinstance(response, dict) else {}
    if not isinstance(decision, dict) or decision.get("outcome") != "INVARIANT_PASSED":
        raise ValueError("root12_terminal_decision_missing")
    links = [e for turn in store.get_turn_range(ROOT) for e in store.execution_requests(turn.logical_consultation_id)]
    original = [e for e in links if e.execution_request_id == EXECUTION]
    if len(original) != 1:
        raise ValueError("execution_duplicate_or_missing")
    evidence = {
        "final_synthesis_contract": "bounded_authoritative_consultation",
        "source": "authoritative_estate_consultation_and_execution_records",
        "consultation": {
            "root": ROOT,
            "final_turn": FINAL,
            "response_id": final.response_id,
            "classification": decision.get("classification"),
            "outcome": decision.get("outcome"),
            "basis": decision.get("basis"),
        },
        "execution": {
            "request_id": EXECUTION,
            "provider": original[0].provider_id,
            "status": original[0].status,
            "attempts": [a.__dict__ for a in store.execution_attempts(EXECUTION)],
            "result_reference": original[0].result_reference,
        },
        "authorization": "esc-cc905d159a554863",
        "no_new_execution": True,
    }
    prompt = (
        "Grace, give Pat the final grounded report for the verification already "
        "completed. Explain what was requested, what higher-level reasoning "
        "recommended, what was authorized, what was actually done, what the "
        "evidence proves, the reevaluation conclusion, any remaining uncertainty, "
        "and whether further action is required. Do not claim work that is not in "
        "the authoritative evidence."
    )
    result = process_chat(
        "grace", prompt, session_id=SESSION, participant_role="Steward",
        action="conversation", reasoning_evidence=evidence, persist=True,
    )
    turn = result["turn"]
    receipt = {
        "schema": "estate.grace.final.synthesis.v1",
        "session_id": SESSION,
        "consultation_root": ROOT,
        "consultation_final_turn": FINAL,
        "consultation_response_id": final.response_id,
        "execution_request_id": EXECUTION,
        "grace_turn_id": turn["turn_id"],
        "grace_response": turn["resident_response"],
        "grace_llm": turn["llm"],
        "authoritative_evidence_used": evidence,
        "manual_evidence_copy": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
