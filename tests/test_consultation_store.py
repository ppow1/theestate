from concurrent.futures import ThreadPoolExecutor
import sqlite3

import pytest

from estate.core.consultation_store import ConsultationStore


def test_root_and_continuation_lineage_persist_after_reopen(tmp_path):
    path = tmp_path / "consultations.db"
    store = ConsultationStore(path)
    root = store.allocate_root(subject="Restartability", tags=("mcp", "restartability"), ptm_project_id="PROJ-0042")
    child = store.allocate_continuation(root.logical_consultation_id, question="New evidence", continuation_reason="validation_failed")
    reopened = ConsultationStore(path)

    assert root.logical_consultation_id == "1.00"
    assert child.logical_consultation_id == "1.01"
    assert child.root_logical_id == "1.00"
    assert child.parent_logical_id == "1.00"
    assert reopened.get("1.00").tags == ("mcp", "restartability")
    assert reopened.get("1.01").ptm_project_id is None


def test_continuation_allocation_is_duplicate_protected(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = store.allocate_root()

    def allocate():
        try:
            return store.allocate_continuation(root.logical_consultation_id).logical_consultation_id
        except (sqlite3.IntegrityError, sqlite3.OperationalError):
            return "duplicate_rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: allocate(), range(2)))
    assert sorted(results) == ["1.01", "duplicate_rejected"]


def test_dot_99_requires_explicit_rollover(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = store.allocate_root()
    parent = root
    for _ in range(99):
        parent = store.allocate_continuation(parent.logical_consultation_id)
    assert parent.logical_consultation_id == "1.99"
    with pytest.raises(ValueError, match="rollover_required_after_.99"):
        store.allocate_continuation(parent.logical_consultation_id)
    rollover = store.allocate_root(continues_from="1.99", status="open")
    assert rollover.logical_consultation_id == "2.00"
    assert rollover.predecessor_logical_id == "1.99"


def test_standalone_and_ptm_linked_consultations_are_supported(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    standalone = store.allocate_root(subject="Standalone")
    linked = store.allocate_root(subject="Linked", ptm_project_id="PROJ-1001", ptm_work_item_id="TASK-2002")
    assert standalone.ptm_project_id is None
    assert linked.ptm_project_id == "PROJ-1001"
    assert linked.ptm_work_item_id == "TASK-2002"


def test_tags_ec8_response_validation_and_search(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root(workflow_id="wf-1", tags=("comms8",))
    store.add_tags(record.logical_consultation_id, ["production", "comms8"])
    store.attach_ec8(record.logical_consultation_id, "ec8-test-1", "wf-1")
    store.append_response(record.logical_consultation_id, {"recommendations": ["one"]}, response_id="resp-1")
    stored = store.append_validation(record.logical_consultation_id, expected_result="three recommendations", observed_result="one", evidence={"test": "failed"})

    assert stored.ec8_request_id == "ec8-test-1"
    assert stored.response == {"recommendations": ["one"]}
    assert stored.validation_evidence == {"test": "failed"}
    assert stored.status == "validating"
    assert [item.logical_consultation_id for item in store.search(tag="production")] == ["1.00"]
    assert [item.logical_consultation_id for item in store.search(ec8_request_id="ec8-test-1")] == ["1.00"]


def test_failed_validation_can_open_a_lineage_preserving_continuation(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = store.allocate_root(status="awaiting_reasoning", objective="Restartability")
    failed = store.append_validation(
        root.logical_consultation_id,
        expected_result="service restarts",
        observed_result="browser session was lost",
        evidence={"failure": "session_not_rehydrated"},
        status="continuation_required",
    )
    continuation = store.allocate_continuation(
        failed.logical_consultation_id,
        question="Revise the recommendation using the new evidence.",
        continuation_reason="previous recommendation failed validation",
    )
    assert failed.status == "continuation_required"
    assert continuation.logical_consultation_id == "1.01"
    assert continuation.parent_logical_id == failed.logical_consultation_id


def test_github_projection_is_local_and_non_blocking(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root()
    assert record.github_projection_status == "pending"
    assert store.set_github_projection(record.logical_consultation_id, "failed").github_projection_status == "failed"
    published = store.set_github_projection(record.logical_consultation_id, "published", "github://example/consultation/1.00")
    assert published.github_projection_status == "published"
    assert published.github_reference == "github://example/consultation/1.00"


def test_ec8_identity_remains_separate_from_logical_identity(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root()
    attached = store.attach_ec8(record.logical_consultation_id, "ec8-abcdef")
    assert attached.logical_consultation_id == "1.00"
    assert attached.ec8_request_id == "ec8-abcdef"
    assert attached.logical_consultation_id != attached.ec8_request_id


def test_transport_attempts_preserve_expiry_and_reserve_one_replacement(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root(status="awaiting_reasoning", objective="retry")
    store.attach_ec8(record.logical_consultation_id, "ec8-expired", "wf-1")
    first = store.record_transport_attempt(record.logical_consultation_id, "ec8-expired", workflow_id="wf-1", status="expired", failure_class="wrong_worker_lease_expired", worker_id="codex")
    reserved = store.reserve_transport_retry(record.logical_consultation_id, "ec8-expired", failure_class="wrong_worker_lease_expired")
    repeated = store.reserve_transport_retry(record.logical_consultation_id, "ec8-expired", failure_class="wrong_worker_lease_expired")
    assert first.attempt_number == 1
    assert reserved.attempt_number == repeated.attempt_number == 2
    assert len(store.transport_attempts(record.logical_consultation_id)) == 2
    assert store.transport_attempts(record.logical_consultation_id)[0].status == "expired"


def test_transport_retry_rejected_after_response_or_active_attempt(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    record = store.allocate_root(status="awaiting_reasoning", objective="retry")
    store.attach_ec8(record.logical_consultation_id, "ec8-old")
    store.record_transport_attempt(record.logical_consultation_id, "ec8-old", status="expired")
    store.append_response(record.logical_consultation_id, {"content": "done"})
    with pytest.raises(ValueError, match="response_already_exists"):
        store.reserve_transport_retry(record.logical_consultation_id, "ec8-old", failure_class="expired")


def test_bounded_history_summary_and_context_required(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = store.allocate_root(objective="durable history", question="first")
    store.append_response(root.logical_consultation_id, {"content": "recommendation"})
    child = store.allocate_continuation(root.logical_consultation_id, question="second", current_evidence={"new": "evidence"})
    store.append_validation(child.logical_consultation_id, observed_result="failed", evidence={"reason": "restart"}, status="continuation_required")
    assert store.get_root("1").logical_consultation_id == "1.00"
    assert [x.logical_consultation_id for x in store.get_turn_range(1, 0, 1)] == ["1.00", "1.01"]
    assert [x.logical_consultation_id for x in store.latest_turns(1, 1)] == ["1.01"]
    assert "durable history" in store.compact_summary(1)["summary"]
    context = store.context_required(1, reason="missing validation context", latest=2)
    assert context["status"] == "CONTEXT_REQUIRED"
    assert [x["logical_consultation_id"] for x in context["turns"]] == ["1.00", "1.01"]
