#!/usr/bin/env python3
"""Provider-neutral command line interface for Living Diagnostics."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from estate.diagnostics.impact import PacketError, baseline, create_packet, local_ai_delta, reconcile

def write(value, destination):
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if destination: Path(destination).write_text(rendered)
    else: print(rendered, end="")

def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    impact = sub.add_parser("impact").add_subparsers(dest="action", required=True)
    create = impact.add_parser("create"); create.add_argument("--input", required=True); create.add_argument("--output", required=True)
    base = sub.add_parser("baseline"); base.add_argument("--paths", nargs="+", required=True); base.add_argument("--output", required=True)
    rec = sub.add_parser("reconcile"); rec.add_argument("--baseline", required=True); rec.add_argument("--packets", nargs="*", default=[]); rec.add_argument("--output", required=True)
    cand = sub.add_parser("candidates"); cand.add_argument("--reconciliation", required=True)
    delta = sub.add_parser("local-ai-delta"); delta.add_argument("--reconciliation", required=True); delta.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        if args.command == "impact": write(create_packet(ROOT, json.loads(Path(args.input).read_text())), args.output)
        elif args.command == "baseline": write(baseline(ROOT, args.paths), args.output)
        elif args.command == "reconcile": write(reconcile(ROOT, Path(args.baseline), [Path(p) for p in args.packets]), args.output)
        elif args.command == "candidates": write(json.loads(Path(args.reconciliation).read_text())["candidates"], None)
        else: write(local_ai_delta(ROOT, json.loads(Path(args.reconciliation).read_text())), args.output)
    except (OSError, json.JSONDecodeError, PacketError, KeyError) as exc:
        print(f"diagnostic metadata rejected: {exc}", file=sys.stderr); return 2
    return 0
if __name__ == "__main__": raise SystemExit(main())
