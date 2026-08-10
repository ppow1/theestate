import json
import shutil
import threading
import urllib.request
from pathlib import Path

from estate.core.office_command_surface import controls_for_tab, execute_office_action
from estate.core.provider_capacity import ProviderCapacityRecord, write_capacity_record
from estate.core.provider_health import ProviderHealthRecord, write_health_record
import estate.core.steward_command_center as steward_command_center
from estate.core.steward_command_center import generate_command_center, render_command_center_html, serve_command_center
from estate.core.compute_resources import ComputeResourceObservation, canonical_resource_id, classify_observation, write_compute_projection


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def seed_dashboard_artifacts(root):
    write_json(root, "runtime/operations_runtime/status/latest.json", {"state": "running", "scheduler": {"state": "enabled"}})
    write_json(root, "runtime/background_operations/status/latest.json", {"state": "watching", "watch_state": "enabled"})
    write_json(root, "runtime/operations/status/active.json", [{
        "activity_id": "act-critical",
        "current_state": "Blocked",
        "requires_attention": True,
        "last_message": "Needs Steward attention",
        "severity": "critical",
        "work_package_id": "WP-0635",
        "artifact_paths": ["runtime/evidence/act-critical.json"],
        "metadata": {"summary_safe": True},
    }])
    write_json(root, "runtime/evidence/act-critical.json", {"evidence": "safe"})
    write_json(root, "runtime/post_merge_audit/status/latest.json", {"ring_2_queue": [{"id": "audit-1"}], "active_audits": [{"id": "audit-active"}]})
    write_json(root, "runtime/merge_discovery/status/latest.json", {"repository_targets": [{"repository": "estate-main", "state": "ready", "path": "runtime/merge_discovery/status/latest.json"}]})
    write_json(root, "data/registry/personnel.json", [{"employee_id": "E1", "display_name": "Helen", "office": "Workforce"}])


def test_operational_command_dashboard_aggregates_runtime_artifacts(tmp_path):
    seed_dashboard_artifacts(tmp_path)

    payload = generate_command_center(tmp_path, write=False)
    dashboard = payload["panels"]["office_operational_command_dashboard"]

    assert dashboard["available"] is True
    assert dashboard["data"]["summary"]["runtime_host"] == "running"
    assert dashboard["data"]["summary"]["exceptions_requiring_attention"] >= 1
    assert dashboard["data"]["repositories"][0]["repository"] == "estate-main"
    assert "Workforce" in dashboard["data"]["department_commitments"]
    assert "institutional acceptance remain distinct" in dashboard["data"]["authority_boundaries"]


def test_operational_command_dashboard_renders_filters_drilldown_and_controls(tmp_path):
    seed_dashboard_artifacts(tmp_path)

    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert "Office Operational Command Dashboard" in html
    assert "data-dashboard-filter='repository'" in html
    assert "act-critical" in html
    assert "operations_dashboard.inspect_evidence" in html
    assert "runtime/evidence/act-critical.json" in html
    assert "institutional acceptance" in html


def test_operational_dashboard_actions_are_real_and_safe(tmp_path):
    seed_dashboard_artifacts(tmp_path)
    actions = controls_for_tab("operational-dashboard")
    assert {a["action_id"] for a in actions} == {"operations_dashboard.refresh", "operations_dashboard.inspect_evidence"}
    assert all(a["availability"] == "available" for a in actions)

    result = execute_office_action("operations_dashboard.inspect_evidence", root=tmp_path, evidence_path="runtime/evidence/act-critical.json")
    assert result["outcome"] == "completed"
    assert result["target_tab"] == "operational-dashboard"
    assert "provider" not in " ".join(result.get("runtime_state_changed") or []).lower()


def test_operational_dashboard_renders_engineering_provider_capacity_from_runtime_projection(tmp_path):
    target = tmp_path / "config" / "providers"
    target.mkdir(parents=True)
    shutil.copy(Path("config/providers/catalog.json"), target / "catalog.json")
    write_health_record(ProviderHealthRecord.create(provider_id="codex.execution.cli", status="available", reported_by="test", message="ready"), root=tmp_path)
    write_capacity_record(ProviderCapacityRecord.create(provider_id="codex.execution.cli", capacity_state="available", reported_by="test", max_jobs=4, quota_remaining=3), root=tmp_path)
    payload = generate_command_center(tmp_path, write=True)
    dashboard = payload["panels"]["office_operational_command_dashboard"]["data"]
    provider = next(item for item in dashboard["engineering_provider_capacity"]["providers"] if item["provider_id"] == "codex.execution.cli")
    assert provider["engineering_provider_capacity"]["index"] == 75
    assert (tmp_path / "runtime/engineering_capacity/dashboard.json").is_file()
    html = render_command_center_html(payload)
    assert "Engineering Provider Capacity" in html
    assert "codex.execution.cli" in html
    assert "not physical GPU capacity" in html


def test_operational_dashboard_renders_real_codex_seat_fuel_instead_of_generic_heuristic(tmp_path):
    target = tmp_path / "config" / "providers"
    target.mkdir(parents=True)
    shutil.copy(Path("config/providers/catalog.json"), target / "catalog.json")
    write_health_record(ProviderHealthRecord.create(provider_id="codex.execution.cli", status="available", reported_by="test", message="ready"), root=tmp_path)
    write_capacity_record(ProviderCapacityRecord.create(provider_id="codex.execution.cli", capacity_state="busy", reported_by="test", max_jobs=4, quota_remaining=1), root=tmp_path)
    write_json(tmp_path, "runtime/engineering_capacity/codex_seat_telemetry.json", {
        "version": 1,
        "seats": [
            {"seat_id": seat, "capacity_identity": f"codex.seat.{seat}", "collection_status": "available", "observed_at": "2026-08-10T12:00:00Z", "weekly_limit_percent_left": percent, "weekly_limit_reset_at": "2026-08-15T16:32:00Z", "windows": [], "native_rate_limits": {}, "account": {"type": "chatgpt"}}
            for seat, percent in (("C1", 88), ("C2", 63), ("C3", 36))
        ],
    })

    payload = generate_command_center(tmp_path, write=True)
    html = render_command_center_html(payload)

    assert "Codex Seat C1" in html
    assert "Codex Seat C2" in html
    assert "Codex Seat C3" in html
    assert "88% left" in html
    assert "codex.execution.cli" not in html


def test_operational_dashboard_renders_shared_two_gpu_observability(tmp_path):
    seed_dashboard_artifacts(tmp_path)
    devices = []
    for uuid, name, used in (("GPU-1", "RTX 4090", 6000), ("GPU-2", "Tesla P100", 2000)):
        device = ComputeResourceObservation(resource_id=canonical_resource_id("host-a", uuid), host_id="host-a", nvidia_uuid=uuid, name=name, memory_total_mib=16000, memory_used_mib=used, memory_free_mib=16000-used, utilization_percent=62 if uuid == "GPU-1" else 4, observed_at="2026-08-10T20:00:00Z")
        devices.append(classify_observation(device, now="2026-08-10T20:00:10Z"))
    write_compute_projection(devices, tmp_path)
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "GPU Operational Observability" in html
    assert "GPU1" in html and "GPU2" in html
    assert "62% compute" in html and "4% compute" in html
    assert "37.5% VRAM" in html and "12.5% VRAM" in html
    assert "No Estate-recognized reservation" in html
    assert "#gpu-detail-gpu1" in html and "#gpu-detail-gpu2" in html


def test_operational_command_is_reachable_without_merging_operational_activity(tmp_path):
    payload = generate_command_center(tmp_path, write=False)
    navigation = {item["id"]: item for item in payload["navigation"]["items"]}
    tabs = {item["id"]: item for item in payload["tabs"]}
    assert navigation["operational-dashboard"]["label"] == "Operational Command"
    assert navigation["operational-dashboard"]["panel"] == "office_operational_command_dashboard"
    assert tabs["operational-dashboard"]["label"] == "Operational Command"
    assert "operational-dashboard" in {item["id"] for item in payload["tabs"]}
    assert "operational-activity" in {item["id"] for item in payload["tabs"]}

    html = render_command_center_html(payload)
    assert "data-tab='operational-dashboard'" in html
    assert "id='workspace-operational-dashboard'" in html
    assert "id='workspace-operational-activity'" in html
    assert "Office Operational Command Dashboard" in html
    assert html.count("Engineering Provider Capacity") == 1
    assert "#operational-dashboard" in html


def test_gpu_hash_route_focuses_detail_after_dashboard_materialization(tmp_path):
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "function focusGpuFromHash()" in html
    assert "document.getElementById('gpu-detail-' + gpu)" in html
    assert "[0, 100, 300, 700, 1200]" in html
    assert "window.scrollTo" in html
    assert "target.focus({preventScroll:true})" in html
    assert "currentDashboard.replaceWith(nextDashboard); focusGpuFromHash();" in html


def test_gpu_lost_reason_and_compact_service_access_strip_are_truthful(tmp_path):
    seed_dashboard_artifacts(tmp_path)
    manifest = tmp_path / "runtime" / "ai_services" / "implementations" / "open_webui" / "service.manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"default_endpoint": "http://127.0.0.1:8080"}), encoding="utf-8")
    devices = [ComputeResourceObservation(
        resource_id=canonical_resource_id("host-a", "GPU-2"),
        host_id="host-a", nvidia_uuid="GPU-2", name="Tesla P100",
        logical_gpu_id="GPU2", health_state="LOST", health_reasons=["Windows reports the expected physical device absent or in a problem state"],
        health_classification="DEVICE_MISSING", observed_at="2026-08-10T20:00:00Z",
    )]
    write_compute_projection(devices, tmp_path)
    html = render_command_center_html(generate_command_center(tmp_path, write=False))
    assert "Windows reports the expected physical device absent or in a problem state" in html
    assert "id='service-access-strip'" in html
    assert "Estate Core" in html and "Resident Gateway" in html and "Open WebUI" in html
    assert "target='_blank'" in html
    assert "read-only local service evidence" in html


def test_served_operations_center_refreshes_codex_seat_quota_without_restart(monkeypatch, tmp_path):
    values = iter((42,))

    initial_payload = {
        "version": 1,
        "source": "test",
        "seats": [
            {"seat_id": seat, "capacity_identity": f"codex.seat.{seat}", "collection_status": "available", "observed_at": "2026-08-10T20:21:00Z", "weekly_limit_percent_left": 41, "weekly_limit_reset_at": "2026-08-15T20:32:40Z", "windows": [], "native_rate_limits": {}, "account": {"type": "chatgpt"}, "execution_modes": ["cli"], "execution_surface": "codex-cli"}
            for seat in ("C1", "C2", "C3")
        ],
    }
    write_json(tmp_path, "runtime/engineering_capacity/codex_seat_telemetry.json", initial_payload)
    generate_command_center(tmp_path, write=True)

    def fake_collect(*, root, write=True, **kwargs):
        percent = next(values)
        payload = {
            "version": 1,
            "source": "test",
            "seats": [
                {"seat_id": seat, "capacity_identity": f"codex.seat.{seat}", "collection_status": "available", "observed_at": f"2026-08-10T20:2{percent % 10}:00Z", "weekly_limit_percent_left": percent, "weekly_limit_reset_at": "2026-08-15T20:32:40Z", "windows": [], "native_rate_limits": {}, "account": {"type": "chatgpt"}, "execution_modes": ["cli"], "execution_surface": "codex-cli"}
                for seat in ("C1", "C2", "C3")
            ],
        }
        write_json(root, "runtime/engineering_capacity/codex_seat_telemetry.json", payload)
        return payload

    monkeypatch.setattr(steward_command_center, "collect_codex_seat_telemetry", fake_collect)
    monkeypatch.setattr(steward_command_center, "discover_grace_gpus", lambda: [])
    monkeypatch.setattr(steward_command_center.time, "monotonic", iter((0.0, 31.0, 31.0)).__next__)
    server = serve_command_center(host="127.0.0.1", port=0, root=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        initial = urllib.request.urlopen(base + "/", timeout=5).read().decode()
        refreshed = json.loads(urllib.request.urlopen(base + "/status.json", timeout=5).read().decode())
        assert "41% left" in initial
        assert "42% left" in refreshed["operational_dashboard_html"]
        assert all(f"Codex Seat {seat}" in refreshed["operational_dashboard_html"] for seat in ("C1", "C2", "C3"))
        assert "codex.execution.cli" not in refreshed["operational_dashboard_html"]
        assert "observed=2026-08-10T20:22:00Z" in refreshed["operational_dashboard_html"]
        assert server.server_address[1] != 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
