#!/usr/bin/env python3
"""Read-only diagnostic CLI for WP-4223 recommendations."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from recommendation_engine import RecommendationError, compare, explain, recommend, validate_inputs


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def from_manifest(path: Path) -> dict:
    module_path = Path(__file__).parents[1] / "WP-4222/dashboard_integration/integration.py"
    spec = importlib.util.spec_from_file_location("wp4222_integration", module_path)
    if spec is None or spec.loader is None:
        raise RecommendationError("WP-4222 integration provider is not loadable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.compose_dashboard(module.load_manifest(path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic advisory recommendation diagnostics")
    parser.add_argument("command", choices=("recommend", "explain", "compare", "validate"))
    parser.add_argument("input", type=Path, help="WP-4222 integration snapshot (or manifest with --manifest)")
    parser.add_argument("identifiers", nargs="*")
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    try:
        integration = from_manifest(args.input) if args.manifest else load(args.input)
        if args.command == "validate":
            errors = validate_inputs(integration)
            print(json.dumps({"valid": not errors, "errors": errors}, sort_keys=True, indent=2)); return bool(errors)
        result = recommend(integration, limit=args.limit)
        if args.command == "recommend": value = result
        elif args.command == "explain" and len(args.identifiers) == 1: value = explain(result, args.identifiers[0])
        elif args.command == "compare" and len(args.identifiers) == 2: value = compare(result, *args.identifiers)
        else: parser.error("explain requires one ID; compare requires two IDs")
        print(json.dumps(value, sort_keys=True, indent=2)); return 0
    except (OSError, json.JSONDecodeError, RecommendationError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
