import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.resident_cards import build_resident_cards
from estate.core.resident_presence import build_resident_presence


def write_json(root, rel, data):
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def seed(root):
    write_json(root, "data/registry/residents.json", [
        {"id": "RES-000001", "name": "Alfred", "department": "Administration", "office": "Manager of Administration", "status": "Active", "role": "Routes local work."},
        {"id": "RES-000003", "name": "Helen", "department": "Human Resources", "office": "Manager of Human Resources", "status": "Active", "role": "Coordinates personnel."},
    ])
    write_json(root, "data/registry/personnel.json", [
        {"display_name": "Alfred", "mailbox_id": 7, "resident_id": "RES-000001", "current_office": "Administration"},
        {"display_name": "Helen", "mailbox_id": 6, "resident_id": "RES-000003", "current_office": "Human Resources"},
    ])
    write_json(root, "data/registry/mailboxes.json", [])


def test_alfred_and_helen_presence_render_from_runtime(tmp_path):
    seed(tmp_path)
    write_json(tmp_path, "runtime/residents/presence.json", {"residents": [
        {"resident_id": "RES-000001", "name": "Alfred", "presence_state": "working", "current_duty": "Route messages", "last_heartbeat": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        {"resident_id": "RES-000003", "name": "Helen", "presence_state": "waiting_for_steward", "needs_steward": True, "last_heartbeat": datetime.now(timezone.utc).isoformat(timespec="seconds")},
    ]})
    payload = build_resident_presence(tmp_path)
    by_name = {r["name"]: r for r in payload["residents"]}
    assert by_name["Alfred"]["presence_state"] == "working"
    assert by_name["Helen"]["needs_steward"] is True
    assert by_name["Alfred"]["autonomous_execution"] is False


def test_missing_runtime_data_degrades_gracefully(tmp_path):
    seed(tmp_path)
    payload = build_resident_presence(tmp_path, names=("Future",))
    future = payload["residents"][0]
    assert future["presence_state"] == "degraded"
    assert future["resident_id"] is None
    assert "missing" in future["status_reason"].lower()


def test_stale_heartbeat_is_detectable(tmp_path):
    seed(tmp_path)
    write_json(tmp_path, "runtime/residents/presence.json", {"residents": [
        {"resident_id": "RES-000001", "name": "Alfred", "presence_state": "available", "last_heartbeat": "2000-01-01T00:00:00+00:00"}
    ]})
    alfred = build_resident_presence(tmp_path, names=("Alfred",))["residents"][0]
    assert alfred["heartbeat_stale"] is True
    assert alfred["presence_state"] == "degraded"


def test_resident_cards_consume_presence_data(tmp_path):
    seed(tmp_path)
    write_json(tmp_path, "runtime/residents/presence.json", {"residents": [
        {"resident_id": "RES-000001", "name": "Alfred", "presence_state": "working", "current_duty": "Inspect local presence", "last_heartbeat": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    ]})
    card = build_resident_cards(tmp_path, names=("Alfred",))["cards"][0]
    assert card["presence_state"] == "working"
    assert card["current_duty"] == "Inspect local presence"
    assert card["visible_presence_only"] is True
