import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.estate_capability_registry import generate_estate_capability_registry, format_estate_capability_registry


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_capability_discovery_with_provider_dependency_and_sources(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{
        "id": "CAP-1",
        "name": "Operations Board",
        "owner": "Operations Center",
        "status": "Operational",
        "lifecycle_state": "Operationally Validated",
        "dependencies": ["SVC-1"],
        "related_services": ["SVC-1"],
        "implementation_references": ["src/estate/core/operations_board.py"],
        "evidence_references": ["docs/operations/Operations_Board_Runtime_Integration.md"],
    }])
    write_json(tmp_path, "data/registry/providers.json", [{"id": "PRV-1", "name": "Local Provider", "capability": "CAP-1", "service": "Operations", "status": "Operational"}])
    write_json(tmp_path, "data/registry/services.json", [{"id": "SVC-1", "name": "Operations", "status": "Active"}])
    write_json(tmp_path, "runtime/capabilities/capability_lifecycle_report.json", {"capabilities": [{"id": "CAP-1", "valid_lifecycle_state": True, "warnings": []}]})

    registry = generate_estate_capability_registry(tmp_path, write=False)

    cap = registry["capabilities"][0]
    assert registry["summary"]["capability_count"] == 1
    assert cap["providers"][0]["id"] == "PRV-1"
    assert cap["dependencies"] == ["SVC-1"]
    assert cap["validation_status"] == "valid"
    assert "src/estate/core/operations_board.py" in cap["source_artifact_links"]


def test_missing_metadata_is_graceful(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-1"}])

    registry = generate_estate_capability_registry(tmp_path, write=False)

    cap = registry["capabilities"][0]
    assert cap["name"] == "CAP-1"
    assert cap["owning_subsystem"] == "Unknown"
    assert cap["implementation_status"] == "unknown"
    assert cap["validation_status"] == "unknown"
    assert any(w["type"] == "missing_name" for w in registry["warnings"])


def test_dependency_display_and_authoritative_links_in_markdown(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-1", "name": "Capability", "owner": "Subsystem", "status": "Installed", "lifecycle_state": "Implemented", "dependencies": ["CAP-0"], "implementation_references": ["src/x.py"]}])

    markdown = format_estate_capability_registry(generate_estate_capability_registry(tmp_path, write=False))

    assert "- Dependencies: CAP-0" in markdown
    assert "data/registry/capabilities.json" in markdown
    assert "src/x.py" in markdown
    assert "not the source of truth" in markdown


def test_estate_capability_registry_cli(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-1", "name": "Capability", "owner": "Subsystem", "status": "Operational", "lifecycle_state": "Implemented"}])

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "estate-capability-registry", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["capability_count"] == 1
    assert (tmp_path / "runtime" / "capabilities" / "estate_capability_registry.json").exists()
    assert (tmp_path / "operations" / "capabilities" / "estate_capability_registry.md").exists()
