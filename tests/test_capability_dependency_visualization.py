import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.capability_dependency_visualization import generate_capability_dependency_visualization, format_capability_dependency_visualization
from estate.core.steward_command_center import generate_command_center, render_command_center_html


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_complete_dependency_metadata_links_nodes_and_edges(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [
        {"id": "CAP-A", "name": "Capability A", "owner": "Ops", "status": "Operational", "lifecycle_state": "Operationally Validated", "dependencies": ["CAP-B"], "implementation_references": ["src/a.py"]},
        {"id": "CAP-B", "name": "Capability B", "owner": "Ops", "status": "Operational", "lifecycle_state": "Implemented", "dependencies": []},
    ])
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("# implementation", encoding="utf-8")

    payload = generate_capability_dependency_visualization(tmp_path, write=False)

    cap_a = next(node for node in payload["nodes"] if node["id"] == "CAP-A")
    cap_b = next(node for node in payload["nodes"] if node["id"] == "CAP-B")
    assert cap_a["upstream_dependencies"] == ["CAP-B"]
    assert cap_b["downstream_dependents"] == ["CAP-A"]
    assert cap_a["authoritative_artifact"] == "data/registry/capabilities.json"
    assert "src/a.py" in cap_a["source_artifact_links"]
    assert payload["summary"]["edge_count"] == 1


def test_partial_dependency_metadata_does_not_invent_missing_edges(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [
        {"id": "CAP-A", "name": "Capability A", "owner": "Ops", "status": "Operational", "lifecycle_state": "Implemented", "dependencies": ["CAP-MISSING"]},
        {"id": "CAP-B", "name": "Capability B", "owner": "Ops", "status": "Planned", "lifecycle_state": "Designed", "dependencies": []},
    ])

    payload = generate_capability_dependency_visualization(tmp_path, write=False)

    assert any(node["id"] == "CAP-MISSING" and node["type"] == "external_reference" for node in payload["nodes"])
    cap_b = next(node for node in payload["nodes"] if node["id"] == "CAP-B")
    assert cap_b["upstream_dependencies"] == []
    assert any(w["type"] == "no_explicit_relationships" for w in cap_b["warnings"])


def test_missing_dependency_metadata_warns_and_renders(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [
        {"id": "CAP-A", "name": "Capability A", "owner": "Ops", "status": "Unknown", "lifecycle_state": "Designed"}
    ])

    payload = generate_capability_dependency_visualization(tmp_path, write=False)
    markdown = format_capability_dependency_visualization(payload)

    assert payload["summary"]["edge_count"] == 0
    assert any(w["type"] == "missing_capability_dependency_metadata" for w in payload["warnings"])
    assert "No explicit capability dependency edges were found" in markdown
    assert "data/registry/capabilities.json" in markdown


def test_cli_writes_visualization_outputs(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-A", "name": "Capability A", "owner": "Ops", "status": "Operational", "lifecycle_state": "Implemented", "dependencies": []}])

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "capability-dependency-visualization", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["capability_node_count"] == 1
    assert (tmp_path / "runtime" / "capabilities" / "capability_dependency_visualization.json").exists()
    assert (tmp_path / "operations" / "capabilities" / "capability_dependency_visualization.md").exists()


def test_command_center_mission_control_embeds_dependency_visualization(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-A", "name": "Capability A", "owner": "Ops", "status": "Operational", "lifecycle_state": "Implemented", "dependencies": []}])

    payload = generate_command_center(tmp_path, write=False)
    html = render_command_center_html(payload)

    assert "Capability Dependencies" in html
    assert "Capability A" in html
    assert "data/registry/capabilities.json" in html
