from estate.core.office_command_surface import controls_for_tab, execute_office_action


def test_wp0647_executive_workspace_is_reachable_from_existing_office_surface(tmp_path):
    controls = controls_for_tab("mission-control")
    assert any(c["action_id"] == "office_intelligence.refresh_executive_workspace" for c in controls)

    result = execute_office_action("office_intelligence.refresh_executive_workspace", root=tmp_path)

    assert result["outcome"] == "completed"
    assert result["source_handler"] == "estate.core.office_executive_workspace.build_executive_workspace"
    assert (tmp_path / "runtime/office/executive_workspace.json").exists()
    assert (tmp_path / "operations/steward/executive_workspace.md").exists()


def test_wp0647_ledger_exists_and_rejects_duplicate_system_creation():
    ledger = "operations/steward/estate_feature_activation_ledger.md"
    text = open(ledger, encoding="utf-8").read()

    assert "single operational activation record" in text
    assert "not a second registry, scheduler, queue, authority system" in text
    assert "Connected by WP-0647" in text
    assert "WP-4030 estate backup/restore | Staged only" in text
