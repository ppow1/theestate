import json
from pathlib import Path


def actions():
    return json.loads(Path("collaboration/workstreams/WP-0201/proposed/action_metadata.json").read_text())


def test_controls_cover_settings_help_about():
    assert {a["target_tab"] for a in actions()} == {"settings", "help", "about"}


def test_local_only_and_mutations_confirmed():
    for action in actions():
        assert action["local_only_no_upload_guarantee"] is True
        if action["writes_artifacts"]:
            assert action["confirmation_requirement"] in {"confirm_generated_artifact", "preview_before_write"}


def test_diagnostics_has_sensitivity_warning():
    diag = next(a for a in actions() if a["action_id"] == "about.export_diagnostics_manifest")
    assert "sensitivity warning" in diag["description"].lower()
