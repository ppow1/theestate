import shutil
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from estate.core.engineering_capacity_runtime import _fuel_gauge, generate_engineering_capacity_dashboard
from estate.core.provider_capacity import ProviderCapacityRecord, write_capacity_record
from estate.core.provider_health import ProviderHealthRecord, write_health_record


def copy_catalog(root):
    target = root / "config" / "providers"
    target.mkdir(parents=True)
    shutil.copy(Path("config/providers/catalog.json"), target / "catalog.json")


def test_engineering_capacity_dashboard_combines_codex_and_workers(tmp_path):
    copy_catalog(tmp_path)
    write_health_record(ProviderHealthRecord.create(provider_id="codex.execution.cli", status="available", reported_by="test", message="ready"), root=tmp_path)
    write_capacity_record(ProviderCapacityRecord.create(provider_id="codex.execution.cli", capacity_state="available", reported_by="test", active_jobs=0, max_jobs=2), root=tmp_path)
    (tmp_path / "runtime/workers/heartbeats").mkdir(parents=True)
    (tmp_path / "runtime/workers/heartbeats/ca7.json").write_text('{"worker_id":"ca7","status":"idle","last_heartbeat":"2026-07-10T00:00:00Z"}\n')
    payload = generate_engineering_capacity_dashboard(root=tmp_path, write=True, stale_after_minutes=999999)
    assert payload["summary"]["cloud_codex_seat_count"] >= 1
    assert payload["summary"]["idle_worker_count"] == 1
    assert (tmp_path / "operations/engineering_capacity/runtime_dashboard.md").exists()


def test_engineering_capacity_dashboard_cli(tmp_path):
    copy_catalog(tmp_path)
    result = subprocess.run([sys.executable, "-m", "estate.cli.main", "engineering-capacity-dashboard", "--json"], cwd=tmp_path, text=True, capture_output=True, env={"PYTHONPATH": str(Path.cwd() / "src")})
    assert result.returncode == 0, result.stdout + result.stderr
    assert "cloud_codex_seat_count" in result.stdout


def test_wp0532_state_mapping_preserves_unknown_and_quota_override():
    for state, expected in {"idle": 100, "available": 85, "busy": 55, "saturated": 20, "quota_limited": 0, "unknown": None}.items():
        assert _fuel_gauge({"capacity_state": state, "health_status": "available"})["percent"] == expected
    assert _fuel_gauge({"capacity_state": "busy", "health_status": "available", "quota_remaining": 1, "max_jobs": 4})["percent"] == 25


def test_wp0532_provider_projection_is_separate_and_freshness_is_explicit(tmp_path):
    copy_catalog(tmp_path)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    old = (now - timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    health = replace(ProviderHealthRecord.create(provider_id="codex.execution.cli", status="available", reported_by="test", message="ready"), checked_at=old)
    capacity = replace(ProviderCapacityRecord.create(provider_id="codex.execution.cli", capacity_state="busy", reported_by="test", max_jobs=4, quota_remaining=1), checked_at=old)
    write_health_record(health, root=tmp_path)
    write_capacity_record(capacity, root=tmp_path)
    payload = generate_engineering_capacity_dashboard(root=tmp_path, write=False, stale_after_minutes=30)
    provider = next(item for item in payload["providers"] if item["provider_id"] == "codex.execution.cli")
    assert provider["engineering_provider_capacity"]["index"] == 25
    assert provider["engineering_provider_capacity"]["freshness"]["state"] == "stale"
    assert "gpus.json" not in payload["source_artifacts"]
    assert "RTX 4090" not in str(provider)
    missing = next(item for item in payload["providers"] if item["capacity_state"] == "unknown")
    assert missing["engineering_provider_capacity"]["index"] is None
    assert missing["engineering_provider_capacity"]["freshness"]["state"] == "unknown"


def test_wp0532_projects_seats_separately_and_missing_native_evidence_is_unknown(tmp_path):
    copy_catalog(tmp_path)
    write_capacity_record(ProviderCapacityRecord.create(
        provider_id="codex.execution.cli", capacity_state="unknown", reported_by="discovery",
        message="no supported noninteractive usage mechanism",
        metadata={"seat_id": "C2", "source": "codex-cli-capability-discovery", "collection_success": False},
    ), root=tmp_path, validate_catalog=False)
    payload = generate_engineering_capacity_dashboard(root=tmp_path, write=False, stale_after_minutes=30)
    seats = {item["logical_seat_id"]: item for item in payload["codex_seat_observations"]}
    assert set(seats) == {"C1", "C2", "C3"}
    assert seats["C2"]["collection_success"] is False
    assert seats["C2"]["capacity_state"] == "unknown"
    assert seats["C2"]["freshness"]["state"] == "current"
    assert seats["C1"]["native_capacity_fields"] == {}
    assert seats["C1"]["reason"]
