import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from estate.core import comfyui_provider_health
from estate.core.comfyui_execution_provider_adapter import ComfyUIExecutionProviderAdapter
from estate.core.comfyui_provider_health import PROVIDER_ID, has_fresh_comfyui_evidence, probe_comfyui_health, validate_loopback_endpoint
from estate.core.execution_provider_adapter import ExecutionProviderAdapterRequest
from estate.core.engineering_lifecycle_slice import EngineeringLifecycleSlice
from estate.core.execution_dispatch import load_dispatch_queue
from estate.core.helen_workforce import HelenWorkforceStore
from estate.core.provider_catalog import load_provider_catalog


def request(**overrides):
    data = {"adapter_request_id": "adapter-comfy-001", "dispatch_id": "dispatch-comfy-001", "provider_id": PROVIDER_ID,
            "provider_type": "media", "work_package_id": "WP-0675", "prompt_source": "collaboration/evidence/proof.json",
            "classification": "Estate Internal", "read_scope_paths": ["collaboration/evidence"], "write_scope_paths": [],
            "blocked_scope_paths": [], "expected_outputs": [], "validation_required": True, "decision_reference": "STEWARD AUTHORIZATION: ComfyUI admission",
            "created_at": "2026-07-26T12:00:00Z", "metadata": {"endpoint": "http://127.0.0.1:8188/system_stats", "required_capabilities": ["image_iteration"], "workflow": {"1": {"class_type": "TestNode", "inputs": {}}}}}
    data.update(overrides)
    return ExecutionProviderAdapterRequest.from_dict(data)


def root_with_catalog(tmp_path):
    target = tmp_path / "config/providers"
    target.mkdir(parents=True)
    shutil.copy(Path("config/providers/catalog.json"), target / "catalog.json")
    return tmp_path


def test_canonical_catalog_admits_loopback_no_spend_comfyui_provider():
    provider = load_provider_catalog().get_provider(PROVIDER_ID)
    assert provider.provider_type == "media"
    assert provider.cost_model == "no_spend_local"
    assert provider.requires_network is False
    assert provider.metadata["service_id"] == "comfyui"
    assert provider.metadata["loopback_only"] is True
    assert set(provider.capabilities) == {"image_generation", "image_iteration"}


def test_loopback_only_health_endpoint_rejects_external_hosts():
    assert validate_loopback_endpoint("http://127.0.0.1:8188/system_stats")
    with pytest.raises(ValueError, match="loopback-only"):
        validate_loopback_endpoint("http://example.com:8188/system_stats")
    with pytest.raises(ValueError, match="exactly /system_stats"):
        validate_loopback_endpoint("http://127.0.0.1:8188/prompt")


def test_health_fetch_uses_get_and_blocks_redirects(monkeypatch):
    captured = {}

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"{}"

    class Opener:
        def open(self, request, timeout):
            captured["method"] = request.get_method()
            captured["timeout"] = timeout
            return Response()

    def build_opener(handler):
        assert handler.redirect_request(None, None, 302, "found", {}, "http://example.com") is None
        return Opener()

    monkeypatch.setattr(comfyui_provider_health, "build_opener", build_opener)
    assert comfyui_provider_health._default_fetch("http://127.0.0.1:8188/system_stats", 2.0) == (200, b"{}")
    assert captured == {"method": "GET", "timeout": 2.0}


def test_probe_writes_current_health_and_unknown_capacity_without_execution(tmp_path):
    root = root_with_catalog(tmp_path)
    result = probe_comfyui_health(root=root, fetch=lambda endpoint, timeout: (200, b'{"system": {"os": "Windows"}}'))
    assert result["health_status"] == "available"
    assert result["endpoint_reachable"] is True
    assert result["live_provider_called"] is False
    assert result["workflow_submitted"] is False
    assert result["image_generated"] is False
    assert has_fresh_comfyui_evidence(root=root) is False  # capacity remains unknown; probe cannot select.


def test_probe_records_unreachable_and_malformed_evidence(tmp_path):
    root = root_with_catalog(tmp_path)
    unreachable = probe_comfyui_health(root=root, fetch=lambda endpoint, timeout: (_ for _ in ()).throw(TimeoutError()))
    assert unreachable["health_status"] == "offline"
    malformed = probe_comfyui_health(root=root, fetch=lambda endpoint, timeout: (200, b'[]'))
    assert malformed["health_status"] == "degraded"
    assert malformed["response_malformed"] is True


def test_stale_or_missing_evidence_cannot_select_provider(tmp_path):
    root = root_with_catalog(tmp_path)
    assert has_fresh_comfyui_evidence(root=root) is False
    probe_comfyui_health(root=root, fetch=lambda endpoint, timeout: (200, b'{}'), freshness_seconds=1)
    assert has_fresh_comfyui_evidence(root=root, now=datetime(2100, 1, 1, tzinfo=timezone.utc)) is False


def test_adapter_prepares_deterministic_request_without_network_or_acceptance():
    adapter = ComfyUIExecutionProviderAdapter()
    first = adapter.prepare_workflow_request(request())
    second = adapter.prepare_workflow_request(request())
    assert first == second
    assert first["live_provider_called"] is False
    assert first["workflow_submitted"] is False
    assert first["image_generated"] is False
    assert first["acceptance_granted"] is False
    result = adapter.dry_run(request())
    assert result.status == "dry_run_completed"
    assert result.metadata["live_provider_called"] is False


def test_adapter_rejects_external_target_and_live_submit():
    adapter = ComfyUIExecutionProviderAdapter()
    with pytest.raises(ValueError, match="loopback-only"):
        adapter.prepare_workflow_request(request(metadata={"endpoint": "http://example.com/system_stats", "required_capabilities": ["image_generation"], "workflow": {"1": {}}}))
    submitted = adapter.submit(request())
    assert submitted.status == "blocked"
    assert submitted.metadata["workflow_submitted"] is False
    assert submitted.metadata["acceptance_granted"] is False


def test_adapter_rejects_non_image_capability_and_preserves_dispatch_identity():
    adapter = ComfyUIExecutionProviderAdapter()
    with pytest.raises(ValueError, match="requires image_generation"):
        adapter.prepare_workflow_request(request(metadata={"required_capabilities": ["planning"], "workflow": {"1": {}}}))
    result = adapter.dry_run(request())
    assert result.dispatch_id == "dispatch-comfy-001"
    assert result.provider_id == PROVIDER_ID


def test_lifecycle_replay_and_comfyui_request_preparation_do_not_duplicate_dispatch_or_requests(tmp_path):
    registry = tmp_path / "data/registry"
    registry.mkdir(parents=True)
    (registry / "personnel.json").write_text(json.dumps([
        {"employee_id": 1, "mailbox_id": 1, "display_name": "Steward", "current_title": "Steward", "current_office": "Stewardship"},
        {"employee_id": 12, "mailbox_id": 12, "display_name": "Grace", "current_title": "Director of Operations", "current_office": "Office of Operations"},
    ]))
    (registry / "mailboxes.json").write_text("[]")
    lifecycle = EngineeringLifecycleSlice(tmp_path, "comfyui-admission-replay")
    lifecycle.intake(occurred_at="2026-07-26T12:00:00+00:00")
    HelenWorkforceStore(tmp_path).record_operational_disposition(
        lifecycle.request_id, disposition="fulfilled", decided_by="Helen",
        evidence_references=["fixture://helen/ready.json"], fulfilled_capabilities=["image_iteration"],
        reason="Fixture readiness.", authority_evidence=["STEWARD AUTHORIZATION: ComfyUI admission"],
    )
    lifecycle.advance()
    lifecycle.advance()
    assert len(load_dispatch_queue(tmp_path)) == 1
    adapter = ComfyUIExecutionProviderAdapter()
    assert adapter.prepare_workflow_request(request()) == adapter.prepare_workflow_request(request())
    assert len(load_dispatch_queue(tmp_path)) == 1
