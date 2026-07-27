#!/usr/bin/env python3
"""Read-only diagnostic CLI; emits JSON and never writes input files."""
import argparse
import json
from pathlib import Path

from analytics_engine import compare, explain, generate_snapshot, history, trend, validate_snapshot


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def main(argv=None):
    parser = argparse.ArgumentParser(description="WP-4225 read-only campaign analytics")
    sub = parser.add_subparsers(dest="command", required=True)
    analytics = sub.add_parser("analytics"); analytics.add_argument("observation"); analytics.add_argument("--generated-at", required=True)
    summary = sub.add_parser("summary"); summary.add_argument("snapshot")
    trends = sub.add_parser("trend"); trends.add_argument("history"); trends.add_argument("period", choices=("daily", "weekly", "monthly", "campaign_lifetime"))
    comparison = sub.add_parser("compare"); comparison.add_argument("left"); comparison.add_argument("right")
    histories = sub.add_parser("history"); histories.add_argument("history")
    validation = sub.add_parser("validate"); validation.add_argument("snapshot")
    explanation = sub.add_parser("explain"); explanation.add_argument("snapshot"); explanation.add_argument("--metric")
    args = parser.parse_args(argv)
    if args.command == "analytics": result = generate_snapshot(load(args.observation), generated_at=args.generated_at)
    elif args.command == "summary":
        item = load(args.snapshot); validate_snapshot(item)
        result = {"snapshot_identifier": item["snapshot_identifier"], "generation_timestamp": item["generation_timestamp"], "metrics": item["metrics"]}
    elif args.command == "trend": result = trend(load(args.history), args.period)
    elif args.command == "compare": result = compare(load(args.left), load(args.right))
    elif args.command == "history": result = history(load(args.history))
    elif args.command == "validate": result = {"valid": not validate_snapshot(load(args.snapshot))}
    else: result = explain(load(args.snapshot), args.metric)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
