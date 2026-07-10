"""Protected local personal journal store.

Journals are private working memory. Raw entries are not institutional truth,
not routine telemetry, and not eligible for public/status/search surfaces.
"""
from __future__ import annotations

import hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

ENTRY_SCHEMA = "estate.personal_journal_entry.v1"
SUMMARY_SCHEMA = "estate.personal_journal_summary.v1"
EXPORT_SCHEMA = "estate.personal_journal_export.v1"
AUDIT_SCHEMA = "estate.personal_journal_audit.v1"
DEFAULT_CLASSIFICATION = "Steward Only"
PROTECTED = {"Steward Only", "Local Only", "Restricted"}


def _now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def _slug(v): return re.sub(r"[^a-z0-9_-]+", "-", str(v).strip().lower()).strip("-") or "unknown"
def _read(p: Path, default):
    if not p.exists(): return default
    return json.loads(p.read_text(encoding="utf-8"))
def _write(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(data, indent=2, sort_keys=True)+"\n", encoding="utf-8"); return p

class JournalAccessError(PermissionError): pass

class PersonalJournalStore:
    def __init__(self, root: str|Path|None=None):
        self.root = Path(root) if root else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
    def personnel(self): return _read(self.root/"data/registry/personnel.json", []) or []
    def resolve_owner(self, owner):
        key=_slug(owner)
        for p in self.personnel():
            vals=[p.get("employee_id"), p.get("resident_id"), p.get("display_name"), p.get("mailbox_id")]
            if key in {_slug(v) for v in vals if v is not None}:
                kind="resident" if p.get("resident_id") and key==_slug(p.get("resident_id")) else "employee"
                return {"owner_kind": kind, "employee_id": p.get("employee_id"), "resident_id": p.get("resident_id"), "display_name": p.get("display_name")}
        raise ValueError("owner must resolve to existing personnel identity")
    def owner_key(self, ident): return f"employee-{ident['employee_id']}" if ident.get("employee_id") is not None else f"resident-{_slug(ident.get('resident_id'))}"
    def base(self, owner):
        ident=self.resolve_owner(owner); return self.root/"runtime/protected_journals"/self.owner_key(ident), ident
    def _audit(self, action, actor, owner_id, result, details=None):
        rec={"schema_version":AUDIT_SCHEMA,"occurred_at":_now(),"action":action,"actor":str(actor),"owner_id":owner_id,"result":result,"details":details or {}}
        path=self.root/"runtime/protected_journals/audit.jsonl"; path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f: f.write(json.dumps(rec, sort_keys=True)+"\n")
        return rec
    def _can_read(self, entry, actor):
        a=_slug(actor); allowed={_slug(entry["owner_id"]), _slug(entry.get("author")), "steward", "founder", "ingrid"} | {_slug(x) for x in entry.get("readers", [])}
        return a in allowed
    def _can_write(self, entry, actor):
        a=_slug(actor); return a in {_slug(entry["owner_id"]), _slug(entry.get("author")), "steward", "founder", "ingrid"} | {_slug(x) for x in entry.get("writers", [])}
    def _load_entry(self, owner, entry_id):
        b, ident=self.base(owner); p=b/"entries"/f"{entry_id}.json"; return p, ident, _read(p, None)
    def create_entry(self, owner, author, body, *, entry_type="reflection", title="", classification=DEFAULT_CLASSIFICATION, readers=None, writers=None):
        b, ident=self.base(owner); owner_id=self.owner_key(ident)
        eid="jrn_"+hashlib.sha256(f"{owner_id}|{author}|{_now()}|{body}".encode()).hexdigest()[:16]
        entry={"schema_version":ENTRY_SCHEMA,"entry_id":eid,"owner_id":owner_id,"owner_identity":ident,"author":author,"title":title,"entry_type":entry_type,"classification":classification,"created_at":_now(),"updated_at":_now(),"status":"active","body":body,"redactions":[],"readers":readers or [],"writers":writers or [],"governance":{"private_working_memory":True,"institutional_truth":False,"public_surface_allowed":False,"cloud_storage_allowed":False}}
        _write(b/"entries"/f"{eid}.json", entry); self._audit("write", author, owner_id, "allowed", {"entry_id":eid}); return {"path":str((b/"entries"/f"{eid}.json").relative_to(self.root)),"entry":entry}
    def list_entries(self, owner, actor):
        b, ident=self.base(owner); owner_id=self.owner_key(ident); rows=[]
        for p in sorted((b/"entries").glob("*.json")):
            e=_read(p,{}); 
            if self._can_read(e, actor): rows.append({k:e.get(k) for k in ["entry_id","title","entry_type","classification","created_at","updated_at","status"]})
        self._audit("list", actor, owner_id, "allowed", {"count":len(rows)}); return {"owner_id":owner_id,"entries":rows}
    def read_entry(self, owner, entry_id, actor):
        p, ident, e=self._load_entry(owner, entry_id); owner_id=self.owner_key(ident)
        if not e or not self._can_read(e, actor): self._audit("read", actor, owner_id, "denied", {"entry_id":entry_id}); raise JournalAccessError("journal read denied")
        self._audit("read", actor, owner_id, "allowed", {"entry_id":entry_id}); return e
    def redact_entry(self, owner, entry_id, actor, reason, replacement="[redacted]"):
        p, ident, e=self._load_entry(owner, entry_id); owner_id=self.owner_key(ident)
        if not e or not self._can_write(e, actor): self._audit("redact", actor, owner_id, "denied", {"entry_id":entry_id}); raise JournalAccessError("journal redaction denied")
        e["body"]=replacement; e["status"]="redacted"; e["updated_at"]=_now(); e.setdefault("redactions",[]).append({"at":_now(),"by":actor,"reason":reason}); _write(p,e); self._audit("redact", actor, owner_id, "allowed", {"entry_id":entry_id,"reason":reason}); return e
    def archive_entry(self, owner, entry_id, actor, reason):
        p, ident, e=self._load_entry(owner, entry_id); owner_id=self.owner_key(ident)
        if not e or not self._can_write(e, actor): self._audit("archive", actor, owner_id, "denied", {"entry_id":entry_id}); raise JournalAccessError("journal archival denied")
        e["status"]="archived"; e["archived_at"]=_now(); e["archive_reason"]=reason; e["updated_at"]=_now(); _write(p,e); self._audit("archive", actor, owner_id, "allowed", {"entry_id":entry_id}); return e
    def approve_summary(self, owner, entry_id, actor, summary):
        e=self.read_entry(owner, entry_id, actor); owner_id=e["owner_id"]
        if _slug(actor) not in {"steward","founder","ingrid",_slug(e["owner_id"])}: self._audit("summary_approval", actor, owner_id, "denied", {"entry_id":entry_id}); raise JournalAccessError("summary approval denied")
        s={"schema_version":SUMMARY_SCHEMA,"summary_id":"jsum_"+entry_id[4:],"source_entry_id":entry_id,"owner_id":owner_id,"approved_by":actor,"approved_at":_now(),"classification":"Estate Internal","summary":summary,"raw_entry_included":False,"institutional_truth":False}
        b,_=self.base(owner); _write(b/"summaries"/f"{s['summary_id']}.json",s); self._audit("summary_approval", actor, owner_id, "allowed", {"entry_id":entry_id,"summary_id":s["summary_id"]}); return s
    def export_entries(self, owner, actor, *, scope="summaries", entry_ids=None, include_body=False):
        b, ident=self.base(owner); owner_id=self.owner_key(ident); entries=[]
        if include_body and _slug(actor) not in {"steward","founder","ingrid",owner_id}: self._audit("export", actor, owner_id, "denied", {"include_body":include_body}); raise JournalAccessError("raw journal export denied")
        if scope=="summaries": entries=[_read(p,{}) for p in sorted((b/"summaries").glob("*.json"))]
        else:
            for eid in (entry_ids or []):
                e=self.read_entry(owner,eid,actor); entries.append(e if include_body else {k:e.get(k) for k in ["entry_id","title","entry_type","classification","created_at","status"]})
        payload={"schema_version":EXPORT_SCHEMA,"exported_at":_now(),"owner_id":owner_id,"exported_by":actor,"scope":scope,"include_body":include_body,"items":entries}
        self._audit("export", actor, owner_id, "allowed", {"scope":scope,"count":len(entries),"include_body":include_body}); return payload
    def privacy_safe_status(self):
        base=self.root/"runtime/protected_journals"; rows=[]
        for d in sorted(base.glob("employee-*")) + sorted(base.glob("resident-*")):
            rows.append({"owner_id":d.name,"entry_count":len(list((d/"entries").glob("*.json"))),"approved_summary_count":len(list((d/"summaries").glob("*.json"))),"body_included":False})
        return {"schema_version":"estate.personal_journal_status.v1","generated_at":_now(),"privacy":"metadata counts only; no journal bodies or raw reflections","owners":rows}
