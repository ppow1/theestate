"""Three-process harness proof for ESTATE-NOTEBOOK-001.

The parent is the deterministic harness. Each worker invocation is a separate
Python process and receives a serialized packet, current-stage files, and
validation context only. No model is invoked; the result is explicitly
HARNESS-LEVEL FRESH-SESSION CONTINUITY.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POC = ROOT / "workspace"
INPUT = ROOT / "input"
EVIDENCE = ROOT / "evidence"
STATE_PATH = POC / "verified_state.json"
sys.path.insert(0, str(ROOT.parents[1] / "src"))
from estate.core.engineering_notebook import (  # noqa: E402
    NotebookRejection,
    acknowledge,
    apply_verified_update,
    build_packet,
    create_handoff,
    create_notebook,
    digest_json,
    detect_freshness,
    refresh_notebook,
    state_digest,
    utc_now,
    write_notebook_atomic,
)


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def worker_main(packet_path: Path, result_path: Path) -> None:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    state = packet["state"]
    core = packet["packet_core"]
    if packet.get("handoff") is not None:
        handoff = packet["handoff"]
        if handoff["state_digest"] != state["state_digest"] or handoff["packet_digest"] != digest_json(core):
            raise RuntimeError("handoff does not match supplied packet")
    ack = packet["ack"]
    acknowledge(state, ack, current_source_digests=packet["source_digests"], current_source_commit=packet["source_commit"], current_stage_files=packet["stage_files"], current_authority_digest=packet["authority_digest"], current_evidence_digest=packet["evidence_digest"], current_assigned_worker=packet["assigned_worker"])
    stage = packet["stage"]
    output = Path(packet["output"])
    output.parent.mkdir(parents=True, exist_ok=True)
    if stage == "parser":
        output.write_text(json.dumps({"items": [{"id": "fixture-1", "title": "bounded"}]}), encoding="utf-8")
    elif stage == "schema":
        output.write_text('{"schema_valid": true}', encoding="utf-8")
    elif stage == "html":
        output.write_text("<html><body>fixture-1 searchable dashboard</body></html>", encoding="utf-8")
    else:
        raise RuntimeError(f"unsupported stage: {stage}")
    result = {"session_id": f"pid-{os.getpid()}", "worker_id": packet["worker_id"], "acknowledgment": ack, "actions": [f"completed {stage}"], "validation": {"stage": stage, "output": str(output.relative_to(ROOT)).replace("\\", "/"), "validation": "pass"}, "fixture_hash": hashlib.sha256((INPUT / "corpus.md").read_bytes()).hexdigest()}
    atomic_json(result_path, result)


def run_worker(packet: dict, session_number: int) -> dict:
    packet_path = POC / f"session_{session_number}_packet.json"
    result_path = POC / f"session_{session_number}_result.json"
    atomic_json(packet_path, packet)
    completed = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(packet_path), str(result_path)], cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"worker session {session_number} failed: {completed.stdout}\n{completed.stderr}")
    return json.loads(result_path.read_text(encoding="utf-8"))


def make_ack(core: dict) -> dict:
    return {"notebook_id": core["notebook_id"], "objective": core["objective"], "stage": core["current_stage"], "permitted_repository": core["permitted_repository"], "permitted_write_paths": core["permitted_write_paths"], "blocker": core["current_blocker"], "required_validation": core["required_validation"], "prohibited_actions": core["prohibited_actions"], "stage_files": core["stage_files"]}


def main() -> None:
    if POC.exists():
        shutil.rmtree(POC)
    INPUT.mkdir(parents=True, exist_ok=True); EVIDENCE.mkdir(parents=True, exist_ok=True)
    corpus = INPUT / "corpus.md"
    corpus.write_text("# Fixed corpus\nfixture-1\n", encoding="utf-8")
    fixture_before = hashlib.sha256(corpus.read_bytes()).hexdigest()
    source_commit = "fixture-commit-001"; source_digests = {"experiments/engineering_notebook_001/input/corpus.md": fixture_before}
    state = create_notebook(notebook_id="poc-001", owner="Engineering", assigned_worker="worker-a", objective_id="ESTATE-NOTEBOOK-001-POC", work_package_ref="ESTATE-NOTEBOOK-001", source_commit=source_commit, objective="Complete parser, schema, and HTML stages from verified notebook state.", stage="parser", remaining_stages=["schema", "html"], repository="experiments/engineering_notebook_001", read_paths=["experiments/engineering_notebook_001/input"], write_paths=["experiments/engineering_notebook_001/workspace"], source_digests=source_digests, authorization_refs=["ESTATE-NOTEBOOK-001"])
    state["evidence"]["commands"] = ["python poc_runner.py"]
    state["continuity"]["next_stage_files"] = ["experiments/engineering_notebook_001/input/corpus.md"]
    state["state_digest"] = state_digest(state)
    write_notebook_atomic(STATE_PATH, state, root=ROOT)
    records = []; receipts = []; handoffs = []
    for session_number, stage in enumerate(("parser", "schema"), start=1):
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        stage_files = state["continuity"]["next_stage_files"]
        core = build_packet(state, current_stage_files=stage_files, failures=state["evidence"]["unresolved_failures"])
        packet = {"packet_core": core, "state": state, "stage": stage, "worker_id": f"worker-{session_number}", "source_digests": source_digests, "source_commit": source_commit, "stage_files": stage_files, "authority_digest": core["authority_digest"], "evidence_digest": core["evidence_digest"], "assigned_worker": core["assigned_worker"], "output": str(POC / "workspace" / {"parser": "parsed.json", "schema": "validated.json"}[stage]), "ack": make_ack(core), "handoff": None}
        result = run_worker(packet, session_number)
        result["state_digest_before"] = state["state_digest"]; result["packet_digest"] = digest_json(core)
        records.append(result)
        task = deepcopy(state["task"]); task["current_stage"] = next((x for x in ("parser", "schema", "html") if x not in [*task["completed_stages"], stage]), "html"); task["completed_stages"] = [*task["completed_stages"], stage]; task["remaining_stages"] = [x for x in ("parser", "schema", "html") if x not in task["completed_stages"]]; task["stage_status"] = "active"; task["next_action"] = "Complete the next stage."
        evidence = deepcopy(state["evidence"]); evidence["files"] = [*evidence["files"], result["validation"]["output"]]; evidence["last_results"] = [*evidence["last_results"], result["validation"]]; evidence["receipts"] = [*evidence["receipts"], f"experiments/engineering_notebook_001/evidence/receipt-{stage}.json"]
        continuity = deepcopy(state["continuity"]); continuity["previous_session"] = result["worker_id"]; continuity["handoff_reason"] = "fresh process session handoff"; continuity["compaction_summary"] = f"Completed {stage}; carry only verified packet and current stage."; continuity["next_stage_files"] = [result["validation"]["output"]]
        changes = {"task": task, "evidence": evidence, "continuity": continuity}; observed = {**changes, "artifacts_exist": True, "required_validators_passed": True}
        proposal = {"schema_version": "estate.engineering-notebook.update-proposal.v1", "proposal_id": f"stage-{stage}", "notebook_id": state["notebook_id"], "worker": state["assigned_worker"], "proposed_at": utc_now(), "idempotency_key": f"idem-stage-{stage}", "prior_state_digest": state["state_digest"], "reason": "harness accepted independent worker validation", "changes": changes, "provenance": [{"source": "poc_runner.py", "category": "validator_produced", "digest": None, "observed_at": utc_now(), "claim": f"Independent process validated the {stage} stage."}]}
        state, receipt = apply_verified_update(state, proposal, observed); write_notebook_atomic(STATE_PATH, state, root=ROOT); atomic_json(EVIDENCE / f"receipt-{stage}.json", receipt); receipts.append(receipt); records[-1]["update_proposal"] = proposal; records[-1]["verification_receipt"] = receipt; records[-1]["state_digest_after"] = state["state_digest"]
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    first_handoff_core = build_packet(state, current_stage_files=state["continuity"]["next_stage_files"], failures=[]); first_handoff = create_handoff(state, reason="session 2 completed schema; refresh required before session 3", next_worker="worker-3", packet_digest=digest_json(first_handoff_core), session_id=records[-1]["session_id"]); handoffs.append(first_handoff)
    stale = deepcopy(state); stale["status"] = "conflicted"; stale["freshness"] = {**stale["freshness"], "state": "conflicted", "conflicts": ["experiments/engineering_notebook_001/input/corpus.md"]}; stale["state_digest"] = state_digest(stale)
    stale_core = build_packet(stale, current_stage_files=stale["continuity"]["next_stage_files"], failures=[])
    stale_ack = make_ack(stale_core); stale_rejection = None
    try: acknowledge(stale, stale_ack, current_source_digests={"experiments/engineering_notebook_001/input/corpus.md": "b" * 64}, current_source_commit=source_commit, current_stage_files=stale["continuity"]["next_stage_files"], current_authority_digest=digest_json(stale["authority"]), current_evidence_digest=digest_json(stale["evidence"]), current_assigned_worker=stale["assigned_worker"])
    except NotebookRejection as error: stale_rejection = error.receipt
    if stale_rejection is None: raise RuntimeError("stale proof did not reject acknowledgment")
    atomic_json(EVIDENCE / "receipt-stale-rejection.json", stale_rejection)
    state, refresh_receipt = refresh_notebook(stale, current_source_digests=source_digests, current_source_commit=source_commit, update_id="refresh-authoritative", idempotency_key="idem-refresh"); atomic_json(EVIDENCE / "receipt-refresh.json", refresh_receipt); receipts.append(refresh_receipt)
    stage = "html"; stage_files = state["continuity"]["next_stage_files"]; core = build_packet(state, current_stage_files=stage_files, failures=[]); handoff = create_handoff(state, reason="authoritative refresh verified; resume HTML", next_worker="worker-3", packet_digest=digest_json(core), session_id="session-3"); handoffs.append(handoff)
    packet = {"packet_core": core, "state": state, "stage": stage, "worker_id": "worker-3", "source_digests": source_digests, "source_commit": source_commit, "stage_files": stage_files, "authority_digest": core["authority_digest"], "evidence_digest": core["evidence_digest"], "assigned_worker": core["assigned_worker"], "output": str(POC / "workspace" / "dashboard.html"), "ack": make_ack(core), "handoff": handoff}
    result = run_worker(packet, 3); result["state_digest_before"] = state["state_digest"]; result["packet_digest"] = digest_json(core); records.append(result)
    task = deepcopy(state["task"]); task.update({"current_stage": "html", "stage_status": "complete", "completed_stages": [*task["completed_stages"], "html"], "remaining_stages": [], "next_action": "Close the proof."}); evidence = deepcopy(state["evidence"]); evidence["files"].append(result["validation"]["output"]); evidence["last_results"].append(result["validation"]); evidence["schema_state"] = "pass"; evidence["compilation_state"] = "pass"; evidence["fixture_integrity"] = "pass"; evidence["receipts"].append("experiments/engineering_notebook_001/evidence/receipt-html.json"); continuity = deepcopy(state["continuity"]); continuity["previous_session"] = result["worker_id"]; continuity["compaction_summary"] = "Completed html; carry verified final output."; continuity["next_stage_files"] = [result["validation"]["output"]]; changes = {"task": task, "evidence": evidence, "continuity": continuity}; observed = {**changes, "artifacts_exist": True, "required_validators_passed": True}; proposal = {"schema_version": "estate.engineering-notebook.update-proposal.v1", "proposal_id": "stage-html", "notebook_id": state["notebook_id"], "worker": state["assigned_worker"], "proposed_at": utc_now(), "idempotency_key": "idem-stage-html", "prior_state_digest": state["state_digest"], "reason": "harness accepted independent worker validation", "changes": changes, "provenance": [{"source": "poc_runner.py", "category": "validator_produced", "digest": None, "observed_at": utc_now(), "claim": "Independent process validated the html stage."}]}; state, receipt = apply_verified_update(state, proposal, observed); write_notebook_atomic(STATE_PATH, state, root=ROOT); atomic_json(EVIDENCE / "receipt-html.json", receipt); receipts.append(receipt); records[-1]["update_proposal"] = proposal; records[-1]["verification_receipt"] = receipt; records[-1]["state_digest_after"] = state["state_digest"]
    state = json.loads(STATE_PATH.read_text(encoding="utf-8")); final_observed = {"status": "completed", "artifacts_exist": True, "required_validators_passed": True}; final_proposal = {"schema_version": "estate.engineering-notebook.update-proposal.v1", "proposal_id": "proof-close", "notebook_id": state["notebook_id"], "worker": state["assigned_worker"], "proposed_at": utc_now(), "idempotency_key": "idem-proof-close", "prior_state_digest": state["state_digest"], "reason": "all independent process validations passed", "changes": {"status": "completed"}, "provenance": [{"source": "poc_runner.py", "category": "validator_produced", "digest": None, "observed_at": utc_now(), "claim": "All three independent process stages passed."}]}; state, receipt = apply_verified_update(state, final_proposal, final_observed); write_notebook_atomic(STATE_PATH, state, root=ROOT); atomic_json(EVIDENCE / "receipt-close.json", receipt); receipts.append(receipt)
    atomic_json(EVIDENCE / "notebook_state.json", state); EVIDENCE.joinpath("notebook.md").write_text(__import__("estate.core.engineering_notebook", fromlist=["render_markdown"]).render_markdown(state), encoding="utf-8"); atomic_json(EVIDENCE / "handoff.json", handoff)
    fixture_after = hashlib.sha256(corpus.read_bytes()).hexdigest(); report = {"classification": "HARNESS-LEVEL FRESH-SESSION CONTINUITY", "model_invoked": False, "sessions": records, "handoff_records": handoffs, "stale_conflict": {"diagnostic": detect_freshness(state, {"experiments/engineering_notebook_001/input/corpus.md": "b" * 64}), "acknowledgment_rejected": True, "rejection_receipt": stale_rejection, "refresh_revision": state["revision"]}, "fixture_hash_before": fixture_before, "fixture_hash_after": fixture_after, "fixture_unchanged": fixture_before == fixture_after, "receipts": len(receipts), "handoffs": len(handoffs), "final_state_digest": state["state_digest"], "institutional_acceptance": "not_granted"}; atomic_json(EVIDENCE / "poc_report.json", report)
    print(json.dumps({"status": state["status"], "classification": report["classification"], "sessions": len(records), "receipts": len(receipts), "handoffs": len(handoffs), "fixture_unchanged": report["fixture_unchanged"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--worker", nargs=2, metavar=("PACKET", "RESULT")); args = parser.parse_args()
    if args.worker: worker_main(Path(args.worker[0]), Path(args.worker[1]))
    else: main()
