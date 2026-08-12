from __future__ import annotations

import subprocess
import sys
import threading

from tools.concurrent_result_collection import collect_processes
from tools.run_ec_000223_bounded_attempt import telemetry_loop


def test_two_large_child_results_are_collected_without_pipe_deadlock():
    command = [sys.executable, "-c", "import sys; sys.stdout.write('x' * 250000); sys.stderr.write('y' * 250000)"]
    processes = {name: subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for name in ("4090", "p100")}
    results = collect_processes(processes, timeout=10)
    assert set(results) == {"4090", "p100"}
    assert all(result["returncode"] == 0 for result in results.values())
    assert all(len(result["stdout"]) == 250000 and len(result["stderr"]) == 250000 for result in results.values())


def test_telemetry_guard_runs_independently_of_result_collection(monkeypatch):
    samples = []
    guard = {}
    stop = threading.Event()
    def sample_once():
        stop.set()
        return {"observed_at": "t1", "gpus": {"GPU-6785b322-899d-8eec-e817-31d83279a414": {"utilization": 10}}}
    monkeypatch.setattr("tools.run_ec_000223_bounded_attempt.sample_telemetry", sample_once)
    thread = threading.Thread(target=telemetry_loop, args=(samples, stop, guard))
    thread.start()
    thread.join(timeout=3)
    stop.set()
    thread.join(timeout=3)
    assert samples and guard == {}
