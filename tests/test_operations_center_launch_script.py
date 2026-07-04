from pathlib import Path


SCRIPT = Path("launch_operations_center.ps1")


def test_launch_script_is_steward_facing_local_first_entry_point():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "src/estate/core/operations_center_bootstrap.py" in text
    assert "operations-center-settings" in text
    assert "operations-center\", \"start" in text
    assert "Local URL:" in text
    assert "Safe shutdown:" in text
    assert "no cloud dependency" in text.lower()
    assert "no secret storage" in text.lower()
    assert "no automatic work package execution" in text.lower()
    assert "no Steward authorization bypass" in text


def test_launch_script_checks_dependencies_and_uses_existing_bootstrap():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "Get-Command python" in text
    assert "Get-Command py" in text
    assert "PYTHONPATH" in text
    assert "ESTATE_ROOT" in text
    assert "estate.cli.main" in text
    assert "operations-center\", \"start" in text
    assert "steward-command-center" not in text
