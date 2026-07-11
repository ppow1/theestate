import shutil
from pathlib import Path

from estate.core.engineering_provider_routing_runtime import recommend_engineering_provider
from estate.core.provider_capacity import ProviderCapacityRecord, write_capacity_record
from estate.core.provider_health import ProviderHealthRecord, write_health_record


def copy_catalog(root):
    target = root / "config" / "providers"
    target.mkdir(parents=True)
    shutil.copy(Path("config/providers/catalog.json"), target / "catalog.json")


def test_engineering_provider_routing_prefers_cloud_for_repo_write_when_available(tmp_path):
    copy_catalog(tmp_path)
    write_health_record(ProviderHealthRecord.create(provider_id="codex.execution.cli", status="available", reported_by="test", message="ready"), root=tmp_path)
    write_capacity_record(ProviderCapacityRecord.create(provider_id="codex.execution.cli", capacity_state="available", reported_by="test", active_jobs=0, max_jobs=2), root=tmp_path)
    payload = recommend_engineering_provider({"routing_request_id": "route-eng", "work_type": "repository implementation", "requires_repo_write": True}, root=tmp_path, write=True)
    assert payload["recommended_provider"] == "codex_cloud_web"
    assert payload["constraints"]["traffic_controller_decides_movement"] is True
    assert (tmp_path / "runtime/engineering_provider_routing/latest.json").exists()


def test_engineering_provider_routing_uses_local_when_cloud_constrained(tmp_path):
    copy_catalog(tmp_path)
    write_health_record(ProviderHealthRecord.create(provider_id="codex.execution.cli", status="out_of_quota", reported_by="test", message="limited"), root=tmp_path)
    write_capacity_record(ProviderCapacityRecord.create(provider_id="codex.execution.cli", capacity_state="quota_limited", reported_by="test"), root=tmp_path)
    (tmp_path / "runtime/workers/heartbeats").mkdir(parents=True)
    (tmp_path / "runtime/workers/heartbeats/ca7.json").write_text('{"worker_id":"ca7","status":"idle","last_heartbeat":"2026-07-10T00:00:00Z"}\n')
    payload = recommend_engineering_provider({"routing_request_id": "route-eng-local", "work_type": "repository implementation", "requires_repo_write": True}, root=tmp_path, stale_after_minutes=999999, write=True)
    assert payload["recommended_provider"] == "local_ollama_gpu"
    assert payload["engineering_capacity_summary"]["constrained_cloud_codex_seat_count"] >= 1
