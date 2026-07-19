"""Canonical Character Bible loader for provider-independent resident context."""
from __future__ import annotations
import json, hashlib
from pathlib import Path
from typing import Any
from estate.core.paths import ESTATE_ROOT

def _root(root=None): return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
def _key(v): return str(v or "").lower().replace(" ","-").strip("-")
def _excerpt(path:Path, limit=900):
    try: return path.read_text(encoding="utf-8")[:limit]
    except Exception: return ""
DEFAULTS={"alfred":{"temperament":"composed, precise, dryly warm","speech":"concise executive cadence"},"helen":{"temperament":"approachable, perceptive, humane","speech":"warm workforce-development clarity"},"grace":{"temperament":"energetic, capable, playful, decisive","speech":"operationally direct with momentum"},"ingrid":{"temperament":"reserved, elegant, dryly witty, privacy-aware","speech":"measured and boundary-literate"},"evelyn":{"temperament":"intimate, perceptive, candid, quietly playful","speech":"softly direct and Steward-private"},"eleanor":{"temperament":"archival, careful, exact, quietly humane","speech":"provenance-aware with ledger precision"},"marie":{"temperament":"curious, analytical, patient, source-minded","speech":"research-forward with explicit uncertainty"},"judy":{"temperament":"precise, cautious, practical, calmly skeptical","speech":"concise legal-risk framing"}}
def load_character_context(resident, *, surface_id="resident", root=None):
    base=_root(root); key=_key(resident); sources=[]; excerpts=[]
    candidates=[base/"residents"/f"{key}.md", *sorted((base/"docs/residents"/key).glob("**/*"))] if (base/"docs/residents"/key).exists() else [base/"residents"/f"{key}.md"]
    for p in candidates:
        if p.is_file() and p.suffix.lower() in {".md",".json",".yaml",".yml"}:
            rel=str(p.relative_to(base)).replace('\\','/'); sources.append(rel); excerpts.append({"source":rel,"excerpt":_excerpt(p)})
    # The behavior registry is the provider-neutral, machine-readable expression
    # of canon.  Load only the named resident's row; never let a model infer one
    # resident's manner from another resident's prompt or conversation.
    behavior_path = base / "data/character-architecture/resident_behavior_profiles_v0_1.json"
    behavior = None
    if behavior_path.exists():
        try:
            registry = json.loads(behavior_path.read_text(encoding="utf-8"))
            behavior = (registry.get("residents") or {}).get(key)
            if behavior:
                sources.append(str(behavior_path.relative_to(base)).replace('\\', '/'))
        except (OSError, ValueError, TypeError):
            behavior = None
    private= key=="evelyn" or surface_id.startswith(("conference","room"))
    content={"schema_version":"character_bible_context.v1","resident_key":key,"stable_traits":DEFAULTS.get(key,{}),"behavior_profile":behavior or {},"sources":sources[:20],"source_lineage":excerpts[:6],"unknown_policy":"missing durable personal facts remain unknown","authority_elevation_allowed":False,"private_material_excluded": surface_id.startswith(("conference","room"))}
    content["context_hash"]=hashlib.sha256(json.dumps(content,sort_keys=True,default=str).encode()).hexdigest()[:16]
    return content
