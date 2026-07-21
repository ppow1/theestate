"""Governed canonical portrait acceptance and resolution (WP-4127).

This validator can establish eligibility and integrity; it never grants Steward approval.
"""
from __future__ import annotations
import argparse, hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "canonical_portrait_lock_v1"
STATES = {"candidate", "preferred", "provisional", "canonical", "rejected", "superseded", "retired"}
REQUIRED_SLOTS = {"hero_portrait", "professional_office_portrait", "full_body_standing_reference", "profile_reference", "rear_reference", "front_three_quarter_reference", "rear_three_quarter_reference", "expression_sheet", "headshot_set", "thumbnail_set"}
CHECKS = {"identity", "metadata", "provenance", "hash", "crop", "derivative", "consistency", "access"}

def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def record_hash(record: dict) -> str:
    copy = {k: v for k, v in record.items() if k != "lock_hash"}
    return "sha256:" + hashlib.sha256(canonical_json(copy)).hexdigest()

def _diag(out, code, severity, message, slot=None):
    item = {"code": code, "severity": severity, "message": message}
    if slot: item["slot"] = slot
    out.append(item)

def validate_lock(record: dict, *, root: Path, now: datetime | None = None) -> dict:
    """Validate lock evidence without changing state or manufacturing approval."""
    ds=[]; now=now or datetime.now(timezone.utc)
    if record.get("schema_version") != SCHEMA_VERSION: _diag(ds,"PCL-SCHEMA-001","error","Unsupported schema version")
    state=record.get("state")
    if state not in STATES: _diag(ds,"PCL-STATE-001","error","Invalid lifecycle state")
    if not record.get("resident_id") or not record.get("lock_id") or not record.get("lock_version"): _diag(ds,"PCL-IDENTITY-001","error","Lock identity fields are required")
    if record.get("lock_hash") != record_hash(record): _diag(ds,"PCL-LOCK-HASH-001","error","Lock hash does not match canonical record content")
    slots=record.get("slots",[]); names=[s.get("category") for s in slots]
    required=set(record.get("required_categories", REQUIRED_SLOTS))
    missing=sorted(required-set(names))
    if missing: _diag(ds,"PCL-COVERAGE-001","error","Missing required categories: "+", ".join(missing))
    for duplicate in sorted({x for x in names if names.count(x)>1}): _diag(ds,"PCL-UNIQUE-001","error","Category occurs more than once",duplicate)
    canonical_asset_ids=[]
    for slot in slots:
        category=slot.get("category"); asset=slot.get("asset") or {}; evidence=slot.get("acceptance_evidence") or {}
        if slot.get("state") not in STATES: _diag(ds,"PCL-SLOT-STATE-001","error","Invalid slot state",category)
        if slot.get("state") == "canonical":
            if asset.get("asset_id") in canonical_asset_ids: _diag(ds,"PCL-ASSET-REUSE-001","error","Canonical asset cannot fill multiple categories",category)
            canonical_asset_ids.append(asset.get("asset_id"))
            if state != "canonical": _diag(ds,"PCL-PARENT-STATE-001","error","Canonical slot requires canonical lock",category)
            if not asset.get("asset_id") or not asset.get("path") or not str(asset.get("sha256","")).startswith("sha256:"): _diag(ds,"PCL-ASSET-001","error","Canonical asset identity, path, and hash required",category)
            else:
                path=(root/asset["path"]).resolve()
                if not path.is_file(): _diag(ds,"PCL-FILE-MISSING-001","error","Canonical file is missing",category)
                elif "sha256:"+hashlib.sha256(path.read_bytes()).hexdigest()!=asset["sha256"]: _diag(ds,"PCL-ASSET-HASH-001","error","Canonical file hash mismatch",category)
            absent=sorted(CHECKS-set(evidence))
            if absent: _diag(ds,"PCL-EVIDENCE-001","error","Missing checks: "+", ".join(absent),category)
            for name in CHECKS & set(evidence):
                if evidence[name].get("result") != "pass" or not evidence[name].get("evidence_ref"): _diag(ds,"PCL-CHECK-001","error",f"{name} check is not evidenced as passed",category)
    decision=record.get("steward_decision") or {}
    if state == "canonical":
        if not (decision.get("explicit_approval") is True and decision.get("authority_role")=="Steward" and all(decision.get(k) for k in ("decision_id","steward_id","decided_at","signed_record_sha256"))): _diag(ds,"PCL-STEWARD-001","error","Explicit complete Steward approval is required")
        if any(s.get("state") != "canonical" for s in slots) or set(names)!=required: _diag(ds,"PCL-CANON-COVERAGE-001","error","Canonical lock requires exactly one canonical asset in every required category")
        if record.get("blocking_findings"): _diag(ds,"PCL-BLOCKING-001","error","Canonical lock has blocking findings")
    elif decision.get("explicit_approval") is True: _diag(ds,"PCL-APPROVAL-CONFLICT-001","error","Noncanonical lock cannot claim approval")
    try:
        reviewed=datetime.fromisoformat(record["reviewed_at"].replace("Z","+00:00")); days=record.get("stale_after_days",365)
        if (now-reviewed).days>days: _diag(ds,"PCL-STALE-001","error" if state=="canonical" else "warning","Lock review is stale")
    except (KeyError,TypeError,ValueError): _diag(ds,"PCL-TIME-001","error","reviewed_at must be ISO-8601")
    for ref in record.get("downstream_references",[]):
        if ref.get("lock_hash") != record.get("lock_hash"): _diag(ds,"PCL-DOWNSTREAM-STALE-001","error","Downstream reference is not pinned to this lock hash")
    ds.sort(key=lambda x:(x["code"],x.get("slot",""),x["message"]))
    return {"schema_version":"canonical_portrait_lock_validation_v1","status":"fail" if any(x["severity"]=="error" for x in ds) else "pass","canonical":state=="canonical" and not any(x["severity"]=="error" for x in ds),"may_grant_steward_approval":False,"diagnostics":ds,"coverage":{"required":len(required),"represented":len(required&set(names)),"canonical":sum(s.get("state")=="canonical" for s in slots)}}

def resolve_canonical(records: list[dict], resident_id: str, category: str, *, root: Path) -> dict:
    matches=[(r,s) for r in records if r.get("resident_id")==resident_id and r.get("state")=="canonical" for s in r.get("slots",[]) if s.get("category")==category and s.get("state")=="canonical"]
    valid=[(r,s) for r,s in matches if validate_lock(r,root=root)["status"]=="pass"]
    if len(valid)!=1: return {"status":"unavailable","code":"PCL-RESOLVE-MISSING-001" if not valid else "PCL-RESOLVE-AMBIGUOUS-001","asset":None}
    r,s=valid[0]; return {"status":"resolved","lock_id":r["lock_id"],"lock_version":r["lock_version"],"lock_hash":r["lock_hash"],"asset":s["asset"]}

def main():
    p=argparse.ArgumentParser(); p.add_argument("record",type=Path); p.add_argument("--root",type=Path,default=Path.cwd()); p.add_argument("--output",type=Path); a=p.parse_args()
    result=validate_lock(json.loads(a.record.read_text()),root=a.root)
    if a.output: a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({"status":result["status"],"canonical":result["canonical"],"diagnostics":len(result["diagnostics"])})); return 0 if result["status"]=="pass" else 2
if __name__=="__main__": raise SystemExit(main())
