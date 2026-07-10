import json
import sys
import subprocess

from estate.core.operations_center_settings import SETTINGS_OUTPUT, load_operations_center_settings, save_operations_center_settings
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def test_settings_defaults_are_versioned_local_and_safe_when_missing(tmp_path):
    payload = load_operations_center_settings(tmp_path)

    assert payload["version"] == 1
    assert payload["ui_version"] == "operations-center-settings-v1"
    assert payload["effective_source"] == "documented_defaults"
    assert payload["settings"]["appearance"]["theme"] == "system"
    assert payload["settings"]["workspace"]["default_profile"] == "mission-control"
    assert payload["settings"]["operator_visibility"]["default_verbosity_profile"] == "default"
    assert payload["settings"]["refresh"]["quiet_refresh_seconds"] == 30
    assert payload["settings"]["persistence"] == {"local_only": True, "stores_secrets": False, "path": SETTINGS_OUTPUT}
    assert any(w["type"] == "settings_file_missing" for w in payload["warnings"])


def test_settings_persistence_and_command_center_integration(tmp_path):
    saved = save_operations_center_settings(
        tmp_path,
        appearance__theme="dark",
        appearance__accent="blue",
        workspace__default_profile="validation",
        operator_visibility__global_verbosity="detailed",
        refresh__quiet_refresh_seconds=45,
        command_console__mode="collapsed",
    )
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert (tmp_path / SETTINGS_OUTPUT).exists()
    assert saved["settings"]["appearance"]["theme"] == "dark"
    assert payload["workspace_profile"]["selected_profile"] == "validation"
    settings = payload["panels"]["settings"]["data"]
    assert settings["theme"]["value"] == "dark"
    assert settings["accent"] == "blue"
    assert settings["refresh_behavior"]["quiet_refresh_seconds"] == 45
    assert settings["command_console"]["mode"] == "collapsed"
    assert "Settings version:" in html
    assert "Default workspace:" in html


def test_invalid_settings_fail_safely_and_report_warnings(tmp_path):
    path = tmp_path / SETTINGS_OUTPUT
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"settings": {"settings_schema_version": 999, "appearance": {"theme": "neon"}, "workspace": {"default_profile": "missing", "visible_panels": []}, "operator_visibility": {"default_verbosity_profile": "missing", "global_verbosity": "loud"}, "refresh": {"mode": "storm", "quiet_refresh_seconds": -1}, "command_console": {"mode": "floating", "open_on_start": "yes"}}}), encoding="utf-8")

    payload = load_operations_center_settings(tmp_path)
    settings = payload["settings"]

    assert settings["settings_schema_version"] == 1
    assert settings["appearance"]["theme"] == "system"
    assert settings["workspace"]["default_profile"] == "mission-control"
    assert settings["operator_visibility"]["default_verbosity_profile"] == "default"
    assert settings["operator_visibility"]["global_verbosity"] == "normal"
    assert settings["refresh"]["mode"] == "quiet"
    assert settings["refresh"]["quiet_refresh_seconds"] == 30
    assert settings["refresh"]["enabled"] is True
    assert settings["command_console"]["mode"] == "inline"
    assert settings["command_console"]["open_on_start"] is False
    assert len([w for w in payload["warnings"] if w["type"] in {"invalid_setting", "settings_version_mismatch"}]) >= 8


def test_settings_cli_outputs_json(tmp_path):
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "operations-center-settings", "--json"], cwd=tmp_path, env={"PYTHONPATH": str(__import__('pathlib').Path.cwd() / 'src')}, text=True, capture_output=True, check=True)
    payload = json.loads(result.stdout)

    assert payload["ui_version"] == "operations-center-settings-v1"
    assert payload["settings"]["persistence"]["local_only"] is True
