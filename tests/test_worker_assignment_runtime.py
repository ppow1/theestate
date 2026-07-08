import json
import subprocess
import sys
from pathlib import Path

from estate.core.worker_assignment_runtime import WorkerAssignmentRuntime
from estate.core.worker_assignments import WorkerAssignmentRecord


def test_assignment_record_written(tmp_path):
    runtime = WorkerAssignmentRuntime(root=tmp_path)
    rec, paths = runtime.create_assignment(assigned_by="Steward", assigned_to="A2C2", mission="Build", summary="Build summary")
    assert Path(paths["record"]).exists()
    assert json.loads(Path(paths["record"]).read_text())["assignment_id"] == rec.assignment_id


def test_assignment_update_changes_state(tmp_path):
    runtime = WorkerAssignmentRuntime(root=tmp_path)
    rec, _ = runtime.create_assignment(assigned_by="Steward", assigned_to="A2C2", mission="Build", summary="Build summary")
    updated, _ = runtime.update_assignment(rec.assignment_id, state="running")
    assert updated.state == "running"
    assert runtime.load_assignment(rec.assignment_id).state == "running"


def test_board_and_latest_status_generated(tmp_path):
    runtime = WorkerAssignmentRuntime(root=tmp_path)
    rec, paths = runtime.create_assignment(assigned_by="Steward", assigned_to="A2C2", mission="Build", summary="Build summary")
    board = json.loads(Path(paths["board"]).read_text())
    latest = json.loads(Path(paths["latest"]).read_text())
    assert board["assignment_count"] == 1
    assert latest["assignment_id"] == rec.assignment_id


def test_cli_create_update_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "src")
    cmd = [sys.executable, "-m", "estate.cli.main"]
    create = subprocess.run(cmd + ["worker-assignment-create", "--work-package-id", "WP-0608", "--assigned-to", "A2C2", "--assigned-by", "Steward", "--mission", "Implement worker assignment board"], cwd=Path.cwd(), text=True, capture_output=True)
    assert create.returncode == 0, create.stdout + create.stderr
    assignment_id = [line.split(": ", 1)[1] for line in create.stdout.splitlines() if line.startswith("Worker assignment created")][0]
    update = subprocess.run(cmd + ["worker-assignment-update", "--assignment-id", assignment_id, "--state", "running"], cwd=Path.cwd(), text=True, capture_output=True)
    assert update.returncode == 0, update.stdout + update.stderr
    listing = subprocess.run(cmd + ["worker-assignment-list"], cwd=Path.cwd(), text=True, capture_output=True)
    assert listing.returncode == 0, listing.stdout + listing.stderr
    assert assignment_id in listing.stdout


def test_cli_list_succeeds_with_no_assignments(tmp_path):
    board = WorkerAssignmentRuntime(root=tmp_path).generate_board(write=True)
    assert board["assignment_count"] == 0
    assert board["active_count"] == 0


def test_cli_list_reports_active_and_blocked_assignments(tmp_path):
    runtime = WorkerAssignmentRuntime(root=tmp_path)
    runtime.create_assignment(assigned_by="Steward", assigned_to="A2C1", mission="Active", summary="Active")
    runtime.create_assignment(assigned_by="Steward", assigned_to="A2C2", mission="Blocked", summary="Blocked", state="blocked", blocked_reason="Waiting")
    board = runtime.generate_board(write=True)
    assert board["active_count"] == 1
    assert board["blocked_count"] == 1
