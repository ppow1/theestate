"""Start one registered, UUID-bound Ollama lane without loading a model."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from estate.core.gpu_runtime_lanes import endpoint_health, load_registered_lanes, start_ollama_lane


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--lane-id", required=True)
    parser.add_argument("--executable")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    lane = next((row for row in load_registered_lanes(root) if row.runtime_lane_id == args.lane_id), None)
    if lane is None:
        raise SystemExit(f"registered runtime lane not found: {args.lane_id}")
    evidence = start_ollama_lane(root, lane, executable=args.executable)
    health = endpoint_health(lane)
    for _ in range(30):
        if health.get("healthy"):
            break
        time.sleep(1)
        health = endpoint_health(lane)
    print(json.dumps({"process": evidence, "health": health}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
