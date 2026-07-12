"""Production-readiness validation reports for work-package delivery artifacts."""
from __future__ import annotations

import json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.work_package_validation import VALIDATION_RECIPES, get_validation_recipe

REQ = ["work_package_id","codex_status","completed_at","branch","summary","files_changed","tests_run","known_limitations","ready_for_ca_review"]


def _root(root: str|Path|None=None)->Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())

def _now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _git(root:Path,*args:str)->str|None:
    try: return subprocess.run(["git",*args],cwd=root,text=True,capture_output=True,check=False).stdout.strip() or None
    except OSError: return None

def _read_json(path:Path)->Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e: return {"_parse_error": str(e)}

def _wp_from_name(name:str)->str|None:
    m=re.search(r"WP-\d{4,}", name.upper()); return m.group(0) if m else None

def find_completion_artifact(root:Path, wp:str)->Path|None:
    d=root/"collaboration/work_packages/completions"
    exact=d/f"{wp}_codex_done.json"
    if exact.exists(): return exact
    matches=sorted(d.glob(f"{wp}*.json")) if d.exists() else []
    return matches[0] if matches else None

def validate_receipt(work_package_id:str, root: str|Path|None=None)->dict[str,Any]:
    base=_root(root); wp=work_package_id.upper(); path=find_completion_artifact(base,wp)
    gaps=[]; findings=[]; blockers=[]; data={}
    if not path:
        return {"work_package_id":wp,"receipt_status":"missing","completion_artifact_path":None,"receipt_gaps":["completion_artifact"],"blocking_reasons":["Completion artifact is missing."],"non_blocking_findings":[],"pr_metadata_status":"unavailable"}
    rel=str(path.relative_to(base)).replace('\\','/')
    data=_read_json(path)
    if data.get("_parse_error"):
        return {"work_package_id":wp,"receipt_status":"incomplete","completion_artifact_path":rel,"receipt_gaps":["parseable_json"],"blocking_reasons":[f"Completion artifact is not parseable JSON: {data['_parse_error']}"],"non_blocking_findings":[],"pr_metadata_status":"unavailable"}
    required=list(REQ)
    if not (data.get("pull_request_url") or data.get("pull_request_not_applicable_reason") or data.get("pr_not_applicable_reason")):
        gaps.append("pull_request_url_or_not_applicable_reason")
    if not (data.get("merge_authority") or data.get("merge_authority_equivalent") or data.get("delivery_authority")):
        gaps.append("merge_authority_or_equivalent")
    for k in required:
        v=data.get(k)
        if v is None or v=="" or (v==[] and k != "known_limitations"): gaps.append(k)
    if data.get("work_package_id") and str(data.get("work_package_id")).upper()!=wp: gaps.append("work_package_id_matches_filename")
    if data.get("codex_status") and str(data.get("codex_status")).lower() not in {"done","complete","completed"}: gaps.append("codex_status_done")
    if data.get("ready_for_ca_review") is not True:
        reason=data.get("ready_for_ca_review_reason") or data.get("not_ready_reason")
        (findings if reason else blockers).append("ready_for_ca_review is not true" + (f": {reason}" if reason else "."))
    limitations=data.get("known_limitations") or []
    if isinstance(limitations,str): limitations=[limitations]
    for lim in limitations:
        if any(word in str(lim).lower() for word in ["blocker","blocking","not production ready","critical"]):
            blockers.append(f"Blocking known limitation: {lim}")
    pr_status="available" if data.get("pull_request_url") else "unavailable"
    if pr_status=="available": findings.append("Live PR metadata was not checked by the local-first validator.")
    status="complete" if not gaps else "incomplete"
    if gaps: blockers.append("Completion artifact is missing required metadata: "+", ".join(gaps))
    return {"work_package_id":wp,"receipt_status":status,"completion_artifact_path":rel,"receipt_gaps":gaps,"blocking_reasons":blockers,"non_blocking_findings":findings,"pr_metadata_status":pr_status,"branch":data.get("branch"),"pull_request_url":data.get("pull_request_url")}

def calculate_production_readiness(execution_status:str, receipt:dict[str,Any], coverage_status:str="covered", findings:list[str]|None=None)->dict[str,Any]:
    blockers=list(receipt.get("blocking_reasons") or [])
    non=list(receipt.get("non_blocking_findings") or []) + list(findings or [])
    if execution_status in {"failed","no_recipe"}: blockers.append(f"Execution status blocks readiness: {execution_status}.")
    if receipt.get("receipt_status") in {"missing","incomplete"}: pass
    ready=not blockers and execution_status in {"passed","passed_with_findings"} and receipt.get("receipt_status")=="complete"
    return {"production_ready":ready,"blocking_reasons":blockers,"non_blocking_findings":non,"required_followups":blockers.copy(),"execution_status":execution_status,"receipt_status":receipt.get("receipt_status"),"coverage_status":coverage_status}

def _latest_report(root:Path, wp:str)->dict[str,Any]:
    p=root/"runtime/validation/work_packages"/f"{wp}_validation.json"
    if not p.exists(): return {"path":None,"status":"missing"}
    data=_read_json(p); return {"path":str(p.relative_to(root)).replace('\\','/'),"status":data.get("validation_status","unknown")}

def _is_invalid_placeholder_residue(root: Path, wp: str) -> bool:
    """Return true for validation-only placeholder artifacts outside production inputs."""
    if wp != "WP-9999":
        return False
    has_pending = any((root / "collaboration/work_packages/pending").glob(f"{wp}*.md"))
    has_completion = find_completion_artifact(root, wp) is not None
    if has_pending or has_completion:
        return False
    report = root / "runtime/validation/work_packages" / f"{wp}_validation.json"
    if not report.exists():
        return True
    data = _read_json(report)
    return data.get("validation_status") == "no_recipe"


def _work_package_lifecycle_paths(root: Path, wp: str) -> dict[str, str | None]:
    paths = {}
    for state, folder in [("completion", "collaboration/work_packages/completions"), ("pending", "collaboration/work_packages/pending"), ("active", "collaboration/work_packages/active"), ("blocked", "collaboration/work_packages/blocked"), ("deferred", "collaboration/work_packages/deferred")]:
        d = root / folder
        match = next((str(p.relative_to(root)).replace("\\", "/") for p in sorted(d.glob(f"{wp}*")) if p.is_file()), None) if d.exists() else None
        paths[state] = match
    return paths

def _work_package_lifecycle_state(paths: dict[str, str | None], receipt: dict[str, Any]) -> str:
    if receipt.get("receipt_status") == "complete" or paths.get("completion"):
        return "completed_receipt_backed"
    if paths.get("active"):
        return "active"
    if paths.get("blocked"):
        return "blocked"
    if paths.get("deferred"):
        return "deferred"
    if paths.get("pending"):
        return "pending_authored_not_completed"
    return "unknown_no_queue_artifact"

def _discover_wps(root:Path)->set[str]:
    ids=set(VALIDATION_RECIPES)
    for folder in ["collaboration/work_packages/completions","collaboration/work_packages/pending","operations/validation/reports","runtime/validation/work_packages"]:
        d=root/folder
        if d.exists():
            for p in d.glob("*"):
                wp=_wp_from_name(p.name)
                if wp and not _is_invalid_placeholder_residue(root, wp):
                    ids.add(wp)
    return ids

def generate_validation_coverage_manifest(root: str|Path|None=None, write:bool=True)->dict[str,Any]:
    base=_root(root); entries=[]
    for wp in sorted(_discover_wps(base)):
        receipt=validate_receipt(wp,base); latest=_latest_report(base,wp); recipe="registered" if get_validation_recipe(wp) else "missing"
        exec_status=latest["status"] if latest["status"]!="missing" else ("no_recipe" if recipe=="missing" else "missing_report")
        prod=calculate_production_readiness(exec_status, receipt, "covered" if recipe=="registered" else "no_recipe")
        lifecycle_paths = _work_package_lifecycle_paths(base, wp)
        lifecycle_state = _work_package_lifecycle_state(lifecycle_paths, receipt)
        entries.append({"work_package_id":wp,"lifecycle_state":lifecycle_state,"pending_file_path":lifecycle_paths.get("pending"),"completion_artifact_path":receipt.get("completion_artifact_path") or lifecycle_paths.get("completion"),"receipt_status":receipt.get("receipt_status"),"recipe_status":recipe,"latest_validation_report_path":latest["path"],"latest_validation_status":latest["status"],"production_readiness_status":"ready" if prod["production_ready"] else "blocked","blockers":prod["blocking_reasons"],"required_followups":prod["required_followups"]})
    payload={"generated_at":_now(),"work_packages":entries,"summary":{"total_work_packages_scanned":len(entries),"total_production_ready":sum(e["production_readiness_status"]=="ready" for e in entries),"total_blocked":sum(e["production_readiness_status"]!="ready" for e in entries),"total_missing_recipes":sum(e["recipe_status"]=="missing" for e in entries),"total_missing_receipts":sum(e["receipt_status"]=="missing" for e in entries),"total_incomplete_receipts":sum(e["receipt_status"]=="incomplete" for e in entries)}}
    if write:
        (base/"runtime/validation").mkdir(parents=True,exist_ok=True); (base/"operations/validation").mkdir(parents=True,exist_ok=True)
        (base/"runtime/validation/validation_coverage_manifest.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        (base/"operations/validation/validation_coverage_manifest.md").write_text(format_coverage_manifest_markdown(payload)+"\n",encoding="utf-8")
    return payload

def generate_production_readiness_report(root: str|Path|None=None, write:bool=True)->dict[str,Any]:
    base=_root(root); manifest=generate_validation_coverage_manifest(base,write=write); s=manifest["summary"]
    recent=sorted((base/"runtime/validation/work_packages").glob("WP-*_validation.json"), key=lambda p:p.stat().st_mtime, reverse=True)[:10] if (base/"runtime/validation/work_packages").exists() else []
    blocking=[e for e in manifest["work_packages"] if e["production_readiness_status"]!="ready"]
    ready=[e for e in manifest["work_packages"] if e["production_readiness_status"]=="ready"]
    payload={"generated_at":_now(),"git_branch":_git(base,"branch","--show-current"),"git_commit":_git(base,"rev-parse","HEAD"),**s,"open_validation_observations":_open_observations(base),"recent_validation_reports":[str(p.relative_to(base)).replace('\\','/') for p in recent],"recommended_next_action":"Resolve blocking receipt, recipe, and validation gaps before CA production-readiness acceptance." if blocking else "Ready for Chief Architect production-readiness acceptance review.","blocking_work_packages":blocking,"ready_for_chief_architect_production_readiness_acceptance":ready,"coverage_manifest_paths":{"markdown":"operations/validation/validation_coverage_manifest.md","json":"runtime/validation/validation_coverage_manifest.json"}}
    if write:
        (base/"runtime/validation/production_readiness_report.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        (base/"operations/validation/production_readiness_report.md").write_text(format_production_readiness_markdown(payload)+"\n",encoding="utf-8")
    return payload

def _open_observations(base:Path)->list[Any]:
    p=base/"validation/observations/validation_observations.jsonl"
    if not p.exists(): return []
    out=[]
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            obj=json.loads(line); 
            if obj.get("status","open")=="open": out.append(obj)
        except Exception: pass
    return out

def format_coverage_manifest_markdown(payload):
    lines=["# Validation Coverage Manifest","",f"Generated at: {payload['generated_at']}","","## Summary"]
    for k,v in payload["summary"].items(): lines.append(f"- {k}: {v}")
    lines += ["","## Work Packages"]
    for e in payload["work_packages"]: lines.append(f"- {e['work_package_id']} — receipt: {e['receipt_status']}; recipe: {e['recipe_status']}; validation: {e['latest_validation_status']}; lifecycle: {e.get('lifecycle_state', 'unknown')}; production: {e['production_readiness_status']}; blockers: {len(e['blockers'])}")
    return "\n".join(lines)

def format_production_readiness_markdown(payload):
    lines=["# Production Readiness Report","",f"- generated_at: {payload['generated_at']}",f"- git branch: {payload.get('git_branch') or 'unknown'}",f"- git commit: {payload.get('git_commit') or 'unknown'}","","## Totals"]
    for k in ["total_work_packages_scanned","total_production_ready","total_blocked","total_missing_recipes","total_missing_receipts","total_incomplete_receipts"]: lines.append(f"- {k}: {payload[k]}")
    lines += ["","## Recommended Next Action",payload["recommended_next_action"],"","## Blocking Work Packages"]
    lines += [f"- {e['work_package_id']}: {'; '.join(e['blockers'][:3])}" for e in payload["blocking_work_packages"][:100]] or ["- None."]
    lines += ["","## Ready for Chief Architect Production-Readiness Acceptance"]
    lines += [f"- {e['work_package_id']}" for e in payload["ready_for_chief_architect_production_readiness_acceptance"][:100]] or ["- None."]
    lines += ["","## Recent Validation Reports"] + [f"- `{p}`" for p in payload["recent_validation_reports"]]
    return "\n".join(lines)
