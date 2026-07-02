import json

from estate.core.collaboration_messages import acknowledge_message, create_reply, group_threads
from estate.core.mailbox_index import generate_mailbox_index, mailbox_index_summary


def write_message(root, **overrides):
    message = {
        "id": "msg_original",
        "version": 1,
        "created_at": "2026-07-02T00:00:00",
        "created_by": "Chief Architect #3",
        "source": "office.chief_architect_3",
        "destination": "office.chief_architect_4",
        "classification": "Estate Internal",
        "message_type": "review_request",
        "priority": "normal",
        "status": "open",
        "requires_ack": True,
        "payload": {"title": "Review request", "summary": "Please review.", "instructions": "Ack and reply.", "artifact_refs": []},
    }
    message.update(overrides)
    path = root / "collaboration" / "messages" / f"{message['id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(message), encoding="utf-8")
    return path


def test_acknowledge_message_updates_original_and_writes_ack(tmp_path):
    path = write_message(tmp_path)

    result = acknowledge_message("msg_original", actor="Chief Architect #4", note="Received.", root=tmp_path)

    original = json.loads(path.read_text(encoding="utf-8"))
    ack = result["acknowledgement"]
    assert original["ack_status"] == "acknowledged"
    assert original["acknowledged_by"] == "Chief Architect #4"
    assert ack["acknowledges"] == "msg_original"
    assert ack["reply_to"] == "msg_original"
    assert ack["thread_id"] == "msg_original"
    assert (tmp_path / result["acknowledgement_path"]).exists()


def test_reply_references_original_thread(tmp_path):
    write_message(tmp_path, thread_id="thread-review-1")

    result = create_reply("msg_original", actor="Chief Architect #4", body="Approved with comments.", root=tmp_path)

    reply = result["reply"]
    assert reply["reply_to"] == "msg_original"
    assert reply["thread_id"] == "thread-review-1"
    assert reply["payload"]["summary"] == "Approved with comments."
    assert "msg_original" in group_threads(tmp_path)["thread-review-1"]
    assert reply["id"] in group_threads(tmp_path)["thread-review-1"]


def test_mailbox_index_surfaces_ack_required_and_thread_fields(tmp_path):
    write_message(tmp_path, thread_id="thread-review-2", ack_status="pending")

    index = generate_mailbox_index(tmp_path)
    summary = mailbox_index_summary(index)

    item = next(m for m in index["messages"] if m["message_id"] == "msg_original")
    assert item["thread_id"] == "thread-review-2"
    assert item["ack_status"] == "pending"
    assert summary["ack_required_message_count"] == 1
    assert summary["thread_count"] == 1
