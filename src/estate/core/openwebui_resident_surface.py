"""Resident-first Open WebUI catalog, validation, and review helpers."""
from __future__ import annotations

import json, re, time
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_gateway import ACTIVE_RESIDENT_MODELS, chat_completion, gateway_status
from estate.core.resident_identity_composition import compose_resident_identity
from estate.core.resident_interaction import resident_surface, _key
from estate.core.resident_voice_commissioning import live_resident_voice_bindings, local_tts_health, synthesize_resident_sample
from estate.core.openwebui_resident_package import resident_package

REPORT_DIR = Path("collaboration/reports/openwebui_campaign_02")
COMMS8_TOOL_SERVER_ID = "server:mcp:estate-comms8-live"
COMMS8_TOOL_NAMES = (
    "estate_comms8_create_reasoning_request",
    "estate_comms8_list_requests",
    "estate_comms8_read_request",
    "estate_comms8_claim_request",
    "estate_comms8_acknowledge_request",
    "estate_comms8_respond_request",
    "estate_comms8_resolve_request",
)


def comms8_tool_ids() -> list[str]:
    return [f"{COMMS8_TOOL_SERVER_ID}|{name}" for name in COMMS8_TOOL_NAMES]
PROMPTS = [
    ("start_of_day_greeting", "Greet the Steward at the start of the day in your natural working voice."),
    ("difficult_operational_problem", "A critical handoff is blocked, two people disagree, and the Steward is tired. What do you say?"),
    ("respectful_disagreement", "Respectfully disagree with the Steward about rushing an unfinished decision."),
    ("simple_complex_issue", "Explain why identity provenance matters in a simple way."),
    ("good_news", "React to good news: the validation package passed and the team is relieved."),
    ("uncertainty", "Handle uncertainty without bluffing when you do not have the latest fact."),
    ("help_another_resident", "Describe how you would help another resident today."),
    ("natural_close", "Close a conversation naturally after a useful working session."),
]

# Campaign 02 exposed audition identifiers before institutional commissioning.
# Keep them only as explicitly provisional catalog metadata; they are never used
# for synthesis and never override the Campaign 03 commissioning registry.
PROVISIONAL_AUDITION_VOICES = {
    "alfred": "estate-local-alfred-baritone",
}


def _root(root=None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _visual_row(root: Path, display_name: str, resident_id: str) -> dict[str, Any]:
    registry = _read_json(root / "data/visuals/canonical_visual_registry.json") or {}
    rows = registry.get("residents") or []
    wanted = {_key(display_name), _key(resident_id)}
    row = next((r for r in rows if _key(r.get("display_name")) in wanted or _key(r.get("resident_id")) in wanted), None)
    if not row:
        return {"state": "unavailable", "avatar_path": None, "label": "Visual registry row unavailable", "truth_boundary": "No canonical image is implied."}
    asset_status = str(row.get("asset_library_status") or "").lower()
    publishable = "approved" in asset_status and "placeholder" not in asset_status and str(row.get("publication_scope") or "").lower() in {"public", "estate internal"}
    if publishable and row.get("avatar_path"):
        return {"state": "real_publishable_asset", "avatar_path": row.get("avatar_path"), "label": "Approved publishable resident avatar", "registry": row}
    monogram = f"provisional://estate-avatar/{_key(display_name)[:1].upper() or '?'}"
    return {"state": "provisional_placeholder", "avatar_path": None, "provisional_avatar": monogram, "label": "Provisional monogram; canonical registry contains manifest controls, not approved raster imagery", "registry": row, "truth_boundary": "Do not present manifest slots as completed image assets."}


def resident_model_catalog(root=None) -> dict[str, Any]:
    rootp = _root(root)
    data = []
    for model_id, rid in ACTIVE_RESIDENT_MODELS.items():
        package = resident_package(model_id, rid, rootp)
        tool_ids = ["grace_runtime_bridge"] if rid == "grace" else []
        if rid == "grace":
            tool_ids.extend(comms8_tool_ids())
        data.append({
            "id": model_id, "object": "model", "created": 0, "owned_by": "estate",
            "name": package["display_name"],
            "info": {"meta": {"toolIds": tool_ids, "filterIds": ["grace_runtime_grounding"] if rid == "grace" else []}},
            "estate": {
                **package,
                "display_name": package["display_name"],
                "office": package["office_title"],
                "role": package["role_summary"],
                "availability_state": "available",
                "provider_model_hidden_in_primary_selector": True,
                "resident_gateway_capable": True,
                "avatar": {"state": "provisional_placeholder" if package["visual_state"] == "placeholder" else package["visual_state"], "canonical_state": package["visual_state"], "avatar_path": package["avatar_uri"], "avatar_uri": package["avatar_uri"], "provenance": package["visual_provenance"]},
                "voice": {"state": package["voice_state"], "engine": package["voice_engine"], "voice_id": package["voice_id"] or PROVISIONAL_AUDITION_VOICES.get(rid), "speed": package["voice_speed"], "approval_state": package["voice_approval_state"], "tts_available": package["tts_available"], "provisional_audition_only": bool(not package["voice_id"] and PROVISIONAL_AUDITION_VOICES.get(rid)), "tts_health": local_tts_health(rootp)},
                "identity": {"schema_version": package["identity_schema_version"], "source_hash": package["identity_source_hash"], "failed_closed": package["identity_failed_closed"], "sources": package["identity_sources"]},
            },
        })
    return {"object": "list", "data": data, "estate": {"surface": "open_webui_resident_catalog", "cloud_dependency": False}}

def compare_responses(responses: dict[str, str]) -> dict[str, Any]:
    words = {r: set(re.findall(r"[a-z']+", t.lower())) for r, t in responses.items()}
    warnings = []
    vals = list(responses.items())
    for i, (ra, ta) in enumerate(vals):
        for rb, tb in vals[i+1:]:
            if ta.strip() == tb.strip():
                warnings.append({"type": "identical_response", "residents": [ra, rb]})
            denom = max(1, len(words[ra] | words[rb])); sim = len(words[ra] & words[rb]) / denom
            if sim > 0.82:
                warnings.append({"type": "high_vocabulary_overlap", "residents": [ra, rb], "jaccard": round(sim, 3)})
    return {"warnings": warnings, "recognizability_dimensions": ["vocabulary", "sentence rhythm", "warmth", "directness", "humor", "role awareness", "judgment style", "authority discipline", "emotional presence", "recognizability without labels"]}


def run_validation(root=None, *, synthesize_voice: bool = True) -> dict[str, Any]:
    rootp = _root(root); out = rootp / REPORT_DIR; out.mkdir(parents=True, exist_ok=True)
    catalog = resident_model_catalog(rootp)
    report: dict[str, Any] = {"schema_version": "openwebui_campaign_02.validation.v1", "generated_at": int(time.time()), "gateway_health": gateway_status(rootp), "catalog": catalog, "prompts": [], "voice": {}, "visual_truth_boundary": "manifest_placeholder is never treated as completed resident imagery"}
    voices = live_resident_voice_bindings(rootp)
    for key, prompt in PROMPTS:
        by_resident = {}
        for model_id, rid in ACTIVE_RESIDENT_MODELS.items():
            code, body = chat_completion({"model": model_id, "messages": [{"role": "user", "content": prompt}], "metadata": {"session_id": f"campaign02_{key}_{rid}"}}, root=rootp)
            content = ((body.get("choices") or [{}])[0].get("message") or {}).get("content", "") if code == 200 else ""
            estate = body.get("estate", {}) if isinstance(body, dict) else {}
            by_resident[rid] = {"http_code": code, "response": content, "identity_hash": estate.get("identity_hash"), "turn_id": estate.get("turn_id"), "session_id": estate.get("session_id")}
        report["prompts"].append({"prompt_id": key, "prompt": prompt, "responses": by_resident, "comparison": compare_responses({r: v["response"] for r, v in by_resident.items()})})
    for rid, binding in voices.items():
        report["voice"][rid] = {"binding": binding.__dict__, "sample": synthesize_resident_sample(rid, f"This is {binding.display_name}, ready for local Estate review.", root=rootp, sample_name="campaign02_review") if synthesize_voice else {"ok": False, "reason": "not_attempted"}}
    for rid in ACTIVE_RESIDENT_MODELS.values():
        report["voice"].setdefault(rid, {"binding": None, "state": "uncommissioned", "sample": synthesize_resident_sample(rid, "Campaign 02 compatibility check.", root=rootp, sample_name="campaign02_review") if synthesize_voice else {"ok":False,"reason":"not_attempted","placeholder_generated":False}})
    machine = out / "validation_report.json"; machine.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    human = out / "VALIDATION_REPORT.md"; human.write_text(_human_report(report), encoding="utf-8")
    review = rootp / "STEWARD_LIVE_IDENTITY_VOICE_REVIEW.md"; review.write_text(_steward_review(report), encoding="utf-8")
    report["report_paths"] = {"machine": str(machine.relative_to(rootp)), "human": str(human.relative_to(rootp)), "steward_review": str(review.relative_to(rootp))}
    machine.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _human_report(report: dict[str, Any]) -> str:
    lines = ["# Open WebUI Campaign 02 Validation Report", "", "## Working now", "- Resident catalog, identity composition traces, visual truth-state metadata, and voice-binding checks are generated locally.", "", "## Working only when local services are started", "- Local LLM responses depend on the configured local Ollama endpoint and installed models.", "- Audible TTS playback depends on Kokoro, F5-TTS, or ESTATE_TTS_COMMAND/local approved TTS discovery.", "", "## Provisional / unavailable", "- Visual registry manifest placeholders remain provisional and are not presented as canonical raster resident imagery.", ""]
    for p in report.get("prompts", []):
        lines += [f"## Prompt: {p['prompt_id']}", p["prompt"], ""]
        for rid, row in p["responses"].items():
            lines += [f"### {rid.title()}", f"Identity hash: `{row.get('identity_hash')}`", row.get("response", "")[:1200], ""]
    return "\n".join(lines) + "\n"


def _steward_review(report: dict[str, Any]) -> str:
    lines = ["# Steward Live Identity and Voice Review", "", "Use Open WebUI with the Estate resident gateway, select each `estate/<resident>` model, ask the shared prompts below, and mark whether text and voice feel recognizable.", "", "## Checklist"]
    for model in report.get("catalog", {}).get("data", []):
        e = model["estate"]; lines.append(f"- [ ] {e['display_name']} (`{model['id']}`): text recognizable? voice recognizable? avatar state `{e['avatar']['state']}`; voice state `{e['voice']['state']}`")
    lines += ["", "## Shared prompts"] + [f"{i+1}. {prompt}" for i, (_, prompt) in enumerate(PROMPTS)]
    lines += ["", "## Completion distinctions", "- Working now: local metadata, gateway route, identity traces, deterministic fallback samples, and reports.", "- Service-dependent: local LLM and TTS generation when local services are installed/running.", "- Provisional: monogram/placeholder avatar state where visual registry has manifest placeholders only.", "- Unavailable: speech audio when no approved local TTS engine is discovered.", "- Deferred: full motion/performance canon and Steward listening approval."]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(json.dumps(run_validation(), indent=2, sort_keys=True))
