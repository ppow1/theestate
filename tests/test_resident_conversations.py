import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.resident_conversations import build_resident_conversations_workspace
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed_workspace(root):
    write_json(root, "data/registry/residents.json", [
        {"id": "RES-000001", "name": "Alfred", "department": "Administration", "office": "Manager of Administration", "status": "Active", "role": "Coordinates routing."},
        {"id": "RES-000003", "name": "Helen", "department": "Human Resources", "office": "Manager of Human Resources", "status": "Active", "role": "Coordinates personnel fit."},
        {"id": "RES-999999", "name": "Future", "office": "Future Office", "status": "Dormant", "role": "Future registered resident."},
    ])
    write_json(root, "data/registry/personnel.json", [
        {"employee_id": 6, "display_name": "Helen", "mailbox_id": 6, "resident_id": "RES-000003"},
        {"employee_id": 7, "display_name": "Alfred", "mailbox_id": 7, "resident_id": "RES-000001"},
    ])
    write_json(root, "data/registry/mailboxes.json", [
        {"mailbox_id": 7, "display_name": "Alfred Personal Mailbox", "owning_office": "Administration"},
        {"mailbox_id": 6, "display_name": "Helen Personal Mailbox", "owning_office": "Human Resources"},
    ])
    write_json(root, "data/objects/RES-000001.json", {"id": "RES-000001", "name": "Alfred"})
    write_json(root, "collaboration/messages/msg_alfred.json", {
        "id": "msg_alfred", "created_at": "2026-07-01T00:00:00Z", "created_by": "Alfred", "source": "Alfred", "destination_mailbox_id": 7, "status": "open", "related_artifact": "operations/alfred/operational_briefing.md", "payload": {"title": "Alfred routing note", "summary": "Route a local artifact.", "artifact_refs": ["collaboration/work_packages/pending/WP-0059_SERIES_resident_conversations_workspace.md"]}
    })
    write_json(root, "collaboration/messages/msg_helen.json", {
        "id": "msg_helen", "created_by": "CA3", "destination_mailbox_id": 6, "status": "open", "payload": {"title": "Helen onboarding note", "summary": "Coordinate onboarding."}
    })


def test_resident_conversations_cover_alfred_helen_unknown_and_future(tmp_path):
    seed_workspace(tmp_path)

    workspace = build_resident_conversations_workspace(tmp_path, names=("Alfred", "Helen", "Future", "Unknown"))
    by_name = {item["resident_name"]: item for item in workspace["data"]["conversations"]}

    assert by_name["Alfred"]["mailbox"]["mailbox_id"] == 7
    assert by_name["Helen"]["role"] == "Coordinates personnel fit."
    assert by_name["Future"]["status"] == "Dormant"
    assert by_name["Unknown"]["available"] is False
    assert by_name["Unknown"]["mailbox"]["display_name"] == "Not available yet"


def test_resident_conversations_show_empty_and_linked_sources(tmp_path):
    seed_workspace(tmp_path)

    workspace = build_resident_conversations_workspace(tmp_path, names=("Alfred", "Future"))
    alfred, future = workspace["data"]["conversations"]

    assert alfred["recent_messages"][0]["title"] == "Alfred routing note"
    assert "operations/alfred/operational_briefing.md" in alfred["source_artifacts"]
    assert "collaboration/work_packages/pending/WP-0059_SERIES_resident_conversations_workspace.md" in alfred["source_artifacts"]
    assert future["recent_messages"] == []
    assert "Conversation is an interface surface only" in workspace["data"]["record_policy"]
    assert "No authoritative voice/chat transcript" in future["transcript_audit_placeholder"]


def test_command_center_renders_resident_conversations_workspace(tmp_path):
    seed_workspace(tmp_path)

    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert "Resident Conversations" in [item["label"] for item in payload["navigation"]["items"]]
    assert "Resident Conversations Workspace" in html
    assert "Resident selection" in html
    assert "Alfred routing note" in html
    assert "No conversation-related institutional messages" in html
    assert "Conversation is an interface surface only" in html
