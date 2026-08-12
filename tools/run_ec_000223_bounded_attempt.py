"""Run one bounded EC-000223 attempt with independent result collection.

The child pipes are drained while each child is running.  Waiting for a child
to exit before reading its output can deadlock when governed JSON exceeds the
Windows pipe buffer; this runner intentionally keeps collection concurrent.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from tools.concurrent_result_collection import collect_processes
except ModuleNotFoundError:  # direct execution as ``python tools/run_...py``
    from concurrent_result_collection import collect_processes

P100_UUID = "GPU-6785b322-899d-8eec-e817-31d83279a414"
RTX4090_UUID = "GPU-46f3fd00-5454-4536-4196-5d8b727e14f2"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sample_telemetry() -> dict[str, object]:
    command = ["nvidia-smi", "--query-gpu=uuid,utilization.gpu,memory.used,memory.free,temperature.gpu,power.draw", "--format=csv,noheader,nounits"]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "nvidia-smi failed")
    rows: dict[str, dict[str, object]] = {}
    for line in completed.stdout.splitlines():
        fields = [field.strip() for field in line.split(",")]
        if len(fields) != 6:
            continue
        uuid, utilization, used, free, temperature, power = fields
        rows[uuid] = {"utilization": float(utilization), "memory_used_mib": float(used), "memory_free_mib": float(free), "temperature_c": float(temperature), "power_w": float(power)}
    if P100_UUID not in rows or RTX4090_UUID not in rows:
        raise RuntimeError("required GPU UUID missing from nvidia-smi")
    return {"observed_at": _now(), "gpus": rows}


def telemetry_loop(samples: list[dict[str, object]], stop: threading.Event, guard: dict[str, object]) -> None:
    above_target = 0
    while not stop.is_set():
        try:
            sample = sample_telemetry()
            samples.append(sample)
            p100 = sample["gpus"][P100_UUID]
            utilization = float(p100["utilization"])
            above_target = above_target + 1 if utilization > 80 else 0
            if above_target >= 2:
                guard.update({"state": "cancel_requested", "reason": "P100 utilization materially exceeded 80 percent for two consecutive samples"})
                stop.set()
                return
        except Exception as exc:  # device loss is a hard stop; no recovery action here
            guard.update({"state": "hard_stop", "reason": str(exc)})
            stop.set()
            return
        stop.wait(1.0)


def _child_code() -> str:
    return (
        "import json,sys; from pathlib import Path; "
        "from estate.core.openwebui_engineering_workflow import execute_bounded_local_text_from_chat; "
        "payload=json.loads(sys.argv[1]); result=execute_bounded_local_text_from_chat(payload, user_message=sys.argv[2], session_id=sys.argv[3], root=Path(sys.argv[4])); "
        "print(json.dumps(result, sort_keys=True))"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    child = _child_code()
    tasks = {
        "4090": ({"model": "estate/grace"}, "Grace, run a small bounded local text task on the RTX 4090. Answer with one short sentence.", "ec-000223-task-a"),
        "p100": ({"model": "estate/grace"}, "Grace, run a small bounded local text task on the Tesla P100. Answer with one short sentence.", "ec-000223-task-b"),
    }
    processes = {}
    for name, (payload, prompt, session) in tasks.items():
        processes[name] = subprocess.Popen([sys.executable, "-c", child, json.dumps(payload), prompt, session, str(root)], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    samples: list[dict[str, object]] = []
    guard: dict[str, object] = {"state": "running", "target_utilization_percent": 80}
    telemetry_stop = threading.Event()
    telemetry_thread = threading.Thread(target=telemetry_loop, args=(samples, telemetry_stop, guard), daemon=True)
    telemetry_thread.start()
    started = _now()
    results = collect_processes(processes, timeout=240)
    telemetry_stop.set()
    telemetry_thread.join(timeout=6)
    if guard.get("state") in {"cancel_requested", "hard_stop"}:
        for process in processes.values():
            if process.poll() is None:
                process.terminate()
    result = {"schema": "ec-000223.bounded-attempt.v1", "started_at": started, "finished_at": _now(), "guard": guard, "telemetry": samples, "results": results, "process_ids": {name: process.pid for name, process in processes.items()}}
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": str(output.relative_to(root)).replace("\\", "/"), "guard": guard, "process_ids": result["process_ids"], "result_returncodes": {name: item["returncode"] for name, item in results.items()}}, sort_keys=True))
    return 0 if guard.get("state") == "running" and all(item["returncode"] == 0 for item in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
