import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.service_status_board import generate_service_status_board, format_service_status_board


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path, payload):
    write(path, json.dumps(payload))


def seed(root, services, providers=None):
    write(root / "src/estate/cli/main.py", "cli")
    write_json(root / "data/registry/capabilities.json", [])
    write_json(root / "data/registry/providers.json", providers or [])
    write_json(root / "data/registry/services.json", services)


def by_id(payload, service_id):
    return next(service for service in payload["services"] if service["service_id"] == service_id)


def test_status_board_renders_complete_service_data_with_drill_down_links(tmp_path):
    seed(tmp_path, [
        {"id": "SVC-HEALTHY", "name": "Healthy", "status": "Active", "owner": "Ops", "dependencies": []},
        {"id": "SVC-DEGRADED", "name": "Degraded", "status": "Degraded", "owner": "Ops", "dependencies": ["SVC-HEALTHY"]},
        {"id": "SVC-BLOCKED", "name": "Blocked", "status": "Blocked", "owner": "Ops", "dependencies": []},
        {"id": "SVC-UNAVAILABLE", "name": "Unavailable", "status": "Unavailable", "owner": "Ops", "dependencies": []},
    ])

    payload = generate_service_status_board(tmp_path, write=True)
    markdown = format_service_status_board(payload)

    assert by_id(payload, "SVC-HEALTHY")["board_state"] == "healthy"
    assert by_id(payload, "SVC-DEGRADED")["board_state"] == "degraded"
    assert by_id(payload, "SVC-BLOCKED")["board_state"] == "blocked"
    assert by_id(payload, "SVC-UNAVAILABLE")["board_state"] == "unavailable"
    assert by_id(payload, "SVC-DEGRADED")["dependencies"] == [{"service_id": "SVC-HEALTHY", "health_status": "healthy"}]
    assert all(by_id(payload, "SVC-HEALTHY")["drill_down_links"].values())
    assert "does not become the source of truth" in markdown
    assert (tmp_path / "runtime/services/service_status_board.json").exists()
    assert (tmp_path / "operations/services/service_status_board.md").exists()


def test_status_board_handles_partial_and_unavailable_service_data(tmp_path):
    seed(tmp_path, [
        {"id": "SVC-PARTIAL", "name": "Partial", "status": "Draft", "owner": "Ops"},
        {"id": "SVC-MISSING", "status": "Active", "dependencies": ["SVC-NOPE"]},
    ])

    payload = generate_service_status_board(tmp_path, write=False)

    assert by_id(payload, "SVC-PARTIAL")["board_state"] in {"degraded", "unknown"}
    assert by_id(payload, "SVC-MISSING")["board_state"] == "degraded"
    assert payload["summary"]["warning_count"] > 0
    for service in payload["services"]:
        for link in service["source_artifacts"]:
            assert link["path"]
            assert link["available"] is True


def test_status_board_gracefully_reports_unavailable_registry(tmp_path):
    seed(tmp_path, [{"id": "SVC-A", "name": "A", "status": "Active", "owner": "Ops", "dependencies": []}])
    (tmp_path / "data/registry/services.json").unlink()

    payload = generate_service_status_board(tmp_path, write=False)

    assert payload["summary"]["service_count"] >= 0
    assert any(path.endswith("services.json") for path in payload["inputs"]["unavailable"])


def test_service_status_board_cli(tmp_path):
    seed(tmp_path, [{"id": "SVC-A", "name": "A", "status": "Active", "owner": "Ops", "dependencies": []}])

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "service-status-board", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["service_count"] >= 1
    assert (tmp_path / "runtime/services/service_status_board.json").exists()
