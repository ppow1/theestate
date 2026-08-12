"""Detached, durable runner for CME process-ownership tests.

The launch command only creates a new process and returns.  The detached
runner owns all waiting, timeout handling, and evidence writes.  It is
deliberately independent of CME and does not inspect or mutate Live state.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_ROOT = REPOSITORY_ROOT / "runtime" / "evidence" / "cme-owner-isolation"
FOCUSED_TEST = REPOSITORY_ROOT / "tests" / "test_cme_chatgpt_reasoning_owner.py"
LIVE_ACCEPTANCE = REPOSITORY_ROOT / "tools" / "cme_live_acceptance.py"
FULL_LOOP_ACCEPTANCE = REPOSITORY_ROOT / "tools" / "cme_full_loop_acceptance.py"
CONTINUE_8_ACCEPTANCE = REPOSITORY_ROOT / "tools" / "cme_continue_8_acceptance.py"
EXECUTION_FIXTURE_ACCEPTANCE = REPOSITORY_ROOT / "tools" / "cme_execution_fixture_acceptance.py"
COMPLETION_MARKER = "CME_OWNER_ISOLATION_COMPLETE"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _run_id() -> str:
    return "cme-owner-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid4().hex[:10]


def launch(command: list[str], *, evidence_root: Path = DEFAULT_EVIDENCE_ROOT, timeout_seconds: float = 900) -> dict:
    """Launch the harness and return without waiting for the test child."""
    if not command:
        raise ValueError("command is required")
    evidence_root.mkdir(parents=True, exist_ok=True)
    run_id = _run_id()
    run_dir = evidence_root / run_id
    run_dir.mkdir()  # UUID-backed IDs make collisions practically impossible; do not reuse them.
    request = {
        "run_id": run_id,
        "command": command,
        "timeout_seconds": timeout_seconds,
        "evidence_path": str(run_dir),
        "requested_at": _now(),
    }
    _write_json(run_dir / "request.json", request)
    harness_command = [sys.executable, str(Path(__file__).resolve()), "run", str(run_dir / "request.json")]
    creation_flags = 0
    if os.name == "nt":
        # Break away from a command-runner job, create a new process group, and
        # detach stdio.  The harness is consequently the first durable owner
        # below the runner; Codex never owns or waits on pytest.
        creation_flags = (
            subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.DETACHED_PROCESS
            | getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000)
        )
    process = subprocess.Popen(
        harness_command,
        cwd=str(Path(__file__).resolve().parents[1]),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        creationflags=creation_flags,
    )
    return {"run_id": run_id, "harness_pid": process.pid, "evidence_path": str(run_dir), "launch_returned": True}


def run_harness(request_path: Path) -> int:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    run_dir = Path(request["evidence_path"])
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    manifest_path = run_dir / "manifest.json"
    marker_path = run_dir / "completion.marker"
    started = _now()
    command = [str(run_dir) if item == "__RUN_DIR__" else item for item in request["command"]]
    manifest = {
        "schema": "estate.cme-owner-isolation-run.v1",
        "run_id": request["run_id"],
        "harness_pid": os.getpid(),
        "parent_pid": os.getppid(),
        "child_pid": None,
        "test_child_pid": None,
        "start_timestamp": started,
        "end_timestamp": None,
        "command": command,
        "command_string": subprocess.list2cmdline(command),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "exit_code": None,
        "completion_timestamp": None,
        "completion_marker": None,
        "timeout_classification": None,
        "status": "RUNNING",
    }
    _write_json(manifest_path, manifest)
    child = None
    try:
        with stdout_path.open("w", encoding="utf-8", errors="replace") as stdout, stderr_path.open("w", encoding="utf-8", errors="replace") as stderr:
            flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
            child = subprocess.Popen(command, cwd=str(Path(__file__).resolve().parents[1]), stdout=stdout, stderr=stderr, text=True, creationflags=flags)
            manifest["test_child_pid"] = child.pid
            manifest["child_pid"] = child.pid
            _write_json(manifest_path, manifest)
            try:
                child.wait(timeout=float(request.get("timeout_seconds", 900)))
            except subprocess.TimeoutExpired:
                manifest["timeout_classification"] = "CHILD_TIMEOUT"
                manifest["status"] = "TIMED_OUT"
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            manifest["exit_code"] = child.returncode
    except Exception as exc:  # Evidence must survive harness/test launch failures too.
        manifest["status"] = "HARNESS_ERROR"
        manifest["stderr_error"] = f"{type(exc).__name__}: {exc}"
        manifest["exit_code"] = 1
    finally:
        if manifest["status"] == "RUNNING":
            manifest["status"] = "COMPLETED" if manifest["exit_code"] == 0 else "FAILED"
        manifest["completion_timestamp"] = _now()
        manifest["end_timestamp"] = manifest["completion_timestamp"]
        manifest["completion_marker"] = COMPLETION_MARKER
        # The manifest is durable before the marker is published.  A reader
        # that observes the marker can therefore trust every required field.
        _write_json(manifest_path, manifest)
        marker_path.write_text(COMPLETION_MARKER + "\n", encoding="utf-8")
    return int(manifest["exit_code"] if manifest["exit_code"] is not None else 1)


def inspect_run(run_id: str, *, evidence_root: Path = DEFAULT_EVIDENCE_ROOT) -> dict:
    """Read-only inspection performed after launch in a separate process."""
    run_dir = evidence_root / run_id
    manifest_path = run_dir / "manifest.json"
    marker_path = run_dir / "completion.marker"
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest not found for run {run_id}: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    marker = marker_path.read_text(encoding="utf-8").strip() if marker_path.exists() else None
    manifest["completion_marker_observed"] = marker
    manifest["independent_completion_proven"] = bool(
        marker == COMPLETION_MARKER
        and manifest.get("end_timestamp")
        and manifest.get("exit_code") is not None
        and manifest.get("child_pid")
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    launch_parser = sub.add_parser("launch")
    launch_parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    launch_parser.add_argument("--timeout-seconds", type=float, default=900)
    launch_parser.add_argument("command", nargs=argparse.REMAINDER)
    focused_parser = sub.add_parser("launch-focused", help="launch the guarded process-ownership pytest via the detached harness")
    focused_parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    focused_parser.add_argument("--timeout-seconds", type=float, default=900)
    live_parser = sub.add_parser("launch-live", help="launch the existing 7.00 live acceptance through the detached harness")
    live_parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    live_parser.add_argument("--timeout-seconds", type=float, default=900)
    reconcile_parser = sub.add_parser("launch-reconcile", help="reconcile an already-resolved live attempt through the detached harness")
    reconcile_parser.add_argument("evidence_path", type=Path)
    reconcile_parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    reconcile_parser.add_argument("--timeout-seconds", type=float, default=120)
    full_parser = sub.add_parser("launch-full-loop", help="launch one full CME reason/execute/observe/reason acceptance")
    full_parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    full_parser.add_argument("--timeout-seconds", type=float, default=1800)
    state_parser = sub.add_parser("launch-state-reconcile", help="reconcile one terminal existing CME turn through the detached harness")
    state_parser.add_argument("logical_consultation_id")
    state_parser.add_argument("evidence_path", type=Path)
    state_parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    state_parser.add_argument("--timeout-seconds", type=float, default=120)
    continue_parser = sub.add_parser("launch-continue-8", help="continue existing consultation 8.00 through evidence acquisition")
    continue_parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    continue_parser.add_argument("--timeout-seconds", type=float, default=1800)
    fixture_parser = sub.add_parser("launch-execution-fixture", help="launch the controlled fixture execution-branch acceptance")
    fixture_parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    fixture_parser.add_argument("--timeout-seconds", type=float, default=1800)
    inspect_parser = sub.add_parser("inspect", help="read persisted evidence after launch")
    inspect_parser.add_argument("run_id")
    inspect_parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("request", type=Path)
    args = parser.parse_args()
    if args.action == "launch":
        command = args.command[1:] if args.command[:1] == ["--"] else args.command
        print(json.dumps(launch(command, evidence_root=args.evidence_root, timeout_seconds=args.timeout_seconds)))
        return 0
    if args.action == "launch-focused":
        command = [sys.executable, "-m", "pytest", "-q", str(FOCUSED_TEST)]
        print(json.dumps(launch(command, evidence_root=args.evidence_root, timeout_seconds=args.timeout_seconds)))
        return 0
    if args.action == "launch-live":
        command = [sys.executable, str(LIVE_ACCEPTANCE), "__RUN_DIR__"]
        print(json.dumps(launch(command, evidence_root=args.evidence_root, timeout_seconds=args.timeout_seconds)))
        return 0
    if args.action == "launch-reconcile":
        command = [sys.executable, str(REPOSITORY_ROOT / "tools" / "cme_post_completion_reconcile.py"), str(args.evidence_path)]
        print(json.dumps(launch(command, evidence_root=args.evidence_root, timeout_seconds=args.timeout_seconds)))
        return 0
    if args.action == "launch-full-loop":
        command = [sys.executable, str(FULL_LOOP_ACCEPTANCE), "__RUN_DIR__"]
        print(json.dumps(launch(command, evidence_root=args.evidence_root, timeout_seconds=args.timeout_seconds)))
        return 0
    if args.action == "launch-state-reconcile":
        command = [sys.executable, str(REPOSITORY_ROOT / "tools" / "cme_state_reconcile.py"), args.logical_consultation_id, str(args.evidence_path)]
        print(json.dumps(launch(command, evidence_root=args.evidence_root, timeout_seconds=args.timeout_seconds)))
        return 0
    if args.action == "launch-continue-8":
        command = [sys.executable, str(CONTINUE_8_ACCEPTANCE), "__RUN_DIR__"]
        print(json.dumps(launch(command, evidence_root=args.evidence_root, timeout_seconds=args.timeout_seconds)))
        return 0
    if args.action == "launch-execution-fixture":
        command = [sys.executable, str(EXECUTION_FIXTURE_ACCEPTANCE), "__RUN_DIR__"]
        print(json.dumps(launch(command, evidence_root=args.evidence_root, timeout_seconds=args.timeout_seconds)))
        return 0
    if args.action == "inspect":
        print(json.dumps(inspect_run(args.run_id, evidence_root=args.evidence_root), indent=2, sort_keys=True))
        return 0
    return run_harness(args.request)


if __name__ == "__main__":
    raise SystemExit(main())
