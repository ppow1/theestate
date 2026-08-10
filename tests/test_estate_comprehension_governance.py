import json
import sqlite3
from pathlib import Path

import pytest

import estate.core.estate_knowledge_store as store
import estate.core.estate_comprehension_governance as governance


ROOT = Path(__file__).resolve().parents[1]


def _setup(tmp_path, monkeypatch, *, purpose="Estate bounded comprehension result v1", owner="estate", tags=("SCHEMA",)):
    db = tmp_path / "projection.sqlite3"
    monkeypatch.setattr(store, "database_path", lambda root=None: db)
    monkeypatch.setattr(governance, "database_path", lambda root=None: db)
    with store.connect(ROOT) as connection:
        asset_id = "asset:test-governed"
        content_hash = "hash-current"
        connection.execute("INSERT INTO assets(asset_id,current_path,repository,current_source_revision,current_git_blob,current_content_hash,file_type,extension,size_bytes,classification,scan_status,comprehension_status,purpose_summary,owner,unknown_reason,first_seen,last_seen,last_scanned,last_comprehended,source_kind,current_state,scope_policy,provider_content_allowed) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (asset_id, "schemas/troubleshooting/comprehension_result_v1.schema.json", "https://github.com/ppow1/theestate.git", "rev-current", None, content_hash, "schema", ".json", 10, "estate_internal", "CLASSIFIED", "PARTIAL", purpose, owner, None, "now", "now", "now", None, "DETERMINISTIC", "CURRENT", "STRUCTURAL_SCAN", 1))
        if owner:
            connection.execute("INSERT INTO ownership(asset_id,owner,confidence,source_kind,source_ref,source_revision,is_current) VALUES(?,?,?,?,?,?,1)", (asset_id, owner, "HIGH", "DETERMINISTIC", "tests/test_estate_comprehension_governance.py", "rev-current"))
        for tag in tags:
            connection.execute("INSERT INTO tags(asset_id,tag,source_kind,confidence,source_ref,source_revision,current_state) VALUES(?,?,?,?,?,?,?)", (asset_id, tag, "DETERMINISTIC", "HIGH", "schemas/troubleshooting/comprehension_result_v1.schema.json", "rev-current", "CURRENT"))
        result_id = "result:test"
        batch_id = "batch:test"
        interpretation_id = "interpretation:test"
        candidate = {"asset_id": asset_id, "lifecycle": "CANDIDATE", "purpose": purpose, "owner_candidate": owner, "summary": None, "tags": list(tags), "evidence_refs": [asset_id], "unresolved_questions": []}
        connection.execute("INSERT INTO comprehension_batches(batch_id,scope_id,source_revision,selection_reason,created_at,updated_at,provider_type,provider_model,worker_identity,state,attempt_count,result_state) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (batch_id, "scope", "rev-candidate", "test", "now", "now", "local_ai", "test-model", "local-worker", "COMPLETED", 1, "ACCEPTED_CANDIDATE"))
        connection.execute("INSERT INTO comprehension_results(result_id,batch_id,provider_type,provider_model,worker_identity,source_revision,input_hash,output_hash,output_json,validation_state,created_at,human_review_required) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (result_id, batch_id, "local_ai", "test-model", "local-worker", "rev-candidate", "input", "output", json.dumps({"items": [candidate]}), "VALIDATED_CANDIDATE", "now", 1))
        connection.execute("INSERT INTO candidate_interpretations(interpretation_id,result_id,batch_id,asset_id,candidate_json,lifecycle,provider_type,provider_model,worker_identity,source_revision,content_hash,created_at,validation_state) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (interpretation_id, result_id, batch_id, asset_id, json.dumps(candidate), "CANDIDATE", "local_ai", "test-model", "local-worker", "rev-candidate", content_hash, "now", "CANDIDATE_REVIEW_REQUIRED"))
    return asset_id, interpretation_id


def test_assertion_extraction_corroboration_review_and_idempotent_application(tmp_path, monkeypatch):
    asset_id, interpretation_id = _setup(tmp_path, monkeypatch)
    assert governance.extract_assertions(ROOT, interpretation_id=interpretation_id)["assertions_created"] == 3
    assert governance.extract_assertions(ROOT, interpretation_id=interpretation_id)["assertions_created"] == 0
    result = governance.corroborate(ROOT, asset_id=asset_id)
    assert result["counts"]["CORROBORATED"] == 2
    assert result["counts"]["PARTIALLY_CORROBORATED"] == 1
    reviewed = governance.review_batch(ROOT, asset_prefix="schemas")
    assert reviewed["reviewed"] == 3
    eligible = governance.eligible(ROOT)
    assert eligible["eligible_count"] == 3
    applied = governance.apply_eligible(ROOT, actor_id="deterministic-review-policy", actor_type="deterministic_policy")
    assert applied["applied_count"] == 3
    assert governance.apply_eligible(ROOT, actor_id="deterministic-review-policy", actor_type="deterministic_policy")["applied_count"] == 0
    with store.connect(ROOT, create=False) as connection:
        assert connection.execute("SELECT comprehension_status FROM assets WHERE asset_id=?", (asset_id,)).fetchone()[0] == "COMPREHENDED"
        assert connection.execute("SELECT COUNT(*) FROM application_history").fetchone()[0] == 3


def test_provider_cannot_self_approve_and_contradiction_is_rejected(tmp_path, monkeypatch):
    asset_id, interpretation_id = _setup(tmp_path, monkeypatch, owner="authoritative-owner")
    with store.connect(ROOT, create=False) as connection:
        candidate = json.loads(connection.execute("SELECT candidate_json FROM candidate_interpretations WHERE interpretation_id=?", (interpretation_id,)).fetchone()[0])
        candidate["owner_candidate"] = "wrong-owner"
        connection.execute("UPDATE candidate_interpretations SET candidate_json=? WHERE interpretation_id=?", (json.dumps(candidate), interpretation_id))
    governance.extract_assertions(ROOT, interpretation_id=interpretation_id)
    governance.corroborate(ROOT, asset_id=asset_id)
    governance.review_batch(ROOT, asset_prefix="schemas")
    with store.connect(ROOT, create=False) as connection:
        assertion_id = connection.execute("SELECT assertion_id FROM candidate_assertions WHERE assertion_kind='OWNER'").fetchone()[0]
    with pytest.raises(ValueError, match="cannot approve"):
        governance.decide(ROOT, assertion_id, decision="APPROVE_FOR_INDEX_APPLICATION", reviewer_id="local-worker", reviewer_type="local_ai", rationale="self approval", evidence_refs=[])
    with store.connect(ROOT, create=False) as connection:
        row = connection.execute("SELECT corroboration_state,review_state,application_state FROM candidate_assertions WHERE assertion_id=?", (assertion_id,)).fetchone()
        assert tuple(row) == ("CONTRADICTED", "REJECTED", "NOT_ELIGIBLE")


def test_unverifiable_and_partial_candidates_remain_review_exceptions(tmp_path, monkeypatch):
    asset_id, interpretation_id = _setup(tmp_path, monkeypatch, purpose=None, owner=None, tags=())
    with store.connect(ROOT, create=False) as connection:
        candidate = {"asset_id": asset_id, "lifecycle": "CANDIDATE", "purpose": None, "owner_candidate": None, "summary": "semantic inference", "tags": [], "evidence_refs": [], "unresolved_questions": ["Who owns this?"]}
        connection.execute("UPDATE candidate_interpretations SET candidate_json=? WHERE interpretation_id=?", (json.dumps(candidate), interpretation_id))
    governance.extract_assertions(ROOT, interpretation_id=interpretation_id)
    governance.corroborate(ROOT, asset_id=asset_id)
    governance.review_batch(ROOT, asset_prefix="schemas")
    summary = governance.review_summary(ROOT, asset_id=asset_id)
    assert summary["application"] == {"NOT_ELIGIBLE": 2}
    assert governance.eligible(ROOT)["eligible_count"] == 0


def test_partial_corroboration_is_reviewable_but_not_full_approval(tmp_path, monkeypatch):
    asset_id, interpretation_id = _setup(tmp_path, monkeypatch)
    with store.connect(ROOT, create=False) as connection:
        candidate = json.loads(connection.execute("SELECT candidate_json FROM candidate_interpretations WHERE interpretation_id=?", (interpretation_id,)).fetchone()[0])
        candidate["purpose"] = "Estate comprehension contract"
        connection.execute("UPDATE candidate_interpretations SET candidate_json=? WHERE interpretation_id=?", (json.dumps(candidate), interpretation_id))
    governance.extract_assertions(ROOT, interpretation_id=interpretation_id)
    governance.corroborate(ROOT, asset_id=asset_id)
    with store.connect(ROOT, create=False) as connection:
        row = connection.execute("SELECT corroboration_state FROM candidate_assertions WHERE assertion_kind='PURPOSE'").fetchone()
        assert row[0] == "PARTIALLY_CORROBORATED"
    governance.review_batch(ROOT, asset_prefix="schemas")
    assert governance.eligible(ROOT)["eligible_count"] == 3


def test_conflicting_application_values_are_blocked(tmp_path, monkeypatch):
    asset_id, interpretation_id = _setup(tmp_path, monkeypatch)
    governance.extract_assertions(ROOT, interpretation_id=interpretation_id)
    governance.corroborate(ROOT, asset_id=asset_id)
    governance.review_batch(ROOT, asset_prefix="schemas")
    with store.connect(ROOT, create=False) as connection:
        source = connection.execute("SELECT * FROM candidate_assertions WHERE assertion_kind='PURPOSE'").fetchone()
        columns = [item[1] for item in connection.execute("PRAGMA table_info(candidate_assertions)").fetchall()]
        values = dict(zip(columns, source))
        values.update({"assertion_id": "assertion:conflict", "proposed_value": "conflicting purpose", "review_state": "APPROVED", "application_state": "ELIGIBLE"})
        connection.execute("INSERT INTO candidate_assertions(" + ",".join(columns) + ") VALUES(" + ",".join("?" for _ in columns) + ")", [values[column] for column in columns])
    result = governance.apply_eligible(ROOT, actor_id="policy", actor_type="deterministic_policy")
    assert result["applied_count"] == 2
    with store.connect(ROOT, create=False) as connection:
        states = connection.execute("SELECT conflict_state,application_state FROM candidate_assertions WHERE assertion_kind='PURPOSE' ORDER BY assertion_id").fetchall()
        assert all(tuple(row) == ("CONTRADICTORY_APPLICATIONS", "NOT_ELIGIBLE") for row in states)


def test_reversal_history_and_source_change_revalidation(tmp_path, monkeypatch):
    asset_id, interpretation_id = _setup(tmp_path, monkeypatch)
    governance.extract_assertions(ROOT, interpretation_id=interpretation_id)
    governance.corroborate(ROOT, asset_id=asset_id)
    governance.review_batch(ROOT, asset_prefix="schemas")
    applied = governance.apply_eligible(ROOT, actor_id="policy", actor_type="deterministic_policy")
    application_id = applied["applications"][0]["application_id"]
    reversed_result = governance.reverse_application(ROOT, application_id, actor_id="human-reviewer", actor_type="human", reason="review correction")
    assert reversed_result["status"] == "REVERSED"
    governance.extract_assertions(ROOT, interpretation_id=interpretation_id)
    with store.connect(ROOT, create=False) as connection:
        # Apply a fresh assertion, then change its source hash without touching canonical files.
        connection.execute("UPDATE candidate_assertions SET application_state='ELIGIBLE',review_state='APPROVED' WHERE assertion_kind='OWNER'")
        connection.execute("UPDATE assets SET current_content_hash='changed-hash',current_source_revision='rev-new' WHERE asset_id=?", (asset_id,))
    result = governance.revalidate_applications(ROOT)
    assert result["status"] in {"CURRENT", "REVALIDATION_REQUIRED"}


def test_resident_neutral_query_separates_history_and_related_assets(tmp_path, monkeypatch):
    asset_id, interpretation_id = _setup(tmp_path, monkeypatch)
    governance.extract_assertions(ROOT, interpretation_id=interpretation_id)
    governance.corroborate(ROOT, asset_id=asset_id)
    governance.review_batch(ROOT, asset_prefix="schemas")
    governance.apply_eligible(ROOT, actor_id="policy", actor_type="deterministic_policy")
    grace = governance.resident_query(ROOT, role="grace", query="comprehension_result")
    historian = governance.resident_query(ROOT, role="historian", query="comprehension_result")
    researcher = governance.resident_query(ROOT, role="researcher", query="comprehension_result")
    assert grace["applied_understanding"] and not grace["application_history"]
    assert historian["application_history"]
    assert researcher["related_assets"]
