import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.service_dependency_matrix import generate_service_dependency_matrix, format_service_dependency_matrix


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed(root):
    write(root / "src/estate/cli/main.py", "cli")
    write_json(root / "data/registry/capabilities.json", [])


def test_dependency_mapping_and_startup_order(tmp_path):
    seed(tmp_path)
    write_json(tmp_path / "data/registry/services.json", [
        {"id": "SVC-A", "name": "Foundation", "status": "Active", "owner": "Ops", "dependencies": []},
        {"id": "SVC-B", "name": "Consumer", "status": "Active", "owner": "Ops", "dependencies": ["SVC-A"]},
    ])
    write_json(tmp_path / "data/registry/providers.json", [{"id": "PRV-A", "name": "Foundation Provider", "service": "Foundation", "status": "Operational"}])

    payload = generate_service_dependency_matrix(tmp_path, write=False)

    assert payload["summary"]["explicit_dependency_count"] == 1
    assert [step["service_id"] for step in payload["startup_order"]].index("SVC-A") < [step["service_id"] for step in payload["startup_order"]].index("SVC-B")
    foundation = next(row for row in payload["matrix"] if row["service_id"] == "SVC-A")
    consumer = next(row for row in payload["matrix"] if row["service_id"] == "SVC-B")
    assert foundation["required_providers"][0]["id"] == "PRV-A"
    assert consumer["startup_after"] == ["SVC-A"]
    assert "SVC-B" in foundation["failure_impact"]
    assert "data/registry/services.json" in consumer["source_artifacts"]


def test_incomplete_metadata_and_unresolved_dependencies_warn(tmp_path):
    seed(tmp_path)
    write_json(tmp_path / "data/registry/services.json", [{"id": "SVC-MISSING", "name": "Missing", "status": "Draft", "owner": "Ops", "dependencies": ["SVC-NOPE"]}])
    write_json(tmp_path / "data/registry/providers.json", [{"id": "PRV-X", "name": "External", "service": "Unmatched Service", "status": "Observed"}])

    payload = generate_service_dependency_matrix(tmp_path, write=False)

    assert any(w["type"] == "unresolved_service_dependency" for w in payload["warnings"])
    assert any(w["type"] == "unmatched_provider_service" for w in payload["warnings"])
    row = next(row for row in payload["matrix"] if row["service_id"] == "SVC-MISSING")
    assert row["required_services"] == ["SVC-NOPE"]
    assert row["startup_after"] == []


def test_writes_outputs_and_markdown_notes_read_only(tmp_path):
    seed(tmp_path)
    write_json(tmp_path / "data/registry/services.json", [])
    write_json(tmp_path / "data/registry/providers.json", [])

    payload = generate_service_dependency_matrix(tmp_path, write=True)
    markdown = format_service_dependency_matrix(payload)

    assert (tmp_path / "runtime/services/service_dependency_matrix.json").exists()
    assert (tmp_path / "operations/services/service_dependency_matrix.md").exists()
    assert "does not create a duplicate dependency registry" in markdown
    assert "## Startup order" in markdown


def test_service_dependency_matrix_cli(tmp_path):
    seed(tmp_path)
    write_json(tmp_path / "data/registry/services.json", [])
    write_json(tmp_path / "data/registry/providers.json", [])

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "service-dependency-matrix", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["service_count"] >= 0
    assert (tmp_path / "runtime/services/service_dependency_matrix.json").exists()
