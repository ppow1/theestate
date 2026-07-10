"""Local merge/promotion and completion-receipt discovery for post-merge audits."""
from __future__ import annotations

import json, re, subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.operational_target_resolution import OperationalTargetResolver
from estate.core.merge_discovery_consolidation import MergeDiscoveryConsolidator
from estate.core.paths import ESTATE_ROOT

BASE = Path("runtime/merge_discovery")
TARGETS = BASE / "targets"
DISCOVERIES = BASE / "discoveries"
CANDIDATES = BASE / "candidates"
STATUS = BASE / "status"
WP_RE = re.compile(r"WP-\d{4}")
FINAL_VERDICTS = {"accepted", "accepted_with_notes", "ring2_required", "needs_repair", "blocked", "not_merged", "workspace_failed", "validation_failed"}

def utc_now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
def _root(root=None): return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
def _write(p:Path, d:Any): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(d, indent=2, sort_keys=True)+"\n", encoding="utf-8")
def _read(p:Path): return json.loads(p.read_text(encoding="utf-8"))
def _rel(p:Path, root:Path):
    try: return str(p.relative_to(root)).replace('\\','/')
    except ValueError: return str(p).replace('\\','/')

def _git(repo:Path, *args:str) -> str:
    r=subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)
    if r.returncode: raise RuntimeError((r.stderr or r.stdout).strip())
    return r.stdout.strip()

def _git_ok(repo:Path, *args:str) -> tuple[str, str, int]:
    r=subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

@dataclass
class MergeDiscoveryRecord:
    discovery_id:str; target_id:str; source_kind:str; source_commit:str; source_reference:str
    work_package_id:str|None=None; completion_receipt_path:str|None=None; correlation_method:str|None=None
    state:str="discovered"; duplicate_of:str|None=None; audit_request_id:str|None=None; created_at:str=field(default_factory=utc_now_iso)
    warnings:list[str]=field(default_factory=list); errors:list[str]=field(default_factory=list); metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return asdict(self)

class MergeDiscovery:
    def __init__(self, root:Path|None=None):
        self.root=_root(root); self.targets=OperationalTargetRuntime(self.root); self.resolver=OperationalTargetResolver(self.root)
    def cursor_path(self, target_id): return self.root/TARGETS/target_id/"cursor.json"
    def records_dir(self): return self.root/DISCOVERIES
    def requests_dir(self): return self.root/"runtime/post_merge_audit/requests"
    def scan(self, target="estate-main", max_commits:int=100, replay:bool=False, backfill_mode:str="quarantine", max_candidates:int=20, max_requests_per_cycle:int=5, minimum_evidence_level:str="implementation") -> dict[str,Any]:
        res=self.resolver.resolve(target); target_id=res.canonical_target_id or target
        t=self.targets.get(target_id); repo=Path(t.local_path or self.root)
        remote=getattr(t,"remote",None) or "origin"
        branch=getattr(t,"base_branch",None) or "main"
        watched_ref=f"{remote}/{branch}"
        curp=self.cursor_path(target_id); cursor=_read(curp) if curp.exists() and not replay else {}
        remote_check_out, _, remote_check_rc = _git_ok(repo,"remote","get-url",remote)
        remote_available = remote_check_rc == 0
        fetch_out, fetch_err, fetch_rc = _git_ok(repo,"fetch","--quiet",remote) if remote_available else ("", "", 0)
        if fetch_rc != 0:
            failure={"target_id":target_id,"watched_remote_ref":watched_ref,"last_fetch_at":utc_now_iso(),"status":"fetch_failed","errors":[fetch_err or fetch_out or "git fetch failed"],"last_scanned_commit":cursor.get("last_scanned_commit")}
            _write(self.root/STATUS/"latest.json", {"target_id":target_id,"cursor":cursor,"records":[],"summary":{"merge_discovery_available":True,"watched_remote_ref":watched_ref,"last_fetch_at":failure["last_fetch_at"],"last_scanned_commit":cursor.get("last_scanned_commit"),"fetch_failed":True,"errors":failure["errors"]},"provider_execution_performed":False,"dispatch_execution_performed":False})
            _write(self.root/STATUS/"fetch_failure.json", failure)
            return {"target_id":target_id,"cursor":cursor,"records":[],"summary":{"merge_discovery_available":True,"watched_remote_ref":watched_ref,"last_fetch_at":failure["last_fetch_at"],"last_scanned_commit":cursor.get("last_scanned_commit"),"fetch_failed":True,"errors":failure["errors"]},"provider_execution_performed":False,"dispatch_execution_performed":False}
        last=cursor.get("last_scanned_commit")
        scan_ref = watched_ref if remote_available else branch
        revs=_git(repo,"rev-list",f"--max-count={max_commits}",scan_ref).splitlines()
        if last and last in revs: revs=revs[:revs.index(last)]
        revs=list(reversed(revs))
        metrics={"merge_commits_scanned":0,"work_packages_discovered":0,"discoveries_ambiguous":0,"discoveries_ignored":0,"audit_requests_created_from_merges":0,"duplicate_audit_requests_suppressed":0}
        records=[]
        for sha in revs:
            rec=self._discover_commit(repo, target_id, sha)
            if not rec: continue
            if rec.source_kind=="merge": metrics["merge_commits_scanned"]+=1
            if self._has_final_verdict(rec):
                rec.state="already_processed"; metrics["duplicate_audit_requests_suppressed"]+=1
            records.append(rec.to_dict())
            if rec.state in {"discovered","request_created","already_processed"}: metrics["work_packages_discovered"]+=1
            if rec.state=="ambiguous": metrics["discoveries_ambiguous"]+=1
            if rec.state=="ignored": metrics["discoveries_ignored"]+=1
            _write(self.records_dir()/f"{rec.discovery_id}.json", rec.to_dict())
            if rec.state in {"discovered","ambiguous","blocked","failed"}: _write(self.root/CANDIDATES/f"{rec.discovery_id}.json", rec.to_dict())
        head=_git(repo,"rev-parse",scan_ref) if repo.exists() else None
        cursor={"target_id":target_id,"base_branch":branch,"watched_remote_ref":watched_ref,"last_fetch_at":utc_now_iso(),"last_scanned_commit":head,"last_scanned_at":utc_now_iso(),"last_discovery_count":len(records),"last_request_count":metrics["audit_requests_created_from_merges"],"status":"ok","warnings":[],"errors":[]}
        _write(curp,cursor)
        consolidation=MergeDiscoveryConsolidator(self.root).consolidate(target_id, records=records, mode=backfill_mode, max_candidates=max_candidates, max_requests_per_cycle=max_requests_per_cycle, minimum_evidence_level=minimum_evidence_level)
        cs=consolidation.get("summary", {})
        metrics["audit_requests_created_from_merges"]=cs.get("admitted_requests",0)
        metrics["duplicate_audit_requests_suppressed"]=cs.get("requests_suppressed_by_grouping",0)
        summary={"merge_discovery_available":True, **metrics, **cs, "last_merge_scan_at":cursor["last_scanned_at"], "last_fetch_at":cursor["last_fetch_at"], "watched_remote_ref":watched_ref, "last_scanned_commit":head, "pending_discovery_candidates":self._candidate_count(), "ambiguous_discoveries":self._ambiguous_count(), "latest_discovered_work_package":next((r.get("work_package_id") for r in reversed(records) if r.get("work_package_id")), None), "latest_created_audit_request":next((r.get("audit_request_id") for r in reversed(consolidation.get("admitted_requests", [])) if r.get("audit_request_id")), None), "duplicate_requests_suppressed":metrics["duplicate_audit_requests_suppressed"]}
        payload={"target_id":target_id,"cursor":cursor,"records":records,"consolidation":consolidation,"summary":summary,"provider_execution_performed":False,"dispatch_execution_performed":False}
        _write(self.root/STATUS/"latest.json", payload); _write(self.root/STATUS/"summary.json", summary)
        return payload
    def _discover_commit(self, repo, target_id, sha):
        parents=_git(repo,"rev-list","--parents","-n","1",sha).split(); files=_git(repo,"diff-tree","--no-commit-id","--name-only","-r",sha).splitlines(); msg=_git(repo,"log","-n","1","--format=%B",sha)
        source_kind="merge" if len(parents)>2 else "promotion"
        receipt_paths=[f for f in files if f.startswith("collaboration/work_packages/completions/") and f.endswith(".json")]
        pending_only=bool(files) and all(f.startswith("collaboration/work_packages/pending/") for f in files)
        if pending_only:
            return None
        if source_kind!="merge" and not receipt_paths and not WP_RE.search(msg): return None
        evidence=[]; receipt_path=None; warnings=[]; metadata={"changed_paths":files}
        for rp in receipt_paths:
            p=repo/rp; receipt_path=rp
            try:
                d=json.loads(_git(repo,"show",f"{sha}:{rp}")); metadata["receipt"]={k:d.get(k) for k in ["work_package_id","pull_request_url","files_changed"]}
                if d.get("work_package_id"): evidence.append((d["work_package_id"],"receipt_work_package_id"))
                else: warnings.append("completion_receipt_missing_work_package_id")
            except Exception as exc: warnings.append(f"completion_receipt_unreadable:{exc}")
            m=WP_RE.search(Path(rp).name)
            if m: evidence.append((m.group(0),"receipt_filename"))
        for m in WP_RE.finditer(msg): evidence.append((m.group(0),"commit_message"))
        for f in files:
            m=WP_RE.search(f)
            if m: evidence.append((m.group(0),"changed_path"))
        ids={x[0] for x in evidence}
        rec=MergeDiscoveryRecord(f"md-{uuid4().hex}",target_id,source_kind,sha,sha,completion_receipt_path=receipt_path,warnings=warnings,metadata=metadata)
        if not ids: rec.state="ignored"; rec.warnings.append("no_work_package_identity_evidence"); return rec
        receipt_ids={wp for wp,method in evidence if method in {"receipt_work_package_id","receipt_filename"}}
        if receipt_ids and len(receipt_ids)==1:
            rec.work_package_id=next(iter(receipt_ids)); rec.correlation_method=next(m for wp,m in evidence if wp==rec.work_package_id and m in {"receipt_work_package_id","receipt_filename"}); rec.state="discovered"; rec.metadata["identity_evidence"]=evidence; rec.metadata["evidence_level"]="completion_receipt_commit"; return rec
        if len(ids)>1: rec.state="ambiguous"; rec.errors.append("conflicting_work_package_ids:"+",".join(sorted(ids))); rec.metadata["identity_evidence"]=evidence; return rec
        rec.work_package_id=next(iter(ids)); rec.correlation_method=next(m for wp,m in evidence if wp==rec.work_package_id); rec.state="discovered"; rec.metadata["identity_evidence"]=evidence; return rec
    def _dedupe_and_request(self, rec, metrics):
        if not rec.work_package_id or rec.state!="discovered": return
        key={"target_id":rec.target_id,"work_package_id":rec.work_package_id,"source_commit":rec.source_commit}
        for p in self.records_dir().glob("*.json") if self.records_dir().exists() else []:
            d=_read(p); md=d.get("metadata",{})
            if d.get("target_id")==key["target_id"] and d.get("work_package_id")==key["work_package_id"] and d.get("source_commit")==key["source_commit"] and d.get("audit_request_id"):
                rec.state="already_processed"; rec.duplicate_of=d.get("discovery_id"); metrics["duplicate_audit_requests_suppressed"]+=1; return
        if self._has_final_verdict(rec): rec.state="already_processed"; metrics["duplicate_audit_requests_suppressed"]+=1; return
        req=PostMergeAuditRequest.create(rec.target_id,rec.work_package_id,rec.source_kind,rec.source_reference,expected_files=[],metadata={"discovery_id":rec.discovery_id,"source_commit":rec.source_commit,"completion_receipt_path":rec.completion_receipt_path,"correlation_method":rec.correlation_method})
        d=req.to_dict(); d["state"]="pending"; _write(self.requests_dir()/f"{req.audit_id}.json",d); rec.audit_request_id=req.audit_id; rec.state="request_created"; metrics["audit_requests_created_from_merges"]+=1
    def _has_final_verdict(self, rec):
        vd=self.root/"runtime/post_merge_audit/verdicts"
        if not vd.exists(): return False
        for p in vd.glob("*.json"):
            d=_read(p)
            if d.get("target_id")==rec.target_id and d.get("work_package_id")==rec.work_package_id and d.get("verdict") in FINAL_VERDICTS: return True
        return False
    def _candidate_count(self): return len(list((self.root/CANDIDATES).glob("*.json"))) if (self.root/CANDIDATES).exists() else 0
    def _ambiguous_count(self): return sum(1 for p in (self.records_dir().glob("*.json") if self.records_dir().exists() else []) if _read(p).get("state")=="ambiguous")
    def status(self,target="estate-main"):
        p=self.root/STATUS/"latest.json"
        return _read(p) if p.exists() else {"merge_discovery_available":True,"summary":{"merge_discovery_available":True}}
    def candidates(self,target="estate-main"):
        return {"candidates":[_read(p) for p in sorted((self.root/CANDIDATES).glob("*.json"))] if (self.root/CANDIDATES).exists() else []}
