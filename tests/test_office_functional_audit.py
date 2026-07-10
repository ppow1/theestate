from estate.core.office_functional_audit import run_office_functional_audit
from estate.core.office_command_surface import ACTION_CONTROLS
from estate.core.steward_command_center import OFFICE_NAVIGATION


def test_audit_inventories_navigation_actions_and_controls(tmp_path):
    result = run_office_functional_audit(tmp_path, write=True)
    records = result["records"]
    ids = {r["surface_id"] for r in records}
    for nav in OFFICE_NAVIGATION:
        assert f"navigation:{nav['id']}" in ids
    for action in ACTION_CONTROLS:
        assert f"action:{action['action_id']}" in ids
    assert "control:settings-theme" in ids
    assert (tmp_path / "runtime/steward/office_functional_audit.json").is_file()
    assert (tmp_path / "runtime/steward/office_repair_waves.json").is_file()
    assert result["summary"]["repair_waves"] == sorted(result["summary"]["repair_waves"], key=lambda x: x["wave"])


def test_audit_detects_missing_handlers_and_disabled_truthfully(tmp_path):
    result = run_office_functional_audit(tmp_path, write=False)
    actions = {r["action_id"]: r for r in result["records"] if r["surface_type"] == "office_action"}
    assert actions["ai_services.start_stop_load"]["classification"] == "missing_required_capability"
    assert actions["settings.save_apply"]["classification"] == "functional"
    assert all(r["classification"] in {"functional","partially_functional","display_only","placeholder","broken","duplicative","missing_required_capability"} for r in result["records"])
