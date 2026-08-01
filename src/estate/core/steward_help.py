"""Current, read-only Steward help and capability discovery surface."""
from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .estate_skills import SkillRegistry

SCHEMA_VERSION = "estate.current-capabilities.v1"
INSTITUTIONAL_ACCEPTANCE = "not_granted"
_STATUS = {"operational_now", "authorization_required", "registered_unavailable", "temporarily_unavailable", "capability_gap", "prohibited", "planned"}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def _read(root: Path, rel: str, default: Any) -> Any:
    p = root / rel
    try: return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
    except (OSError, ValueError): return default

def _digest(path: Path) -> str | None:
    if not path.exists(): return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()

def _source(root: Path, rel: str) -> dict[str, Any]:
    p = root / rel
    return {"reference": rel.replace("\\", "/"), "exists": p.exists(), "sha256": _digest(p)}

def _probe(url: str, *, timeout: float = 1.5, expected: str | None = None) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(4096).decode("utf-8", "replace")
            payload = json.loads(body) if body.lstrip().startswith(("{", "[")) else None
            ok = response.status in range(200, 300) and (expected is None or expected in body)
            return {"reachable": True, "status": response.status, "ok": ok, "payload_summary": _summary(payload)}
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {"reachable": False, "status": None, "ok": False, "reason": type(exc).__name__}

def _summary(value: Any) -> Any:
    if isinstance(value, dict):
        keep = {k: value[k] for k in ("service", "healthy", "ready", "mode", "resident_id", "model", "name") if k in value}
        return keep
    return None

def _entity(entity_id: str, name: str, description: str, *, owner: str, maturity: Any, availability: str, dispatchable: bool | None, scope: str, prohibited: list[str], authority: list[str], phrases: list[str], outputs: list[str], reasons: list[str], project: str | None, sources: list[dict[str, Any]], acceptance: str = INSTITUTIONAL_ACCEPTANCE, qualified: list[str] | None = None) -> dict[str, Any]:
    if availability not in _STATUS: raise ValueError(f"invalid help status: {availability}")
    return {"id":entity_id,"name":name,"description":description,"owner":owner,"maturity":maturity,"availability":availability,"dispatchability":"dispatchable" if dispatchable is True else "not_dispatchable" if dispatchable is False else "unknown","qualified_providers_or_workers":qualified or [],"accepted_scope":scope,"prohibited_or_unsupported_scope":prohibited,"classification_ceiling":"Estate Internal","required_authority":authority,"invocation_mode":"governed_execution" if dispatchable else "proposal_or_authorization_required","common_phrases":phrases,"expected_outputs":outputs,"likely_block_or_failure_reasons":reasons,"enabling_project":project,"institutional_acceptance":acceptance,"sources":sources}

def _catalog_provider(catalog: dict[str, Any], provider_id: str) -> dict[str, Any]:
    return next((p for p in catalog.get("providers", []) if p.get("provider_id") == provider_id), {})

def _provider_state(root: Path, provider_id: str, catalog: dict[str, Any]) -> dict[str, Any]:
    p = _catalog_provider(catalog, provider_id)
    health = _read(root, "runtime/providers/health/status/latest.json", {})
    record = health.get(provider_id) if isinstance(health, dict) else None
    stale = True
    if isinstance(record, dict) and record.get("expires_at"):
        try: stale = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00")) <= datetime.now(timezone.utc)
        except ValueError: stale = True
    if provider_id == "qwen.local.text":
        probe = _probe("http://127.0.0.1:11434/api/tags", expected="qwen3:8b")
        if probe["ok"]: return {"availability":"authorization_required","dispatchable":False,"reason":"fresh loopback reachability is present, but governed authorization and validation remain required","evidence_stale":stale,"health":probe}
    if provider_id == "codex.execution.cli":
        state = _read(root, "runtime/provider_health/providers/codex_cli_openai.json", {})
        return {"availability":"temporarily_unavailable" if state.get("is_stale", True) or state.get("availability") != "available" else "authorization_required","dispatchable":False,"reason":"provider health is stale/offline; provider catalog does not grant execution authority","evidence_stale":bool(state.get("is_stale", True)),"health":{k:state.get(k) for k in ("availability","health_state","observed_at","warnings")}}
    if provider_id == "comfyui.local.image":
        probe = _probe("http://127.0.0.1:8188/system_stats")
        return {"availability":"authorization_required" if probe["ok"] else "registered_unavailable","dispatchable":False,"reason":"fresh health/capacity and separate live submission authorization are required","evidence_stale":not probe["ok"],"health":probe}
    return {"availability":"registered_unavailable","dispatchable":False,"reason":"catalog registration is not current operational evidence","evidence_stale":True,"health":{}}

def build_snapshot(root: str | Path, *, include_live_probes: bool = True) -> dict[str, Any]:
    root = Path(root).resolve()
    caps = _read(root, "data/registry/capabilities.json", [])
    providers = _read(root, "data/registry/providers.json", [])
    catalog = _read(root, "config/providers/catalog.json", {})
    residents = _read(root, "data/registry/residents.json", [])
    skill_path = root / "config/skills/estate_skill_registry.json"
    skills = SkillRegistry.load(skill_path)
    sources = ["data/registry/capabilities.json", "data/registry/providers.json", "data/registry/residents.json", "config/providers/catalog.json", "config/skills/estate_skill_registry.json", "runtime/residents/helen/readiness.json", "runtime/providers/health/status/latest.json", "runtime/provider_health/providers/codex_cli_openai.json", "runtime/ai_services/implementations/comfyui/service.manifest.json", "config/runtime/canonical_webui_gateway.json"]
    source_records = [_source(root, x) for x in sources]
    entities: list[dict[str, Any]] = []
    resident_by_name = {str(x.get("name", "")).casefold(): x for x in residents if isinstance(x, dict)}
    grace = resident_by_name.get("grace", {})
    helen = resident_by_name.get("helen", {})
    runtime = {"status":"unknown"}
    if include_live_probes:
        try:
            from .canonical_webui_gateway_runtime import load_config, status
            runtime = status(load_config(root / "config/runtime/canonical_webui_gateway.json"))
        except Exception as exc:
            runtime = {"status":"unknown","reason":type(exc).__name__}
    runtime_ready = bool(runtime.get("runtime", {}).get("healthy"))
    entities.append(_entity("grace", "Grace", grace.get("role", "Operations coordination and governed routing."), owner="Operations", maturity="active resident", availability="operational_now" if runtime_ready else "temporarily_unavailable", dispatchable=False, scope="Help, discovery, bounded operational coordination, and governed handoffs.", prohibited=["provider execution without governed dispatch", "institutional acceptance", "unbounded movement"], authority=["explicit request for any governed action", "existing Operations/Steward decisions"], phrases=["Grace, help.","Grace, what can we do?","Grace, prepare a proposal before execution."], outputs=["plain-language answer", "bounded proposal or governed handoff"], reasons=[] if runtime_ready else ["canonical Grace/Gateway/WebUI path is not currently semantically ready"], project=None, sources=[_source(root,"data/registry/residents.json"),_source(root,"config/runtime/canonical_webui_gateway.json")], qualified=["Grace"]))
    readiness = _read(root, "runtime/residents/helen/readiness.json", {})
    helen_ready = readiness.get("overall_status") in {"ready", "ready_with_limitations"}
    entities.append(_entity("helen", "Helen", "Capability, qualification, availability, capacity, and gap assessment.", owner="Human Resources", maturity=readiness.get("overall_status", "unknown"), availability="operational_now" if helen_ready else "temporarily_unavailable", dispatchable=False, scope="Readiness and workforce assessment; bounded recommendations.", prohibited=["granting constitutional authority", "claiming provider execution", "inventing qualification"], authority=["Helen assessment authority under existing governance"], phrases=["Helen, do we have a governed transcription capability?","What is unavailable and what project enables it?"], outputs=["qualification and readiness assessment", "bounded gap and enabling project"], reasons=[] if helen_ready else ["Helen readiness evidence is missing or not ready"], project=None, sources=[_source(root,"runtime/residents/helen/readiness.json"),_source(root,"data/registry/residents.json")], qualified=["Helen"]))
    entities.append(_entity("engineering", "Engineering", "Technical design, bounded implementation, review, and validation coordination.", owner="Engineering", maturity="registered", availability="authorization_required", dispatchable=False, scope="Explicitly scoped repository/design/review work through canonical authorization and Dispatch.", prohibited=["implicit write scope", "provider selection without readiness", "merge or acceptance without authority"], authority=["owner authorization", "PTM/readiness", "Operations and Dispatch as applicable"], phrases=["Grace, ask Engineering to draft...","Grace, ask Engineering to review these exact files..."], outputs=["bounded design or implementation artifact", "receipt and validation evidence"], reasons=["each request needs current authority, scope, worker, provider, and readiness"], project="Capability-specific enabling project", sources=[_source(root,"config/providers/catalog.json"),_source(root,"data/registry/residents.json")], qualified=["Engineering workers assessed by Helen"]))
    for provider_id, display, desc, phrases in [("qwen.local.text","qwen.local.text","Loopback Qwen-family text generation and bounded repository reads.",["Grace, ask Engineering to draft...","Helen, is Qwen text available now?"]), ("codex.execution.cli","codex.execution.cli","Bounded Codex CLI execution with declared workspace and outputs.",["Grace, ask Engineering to review these exact files..."]), ("comfyui.local.image","ComfyUI","Local image workflow preparation and governed submission.",["Grace, prepare a ComfyUI image proposal."])]:
        pstate = _provider_state(root, provider_id, catalog) if include_live_probes else {"availability":"registered_unavailable","dispatchable":False,"reason":"live probe not requested","evidence_stale":True}
        cp = _catalog_provider(catalog, provider_id)
        entities.append(_entity(provider_id, display, desc, owner="Engineering", maturity=cp.get("status", "registered"), availability=pstate["availability"], dispatchable=pstate["dispatchable"], scope="Only capabilities declared by the provider catalog and current authorization.", prohibited=["unbounded shell or repository access", "assuming installed/catalog status means ready"], authority=["explicit governed authorization", "fresh provider health/capacity"], phrases=phrases, outputs=["provider receipt", "validated artifact when separately authorized"], reasons=[pstate["reason"]], project="Provider health/readiness enablement" if pstate.get("availability") != "authorization_required" else None, sources=[_source(root,"config/providers/catalog.json"),_source(root,"config/providers/qwen_local_text.json") if provider_id == "qwen.local.text" else _source(root,"runtime/ai_services/implementations/comfyui/service.manifest.json") if provider_id == "comfyui.local.image" else _source(root,"runtime/provider_health/providers/codex_cli_openai.json")], qualified=[provider_id]))
    qwen_coder = next((p for p in providers if str(p.get("name", "")).lower().find("qwen") >= 0 and p.get("model")), None)
    if qwen_coder:
        entities.append(_entity("qwen-coder", "Qwen Coder", "Observed Qwen coder model record; no current formal routing or fresh dispatch evidence is claimed.", owner="Engineering", maturity="observed", availability="registered_unavailable", dispatchable=False, scope="Observation only until formal provider routing, health, qualification, and authority are current.", prohibited=["treating model presence or historical use as operational dispatchability"], authority=["future provider onboarding and explicit governed authorization"], phrases=["Helen, is Qwen Coder available now?"], outputs=["future bounded text artifact and provider receipt"], reasons=["observed model record is historical and formal routing policy is pending"], project="Qwen Coder provider onboarding", sources=[_source(root,"data/registry/providers.json"),_source(root,"data/registry/capabilities.json")], qualified=[]))
    for cap in caps:
        if cap.get("name") == "Whisper":
            entities.append(_entity("CAP-000006", "Whisper", cap.get("description", "Speech transcription."), owner=cap.get("owner", "Administration"), maturity=cap.get("lifecycle_state", "Designed"), availability="planned", dispatchable=False, scope="No current governed transcription execution is proven.", prohibited=["claiming transcription is operational from installation/catalog evidence"], authority=["future governed onboarding and execution authorization"], phrases=["Can we transcribe audio?","Helen, do we have a governed transcription capability?"], outputs=["future transcript artifact with provenance"], reasons=["registry says Pending Install; no current operational provider evidence"], project="Whisper capability onboarding", sources=[_source(root,"data/registry/capabilities.json"),_source(root,"data/registry/providers.json")], qualified=[]))
    skill_items = []
    for s in skills.skills:
        skill_items.append(_entity(s["skill_id"], s["name"], s["purpose"], owner=s["owner"], maturity=s["maturity"], availability="authorization_required" if s["availability"] == "available" else "registered_unavailable", dispatchable=False, scope="Declared bounded Skill scope only.", prohibited=["discovery silently executing", "repository mutation or acceptance through help"], authority=s["authority"].get("required", []), phrases=s.get("aliases", []) + ["Grace, use the Check Git Skill and report only."], outputs=["declared Skill artifact and receipt"], reasons=["explicit execution authority is still required"], project=None, sources=[_source(root,"config/skills/estate_skill_registry.json")], acceptance=s["institutional_acceptance"], qualified=[s["maintainer"]]))
    entities.extend(skill_items)
    entities.append(_entity("estate-skills", "Estate Skills framework", "Canonical versioned governed procedure registry and read-only discovery.", owner="Estate Architecture", maturity="operational implementation", availability="operational_now", dispatchable=False, scope="Discovery, explanation, readiness assessment, and explicitly governed Skill invocation.", prohibited=["creating authority by registration", "help-triggered execution"], authority=["Skill-specific authority and canonical lifecycle"], phrases=["What Skills are available?","How do I ask for this outcome?"], outputs=["current Skill list and proposal guidance"], reasons=[], project=None, sources=[_source(root,"config/skills/estate_skill_registry.json"),_source(root,"schemas/skills/skill_manifest_v1.schema.json")]))
    entities.append(_entity("capability-onboarding", "Capability onboarding framework", "Existing capability/provider registration and Grace/Helen/Engineering readiness path.", owner="Engineering", maturity="registered", availability="authorization_required", dispatchable=False, scope="Capability registration and governed readiness assessment.", prohibited=["registration alone proving operation", "bypassing Helen/PTM/authorization"], authority=["owner and Engineering authorization"], phrases=["What project enables this capability?"], outputs=["registration, assessment, gap, and evidence"], reasons=["capability-specific evidence may be stale or missing"], project="Capability-specific onboarding", sources=[_source(root,"src/estate/core/engineering_capability_enablement.py"),_source(root,"config/providers/catalog.json")]))
    entities.append(_entity("openwebui-estate-path", "Open WebUI / Grace / Resident Gateway", "Canonical authenticated Open WebUI path through Grace runtime and the Resident Gateway.", owner="Operations", maturity="validated operational path", availability="operational_now" if runtime_ready else "temporarily_unavailable", dispatchable=False, scope="Authenticated WebUI conversation using the canonical shared state and Grace/Gateway route.", prohibited=["unauthenticated readiness being treated as authenticated acceptance", "database reset or alternate state"], authority=["existing approved administrator session for use; governed request authority for actions"], phrases=["Grace, help.","Grace, what Skills are available?"], outputs=["authenticated conversation response and bounded evidence"], reasons=[] if runtime_ready else ["canonical three-service semantic readiness is not currently proven"], project=None, sources=[_source(root,"config/runtime/canonical_webui_gateway.json"),_source(root,"runtime/ai_services/implementations/open_webui/service.manifest.json")]))
    conflicts = []
    for cap in caps:
        if cap.get("status") in {"Operational", "Installed"} and not cap.get("operational_evidence_references"):
            conflicts.append({"entity_id":cap.get("id"),"reason":"registry status is stronger than current operational-evidence field; help uses fail-closed status"})
    return {"schema_version":SCHEMA_VERSION,"generated_at":_now(),"institutional_acceptance":INSTITUTIONAL_ACCEPTANCE,"source_references":source_records,"entities":entities,"conflicts":conflicts,"generation_policy":{"read_only":True,"live_probes":include_live_probes,"installed_or_registered_is_not_operational":True,"historical_success_is_not_current_availability":True}}

def render_cheat_sheet(snapshot: dict[str, Any]) -> str:
    groups = [("operational_now", "What is operational now"), ("authorization_required", "What requires authorization"), ("registered_unavailable", "What is registered but unavailable"), ("temporarily_unavailable", "What is temporarily unavailable"), ("capability_gap", "Capability gaps"), ("planned", "What is planned")]
    lines=["# Steward Cheat Sheet — Current Capabilities", "", f"Generated: {snapshot['generated_at']}", "", "This is a read-only current-state view. Help never executes a Skill or grants authority.", ""]
    by={k:[] for k,_ in groups}
    for e in snapshot["entities"]: by.setdefault(e["availability"], []).append(e)
    for key,title in groups:
        lines += [f"## {title}", ""]
        rows=by.get(key,[])
        lines += [f"- **{e['name']}** (`{e['id']}`): {e['description']}" + (f" Block: {e['likely_block_or_failure_reasons'][0]}." if e["likely_block_or_failure_reasons"] else "") for e in rows] or ["- None proven in the current snapshot."]
        lines.append("")
    lines += ["## Common things the Steward can say", "", "- Grace, help.", "- Grace, what can we do?", "- Grace, show my commands.", "- Grace, what Skills are available?", "- Grace, use the Check Git Skill and report only.", "- Helen, do we have a governed transcription capability?", "- Grace, prepare a proposal before execution.", "", "## Known limits", "", "- Catalog registration, installation, historical success, or a passing test does not prove current dispatchability.", "- Help and discovery never execute providers, Skills, repository changes, merges, deletions, purchases, external messages, or acceptance actions.", "- Fresh authority, worker, provider health/capacity, PTM/readiness, and validation remain request-specific.", "", f"## Institutional acceptance", "", f"- `{snapshot['institutional_acceptance']}`; this surface never infers acceptance.", "", "## Sources", ""]
    lines += [f"- {x['reference']} — sha256 `{x['sha256']}`" for x in snapshot["source_references"]]
    return "\n".join(lines) + "\n"

def _match(snapshot: dict[str, Any], text: str, *, scope: str | None = None) -> list[dict[str, Any]]:
    q=text.casefold(); terms=[x for x in re.findall(r"[a-z0-9][a-z0-9 ./_?-]+", q) if len(x.strip()) > 2]
    out=[]
    for e in snapshot["entities"]:
        hay=" ".join(str(e.get(k,"")) for k in ("id","name","description","owner","accepted_scope","common_phrases")) .casefold()
        if scope and scope.casefold() not in hay: continue
        if any(t.strip() in hay for t in terms): out.append(e)
    return out

def _outcome_matches(snapshot: dict[str, Any], outcome: str) -> list[dict[str, Any]]:
    q = outcome.casefold()
    keyword_map = {
        "transcri": ["Whisper"], "audio": ["Whisper"], "git": ["Repository Health"], "repo": ["Repository Health"],
        "image": ["ComfyUI"], "comfy": ["ComfyUI"], "qwen": ["qwen.local.text", "Qwen Coder"], "skill": ["Repository Health", "Estate Skills framework"],
    }
    names = {name for key, names in keyword_map.items() if key in q for name in names}
    if names: return [e for e in snapshot["entities"] if e["name"] in names or e["id"] in names]
    return _match(snapshot, outcome)

def answer(snapshot: dict[str, Any], request: str, *, resident: str = "Grace") -> dict[str, Any]:
    original=request; q=request.casefold().strip(); discovery_only=True
    if not q: q="help"
    if "what skills" in q:
        skills = [e for e in snapshot["entities"] if e["id"] in {"repository-health", "estate-skills"}]
        names = ", ".join(f"{e['name']} ({e['availability'].replace('_',' ')})" for e in skills)
        return {"resident":resident,"request":original,"intent":"skill_discovery","plain_language":f"The current Skill surface lists: {names}. Discovery is read-only; no Skill was executed. Ask ‘Grace, use the Check Git Skill and report only’ only when you want a separate explicit request.","matches":skills,"executed":False,"institutional_acceptance":snapshot["institutional_acceptance"]}
    if any(x in q for x in ("help", "what can we do", "show my commands", "current capabilities")):
        text="I can explain current capabilities, Skills, owners, limits, authority, and blockers. I will not execute from a help request. Ask: ‘Grace, what Skills are available?’, ‘Helen, do we have a governed transcription capability?’, or ‘Grace, use the Check Git Skill and report only.’"
        return {"resident":resident,"request":original,"intent":"help_or_discovery","plain_language":text,"matches":snapshot["entities"],"executed":False,"institutional_acceptance":snapshot["institutional_acceptance"]}
    if "how do i ask" in q or "how do we ask" in q:
        outcome=q.split("how do i ask",1)[-1].strip(" :?") or "the outcome"
        return {"resident":resident,"request":original,"intent":"request_guidance","plain_language":f"Say: ‘Grace, prepare a proposal for {outcome}; do not execute until authorized.’ For sensitive or execution work, include exact scope, expected output, authority, and whether you want proposal-only or governed execution.","matches":_outcome_matches(snapshot,outcome),"executed":False,"institutional_acceptance":snapshot["institutional_acceptance"]}
    if q.startswith("what can engineering") or q.startswith("what can helen") or "what can " in q:
        who="Helen" if "helen" in q else "Engineering" if "engineering" in q else q.split("what can ",1)[-1].strip(" ?")
        matches=[e for e in snapshot["entities"] if e["owner"].casefold() == who.casefold() or e["name"].casefold() == who.casefold()]
        if not matches: return {"resident":resident,"request":original,"intent":"scoped_discovery","plain_language":f"I cannot prove a current capability record for {who}; Helen can return a bounded gap and enabling project.","matches":[],"executed":False,"institutional_acceptance":snapshot["institutional_acceptance"]}
        return {"resident":resident,"request":original,"intent":"scoped_discovery","plain_language":f"{who} has {len(matches)} recorded capability or responsibility entries. Current availability and authorization are shown per entry; no execution was requested.","matches":matches,"executed":False,"institutional_acceptance":snapshot["institutional_acceptance"]}
    if q.startswith("can we ") or "do we have" in q or "is this capability" in q:
        outcome=q[7:].strip(" ?") if q.startswith("can we ") else q.replace("do we have", "").replace("is this capability", "").strip(" ?"); matches=_outcome_matches(snapshot,outcome)
        if len(matches) != 1:
            return {"resident":resident,"request":original,"intent":"outcome_discovery","plain_language":"I need a more specific outcome before I can identify one record; I will not guess or execute.","matches":matches,"executed":False,"ambiguous":len(matches)>1,"institutional_acceptance":snapshot["institutional_acceptance"]}
        e=matches[0]; return {"resident":resident,"request":original,"intent":"outcome_discovery","plain_language":f"{e['name']} is {e['availability'].replace('_',' ')}. {e['description']} {e['likely_block_or_failure_reasons'][0] if e['likely_block_or_failure_reasons'] else 'A separate governed request is still required.'}","matches":matches,"executed":False,"institutional_acceptance":snapshot["institutional_acceptance"]}
    matches=_match(snapshot,q)
    return {"resident":resident,"request":original,"intent":"discovery","plain_language":"I found no unambiguous help record for that phrase. Ask for ‘current capabilities’, a named resident, a formal Skill, or ‘how do I ask for <outcome>’. I did not execute anything.","matches":matches,"executed":False,"institutional_acceptance":snapshot["institutional_acceptance"]}

def write_surfaces(root: str | Path, *, output_json: str = "docs/operations/help/current_capabilities_20260801.json", output_md: str = "docs/operations/help/Steward_Cheat_Sheet_20260801.md") -> dict[str, Any]:
    root=Path(root).resolve(); snapshot=build_snapshot(root); jp=root/output_json; mp=root/output_md
    jp.parent.mkdir(parents=True,exist_ok=True); mp.parent.mkdir(parents=True,exist_ok=True)
    jp.write_text(json.dumps(snapshot,indent=2,sort_keys=True)+"\n",encoding="utf-8"); mp.write_text(render_cheat_sheet(snapshot),encoding="utf-8")
    return {"snapshot":snapshot,"json_path":str(jp),"cheat_sheet_path":str(mp)}
