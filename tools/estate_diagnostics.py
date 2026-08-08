#!/usr/bin/env python3
"""Build, query, validate, and reconcile Estate living diagnostics."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from estate.diagnostics.living import DiagnosticsRepository, GENERATED, SOURCE, build, canonical_json, generate_manifest, reconcile


def validate(root: Path) -> dict:
    first = build(root, generated_at="2000-01-01T00:00:00Z")
    before = {p.name:p.read_bytes() for p in (root/GENERATED).iterdir()}
    second = build(root, generated_at="2000-01-01T00:00:00Z")
    after = {p.name:p.read_bytes() for p in (root/GENERATED).iterdir()}
    source=DiagnosticsRepository(root).source(); ids=[x["checkpoint_id"] for x in source["checkpoints"]]
    assert len(ids)==len(set(ids)) and all(len(x.split("."))==3 for x in ids)
    assert before==after, "build is not deterministic"
    assert len(source["checkpoints"])>=12
    assert all((root/p).exists() for x in source["checkpoints"] for p in x["source_dependencies"])
    assert "mermaid" in (root/GENERATED/"index.html").read_text(encoding="utf-8")
    return {"status":"PASS","checks":8,"checkpoint_count":len(ids),"deterministic":True,"first":first,"second":second}


def main() -> int:
    json_requested = "--json" in sys.argv
    if json_requested: sys.argv.remove("--json")
    parser=argparse.ArgumentParser(); parser.add_argument("--root",type=Path,default=ROOT)
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("build"); sub.add_parser("validate"); sub.add_parser("version-status"); sub.add_parser("freshness"); sub.add_parser("stale")
    s=sub.add_parser("search");s.add_argument("phrase")
    c=sub.add_parser("checkpoint");c.add_argument("checkpoint_id")
    f=sub.add_parser("failure");f.add_argument("code")
    w=sub.add_parser("workflow");w.add_argument("name")
    a=sub.add_parser("affected-by");a.add_argument("dependencies",nargs="+")
    r=sub.add_parser("reconcile");r.add_argument("--accepted-manifest",type=Path);r.add_argument("--impact-packet",type=Path,action="append",default=[]);r.add_argument("--incremental",action="store_true")
    args=parser.parse_args(); root=args.root.resolve(); repo=DiagnosticsRepository(root)
    if args.command=="build": result=build(root)
    elif args.command=="validate": result=validate(root)
    elif args.command=="version-status":
        m=generate_manifest(root); result={k:m[k] for k in ("repository","repository_revision","branch","worktree_identity","dirty_state","generated_at","components")}
    elif args.command=="freshness": result=repo.generated("freshness-report.json")
    elif args.command=="search": result=repo.search(args.phrase)
    elif args.command=="checkpoint": result=repo.checkpoint(args.checkpoint_id)
    elif args.command=="failure": result=[x for x in repo.generated("search-index.json")["entries"] if args.code.upper() in x["failure_codes"]]
    elif args.command=="workflow": result=[x for x in repo.generated("search-index.json")["entries"] if args.name.lower() in x["workflow"].lower()]
    elif args.command=="stale": result=[x for x in repo.generated("search-index.json")["entries"] if x["status"] in {"REVALIDATION_REQUIRED","STALE","UNKNOWN"}]
    elif args.command=="affected-by": result=repo.affected(args.dependencies)
    else: result=reconcile(root,args.accepted_manifest,args.impact_packet,"incremental" if args.incremental else "full")
    if json_requested or not isinstance(result,list): print(canonical_json(result),end="")
    else:
        for item in result: print(f"{item['checkpoint_id']} [{item['status']}] {item['title']}")
    return 0
if __name__=="__main__": raise SystemExit(main())
