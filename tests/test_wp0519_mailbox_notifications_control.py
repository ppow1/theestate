import json

from estate.core.office_command_surface import execute_office_action, ACTION_CONTROLS
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def seed(root):
    write_json(root, "data/registry/personnel.json", [
        {"employee_id": 7, "display_name": "Alfred", "current_title": "Manager", "current_office": "Administration", "mailbox_id": 7},
        {"employee_id": 8, "display_name": "Chief Architect #5", "current_title": "Chief Architect #5", "current_office": "Office of Chief Architect", "mailbox_id": 8},
    ])
    write_json(root, "data/registry/mailboxes.json", [])
    write_json(root, "collaboration/messages/msg_wp0519.json", {
        "id": "msg_wp0519", "version": 1, "created_at": "2026-07-10T00:00:00+00:00",
        "source": "employee.7", "source_employee_id": 7, "destination": "employee.8",
        "message_type": "coordination", "priority": "high", "status": "open", "requires_ack": True,
        "ack_status": "pending", "payload": {"title": "WP-0519", "summary": "Needs Office attention"}
    })
    write_json(root, "runtime/notifications/gotify_delivery_report.json", {"status": "failed", "error": "endpoint unavailable"})


def test_wp0519_browser_to_handler_to_state_to_render_flow(tmp_path):
    seed(tmp_path)
    action_ids = {c["action_id"] for c in ACTION_CONTROLS}
    for required in ["mailboxes.refresh", "mailboxes.open_message", "mailboxes.local_acknowledge", "mailboxes.mark_read_state", "mailboxes.reply_or_route", "mailboxes.open_personnel", "attention.clear_local", "delivery.inspect_failures", "notifications.refresh_center"]:
        assert required in action_ids

    assert execute_office_action("mailboxes.refresh", root=tmp_path, query="WP-0519", request_id="refresh")["outcome"] == "completed"
    assert execute_office_action("mailboxes.open_message", root=tmp_path, message_id="msg_wp0519", request_id="open")["outcome"] == "completed"
    assert execute_office_action("mailboxes.mark_read_state", root=tmp_path, message_id="msg_wp0519", read_state="read", request_id="read")["outcome"] == "completed"
    assert execute_office_action("mailboxes.mark_read_state", root=tmp_path, message_id="msg_wp0519", read_state="unread", request_id="unread")["outcome"] == "completed"
    assert execute_office_action("mailboxes.reply_or_route", root=tmp_path, message_id="msg_wp0519", body="Reply through bus", request_id="reply")["outcome"] == "completed"
    assert execute_office_action("mailboxes.reply_or_route", root=tmp_path, message_id="msg_wp0519", route_target="personnel", request_id="route")["outcome"] == "completed"
    assert execute_office_action("mailboxes.open_personnel", root=tmp_path, employee_id="7", request_id="personnel")["outcome"] == "completed"
    assert execute_office_action("mailboxes.local_acknowledge", root=tmp_path, message_id="msg_wp0519", request_id="ack")["outcome"] == "completed"
    clear = execute_office_action("attention.clear_local", root=tmp_path, attention_id="notification:mailbox:msg_wp0519", request_id="clear")
    assert clear["outcome"] == "completed"
    assert "authoritative source closure was not changed" in clear["steward_message"]
    assert execute_office_action("delivery.inspect_failures", root=tmp_path, request_id="failures")["outcome"] == "completed"

    assert json.loads((tmp_path / "runtime/steward/mailbox_message_read_state.json").read_text())["messages"]["msg_wp0519"]["state"] == "unread"
    assert (tmp_path / "runtime/steward/delivery_failure_inspection.json").exists()
    assert (tmp_path / "runtime/steward/mailbox_control_center.json").exists()
    assert "Reply through bus" in "\n".join(p.read_text() for p in (tmp_path / "collaboration/messages").glob("*.json"))

    html = render_command_center_html(generate_command_center(root=tmp_path, write=False))
    assert "mailboxes.open_message" in html
    assert "mailboxes.mark_read_state" in html
    assert "attention.clear_local" in html
    assert "delivery.inspect_failures" in html
