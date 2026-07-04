import json

from estate.core.operations_center_workspace_profiles import (
    PROFILES_OUTPUT,
    resolve_workspace_profile,
    save_workspace_profile,
)
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def test_default_workspace_profiles_restore_task_focused_layouts(tmp_path):
    payload = resolve_workspace_profile(tmp_path, profile_name="validation")

    assert payload["selected_profile"] == "validation"
    assert payload["profile"]["active_tab"] == "validation"
    assert payload["profile"]["operator_activity"]["verbosity"] == "detailed"
    assert payload["compatibility"]["compatible"] is True
    assert "mission-control" in payload["available_profiles"]


def test_workspace_profile_save_and_load_persists_local_configuration(tmp_path):
    saved = save_workspace_profile(tmp_path, name="custom-review", base_profile="active-projects", active_tab="work-packages")
    reloaded = resolve_workspace_profile(tmp_path, profile_name="custom-review")

    assert saved["profile"]["active_tab"] == "work-packages"
    assert reloaded["profile"]["active_tab"] == "work-packages"
    assert (tmp_path / PROFILES_OUTPUT).exists()
    data = json.loads((tmp_path / PROFILES_OUTPUT).read_text())
    assert data["profiles"]["custom-review"]["layout_version"] == "layout-framework-v1"


def test_workspace_profiles_skip_unavailable_panels_gracefully(tmp_path):
    payload = resolve_workspace_profile(tmp_path, profile_name="mission-control", available_panels={"home", "validation"})

    assert payload["profile"]["tab_order"] == ["home", "validation"]
    assert any(warning["type"] == "unavailable_panel" for warning in payload["warnings"])


def test_command_center_embeds_workspace_profile_metadata(tmp_path):
    payload = generate_command_center(root=tmp_path, write=True)
    html = render_command_center_html(payload)

    assert payload["workspace_profile"]["profile"]["active_tab"] == "mission-control"
    assert "WORKSPACE_PROFILE" in html
    assert "operations_center_workspace_profiles.json" in json.dumps(payload["layout_framework"])
