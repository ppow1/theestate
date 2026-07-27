"""Read-only WP-4227 confidence diagnostics."""
import argparse
import json
from pathlib import Path
from estate.core.engineering_recommendation_confidence import assess, compare, explain, history, validate_report

def _load(path):
    with Path(path).open(encoding="utf-8") as stream: return json.load(stream)

def main(argv=None):
    parser=argparse.ArgumentParser(prog="engineering-recommendation-confidence")
    sub=parser.add_subparsers(dest="command",required=True)
    for name in ("confidence","evidence"):
        p=sub.add_parser(name); p.add_argument("sources"); p.add_argument("--assessed-at",required=True)
    p=sub.add_parser("explain"); p.add_argument("report"); p.add_argument("recommendation_id")
    p=sub.add_parser("compare"); p.add_argument("left"); p.add_argument("right")
    p=sub.add_parser("validate"); p.add_argument("report")
    p=sub.add_parser("history"); p.add_argument("reports",nargs="+")
    args=parser.parse_args(argv)
    if args.command in ("confidence","evidence"):
        report=assess(_load(args.sources),assessed_at=args.assessed_at)
        out=report if args.command=="confidence" else {"read_only":True,"evidence":[x["provenance_bundle"] for x in report["assessments"]]}
    elif args.command=="explain": out=explain(_load(args.report),args.recommendation_id)
    elif args.command=="compare": out=compare(_load(args.left),_load(args.right))
    elif args.command=="validate": validate_report(_load(args.report)); out={"valid":True,"read_only":True}
    else: out=history([_load(path) for path in args.reports])
    print(json.dumps(out,sort_keys=True,indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
