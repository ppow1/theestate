"""Reusable local resident interaction framework for chat, surfaces, and memory governance."""
from __future__ import annotations

import base64, hashlib, json, os, re, shutil, subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_authority import check_authority, list_authority, ALLOWED, REQUIRES_STEWARD, REQUIRES_ESCALATION

CHAT_STORE = Path("runtime/resident_interactions/sessions")
ATTACHMENT_STORE = Path("runtime/resident_interactions/attachments")
VISION_CONFIG_PATH = Path("runtime/residents/alfred/vision_model_config.json")
SURFACE_DIR = Path("operations/residents/surfaces")
FORGET_AUDIT = Path("runtime/resident_interactions/forget_audit.jsonl")
STANDARD_VERSION = "resident-api-standard-v1"


OLLAMA_ENDPOINT = os.environ.get("ESTATE_OLLAMA_ENDPOINT", "http://127.0.0.1:11434").rstrip("/")
PREFERRED_ALFRED_MODEL = os.environ.get("ESTATE_ALFRED_OLLAMA_MODEL", "qwen3:8b")

class LocalOllamaAdapter:
    """Small local-only Ollama provider boundary for resident chat."""

    provider = "ollama"

    def __init__(self, endpoint: str = OLLAMA_ENDPOINT, timeout: float = 12.0):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def discover_models(self) -> dict[str, Any]:
        names: list[str] = []
        source = f"{self.endpoint}/api/tags"
        try:
            with urllib.request.urlopen(f"{self.endpoint}/api/tags", timeout=min(self.timeout, 4.0)) as response:
                payload = json.loads(response.read().decode("utf-8"))
            for item in payload.get("models") or []:
                name = item.get("name") or item.get("model")
                if name:
                    names.append(str(name))
        except Exception as http_exc:
            exe = shutil.which("ollama")
            if not exe:
                return {"available": False, "provider": self.provider, "endpoint": self.endpoint, "models": [], "discovery": f"Ollama unavailable locally: {http_exc}; ollama executable not found"}
            try:
                res = subprocess.run([exe, "list"], text=True, capture_output=True, timeout=4, check=False)
                if res.returncode != 0:
                    return {"available": False, "provider": self.provider, "endpoint": self.endpoint, "models": [], "discovery": f"ollama list failed: {res.stderr.strip() or http_exc}"}
                source = "ollama list"
                for line in res.stdout.splitlines()[1:]:
                    parts = line.split()
                    if parts:
                        names.append(parts[0])
            except Exception as cli_exc:
                return {"available": False, "provider": self.provider, "endpoint": self.endpoint, "models": [], "discovery": f"Ollama probe failed locally: {cli_exc}"}
        unique = list(dict.fromkeys(names))
        return {"available": bool(unique), "provider": self.provider, "endpoint": self.endpoint, "models": unique, "model": unique[0] if unique else None, "discovery": f"local Ollama models discovered via {source}" if unique else f"no local Ollama models discovered via {source}"}

    def select_model(self, resident: str, models: list[str]) -> str | None:
        if _key(resident) == "alfred" and PREFERRED_ALFRED_MODEL in models:
            return PREFERRED_ALFRED_MODEL
        return models[0] if models else None

    def generate(self, *, resident: str, prompt: str, model: str | None = None) -> dict[str, Any]:
        discovery = self.discover_models()
        if not discovery.get("available"):
            return {"ok": False, "text": None, "metadata": _llm_metadata("deterministic_fallback", provider=self.provider, model=model, endpoint=self.endpoint, fallback_used=True, fallback_reason=discovery.get("discovery"))}
        selected = model or self.select_model(resident, discovery.get("models") or [])
        if not selected:
            return {"ok": False, "text": None, "metadata": _llm_metadata("deterministic_fallback", provider=self.provider, endpoint=self.endpoint, fallback_used=True, fallback_reason="No usable local Ollama model selected")}
        body = json.dumps({"model": selected, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}).encode("utf-8")
        req = urllib.request.Request(f"{self.endpoint}/api/generate", data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            text = str(payload.get("response") or "").strip()
            if not text:
                raise RuntimeError("Ollama returned an empty response")
            return {"ok": True, "text": text, "metadata": _llm_metadata("local_llm", provider=self.provider, model=selected, endpoint=self.endpoint, fallback_used=False, fallback_reason=None)}
        except Exception as exc:
            return {"ok": False, "text": None, "metadata": _llm_metadata("deterministic_fallback", provider=self.provider, model=selected, endpoint=self.endpoint, fallback_used=True, fallback_reason=f"Local Ollama invocation failed: {exc}")}


IMAGE_MIME_EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}
VISION_MODEL_HINTS = ("llava", "bakllava", "moondream", "minicpm-v", "qwen2-vl", "qwen2.5vl", "qwen-vl", "vision")

def _default_vision_config() -> dict[str, Any]:
    return {"provider":"ollama","endpoint":OLLAMA_ENDPOINT,"preferred_model":"llama3.2-vision:11b","fallback_behavior":"vision_unavailable","cloud_allowed":False}

def load_vision_config(root: Path | None = None) -> dict[str, Any]:
    base = _root(root) if root is not None else Path.cwd()
    cfg = _default_vision_config()
    path = base / VISION_CONFIG_PATH
    data = _read_json(path) if path.exists() else None
    if isinstance(data, dict):
        cfg.update({k: data.get(k) for k in cfg if k in data})
    cfg["config_path"] = str(VISION_CONFIG_PATH)
    cfg["cloud_allowed"] = False
    return cfg

def _model_metadata_indicates_vision(model: dict[str, Any]) -> bool:
    text = json.dumps(model, sort_keys=True).lower()
    return any(token in text for token in ("vision", "clip", "projector", "mmproj", "image", "llava"))

def is_vision_capable_model(name: str, metadata: dict[str, Any] | None = None) -> bool:
    lname = str(name or "").lower()
    return any(h in lname for h in VISION_MODEL_HINTS) or (isinstance(metadata, dict) and _model_metadata_indicates_vision(metadata))

class LocalVisionAdapter:
    """Local-only multimodal boundary; never calls cloud vision APIs."""

    provider = "ollama"

    def __init__(self, ollama: LocalOllamaAdapter | None = None, root: Path | None = None, config: dict[str, Any] | None = None):
        self.config = config or load_vision_config(root)
        endpoint = str(self.config.get("endpoint") or OLLAMA_ENDPOINT)
        self.ollama = ollama or LocalOllamaAdapter(endpoint=endpoint)

    def _show_model(self, name: str) -> dict[str, Any] | None:
        body = json.dumps({"name": name}).encode("utf-8")
        req = urllib.request.Request(f"{self.ollama.endpoint}/api/show", data=body, headers={"Content-Type":"application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=min(self.ollama.timeout, 4.0)) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None

    def discover_models(self) -> dict[str, Any]:
        status = self.ollama.discover_models()
        detected = status.get("models") or []
        metadata_by_model = {}
        models = []
        for m in detected:
            meta = self._show_model(m)
            if meta:
                metadata_by_model[m] = meta
            if is_vision_capable_model(m, meta):
                models.append(m)
        preferred = self.config.get("preferred_model")
        selected = preferred if preferred in models else (models[0] if models else None)
        return {**status, "available": bool(models), "detected_models": detected, "models": models, "vision_capable_models": models, "model": selected, "preferred_model": preferred, "configuration_path": self.config.get("config_path"), "cloud_allowed": False, "vision_capable": bool(models), "model_metadata": metadata_by_model, "discovery": ("local vision-capable Ollama models discovered" if models else "no local vision-capable model discovered")}

    def summarize_image(self, *, image_path: Path, prompt: str = "Describe the pasted image for a resident conversation.", model: str | None = None) -> dict[str, Any]:
        status = self.discover_models()
        selected = model or status.get("model")
        if not status.get("available") or not selected:
            return {"ok": False, "status": "unavailable", "summary": None, "provider": "none", "model": None, "reason": status.get("discovery")}
        try:
            encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
            body = json.dumps({"model": selected, "prompt": prompt, "images": [encoded], "stream": False, "options": {"temperature": 0.1}}).encode("utf-8")
            req = urllib.request.Request(f"{self.ollama.endpoint}/api/generate", data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=self.ollama.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            text = str(payload.get("response") or "").strip()
            if not text:
                raise RuntimeError("empty local vision response")
            return {"ok": True, "status": "processed", "summary": text, "provider": self.provider, "model": selected, "reason": None}
        except Exception as exc:
            return {"ok": False, "status": "failed", "summary": None, "provider": self.provider, "model": selected, "reason": f"Local vision invocation failed: {exc}"}

def local_vision_status(adapter: LocalVisionAdapter | None = None) -> dict[str, Any]:
    return (adapter or LocalVisionAdapter()).discover_models()

def _attachment_dir(root: Path, resident: str, sid: str) -> Path:
    return root / ATTACHMENT_STORE / _key(resident) / _safe(sid)

def _safe_attachment_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    return {k: meta.get(k) for k in ("attachment_id","kind","source","created_at","original_filename","mime_type","size_bytes","storage_path","sha256","redaction_status","vision_status","vision_provider","vision_model","summary") if k in meta}

def create_attachment(root: Path, resident: str, sid: str, item: dict[str, Any], *, index: int = 1, vision_adapter: LocalVisionAdapter | None = None) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("attachment must be an object")
    kind = item.get("kind")
    source = item.get("source") or "api"
    mime = str(item.get("mime_type") or ("text/plain" if kind == "text_snippet" else "")).lower()
    aid = f"attach_{index:04d}"
    folder = _attachment_dir(root, resident, sid); folder.mkdir(parents=True, exist_ok=True)
    if kind == "image":
        if mime not in IMAGE_MIME_EXT:
            raise ValueError("unsupported image mime type")
        raw = base64.b64decode(str(item.get("data_base64") or ""), validate=True)
        if not raw:
            raise ValueError("empty image attachment")
        filename = _safe(item.get("original_filename") or f"clipboard-image{IMAGE_MIME_EXT[mime]}")
        if not filename.lower().endswith(IMAGE_MIME_EXT[mime]): filename += IMAGE_MIME_EXT[mime]
        path = folder / f"{aid}_{filename}"
        path.write_bytes(raw)
        summary = None; vstatus = "not_attempted"; vprovider = "none"; vmodel = None
        vision = (vision_adapter or LocalVisionAdapter(root=root)).summarize_image(image_path=path, prompt=str(item.get("prompt") or "Describe this pasted resident conversation image."))
        vstatus = vision.get("status") or ("processed" if vision.get("ok") else "unavailable")
        vprovider = vision.get("provider") or "none"; vmodel = vision.get("model"); summary = vision.get("summary")
    elif kind == "text_snippet":
        text = str(item.get("text") or "")
        if not text.strip(): raise ValueError("empty text snippet")
        raw = text.encode("utf-8")
        mime = "text/plain"
        path = folder / f"{aid}_clipboard-text.txt"
        path.write_bytes(raw)
        summary = text[:500]; vstatus = "not_attempted"; vprovider = "none"; vmodel = None
    else:
        raise ValueError("unsupported attachment kind")
    rel = str(path.relative_to(root)).replace('\\','/')
    if not rel.startswith(str(ATTACHMENT_STORE).replace('\\','/') + "/"):
        raise ValueError("attachment storage escaped bounded directory")
    return {"attachment_id": aid, "kind": kind, "source": source, "created_at": _now(), "original_filename": _safe(item.get("original_filename") or path.name), "mime_type": mime, "size_bytes": len(raw), "storage_path": rel, "sha256": hashlib.sha256(raw).hexdigest(), "redaction_status": "active", "vision_status": vstatus, "vision_provider": vprovider, "vision_model": vmodel, "summary": summary}

def _llm_metadata(mode: str, *, provider="none", model=None, endpoint=None, fallback_used=False, fallback_reason=None):
    return {"mode": mode, "provider": provider or "none", "model": model, "endpoint": endpoint, "fallback_used": bool(fallback_used), "fallback_reason": fallback_reason}

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

def local_llm_status(adapter: LocalOllamaAdapter | None = None) -> dict[str, Any]:
    adapter = adapter or LocalOllamaAdapter()
    status = adapter.discover_models()
    models = status.get("models") or []
    status.update({"intended_mode":"local_llm", "model": adapter.select_model("alfred", models) if models else None})
    if not status.get("available"):
        status.setdefault("discovery", "deterministic fallback available")
    return status

def resident_surface(resident: str, root=None) -> dict[str, Any]:
    r = _root(root); key = _key(resident).replace("alfred-operations", "alfred")
    profile = RESIDENT_PROFILES.get(key, {"resident_id":key,"resident_display_name":str(resident).title(),"office":"Unassigned resident office","role":"Future resident","implementation_version":f"{key}-implementation-v1"})
    artifact = r / SURFACE_DIR / f"{key}.json"
    data = _read_json(artifact) if artifact.exists() else None
    caps = data.get("capabilities") if isinstance(data, dict) and isinstance(data.get("capabilities"), list) else DEFAULT_CAPABILITIES
    return {"kind":"resident_interaction_surface","resident_id":profile["resident_id"],"resident_display_name":profile["resident_display_name"],"office":profile["office"],"role":profile["role"],"resident_api_standard_version":STANDARD_VERSION,"resident_implementation_version":profile["implementation_version"],"surface_reference":str((SURFACE_DIR / f"{key}.json")).replace('\\','/'),"capabilities":caps,"chat_endpoints":{"get":"GET /api/residents/{resident_id}/chat","post":"POST /api/residents/{resident_id}/chat JSON with optional attachments[] base64/text payloads","forget":"POST /api/residents/{resident_id}/forget","surface":"GET /api/residents/{resident_id}/surface"},"extension_mechanism":{"proposal_template":"docs/operations/residents/resident_api_extension_proposal_template.md","profile_template":"docs/operations/residents/resident_implementation_profile_template.md","rule":"Add or change capabilities through reviewed resident surface/profile artifacts; do not hide one-off UI-only actions."}}

def _next_session_id(root, resident):
    day = datetime.now(timezone.utc).strftime("%Y%m%d"); folder = root/CHAT_STORE; folder.mkdir(parents=True, exist_ok=True)
    n = len(list(folder.glob(f"{_key(resident)}_steward_{day}_*.json"))) + 1
    return f"{_key(resident)}_steward_{day}_{n:03d}"

def _session_path(root, sid): return root/CHAT_STORE/f"{_safe(sid)}.json"

def _artifact_hint(root: Path, rel: str) -> str | None:
    path = root / rel
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return rel
    line = next((ln.strip("# |") for ln in text.splitlines() if ln.strip()), rel)
    return f"{rel}: {line[:120]}"

def _context_packet(root: Path, resident: str, session: dict[str, Any] | None = None) -> dict[str, Any]:
    artifacts = []
    for rel in (
        "runtime/validation/production_readiness.json",
        "runtime/validation/local_operational_validation_run.json",
        "runtime/work_packages/assignment_queue.json",
        "operations/residents/surfaces/alfred.json",
        "operations/departments/engineering/cuemastery_execution_handoff.md",
    ):
        hint = _artifact_hint(root, rel)
        artifacts.append({"path": rel, "available": bool(hint), "summary": hint or "unavailable"})
    turns = []
    for t in (session or {}).get("turns", [])[-4:]:
        if t.get("memory_status", "active") == "active":
            turns.append({"user": str(t.get("user_message") or "")[:240], "resident": str(t.get("resident_response") or "")[:240]})
    pending = [str(p.relative_to(root)).replace('\\','/') for p in sorted((root/"collaboration/work_packages/pending").glob("WP-*.md"))[:8]] if (root/"collaboration/work_packages/pending").exists() else []
    return {"artifacts": artifacts, "recent_history": turns, "pending_work_packages": pending}

def _alfred_prompt(message: str, surface: dict[str, Any], auth: dict[str, Any], context: dict[str, Any], llm_meta: dict[str, Any]) -> str:
    caps = [c.get("id") for c in surface.get("capabilities", [])]
    return "\n".join([
        "You are Alfred, resident of the Estate, Office of Operations.",
        "You are speaking with Pat, the Steward.",
        "Answer the actual question asked. Do not repeat the same generic status summary unless the Steward asked for status.",
        "Use local Estate context when relevant. Do not claim to have executed privileged actions.",
        "If asked about your mode, explain whether this response is local_llm or deterministic_fallback based on metadata available to you.",
        "If you do not know something, say what you can verify from local artifacts and what remains unknown.",
        f"Resident metadata: {json.dumps({k: surface.get(k) for k in ['resident_id','resident_display_name','office','role','resident_api_standard_version','resident_implementation_version']}, sort_keys=True)}",
        f"Allowed capabilities: {json.dumps(caps, sort_keys=True)}",
        f"Authority status for requested action: {json.dumps(auth, sort_keys=True)}",
        f"Response metadata available to you: {json.dumps(llm_meta, sort_keys=True)}",
        f"Bounded Estate context packet: {json.dumps(context, sort_keys=True)[:4000]}",
        f"Steward message: {message}",
        "Respond as Alfred in concise, direct prose.",
    ])

def _fallback_response(resident, message, surface, root: Path | None = None):
    if surface.get("resident_id") == "alfred":
        hints = []
        if root is not None:
            for rel in (
                "runtime/validation/production_readiness.json",
                "runtime/validation/local_operational_validation_run.json",
                "operations/boards/active_work.md",
                "operations/boards/daily_board.md",
                "operations/work_packages/assignment_queue.md",
                "operations/departments/engineering/cuemastery_execution_handoff.md",
            ):
                hint = _artifact_hint(root, rel)
                if hint:
                    hints.append(hint)
        context = "; ".join(hints[:3]) if hints else "local Estate context is available through validation, work-package, resident, and Operations Center artifacts as they are generated."
        return (
            "Good morning, Pat. Current Estate status: " + context + " "
            "Recommended next action: review the validation/production-readiness signal first, then the pending work-package queue and Engineering/CueMastery handoff if present. "
            "I can summarize, recommend, and propose actions from local artifacts through the resident interaction framework, but I will not execute privileged actions or claim Steward authorization from this chat. "
            f"Prompt received: {message[:180]}"
        )
    return f"{surface['resident_display_name']} received your message locally. I can discuss, recommend, or propose actions within my resident surface, but I will not execute work or claim authorization from this chat. Prompt summary: {message[:180]}"

def process_chat(resident: str, user_message: str, *, session_id: str|None=None, participant_role="Steward", action: str="summarize", root=None, attachments: list[dict[str, Any]] | None=None, vision_adapter: LocalVisionAdapter | None=None) -> dict[str, Any]:
    rootp = _root(root); surface = resident_surface(resident, rootp); sid = session_id or _next_session_id(rootp, resident)
    existing = _read_json(_session_path(rootp, sid)) or {"kind":"resident_interaction_session","session_id":sid,"resident_id":surface["resident_id"],"resident_display_name":surface["resident_display_name"],"created_at":_now(),"turns":[],"memory_status":"active"}
    turn_no = len(existing.get("turns", [])) + 1
    attachment_records = [create_attachment(rootp, surface["resident_id"], sid, item, index=i+1, vision_adapter=vision_adapter) for i, item in enumerate(attachments or [])]
    llm_status = local_llm_status()
    auth = check_authority(surface["resident_id"], action, root=rootp, audit=True)
    status = "within_responsibility" if auth.get("decision")==ALLOWED else ("requires_steward_authorization" if auth.get("decision")==REQUIRES_STEWARD else "blocked" if not auth.get("allowed") else "conversation_only")
    auth_record = {"action_requested": action not in {"summarize","observe","conversation"},"action_executed":False,"authority_status":status,"authority_reference":"src/estate/core/resident_authority.py","decision":auth.get("decision")}
    adapter = LocalOllamaAdapter()
    base_meta = _llm_metadata("local_llm", provider="ollama", model=llm_status.get("model"), endpoint=llm_status.get("endpoint") or OLLAMA_ENDPOINT, fallback_used=False, fallback_reason=None)
    context_packet = _context_packet(rootp, resident, existing)
    if attachment_records:
        context_packet["attachments"] = [_safe_attachment_metadata(a) for a in attachment_records]
        summaries = [a.get("summary") for a in attachment_records if a.get("kind") == "image" and a.get("vision_status") == "processed" and a.get("summary")]
        if summaries:
            user_message_for_prompt = user_message + "\nLocal image summaries: " + " | ".join(summaries)
        else:
            user_message_for_prompt = user_message + "\nAttachment note: pasted image/text artifacts were received and stored locally; visual inspection is unavailable unless a local vision model processed them."
    else:
        user_message_for_prompt = user_message
    prompt = _alfred_prompt(user_message_for_prompt, surface, auth_record, context_packet, base_meta) if surface.get("resident_id") == "alfred" else user_message_for_prompt
    generated = adapter.generate(resident=surface["resident_id"], prompt=prompt, model=llm_status.get("model")) if llm_status.get("available") else {"ok": False, "metadata": _llm_metadata("deterministic_fallback", provider=llm_status.get("provider"), model=llm_status.get("model"), endpoint=llm_status.get("endpoint") or OLLAMA_ENDPOINT, fallback_used=True, fallback_reason=llm_status.get("discovery") or "Local Ollama unavailable")}
    llm_meta = generated.get("metadata") or base_meta
    response = generated.get("text") if generated.get("ok") else _fallback_response(resident, user_message, surface, rootp)
    if attachment_records and any(a.get("kind") == "image" and a.get("vision_status") != "processed" for a in attachment_records):
        response += "\n\nAttachment note: I received and stored the pasted image locally, but no local vision-capable model is available to visually inspect it yet."
    elif attachment_records and any(a.get("kind") == "image" and a.get("summary") for a in attachment_records) and not generated.get("ok"):
        response += "\n\nLocal image observation: " + " | ".join(a.get("summary") for a in attachment_records if a.get("summary"))
    turn = {"session_id":sid,"turn_id":f"turn_{turn_no:04d}","resident_id":surface["resident_id"],"resident_display_name":surface["resident_display_name"],"participant_role":participant_role,"created_at":_now(),"user_message":user_message,"resident_response":response,"context_used":[surface["surface_reference"],"src/estate/core/resident_authority.py","bounded_estate_context_packet"],"llm":llm_meta,"resident_surface":{"resident_api_standard_version":surface["resident_api_standard_version"],"resident_implementation_version":surface["resident_implementation_version"],"allowed_capabilities":[c["id"] for c in surface["capabilities"]],"surface_reference":surface["surface_reference"]},"authority":auth_record,"attachments":[_safe_attachment_metadata(a) for a in attachment_records],"memory_status":"active"}
    existing.setdefault("turns", []).append(turn); existing["updated_at"]=_now(); existing["memory_status"]="active"; existing["normal_history"]=[t for t in existing["turns"] if t.get("memory_status")=="active"]
    path = _session_path(rootp, sid); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(existing, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return {"ok":True,"session_id":sid,"turn":turn,"session_path":str(path.relative_to(rootp)).replace('\\','/'),"llm_discovery":llm_status}

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
            for a in t.get("attachments", []) or []:
                a["redaction_status"] = memory_status
                a["summary"] = None
    data["memory_status"] = memory_status if turn_id is None else data.get("memory_status","active")
    data["normal_history"]=[t for t in data.get("turns", []) if t.get("memory_status")=="active"]; data["updated_at"]=_now(); path.write_text(json.dumps(data, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    audit={"kind":"resident_conversation_forget_audit","session_id":session_id,"turn_id":turn_id,"affected_turns":affected,"memory_status":memory_status,"reason":reason,"created_at":_now(),"content_preserved_in_normal_history":False}
    ap=rootp/FORGET_AUDIT; ap.parent.mkdir(parents=True, exist_ok=True); ap.open("a",encoding="utf-8").write(json.dumps(audit, sort_keys=True)+"\n")
    return {"ok":True, **audit, "audit_path":str(FORGET_AUDIT)}
