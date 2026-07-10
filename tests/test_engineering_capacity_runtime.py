import shutil
import subprocess
import sys
from pathlib import Path

from estate.core.engineering_capacity_runtime import generate_engineering_capacity_dashboard
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
