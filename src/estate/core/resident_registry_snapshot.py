"""Synchronized read-only resident registry snapshots for resident runtime."""
from __future__ import annotations
import hashlib,json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from estate.core.paths import ESTATE_ROOT

def _root(root=None): return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
def _now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def _key(v): return str(v or "").strip().lower().replace(" ","-")
def _read(path): return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
def build_resident_registry_snapshot(root=None):
    base=_root(root); sources=[]; diagnostics=[]; conflicts=[]
    path=base/"data/registry/residents.json"; rows=_read(path) or []; sources.append("data/registry/residents.json")
    seen={}; residents=[]
    for r in rows if isinstance(rows,list) else []:
        rid=str(r.get("id") or ""); name=str(r.get("name") or "")
        k=_key(rid or name)
        if k in seen: conflicts.append({"type":"duplicate_resident_id","resident_id":rid,"paths":["data/registry/residents.json"]})
        seen[k]=r
        residents.append({"id":rid,"name":name,"office":r.get("office"),"department":r.get("department"),"role":r.get("role"),"status":r.get("status"),"classification":r.get("classification"),"gateway_model":r.get("gateway_model"),"mailbox_id":r.get("mailbox_id"),"canonical":r.get("canonical") or ""})
    # mailbox binding is optional but diagnosable
    personnel_path=base/"data/registry/personnel.json"
    if personnel_path.exists(): sources.append("data/registry/personnel.json")
    active=[r for r in residents if str(r.get("status","")).lower()=="active"]
    payload={"schema_version":"resident_registry_snapshot.v1","snapshot_timestamp":_now(),"sources":sources,"record_counts":{"residents":len(residents),"active_residents":len(active)},"residents":residents,"active_residents":active,"conflicts":conflicts,"diagnostics":diagnostics}
    payload["snapshot_hash"]=hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()[:16]
    payload["failed_closed"]=bool(conflicts)
    return payload

def describe_resident_state(name, root=None):
    snap=build_resident_registry_snapshot(root); wanted=_key(name)
    for r in snap["residents"]:
        if wanted in {_key(r.get("id")),_key(r.get("name"))}: return {"snapshot":snap,"resident":r,"state":str(r.get("status") or "unknown").lower()}
    return {"snapshot":snap,"resident":None,"state":"unknown"}
