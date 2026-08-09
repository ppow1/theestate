#!/usr/bin/env python3
"""Build, query, validate, and reconcile Estate living diagnostics."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from estate.diagnostics.living import DiagnosticsRepository, GENERATED, SOURCE, advance_accepted_baseline, build, canonical_json, generate_manifest, reconcile
from estate.diagnostics.impact import create_packet, local_ai_delta, preserve_candidate, query_candidates
from estate.diagnostics.knowledge import ingest_candidate, query_knowledge, validate_knowledge
from estate.diagnostics.comprehension import build_model, comprehension_packet, query_model


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
    b=sub.add_parser("accept-baseline");b.add_argument("--actor",required=True);b.add_argument("--reason",required=True);b.add_argument("--expected-revision")
    impact=sub.add_parser("impact"); impact_sub=impact.add_subparsers(dest="impact_command",required=True)
    create=impact_sub.add_parser("create");create.add_argument("--request",type=Path,required=True);create.add_argument("--output",type=Path,required=True)
    candidates=sub.add_parser("candidates");candidates.add_argument("phrase",nargs="?")
    sub.add_parser("local-ai-delta")
    knowledge=sub.add_parser("knowledge"); knowledge_sub=knowledge.add_subparsers(dest="knowledge_command",required=True)
    kv=knowledge_sub.add_parser("validate"); kv.add_argument("path",type=Path)
    ki=knowledge_sub.add_parser("ingest"); ki.add_argument("path",type=Path)
    kq=knowledge_sub.add_parser("query"); kq.add_argument("phrase",nargs="?")
    comprehension=sub.add_parser("comprehension"); comprehension_sub=comprehension.add_subparsers(dest="comprehension_command",required=True)
    cb=comprehension_sub.add_parser("build"); cb.add_argument("--output",type=Path,required=True)
    cc=comprehension_sub.add_parser("component"); cc.add_argument("component_id")
    cw=comprehension_sub.add_parser("workflow"); cw.add_argument("workflow_id")
    cq=comprehension_sub.add_parser("query"); cq.add_argument("phrase")
    cp=comprehension_sub.add_parser("packet"); cp.add_argument("scope"); cp.add_argument("--output",type=Path,required=True)
    cd=comprehension_sub.add_parser("diagram"); cd.add_argument("scope",nargs="?",default="components")
    cs=comprehension_sub.add_parser("stale")
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
    elif args.command=="accept-baseline": result=advance_accepted_baseline(root,actor=args.actor,reason=args.reason,expected_revision=args.expected_revision)
    elif args.command=="impact":
        request=json.loads(args.request.read_text(encoding="utf-8")); result=create_packet(root,request)
        output=args.output if args.output.is_absolute() else root/args.output; output.parent.mkdir(parents=True,exist_ok=True); output.write_text(canonical_json(result),encoding="utf-8")
        result={"status":"ACCEPTED","packet":str(output),"change_id":result["change_id"]}
    elif args.command=="candidates": result=query_candidates(root,args.phrase)
    elif args.command=="knowledge":
        path = args.path if getattr(args, "path", None) and args.path.is_absolute() else (root / args.path if getattr(args, "path", None) else None)
        if args.knowledge_command == "validate":
            value = json.loads(path.read_text(encoding="utf-8")); value = value.get("knowledge", value) if isinstance(value, dict) else value
            errors = validate_knowledge(value); result={"valid":not errors,"errors":errors}
        elif args.knowledge_command == "ingest":
            value = json.loads(path.read_text(encoding="utf-8")); value = value.get("knowledge", value) if isinstance(value, dict) else value
            destination = ingest_candidate(root, value); result={"status":"CANDIDATE_PRESERVED","path":destination.relative_to(root).as_posix(),"canonical_promotion":False}
        else: result=query_knowledge(root,args.phrase)
    elif args.command=="comprehension":
        output = args.output if getattr(args, "output", None) and args.output.is_absolute() else (root / args.output if getattr(args, "output", None) else None)
        model = build_model(root, output if args.comprehension_command == "build" else None)
        if args.comprehension_command == "build":
            try: output_name = output.relative_to(root).as_posix()
            except ValueError: output_name = str(output)
            result = {"status":"BUILT", "output":output_name, "model_id":model["model_id"], "source_revision":model["provenance"]["repository_revision"], "component_count":len(model["components"]), "workflow_count":len(model["workflows"]), "checkpoint_count":len(model["checkpoints"]), "failure_seam_count":len(model["failure_seams"]), "staleness":model["staleness"]}
        elif args.comprehension_command == "component":
            result = next((x for x in model["components"] if x["component_id"] == args.component_id), None)
        elif args.comprehension_command == "workflow":
            result = next((x for x in model["workflows"] if x["workflow_id"] == args.workflow_id), None)
        elif args.comprehension_command == "query":
            result = query_model(model, args.phrase)
        elif args.comprehension_command == "diagram":
            from estate.diagnostics.comprehension import render_mermaid
            result = {"scope":args.scope, "source_revision":model["provenance"]["repository_revision"], "mermaid":render_mermaid(model, args.scope)}
        elif args.comprehension_command == "stale":
            result = model["staleness"]
        else:
            packet = comprehension_packet(root, model, args.scope)
            output.parent.mkdir(parents=True, exist_ok=True); output.write_text(canonical_json(packet), encoding="utf-8")
            try: output_name = output.relative_to(root).as_posix()
            except ValueError: output_name = str(output)
            result = {"status":"PACKET_BUILT", "output":output_name, "scope":args.scope, "source_revision":packet["source_revision"], "canonical_mutation":False}
    elif args.command=="local-ai-delta": result=local_ai_delta(root)
    else: result=reconcile(root,args.accepted_manifest,args.impact_packet,"incremental" if args.incremental else "full")
    if json_requested or not isinstance(result,list): print(canonical_json(result),end="")
    else:
        for item in result: print(f"{item['checkpoint_id']} [{item['status']}] {item['title']}")
    return 2 if isinstance(result,dict) and result.get("reconciliation_outcome") in {"ACCEPTED_BASELINE_MISSING","ACCEPTED_BASELINE_INVALID"} else 0
if __name__=="__main__": raise SystemExit(main())
