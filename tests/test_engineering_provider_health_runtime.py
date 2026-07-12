import json
from pathlib import Path

from estate.core.engineering_provider_health_runtime import collect_provider_health, evaluate_provider
from estate.core.provider_capacity import ProviderCapacityRecord, write_capacity_record
from estate.core.provider_health import ProviderHealthRecord, write_health_record


def test_health_classifications_and_history(tmp_path):
    (tmp_path / "runtime/provider_registry/codex").mkdir(parents=True)
    (tmp_path / "runtime/provider_registry/codex/capabilities.json").write_text(json.dumps({"observed_at":"2026-07-12T01:00:00Z"}), encoding="utf-8")
    write_capacity_record(ProviderCapacityRecord.create(provider_id="codex_cli_openai", capacity_state="available", reported_by="test", max_jobs=2), root=tmp_path, validate_catalog=False)
    write_health_record(ProviderHealthRecord.create(provider_id="codex_cli_openai", status="available", reported_by="test", message="ok", metadata={"authentication_state":"valid","recent_success_count":4,"last_success_at":"2026-07-12T01:00:00Z"}), root=tmp_path, validate_catalog=False)
    rec = evaluate_provider("codex_cli_openai", root=tmp_path, stale_after_seconds=999999)
    assert rec["health_state"] in {"healthy", "degraded"}  # executable availability may vary by test host
    assert rec["recommended_for_dispatch"] == (rec["health_state"] == "healthy")

    write_health_record(ProviderHealthRecord.create(provider_id="local_ollama_gpu", status="offline", reported_by="test", message="down", metadata={"authentication_state":"valid"}), root=tmp_path, validate_catalog=False)
    assert evaluate_provider("local_ollama_gpu", root=tmp_path)["health_state"] == "offline"

    write_health_record(ProviderHealthRecord.create(provider_id="local_gpu_runtime", status="available", reported_by="test", message="bad auth", metadata={"authentication_state":"invalid"}), root=tmp_path, validate_catalog=False)
    assert evaluate_provider("local_gpu_runtime", root=tmp_path)["health_state"] == "offline"

    payload1 = collect_provider_health(root=tmp_path)
    payload2 = collect_provider_health(root=tmp_path)
    assert [p["provider_id"] for p in payload1["providers"]] == [p["provider_id"] for p in payload2["providers"]]
    assert len((tmp_path / "runtime/provider_health/history.jsonl").read_text().splitlines()) == 2


def test_degraded_thresholds_and_malformed_evidence(tmp_path):
    (tmp_path / "runtime/provider_registry/codex").mkdir(parents=True)
    (tmp_path / "runtime/provider_registry/codex/capabilities.json").write_text("not-json", encoding="utf-8")
    write_capacity_record(ProviderCapacityRecord.create(provider_id="codex_cloud_web", capacity_state="saturated", reported_by="test", active_jobs=5, max_jobs=5, queue_depth=12), root=tmp_path, validate_catalog=False)
    write_health_record(ProviderHealthRecord.create(provider_id="codex_cloud_web", status="available", reported_by="test", message="slow", metadata={"authentication_state":"valid","recent_success_count":1,"recent_failure_count":3,"consecutive_failures":3,"latency_ms":45000}), root=tmp_path, validate_catalog=False)
    rec = evaluate_provider("codex_cloud_web", root=tmp_path, stale_after_seconds=0)
    assert rec["health_state"] == "degraded"
    assert rec["recommended_for_dispatch"] is False
    assert any("failure" in r for r in rec["health_reasons"])
