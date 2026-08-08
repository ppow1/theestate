import json
from pathlib import Path
import subprocess
import sys
import time


HARNESS = Path(__file__).resolve().parents[1] / "tools" / "cme_owner_isolation.py"


def launch(tmp_path, code, timeout="10"):
    result = subprocess.run(
        [sys.executable, str(HARNESS), "launch", "--evidence-root", str(tmp_path), "--timeout-seconds", timeout, "--", sys.executable, "-c", code],
        text=True, capture_output=True, check=True,
    )
    return json.loads(result.stdout)


def wait_for_manifest(run):
    manifest = Path(run["evidence_path"]) / "manifest.json"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            if data["completion_marker"]:
                return data
        time.sleep(0.05)
    raise AssertionError(f"harness did not complete: {manifest}")


def test_launch_returns_immediately_and_persists_stdout_stderr_exit_and_marker(tmp_path):
    started = time.monotonic()
    run = launch(tmp_path, "import sys; print('captured stdout'); print('captured stderr', file=sys.stderr)")
    assert time.monotonic() - started < 2
    assert run["harness_pid"] > 0
    data = wait_for_manifest(run)
    run_dir = Path(run["evidence_path"])
    assert data["exit_code"] == 0
    assert "captured stdout" in (run_dir / "stdout.txt").read_text(encoding="utf-8")
    assert "captured stderr" in (run_dir / "stderr.txt").read_text(encoding="utf-8")
    assert (run_dir / "completion.marker").read_text(encoding="utf-8").strip() == "CME_OWNER_ISOLATION_COMPLETE"
    assert data["test_child_pid"] > 0
    assert data["completion_timestamp"]


def test_child_timeout_is_durable(tmp_path):
    run = launch(tmp_path, "import time; time.sleep(5)", timeout="0.2")
    data = wait_for_manifest(run)
    assert data["status"] == "TIMED_OUT"
    assert data["timeout_classification"] == "CHILD_TIMEOUT"
    assert data["completion_marker"] == "CME_OWNER_ISOLATION_COMPLETE"
    assert data["exit_code"] != 0


def test_run_ids_are_unique_and_unit_harness_never_targets_live_default_state(tmp_path):
    first = launch(tmp_path, "print('one')")
    second = launch(tmp_path, "print('two')")
    assert first["run_id"] != second["run_id"]
    assert "theestate-data" not in first["evidence_path"]
    assert "chatgpt-mailbox-worker" not in first["evidence_path"]


def test_separate_inspect_command_proves_independent_completion(tmp_path):
    run = launch(tmp_path, "print('inspectable')")
    data = wait_for_manifest(run)
    inspected = subprocess.run(
        [sys.executable, str(HARNESS), "inspect", run["run_id"], "--evidence-root", str(tmp_path)],
        text=True, capture_output=True, check=True,
    )
    result = json.loads(inspected.stdout)
    assert result["run_id"] == run["run_id"]
    assert result["child_pid"] == data["child_pid"]
    assert result["independent_completion_proven"] is True
