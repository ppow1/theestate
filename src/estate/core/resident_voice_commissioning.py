"""Resident audible voice commissioning helpers for the local Open WebUI path.

This module intentionally refuses to label synthetic tones as speech. It uses an
approved local command-line TTS engine when one is discoverable and otherwise
returns a clear unavailable status for Steward machine repair.
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import time
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_gateway import ACTIVE_RESIDENT_MODELS, chat_completion

SCHEMA_VERSION = "resident-audible-voice-commissioning-v2"
LOCAL_TTS_PROVIDER = "estate.local.intelligible_tts"
VOICE_BINDINGS_PATH = Path("runtime/voice/resident_voice_bindings.json")
SAMPLES_DIR = Path("runtime/voice/listening_samples")


@dataclass(frozen=True)
class ResidentVoiceBinding:
    resident_id: str
    display_name: str
    gateway_model: str
    voice_id: str
    provider: str
    traits: dict[str, Any]
    provenance: str
    fallback_voice_id: str
    lifecycle_state: str = "operational"
    open_webui_playback: bool = True


VOICE_BINDINGS: dict[str, ResidentVoiceBinding] = {
    "alfred": ResidentVoiceBinding("alfred", "Alfred", "estate/alfred", "estate-local-alfred-baritone", LOCAL_TTS_PROVIDER, {"presence": "formal but warm", "cadence": "measured", "pace_wpm": 142, "pitch_hz": 132, "warmth": "medium", "confidence": "high"}, "residents/alfred.md and gateway model estate/alfred", "estate-local-neutral-low"),
    "helen": ResidentVoiceBinding("helen", "Helen", "estate/helen", "estate-local-helen-clear-mezzo", LOCAL_TTS_PROVIDER, {"presence": "clear director", "cadence": "steady", "pace_wpm": 154, "pitch_hz": 188, "warmth": "medium-high", "confidence": "high"}, "residents/helen.md and gateway model estate/helen", "estate-local-neutral-mid"),
    "ingrid": ResidentVoiceBinding("ingrid", "Ingrid", "estate/ingrid", "estate-local-ingrid-low-alto", LOCAL_TTS_PROVIDER, {"presence": "calm precise authority", "cadence": "deliberate", "pace_wpm": 132, "pitch_hz": 164, "warmth": "reserved", "confidence": "high"}, "docs/residents/ingrid/Ingrid_Voice_Identity_v0_1.md and gateway model estate/ingrid", "estate-local-neutral-low"),
    "grace": ResidentVoiceBinding("grace", "Grace", "estate/grace", "estate-local-grace-executive-alto", LOCAL_TTS_PROVIDER, {"presence": "executive operations", "cadence": "crisp", "pace_wpm": 148, "pitch_hz": 176, "warmth": "controlled", "confidence": "very high"}, "operations/residents/surfaces/grace.json and gateway model estate/grace", "estate-local-neutral-mid"),
    "evelyn": ResidentVoiceBinding("evelyn", "Evelyn", "estate/evelyn", "estate-local-evelyn-warm-contralto", LOCAL_TTS_PROVIDER, {"presence": "warm relational", "cadence": "gentle", "pace_wpm": 138, "pitch_hz": 172, "warmth": "high", "confidence": "medium-high"}, "operations/residents/surfaces/evelyn.json and gateway model estate/evelyn", "estate-local-neutral-mid"),
    "eleanor": ResidentVoiceBinding("eleanor", "Eleanor", "estate/eleanor", "estate-local-eleanor-archival-mezzo", LOCAL_TTS_PROVIDER, {"presence": "archival careful", "cadence": "exact", "pace_wpm": 136, "pitch_hz": 180, "warmth": "quiet"}, "residents/eleanor.md and gateway model estate/eleanor", "estate-local-neutral-mid"),
    "marie": ResidentVoiceBinding("marie", "Marie", "estate/marie", "estate-local-marie-research-mezzo", LOCAL_TTS_PROVIDER, {"presence": "curious analytical", "cadence": "patient", "pace_wpm": 146, "pitch_hz": 184, "warmth": "medium"}, "residents/marie.md and gateway model estate/marie", "estate-local-neutral-mid"),
    "judy": ResidentVoiceBinding("judy", "Judy", "estate/judy", "estate-local-judy-counsel-alto", LOCAL_TTS_PROVIDER, {"presence": "calm skeptical counsel", "cadence": "precise", "pace_wpm": 140, "pitch_hz": 168, "warmth": "reserved"}, "residents/judy.md and gateway model estate/judy", "estate-local-neutral-low"),
}


def _root(root: str | Path | None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT


def discover_local_tts_engine() -> dict[str, Any]:
    custom = os.environ.get("ESTATE_TTS_COMMAND")
    candidates = []
    if custom:
        parts = shlex.split(custom)
        candidates.append(("custom-command", parts[0] if parts else custom, parts or [custom]))
    for exe in ("kokoro", "f5-tts_infer-cli", "f5-tts", "espeak-ng", "espeak", "spd-say", "say"):
        found = shutil.which(exe)
        if found:
            candidates.append((exe, found, [found]))
    if candidates:
        name, path, argv = candidates[0]
        return {"available": True, "engine": name, "executable": path, "argv": argv, "reason": None}
    return {"available": False, "engine": None, "executable": None, "argv": [], "reason": "No approved local intelligible TTS engine found. Checked ESTATE_TTS_COMMAND, Kokoro, F5-TTS, espeak/espeak-ng, speech-dispatcher, and macOS say."}


def installed_capability_audit(root: str | Path | None = None) -> dict[str, Any]:
    rootp = _root(root)
    engine = discover_local_tts_engine()
    return {"schema_version": SCHEMA_VERSION, "provider": LOCAL_TTS_PROVIDER, "engine": engine, "model": "approved local intelligible text-to-speech engine; no paid external API", "endpoint": "resident_voice_commissioning.synthesize_resident_sample; Open WebUI path uses resident_gateway.chat_completion then local synthesis", "launch_method": "local command discovered from Estate environment", "health_check": local_tts_health(rootp), "repository_placeholders_distinguished": True, "placeholder_waveforms_commissioned_as_speech": False}


def local_tts_health(root: str | Path | None = None) -> dict[str, Any]:
    rootp = _root(root)
    engine = discover_local_tts_engine()
    return {"ok": bool(engine.get("available")), "provider": LOCAL_TTS_PROVIDER, "sample_dir": str(rootp / SAMPLES_DIR), "engine": engine, "streaming_supported": False, "unavailable_behavior": "synthesis returns ok=false and does not create sine/formant placeholder speech"}


def live_resident_voice_bindings(root: str | Path | None = None) -> dict[str, ResidentVoiceBinding]:
    live = set(ACTIVE_RESIDENT_MODELS.values())
    return {rid: binding for rid, binding in VOICE_BINDINGS.items() if rid in live and binding.gateway_model in ACTIVE_RESIDENT_MODELS}


def write_voice_binding_matrix(root: str | Path | None = None) -> dict[str, Any]:
    rootp = _root(root)
    payload = {"schema_version": SCHEMA_VERSION, "generated_at": int(time.time()), "bindings": {rid: asdict(binding) for rid, binding in live_resident_voice_bindings(rootp).items()}, "tts_health": local_tts_health(rootp)}
    path = rootp / VOICE_BINDINGS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def synthesize_resident_sample(resident_id: str, text: str, *, root: str | Path | None = None, sample_name: str | None = None) -> dict[str, Any]:
    rootp = _root(root)
    binding = live_resident_voice_bindings(rootp).get(resident_id)
    if binding is None:
        return {"ok": False, "reason": "resident_voice_binding_not_live", "resident_id": resident_id}
    engine = discover_local_tts_engine()
    if not engine.get("available"):
        return {"ok": False, "resident_id": resident_id, "provider": binding.provider, "voice_id": binding.voice_id, "reason": engine.get("reason"), "placeholder_generated": False}
    path = rootp / SAMPLES_DIR / resident_id / f"{sample_name or 'sample'}.wav"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        _run_tts(engine, text, path, binding)
        _assert_playable_audio(path)
    except Exception as exc:
        return {"ok": False, "resident_id": resident_id, "provider": binding.provider, "voice_id": binding.voice_id, "reason": f"local_tts_failed: {type(exc).__name__}: {exc}", "placeholder_generated": False}
    return {"ok": True, "resident_id": resident_id, "provider": binding.provider, "engine": engine.get("engine"), "voice_id": binding.voice_id, "audio_path": str(path), "bytes": path.stat().st_size, "playback_path": "Open WebUI audio element can play generated WAV file", "placeholder_generated": False}


def _run_tts(engine: dict[str, Any], text: str, output: Path, binding: ResidentVoiceBinding) -> None:
    exe = str(engine["executable"])
    name = str(engine["engine"])
    if name == "custom-command":
        cmd = [str(part) for part in engine.get("argv", [exe])] + [str(output), text]
    elif name in {"espeak", "espeak-ng"}:
        cmd = [exe, "-w", str(output), "-s", str(binding.traits.get("pace_wpm", 145)), text]
    elif name == "say":
        aiff = output.with_suffix(".aiff")
        subprocess.run([exe, "-o", str(aiff), text], check=True, text=True, capture_output=True, timeout=60)
        subprocess.run(["afconvert", str(aiff), str(output)], check=True, text=True, capture_output=True, timeout=60)
        return
    else:
        cmd = [exe, "--output", str(output), "--text", text]
    subprocess.run(cmd, check=True, text=True, capture_output=True, timeout=120)


def _assert_playable_audio(path: Path) -> None:
    if not path.exists() or path.stat().st_size <= 44:
        raise RuntimeError("TTS output file is missing or empty")
    with wave.open(str(path), "rb") as wav:
        if wav.getnframes() <= 0:
            raise RuntimeError("TTS output has no audio frames")


def synthesize_open_webui_resident_response(payload: dict[str, Any], *, root: str | Path | None = None) -> tuple[int, dict[str, Any]]:
    code, body = chat_completion(payload, root=root)
    if code != 200:
        return code, body
    resident_id = body.get("estate", {}).get("resident_id")
    content = (body.get("choices") or [{}])[0].get("message", {}).get("content") or (body.get("choices") or [{}])[0].get("delta", {}).get("content") or ""
    audio = synthesize_resident_sample(resident_id, content, root=root, sample_name=f"openwebui_{body.get('id', 'response')}")
    body.setdefault("estate", {})["audio"] = audio
    body["estate"]["open_webui_audio_integration"] = "resident gateway response passed to approved local intelligible TTS when available; unavailable status is explicit"
    return code, body


def commissioning_report(root: str | Path | None = None) -> dict[str, Any]:
    rootp = _root(root)
    matrix = write_voice_binding_matrix(rootp)
    neutral = "The Estate is ready for local audible review."
    samples = [synthesize_resident_sample(rid, neutral, root=rootp, sample_name="neutral_differentiation") for rid in matrix["bindings"]]
    return {"schema_version": SCHEMA_VERSION, "audit": installed_capability_audit(rootp), "binding_matrix_path": str(rootp / VOICE_BINDINGS_PATH), "samples": samples, "steward_review_matrix": [{"resident_id": rid, "voice_id": b["voice_id"], "review_decision": "pending_steward_listening_review", "tune_notes": ""} for rid, b in matrix["bindings"].items()], "remaining_issues": ["Human listening acceptance remains pending Steward review."] + ([] if local_tts_health(rootp)["ok"] else ["Codex environment did not locate an approved local TTS engine; run the local generation workflow on the Steward machine with Kokoro/F5-TTS or ESTATE_TTS_COMMAND."])}
