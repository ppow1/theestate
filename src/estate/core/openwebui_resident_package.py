"""Canonical Open WebUI resident package projection."""
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any
from estate.core.paths import ESTATE_ROOT
from estate.core.resident_identity_composition import compose_resident_identity
from estate.core.resident_interaction import resident_surface
from estate.core.resident_voice_commissioning import commissioned_voice_projection

def _root(root=None) -> Path: return Path(root) if root is not None else ESTATE_ROOT
def _key(v: Any) -> str: return re.sub(r"[^a-z0-9-]+","-",str(v or "").lower()).strip("-")
def _read(path: Path) -> Any:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return None

def visual_projection(resident_id: str, display_name: str, root=None) -> dict[str, Any]:
    rootp=_root(root); reg=_read(rootp/"data/visuals/canonical_visual_registry.json") or {}; rows=reg.get("residents") or []
    wanted={_key(resident_id), _key(display_name)}
    row=next((r for r in rows if _key(r.get("resident_id")) in wanted or _key(r.get("display_name")) in wanted), None)
    if not row: return {"visual_state":"unavailable","avatar_uri":None,"visual_provenance":{"registry":"data/visuals/canonical_visual_registry.json","reason":"no_row"}}
    status=str(row.get("asset_library_status") or "").lower(); scope=str(row.get("publication_scope") or "").lower()
    if "restricted" in scope: state="restricted"
    elif "canonical" in status and row.get("avatar_path"): state="canonical"
    elif "placeholder" in status: state="placeholder"
    elif "provisional" in status or row.get("physical_specification_status") == "provisional": state="provisional"
    else: state="unavailable"
    return {"visual_state":state,"avatar_uri":row.get("avatar_path"),"visual_provenance":{"registry":"data/visuals/canonical_visual_registry.json","row":row,"truth_boundary":"manifest controls are not promoted to final raster portraits"}}

def resident_package(model_id: str, resident_id: str, root=None) -> dict[str, Any]:
    rootp=_root(root); surface=resident_surface(resident_id, rootp); comp=compose_resident_identity(resident_id, surface_id="open-webui-resident-package", root=rootp)
    voice=commissioned_voice_projection(resident_id, rootp); visual=visual_projection(resident_id, surface.get("resident_display_name", resident_id.title()), rootp)
    return {"resident_id":resident_id,"display_name":surface.get("resident_display_name", resident_id.title()),"office_title":surface.get("office"),"role_summary":surface.get("role"),"model_id":model_id,"identity_schema_version":comp.get("schema_version"),"identity_source_hash":comp.get("identity_version_or_source_hash"),"identity_failed_closed":comp.get("failed_closed"),"identity_sources":comp.get("source_trace") or comp.get("included_context_layers",[]),"visual_state":visual["visual_state"],"avatar_uri":visual["avatar_uri"],"visual_provenance":visual["visual_provenance"],"voice_state":voice["voice_state"],"voice_engine":voice["voice_engine"],"voice_id":voice["voice_id"],"voice_speed":voice["voice_speed"],"voice_approval_state":voice["voice_approval_state"],"tts_available":voice["tts_available"],"voice_provenance":voice["voice_provenance"],"capabilities":["chat.completions","resident_identity_composition","openwebui_catalog"],"privileged_actions_enabled":False,"ready_state":ready_state(surface.get("resident_display_name", resident_id.title()), voice, visual)}

def ready_state(name: str, voice: dict[str,Any], visual: dict[str,Any]) -> dict[str, Any]:
    label = f"{name} ready"
    return {"label":label,"identity":"canonical","office":"loaded","visual":visual["visual_state"],"voice": (f"canonical — Kokoro {voice['voice_id']} @ {voice['voice_speed']}" if voice["voice_state"]=="canonical" else voice["voice_state"]),"tts_engine":"available" if voice.get("tts_available") else "unavailable","memory_session":"connected","privileged_actions":"disabled"}
