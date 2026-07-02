import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.resident_cards import build_resident_cards
from estate.core.steward_command_center import render_command_center_html


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed_registries(root):
    write_json(root, "data/registry/residents.json", [
        {"id": "RES-000001", "name": "Alfred", "office": "Manager of Administration", "status": "Active", "role": "Coordinates the Estate."},
        {"id": "RES-000003", "name": "Helen", "department": "Human Resources", "office": "Manager of Human Resources", "status": "Active", "role": "Manages resident and worker assignment fit."},
        {"id": "RES-999999", "name": "Future", "office": "Future Office", "status": "Dormant"},
    ])
    write_json(root, "data/registry/personnel.json", [
        {"employee_id": 6, "display_name": "Helen", "mailbox_id": 6, "resident_id": "RES-000003"},
    ])
    write_json(root, "data/registry/mailboxes.json", [
        {"mailbox_id": 10100, "display_name": "Alfred Routing Intake", "owning_office": "Chief of Staff"},
        {"mailbox_id": 10004, "display_name": "Human Resources Office", "owning_office": "Human Resources"},
    ])
    write_json(root, "data/objects/RES-000001.json", {"id": "RES-000001", "name": "Alfred"})
    write_json(root, "runtime/residents/status.json", {"Helen": {"current_duty": "Coordinate onboarding status."}})


def test_resident_cards_use_populated_runtime_and_registry_data(tmp_path):
    seed_registries(tmp_path)

    payload = build_resident_cards(tmp_path)
    cards = {card["name"]: card for card in payload["cards"]}

    assert cards["Alfred"]["role"] == "Coordinates the Estate."
    assert cards["Alfred"]["mailbox"]["mailbox_id"] == 10100
    assert cards["Alfred"]["needs_steward"] == "No"
    assert cards["Alfred"]["details_link"] == "data/objects/RES-000001.json"
    assert cards["Helen"]["current_duty"] == "Coordinate onboarding status."
    assert cards["Helen"]["mailbox"]["mailbox_id"] == 6


def test_resident_cards_degrade_with_missing_data(tmp_path):
    payload = build_resident_cards(tmp_path)
    alfred = payload["cards"][0]

    assert alfred["available"] is False
    assert alfred["name"] == "Alfred"
    assert alfred["operational_status"] == "Not available yet"
    assert alfred["mailbox"]["display_name"] == "Not available yet"


def test_resident_cards_are_extensible_for_future_residents(tmp_path):
    seed_registries(tmp_path)

    payload = build_resident_cards(tmp_path, names=("Alfred", "Helen", "Future"))
    future = payload["cards"][2]

    assert future["name"] == "Future"
    assert future["operational_status"] == "Dormant"
    assert set(["name", "role", "operational_status", "current_duty", "mailbox", "last_activity", "needs_steward", "details_link"]).issubset(future.keys())


def test_resident_card_html_contains_required_fields(tmp_path):
    seed_registries(tmp_path)
    cards = build_resident_cards(tmp_path)["cards"]
    html = render_command_center_html({"generated_at": "now", "panels": {"alfred_resident_card": cards[0], "helen_resident_card": cards[1]}})

    for label in ["Operational Status", "Current Duty", "Mailbox", "Last Activity", "Needs Steward", "Resident Details"]:
        assert label in html
