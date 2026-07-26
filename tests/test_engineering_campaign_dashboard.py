import json
import shutil
from pathlib import Path

from estate.core.engineering_campaign_dashboard import dashboard_operation, load_engineering_campaign_dashboard
from estate.core.steward_command_center import generate_command_center, render_command_center_html


REPO = Path(__file__).resolve().parents[1]


def install_stack(root, *, enabled=True):
    for name in ("WP-4218", "WP-4219", "WP-4222"):
        target = root / "collaboration/workstreams" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(REPO / "collaboration/workstreams" / name, target)
    config = root / "config/engineering_campaign_dashboard.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(json.dumps({"enabled": enabled, "provider_manifest": "collaboration/workstreams/WP-4222/fixtures/providers.json",
        "refresh_policy": "manual", "freshness_threshold_seconds": 86400, "last_known_valid": True,
        "diagnostic_verbosity": "safe", "access_roles": ["estate_operator", "steward"]}), encoding="utf-8")


def test_adapter_snapshot_panels_summary_health_and_provenance(tmp_path):
    install_stack(tmp_path)
    snapshot = dashboard_operation(tmp_path, "snapshot", role="estate_operator")
    assert snapshot["ok"] and snapshot["read_only"] and snapshot["advisory_only"]
    assert set(snapshot["provenance"]) == {"source_queue_generation_id", "source_revision", "dashboard_snapshot_id", "schema_version", "generation_time", "content_hash", "references"}
    assert dashboard_operation(tmp_path, "panel", role="steward", panel_id="dependency_graph")["panel"]["panel_id"] == "dependency_graph"
    assert dashboard_operation(tmp_path, "summary", role="steward")["operator_summary"]
    assert dashboard_operation(tmp_path, "health", role="steward")["provider_diagnostics"]


def test_authorization_and_unsupported_mutation_are_fail_closed(tmp_path):
    install_stack(tmp_path)
    assert dashboard_operation(tmp_path, "snapshot", role="anonymous")["state"] == "unauthorized"
    assert dashboard_operation(tmp_path, "assign", role="steward") == {"ok": False, "state": "unsupported", "read_only": True}


def test_refresh_audit_and_last_known_valid_fallback(tmp_path):
    install_stack(tmp_path)
    refreshed = dashboard_operation(tmp_path, "refresh", role="steward")
    assert refreshed["ok"] and (tmp_path / "runtime/steward/engineering_campaign_dashboard_last_valid.json").is_file()
    manifest = tmp_path / "collaboration/workstreams/WP-4222/fixtures/providers.json"
    manifest.unlink()
    fallback = load_engineering_campaign_dashboard(tmp_path, role="steward", refresh=True, write=True)
    assert fallback["last_known_valid"] and not fallback["current"] and fallback["state"] == "unavailable"
    audit = (tmp_path / "runtime/audit/engineering_campaign_dashboard.jsonl").read_text(encoding="utf-8")
    assert "refresh_succeeded" in audit and "refresh_failed" in audit


def test_invalid_and_incompatible_primary_provider_never_look_healthy(tmp_path):
    install_stack(tmp_path)
    manifest_path = tmp_path / "collaboration/workstreams/WP-4222/fixtures/providers.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["providers"][0]["contract_version"] = "estate.engineering-queue/v2"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = load_engineering_campaign_dashboard(tmp_path)
    assert not result["available"] and result["state"] == "unavailable"


def test_optional_provider_degradation_is_preserved_and_output_is_deterministic(tmp_path):
    install_stack(tmp_path)
    first = load_engineering_campaign_dashboard(tmp_path)
    second = load_engineering_campaign_dashboard(tmp_path)
    assert first["integration"]["health"] == "degraded"
    assert first["response_content_hash"] == second["response_content_hash"]
    assert any(row["required"] is False and row["status"] != "healthy" for row in first["integration"]["provider_diagnostics"])
    assert str(tmp_path) not in json.dumps(first)


def test_office_installation_and_disable_rollback(tmp_path):
    install_stack(tmp_path)
    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)
    assert payload["panels"]["engineering_campaign_dashboard"]["data"]["available"]
    assert "Engineering Campaign Dashboard" in html and "Manual refresh" in html
    for forbidden in ("Execute", "Assign", "Dispatch", "Reserve", "Merge action"):
        assert forbidden not in html.split("Engineering Campaign Dashboard", 1)[1].split("</section>", 1)[0]
    config = tmp_path / "config/engineering_campaign_dashboard.json"
    value = json.loads(config.read_text(encoding="utf-8")); value["enabled"] = False
    config.write_text(json.dumps(value), encoding="utf-8")
    disabled = load_engineering_campaign_dashboard(tmp_path)
    assert disabled["state"] == "unsupported"
