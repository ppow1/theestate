import json

from estate.core.global_search_command_palette import (
    build_global_palette,
    execute_registered_command,
    search_global_palette,
)
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def test_global_search_indexes_required_domains(tmp_path):
    (tmp_path / "collaboration/work_packages/pending").mkdir(parents=True)
    (tmp_path / "collaboration/work_packages/pending/WP-0001.md").write_text("# Searchable Work Package\n", encoding="utf-8")
    (tmp_path / "data/registry").mkdir(parents=True)
    (tmp_path / "data/registry/missions.json").write_text(json.dumps({"title": "Searchable Mission"}), encoding="utf-8")
    (tmp_path / "collaboration/messages").mkdir(parents=True)
    (tmp_path / "collaboration/messages/msg.json").write_text(json.dumps({"title": "Searchable Mailbox"}), encoding="utf-8")
    (tmp_path / "residents").mkdir()
    (tmp_path / "residents/alfred.md").write_text("# Searchable Resident\n", encoding="utf-8")
    (tmp_path / "operations/boards").mkdir(parents=True)
    (tmp_path / "operations/boards/daily_board.md").write_text("# Searchable Daily Board\n", encoding="utf-8")
    (tmp_path / "operations/boards/parking_lot.md").write_text("# Searchable Parking Lot\n", encoding="utf-8")
    (tmp_path / "operations/validation").mkdir(parents=True)
    (tmp_path / "operations/validation/report.md").write_text("# Searchable Validation\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/manual.md").write_text("# Searchable Documentation\n", encoding="utf-8")

    palette = build_global_palette(tmp_path)
    domains = {item["domain"] for item in palette["artifacts"]}

    assert {"work_package", "mission", "mailbox", "resident", "daily_board", "parking_lot", "validation", "documentation"} <= domains
    assert (tmp_path / "runtime/search/global_command_palette.json").exists()


def test_command_lookup_empty_results_and_unavailable_handling(tmp_path):
    palette = build_global_palette(tmp_path)
    assert any(command["id"] == "navigate.validation" for command in palette["commands"])

    empty = search_global_palette("definitely-no-match", tmp_path, refresh=False)
    assert empty["match_count"] == 0

    available = execute_registered_command("navigate.validation")
    assert available["ok"] is True
    assert available["operation"] == "activate_tab"

    notification_center = execute_registered_command("notification-center")
    assert notification_center["ok"] is True
    assert notification_center["operation"] == "activate_tab"
    assert notification_center["target"] == "recalls"

    unavailable = execute_registered_command("command.ai-interpret")
    assert unavailable["ok"] is False
    assert unavailable["status"] == "unavailable"
    assert "forbids invented AI interpretation" in unavailable["message"]


def test_command_center_renders_keyboard_incremental_palette(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/manual.md").write_text("# Searchable Documentation\n", encoding="utf-8")
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert "Global Search and Command Palette" in html
    assert "id=\"global-search-input\"" in html
    assert "renderGlobalPaletteResults" in html
    assert "event.key === '/'" in html
    assert "unavailable_reason" in html


def test_notification_center_is_searchable_and_registered_command(tmp_path):
    palette = build_global_palette(tmp_path)
    command_ids = {command["id"] for command in palette["commands"]}

    assert "notification-center" in command_ids
    assert "navigate.notification-center" in command_ids

    search_result = search_global_palette("notification center", tmp_path, refresh=False)
    assert any(match.get("id") == "notification-center" for match in search_result["matches"])

    command = execute_registered_command("notification-center")
    assert command == {
        "ok": True,
        "command_id": "notification-center",
        "status": "ready",
        "operation": "activate_tab",
        "target": "recalls",
        "cli": None,
        "message": "Command is registered; execute through the existing operation handler.",
    }
