import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from estate.core.comfyui_provider_capacity import (
    PROVIDER_ID, evaluate_comfyui_selection_eligibility, has_fresh_qualifying_capacity,
    probe_comfyui_capacity, validate_capacity_endpoint,
)
from estate.core.provider_health import ProviderHealthRecord, write_health_record


def root_with_catalog(tmp_path):
    target = tmp_path / "config/providers"
    target.mkdir(parents=True)
    shutil.copy(Path("config/providers/catalog.json"), target / "catalog.json")
    return tmp_path


def fresh_health(root):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    record = ProviderHealthRecord.create(provider_id=PROVIDER_ID, status="available", reported_by="test", message="healthy",
        expires_at=(now + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"), capabilities_available=["image_generation", "image_iteration"])
    write_health_record(record, root=root)


def queue(running=(), pending=()):
    return (
        ("GET", "http://127.0.0.1:8188/queue", 2.0),
        (
            200,
            json.dumps({"queue_running": list(running), "queue_pending": list(pending)}).encode("utf-8"),
            "http://127.0.0.1:8188/queue",
        ),
    )


def fetch_for(response):
    expected, result = response
    def fetch(method, endpoint, timeout):
        assert (method, endpoint, timeout) == expected
        return result
    return fetch


def test_capacity_endpoint_is_exact_loopback_get_only_surface():
    assert validate_capacity_endpoint("http://127.0.0.1:8188/queue")
    for endpoint in ("http://example.com/queue", "https://127.0.0.1:8188/queue", "http://127.0.0.1:8188/prompt", "http://127.0.0.1:8188/queue?x=1", "http://127.0.0.1:8188/queue#fragment"):
        with pytest.raises(ValueError):
            validate_capacity_endpoint(endpoint)
    with pytest.raises(ValueError, match="at most ten"):
        probe_comfyui_capacity(root=Path("."), timeout_seconds=10.1, fetch=lambda m, e, t: (200, b"", e))


def test_idle_available_evidence_requires_fresh_health(tmp_path):
    root = root_with_catalog(tmp_path)
    unknown = probe_comfyui_capacity(root=root, fetch=fetch_for(queue()))
    assert unknown["capacity_state"] == "unknown"
    assert unknown["endpoint_reachable"] is True
    fresh_health(root)
    available = probe_comfyui_capacity(root=root, fetch=fetch_for(queue()))
    assert available["capacity_state"] == "available"
    assert available["active_jobs"] == available["queue_depth"] == 0
    assert has_fresh_qualifying_capacity(root=root)


def test_busy_unavailable_malformed_timeout_and_redirect_fail_closed(tmp_path):
    root = root_with_catalog(tmp_path); fresh_health(root)
    assert probe_comfyui_capacity(root=root, fetch=fetch_for(queue(running=["redacted"]))) ["capacity_state"] == "busy"
    unavailable = probe_comfyui_capacity(root=root, fetch=lambda m, e, t: (503, b"", e))
    assert unavailable["capacity_state"] == "unknown" and unavailable["availability"] == "unavailable"
    assert unavailable["endpoint_reachable"] is True
    malformed = probe_comfyui_capacity(root=root, fetch=lambda m, e, t: (200, b"{}", e))
    assert malformed["capacity_state"] == "unknown" and malformed["response_malformed"] is True
    timeout = probe_comfyui_capacity(root=root, fetch=lambda m, e, t: (_ for _ in ()).throw(TimeoutError()))
    assert timeout["capacity_state"] == "unknown"
    assert timeout["endpoint_reachable"] is False
    redirected = probe_comfyui_capacity(root=root, fetch=lambda m, e, t: (200, b'{"queue_running": [], "queue_pending": []}', "http://example.com/queue"))
    assert redirected["capacity_state"] == "unknown"


def test_stale_busy_and_unknown_capacity_are_non_selectable_and_governance_remains_required(tmp_path):
    root = root_with_catalog(tmp_path); fresh_health(root)
    busy = probe_comfyui_capacity(root=root, fetch=fetch_for(queue(pending=["redacted"])))
    assert busy["capacity_state"] == "busy"
    blocked = evaluate_comfyui_selection_eligibility(root=root, required_capability="image_iteration")
    assert blocked["eligible"] is False and blocked["provider_selected"] is False
    available = probe_comfyui_capacity(root=root, fetch=fetch_for(queue()))
    stale = evaluate_comfyui_selection_eligibility(root=root, required_capability="image_iteration", now=datetime(2100, 1, 1, tzinfo=timezone.utc))
    assert available["capacity_state"] == "available" and stale["eligible"] is False
    gates = evaluate_comfyui_selection_eligibility(root=root, required_capability="image_iteration", privacy_cleared=True, egress_cleared=True, authority_granted=True, dispatch_authorized=True)
    assert gates["eligible"] is True
    assert gates["dispatch_created"] is False and gates["live_provider_called"] is False and gates["acceptance_granted"] is False


def test_available_capacity_cannot_override_unavailable_health(tmp_path):
    root = root_with_catalog(tmp_path)
    fresh_health(root)
    available = probe_comfyui_capacity(root=root, fetch=fetch_for(queue()))
    now = datetime.now(timezone.utc).replace(microsecond=0)
    unavailable_health = ProviderHealthRecord.create(
        provider_id=PROVIDER_ID, status="offline", reported_by="test", message="unreachable",
        expires_at=(now + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        capabilities_available=[])
    unavailable_health.checked_at = (now + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
    write_health_record(unavailable_health, root=root)
    eligibility = evaluate_comfyui_selection_eligibility(
        root=root, required_capability="image_generation", privacy_cleared=True,
        egress_cleared=True, authority_granted=True, dispatch_authorized=True,
    )
    assert available["capacity_state"] == "available"
    assert eligibility["eligible"] is False
    assert "fresh available health evidence is required" in eligibility["reasons"]


def test_repeated_probes_are_canonical_and_never_submit_or_generate(tmp_path):
    root = root_with_catalog(tmp_path); fresh_health(root)
    first = probe_comfyui_capacity(root=root, fetch=fetch_for(queue()))
    second = probe_comfyui_capacity(root=root, fetch=fetch_for(queue()))
    assert first["capacity_state"] == second["capacity_state"] == "available"
    assert first["workflow_submitted"] is second["workflow_submitted"] is False
    assert first["image_generated"] is second["image_generated"] is False
