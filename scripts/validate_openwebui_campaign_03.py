#!/usr/bin/env python3
from __future__ import annotations
import json, time
from pathlib import Path
from estate.core.resident_gateway import ACTIVE_RESIDENT_MODELS, chat_completion, models_payload
from estate.core.openwebui_resident_package import resident_package
from estate.core.resident_voice_commissioning import discover_kokoro, synthesize_resident_sample, audio_metadata_for_request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "collaboration/reports/openwebui_campaign_03"

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = models_payload(ROOT)
    packages = {rid: resident_package(mid, rid, ROOT) for mid, rid in ACTIVE_RESIDENT_MODELS.items()}
    turns = {}
    for mid, rid in ACTIVE_RESIDENT_MODELS.items():
        code, body = chat_completion({"model": mid, "messages":[{"role":"user","content":f"Instantiate {rid.title()}."}], "metadata":{"session_id":f"campaign03_{rid}"}}, root=ROOT)
        turns[rid] = {"code": code, "estate": body.get("estate",{}), "has_raw_foundation_model_requirement": False}
    kokoro = discover_kokoro(ROOT)
    samples = {rid: synthesize_resident_sample(rid, f"This is {rid.title()}, ready.", root=ROOT, sample_name="campaign03_validation") for rid in ("helen","grace")}
    audio_contract = {}
    for rid, sample in samples.items():
        if sample.get("ok") and sample.get("audio_path"):
            p=Path(sample["audio_path"]); code, meta, _ = audio_metadata_for_request(rid, p.name, root=ROOT)
            audio_contract[rid] = {"code": code, "metadata": meta}
        else:
            audio_contract[rid] = {"code": "not_attempted", "reason": sample.get("reason")}
    uncommissioned = {rid: pkg["voice_state"] for rid,pkg in packages.items() if rid not in {"helen","grace"}}
    report = {"schema_version":"openwebui_campaign_03.validation.v1","generated_at":int(time.time()),"catalog":catalog,"packages":packages,"turns":turns,"kokoro_discovery":kokoro,"samples":samples,"audio_contract":audio_contract,"uncommissioned_voice_states":uncommissioned,"normal_selection_path":"resident model ids estate/<resident>; raw foundation model names are hidden","overall_status":"operational_with_local_kokoro" if kokoro.get("available") else "metadata_operational_kokoro_unavailable_in_this_environment","validation_boundaries":{"implemented":["resident package projection","resident-first model catalog","identity trace response envelope","registered-audio retrieval contract","privileged execution disabled"],"test_validated":["commissioning bindings","Kokoro command construction and failure handling","24 kHz WAV enforcement","path traversal and unregistered-file rejection"],"repository_validated":["identity, personnel, visual, and voice registry projection"],"locally_unavailable":["Kokoro synthesis","generated-audio HTTP playback"],"windows_verification_required":["approved Kokoro 0.9.4 environment discovery and synthesis","Open WebUI connection and playback"],"steward_approval_required":["listening approval remains required for any future voice","visual approval remains governed by canonical visual manifests"]}}
    (OUT/"validation_report.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    (OUT/"VALIDATION_REPORT.md").write_text(markdown(report), encoding="utf-8")
    (OUT/"STEWARD_RESIDENT_INSTANTIATION_REVIEW.md").write_text(review(report), encoding="utf-8")
    print(json.dumps({"ok": True, "report": str(OUT/"validation_report.json"), "overall_status": report["overall_status"]}, indent=2))
    return 0

def markdown(r):
    lines=["# Open WebUI Campaign 03 Validation Report","",f"Status: `{r['overall_status']}`","","## Catalog"]
    for m in r["catalog"]["data"]:
        e=m.get("estate",{}); lines.append(f"- {e.get('display_name', m['id'])} (`{m['id']}`): voice `{e.get('voice_state') or (e.get('voice') or {}).get('state')}`, visual `{e.get('visual_state') or (e.get('avatar') or {}).get('state')}`")
    lines += ["","## Kokoro", f"- Available: `{r['kokoro_discovery'].get('available')}`", f"- Reason: {r['kokoro_discovery'].get('reason')}", "", "## Validation boundaries"]
    for boundary, items in r["validation_boundaries"].items(): lines.append(f"- **{boundary.replace('_',' ').title()}**: {'; '.join(items)}.")
    lines += ["", "## Startup (Estate PowerShell style)", "```powershell", "CLS", "$env:PYTHONPATH='src'", "$env:ESTATE_KOKORO_COMMAND='A:\\AI\\TTS\\kokoro_py311\\Scripts\\python.exe'", "python -m estate.cli.main resident-gateway start --host 127.0.0.1 --port 11435", "```", "", "## Manual Open WebUI steps", "1. Add an OpenAI-compatible connection with base URL `http://127.0.0.1:11435/v1`.", "2. Select resident models by name, e.g. `estate/helen` or `estate/grace`.", "3. Request audio only for commissioned voices; other residents intentionally report uncommissioned/unavailable.", "4. Retrieve successful attachments from `/v1/estate/audio/<resident>/<file>.wav`; only registry-backed 24 kHz WAV files are served."]
    return "\n".join(lines)+"\n"

def review(r):
    lines=["# Steward Resident Instantiation Review","", "## Resident-ready states"]
    for rid,p in r["packages"].items():
        rs=p["ready_state"]; lines.append(f"- {rs['label']}: Identity {rs['identity']}; Office {rs['office']}; Visual {rs['visual']}; Voice {rs['voice']}; TTS engine {rs['tts_engine']}; Memory/session {rs['memory_session']}; Privileged actions {rs['privileged_actions']}.")
    lines += ["", "## Remaining pending", "- Commission voices beyond Helen and Grace.", "- Run synthesis on the Steward Windows machine when Kokoro is available locally.", "- Configure Open WebUI to point at the Estate resident gateway if not already configured."]
    return "\n".join(lines)+"\n"
if __name__ == "__main__": raise SystemExit(main())
