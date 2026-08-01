"""Bounded read-only Repository Health Skill implementation."""
from __future__ import annotations
import hashlib, json, os, re, subprocess, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .estate_skills import SkillError, validate_receipt

def _now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def _git(root: Path, *args: str) -> str:
    p=subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    if p.returncode: raise SkillError(f"git read failed: {' '.join(args)}")
    return p.stdout.strip()
def _lines(text): return [x for x in text.splitlines() if x.strip()]
def _redact_remote(value): return re.sub(r"(https?://)([^/@]+):([^/@]+)@", r"\1<redacted>@", value)
def _ref_exists(root: Path, ref: str) -> bool:
    p=subprocess.run(["git","-C",str(root),"show-ref","--verify","--quiet",ref],capture_output=True)
    return p.returncode == 0
def _refs(root: Path):
    rows=[]
    for line in _lines(_git(root,"for-each-ref","--format=%(refname)|%(objectname)|%(upstream)|%(upstream:track)","refs/heads")):
        ref, head, upstream, track=(line.split("|",3)+[""]*4)[:4]; rows.append({"ref":ref,"head":head,"upstream":upstream or None,"ahead_behind":track or None,"upstream_missing":bool(upstream and not _ref_exists(root,upstream))})
    return rows
def _worktrees(root: Path):
    items=[]; current=None
    for line in _lines(_git(root,"worktree","list","--porcelain")):
        if line.startswith("worktree "):
            if current: items.append(current)
            current={"path":line[9:],"head":None,"branch":None,"detached":False}
        elif current and line.startswith("HEAD "): current["head"]=line[5:]
        elif current and line.startswith("branch "): current["branch"]=line[7:]
        elif current and line=="detached": current["detached"]=True
    if current: items.append(current)
    return items
def _status(root: Path):
    entries=_lines(_git(root,"status","--porcelain=v1","--untracked-files=all")); tracked=sum(1 for x in entries if not x.startswith("??")); untracked=sum(1 for x in entries if x.startswith("??"));
    ignored=_lines(_git(root,"status","--short","--ignored","--untracked-files=all")); ignored_count=sum(1 for x in ignored if x.startswith("!!"))
    return {"clean":not entries,"tracked_modified":tracked,"untracked":untracked,"ignored":ignored_count}
def _noncanonical_refs(root: Path, configured: list[str]):
    roots=[Path(x) for x in configured if Path(x).exists()]; hits=[]; count=0
    needles=["A:\\theestate", "A:/theestate"]
    for base in roots:
        for current, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".pytest_cache", "runtime"}]
            for name in files:
                if count>=5000: break
                p=Path(current)/name
                try: size=p.stat().st_size
                except OSError: continue
                if size>2_000_000: continue
                if p.suffix.lower() not in {".py",".ps1",".cmd",".bat",".json",".yaml",".yml",".md",".txt",".ini",".toml"}: continue
                try: text=p.read_text(encoding="utf-8", errors="ignore")
                except OSError: continue
                count+=1
                for needle in needles:
                    if needle.lower() in text.lower() and "A:\\theestate-wp4233" not in text and "A:/theestate-wp4233" not in text:
                        hits.append({"path":str(p),"matched_reference":needle,"content_excluded":True}); break
            if count>=5000: break
        if count>=5000: break
    return {"files_scanned":count,"hits":hits[:200],"truncated":count>=5000}
def inspect_repository(root: str|Path, *, approved_worktrees=None, scan_roots=None):
    root=Path(root).resolve(); approved_worktrees=approved_worktrees or [str(root)]; scan_roots=scan_roots or [str(root/"scripts"),str(root/"config"),str(root/"docs")]
    remote=_git(root,"remote","get-url","origin") if _git(root,"remote") else None
    stashes=[{"ref":line.split(" ",1)[0],"subject":line.split(" ",1)[1] if " " in line else ""} for line in _lines(_git(root,"stash","list","--format=%gd %s"))]
    branches=_refs(root); unique=[]
    for b in branches:
        try:
            n=int(_git(root,"rev-list",b["ref"],"--not","--remotes","--count") or 0)
            if n: unique.append({"ref":b["ref"],"unpublished_commit_count":n,"head":b["head"]})
        except SkillError: pass
    return {"schema_version":"repository_health.report.v1","generated_at":_now(),"canonical_repository":{"root":str(root),"git_dir":_git(root,"rev-parse","--git-dir"),"common_dir":_git(root,"rev-parse","--path-format=absolute","--git-common-dir"),"head":_git(root,"rev-parse","HEAD"),"remote_origin":_redact_remote(remote) if remote else None},"approved_worktrees":approved_worktrees,"worktrees":_worktrees(root),"branch_refs":branches,"local_branches_with_unique_commits":unique,"status":_status(root),"stashes":stashes,"noncanonical_startup_runtime_references":_noncanonical_refs(root,scan_roots),"risks":["Unpublished local commits require preservation before cleanup." if unique else "No local branch commits are currently ahead of all remotes.","Stashes are inventory-only and must not be changed.","Path references are bounded scans; inspect listed files before migration."],"institutional_acceptance":"not_granted"}
def execute(root: str|Path, *, output_dir: str|Path, invocation_id: str|None=None, approved_worktrees=None, scan_roots=None):
    root=Path(root).resolve(); out=Path(output_dir); out=out if out.is_absolute() else root/out; out.mkdir(parents=True, exist_ok=True)
    invocation_id=invocation_id or f"repository-health-{uuid.uuid4().hex}"
    report=inspect_repository(root,approved_worktrees=approved_worktrees,scan_roots=scan_roots)
    report["invocation_id"]=invocation_id; report["skill_id"]="repository-health"; report["skill_version"]="1.0.0"
    report_path=out/f"{invocation_id}.report.json"; receipt_path=out/f"{invocation_id}.receipt.json"
    if report_path.exists() or receipt_path.exists(): raise SkillError("replay conflict: invocation artifacts already exist")
    report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    receipt={"schema_version":"estate.skill.receipt.v1","receipt_id":f"receipt-{invocation_id}","invocation_id":invocation_id,"skill_id":"repository-health","status":"completed","artifacts":[str(report_path)],"validation":{"status":"valid","report_sha256":hashlib.sha256(report_path.read_bytes()).hexdigest()},"reconciliation":{"status":"reconciled","scope":"bounded_read_only_repository_inspection"},"terminal_result":{"status":"completed","summary":"Repository Health report produced; no repository mutation performed."},"institutional_acceptance":"not_granted"}
    validate_receipt(receipt); receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return report, receipt
