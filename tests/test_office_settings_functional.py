import json

from estate.core.office_command_surface import execute_office_action
from estate.core.operations_center_settings import SETTINGS_OUTPUT, export_operations_center_settings, import_operations_center_settings
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def test_settings_e2e_theme_navigation_reload_restart(tmp_path):
    payload = generate_command_center(root=tmp_path, write=False)
    html = render_command_center_html(payload)
    assert "settings-save-apply" in html
    settings = payload["settings_manager"]["settings"]
    settings["appearance"]["theme"] = "dark"
    settings["workspace"]["visible_panels"]["help"] = False
    settings["workspace"]["navigation_order"] = ["settings", "home"] + [x for x in settings["workspace"]["navigation_order"] if x not in {"settings", "home"}]
    result = execute_office_action("settings.save_apply", root=tmp_path, settings_json=json.dumps({"settings": settings}))
    assert result["outcome"] == "completed"
    stored = json.loads((tmp_path / SETTINGS_OUTPUT).read_text(encoding="utf-8"))
    assert stored["settings"]["appearance"]["theme"] == "dark"
    reloaded = generate_command_center(root=tmp_path, write=False)
    assert reloaded["settings_manager"]["settings"]["appearance"]["theme"] == "dark"
    assert "help" not in [item["id"] for item in reloaded["navigation"]["items"]]
    html2 = render_command_center_html(reloaded)
    assert "data-theme='dark'" in html2
    recreated = generate_command_center(root=tmp_path, write=False)
    assert recreated["settings_manager"]["settings"]["appearance"]["theme"] == "dark"


def test_settings_reset_export_import_and_malformed_import(tmp_path):
    result = execute_office_action("settings.reset_defaults", root=tmp_path)
    assert result["outcome"] == "completed"
    exported = export_operations_center_settings(tmp_path)
    assert exported["version"] == 1 and exported["settings"]["persistence"]["local_only"] is True
    exported["settings"]["appearance"]["accent"] = "blue"
    imported = import_operations_center_settings(tmp_path, exported)
    assert imported["settings"]["appearance"]["accent"] == "blue"
    bad = execute_office_action("settings.import", root=tmp_path, settings_json=json.dumps({"settings": {}, "exec": "rm -rf"}))
    assert bad["outcome"] == "failed"


def test_malformed_stored_settings_are_recoverable(tmp_path):
    path = tmp_path / SETTINGS_OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not-json", encoding="utf-8")
    payload = generate_command_center(root=tmp_path, write=False)
    assert payload["settings_manager"]["warnings"]
    assert payload["settings_manager"]["settings"]["appearance"]["theme"] == "system"
