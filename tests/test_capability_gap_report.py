import json
from pathlib import Path

from estate.core.capability_gap_report import generate_capability_gap_report, format_capability_gap_report


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed_root(tmp_path):
    write_json(tmp_path / "data/registry/providers.json", [])
    write_json(tmp_path / "data/registry/services.json", [])
    write_json(tmp_path / "data/registry/missions.json", {"missions": []})
    write(tmp_path / "operations/boards/roadmap.md", """# Roadmap
| Capability | Current Milestone | Status | Key Dependency | Future Initiative |
|---|---|---|---|---|
| Roadmap Only | Design | Planned | Stable registries | Build later |
""")
    write(tmp_path / "operations/readiness/operational_readiness_dashboard.md", """# Operational Readiness Dashboard
Overall readiness status: blocked
## Degraded Subsystems
- unavailable_subsystems: One or more source artifacts are unavailable.
""")
    write(tmp_path / "operations/validation/validation_metrics_dashboard.md", "# Validation Metrics Dashboard\n")


def test_capability_gap_report_covers_required_states(tmp_path):
    seed_root(tmp_path)
    write_json(tmp_path / "data/registry/capabilities.json", [
        {"id": "CAP-PLAN", "name": "Planned Only", "lifecycle_state": "Designed", "status": "Pending Install", "dependencies": []},
        {"id": "CAP-UNVALIDATED", "name": "Implemented Unvalidated", "lifecycle_state": "Implemented", "status": "Installed", "implementation_references": ["impl.txt"], "dependencies": []},
        {"id": "CAP-OP", "name": "Operational Validated", "lifecycle_state": "Implemented", "status": "Operational", "implementation_references": ["impl.txt"], "dependencies": []},
        {"id": "CAP-DEGRADED", "name": "Degraded Capability", "lifecycle_state": "Implemented", "status": "Degraded", "implementation_references": ["impl.txt"], "dependencies": []},
        {"id": "CAP-BLOCKED", "name": "Blocked Capability", "lifecycle_state": "Implemented", "status": "Installed", "implementation_references": ["impl.txt"], "dependencies": ["CAP-MISSING"]},
    ])
    write(tmp_path / "impl.txt", "implementation")
    write_json(tmp_path / "runtime/validation/operational_validation_report.json", {
        "capabilities_reviewed": [
            {"id": "CAP-OP", "validation_evidence_found": True, "evidence_gaps": []}
        ]
    })

    report = generate_capability_gap_report(tmp_path, write=False)

    assert any(item["id"] == "CAP-PLAN" for item in report["planned_capabilities_without_implementation_evidence"])
    assert any(item["id"] == "CAP-UNVALIDATED" for item in report["implemented_capabilities_missing_validation_evidence"])
    assert any(item["id"] == "CAP-OP" for item in report["operational_capabilities"])
    assert any(item.get("id") == "CAP-DEGRADED" for item in report["operational_capabilities_with_degraded_status"])
    assert any(item["id"] == "CAP-BLOCKED" for item in report["capabilities_blocked_by_dependencies"])
    assert any(item["name"] == "Roadmap Only" for item in report["planned_capabilities_without_implementation_evidence"])
    assert report["missing_data_states"]


def test_capability_gap_report_writes_json_and_markdown(tmp_path):
    seed_root(tmp_path)
    write_json(tmp_path / "data/registry/capabilities.json", [])

    report = generate_capability_gap_report(tmp_path, write=True)
    markdown = format_capability_gap_report(report)

    assert (tmp_path / "runtime/capabilities/capability_gap_report.json").exists()
    assert (tmp_path / "operations/capabilities/capability_gap_report.md").exists()
    assert "Planned Capabilities Without Implementation Evidence" in markdown
    assert "None found." in markdown or "Roadmap Only" in markdown
