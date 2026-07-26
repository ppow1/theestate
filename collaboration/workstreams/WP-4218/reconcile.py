#!/usr/bin/env python3
"""Read-only diagnostic entry point; writes only beneath an explicit output root."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from reconciler.engine import ReconciliationError, canonical, discover, reconcile, render_report, validate_queue

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="WP-4218 staged advisory reconciler")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("generate"); run.add_argument("--source", required=True); run.add_argument("--output", required=True); run.add_argument("--revision", required=True); run.add_argument("--timestamp", default="1970-01-01T00:00:00Z")
    val = sub.add_parser("validate"); val.add_argument("queue")
    cmp = sub.add_parser("compare"); cmp.add_argument("left"); cmp.add_argument("right")
    exp = sub.add_parser("explain"); exp.add_argument("queue"); exp.add_argument("--item")
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            source, output = Path(args.source).resolve(), Path(args.output).resolve()
            if output == source or source in output.parents: raise ReconciliationError("output must not be within the authoritative source root")
            records = discover(source); queue = reconcile(records, args.revision, args.timestamp)
            output.mkdir(parents=True, exist_ok=True)
            (output / "engineering_queue_v1.json").write_bytes(canonical(queue)); (output / "reconciliation_summary.md").write_text(render_report(queue), encoding="utf-8")
            print(json.dumps({"records": len(records), "generation_identifier": queue["generation_identifier"], "output": str(output)}, sort_keys=True)); return 0
        queue = json.loads(Path(args.queue if args.command != "compare" else args.left).read_text()); validate_queue(queue)
        if args.command == "validate": print("valid"); return 0
        if args.command == "compare":
            other = json.loads(Path(args.right).read_text()); validate_queue(other)
            same = queue["deterministic_content_hash"] == other["deterministic_content_hash"]; print("equivalent" if same else "different"); return 0 if same else 1
        rows = [r for r in queue["rows"] if not args.item or r["item_identifier"] == args.item.upper()]
        print(json.dumps([{"item": r["item_identifier"], "classification": r["reconciliation_classification"], "readiness": r["readiness_classification"], "diagnostics": r["diagnostics"], "blockers": r["blockers"], "provenance": r["provenance"]} for r in rows], indent=2, sort_keys=True)); return 0
    except (OSError, json.JSONDecodeError, ReconciliationError) as exc:
        print(f"error: {exc}", file=sys.stderr); return 2
if __name__ == "__main__": raise SystemExit(main())
