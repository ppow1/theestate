"""Read-only CLI for WP-4226 campaign snapshots."""
import argparse, json
from estate.core.engineering_campaign_replay import compare, create_snapshot, history, load, replay, validate_snapshot

def main(argv=None):
    p=argparse.ArgumentParser(prog="engineering-campaign-replay"); sub=p.add_subparsers(dest="command",required=True)
    s=sub.add_parser("snapshot"); s.add_argument("sources"); s.add_argument("--generated-at",required=True)
    for name in ("replay","validate","explain"): q=sub.add_parser(name); q.add_argument("snapshot")
    q=sub.add_parser("compare"); q.add_argument("left"); q.add_argument("right")
    for name in ("history","list"): q=sub.add_parser(name); q.add_argument("snapshots",nargs="+")
    a=p.parse_args(argv)
    if a.command=="snapshot": out=create_snapshot(load(a.sources),generated_at=a.generated_at)
    elif a.command=="replay": out=replay(load(a.snapshot))
    elif a.command=="validate": validate_snapshot(load(a.snapshot)); out={"valid":True}
    elif a.command=="explain":
        x=load(a.snapshot); validate_snapshot(x); out={"snapshot_identifier":x["snapshot_identifier"],"provenance":x["provenance"],"schema_versions":x["schema_versions"],"read_only":True}
    elif a.command=="compare": out=compare(load(a.left),load(a.right))
    else: out=history([load(x) for x in a.snapshots])
    print(json.dumps(out,sort_keys=True,indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
