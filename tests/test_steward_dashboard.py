import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.steward_dashboard import generate_steward_dashboard, format_steward_dashboard_markdown


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def sample_dashboard_inputs(root):
    write_json(root, "runtime/operations/operations_board.json", {
        "summary": {"overall_status": "ok", "warning_count": 0},
        "capabilities": {"items": [
            {"id": "CAP-A", "name": "Active Capability", "status": "Active", "lifecycle_state": "Implemented"},
            {"id": "CAP-B", "name": "Blocked Capability", "status": "Blocked", "lifecycle_state": "Implemented"},
            {"id": "CAP-C", "name": "Review Capability", "status": "Review Pending", "lifecycle_state": "Implemented"},
        ]},
        "workers": {"known_workers": [{"worker": "worker.audit", "message_count": 2}]},
        "audit": {"result_count": 1},
    })
    board_md = root / "operations/board/latest.md"
    board_md.parent.mkdir(parents=True, exist_ok=True)
    board_md.write_text("# Estate Operations Board\n", encoding="utf-8")
    write_json(root, "runtime/capabilities/capability_lifecycle_report.json", {
        "summary": {"capability_count": 3, "counts_by_lifecycle_state": {"Implemented": 3}},
        "candidates": {"operational_validation_candidates": ["CAP-A"]},
    })
    write_json(root, "collaboration/status/worker_inbox_summary.json", {
        "worker_count": 1,
        "message_count": 2,
        "workers": [{"worker": "worker.audit", "message_count": 2}],
    })
    write_json(root, "runtime/audit/latest.json", {"summary": {"passed": 4, "failed": 0}})
    write_json(root, "collaboration/audit/results/result1.json", {"id": "AUD-1", "status": "passed"})


def test_steward_dashboard_generation_with_full_inputs(tmp_path):
    sample_dashboard_inputs(tmp_path)

    dashboard = generate_steward_dashboard(tmp_path)

    assert dashboard["summary"]["operations_board_available"] is True
    assert len(dashboard["work"]["active"]) == 1
    assert len(dashboard["work"]["blocked"]) == 1
    assert len(dashboard["work"]["review_pending"]) == 1
    assert dashboard["audit_status"]["audit_result_count"] == 1
    assert dashboard["worker_inbox_status"]["worker_count"] == 1
    assert (tmp_path / "runtime/steward/dashboard.json").exists()
    assert (tmp_path / "operations/steward/dashboard.md").exists()


def test_steward_dashboard_generation_with_missing_operations_board(tmp_path):
    write_json(tmp_path, "runtime/audit/latest.json", {"summary": {"passed": 1}})

    dashboard = generate_steward_dashboard(tmp_path)

    assert dashboard["summary"]["operations_board_available"] is False
    assert any(w["type"] == "missing_optional_artifact" and w["path"] == "runtime/operations/operations_board.json" for w in dashboard["warnings_requiring_steward_attention"])


def test_steward_dashboard_generation_with_malformed_json(tmp_path):
    sample_dashboard_inputs(tmp_path)
    (tmp_path / "runtime/audit/latest.json").write_text("{not-json", encoding="utf-8")

    dashboard = generate_steward_dashboard(tmp_path)

    assert any(w["type"] == "malformed_json" and w["path"] == "runtime/audit/latest.json" for w in dashboard["warnings_requiring_steward_attention"])
    assert dashboard["audit_status"]["latest_summary"] == {}


def test_steward_dashboard_markdown_generation(tmp_path):
    sample_dashboard_inputs(tmp_path)
    dashboard = generate_steward_dashboard(tmp_path, write=False)

    markdown = format_steward_dashboard_markdown(dashboard)

    assert markdown.startswith("# Estate Steward Dashboard")
    assert "## Current Operational Summary" in markdown
    assert "## Audit Status" in markdown
    assert "## Warnings Requiring Steward Attention" in markdown


def test_steward_dashboard_cli_registration(tmp_path):
    sample_dashboard_inputs(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "steward-dashboard", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["operations_board_available"] is True
    assert (tmp_path / "runtime/steward/dashboard.json").exists()
