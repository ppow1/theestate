"""Reusable local resident interaction framework for chat, surfaces, and memory governance."""
from __future__ import annotations

import json, os, re, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_authority import check_authority, list_authority, ALLOWED, REQUIRES_STEWARD, REQUIRES_ESCALATION

CHAT_STORE = Path("runtime/resident_interactions/sessions")
SURFACE_DIR = Path("operations/residents/surfaces")
FORGET_AUDIT = Path("runtime/resident_interactions/forget_audit.jsonl")
STANDARD_VERSION = "resident-api-standard-v1"

RESIDENT_PROFILES = {
    "alfred": {"resident_id":"alfred","resident_display_name":"Alfred","office":"Office of Operations","role":"Operational resident coordinator","implementation_version":"alfred-operations-implementation-v1"},
    "helen": {"resident_id":"helen","resident_display_name":"Helen","office":"Human Resources","role":"HR onboarding resident","implementation_version":"helen-hr-implementation-v1"},
    "ingrid": {"resident_id":"ingrid","resident_display_name":"Ingrid","office":"Security","role":"Security resident","implementation_version":"ingrid-security-implementation-v1"},
    "chief-architect-5": {"resident_id":"chief-architect-5","resident_display_name":"Chief Architect #5","office":"Architecture","role":"Chief Architect","implementation_version":"chief-architect-5-implementation-v1"},
    "character-development-engineer": {"resident_id":"character-development-engineer","resident_display_name":"Character Development Engineer","office":"Office of Character Development","role":"Resident behavior and surface proposal engineer","implementation_version":"character-development-engineer-implementation-v1"},
}

DEFAULT_CAPABILITIES = [
    {"id":"conversation.respond","label":"Respond in conversation","description":"Generate a visible local resident response to Steward input.","implementation_status":"implemented","backing":"estate.core.resident_interaction.process_chat","authority_category":"conversation_only","required_approval_level":"none","version_introduced":STANDARD_VERSION,"owning_office":"resident office"},
    {"id":"recommendation.prepare","label":"Prepare recommendation","description":"Offer non-authoritative recommendations within resident responsibilities.","implementation_status":"implemented","backing":"authority metadata only","authority_category":"recommendation","required_approval_level":"none","version_introduced":STANDARD_VERSION,"owning_office":"resident office"},
    {"id":"action.propose","label":"Propose action","description":"Describe a proposed action without executing it.","implementation_status":"implemented","backing":"authority metadata only","authority_category":"proposed_action","required_approval_level":"steward_for_execution","version_introduced":STANDARD_VERSION,"owning_office":"resident office"},
    {"id":"character.mood_arc.evaluate","label":"Evaluate character mood arc","description":"Future extension example for Character Development Engineering; not executed by WP-0126.","implementation_status":"planned","backing":"extension proposal required","authority_category":"behavior_extension","required_approval_level":"chief_architect_or_steward_review","version_introduced":"future-proposal","owning_office":"Office of Character Development"},
]

def _root(root=None): return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
def _now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def _key(v): return re.sub(r"[^a-z0-9-]+", "-", str(v or "").lower()).strip("-") or "resident"
def _safe(v): return re.sub(r"[^A-Za-z0-9_.-]", "_", str(v))
def _read_json(path):
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return None

def local_llm_status() -> dict[str, Any]:
    exe = shutil.which("ollama")
    status = {"intended_mode":"local_llm","available":False,"provider":"none","model":None,"discovery":"ollama executable not found; deterministic fallback available"}
    if not exe: return status
    status.update({"provider":"ollama","discovery":"ollama executable found; probing local models"})
    try:
        res = subprocess.run([exe,"list"], text=True, capture_output=True, timeout=2, check=False)
        lines = [l.split() for l in res.stdout.splitlines()[1:] if l.strip()]
        if res.returncode == 0 and lines:
            status.update({"available":True,"model":lines[0][0],"discovery":"ollama local model discovered"})
    except Exception as exc:
        status["discovery"] = f"ollama probe failed locally: {exc}"
    return status

def resident_surface(resident: str, root=None) -> dict[str, Any]:
    r = _root(root); key = _key(resident).replace("alfred-operations", "alfred")
    profile = RESIDENT_PROFILES.get(key, {"resident_id":key,"resident_display_name":str(resident).title(),"office":"Unassigned resident office","role":"Future resident","implementation_version":f"{key}-implementation-v1"})
    artifact = r / SURFACE_DIR / f"{key}.json"
    data = _read_json(artifact) if artifact.exists() else None
    caps = data.get("capabilities") if isinstance(data, dict) and isinstance(data.get("capabilities"), list) else DEFAULT_CAPABILITIES
    return {"kind":"resident_interaction_surface","resident_id":profile["resident_id"],"resident_display_name":profile["resident_display_name"],"office":profile["office"],"role":profile["role"],"resident_api_standard_version":STANDARD_VERSION,"resident_implementation_version":profile["implementation_version"],"surface_reference":str((SURFACE_DIR / f"{key}.json")).replace('\\','/'),"capabilities":caps,"chat_endpoints":{"get":"GET /api/residents/{resident_id}/chat","post":"POST /api/residents/{resident_id}/chat","forget":"POST /api/residents/{resident_id}/forget","surface":"GET /api/residents/{resident_id}/surface"},"extension_mechanism":{"proposal_template":"docs/operations/residents/resident_api_extension_proposal_template.md","profile_template":"docs/operations/residents/resident_implementation_profile_template.md","rule":"Add or change capabilities through reviewed resident surface/profile artifacts; do not hide one-off UI-only actions."}}

def _next_session_id(root, resident):
    day = datetime.now(timezone.utc).strftime("%Y%m%d"); folder = root/CHAT_STORE; folder.mkdir(parents=True, exist_ok=True)
    n = len(list(folder.glob(f"{_key(resident)}_steward_{day}_*.json"))) + 1
    return f"{_key(resident)}_steward_{day}_{n:03d}"

def _session_path(root, sid): return root/CHAT_STORE/f"{_safe(sid)}.json"

def _fallback_response(resident, message, surface):
    return f"{surface['resident_display_name']} received your message locally. I can discuss, recommend, or propose actions within my resident surface, but I will not execute work or claim authorization from this chat. Prompt summary: {message[:180]}"

def process_chat(resident: str, user_message: str, *, session_id: str|None=None, participant_role="Steward", action: str="summarize", root=None) -> dict[str, Any]:
    rootp = _root(root); surface = resident_surface(resident, rootp); sid = session_id or _next_session_id(rootp, resident)
    existing = _read_json(_session_path(rootp, sid)) or {"kind":"resident_interaction_session","session_id":sid,"resident_id":surface["resident_id"],"resident_display_name":surface["resident_display_name"],"created_at":_now(),"turns":[],"memory_status":"active"}
    turn_no = len(existing.get("turns", [])) + 1
    llm = local_llm_status(); mode = "local_llm" if llm.get("available") else "deterministic_fallback"
    auth = check_authority(surface["resident_id"], action, root=rootp, audit=True)
    status = "within_responsibility" if auth.get("decision")==ALLOWED else ("requires_steward_authorization" if auth.get("decision")==REQUIRES_STEWARD else "blocked" if not auth.get("allowed") else "conversation_only")
    response = _fallback_response(resident, user_message, surface)
    turn = {"session_id":sid,"turn_id":f"turn_{turn_no:04d}","resident_id":surface["resident_id"],"resident_display_name":surface["resident_display_name"],"participant_role":participant_role,"created_at":_now(),"user_message":user_message,"resident_response":response,"context_used":[surface["surface_reference"],"src/estate/core/resident_authority.py"],"llm":{"mode":mode,"provider":llm.get("provider","none"),"model":llm.get("model")},"resident_surface":{"resident_api_standard_version":surface["resident_api_standard_version"],"resident_implementation_version":surface["resident_implementation_version"],"allowed_capabilities":[c["id"] for c in surface["capabilities"]],"surface_reference":surface["surface_reference"]},"authority":{"action_requested": action not in {"summarize","observe","conversation"},"action_executed":False,"authority_status":status,"authority_reference":"src/estate/core/resident_authority.py","decision":auth.get("decision")},"memory_status":"active"}
    existing.setdefault("turns", []).append(turn); existing["updated_at"]=_now(); existing["memory_status"]="active"; existing["normal_history"]=[t for t in existing["turns"] if t.get("memory_status")=="active"]
    path = _session_path(rootp, sid); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(existing, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return {"ok":True,"session_id":sid,"turn":turn,"session_path":str(path.relative_to(rootp)).replace('\\','/'),"llm_discovery":llm}

def load_history(resident=None, session_id=None, root=None, include_forgotten=False):
    rootp=_root(root); sessions=[]
    for p in sorted((rootp/CHAT_STORE).glob("*.json")):
        data=_read_json(p)
        if not isinstance(data, dict): continue
        if session_id and data.get("session_id") != session_id: continue
        if resident and _key(data.get("resident_id")) != _key(resident): continue
        turns=data.get("turns", []) if include_forgotten else data.get("normal_history", [t for t in data.get("turns", []) if t.get("memory_status")=="active"])
        sessions.append({**data,"turns":turns,"path":str(p.relative_to(rootp)).replace('\\','/')})
    return {"kind":"resident_interaction_history","sessions":sessions,"include_forgotten":include_forgotten,"storage_path":str(CHAT_STORE)}

def forget_conversation(session_id: str, *, turn_id: str|None=None, memory_status="forgotten", reason="Steward-directed redaction", root=None):
    rootp=_root(root); path=_session_path(rootp, session_id); data=_read_json(path)
    if not isinstance(data, dict): return {"ok":False,"error":"session_not_found","session_id":session_id}
    affected=[]
    for t in data.get("turns", []):
        if turn_id is None or t.get("turn_id")==turn_id:
            affected.append(t.get("turn_id")); t["memory_status"]=memory_status; t["user_message"]="[redacted by Steward forget/redaction]"; t["resident_response"]="[redacted by Steward forget/redaction]"
    data["memory_status"] = memory_status if turn_id is None else data.get("memory_status","active")
    data["normal_history"]=[t for t in data.get("turns", []) if t.get("memory_status")=="active"]; data["updated_at"]=_now(); path.write_text(json.dumps(data, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    audit={"kind":"resident_conversation_forget_audit","session_id":session_id,"turn_id":turn_id,"affected_turns":affected,"memory_status":memory_status,"reason":reason,"created_at":_now(),"content_preserved_in_normal_history":False}
    ap=rootp/FORGET_AUDIT; ap.parent.mkdir(parents=True, exist_ok=True); ap.open("a",encoding="utf-8").write(json.dumps(audit, sort_keys=True)+"\n")
    return {"ok":True, **audit, "audit_path":str(FORGET_AUDIT)}
