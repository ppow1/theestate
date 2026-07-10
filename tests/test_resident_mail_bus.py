import json

from estate.core.resident_mail_bus import (
    acknowledge_bus_message,
    inspect_thread,
    list_mailbox,
    notification_summary,
    office_integrations,
    reply_bus_message,
    resolve_identity,
    send_message,
    unread_count,
)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed(tmp_path):
    write_json(tmp_path / "data/registry/personnel.json", [
        {"employee_id": 1, "display_name": "Steward", "current_office": "Stewardship", "mailbox_id": 1},
        {"employee_id": 6, "display_name": "Helen", "current_office": "Human Resources", "mailbox_id": 6, "resident_id": "RES-000003"},
        {"employee_id": 7, "display_name": "Alfred", "current_office": "Administration", "mailbox_id": 7, "resident_id": "RES-000001"},
        {"employee_id": 12, "display_name": "Grace", "current_office": "Office of Operations", "mailbox_id": 12},
    ])
    write_json(tmp_path / "data/registry/mailboxes.json", [
        {"mailbox_id": 10004, "mailbox_type": "office", "display_name": "Human Resources Office", "owning_office": "Human Resources", "responsible_employee_id": 6},
        {"mailbox_id": 10100, "mailbox_type": "queue", "display_name": "Alfred Routing Intake", "owning_office": "Chief of Staff"},
    ])


def test_routing_identity_resolution_and_unread_counts(tmp_path):
    seed(tmp_path)
    result = send_message("Alfred", "Helen", "Notice", "Please review", root=tmp_path)
    assert result["delivered"] is True
    assert resolve_identity("Helen", tmp_path)["mailbox_id"] == 6
    inbox = list_mailbox("Helen", "inbox", include_body=True, root=tmp_path)
    assert inbox["message_count"] == 1
    assert inbox["messages"][0]["body"] == "Please review"
    assert unread_count("Helen", tmp_path) == 1


def test_office_and_steward_directed_routing(tmp_path):
    seed(tmp_path)
    office = send_message("Helen", "Human Resources Office", "Office notice", "Filed", root=tmp_path)
    steward = send_message("Alfred", "Steward", "Steward notice", "Needs attention", root=tmp_path)
    assert office["message"]["destination_identity"]["mailbox_id"] == 10004
    assert steward["message"]["destination_identity"]["mailbox_id"] == 1


def test_acknowledgments_replies_and_threads_persist(tmp_path):
    seed(tmp_path)
    sent = send_message("Alfred", "Helen", "Thread", "Body", root=tmp_path)
    mid = sent["message"]["id"]
    ack = acknowledge_bus_message(mid, actor="Helen", note="Seen", root=tmp_path)
    reply = reply_bus_message(mid, actor="Helen", body="Reply body", root=tmp_path)
    thread = inspect_thread(sent["message"]["thread_id"], include_body=True, root=tmp_path)
    assert ack["acknowledgement"]["acknowledges"] == mid
    assert reply["reply"]["reply_to"] == mid
    assert thread["message_count"] == 3


def test_duplicate_delivery_prevention(tmp_path):
    seed(tmp_path)
    first = send_message("Alfred", "Helen", "Same", "Same body", root=tmp_path)
    second = send_message("Alfred", "Helen", "Same", "Same body", root=tmp_path)
    assert first["delivered"] is True
    assert second["duplicate"] is True
    assert list_mailbox("Helen", "inbox", root=tmp_path)["message_count"] == 1


def test_restricted_privacy_in_summaries(tmp_path):
    seed(tmp_path)
    send_message("Helen", "Alfred", "Private", "Secret body", classification="Restricted", root=tmp_path)
    summary = notification_summary("Alfred", tmp_path)
    inbox = list_mailbox("Alfred", "inbox", include_body=True, root=tmp_path)
    assert summary["attention"][0]["summary"] == "Restricted content omitted."
    assert "body" not in inbox["messages"][0]


def test_office_integration_surfaces_are_privacy_safe(tmp_path):
    seed(tmp_path)
    send_message("Helen", "Grace", "Directive", "Coordinate", root=tmp_path)
    report = office_integrations(tmp_path)
    assert "alfred_attention" in report
    assert report["grace_operational_directives"]["unread_count"] == 1
