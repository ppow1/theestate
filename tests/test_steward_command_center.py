import json
import sys
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.steward_command_center import generate_command_center, render_command_center_html, serve_command_center


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed_inputs(root):
    write_json(root, "data/registry/residents.json", [
        {"id": "RES-000001", "name": "Alfred", "department": "Administration", "office": "Manager of Administration", "status": "Active", "role": "Coordinates the Estate."},
        {"id": "RES-000003", "name": "Helen", "department": "Human Resources", "office": "Manager of Human Resources", "status": "Active", "role": "Manages resident and worker assignment fit."},
    ])
    write_json(root, "data/registry/personnel.json", [{"employee_id": 6, "display_name": "Helen", "mailbox_id": 6, "resident_id": "RES-000003"}])
    write_json(root, "data/registry/mailboxes.json", [{"mailbox_id": 10100, "display_name": "Alfred Routing Intake", "owning_office": "Chief of Staff"}])
    write_json(root, "data/objects/RES-000001.json", {"id": "RES-000001", "name": "Alfred"})
    write_json(root, "data/objects/RES-000003.json", {"id": "RES-000003", "name": "Helen"})
    write_json(root, "collaboration/mailboxes/index.json", {"summary": {"message_count": 3}})
    (root / "operations/briefings").mkdir(parents=True, exist_ok=True)
    (root / "operations/briefings/morning_briefing.md").write_text("# Morning Briefing\n", encoding="utf-8")
    (root / "operations/work_packages").mkdir(parents=True, exist_ok=True)
    (root / "operations/work_packages/assignment_queue.md").write_text("# Assignment Queue\n", encoding="utf-8")
    write_json(root, "runtime/audit/latest.json", {"summary": {"failed": 0}})
    write_json(root, "runtime/capabilities/capability_lifecycle_report.json", {"summary": {"warning_count": 0}})
    write_json(root, "runtime/dependencies/dependency_graph.json", {"summary": {"warning_count": 0}})
    write_json(root, "runtime/mailboxes/synchronization_duty_latest.json", {"summary": {"warning_count": 0}})
    write_json(root, "runtime/audit/recall_audit_log.json", {"summary": {"warning_count": 0}})
    write_json(root, "runtime/workers/worker_runtime_heartbeat.json", {"summary": {"worker_count": 1, "stale_worker_count": 0, "status_counts": {"active": 1, "blocked": 0}, "warning_count": 0}, "workers": []})


def test_command_center_renders_all_initial_panels(tmp_path):
    seed_inputs(tmp_path)
    payload = generate_command_center(tmp_path)
    html = render_command_center_html(payload)

    for title in ["Alfred Resident Card", "Helen Resident Card", "Morning Briefing", "Steward Decision Queue", "Mailbox Summary", "Work Package Pipeline", "Validation and Estate Health", "Validation Status"]:
        assert title in html
    assert (tmp_path / "runtime/steward/command_center.html").exists()


def test_command_center_degrades_gracefully_when_artifacts_are_missing(tmp_path):
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert payload["panels"]["alfred_resident_card"]["available"] is False
    assert "Supporting artifact is not available yet." in html
    assert "No pending Steward decisions were found" in html


def test_command_center_starts_local_http_server(tmp_path):
    seed_inputs(tmp_path)
    server = serve_command_center(host="127.0.0.1", port=0, root=tmp_path)
    try:
        host, port = server.server_address
        import threading
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        response = urlopen(f"http://{host}:{port}/", timeout=5)
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert "Office of the Steward" in body
        assert "Mailbox Summary" in body
    finally:
        server.shutdown()
        server.server_close()


def test_command_center_cli_generates_json(tmp_path):
    import subprocess

    seed_inputs(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "steward-command-center", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["panels"]["alfred_resident_card"]["available"] is True
    assert (tmp_path / "runtime/steward/command_center.html").exists()


def test_command_center_renders_status_bar_and_activity_console(tmp_path):
    seed_inputs(tmp_path)
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert payload["status_bar"]["validation_state"] == "Validation passing"
    assert payload["status_bar"]["health_state"] in {"pass", "warning"}
    assert payload["status_bar"]["mailbox_count"] == 3
    assert payload["activity_console"]["events"]
    assert 'id="status-bar"' in html
    assert "Estate" in html
    assert "Validation passing" in html
    assert "Health" in html
    assert 'id="activity-console"' in html
    assert "Activity Console" in html
    assert "verbosity-selector" in html
    assert "Quiet" in html
    assert "Normal" in html


def test_activity_console_missing_data_state_is_visible(tmp_path):
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert payload["status_bar"]["estate_status"] == "Needs data"
    assert any(event["severity"] == "missing" for event in payload["activity_console"]["events"])
    assert "missing" in html
    assert "Supporting artifact is not available yet." in html


def test_command_center_status_json_supports_quiet_refresh(tmp_path):
    seed_inputs(tmp_path)
    server = serve_command_center(host="127.0.0.1", port=0, root=tmp_path)
    try:
        host, port = server.server_address
        import threading
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        response = urlopen(f"http://{host}:{port}/status.json", timeout=5)
        payload = json.loads(response.read().decode("utf-8"))
        assert response.status == 200
        assert payload["status_bar"]["validation_state"] == "Validation passing"
        assert 'id="status-bar"' in payload["status_bar_html"]
        assert 'id="activity-console"' in payload["activity_console_html"]
    finally:
        server.shutdown()
        server.server_close()


def test_work_package_pipeline_groups_representative_states_and_copyable_commands(tmp_path):
    seed_inputs(tmp_path)
    base = tmp_path / "collaboration/work_packages"
    (base / "pending").mkdir(parents=True, exist_ok=True)
    (base / "open").mkdir(parents=True, exist_ok=True)
    (base / "completions").mkdir(parents=True, exist_ok=True)
    (tmp_path / "collaboration/messages").mkdir(parents=True, exist_ok=True)
    (base / "pending/WP-9001_SERIES_ready.md").write_text("# SERIES TASK WP-9001 — Ready Package\n\n## Codex Command\nRun me.\n", encoding="utf-8")
    (base / "pending/WP-9002_SERIES_blocked.md").write_text("# SERIES TASK WP-9002 — Blocked Package\n\n## Blockers\n- Needs approval\n", encoding="utf-8")
    (base / "open/WP-LEAP-001_Audit_Worker_v1_Local_Ollama.md").write_text("# Work Package WP-LEAP-001\n", encoding="utf-8")
    write_json(tmp_path, "collaboration/work_packages/completions/WP-9003_codex_done.json", {"work_package_id": "WP-9003", "codex_status": "done", "ready_for_ca_review": True})
    (base / "pending/WP-9003_SERIES_review_ready.md").write_text("# SERIES TASK WP-9003 — Review Ready\n", encoding="utf-8")
    write_json(tmp_path, "collaboration/work_packages/completions/WP-9004_codex_done.json", {"work_package_id": "WP-9004", "codex_status": "done", "ready_for_ca_review": True})
    (base / "pending/WP-9004_SERIES_completed.md").write_text("# SERIES TASK WP-9004 — Completed Package\n", encoding="utf-8")
    write_json(tmp_path, "collaboration/messages/msg_review_wp9004.json", {"payload": {"title": "Review WP-9004", "summary": "WP-9004 reviewed"}})

    payload = generate_command_center(tmp_path, write=False)
    pipeline = payload["panels"]["work_package_pipeline"]["data"]["sections"]
    html = render_command_center_html(payload)

    assert any(item["work_package_id"] == "WP-9001" for item in pipeline["pending"])
    assert any(item["work_package_id"] == "WP-9002" for item in pipeline["blocked"])
    assert any(item["work_package_id"] == "WP-LEAP-001" for item in pipeline["active"])
    assert any(item["work_package_id"] == "WP-9003" for item in pipeline["review-ready"])
    assert any(item["work_package_id"] == "WP-9004" for item in pipeline["completed"])
    assert "Missing-data" in html
    assert "textarea readonly" in html
    assert "collaboration/work_packages/pending/WP-9001_SERIES_ready.md" in html


def test_validation_health_dashboard_shows_pass_warning_fail_stale_and_missing_states(tmp_path):
    seed_inputs(tmp_path)
    write_json(tmp_path, "runtime/validation/local_operational_validation_run.json", {"summary": {"ok": True, "failed_steps": 0, "warning_count": 0}, "warnings": []})
    write_json(tmp_path, "runtime/capabilities/capability_lifecycle_report.json", {"summary": {"warning_count": 1}, "warnings": [{"type": "lifecycle_gap", "message": "Capability has missing validation evidence."}]})
    write_json(tmp_path, "runtime/dependencies/dependency_graph.json", {"summary": {"failed": 1}, "warnings": []})
    write_json(tmp_path, "runtime/workers/worker_runtime_heartbeat.json", {"summary": {"worker_count": 2, "stale_worker_count": 1, "status_counts": {"active": 1, "blocked": 1}, "warning_count": 1}, "warnings": []})
    # Leave mailbox synchronization missing and make recall audit stale.
    (tmp_path / "runtime/mailboxes/synchronization_duty_latest.json").unlink()
    import os, time
    old = time.time() - 72 * 3600
    os.utime(tmp_path / "runtime/audit/recall_audit_log.json", (old, old))

    payload = generate_command_center(tmp_path, write=False)
    health = payload["panels"]["validation_health_dashboard"]["data"]
    html = render_command_center_html(payload)
    states = {check["label"]: check["state"] for check in health["checks"]}

    assert states["Local operational validation"] == "pass"
    assert states["Capability lifecycle report"] == "warning"
    assert states["Dependency graph report"] == "fail"
    assert states["Mailbox synchronization report"] == "missing"
    assert states["Recall audit report"] == "warning"
    assert states["Worker heartbeat report"] == "warning"
    assert health["overall_health"] == "fail"
    assert "Capability has missing validation evidence." in html
    assert "runtime/dependencies/dependency_graph.json" in html
    assert "Review failing validation source reports" in html


def test_command_center_office_navigation_and_tabs_cover_initial_areas(tmp_path):
    seed_inputs(tmp_path)
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    labels = [item["label"] for item in payload["navigation"]["items"]]
    assert labels == [
        "Home",
        "Mission Control",
        "Alfred",
        "Helen",
        "Resident Conversations",
        "Daily Board",
        "Active Projects",
        "Expansion Roadmap",
        "Parking Lot",
        "Work Packages",
        "Mailboxes",
        "Recalls",
        "Validation",
        "Search",
        "Settings",
        "Help",
        "About",
    ]
    assert "id='workspace-tabs'" in html
    assert "id='office-navigation'" in html
    assert "data-tab='settings'" in html
    assert "id='workspace-mission-control'" in html
    assert "id='workspace-search'" in html
    assert "id='workspace-recalls'" in html
    assert "id='workspace-resident-conversations'" in html
    assert "id='workspace-help'" in html
    assert "id='workspace-about'" in html
    assert "Operations Center Help" in html
    assert "Global Search and Command Palette" in html
    assert "Theme <select disabled>" in html
    assert "Per-topic verbosity placeholders" in html
    assert "Component / Version Inventory" in html
    assert "unknown/unavailable" in html


def test_command_center_settings_and_about_inventory_handle_unknown_versions(tmp_path):
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    settings = payload["panels"]["settings"]
    about = payload["panels"]["about"]

    assert settings["available"] is True
    assert settings["data"]["theme"]["options"] == ["light", "dark", "system"]
    assert settings["data"]["activity_console_visible"] is True
    assert "per_topic_verbosity" in settings["data"]
    assert "per_resident_verbosity" in settings["data"]
    assert about["available"] is True
    assert any(item["version"] == "unknown/unavailable" for item in about["data"]["inventory"])
    assert "runtime/steward/command_center.html" in html
    assert "unknown/unavailable" in html



def test_operations_center_help_surface_lists_commands_docs_and_unavailable_features(tmp_path):
    seed_inputs(tmp_path)
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    help_panel = payload["panels"]["help"]
    data = help_panel["data"]

    assert help_panel["available"] is True
    assert data["ui_version"] == "Operations Center v1 / Help and About surfaces v1"
    assert data["active_workspace_profile"]
    assert any(panel["id"] == "help" for panel in data["panels"])
    assert any(workspace["id"] == "help" for workspace in data["workspaces"])
    assert data["command_console_help"]["command_count"] > 0
    assert any(command["command"] == "steward-command-center" for command in data["command_console_help"]["commands"])
    assert any(doc["label"] == "WP-0092 validation report" and doc["available"] is False for doc in data["documentation_links"])
    assert data["known_unavailable_features"]
    assert "Command Console Help" in html
    assert "Service Catalog and Validation Links" in html
    assert "Local-first / Authority Boundary Notes" in html
    assert "unknown/unavailable" in html

def test_command_center_tab_switch_script_and_collapsible_navigation_are_rendered(tmp_path):
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert "function activateOfficeTab" in html
    assert "Office Navigation</summary>" in html
    assert "role='tabpanel' hidden" in html
    assert 'id="activity-console"' in html
    assert 'id="status-bar"' in html



def test_operations_center_layout_framework_declares_regions_and_persistence(tmp_path):
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    layout = payload["layout_framework"]
    data = layout["data"]
    region_ids = {region["id"] for region in data["regions"]}

    assert layout["available"] is True
    assert data["version"] == "layout-framework-v1"
    assert data["layout_preference_key"] == "estate.operations_center.layout.v1"
    assert {"top_navigation_tabs", "left_navigation_panel", "main_workspace", "bottom_activity_stream", "status_bar", "command_console"}.issubset(region_ids)
    assert data["default_preferences"]["activity_console_dock"] == "bottom"
    assert data["default_preferences"]["activity_console_visible"] is True
    assert "Mission Control" in data["future_integration_points"]
    assert "TTS/STT" in data["future_integration_points"]
    assert "localStorage" in html
    assert "LAYOUT_PREF_KEY" in html
    assert "restoreLayoutPreferences" in html
    assert "Operations Center Layout Framework" in html

def test_mailbox_operations_center_summarizes_open_ack_steward_and_warnings(tmp_path):
    seed_inputs(tmp_path)
    write_json(tmp_path, "data/registry/personnel.json", [
        {"employee_id": 1, "display_name": "Steward", "mailbox_id": 1, "resident_id": "RES-000002"},
        {"employee_id": 6, "display_name": "Helen", "mailbox_id": 6, "resident_id": "RES-000003"},
    ])
    write_json(tmp_path, "data/registry/mailboxes.json", [
        {"mailbox_id": 10004, "mailbox_type": "office", "display_name": "Human Resources Office", "owning_office": "Human Resources"},
    ])
    write_json(tmp_path, "collaboration/mailboxes/index.json", {"messages": [
        {"message_id": "m-open", "title": "Open HR note", "destination_mailbox_id": 10004, "status": "open", "requires_ack": False, "path": "collaboration/messages/m-open.json"},
        {"message_id": "m-ack", "title": "Helen acknowledgement", "destination_mailbox_id": 6, "status": "open", "requires_ack": True, "ack_status": "pending", "path": "collaboration/messages/m-ack.json"},
        {"message_id": "m-steward", "title": "Steward action", "destination": "office.steward", "destination_mailbox_id": 1, "status": "open", "requires_ack": True, "path": "collaboration/messages/m-steward.json"},
        {"message_id": "m-warning", "title": "Ambiguous route", "destination": "queue", "destination_mailbox_id": None, "status": "open", "requires_ack": True, "warning": "unresolved destination: queue", "path": "collaboration/messages/m-warning.json"},
    ]})
    write_json(tmp_path, "runtime/mailboxes/synchronization_duty_latest.json", {"generated_at": "2026-07-03T00:00:00Z", "summary": {"warning_count": 0}})

    payload = generate_command_center(tmp_path, write=False)
    center = payload["panels"]["mailbox_operations_center"]["data"]
    html = render_command_center_html(payload)

    assert center["summary"]["open_message_count"] == 4
    assert center["summary"]["ack_required_count"] == 3
    assert center["summary"]["waiting_on_steward_count"] == 1
    assert center["summary"]["warning_count"] == 1
    assert center["summary"]["last_mailbox_synchronization_time"] == "2026-07-03T00:00:00Z"
    assert payload["status_bar"]["mailbox_open_count"] == 4
    assert payload["status_bar"]["mailbox_ack_required_count"] == 3
    assert payload["status_bar"]["mailbox_warning_count"] == 1
    assert "Mailbox Operations Center" in html
    assert "Show summarized messages" in html
    assert "Acknowledgement-required messages" in html
    assert "unresolved destination: queue" in html
    assert "does not mark mail read or acknowledged" in html


def test_mailbox_operations_center_handles_empty_and_missing_artifacts(tmp_path):
    seed_inputs(tmp_path)
    write_json(tmp_path, "collaboration/mailboxes/index.json", {"messages": []})
    (tmp_path / "runtime/mailboxes/synchronization_duty_latest.json").unlink()

    payload = generate_command_center(tmp_path, write=False)
    center = payload["panels"]["mailbox_operations_center"]["data"]
    html = render_command_center_html(payload)

    assert center["summary"]["message_count"] == 0
    assert "No mailbox messages were found" in html
    assert "Missing supporting mailbox artifact" in html
    assert "mailbox_synchronization" in center["missing_sources"]


def test_mailbox_operations_center_can_fallback_to_communication_bus_messages(tmp_path):
    seed_inputs(tmp_path)
    (tmp_path / "collaboration/mailboxes/index.json").unlink()
    write_json(tmp_path, "collaboration/messages/msg_bus_mail.json", {
        "id": "msg_bus_mail",
        "title": "Bus-only mailbox item",
        "destination": "mailbox.6",
        "status": "open",
        "requires_ack": True,
        "created_at": "2026-07-03T02:00:00+00:00",
    })

    payload = generate_command_center(tmp_path, write=False)
    center = payload["panels"]["mailbox_operations_center"]
    html = render_command_center_html(payload)

    assert center["available"] is True
    assert center["path"] == "collaboration/messages/*.json"
    assert center["data"]["summary"]["message_count"] == 1
    assert center["data"]["missing_sources"]
    assert "Bus-only mailbox item" in html
    assert "Missing supporting mailbox artifact(s): mailbox_index" in html


def test_daily_board_workspace_renders_board_parking_lot_conditions_and_sources(tmp_path):
    seed_inputs(tmp_path)
    (tmp_path / "operations/boards").mkdir(parents=True, exist_ok=True)
    (tmp_path / "operations/boards/daily_board.md").write_text("""# Daily Task Board

## Today
| ID | Task | Owner | Status | Blocker | Review Required | Next Action |
|---|---|---|---|---|---|---|
| DT-1 | Ship dashboard | Alfred | Active | None | Yes | Review UI |

## Waiting
| ID | Item | Waiting On | Since | Next Check |
|---|---|---|---|---|

## Blocked
| ID | Item | Blocker | Owner | Escalation Needed |
|---|---|---|---|---|
| BL-1 | Deploy | Missing review | Worker | No |

## Review Required
| ID | Item | Reviewer | Reason | Ready Since |
|---|---|---|---|---|
| RV-1 | Board | Steward | UX check | today |
""", encoding="utf-8")
    (tmp_path / "operations/boards/active_work.md").write_text("""# Active Work Board

## Active Work
| ID | Effort | Owner | Status | Current Milestone | Dependency | Next Action |
|---|---|---|---|---|---|---|
| AW-1 | Operations Center | Alfred | Active | v1 | None | Continue |
""", encoding="utf-8")
    (tmp_path / "operations/boards/parking_lot.md").write_text("""# Parking Lot

## Parking Lot Items
| ID | Idea | Category | Priority | Originator | Date Captured | Status | Target Milestone | Promotion Condition |
|---|---|---|---|---|---|---|---|---|
| PL-1 | Later idea | Automation | Strategic | Steward | today | Captured | Later | Three repeats |
""", encoding="utf-8")
    (tmp_path / "operations/boards/daily_board_integration.md").write_text("""# Daily Board Integration

## Parking Lot Promotion Conditions
- PL-1: Later idea — ready_for_review — Three repeats

## Parking Lot Items Ready for Review
- PL-1: Later idea

## Recommended Next Actions
- Human-review parking_lot.ready_for_review; do not auto-promote from this report.
""", encoding="utf-8")

    payload = generate_command_center(tmp_path, write=False)
    workspace = payload["panels"]["daily_board_workspace"]
    html = render_command_center_html(payload)

    assert workspace["available"] is True
    assert workspace["data"]["daily_priorities"][0]["Task"] == "Ship dashboard"
    assert workspace["data"]["parking_lot_items"][0]["Promotion Condition"] == "Three repeats"
    assert "This workspace keeps today’s Daily Board separate" in html
    assert "not automatically promoted" in html
    assert "PL-1: Later idea" in html
    assert "operations/boards/parking_lot.md" in html


def test_daily_board_workspace_empty_and_missing_states(tmp_path):
    seed_inputs(tmp_path)
    (tmp_path / "operations/boards").mkdir(parents=True, exist_ok=True)
    (tmp_path / "operations/boards/daily_board.md").write_text("# Daily Task Board\n", encoding="utf-8")
    (tmp_path / "operations/boards/parking_lot.md").write_text("# Parking Lot\n", encoding="utf-8")
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)
    assert "No current daily priorities were found in the Daily Board." in html
    assert "No Parking Lot items were found." in html

    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    missing_payload = generate_command_center(empty_root, write=False)
    missing_html = render_command_center_html(missing_payload)
    assert missing_payload["panels"]["daily_board_workspace"]["available"] is False
    assert "Daily Board and Parking Lot source artifacts are not available yet." in missing_html


def test_expansion_roadmap_workspace_shows_states_sources_and_candidates(tmp_path):
    seed_inputs(tmp_path)
    (tmp_path / "operations/boards").mkdir(parents=True, exist_ok=True)
    (tmp_path / "operations/boards/roadmap.md").write_text("""# Strategic Roadmap

## Roadmap
| Capability | Current Milestone | Status | Key Dependency | Future Initiative |
|---|---|---|---|---|
| Proposed Wing | Exploration | Proposed | Steward signal | Research scope |
| Planned Wing | Build runway | Planned | ADR needed | First epic |
| Active Wing | v1 | Active | None | Stabilize |
| Completed Wing | v0 | Completed | Done | Observe |
""", encoding="utf-8")
    write_json(tmp_path, "data/registry/missions.json", {"missions": [{"mission_id": "MISSION-9999", "mission_title": "Planned Mission", "status": "planned", "mission_type": "expansion", "related_work_packages": ["WP-9999"], "notes": "Needs staged epic review."}]})
    (tmp_path / "operations/boards/parking_lot.md").write_text("""# Parking Lot

## Parking Lot Items
| ID | Idea | Category | Priority | Originator | Date Captured | Status | Target Milestone | Promotion Condition |
|---|---|---|---|---|---|---|---|---|
| PL-99 | Future candidate | Expansion | Medium | Steward | today | Captured | Later | Pattern repeats |
""", encoding="utf-8")
    (tmp_path / "Architecture/ADR").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Architecture/ADR/ADR-9999-Proposal.md").write_text("# ADR-9999 Expansion Choice Proposal\n\nStatus: Proposed\n", encoding="utf-8")

    payload = generate_command_center(tmp_path, write=False)
    roadmap = payload["panels"]["expansion_roadmap"]
    html = render_command_center_html(payload)
    statuses = {item["title"]: item["status"] for item in roadmap["data"]["items"]}

    assert roadmap["available"] is True
    assert statuses["Proposed Wing"] == "proposed"
    assert statuses["Planned Wing"] == "planned"
    assert statuses["Active Wing"] == "active"
    assert statuses["Completed Wing"] == "completed"
    assert "Future candidate" in html
    assert "ADR-9999 Expansion Choice Proposal" in html
    assert "operations/boards/roadmap.md" in html
    assert "data/registry/missions.json" in html
    assert "does not approve, commit, or promote future work" in html


def test_expansion_roadmap_workspace_missing_state_is_clear(tmp_path):
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert payload["panels"]["expansion_roadmap"]["available"] is False
    assert "Expansion roadmap source artifacts are not available yet." in html


def test_steward_recall_operations_view_renders_recall_lifecycle_states(tmp_path):
    write_json(tmp_path, "runtime/notifications/notification_router_report.json", {
        "notifications": [
            {"id": "recall-active", "class": "recall", "summary": "Active recall", "reason": "security", "requested_by": "worker.ca3", "originating_worker": "ca3", "action": "prepare_recall_delivery", "eligible_for_immediate_delivery": True, "timestamp": "2026-07-03T10:00:00+00:00"},
            {"id": "ordinary-note", "class": "informational", "summary": "Ordinary notification"},
        ]
    })
    write_json(tmp_path, "runtime/audit/recall_audit_log.json", {
        "records": [
            {"record_id": "recall-delivered", "recall_reason": "operational", "requested_by": "alfred", "delivery_result": "sent", "acknowledgement_state": "pending", "timestamp": "2026-07-03T11:00:00+00:00"},
            {"record_id": "recall-failed", "recall_reason": "constitutional", "delivery_result": "failed", "acknowledgement_state": "pending", "timestamp": "2026-07-03T12:00:00+00:00"},
            {"record_id": "recall-acked", "recall_reason": "architectural", "delivery_result": "sent", "acknowledgement_state": "acknowledged", "timestamp": "2026-07-03T13:00:00+00:00"},
            {"record_id": "recall-unknown-ack", "recall_reason": "security", "delivery_result": "sent", "timestamp": "2026-07-03T14:00:00+00:00"},
        ]
    })
    write_json(tmp_path, "runtime/notifications/gotify_delivery_report.json", {"status": "sent", "generated_at": "2026-07-03T11:01:00+00:00", "payload": {"message": "Recall Steward. reason=operational; requested_by=alfred; action=prepare_recall_delivery"}})
    write_json(tmp_path, "runtime/briefings/morning_briefing.json", {"sections": {"outstanding_recalls": [{"record_id": "recall-delivered", "recall_reason": "operational", "acknowledgement_state": "pending"}]}})

    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)
    recall_panel = payload["panels"]["steward_recall_operations"]

    assert recall_panel["data"]["summary"]["active_recall_count"] == 5
    assert payload["status_bar"]["active_recall_count"] == 5
    assert "Steward Recall Operations" in html
    assert "Active recall" in html
    assert "Ordinary notification" not in html
    assert "delivery_failed" in html
    assert "acknowledged" in html
    assert "unknown" in html
    assert "does not send, approve, escalate, or acknowledge recalls" in html


def test_steward_recall_operations_view_handles_no_recalls_and_missing_artifacts(tmp_path):
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    recall_panel = payload["panels"]["steward_recall_operations"]
    assert recall_panel["data"]["summary"]["recall_count"] == 0
    assert recall_panel["data"]["summary"]["active_recall_count"] == 0
    assert payload["status_bar"]["active_recall_count"] == 0
    assert "No recall requests were found in available local artifacts." in html
    assert "Missing recall artifact" in html
