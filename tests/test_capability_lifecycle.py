import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.capability_lifecycle import generate_capability_lifecycle_report, format_capability_lifecycle_markdown


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_valid_capability_registry_entries(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [
        {
            "id": "CAP-1",
            "name": "Operations Board",
            "lifecycle_state": "Implemented",
            "owner": "Alfred",
            "implementation_references": ["src/estate/core/operations_board.py"],
            "evidence_references": ["docs/operations/Operations_Board_Runtime_Integration.md"],
        }
    ])

    report = generate_capability_lifecycle_report(tmp_path, write=False)

    assert report["summary"]["capability_count"] == 1
    assert report["capabilities"][0]["valid_lifecycle_state"] is True
    assert report["candidates"]["operational_validation_candidates"] == ["CAP-1"]


def test_missing_lifecycle_state(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-1", "name": "Capability"}])

    report = generate_capability_lifecycle_report(tmp_path, write=False)

    assert report["candidates"]["missing_lifecycle_state"] == ["CAP-1"]


def test_invalid_lifecycle_state(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-1", "name": "Capability", "lifecycle_state": "Operational"}])

    report = generate_capability_lifecycle_report(tmp_path, write=False)

    assert report["summary"]["invalid_lifecycle_state_count"] == 1
    assert report["candidates"]["invalid_lifecycle_state"] == ["CAP-1"]


def test_implemented_capability_without_evidence(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-1", "name": "Capability", "lifecycle_state": "Implemented", "implementation_references": ["src/x.py"]}])

    report = generate_capability_lifecycle_report(tmp_path, write=False)

    assert report["candidates"]["implemented_but_missing_evidence"] == ["CAP-1"]


def test_operationally_validated_without_operational_evidence(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-1", "name": "Capability", "lifecycle_state": "Operationally Validated", "implementation_references": ["src/x.py"], "evidence_references": ["docs/x.md"]}])

    report = generate_capability_lifecycle_report(tmp_path, write=False)

    assert any(w["type"] == "missing_operational_evidence" for w in report["capabilities"][0]["warnings"])


def test_malformed_registry_json(tmp_path):
    path = tmp_path / "data" / "registry" / "capabilities.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")

    report = generate_capability_lifecycle_report(tmp_path, write=False)

    assert report["summary"]["capability_count"] == 0
    assert any(w["type"] == "malformed_json" for w in report["warnings"])


def test_markdown_generation(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-1", "name": "Capability", "lifecycle_state": "Designed"}])
    report = generate_capability_lifecycle_report(tmp_path, write=False)

    markdown = format_capability_lifecycle_markdown(report)

    assert markdown.startswith("# Estate Capability Lifecycle Status")
    assert "## Summary" in markdown
    assert "## Warnings" in markdown


def test_capability_lifecycle_cli_registration(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-1", "name": "Capability", "lifecycle_state": "Designed"}])

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "capability-lifecycle", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["capability_count"] == 1
    assert (tmp_path / "runtime" / "capabilities" / "capability_lifecycle_report.json").exists()
    assert (tmp_path / "operations" / "capabilities" / "lifecycle_status.md").exists()
