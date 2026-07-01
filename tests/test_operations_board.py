import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.operations_board import generate_operations_board, format_operations_board_markdown


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def sample_artifacts(root):
    write_json(root, "collaboration/status/worker_inbox_summary.json", {
        "worker_count": 1,
        "message_count": 2,
        "workers": [{"worker": "worker.audit", "message_count": 2, "messages": [{"valid": True}, {"valid": False}]}],
        "errors": [],
    })
    write_json(root, "runtime/collaboration/routing/latest.json", {
        "open_messages": 2,
        "decisions": [{"message_id": "m1"}, {"message_id": "m2"}],
        "errors": [],
    })
    write_json(root, "runtime/collaboration/worker_inboxes/worker.audit.json", {
        "worker": "worker.audit",
        "messages": [{"message_id": "m1"}, {"message_id": "m2"}],
    })
    write_json(root, "runtime/audit/latest.json", {"summary": {"passed": 5, "failed": 0}})
    write_json(root, "collaboration/audit/results/result1.json", {"id": "a1", "status": "passed"})
    write_json(root, "data/registry/capabilities.json", [
        {"id": "CAP-1", "name": "Ops Board", "status": "Implemented", "lifecycle_state": "Implemented"}
    ])
    write_json(root, "data/registry/services.json", [{"id": "SVC-1", "status": "Active"}])
    write_json(root, "data/registry/residents.json", [{"id": "RES-1", "status": "Active"}])
    write_json(root, "data/registry/providers.json", [{"id": "PROV-1", "status": "Available"}])


def test_operations_board_generation_with_all_sample_artifacts(tmp_path):
    sample_artifacts(tmp_path)

    board = generate_operations_board(tmp_path)

    assert board["collaboration"]["open_message_count"] == 2
    assert board["collaboration"]["routed_message_count"] == 2
    assert board["workers"]["known_workers"][0]["invalid_messages"] == 1
    assert board["capabilities"]["count"] == 1
    assert board["services_and_residents"]["provider_count"] == 1
    assert (tmp_path / "runtime" / "operations" / "operations_board.json").exists()
    assert (tmp_path / "operations" / "board" / "latest.md").exists()


def test_operations_board_generation_with_missing_artifacts(tmp_path):
    board = generate_operations_board(tmp_path)

    assert board["summary"]["overall_status"] == "warning"
    assert board["summary"]["missing_artifact_count"] > 0
    assert any(w["type"] == "missing_optional_artifact" for w in board["warnings"])


def test_operations_board_generation_with_malformed_json(tmp_path):
    sample_artifacts(tmp_path)
    bad = tmp_path / "runtime" / "audit" / "latest.json"
    bad.write_text("{not-json", encoding="utf-8")

    board = generate_operations_board(tmp_path)

    assert any(w["type"] == "malformed_json" and w["path"] == "runtime/audit/latest.json" for w in board["warnings"])
    assert board["audit"]["latest_summary"] == {}


def test_operations_board_markdown_generation(tmp_path):
    sample_artifacts(tmp_path)
    board = generate_operations_board(tmp_path, write=False)

    markdown = format_operations_board_markdown(board)

    assert markdown.startswith("# Estate Operations Board")
    assert "## Summary" in markdown
    assert "## Collaboration" in markdown
    assert "## Warnings" in markdown


def test_operations_board_cli_registration(tmp_path):
    sample_artifacts(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "operations-board", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["collaboration"]["open_message_count"] == 2
