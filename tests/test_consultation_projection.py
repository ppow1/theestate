from estate.core.consultation_projection import ConsultationProjection, render_root
from estate.core.consultation_store import ConsultationStore


def _history(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    root = store.allocate_root(objective="restart safety", question="initial question", tags=("comms8",))
    store.attach_ec8(root.logical_consultation_id, "ec8-old")
    store.record_transport_attempt(root.logical_consultation_id, "ec8-old", status="expired", failure_class="transport")
    store.append_response(root.logical_consultation_id, {"content": "Use durable checkpoints."})
    child = store.allocate_continuation(root.logical_consultation_id, question="new evidence")
    store.attach_ec8(child.logical_consultation_id, "ec8-new")
    store.record_transport_attempt(child.logical_consultation_id, "ec8-new", status="resolved", worker_id="chatgpt")
    store.append_response(child.logical_consultation_id, {"content": "Persist browser recovery state."})
    return store


def test_projection_contains_lineage_and_retry_history_idempotently(tmp_path):
    store = _history(tmp_path)
    projection = ConsultationProjection(store, directory=tmp_path / "projection")
    first = projection.project(1)
    content = (tmp_path / "projection" / "consultation-1-00.md").read_text()
    second = projection.project(1)
    assert first["status"] == second["status"] == "pending"
    assert content.count("ec8-old") == 2
    assert "1.01" in content
    assert "supersedes" not in content
    assert store.get_root(1).github_projection_status == "pending"


def test_projection_publisher_success_and_failure_are_non_blocking(tmp_path):
    store = _history(tmp_path)
    published = ConsultationProjection(store, directory=tmp_path / "ok", publisher=lambda root, content: f"github://consultations/{root}")
    assert published.project(1)["status"] == "published"
    assert store.get_root(1).github_reference == "github://consultations/1.00"
    failed = ConsultationProjection(store, directory=tmp_path / "failed", publisher=lambda *_: (_ for _ in ()).throw(ConnectionError("github_down")))
    assert failed.project(1)["status"] == "failed"
    assert store.get_root(1).github_projection_status == "failed"


def test_render_root_is_bounded_and_reopenable(tmp_path):
    store = _history(tmp_path)
    content = render_root(store, "1.00")
    reopened = ConsultationStore(tmp_path / "consultations.db")
    assert "restart safety" in content
    assert reopened.get_root("1").logical_consultation_id == "1.00"
