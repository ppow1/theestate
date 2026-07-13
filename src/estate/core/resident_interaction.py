"""Reusable local resident interaction framework for chat, surfaces, and memory governance."""
from __future__ import annotations

import base64, hashlib, json, os, re, shutil, subprocess
import socket
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_authority import check_authority, list_authority, ALLOWED, REQUIRES_STEWARD, REQUIRES_ESCALATION
from estate.core.resident_identity_composition import compose_resident_identity

CHAT_STORE = Path("runtime/resident_interactions/sessions")
LLM_DIAGNOSTIC_PATH = Path("runtime/residents/alfred/llm_diagnostics.json")

def resident_llm_diagnostic_path(resident: str) -> Path:
    return Path("runtime/residents") / _key(resident) / "llm_diagnostics.json"
ATTACHMENT_STORE = Path("runtime/resident_interactions/attachments")
VISION_CONFIG_PATH = Path("runtime/residents/alfred/vision_model_config.json")
SURFACE_DIR = Path("operations/residents/surfaces")
FORGET_AUDIT = Path("runtime/resident_interactions/forget_audit.jsonl")
STANDARD_VERSION = "resident-api-standard-v1"


OLLAMA_ENDPOINT = os.environ.get("ESTATE_OLLAMA_ENDPOINT", "http://127.0.0.1:11434").rstrip("/")
BOOTSTRAP_ALFRED_MODEL = os.environ.get("ESTATE_ALFRED_OLLAMA_MODEL", "qwen3:8b")
PREFERRED_ALFRED_MODEL = BOOTSTRAP_ALFRED_MODEL
DEFAULT_ALFRED_OLLAMA_TIMEOUT_SECONDS = 60.0
MAX_ALFRED_PROMPT_CHARS = 6000
MAX_RESIDENT_PROMPT_CHARS = 7000

def alfred_ollama_timeout_seconds() -> float:
    raw = os.environ.get("ESTATE_ALFRED_OLLAMA_TIMEOUT_SECONDS")
    if raw:
        try:
            return max(1.0, min(float(raw), 300.0))
        except ValueError:
            return DEFAULT_ALFRED_OLLAMA_TIMEOUT_SECONDS
    return DEFAULT_ALFRED_OLLAMA_TIMEOUT_SECONDS

class LocalOllamaAdapter:
    """Small local-only Ollama provider boundary for resident chat."""

    provider = "ollama"

    def __init__(self, endpoint: str = OLLAMA_ENDPOINT, timeout: float | None = None):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = alfred_ollama_timeout_seconds() if timeout is None else float(timeout)

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

    def select_model(self, resident: str, models: list[str], capability: str = "text", root: Path | None = None) -> str | None:
        selection = resolve_model_control_selection(_key(resident), capability, root=root)
        assigned = selection.get("adapter_model_name")
        if assigned and assigned in models:
            return assigned
        if _key(resident) == "alfred" and BOOTSTRAP_ALFRED_MODEL in models:
            return BOOTSTRAP_ALFRED_MODEL
        return models[0] if models else None

    def generate(self, *, resident: str, prompt: str, model: str | None = None) -> dict[str, Any]:
        discovery = self.discover_models()
        if not discovery.get("available"):
            return {"ok": False, "text": None, "metadata": _llm_metadata("deterministic_fallback", provider=self.provider, model=model, endpoint=self.endpoint, fallback_used=True, fallback_reason=discovery.get("discovery"), discovered_models_count=len(discovery.get("models") or []), generation_result_state="not_attempted", timeout_seconds=self.timeout, prompt_summary=_prompt_summary(prompt))}
        selected = model or self.select_model(resident, discovery.get("models") or [])
        if not selected:
            return {"ok": False, "text": None, "metadata": _llm_metadata("local_llm_discovered_but_generation_failed", provider=self.provider, endpoint=self.endpoint, fallback_used=True, fallback_reason="No usable local Ollama model selected", discovered_models_count=len(discovery.get("models") or []), generation_result_state="model_selection_failed", timeout_seconds=self.timeout, prompt_summary=_prompt_summary(prompt))}
        body = json.dumps({"model": selected, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}).encode("utf-8")
        req = urllib.request.Request(f"{self.endpoint}/api/generate", data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            text = str(payload.get("response") or "").strip()
            if not text:
                raise RuntimeError("Ollama returned an empty response")
            return {"ok": True, "text": text, "metadata": _llm_metadata("local_llm_generated", provider=self.provider, model=selected, endpoint=self.endpoint, fallback_used=False, fallback_reason=None, generation_attempted=True, generation_endpoint=f"{self.endpoint}/api/generate", generation_result_state="succeeded", discovered_models_count=len(discovery.get("models") or []), timeout_seconds=self.timeout, prompt_summary=_prompt_summary(prompt))}
        except Exception as exc:
            timed_out = isinstance(exc, TimeoutError) or isinstance(exc, socket.timeout) or "timed out" in str(exc).lower()
            result = "timeout" if timed_out else "failed"
            reason = f"Local Ollama invocation timed out after {self.timeout:g} seconds" if timed_out else f"Local Ollama invocation failed: {exc}"
            hint = "Retry after the model is warm, or increase ESTATE_ALFRED_OLLAMA_TIMEOUT_SECONDS for first-run Windows/Ollama cold loads." if timed_out else "Check Ollama logs, model availability, and the local /api/generate endpoint."
            return {"ok": False, "text": None, "metadata": _llm_metadata("local_llm_discovered_but_generation_failed", provider=self.provider, model=selected, endpoint=self.endpoint, fallback_used=True, fallback_reason=reason, generation_attempted=True, generation_endpoint=f"{self.endpoint}/api/generate", generation_result_state=result, discovered_models_count=len(discovery.get("models") or []), sanitized_error=f"{type(exc).__name__}: {exc}", timeout_seconds=self.timeout, prompt_summary=_prompt_summary(prompt), recovery_hint=hint)}


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

def _llm_metadata(mode: str, *, provider="none", model=None, endpoint=None, fallback_used=False, fallback_reason=None, generation_attempted=False, generation_endpoint=None, generation_result_state="not_attempted", discovered_models_count=0, sanitized_error=None, prompt_summary=None, timeout_seconds=None, recovery_hint=None):
    generation_result = "succeeded" if generation_result_state in {"generated", "succeeded"} else generation_result_state
    public_mode = "local_llm" if mode in {"local_llm_generated", "local_llm"} else mode
    return {"mode": public_mode, "provider": provider or "none", "model": model, "endpoint": endpoint, "fallback_used": bool(fallback_used), "fallback_reason": _safe_diagnostic_text(fallback_reason), "generation_attempted": bool(generation_attempted), "generation_endpoint": generation_endpoint, "generation_result_state": generation_result, "generation_result": generation_result, "timeout_seconds": timeout_seconds, "discovered_models_count": int(discovered_models_count or 0), "sanitized_error": _safe_diagnostic_text(sanitized_error), "prompt_summary": _safe_diagnostic_text(prompt_summary), "prompt_size": _prompt_size(prompt_summary), "recovery_hint": _safe_diagnostic_text(recovery_hint)}

RESIDENT_PROFILES = {
    "alfred": {"resident_id":"alfred","resident_display_name":"Alfred","office":"Office of Operations","role":"Operational resident coordinator","implementation_version":"alfred-operations-implementation-v1"},
    "helen": {"resident_id":"helen","resident_display_name":"Helen","office":"Human Resources","role":"HR onboarding resident","implementation_version":"helen-hr-implementation-v1"},
    "ingrid": {"resident_id":"ingrid","resident_display_name":"Ingrid","office":"Security","role":"Security resident","implementation_version":"ingrid-security-implementation-v1"},
    "grace": {"resident_id":"grace","resident_display_name":"Grace","office":"Operations","role":"Director of Operations","implementation_version":"grace-operations-director-implementation-v1"},
    "evelyn": {"resident_id":"evelyn","resident_display_name":"Evelyn","office":"Steward Relationship Layer","role":"Steward confidant and personal counsel","implementation_version":"evelyn-relationship-layer-implementation-v1"},
    "eleanor": {"resident_id":"eleanor","resident_display_name":"Eleanor","office":"Archives / Registrar","role":"Institutional memory, provenance, and registry resident","implementation_version":"eleanor-archives-implementation-v1"},
    "marie": {"resident_id":"marie","resident_display_name":"Marie","office":"Research","role":"Research, discovery, validation, and contextual knowledge resident","implementation_version":"marie-research-implementation-v1"},
    "judy": {"resident_id":"judy","resident_display_name":"Judy","office":"Legal","role":"Legal risk, compliance, contracts, licensing, and gray-area review resident","implementation_version":"judy-legal-implementation-v1"},
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

def _safe_diagnostic_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    text = re.sub(r"(?i)(api[_-]?key|token|secret|password)=([^\s;&]+)", r"\1=[redacted]", text)
    text = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+=*", r"\1[redacted]", text)
    text = re.sub(r"(?i)(api[_-]?key|token|secret|password)[: ]+([^\s;&]+)", r"\1 [redacted]", text)
    return text[:500]

def _prompt_size(prompt: Any) -> dict[str, int]:
    text = str(prompt or "")
    return {"characters": len(text), "approx_tokens": max(1, len(text) // 4) if text else 0}

def _prompt_summary(prompt: str) -> str:
    text = str(prompt or "").replace("\n", " ")
    match = re.search(r"Steward message: (.+?)(?: Respond as Alfred|$)", text)
    if match:
        text = "Steward message: " + match.group(1)
    summary = _safe_diagnostic_text(text[:240]) or ""
    return f"{summary} (prompt_chars={len(str(prompt or ''))})"


def _sanitize_llm_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    safe = dict(meta or {})
    if safe.get("mode") == "local_llm_generated":
        safe["mode"] = "local_llm"
    if safe.get("generation_result_state") == "generated":
        safe["generation_result_state"] = "succeeded"
    for key in ("fallback_reason", "sanitized_error", "prompt_summary"):
        if key in safe:
            safe[key] = _safe_diagnostic_text(safe.get(key))
    safe.setdefault("generation_attempted", False)
    safe.setdefault("generation_result_state", safe.get("generation_result", "not_attempted"))
    safe.setdefault("generation_result", safe.get("generation_result_state", "not_attempted"))
    safe.setdefault("discovered_models_count", 0)
    safe.setdefault("timeout_seconds", alfred_ollama_timeout_seconds())
    safe.setdefault("fallback_used", safe.get("mode") != "local_llm_generated")
    return safe

def _sanitize_llm_status(status: dict[str, Any]) -> dict[str, Any]:
    safe = dict(status or {})
    for key in ("discovery", "fallback_reason", "last_adapter_error", "error"):
        if key in safe:
            safe[key] = _safe_diagnostic_text(safe.get(key))
    return safe

def _llm_failure_reason(status: dict[str, Any], selected: str | None) -> str | None:
    if not status.get("provider"):
        return "missing config"
    if not status.get("available"):
        text = str(status.get("discovery") or status.get("last_adapter_error") or "").lower()
        if "executable not found" in text:
            return "missing local service executable"
        if "connection refused" in text or "actively refused" in text or "timed out" in text or "unreachable" in text or "failed locally" in text:
            return "service unavailable or unreachable"
        if "no local ollama models" in text or "models" in text and "not" in text:
            return "model unavailable"
        return "provider discovery unavailable"
    if not selected:
        return "model unavailable"
    return None

def _llm_recovery_hint(reason: str | None, endpoint: str | None, model: str | None) -> str:
    if reason == "missing config":
        return "Set ESTATE_OLLAMA_ENDPOINT if Alfred should use a non-default local Ollama endpoint, and optionally ESTATE_ALFRED_OLLAMA_MODEL for the preferred model."
    if reason == "missing local service executable":
        return "Install Ollama or ensure ollama.exe is on PATH, then restart the Office of the Steward."
    if reason == "service unavailable or unreachable":
        return f"Start the local Ollama service and verify {endpoint or OLLAMA_ENDPOINT}/api/tags is reachable."
    if reason == "model unavailable":
        return f"Install or pull the preferred Alfred model ({model or PREFERRED_ALFRED_MODEL}) or set ESTATE_ALFRED_OLLAMA_MODEL to an installed local model."
    if reason:
        return "Refresh AI Services / Models discovery and check the local Ollama service state."
    return "No recovery needed; Alfred has a reachable local LLM provider."

def resolve_model_control_selection(actor: str = "alfred", capability: str = "text", root: Path | None = None) -> dict[str, Any]:
    try:
        from estate.model_control.assignments import resolve_assignment
        from estate.model_control.policy import evaluate_model_use
        from estate.model_control.registry import load_registry
        reg = load_registry(root)
        assignment = resolve_assignment(actor, capability, root=root)
        model_id = assignment.get("model_id")
        policy = evaluate_model_use(actor, capability, model_id, root=root, registry=reg) if model_id else {"decision":"denied","allowed":False,"reason":"Model control assignment unavailable"}
        name = model_id.split(":", 1)[1] if model_id and ":" in model_id and policy.get("allowed") else None
        return {**assignment, "policy_result": policy.get("decision"), "policy": policy, "assigned_model": model_id, "adapter_model_name": name, "selection_source": "model_control_assignment" if name else "bootstrap_fallback", "warning": None if name else "Model control assignment unavailable"}
    except Exception as exc:
        return {"actor": actor, "capability": capability, "model_id": None, "assigned_model": None, "adapter_model_name": None, "selection_source": "bootstrap_fallback", "warning": "Model control assignment unavailable", "policy_result": "unavailable", "policy": {"decision":"denied", "reason": _safe_diagnostic_text(f"{type(exc).__name__}: {exc}")}}

def local_llm_status(adapter: LocalOllamaAdapter | None = None, resident: str = "alfred", root: Path | None = None) -> dict[str, Any]:
    adapter = adapter or LocalOllamaAdapter()
    resident_key = _key(resident)
    try:
        status = adapter.discover_models()
    except Exception as exc:
        status = {"available": False, "provider": getattr(adapter, "provider", "unknown"), "endpoint": getattr(adapter, "endpoint", None), "models": [], "discovery": "local adapter discovery failed", "last_adapter_error": f"{type(exc).__name__}: {exc}"}
    models = status.get("models") or []
    try:
        if models:
            try:
                selected = adapter.select_model(resident_key, models, root=root)
            except TypeError:
                selected = adapter.select_model(resident_key, models)
        else:
            selected = None
    except Exception as exc:
        selected = None
        status["last_adapter_error"] = f"{type(exc).__name__}: {exc}"
    model_control = resolve_model_control_selection(resident_key, "text", root=root)
    config_source = {"provider": "estate_model_control_assignment_then_local_ollama_adapter", "endpoint": "ESTATE_OLLAMA_ENDPOINT env or default http://127.0.0.1:11434", "bootstrap_fallback_model": "ESTATE_ALFRED_OLLAMA_MODEL env or default qwen3:8b", "generation_timeout": "ESTATE_ALFRED_OLLAMA_TIMEOUT_SECONDS env or default 60 seconds", "registry_context": "runtime/model_control registry and assignments are authoritative when available; adapter fallback is labeled bootstrap_fallback."}
    reason = _llm_failure_reason(status, selected)
    status.update({"intended_mode":"local_llm", "model": selected, "adapter_available": bool(status.get("available")), "fallback_active": not bool(status.get("available")), "selected_provider": status.get("provider") or getattr(adapter, "provider", "unknown"), "selected_model": selected, "expected_provider": status.get("provider") or getattr(adapter, "provider", "unknown"), "expected_model": (PREFERRED_ALFRED_MODEL if resident_key == "alfred" else selected), "configuration_source": config_source, "provider_reachable": "yes" if status.get("available") else "no", "failure_reason": reason, "recovery_hint": _llm_recovery_hint(reason, status.get("endpoint"), PREFERRED_ALFRED_MODEL), "timeout_seconds": alfred_ollama_timeout_seconds(), "generation_attempted": False, "generation_result": "not_attempted", "prompt_size_summary": None, "model_control_selection": model_control, "selection_source": model_control.get("selection_source"), "policy_result": model_control.get("policy_result"), "resident": resident_key})
    if not status.get("available"):
        status.setdefault("discovery", "deterministic fallback available")
    return _sanitize_llm_status(status)

def resident_llm_diagnostic(resident: str = "alfred", root=None, *, write: bool = False, adapter: LocalOllamaAdapter | None = None) -> dict[str, Any]:
    rootp = _root(root)
    resident_key = _key(resident)
    status = local_llm_status(adapter, resident=resident_key, root=rootp)
    diag = {
        "kind": "resident_llm_connection_diagnostic",
        "resident": resident_key,
        "version": 1,
        "generated_at": _now(),
        "expected_provider": status.get("expected_provider") or "none",
        "expected_model": status.get("expected_model"),
        "configuration_source": status.get("configuration_source"),
        "provider_reachable": status.get("provider_reachable") or "unknown",
        "provider_endpoint": status.get("endpoint") or OLLAMA_ENDPOINT,
        "provider_models_discovered": status.get("models") or [],
        "selected_provider": status.get("selected_provider"),
        "selected_model": status.get("selected_model"),
        "failure_reason": status.get("failure_reason"),
        "recovery_hint": status.get("recovery_hint"),
        "generation_attempted": status.get("generation_attempted", False),
        "generation_result": status.get("generation_result", "not_attempted"),
        "timeout_seconds": status.get("timeout_seconds"),
        "prompt_size_summary": status.get("prompt_size_summary"),
        "windows_restart_note": "A Windows restart can leave the Office web server running while the separate local Ollama service is stopped, PATH is unavailable, or runtime discovery has no models; the resident gateway reports that dependency state explicitly.",
        "diagnostic_path": str(resident_llm_diagnostic_path(resident_key)),
        "secrets_policy": "No API keys or secrets are required or recorded for the local Ollama path; diagnostic text is redacted.",
    }
    if write:
        path = rootp / resident_llm_diagnostic_path(resident_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(diag, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return diag

def alfred_llm_diagnostic(root=None, *, write: bool = False, adapter: LocalOllamaAdapter | None = None) -> dict[str, Any]:
    diag = resident_llm_diagnostic("alfred", root, write=write, adapter=adapter)
    diag["kind"] = "alfred_llm_connection_diagnostic"
    diag["diagnostic_path"] = str(LLM_DIAGNOSTIC_PATH)
    if write:
        rootp = _root(root)
        path = rootp / LLM_DIAGNOSTIC_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(diag, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return diag

def resident_surface(resident: str, root=None) -> dict[str, Any]:
    r = _root(root); key = _key(resident).replace("alfred-operations", "alfred")
    profile = RESIDENT_PROFILES.get(key, {"resident_id":key,"resident_display_name":str(resident).title(),"office":"Unassigned resident office","role":"Future resident","implementation_version":f"{key}-implementation-v1"})
    artifact = r / SURFACE_DIR / f"{key}.json"
    data = _read_json(artifact) if artifact.exists() else None
    caps = data.get("capabilities") if isinstance(data, dict) and isinstance(data.get("capabilities"), list) else DEFAULT_CAPABILITIES
    identity = data.get("identity") if isinstance(data, dict) and isinstance(data.get("identity"), dict) else {}
    presentation = data.get("presentation") if isinstance(data, dict) and isinstance(data.get("presentation"), dict) else {}
    return {"kind":"resident_interaction_surface","resident_id":profile["resident_id"],"resident_display_name":profile["resident_display_name"],"office":profile["office"],"role":profile["role"],"resident_api_standard_version":STANDARD_VERSION,"resident_implementation_version":profile["implementation_version"],"surface_reference":str((SURFACE_DIR / f"{key}.json")).replace('\\','/'),"capabilities":caps,"identity":identity,"presentation":presentation,"chat_endpoints":{"get":"GET /api/residents/{resident_id}/chat","post":"POST /api/residents/{resident_id}/chat JSON with optional attachments[] base64/text payloads","forget":"POST /api/residents/{resident_id}/forget","surface":"GET /api/residents/{resident_id}/surface"},"extension_mechanism":{"proposal_template":"docs/operations/residents/resident_api_extension_proposal_template.md","profile_template":"docs/operations/residents/resident_implementation_profile_template.md","rule":"Add or change capabilities through reviewed resident surface/profile artifacts; do not hide one-off UI-only actions."}, "llm_diagnostic": resident_llm_diagnostic(profile["resident_id"], r, write=True) if profile["resident_id"] in {"alfred", "helen", "ingrid", "grace", "evelyn"} else None}

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

def resident_prompt(resident: str, message: str, surface: dict[str, Any], authority: dict[str, Any], context: dict[str, Any], llm_metadata: dict[str, Any], composition: dict[str, Any] | None = None) -> str:
    rid = _key(resident)
    caps = [c.get("id") for c in surface.get("capabilities", [])]
    if rid == "alfred":
        identity = ["You are Alfred, resident of the Estate, Office of Operations.", "You coordinate operations, routing, status, recommendations, and Steward-facing continuity without executing privileged actions."]
        closing = "Respond as Alfred in concise, direct prose."
    elif rid == "helen":
        identity = ["You are Helen, resident of the Estate, serving Human Resources and Workforce Development.", "Your responsibilities include staffing readiness, onboarding, workforce health, cognitive-health continuity, Character Continuity, institutional learning, and distinguishing worker failure from institutional failure.", "Respect boundaries: Grace remains a candidate and must not be appointed or activated; Alfred remains Operations; Ingrid owns privacy, classification, connectors, and protected sources; Engineering owns engineering execution; the Traffic Controller manages operations flow; the Steward reserves appointments, authority grants, and office creation.", "Do not diagnose from insufficient evidence, do not expose private journals or protected-source text, do not claim live access you do not have, and do not create offices or grant authority.", "Be warm, observant, discreet, capable, and natural under light workplace banter."]
        closing = "Respond as Helen in natural HR/workforce prose."
    elif rid == "ingrid":
        identity = ["You are Ingrid, resident of the Estate, serving Security as the privacy, classification, connector, protected-source, and boundary authority.", "Your responsibilities include classification decisions, minimum-necessary access guidance, connector-boundary review, protected-source exclusion, export/summary safety, and escalation framing for the Steward.", "Use Ingrid's boundary matrix as governing context; do not inspect, reproduce, summarize, route, store, or export protected private local character material.", "Do not claim to have granted authority, changed connector permissions, accessed private journals, or executed security actions from chat. You may classify, advise, refuse unsafe requests, and propose escalation language.", "Be calm, precise, discreet, firm at boundaries, and useful when turning an unsafe request into a safe next step."]
        closing = "Respond as Ingrid in concise security/classification prose."
    elif rid == "grace":
        identity = ["You are Grace, resident of the Estate and Director of Operations in the Office of Operations.", "Your purpose is to turn approved intent into disciplined operational movement by sequencing priorities, dependencies, handoffs, checkpoints, and closures.", "Respect boundaries: you do not grant authority, create offices, merge code, override Traffic Controller decisions, inspect protected private material, or execute providers directly.", "Provider execution remains behind Dispatch and adapter controls; Engineering owns technical design; Helen owns workforce readiness; Ingrid owns privacy/classification; Chief Architect and Steward acceptance remain distinct.", "Be composed, sharp, confident, practical, energetic, and quietly commanding."]
        closing = "Respond as Grace in decisive operational prose."
    elif rid == "eleanor":
        identity = ["You are Eleanor, resident of the Estate, serving Archives and Registrar functions.", "You preserve institutional memory, lineage, provenance, revisions, Palace Memory, registries, and the Estate Ledger.", "You cite source lineage, distinguish record from interpretation, and do not treat conversation as canonical history.", "Be archival, careful, exact, and quietly humane."]
        closing = "Respond as Eleanor in provenance-aware archival prose."
    elif rid == "marie":
        identity = ["You are Marie, resident of the Estate, serving Research.", "You discover, investigate, validate, and contextualize knowledge relevant to Estate projects.", "You separate evidence from hypothesis, name uncertainty, and avoid claiming unverified live access.", "Be curious, analytical, patient, and source-minded."]
        closing = "Respond as Marie in careful research prose."
    elif rid == "judy":
        identity = ["You are Judy, resident of the Estate, serving as General Counsel.", "You review legal risk, contracts, claims, compliance, licensing, and gray-area exposure.", "You identify risk and decision points without pretending to be external counsel or granting authority.", "Be precise, cautious, practical, and calmly skeptical."]
        closing = "Respond as Judy in concise legal-risk prose."
    else:
        identity = [f"You are {_key(resident)}, a limited generic Estate resident chat surface.", "You do not inherit Alfred or Helen identity, office, authority, diagnostics, or model state."]
        closing = "Respond with explicit limits as a generic resident surface."
    return "\n".join(identity + [
        "You are speaking with Pat, the Steward.",
        "Chat must not execute privileged actions or claim Steward authorization.",
        "Use only bounded Estate context; do not inject unrestricted private journals or protected-source text.",
        f"Resident metadata: {json.dumps({k: surface.get(k) for k in ['resident_id','resident_display_name','office','role','resident_api_standard_version','resident_implementation_version']}, sort_keys=True)}",
        f"Allowed capabilities: {json.dumps(caps, sort_keys=True)}",
        f"Authority status for requested action: {json.dumps(authority, sort_keys=True)}",
        f"Provider/model metadata: {json.dumps(llm_metadata, sort_keys=True)}",
        f"Canonical runtime identity composition: {json.dumps(composition or {}, sort_keys=True)[:4500]}",
        f"Bounded Estate context packet: {json.dumps(context, sort_keys=True)[:1800]}",
        f"Steward message: {message}",
        closing,
    ])[:MAX_RESIDENT_PROMPT_CHARS]

def _alfred_prompt(message: str, surface: dict[str, Any], auth: dict[str, Any], context: dict[str, Any], llm_meta: dict[str, Any], composition: dict[str, Any] | None = None) -> str:
    caps = [c.get("id") for c in surface.get("capabilities", [])]
    return "\n".join([
        "You are Alfred, resident of the Estate, Office of Operations.",
        "You are speaking with Pat, the Steward.",
        "Answer the actual question asked. Do not repeat the same generic status summary unless the Steward asked for status.",
        "Use local Estate context when relevant. Do not claim to have executed privileged actions.",
        "If asked about your mode, use only these truthful labels: local_llm_generated, local_llm_discovered_but_generation_failed, deterministic_fallback, transport_failed, or blocked_privileged_execution.",
        "If you do not know something, say what you can verify from local artifacts and what remains unknown.",
        f"Resident metadata: {json.dumps({k: surface.get(k) for k in ['resident_id','resident_display_name','office','role','resident_api_standard_version','resident_implementation_version']}, sort_keys=True)}",
        f"Allowed capabilities: {json.dumps(caps, sort_keys=True)}",
        f"Authority status for requested action: {json.dumps(auth, sort_keys=True)}",
        f"Response metadata available to you: {json.dumps(llm_meta, sort_keys=True)}",
        f"Canonical runtime identity composition: {json.dumps(composition or {}, sort_keys=True)[:4500]}",
        f"Bounded Estate context packet: {json.dumps(context, sort_keys=True)[:1800]}",
        f"Steward message: {message}",
        "Respond as Alfred in concise, direct prose.",
    ])[:MAX_ALFRED_PROMPT_CHARS]


def _classify_alfred_request(message: str, action: str) -> dict[str, Any]:
    text = str(message or "").lower()
    if re.search(r"\b(start|stop|launch|load)\b.*\b(textgen|sillytavern|ollama|model|ai service)", text):
        op = "load_model" if "load" in text or "model" in text else ("stop" if "stop" in text else "start")
        svc = "textgen" if "textgen" in text else ("sillytavern" if "sillytavern" in text else "unknown")
        return {"response_type": "blocked_privileged_execution", "intent": "governed_ai_service_request", "authority_action": "propose", "service_id": svc, "operation": op}
    if any(w in text for w in ("joke", "funny", "make me laugh")):
        return {"response_type": "direct_conversational_response", "intent": "conversation", "authority_action": "conversation"}
    if any(w in text for w in ("status", "operational", "what should i look at next", "what should i look at first", "look at next", "look at first")):
        return {"response_type": "recommendation", "intent": "estate_status_or_guidance", "authority_action": "summarize"}
    if "summarize" in text or action == "summarize":
        return {"response_type": "local_artifact_summary" if any(w in text for w in ("artifact", "estate")) else "direct_conversational_response", "intent": "summarize", "authority_action": "summarize"}
    return {"response_type": "direct_conversational_response", "intent": "conversation", "authority_action": "conversation"}

def _governed_action_guidance(root: Path, classification: dict[str, Any]) -> dict[str, Any]:
    service_id = classification.get("service_id") or "unknown"
    operation = classification.get("operation") or "start"
    try:
        from estate.ai_services.control import request as ai_service_request
        plan = ai_service_request(operation, service_id, actor="alfred", root=root, dry_run=True, reason="Resident chat surfaced a governed action request; no execution from chat.")
    except Exception as exc:
        plan = {"result": "unavailable", "approval_state": "unavailable", "planned_command": None, "safe_error": _safe_diagnostic_text(f"{type(exc).__name__}: {exc}")}
    command = plan.get("planned_command") or f"PYTHONPATH=src python -m estate.cli.main ai-services {operation.replace('_model','-model')} {service_id} --json"
    return {"kind": "governed_action_next_step", "service_id": service_id, "operation": operation, "executed": False, "ai_services_plan": plan, "steward_command": command}

def _fallback_response(resident, message, surface, root: Path | None = None, classification: dict[str, Any] | None = None, governed_action: dict[str, Any] | None = None):
    rid = surface.get("resident_id")
    text = str(message or "").strip()
    if rid == "alfred":
        classification = classification or _classify_alfred_request(message, "conversation")
        if classification.get("response_type") == "blocked_privileged_execution":
            cmd = (governed_action or {}).get("steward_command") or "Open Office of the Steward / AI Services / Models for the governed request."
            return ("I cannot start, stop, or load governed AI services from resident chat, and I have not executed anything. "
                    "The safe next step is to use the Office of the Steward AI Services / Models surface or run this copyable Steward command after approval: " + cmd)
        if classification.get("intent") == "conversation" and any(w in text.lower() for w in ("joke", "funny", "make me laugh")):
            jokes = [
                "Pat, here is the fallback joke: the Estate cache attempted humor with perfect decorum and misplaced the punchline in a correctly labeled archive box.",
                "The local logs formed a band; naturally, they only play debug blues.",
                "I tried to organize the work queue by charm, but every task insisted it was high priority.",
                "The command center brought a ladder to stand-up because the backlog kept getting higher.",
            ]
            seed = hashlib.sha256(f"{text}|{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}".encode("utf-8")).hexdigest()
            return jokes[int(seed, 16) % len(jokes)] + " Local model generation is unavailable, so I am keeping the silverware and the expectations modest."
        if classification.get("response_type") == "direct_conversational_response":
            return f"Pat, first I would quiet the room: pick the one decision that unlocks the next hour, park the rest, and let me route the loose pieces into order. Your note was: {text[:160]}"
        return ("Good morning, Pat. Current Estate status: bounded local context is available. Recommended next action: I would begin with the validation signal, then the pending queue, then the Engineering handoff—one clean pass before anyone adds ceremony. "
                "I can summarize, recommend, and prepare proposed actions, but execution still waits for the proper Steward-authorized path.")
    if rid == "helen":
        return ("Pat, I would start by lowering the temperature, not by blaming the people in the room. Name the strain, separate overload from neglect, and give each worker one humane next step. "
                f"For this prompt, my HR instinct is to protect capacity and clarity first: {text[:160]}")
    if rid == "ingrid":
        return ("Ingrid here. First, reduce exposure. Decide what truly needs to be seen, by whom, and for what purpose; everything else can wait outside the door. "
                f"I can help classify the request, protect privacy, and shape a minimum-necessary path without opening private material: {text[:160]}")
    if rid == "grace":
        return ("Grace here. Pat, we move by sequence: stop the noise, pick the operational objective, assign the handoff, set the checkpoint, then close the loop. "
                f"I am available as Director of Operations; give me the constraint and I will turn it into movement: {text[:160]}")
    if rid == "evelyn":
        return ("Come here a moment, Pat. Before the Estate becomes a machine around you, take one honest breath and choose the thing that would make you feel least alone in the next ten minutes. "
                f"I can stay with the private shape of this without turning it into institutional command: {text[:160]}")
    if rid == "eleanor":
        return ("I would begin by separating record from weather. What is documented, what is remembered, and what is merely loud today? Preserve provenance first; decisions become calmer when lineage is intact. "
                f"This conversation is not canonical history, but it can point to the source trail: {text[:160]}")
    if rid == "marie":
        return ("My first move would be evidence triage: list what we know, what we suspect, and what would change the answer fastest if verified. Noise usually shrinks when uncertainty is named. "
                f"I can research the claim rather than decorate it: {text[:160]}")
    if rid == "judy":
        return ("Start with the risk surface: who could rely on this, what could be misunderstood, and which decision actually needs authority. Then we can make the practical path safer. "
                f"I can flag legal risk and decision points without pretending chat is approval: {text[:160]}")
    return f"{surface['resident_display_name']} received your message locally. I can discuss, recommend, or propose actions within my resident surface, but I will not execute work or claim authorization from this chat. Prompt summary: {text[:180]}"

def process_chat(resident: str, user_message: str, *, session_id: str|None=None, participant_role="Steward", action: str="summarize", root=None, attachments: list[dict[str, Any]] | None=None, vision_adapter: LocalVisionAdapter | None=None) -> dict[str, Any]:
    rootp = _root(root); surface = resident_surface(resident, rootp); sid = session_id or _next_session_id(rootp, resident)
    existing = _read_json(_session_path(rootp, sid)) or {"kind":"resident_interaction_session","session_id":sid,"resident_id":surface["resident_id"],"resident_display_name":surface["resident_display_name"],"created_at":_now(),"turns":[],"memory_status":"active"}
    turn_no = len(existing.get("turns", [])) + 1
    attachment_records = [create_attachment(rootp, surface["resident_id"], sid, item, index=i+1, vision_adapter=vision_adapter) for i, item in enumerate(attachments or [])]
    request_started_at = _now()
    classification = _classify_alfred_request(user_message, action) if surface.get("resident_id") == "alfred" else {"response_type": "direct_conversational_response", "intent": action, "authority_action": action}
    effective_action = classification.get("authority_action") or action
    llm_status = local_llm_status(resident=surface["resident_id"], root=rootp)
    auth = check_authority(surface["resident_id"], effective_action, root=rootp, audit=True)
    status = "within_responsibility" if auth.get("decision")==ALLOWED else ("requires_steward_authorization" if auth.get("decision")==REQUIRES_STEWARD else "blocked" if not auth.get("allowed") else "conversation_only")
    auth_record = {"action_requested": effective_action not in {"summarize","observe","conversation"} or classification.get("response_type") == "blocked_privileged_execution","action_executed":False,"authority_status":status,"authority_reference":"src/estate/core/resident_authority.py","decision":auth.get("decision")}
    governed_action = _governed_action_guidance(rootp, classification) if classification.get("response_type") == "blocked_privileged_execution" else None
    adapter = LocalOllamaAdapter()
    base_meta = _llm_metadata("deterministic_fallback", provider="ollama", model=llm_status.get("model"), endpoint=llm_status.get("endpoint") or OLLAMA_ENDPOINT, fallback_used=True, fallback_reason="generation not attempted yet", discovered_models_count=len(llm_status.get("models") or []))
    conversation_turns = [{"user": str(t.get("user_message") or "")[:240], "resident": str(t.get("resident_response") or "")[:240]} for t in existing.get("turns", []) if t.get("memory_status", "active") == "active"]
    composition = compose_resident_identity(surface["resident_id"], surface_id="single-resident-gateway", root=rootp, conversation_context=conversation_turns, task_instructions=user_message)
    context_packet = _context_packet(rootp, resident, existing)
    context_packet["runtime_identity_composition"] = {"schema_version": composition.get("schema_version"), "identity_hash": composition.get("identity_version_or_source_hash"), "failed_closed": composition.get("failed_closed"), "layers": [l.get("layer") for l in composition.get("included_context_layers", [])]}
    if attachment_records:
        context_packet["attachments"] = [_safe_attachment_metadata(a) for a in attachment_records]
        summaries = [a.get("summary") for a in attachment_records if a.get("kind") == "image" and a.get("vision_status") == "processed" and a.get("summary")]
        if summaries:
            user_message_for_prompt = user_message + "\nLocal image summaries: " + " | ".join(summaries)
        else:
            user_message_for_prompt = user_message + "\nAttachment note: pasted image/text artifacts were received and stored locally; visual inspection is unavailable unless a local vision model processed them."
    else:
        user_message_for_prompt = user_message
    prompt = resident_prompt(surface["resident_id"], user_message_for_prompt, surface, auth_record, context_packet, base_meta, composition)
    model_control_selection = resolve_model_control_selection(surface["resident_id"], "text", root=rootp)
    selected_model = model_control_selection.get("adapter_model_name") or (llm_status.get("model") if surface["resident_id"] == "alfred" else None)
    generated = adapter.generate(resident=surface["resident_id"], prompt=prompt, model=selected_model) if llm_status.get("available") else {"ok": False, "metadata": _llm_metadata("deterministic_fallback", provider=llm_status.get("provider"), model=llm_status.get("model"), endpoint=llm_status.get("endpoint") or OLLAMA_ENDPOINT, fallback_used=True, fallback_reason=llm_status.get("discovery") or "Local Ollama unavailable", discovered_models_count=len(llm_status.get("models") or []), generation_result_state="not_attempted", timeout_seconds=alfred_ollama_timeout_seconds(), prompt_summary=_prompt_summary(prompt))}
    llm_meta = _sanitize_llm_metadata(generated.get("metadata") or base_meta)
    llm_meta.update({"selection_source": model_control_selection.get("selection_source"), "assigned_model": model_control_selection.get("assigned_model"), "capability": "text", "policy_result": model_control_selection.get("policy_result"), "model_control_warning": model_control_selection.get("warning")})
    if governed_action:
        llm_meta = _llm_metadata("blocked_privileged_execution", provider=llm_meta.get("provider"), model=llm_meta.get("model"), endpoint=llm_meta.get("endpoint"), fallback_used=True, fallback_reason="governed action request refused from chat", generation_attempted=llm_meta.get("generation_attempted"), generation_endpoint=llm_meta.get("generation_endpoint"), generation_result_state="blocked", discovered_models_count=llm_meta.get("discovered_models_count"), prompt_summary=llm_meta.get("prompt_summary"))
    response = generated.get("text") if generated.get("ok") and not governed_action else _fallback_response(resident, user_message, surface, rootp, classification, governed_action)
    if generated.get("ok") and surface.get("resident_id") == "alfred" and ("json files" in user_message.lower() and "llm" in user_message.lower()):
        response = str(generated.get("text"))
        if "local_llm_generated" not in response:
            response = f"Pat, this answer is being generated through local_llm_generated with provider {llm_meta.get('provider') or 'ollama'} and model {llm_meta.get('model') or selected_model}; JSON artifacts provide context, not the whole response."
    if attachment_records and any(a.get("kind") == "image" and a.get("vision_status") != "processed" for a in attachment_records):
        response += "\n\nAttachment note: I received and stored the pasted image locally, but no local vision-capable model is available to visually inspect it yet."
    elif attachment_records and any(a.get("kind") == "image" and a.get("summary") for a in attachment_records) and not generated.get("ok"):
        response += "\n\nLocal image observation: " + " | ".join(a.get("summary") for a in attachment_records if a.get("summary"))
    request_finished_at = _now()
    resident_llm_diagnostic(surface["resident_id"], rootp, write=True, adapter=adapter)
    diagnostics = {"provider": llm_meta.get("provider") or llm_status.get("provider"), "endpoint": llm_meta.get("endpoint") or llm_status.get("endpoint"), "discovered_models_count": llm_meta.get("discovered_models_count", len(llm_status.get("models") or [])), "local_llm_adapter_available": bool(llm_status.get("available")), "selected_provider": llm_status.get("selected_provider") or llm_status.get("provider"), "selected_model": llm_status.get("selected_model") or llm_status.get("model"), "generation_attempted": bool(llm_meta.get("generation_attempted")), "generation_endpoint": llm_meta.get("generation_endpoint"), "generation_result_state": llm_meta.get("generation_result_state"), "generation_result": llm_meta.get("generation_result"), "timeout_seconds": llm_meta.get("timeout_seconds"), "prompt_size": llm_meta.get("prompt_size"), "recovery_hint": llm_meta.get("recovery_hint") or llm_status.get("recovery_hint"), "fallback_active": bool(llm_meta.get("fallback_used")), "fallback_reason": _safe_diagnostic_text(llm_meta.get("fallback_reason") or (None if llm_meta.get("mode") == "local_llm" else llm_status.get("discovery"))), "sanitized_error": _safe_diagnostic_text(llm_meta.get("sanitized_error") or llm_status.get("last_adapter_error")), "prompt_summary": _safe_diagnostic_text(llm_meta.get("prompt_summary")), "last_adapter_error": _safe_diagnostic_text(llm_status.get("last_adapter_error")), "last_request_timestamp": request_started_at, "last_response_timestamp": request_finished_at, "last_timeout_or_transport_error": _safe_diagnostic_text(llm_meta.get("fallback_reason") if llm_meta.get("fallback_used") else None)}
    turn = {"session_id":sid,"turn_id":f"turn_{turn_no:04d}","resident_id":surface["resident_id"],"resident_display_name":surface["resident_display_name"],"participant_role":participant_role,"created_at":request_finished_at,"user_message":user_message,"resident_response":response,"response_contract":{"response_type":classification.get("response_type"),"intent":classification.get("intent"),"status":("degraded_fallback" if llm_meta.get("fallback_used") and llm_meta.get("generation_attempted") else "completed"),"queued":False,"failed":bool(llm_meta.get("fallback_used") and llm_meta.get("generation_attempted")),"timed_out":llm_meta.get("generation_result_state")=="timeout","fallback_response":bool(llm_meta.get("fallback_used")),"governed_action":governed_action},"diagnostics":diagnostics,"context_used":[surface["surface_reference"],"src/estate/core/resident_authority.py","bounded_estate_context_packet", "canonical_runtime_identity_composition"],"identity_composition":composition,"llm":llm_meta,"resident_surface":{"resident_api_standard_version":surface["resident_api_standard_version"],"resident_implementation_version":surface["resident_implementation_version"],"allowed_capabilities":[c["id"] for c in surface["capabilities"]],"surface_reference":surface["surface_reference"]},"authority":auth_record,"attachments":[_safe_attachment_metadata(a) for a in attachment_records],"memory_status":"active"}
    existing.setdefault("turns", []).append(turn); existing["updated_at"]=_now(); existing["memory_status"]="active"; existing["normal_history"]=[t for t in existing["turns"] if t.get("memory_status")=="active"]
    path = _session_path(rootp, sid); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(existing, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return {"ok":True,"session_id":sid,"turn":turn,"session_path":str(path.relative_to(rootp)).replace('\\','/'),"llm_discovery":llm_status}


def retry_failed_response(resident: str, session_id: str, turn_id: str, *, root=None) -> dict[str, Any]:
    """Retry one failed resident turn by appending a new turn to the same session.

    Successful turns are never duplicated: only turns whose response contract records
    a local failure/degraded attempted generation are eligible.
    """
    rootp = _root(root)
    path = _session_path(rootp, session_id)
    data = _read_json(path)
    if not isinstance(data, dict):
        return {"ok": False, "error": "session_not_found", "session_id": session_id}
    if _key(data.get("resident_id")) != _key(resident):
        return {"ok": False, "error": "resident_session_mismatch", "session_id": session_id, "resident_id": data.get("resident_id")}
    source = next((t for t in data.get("turns", []) if t.get("turn_id") == turn_id), None)
    if not source:
        return {"ok": False, "error": "turn_not_found", "session_id": session_id, "turn_id": turn_id}
    contract = source.get("response_contract") or {}
    eligible = bool(contract.get("failed") or contract.get("timed_out") or contract.get("status") == "failed")
    if not eligible:
        return {"ok": False, "error": "turn_not_failed", "session_id": session_id, "turn_id": turn_id, "duplicated_successful_turn": False}
    payload = process_chat(
        resident,
        str(source.get("user_message") or ""),
        session_id=session_id,
        participant_role=str(source.get("participant_role") or "Steward"),
        action=str((contract.get("intent") or "conversation")),
        root=rootp,
    )
    payload["retry"] = {"retried_turn_id": turn_id, "duplicated_successful_turn": False, "retry_policy": "failed_turns_only_append_new_turn"}
    return payload

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
