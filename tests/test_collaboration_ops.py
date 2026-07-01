import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.collaboration_ops import run_routing_engine, watch_worker_inboxes


def write_message(root, **overrides):
    message = {
        "id": "msg_test_001",
        "version": 1,
        "created_at": "2026-07-01T00:00:00",
        "created_by": "Alfred",
        "source": "alfred",
        "destination": "queue",
        "classification": "Estate Internal",
        "message_type": "implementation",
        "priority": "normal",
        "status": "open",
        "requires_ack": True,
        "payload": {
            "title": "Implement code test",
            "summary": "Build and test a bounded implementation change.",
            "instructions": "Implement the code and run tests.",
            "artifact_refs": [],
        },
    }
    message.update(overrides)
    path = root / "collaboration" / "messages" / f"{message['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(message), encoding="utf-8")
    return path


def test_routing_engine_routes_implementation_message(tmp_path):
    write_message(tmp_path)

    report = run_routing_engine(tmp_path)

    assert report["open_messages"] == 1
    assert report["decisions"][0]["route"]["worker"] == "worker.implementation"
    assert (tmp_path / "runtime" / "collaboration" / "routing" / "latest.json").exists()


def test_inbox_watcher_writes_status_summary(tmp_path):
    write_message(tmp_path, id="msg_test_002")

    summary = watch_worker_inboxes(tmp_path)

    assert summary["worker_count"] == 1
    assert summary["message_count"] == 1
    assert summary["workers"][0]["worker"] == "worker.implementation"
    assert (tmp_path / "collaboration" / "status" / "worker_inbox_summary.json").exists()
    assert (tmp_path / "runtime" / "collaboration" / "worker_inboxes" / "worker.implementation.json").exists()


def test_invalid_envelope_routes_to_alfred_review(tmp_path):
    write_message(tmp_path, id="msg_test_003", payload="not an object")

    report = run_routing_engine(tmp_path)

    assert report["decisions"][0]["valid"] is False
    assert report["decisions"][0]["route"]["worker"] == "alfred.review"
