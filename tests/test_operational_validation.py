import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.operational_validation import generate_operational_validation_report, format_operational_validation_markdown


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def lifecycle(caps):
    return {"version": 1, "capabilities": caps}


def test_evidence_present_generates_operational_validation_candidate(tmp_path):
    write_json(tmp_path, "runtime/capabilities/capability_lifecycle_report.json", lifecycle([
        {"id": "CAP-1", "title": "Operations Board", "lifecycle_state": "Implemented", "implementation_references": ["src/x.py"], "evidence_references": ["docs/x.md"]}
    ]))
    (tmp_path / "operations" / "board").mkdir(parents=True)
    (tmp_path / "operations" / "board" / "latest.md").write_text("Operations Board was exercised.", encoding="utf-8")

    report = generate_operational_validation_report(tmp_path, write=False)

    assert len(report["capabilities_reviewed"]) == 1
    assert report["candidates_for_operationally_validated_review"][0]["id"] == "CAP-1"
    assert report["capabilities_reviewed"][0]["validation_evidence_found"]


def test_evidence_missing_reports_gaps(tmp_path):
    write_json(tmp_path, "runtime/capabilities/capability_lifecycle_report.json", lifecycle([
        {"id": "CAP-1", "title": "Capability", "lifecycle_state": "Implemented"}
    ]))

    report = generate_operational_validation_report(tmp_path, write=False)

    assert report["evidence_gaps"][0]["id"] == "CAP-1"
    assert "implementation_reference" in report["evidence_gaps"][0]["gaps"]
    assert "validation_evidence" in report["evidence_gaps"][0]["gaps"]


def test_malformed_input_artifacts_are_warnings(tmp_path):
    path = tmp_path / "runtime" / "capabilities" / "capability_lifecycle_report.json"
    path.parent.mkdir(parents=True)
    path.write_text("{bad", encoding="utf-8")
    events = tmp_path / "runtime" / "collaboration" / "events" / "events.jsonl"
    events.parent.mkdir(parents=True)
    events.write_text('{"ok": true}\n{bad\n', encoding="utf-8")

    report = generate_operational_validation_report(tmp_path, write=False)

    assert report["capabilities_reviewed"] == []
    assert any(w["type"] == "malformed_input" for w in report["warnings"])


def test_institutionalized_candidate_generation(tmp_path):
    write_json(tmp_path, "runtime/capabilities/capability_lifecycle_report.json", lifecycle([
        {"id": "CAP-2", "title": "Worker Inbox", "lifecycle_state": "Operationally Validated", "implementation_references": ["src/y.py"], "evidence_references": ["docs/y.md"], "operational_evidence_references": ["runtime/y.json"]}
    ]))
    write_json(tmp_path, "collaboration/status/worker_inbox_summary.json", {"summary": "Worker Inbox active"})

    report = generate_operational_validation_report(tmp_path, write=False)

    assert report["candidates_for_institutionalized_review"][0]["id"] == "CAP-2"


def test_markdown_generation_includes_required_sections(tmp_path):
    write_json(tmp_path, "runtime/capabilities/capability_lifecycle_report.json", lifecycle([]))
    report = generate_operational_validation_report(tmp_path, write=False)

    markdown = format_operational_validation_markdown(report)

    assert markdown.startswith("# Continuous Operational Validation Report")
    assert "## Evidence Rules" in markdown
    assert "## Candidates for Operationally Validated Review" in markdown
    assert "## Limitations" in markdown


def test_operational_validation_cli_registration(tmp_path):
    write_json(tmp_path, "runtime/capabilities/capability_lifecycle_report.json", lifecycle([]))

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "operational-validation", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["capabilities_reviewed"] == []
    assert (tmp_path / "runtime" / "validation" / "operational_validation_report.json").exists()
    assert (tmp_path / "operations" / "validation" / "operational_validation_report.md").exists()
