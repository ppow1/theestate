import json

from estate.core.codex_seat_configuration import (
    CODEX_AUTOMATION_CHROMIUM_ROOT,
    codex_seat_configuration,
)


def test_seat_configuration_reuses_bridge_mapping_without_auth_state():
    payload = codex_seat_configuration()

    assert payload["read_only"] is True
    assert [item["seat_id"] for item in payload["seats"]] == ["C1", "C2", "C3"]
    assert [item["codex_home"] for item in payload["seats"]] == [
        r"A:\AI\CodexProfiles\C1",
        r"A:\AI\CodexProfiles\C2",
        r"A:\AI\CodexProfiles\C3",
    ]
    assert [item["interactive_chrome_profile"] for item in payload["seats"]] == [
        "Profile 3", "Profile 4", "Profile 5"
    ]
    assert [item["automation_chromium_profile"] for item in payload["seats"]] == [
        str(CODEX_AUTOMATION_CHROMIUM_ROOT / "C1"),
        str(CODEX_AUTOMATION_CHROMIUM_ROOT / "C2"),
        str(CODEX_AUTOMATION_CHROMIUM_ROOT / "C3"),
    ]


def test_seat_configuration_can_be_read_as_one_seat():
    payload = codex_seat_configuration("C2")
    assert payload["seats"] == [{
        "seat_id": "C2",
        "codex_home": r"A:\AI\CodexProfiles\C2",
        "execution_surface": "codex-cli",
        "interactive_chrome_profile": "Profile 4",
        "automation_chromium_profile": str(CODEX_AUTOMATION_CHROMIUM_ROOT / "C2"),
    }]
