"""Operator entry point for the canonical Estate WebUI/Gateway controller."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from estate.core.canonical_webui_gateway_runtime import load_config, promote, restart, rollback, start_slot, status, stop_slot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "restart", "promote", "rollback", "status"])
    parser.add_argument("--slot", choices=["blue", "green"], default="blue")
    parser.add_argument("--service", choices=["gateway", "webui"], action="append")
    parser.add_argument("--open-browser", action="store_true", help="open WebUI only after semantic readiness")
    parser.add_argument("--config", type=Path, default=Path(__file__).parents[1] / "config" / "runtime" / "canonical_webui_gateway.json")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.action == "start":
        result = start_slot(
            config,
            args.slot,
            services=tuple(args.service or ("gateway", "webui")),
            active_ports=args.slot == "blue",
            open_browser=args.open_browser,
        )
    elif args.action == "stop":
        result = stop_slot(config, args.slot)
    elif args.action == "restart":
        result = restart(config)
    elif args.action == "promote":
        result = promote(config, args.slot)
    elif args.action == "rollback":
        result = rollback(config)
    else:
        result = status(config)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
