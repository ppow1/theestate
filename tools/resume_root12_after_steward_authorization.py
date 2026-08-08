"""Resume root 12 through the existing Steward-decision continuation seam."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.consultation_escalation import resume_after_steward
from estate.core.consultation_store import ConsultationStore
from estate.core.grace_consultation_loop import GraceConsultationLoop


DATA = Path(r"A:\theestate-data")
ESCALATION = "esc-cc905d159a554863"
CURRENT = "12.03"
ROOT = "12.00"
EXECUTION = "exec-f16799a5439b"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    if receipt["lineage"] != {
        "consultation_root": ROOT,
        "current_turn": CURRENT,
        "execution_request_id": EXECUTION,
        "reasoning_result": "MORE_REASONING_REQUIRED",
    }:
        raise ValueError("receipt_lineage_mismatch")
    if receipt["comparison"]["result"] != "PASS" or receipt["scope_assertion"]["fixture_modified"]:
        raise ValueError("unauthorized_or_failed_evidence")

    store = ConsultationStore(DATA / "consultations" / "consultations.db")
    loop = GraceConsultationLoop(store=store)
    escalation = store.escalation(ESCALATION)
    if escalation.current_logical_id != CURRENT:
        raise ValueError("escalation_current_turn_mismatch")

    decisions = store.steward_decisions(ESCALATION)
    if decisions:
        decision = decisions[-1]
    else:
        decision = store.record_steward_decision(
            ESCALATION,
            selected_option="steward_direction",
            decision_text=(
                "Patricia authorizes one additional bounded read-only fixture-evidence acquisition "
                "for the deterministic evidence requested by continuation 12.03. Do not mutate the "
                "fixture, repeat execution, create a new root, or create another logical execution request."
            ),
            decision_action="acquire_one_bounded_read_only_fixture_evidence",
            rationale="Resolve the exact evidence gap identified by 12.03 within the existing root 12 lineage.",
            decision_actor="Steward",
            steward_evidence=[{
                "content": receipt,
                "provenance": "A:\\theestate\\runtime\\evidence\\cme-owner-isolation\\authorized-fixture-evidence.json",
                "impact": "Provides the exact fixture fields, invariant, expected/observed values, and deterministic comparison requested by 12.03.",
            }],
        )

    existing = [
        item for item in store.latest_turns(ROOT, 20)
        if item.parent_logical_id == CURRENT
        and item.continuation_reason == "steward input after bounded autonomous evidence exhaustion"
    ]
    if existing:
        continuation = existing[-1]
        attached = continuation
        idempotent = True
    else:
        continuation = resume_after_steward(
            store,
            CURRENT,
            question=(
                "Reevaluate the original bounded technical verification using the physical execution "
                f"evidence for {EXECUTION} and the newly authorized deterministic fixture evidence. "
                "Do not execute again. Return the authoritative terminal classification and explain "
                "whether the invariant passed."
            ),
            evidence={
                "authorization": ESCALATION,
                "root": ROOT,
                "source": "Steward-authorized bounded fixture evidence",
                "fixture_evidence": receipt,
            },
        )
        attached = loop._create_and_attach(continuation)
        loop.store.set_status(attached.logical_consultation_id, "awaiting_reasoning")
        idempotent = False

    executions = [e for turn in store.get_turn_range(ROOT) for e in store.execution_requests(turn.logical_consultation_id)]
    if len([e for e in executions if e.execution_request_id == EXECUTION]) != 1:
        raise ValueError("execution_lineage_changed")
    if len(executions) != 3:
        raise ValueError(f"unexpected_execution_request_count:{len(executions)}")
    print(json.dumps({
        "escalation_id": ESCALATION,
        "decision_id": decision.decision_id,
        "root": ROOT,
        "parent": CURRENT,
        "continuation": attached.logical_consultation_id,
        "request_id": attached.ec8_request_id,
        "idempotent": idempotent,
        "execution_request_count": len(executions),
        "execution_request_ids": [e.execution_request_id for e in executions],
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
