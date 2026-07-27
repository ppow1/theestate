#!/usr/bin/env python3
"""Offline read-only WP-4221 diagnostic command."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from dashboard import DashboardError, build_snapshot, operator_summary, validate_snapshot
from dashboard.projection import canonical

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description="WP-4221 staged dashboard projection")
    sub=parser.add_subparsers(dest="command",required=True)
    gen=sub.add_parser("generate"); gen.add_argument("--queue",required=True); gen.add_argument("--output",required=True); gen.add_argument("--generated-at",default="1970-01-01T00:00:00Z"); gen.add_argument("--as-of")
    val=sub.add_parser("validate"); val.add_argument("snapshot")
    cmp=sub.add_parser("compare"); cmp.add_argument("left"); cmp.add_argument("right")
    exp=sub.add_parser("explain"); exp.add_argument("snapshot"); exp.add_argument("--panel")
    args=parser.parse_args(argv)
    try:
        if args.command == "generate":
            source=Path(args.queue).resolve(); output=Path(args.output).resolve()
            if output == source or source in output.parents or output in source.parents: raise DashboardError("output and source paths must not overlap")
            queue=json.loads(source.read_text(encoding="utf-8")); snap=build_snapshot(queue,args.generated_at,args.as_of)
            output.mkdir(parents=True,exist_ok=False)
            (output/"dashboard_snapshot_v1.json").write_bytes(canonical(snap))
            panels=output/"panels"; panels.mkdir()
            for name,panel in snap["panels"].items(): (panels/f"{name}.json").write_bytes(canonical(panel))
            (output/"operator_summary.md").write_text(operator_summary(snap),encoding="utf-8")
            print(json.dumps({"snapshot_identifier":snap["snapshot_identifier"],"degradation_status":snap["degradation_status"],"output":str(output)},sort_keys=True)); return 0
        left=json.loads(Path(args.snapshot if args.command != "compare" else args.left).read_text()); validate_snapshot(left)
        if args.command == "validate": print("valid"); return 0
        if args.command == "compare":
            right=json.loads(Path(args.right).read_text()); validate_snapshot(right); same=left["deterministic_content_hash"]==right["deterministic_content_hash"]; print("equivalent" if same else "different"); return 0 if same else 1
        selected={args.panel:left["panels"][args.panel]} if args.panel else {k:v for k,v in left["panels"].items() if v["degradation"] != "none"}
        print(json.dumps(selected,indent=2,sort_keys=True)); return 0
    except (OSError,json.JSONDecodeError,KeyError,DashboardError) as exc:
        print(f"error: {exc}",file=sys.stderr); return 2
if __name__ == "__main__": raise SystemExit(main())
