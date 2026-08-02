import json
from datetime import datetime, timedelta, timezone

import pytest

from estate.core.engineering_notebook import (
    NotebookConflict,
    NotebookError,
    acknowledge,
    apply_verified_update,
    build_packet,
    create_handoff,
    create_notebook,
    detect_freshness,
    digest_json,
    render_markdown,
    validate_notebook,
    validate_update_proposal,
    utc_now,
)


def notebook():
    return create_notebook(
        notebook_id="nb-test-001", owner="Engineering", assigned_worker="worker-a",
        objective_id="OBJ-001", work_package_ref="ESTATE-NOTEBOOK-001",
        source_commit="abc123", objective="Complete a bounded three-stage proof.",
        stage="parser", remaining_stages=["schema", "html"], repository="workspace",
        read_paths=["input"], write_paths=["workspace"], source_digests={"input/manifest.json": "a" * 64},
    )


def test_valid_creation_and_packet():
    state = notebook()
    packet = build_packet(state, current_stage_files=["input/corpus.md"], failures=[])
    assert packet["current_stage"] == "parser"
    assert acknowledge(state, {"notebook_id": "nb-test-001", "objective": packet["objective"], "stage": "parser", "permitted_repository": ["workspace"], "permitted_write_paths": ["workspace"], "blocker": "none", "required_validation": [], "prohibited_actions": state["constraints"]["prohibited_actions"]})
    with pytest.raises(NotebookError):
        bad = dict(packet)
        bad["permitted_write_paths"] = ["other"]
        acknowledge(state, {"notebook_id": bad["notebook_id"], "objective": bad["objective"], "stage": bad["current_stage"], "permitted_repository": bad["permitted_repository"], "permitted_write_paths": bad["permitted_write_paths"], "blocker": bad["current_blocker"], "required_validation": bad["required_validation"], "prohibited_actions": bad["prohibited_actions"]})


def test_unknown_fields_and_unsafe_paths_rejected():
    state = notebook()
    state["unexpected"] = True
    with pytest.raises(NotebookError):
        validate_notebook(state)
    state = notebook()
    state["constraints"]["permitted_write_paths"] = ["../outside"]
    with pytest.raises(NotebookError):
        validate_notebook(state)


def test_stale_and_conflicted_fail_closed():
    state = notebook()
    old = datetime.now(timezone.utc) - timedelta(hours=2)
    state["last_verified_at"] = old.isoformat().replace("+00:00", "Z")
    assert detect_freshness(state, state["freshness"]["source_digests"])["state"] == "stale"
    state["freshness"]["state"] = "conflicted"
    with pytest.raises(NotebookConflict):
        acknowledge(state, {"notebook_id": "nb-test-001", "objective": state["task"]["original_objective"], "stage": "parser", "permitted_repository": ["workspace"], "permitted_write_paths": ["workspace"], "blocker": "none", "required_validation": [], "prohibited_actions": state["constraints"]["prohibited_actions"]})


def test_update_accepts_observed_fact_and_rejects_scope_widening():
    state = notebook()
    proposal = {"schema_version": "estate.engineering-notebook.update-proposal.v1", "proposal_id": "p1", "notebook_id": "nb-test-001", "worker": "worker-a", "proposed_at": utc_now(), "reason": "validator observed parser completion", "changes": {"status": "current"}, "provenance": [{"source": "validator", "category": "validator_produced", "digest": None, "observed_at": utc_now(), "claim": "Parser validation passed."}]}
    updated, receipt = apply_verified_update(state, proposal, {"status": "current"})
    assert updated["status"] == "current" and receipt["status"] == "accepted"
    proposal["changes"] = {"constraints": {}}
    with pytest.raises(NotebookError):
        validate_update_proposal(proposal, state, {})


def test_false_completion_and_invalid_worker_claim_rejected():
    state = notebook()
    proposal = {"schema_version": "estate.engineering-notebook.update-proposal.v1", "proposal_id": "p2", "notebook_id": "nb-test-001", "worker": "worker-a", "proposed_at": utc_now(), "reason": "claim", "changes": {"status": "completed"}, "provenance": []}
    with pytest.raises(NotebookError):
        validate_update_proposal(proposal, state, {"status": "blocked"})
    state["task"]["repair_count"] = 4
    with pytest.raises(NotebookError):
        validate_notebook(state)


def test_redaction_markdown_handoff_and_digest():
    state = notebook()
    state["task"]["current_blocker"] = "password=do-not-print"
    # Secret-like content is never accepted into the state.
    with pytest.raises(NotebookError):
        validate_notebook(state)
    state = notebook()
    text = render_markdown(state)
    assert "Repository canon" in text and "nb-test-001" in text
    handoff = create_handoff(state, reason="context compaction", next_worker="worker-b", packet_digest=digest_json(build_packet(state, current_stage_files=[], failures=[])))
    assert handoff["resume_required"] is True


def test_all_schemas_are_closed_and_parseable():
    from jsonschema import Draft202012Validator
    from pathlib import Path
    root = Path(__file__).parents[1]
    for path in (root / "schemas" / "notebook").glob("*.json"):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
