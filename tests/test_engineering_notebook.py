import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from estate.core.engineering_notebook import (
    NotebookConflict,
    NotebookCorruption,
    NotebookError,
    NotebookRejection,
    acknowledge,
    apply_verified_update,
    archive_notebook,
    build_packet,
    close_notebook,
    create_handoff,
    create_notebook,
    detect_freshness,
    digest_json,
    load_notebook,
    refresh_notebook,
    render_markdown,
    state_digest,
    utc_now,
    validate_notebook,
    write_notebook_atomic,
    write_receipt_append_only,
)


SOURCE = {"input/manifest.json": "a" * 64}


def notebook():
    return create_notebook(
        notebook_id="nb-test-001", owner="Engineering", assigned_worker="worker-a",
        objective_id="OBJ-001", work_package_ref="ESTATE-NOTEBOOK-001",
        source_commit="commit-1", objective="Complete a bounded three-stage proof.",
        stage="parser", remaining_stages=["schema", "html"], repository="workspace",
        read_paths=["input"], write_paths=["workspace"], source_digests=SOURCE,
        authorization_refs=["ESTATE-NOTEBOOK-001"],
    )


def acknowledge_packet(state, *, stage_files=None, source_digests=None, source_commit="commit-1", **overrides):
    stage_files = stage_files or ["input/corpus.md"]
    packet = build_packet(state, current_stage_files=stage_files, failures=[])
    ack = {"notebook_id": packet["notebook_id"], "objective": packet["objective"], "stage": packet["current_stage"], "permitted_repository": packet["permitted_repository"], "permitted_write_paths": packet["permitted_write_paths"], "blocker": packet["current_blocker"], "required_validation": packet["required_validation"], "prohibited_actions": packet["prohibited_actions"], "stage_files": packet["stage_files"]}
    ack.update(overrides)
    return acknowledge(state, ack, current_source_digests=source_digests or SOURCE, current_source_commit=source_commit, current_stage_files=stage_files, current_authority_digest=digest_json(state["authority"]), current_evidence_digest=digest_json(state["evidence"]), current_assigned_worker=state["assigned_worker"])


def proposal(state, changes, *, proposal_id="p1", key="k1", observed=None, category="validator_produced"):
    observed = observed if observed is not None else changes
    return {"schema_version": "estate.engineering-notebook.update-proposal.v1", "proposal_id": proposal_id, "notebook_id": state["notebook_id"], "worker": state["assigned_worker"], "proposed_at": utc_now(), "idempotency_key": key, "prior_state_digest": state["state_digest"], "reason": "validator observed bounded change", "changes": changes, "provenance": [{"source": "validator", "category": category, "digest": None, "observed_at": utc_now(), "claim": "Validator produced the observed bounded fact."}]}


def test_creation_packet_and_exact_acknowledgment():
    state = notebook()
    assert acknowledge_packet(state)
    packet = build_packet(state, current_stage_files=["input/corpus.md"], failures=[])
    assert packet["state_digest"] == state["state_digest"]


def test_missing_authorization_reference_is_rejected():
    with pytest.raises(NotebookError):
        create_notebook(notebook_id="x", owner="Engineering", assigned_worker="worker-a", objective_id="o", work_package_ref="wp", source_commit="c", objective="obj", stage="parser", remaining_stages=[], repository="repo", read_paths=["input"], write_paths=["workspace"], source_digests=SOURCE, authorization_refs=[])


@pytest.mark.parametrize("field,value", [("objective", "wrong"), ("stage", "wrong"), ("permitted_repository", ["other"]), ("permitted_write_paths", ["other"]), ("blocker", "wrong"), ("required_validation", ["wrong"]), ("prohibited_actions", ["unsafe"])])
def test_acknowledgment_mismatch_rejects_with_structured_receipt(field, value):
    state = notebook(); before = deepcopy(state)
    with pytest.raises(NotebookRejection) as error:
        acknowledge_packet(state, **{field: value})
    assert error.value.receipt["status"] == "rejected"
    assert error.value.receipt["resulting_state_digest"] == before["state_digest"]
    assert state == before


def test_stale_digest_rejects_execution_and_refreshes_authoritatively():
    state = notebook(); before = state["state_digest"]
    with pytest.raises(NotebookRejection) as error:
        acknowledge_packet(state, source_digests={"input/manifest.json": "b" * 64})
    assert "freshness" in error.value.receipt["rejected_fields"]
    assert state["state_digest"] == before
    refreshed, receipt = refresh_notebook(state, current_source_digests=SOURCE, current_source_commit="commit-1", update_id="refresh-1", idempotency_key="refresh-key")
    assert refreshed["revision"] == 1 and refreshed["freshness"]["state"] == "current"
    assert receipt["prior_state_digest"] == before
    assert acknowledge_packet(refreshed)


def test_stale_age_conflict_is_visible_and_fail_closed():
    state = notebook(); state["last_verified_at"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat().replace("+00:00", "Z"); state["state_digest"] = state_digest(state)
    assert detect_freshness(state, SOURCE)["state"] == "stale"
    with pytest.raises(NotebookRejection):
        acknowledge_packet(state)


def test_worker_cannot_refresh_conflict_or_change_scope():
    state = notebook()
    bad = proposal(state, {"status": "current"}, observed={"status": "current"})
    state["status"] = "conflicted"; state["state_digest"] = state_digest(state); bad["prior_state_digest"] = state["state_digest"]
    with pytest.raises(NotebookRejection):
        apply_verified_update(state, bad, {"status": "current"})
    with pytest.raises(NotebookRejection):
        apply_verified_update(notebook(), {**proposal(notebook(), {"constraints": {}}, observed={"constraints": {}}), "changes": {"constraints": {}}}, {"constraints": {}})


def test_updates_require_observed_trusted_facts_and_preserve_state_on_rejection():
    state = notebook(); before = state["state_digest"]
    empty = proposal(state, {"status": "current"}, observed={}); empty["provenance"] = []
    with pytest.raises(NotebookRejection) as error:
        apply_verified_update(state, empty, {})
    assert error.value.receipt["status"] == "rejected" and state["state_digest"] == before
    worker_only = proposal(state, {"status": "current"}, observed={"status": "current"}, category="worker_proposed")
    with pytest.raises(NotebookRejection):
        apply_verified_update(state, worker_only, {"status": "current"})


def test_completion_requires_terminal_evidence_and_retry_cannot_roll_back():
    state = notebook()
    complete_task = deepcopy(state["task"]); complete_task.update({"stage_status": "complete", "completed_stages": ["parser", "schema", "html"], "remaining_stages": [], "current_stage": "html"})
    complete_evidence = deepcopy(state["evidence"]); complete_evidence.update({"files": ["workspace/output.json"], "last_results": [{"stage": "html", "output": "workspace/output.json", "validation": "pass"}], "schema_state": "pass", "compilation_state": "pass", "fixture_integrity": "pass"})
    bad = proposal(state, {"status": "completed"}, observed={"status": "completed", "artifacts_exist": True, "required_validators_passed": True})
    with pytest.raises(NotebookRejection):
        apply_verified_update(state, bad, {"status": "completed", "artifacts_exist": True, "required_validators_passed": True})
    changes = {"task": complete_task, "evidence": complete_evidence, "status": "completed"}
    observed = {**changes, "artifacts_exist": True, "required_validators_passed": True}
    updated, _ = apply_verified_update(state, proposal(state, changes, proposal_id="complete", key="complete-key", observed=observed), observed)
    assert updated["status"] == "completed"
    exhausted = notebook(); exhausted["task"]["repair_count"] = exhausted["task"]["retry_limit"]; exhausted["task"]["stage_status"] = "blocked"; exhausted["task"]["current_blocker"] = "retry limit reached"; exhausted["task"]["blocking_severity"] = "high"; exhausted["status"] = "blocked"; exhausted["state_digest"] = state_digest(exhausted)
    with pytest.raises(NotebookRejection):
        acknowledge_packet(exhausted)


def test_replay_conflict_and_stale_prior_digest_are_safe():
    state = notebook(); p = proposal(state, {"status": "current"}, observed={"status": "current"}); updated, receipt = apply_verified_update(state, p, {"status": "current"})
    replayed, replay_receipt = apply_verified_update(updated, p, {"status": "current"})
    assert replayed == updated and replay_receipt["status"] == "replayed"
    conflict = {**p, "proposal_id": "other", "idempotency_key": "other-key"}
    with pytest.raises(NotebookRejection): apply_verified_update(updated, conflict, {"status": "current"})
    stale = proposal(state, {"status": "current"}, proposal_id="stale", key="stale-key", observed={"status": "current"}); stale["prior_state_digest"] = "b" * 64
    with pytest.raises(NotebookRejection): apply_verified_update(updated, stale, {"status": "current"})
    assert receipt["resulting_state_digest"] == updated["state_digest"]


def test_atomic_persistence_corruption_and_interrupted_write(tmp_path):
    state = notebook(); path = tmp_path / "state.json"; write_notebook_atomic(path, state, root=tmp_path); assert load_notebook(path, root=tmp_path) == state
    original = path.read_text(encoding="utf-8")
    with pytest.raises(OSError): write_notebook_atomic(path, state, root=tmp_path, simulate_interrupt=True)
    assert path.read_text(encoding="utf-8") == original
    path.write_text("{bad", encoding="utf-8")
    with pytest.raises(NotebookCorruption): load_notebook(path, root=tmp_path)


def test_duplicate_receipt_is_safe_noop_and_conflicting_receipt_rejected(tmp_path):
    receipt = {"receipt_id": "r1", "status": "accepted"}
    path = tmp_path / "receipt.json"
    write_receipt_append_only(path, receipt, root=tmp_path)
    write_receipt_append_only(path, receipt, root=tmp_path)
    with pytest.raises(NotebookError): write_receipt_append_only(path, {"receipt_id": "r2"}, root=tmp_path)


def test_archive_and_markdown_reflect_verified_state(tmp_path):
    state = notebook(); task = deepcopy(state["task"]); task.update({"stage_status": "complete", "current_stage": "parser", "completed_stages": ["parser"], "remaining_stages": []}); evidence = deepcopy(state["evidence"]); evidence.update({"files": ["workspace/output.json"], "last_results": [{"stage": "parser", "output": "workspace/output.json", "validation": "pass"}], "schema_state": "pass", "compilation_state": "pass", "fixture_integrity": "pass"}); observed={"task":task,"evidence":evidence,"status":"completed","artifacts_exist":True,"required_validators_passed":True}; completed,_=apply_verified_update(state, proposal(state,{"task":task,"evidence":evidence,"status":"completed"},proposal_id="done",key="done-key",observed=observed),observed)
    archived = archive_notebook(completed, tmp_path / "archive.json", root=tmp_path, update_id="archive-1", idempotency_key="archive-key")
    assert archived["status"] == "archived" and "State digest" in render_markdown(archived)


def test_handoff_and_schema_examples_are_convergent():
    state = notebook(); handoff = create_handoff(state, reason="handoff", next_worker="worker-b", packet_digest=digest_json(build_packet(state, current_stage_files=["input/corpus.md"], failures=[])), session_id="session-1")
    root = __import__("pathlib").Path(__file__).parents[1] / "schemas" / "notebook"
    for path in root.glob("*.json"):
        schema = json.loads(path.read_text(encoding="utf-8")); Draft202012Validator.check_schema(schema)
    assert handoff["state_digest"] == state["state_digest"]
    with pytest.raises(NotebookError): create_handoff(state, reason="handoff", next_worker="worker-b", packet_digest="not-a-digest")


def test_paths_timestamps_nested_secrets_and_institutional_acceptance_rejected():
    state = notebook(); state["constraints"]["permitted_write_paths"] = ["foo/../bar"]
    with pytest.raises(NotebookError): validate_notebook(state)
    state = notebook(); state["evidence"]["last_results"] = [{"stage": "x", "output": "x", "validation": "pass", "note": "password=leak"}]
    with pytest.raises(NotebookError): validate_notebook(state)
    state = notebook(); state["created_at"] = "bad"; state["state_digest"] = state_digest(state)
    with pytest.raises(NotebookError): validate_notebook(state)
    state = notebook(); state["institutional_acceptance"] = "accepted"
    with pytest.raises(NotebookError): validate_notebook(state, verify_digest=False)


def _protected_proposal(state, root, mutate, *, proposal_id):
    candidate = deepcopy(state)
    mutate(candidate)
    changes = {root: candidate[root]}
    return proposal(state, changes, proposal_id=proposal_id, key=f"key-{proposal_id}", observed=changes)


@pytest.mark.parametrize(
    ("root", "mutate"),
    [
        ("authority", lambda s: s["authority"].update(merge=True)),
        ("assigned_worker", lambda s: s.update(assigned_worker="worker-b")),
        ("assigned_provider", lambda s: s.update(assigned_provider="provider-b")),
        ("institutional_acceptance", lambda s: s.update(institutional_acceptance="granted")),
        ("constraints", lambda s: s["constraints"].update(permitted_write_paths=["workspace", "outside"])),
        ("constraints", lambda s: s["constraints"].update(permitted_read_paths=["input", "outside"])),
        ("constraints", lambda s: s["constraints"].update(permitted_repository=["other-repository"])),
        ("source_commit", lambda s: s.update(source_commit="other-commit")),
        ("freshness", lambda s: s["freshness"].update(source_digests={"input/manifest.json": "b" * 64})),
        ("task", lambda s: s["task"].update(retry_limit=99)),
        ("evidence", lambda s: s["evidence"].update(commands=["unsafe validation command"])),
        ("task", lambda s: s["task"].update(stop_condition="never stop")),
        ("provenance", lambda s: s.update(provenance=[])),
        ("workspace_identity", lambda s: s.update(workspace_identity="other-workspace")),
        ("benchmark_identity", lambda s: s.update(benchmark_identity="other-benchmark")),
        ("model_identity", lambda s: s.update(model_identity="other-model")),
        ("status", lambda s: s.update(status="archived")),
    ],
)
def test_protected_field_paths_are_rejected_atomically(root, mutate):
    state = notebook()
    before = json.dumps(state, sort_keys=True)
    before_revision = state["revision"]
    before_digest = state["state_digest"]
    bad = _protected_proposal(state, root, mutate, proposal_id=f"protected-{root}-{before_revision}")

    with pytest.raises(NotebookRejection) as error:
        apply_verified_update(state, bad, bad["changes"])

    receipt = error.value.receipt
    assert receipt["status"] == "rejected"
    assert receipt["rejected_fields"]
    assert receipt["accepted_fields"] == []
    assert receipt["revision"] == before_revision
    assert receipt["state_digest"] == before_digest
    assert receipt["resulting_state_digest"] == before_digest
    assert json.dumps(state, sort_keys=True) == before


def test_nested_deletion_and_type_mutation_are_rejected():
    for mutation, expected_path in (
        (lambda s: s["authority"].pop("merge"), "authority.merge"),
        (lambda s: s["task"].update(retry_limit="unbounded"), "task.retry_limit"),
    ):
        state = notebook(); candidate = deepcopy(state); mutation(candidate)
        root = expected_path.split(".")[0]
        bad = proposal(state, {root: candidate[root]}, proposal_id=f"nested-{root}", key=f"nested-key-{root}", observed={root: candidate[root]})
        with pytest.raises(NotebookRejection) as error:
            apply_verified_update(state, bad, bad["changes"])
        assert expected_path in error.value.receipt["rejected_fields"]
        assert state["revision"] == 0


def test_mixed_allowed_and_protected_update_is_all_or_nothing():
    state = notebook(); before = json.dumps(state, sort_keys=True)
    bad = proposal(state, {"status": "current", "authority": {**state["authority"], "merge": True}}, observed={"status": "current", "authority": {**state["authority"], "merge": True}})
    with pytest.raises(NotebookRejection) as error:
        apply_verified_update(state, bad, bad["changes"])
    assert "status" in error.value.receipt["rejected_fields"]
    assert "authority.merge" in error.value.receipt["rejected_fields"]
    assert json.dumps(state, sort_keys=True) == before


def test_blocker_erasure_requires_observed_resolution_evidence():
    state = notebook(); state["task"].update(current_blocker="validation failed", blocking_severity="high"); state["state_digest"] = state_digest(state)
    candidate = deepcopy(state); candidate["task"]["current_blocker"] = "none"; candidate["task"]["blocking_severity"] = "none"
    bad = proposal(state, {"task": candidate["task"]}, observed={"task": candidate["task"]})
    with pytest.raises(NotebookRejection) as error:
        apply_verified_update(state, bad, bad["changes"])
    assert "blocker" in str(error.value).lower()
    assert state["task"]["current_blocker"] == "validation failed"


def test_rejected_replay_remains_rejected_and_accepted_receipt_lists_leaf_paths():
    state = notebook(); before = json.dumps(state, sort_keys=True)
    bad = proposal(state, {"authority": {**state["authority"], "merge": True}}, proposal_id="rejected-replay", key="rejected-replay-key")
    with pytest.raises(NotebookRejection) as first:
        apply_verified_update(state, bad, bad["changes"])
    with pytest.raises(NotebookRejection) as second:
        apply_verified_update(state, bad, bad["changes"])
    assert first.value.receipt["status"] == second.value.receipt["status"] == "rejected"
    assert json.dumps(state, sort_keys=True) == before
    updated, receipt = apply_verified_update(state, proposal(state, {"status": "current"}, proposal_id="accepted-status", key="accepted-status-key"), {"status": "current"})
    assert receipt["accepted_fields"] == ["status"]
    assert receipt["prior_state_digest"] == state["state_digest"]
    assert receipt["resulting_state_digest"] == updated["state_digest"]
