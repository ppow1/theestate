import json
from estate.core.engineering_provider_routing_runtime import recommend_engineering_provider
from estate.core.provider_health import ProviderHealthRecord, write_health_record


def request():
    return {"routing_request_id":"r1","work_summary":"edit repo","requires_repo_write":True}


def test_routing_excludes_unhealthy_cloud_provider(tmp_path):
    write_health_record(ProviderHealthRecord.create(provider_id="codex_cloud_web", status="offline", reported_by="test", message="down"), root=tmp_path, validate_catalog=False)
    result = recommend_engineering_provider(request(), root=tmp_path, write=False)
    assert result["recommended_provider"] == "human_review"
    assert "excluded by health evidence" in result["capacity_reason"]


def test_routing_includes_health_artifact_reference(tmp_path):
    result = recommend_engineering_provider(request(), root=tmp_path, write=False)
    assert result["engineering_provider_health"]["source_artifact"] == "runtime/provider_health/current.json"
