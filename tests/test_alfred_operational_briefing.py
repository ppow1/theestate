import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.alfred import alfred_briefing


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_text(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def sample_artifacts(root):
    write_json(root, "collaboration/messages/msg_review.json", {
        "id": "msg_review",
        "created_at": "2026-07-02T00:00:00",
        "created_by": "Chief Architect #3",
        "source": "office.chief_architect_3",
        "destination": "office.chief_architect_2",
        "message_type": "review_request",
        "status": "open",
        "requires_ack": True,
        "ack_status": "pending",
        "payload": {"title": "Review operational activation", "artifact_refs": []},
    })
    write_text(root, "collaboration/work_packages/pending/WP-TEST_sample.md", "# WP-TEST — Sample Work\n\n## Mission\nDo it.\n")
    write_json(root, "runtime/operations/operations_board.json", {"summary": {"overall_status": "ready"}})
    write_json(root, "runtime/steward/dashboard.json", {"summary": {"ready": True}})
    write_json(root, "runtime/capabilities/capability_lifecycle_report.json", {"capabilities_reviewed": []})
    write_json(root, "runtime/dependencies/dependency_graph.json", {"nodes": [], "edges": []})
    write_json(root, "runtime/validation/operational_validation_report.json", {
        "candidates_for_operationally_validated_review": [{"id": "CAP-1", "name": "Sample", "basis": "Evidence found."}],
        "candidates_for_institutionalized_review": [],
    })
    write_text(root, "operations/boards/parking_lot.md", "| ID | Idea | Category | Priority | Originator | Date Captured | Status | Target Milestone | Promotion Condition |\n|---|---|---|---|---|---|---|---|---|\n| PL-1 | Add Alfred daily briefing | Alfred | Strategic | Worker | 2026-07-02 | Captured | Now | Useful |\n")


def test_operational_briefing_generation_with_representative_artifacts(tmp_path):
    sample_artifacts(tmp_path)

    briefing = alfred_briefing(tmp_path)

    assert briefing["summary"]["pending_work_packages"] == 1
    assert briefing["summary"]["messages_requiring_acknowledgement"] == 1
    assert briefing["validation_candidates"][0]["id"] == "CAP-1"
    assert briefing["parking_lot_items_recently_relevant"][0]["id"] == "PL-1"
    assert (tmp_path / "runtime/alfred/operational_briefing.json").exists()
    assert (tmp_path / "operations/alfred/operational_briefing.md").exists()


def test_missing_artifacts_are_warnings_not_fatal(tmp_path):
    briefing = alfred_briefing(tmp_path)

    assert briefing["summary"]["warnings"] > 0
    assert any(w["type"] == "missing_artifact" for w in briefing["warnings"])


def test_messages_requiring_acknowledgement_appear_in_briefing(tmp_path):
    sample_artifacts(tmp_path)

    briefing = alfred_briefing(tmp_path, write=False)

    assert [m["id"] for m in briefing["messages_requiring_acknowledgement"]] == ["msg_review"]


def test_pending_work_packages_and_codex_ready_commands_appear_without_execution(tmp_path):
    sample_artifacts(tmp_path)

    briefing = alfred_briefing(tmp_path, write=False)

    assert briefing["active_pending_work_packages"][0]["id"] == "WP-TEST"
    assert "Read" in briefing["codex_ready_next_commands"][0]
    assert "do exactly what it says" in briefing["codex_ready_next_commands"][0]
    assert not (tmp_path / "collaboration/work_packages/completions").exists()


def test_alfred_operational_briefing_cli_registration(tmp_path):
    sample_artifacts(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "alfred-operational-briefing", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["pending_work_packages"] == 1
    assert payload["messages_requiring_acknowledgement"][0]["id"] == "msg_review"
