import json
from pathlib import Path

from estate.core.resident_capability_access import resolve_resident_capabilities
from estate.core.resident_lifecycle import status


def test_grace_runtime_identity_and_surface_are_live_after_steward_activation():
    identity = json.loads(Path("runtime/residents/grace/runtime_identity.json").read_text())
    surface = json.loads(Path("operations/residents/surfaces/grace.json").read_text())

    assert identity["resident_id"] == "grace"
    assert identity["status"] == "active"
    assert identity["gateway_model"] == "estate/grace"
    assert identity["open_webui"]["exposed"] is True
    assert surface["resident_id"] == "grace"
    assert surface["presentation"]["gateway_model"] == "estate/grace"
    assert surface["activation_boundary"]["steward_activation_required"] is False


def test_grace_lifecycle_registry_and_capabilities_are_active():
    lifecycle = status("grace")
    residents = json.loads(Path("data/registry/residents.json").read_text())
    capabilities = resolve_resident_capabilities("Grace")

    assert lifecycle["status"] == "active"
    assert any(item.get("name") == "Grace" and item.get("status") == "Active" for item in residents)
    assert capabilities["state"] == "active"
    assert "operational_service" in capabilities["declared_capabilities"]
