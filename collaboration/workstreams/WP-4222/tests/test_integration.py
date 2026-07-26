from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from dashboard_integration import IntegrationError, ProviderRegistry, compose_dashboard, load_manifest

MANIFEST = ROOT / "fixtures/providers.json"
BASE = json.loads(MANIFEST.read_text(encoding="utf-8"))


def write_manifest(tmp_path: Path, value: dict = BASE) -> Path:
    value = copy.deepcopy(value)
    for provider in value["providers"]:
        original = (MANIFEST.parent / provider["path"]).resolve()
        provider["path"] = str(original)
    path = tmp_path / "providers.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_provider_discovery_is_sorted_and_has_required_staged_providers():
    providers = load_manifest(MANIFEST).discover()
    assert [p.provider_id for p in providers] == sorted(p.provider_id for p in providers)
    assert {p.provider_id for p in providers if p.required} == {"wp4220_queue", "wp4221_projection"}


def test_version_compatibility_rejects_required_major_mismatch(tmp_path):
    value = copy.deepcopy(BASE)
    value["providers"][0]["contract_version"] = "estate.engineering-queue/v2"
    with pytest.raises(IntegrationError, match="required provider failure"):
        compose_dashboard(load_manifest(write_manifest(tmp_path, value)))


def test_schema_compatibility_rejects_declared_artifact_mismatch(tmp_path):
    queue = json.loads((ROOT.parent / "WP-4218/examples/engineering_queue_v1.json").read_text())
    queue["queue_schema_version"] = "estate.engineering-queue/v9"
    bad = tmp_path / "bad-queue.json"
    bad.write_text(json.dumps(queue))
    value = copy.deepcopy(BASE)
    value["providers"][0]["path"] = str(bad)
    with pytest.raises(IntegrationError, match="required provider failure"):
        compose_dashboard(load_manifest(write_manifest(tmp_path, value)))


def test_projection_loading_and_panel_registration():
    result = compose_dashboard(load_manifest(MANIFEST))
    snapshot = result["dashboard_snapshot"]
    assert [p["panel_id"] for p in result["panel_registry"]] == snapshot["panel_index"]
    assert len(result["panel_registry"]) == 15
    assert snapshot["snapshot_schema_version"] == "estate.engineering-campaign-dashboard/v1"


def test_degraded_optional_and_missing_provider_are_visible():
    result = compose_dashboard(load_manifest(MANIFEST))
    by_id = {item["provider_id"]: item for item in result["provider_diagnostics"]}
    assert result["health"] == "degraded"
    assert by_id["wp4214_duration"]["status"] == "missing"
    assert "wp4214_duration:artifact_not_found" in result["degradation_reasons"]


def test_unregistered_required_provider_fails_closed(tmp_path):
    value = copy.deepcopy(BASE)
    value["providers"] = [p for p in value["providers"] if p["provider_id"] != "wp4220_queue"]
    with pytest.raises(IntegrationError, match="wp4220_queue:provider_not_registered"):
        compose_dashboard(load_manifest(write_manifest(tmp_path, value)))


def test_duplicate_registration_is_rejected(tmp_path):
    value = copy.deepcopy(BASE)
    value["providers"].append(copy.deepcopy(value["providers"][0]))
    with pytest.raises(IntegrationError, match="duplicate provider"):
        load_manifest(write_manifest(tmp_path, value))


def test_deterministic_repeated_execution():
    first = compose_dashboard(load_manifest(MANIFEST))
    second = compose_dashboard(load_manifest(MANIFEST))
    assert first == second
    assert first["deterministic_content_hash"] == second["deterministic_content_hash"]


def test_read_only_enforcement_preserves_every_existing_provider():
    registry = load_manifest(MANIFEST)
    before = {p.path: hashlib.sha256(p.path.read_bytes()).hexdigest() for p in registry.discover() if p.path.exists()}
    result = compose_dashboard(registry)
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before}
    assert before == after and result["read_only"] is True and result["staging_only"] is True


def test_cli_writes_only_requested_staging_output_and_repeats(tmp_path):
    manifest = write_manifest(tmp_path)
    source_before = manifest.read_bytes()
    one, two = tmp_path / "one.json", tmp_path / "two.json"
    command = [sys.executable, str(ROOT / "integrate.py"), str(manifest)]
    a = subprocess.run(command + ["--output", str(one)], capture_output=True, text=True)
    b = subprocess.run(command + ["--output", str(two)], capture_output=True, text=True)
    assert a.returncode == b.returncode == 0
    assert one.read_bytes() == two.read_bytes()
    assert manifest.read_bytes() == source_before


def test_manifest_shape_and_projection_kind_validation(tmp_path):
    with pytest.raises(IntegrationError, match="manifest schema"):
        ProviderRegistry(tmp_path / "x", {})
    value = copy.deepcopy(BASE)
    next(p for p in value["providers"] if p["provider_id"] == "wp4221_projection")["kind"] = "json"
    with pytest.raises(IntegrationError, match="required provider failure"):
        compose_dashboard(load_manifest(write_manifest(tmp_path, value)))
