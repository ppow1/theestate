import json
from urllib.parse import urlparse

from estate.core.office_command_surface import ACTION_CONTROLS, execute_office_action
from estate.core.steward_command_center import OFFICE_TABS, generate_command_center, render_command_center_html


def test_all_configured_tabs_route_to_rendered_panels(tmp_path):
    payload = generate_command_center(root=tmp_path, write=False)
    html = render_command_center_html(payload)
    for tab in payload["tabs"]:
        assert f"id='workspace-{tab['id']}'" in html
        assert f"data-tab='{tab['id']}'" in html


def test_invalid_startup_tab_falls_back_safely(tmp_path):
    settings = tmp_path / "runtime/steward/operations_center_settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"settings": {"workspace": {"default_active_tab": "not-a-tab"}}}), encoding="utf-8")
    payload = generate_command_center(root=tmp_path, write=False)
    html = render_command_center_html(payload)
    assert "id='workspace-settings' class='workspace-view active'" in html


def test_navigation_script_supports_hash_history_and_duplicate_protection(tmp_path):
    html = render_command_center_html(generate_command_center(root=tmp_path, write=False))
    assert "window.addEventListener('popstate'" in html
    assert "location.hash" in html
    assert "history.pushState" in html
    assert "pendingOfficeRequests.has(actionId)" in html


def test_action_request_ids_returned_and_artifacts_visible(tmp_path):
    result = execute_office_action("work_packages.validate_selected", root=tmp_path, request_id="req-0512")
    assert result["request_id"] == "req-0512"
    assert result["outcome"] == "blocked"
    html = render_command_center_html(generate_command_center(root=tmp_path, write=False))
    assert "Last Office action result" in html
    assert "req-0512" in html


def test_completed_blocked_failed_and_unregistered_render_distinctly(tmp_path, monkeypatch):
    completed = execute_office_action("notifications.refresh_center", root=tmp_path, request_id="done-1")
    blocked = execute_office_action("not.registered", root=tmp_path, request_id="blocked-1")
    from estate.core import office_command_surface as surface
    def boom(**_):
        raise RuntimeError("boom")
    monkeypatch.setitem(surface.HANDLERS, "notifications.refresh_center", boom)
    failed = execute_office_action("notifications.refresh_center", root=tmp_path, request_id="fail-1")
    assert completed["outcome"] == "completed"
    assert blocked["outcome"] == "blocked"
    assert failed["outcome"] == "failed"
    assert failed["diagnostics_path"]
    assert "No Office action is registered" in blocked["steward_message"]


def test_targeted_refresh_and_malformed_endpoint_recovery_are_in_browser_transport(tmp_path):
    html = render_command_center_html(generate_command_center(root=tmp_path, write=False))
    assert "fetch('/api/office/payload?tab='" in html
    assert "Malformed action response" in html
    assert "Recoverable targeted refresh failure" in html
    assert "stale_warning" in html
    assert "payload_version" in html


def test_no_arbitrary_action_id_invokes_unregistered_code(tmp_path):
    registered = {c["action_id"] for c in ACTION_CONTROLS}
    assert "os.system" not in registered
    result = execute_office_action("os.system", root=tmp_path, request_id="nope")
    assert result["outcome"] == "blocked"
    assert result["source_handler"] == "office_command_surface.execute_office_action"
