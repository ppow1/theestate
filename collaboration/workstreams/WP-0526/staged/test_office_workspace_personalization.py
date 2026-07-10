from office_workspace_personalization import (
    WorkspaceDefaults,
    export_state,
    import_state,
    pin_item,
    recover_state,
    restore_defaults,
    save_layout,
    set_favorite_residents,
    set_quick_actions,
    set_section_order,
    unpin_item,
)


def test_save_reload_pin_unpin_order_and_defaults():
    defaults = WorkspaceDefaults("steward")
    state = restore_defaults(defaults)
    state = save_layout(state, "focused", visible_sections=["overview", "residents"], section_order=["residents", "overview"], preferences={"density": "compact"})
    state = set_section_order(state, "focused", ["overview", "residents"])
    state = pin_item(state, "project", "P-1")
    state = pin_item(state, "work_package", "WP-0526")
    state = pin_item(state, "resident", "steward")
    state = pin_item(state, "artifact", "A-1")
    state = unpin_item(state, "project", "P-1")
    state = set_favorite_residents(state, ["steward", "architect", "steward"])
    state = set_quick_actions(state, ["search_office", "new_work_package", "search_office"])

    reloaded = import_state(export_state(state), defaults)

    assert reloaded["active_layout_id"] == "focused"
    assert reloaded["saved_layouts"]["focused"]["section_order"] == ["overview", "residents"]
    assert reloaded["pins"]["project"] == []
    assert reloaded["pins"]["work_package"] == ["WP-0526"]
    assert reloaded["pins"]["resident"] == ["steward"]
    assert reloaded["pins"]["artifact"] == ["A-1"]
    assert reloaded["favorite_residents"] == ["steward", "architect"]
    assert reloaded["quick_actions"] == ["search_office", "new_work_package"]
    assert not reloaded["recovered_from_malformed_state"]

    restored = restore_defaults(defaults)
    assert restored["active_layout_id"] == "default"
    assert restored["pins"]["resident"] == []


def test_malformed_state_recovery_and_safe_import_export():
    defaults = WorkspaceDefaults("steward")
    recovered = recover_state({"schema": "bad", "saved_layouts": "broken", "pins": ["bad"]}, defaults)
    assert recovered["recovered_from_malformed_state"]
    assert recovered["active_layout_id"] == "default"
    assert recovered["pins"]["artifact"] == []

    bad_json = import_state("{not json", defaults)
    assert bad_json["recovered_from_malformed_state"]

    safe_json = export_state({"workspace_id": "steward", "pins": {"resident": ["r1"]}})
    assert '"schema":"estate.office_workspace_personalization.v1"' in safe_json
    assert '"staged_not_installed":true' in safe_json
