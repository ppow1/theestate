import json
from pathlib import Path

from estate.core.resident_capability_access import resolve_resident_capabilities
from estate.core.resident_lifecycle import status


def test_grace_runtime_identity_and_surface_are_not_live_until_steward_activation():
    identity = json.loads(Path("runtime/residents/grace/runtime_identity.json").read_text())
    surface = json.loads(Path("operations/residents/surfaces/grace.json").read_text())

    assert identity["resident_id"] == "grace"
    assert identity["status"] == "appointed_onboarding"
    assert identity["gateway_model"] is None
    assert identity["open_webui"]["exposed"] is False
    assert surface["resident_id"] == "grace"
    assert surface["presentation"]["gateway_model"] is None
    assert surface["activation_boundary"]["steward_activation_required"] is True


def test_grace_lifecycle_registry_and_capabilities_require_activation():
    lifecycle = status("grace")
    residents = json.loads(Path("data/registry/residents.json").read_text())
    capabilities = resolve_resident_capabilities("Grace")

    assert lifecycle["status"] == "onboarding"
    assert not any(item.get("name") == "Grace" and item.get("status") == "Active" for item in residents)
    assert capabilities["state"] == "candidate"
    assert "appointed_onboarding" in capabilities["declared_capabilities"]
