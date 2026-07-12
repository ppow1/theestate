"""Resident-centric conversation isolation and room session bindings."""
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from pathlib import Path
from estate.core.paths import ESTATE_ROOT

def _root(root=None): return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
def _key(v): return str(v or "").lower().replace(" ","-").strip("-")
def _now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
def session_identity(resident_id, user_id="steward", surface_id="resident", session_id=None, room_id=None): return {"schema_version":"resident_conversation_session.v1","resident_id":_key(resident_id),"user_id":user_id,"surface_id":surface_id,"room_id":room_id,"session_id":session_id or str(uuid.uuid4())}
def _path(base, ident):
    scope=_key(ident.get("room_id") or ident["resident_id"]); return base/"runtime/resident_interactions/isolated_sessions"/_key(ident["surface_id"])/scope/f"{_key(ident['session_id'])}.json"
def append_turn(ident, role, content, root=None):
    base=_root(root); p=_path(base,ident); p.parent.mkdir(parents=True,exist_ok=True); data=json.loads(p.read_text()) if p.exists() else {"identity":ident,"turns":[]}
    if data["identity"]["resident_id"]!=ident["resident_id"]: return {"ok":False,"failed_closed":True,"diagnostics":[{"type":"resident_binding_conflict"}]}
    data["turns"].append({"role":role,"content":content,"created_at":_now()}); p.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n"); return {"ok":True,"path":str(p.relative_to(base)),"identity":ident}
def load_history(ident, root=None):
    base=_root(root); p=_path(base,ident); data=json.loads(p.read_text()) if p.exists() else {"identity":ident,"turns":[]}
    return {"identity":ident,"history_source":str(p.relative_to(base)),"turns":data.get("turns",[]),"diagnostics":[]}
def reset_session(ident, root=None):
    base=_root(root); p=_path(base,ident);
    if p.exists(): p.unlink()
    return {"ok":True,"identity":ident,"canonical_identity_deleted":False}
