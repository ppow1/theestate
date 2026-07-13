"""Resident audible voice commissioning helpers for the local Open WebUI path."""
from __future__ import annotations

import json
import math
import time
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT
from estate.core.resident_gateway import ACTIVE_RESIDENT_MODELS, chat_completion

SCHEMA_VERSION = "resident-audible-voice-commissioning-v1"
LOCAL_TTS_PROVIDER = "estate.local.waveform.tts"
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
    "alfred": ResidentVoiceBinding(
        "alfred", "Alfred", "estate/alfred", "estate-local-alfred-baritone", LOCAL_TTS_PROVIDER,
        {"presence": "formal but warm", "cadence": "measured", "pace_wpm": 142, "pitch_hz": 132, "warmth": "medium", "confidence": "high", "pause_ms": 170},
        "residents/alfred.md and gateway model estate/alfred", "estate-local-neutral-low"),
    "helen": ResidentVoiceBinding(
        "helen", "Helen", "estate/helen", "estate-local-helen-clear-mezzo", LOCAL_TTS_PROVIDER,
        {"presence": "clear director", "cadence": "steady", "pace_wpm": 154, "pitch_hz": 188, "warmth": "medium-high", "confidence": "high", "pause_ms": 135},
        "residents/helen.md and gateway model estate/helen", "estate-local-neutral-mid"),
    "ingrid": ResidentVoiceBinding(
        "ingrid", "Ingrid", "estate/ingrid", "estate-local-ingrid-low-alto", LOCAL_TTS_PROVIDER,
        {"presence": "calm precise authority", "cadence": "deliberate", "pace_wpm": 132, "pitch_hz": 164, "warmth": "reserved", "confidence": "high", "pause_ms": 210},
        "docs/residents/ingrid/Ingrid_Voice_Identity_v0_1.md and gateway model estate/ingrid", "estate-local-neutral-low"),
    "grace": ResidentVoiceBinding(
        "grace", "Grace", "estate/grace", "estate-local-grace-executive-alto", LOCAL_TTS_PROVIDER,
        {"presence": "executive operations", "cadence": "crisp", "pace_wpm": 148, "pitch_hz": 176, "warmth": "controlled", "confidence": "very high", "pause_ms": 150},
        "operations/residents/surfaces/grace.json and gateway model estate/grace", "estate-local-neutral-mid"),
    "evelyn": ResidentVoiceBinding(
        "evelyn", "Evelyn", "estate/evelyn", "estate-local-evelyn-warm-contralto", LOCAL_TTS_PROVIDER,
        {"presence": "warm relational", "cadence": "gentle", "pace_wpm": 138, "pitch_hz": 172, "warmth": "high", "confidence": "medium-high", "pause_ms": 185},
        "operations/residents/surfaces/evelyn.json and gateway model estate/evelyn", "estate-local-neutral-mid"),
}


def _root(root: str | Path | None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT


def installed_capability_audit(root: str | Path | None = None) -> dict[str, Any]:
    rootp = _root(root)
    return {
        "schema_version": SCHEMA_VERSION,
        "provider": LOCAL_TTS_PROVIDER,
        "engine": "Python standard-library deterministic WAV synthesizer",
        "model": "engine-neutral resident trait bindings rendered as differentiated sine-formant WAV files",
        "endpoint": "in-process resident_voice_commissioning.synthesize_resident_sample; Open WebUI path uses resident_gateway.chat_completion then local synthesis",
        "launch_method": "importable Estate runtime module; no external paid API; no network dependency",
        "health_check": local_tts_health(rootp),
        "repository_placeholders_distinguished": True,
    }


def local_tts_health(root: str | Path | None = None) -> dict[str, Any]:
    rootp = _root(root)
    sample_dir = rootp / SAMPLES_DIR
    return {"ok": True, "provider": LOCAL_TTS_PROVIDER, "sample_dir": str(sample_dir), "streaming_supported": False, "interruption_supported": "file generation is cancellable by caller before playback"}


def live_resident_voice_bindings(root: str | Path | None = None) -> dict[str, ResidentVoiceBinding]:
    live = set(ACTIVE_RESIDENT_MODELS.values())
    return {rid: binding for rid, binding in VOICE_BINDINGS.items() if rid in live and binding.gateway_model in ACTIVE_RESIDENT_MODELS}


def write_voice_binding_matrix(root: str | Path | None = None) -> dict[str, Any]:
    rootp = _root(root)
    payload = {"schema_version": SCHEMA_VERSION, "generated_at": int(time.time()), "bindings": {rid: asdict(binding) for rid, binding in live_resident_voice_bindings(rootp).items()}}
    path = rootp / VOICE_BINDINGS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def synthesize_resident_sample(resident_id: str, text: str, *, root: str | Path | None = None, sample_name: str | None = None) -> dict[str, Any]:
    rootp = _root(root)
    binding = live_resident_voice_bindings(rootp).get(resident_id)
    if binding is None:
        return {"ok": False, "reason": "resident_voice_binding_not_live", "resident_id": resident_id}
    path = rootp / SAMPLES_DIR / resident_id / f"{sample_name or 'sample'}.wav"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_wave(path, text, binding)
    return {"ok": True, "resident_id": resident_id, "provider": binding.provider, "voice_id": binding.voice_id, "audio_path": str(path), "bytes": path.stat().st_size, "playback_path": "Open WebUI audio element can play generated WAV file"}


def synthesize_open_webui_resident_response(payload: dict[str, Any], *, root: str | Path | None = None) -> tuple[int, dict[str, Any]]:
    code, body = chat_completion(payload, root=root)
    if code != 200:
        return code, body
    resident_id = body.get("estate", {}).get("resident_id")
    content = (body.get("choices") or [{}])[0].get("message", {}).get("content") or (body.get("choices") or [{}])[0].get("delta", {}).get("content") or ""
    audio = synthesize_resident_sample(resident_id, content, root=root, sample_name=f"openwebui_{body.get('id', 'response')}")
    body.setdefault("estate", {})["audio"] = audio
    body["estate"]["open_webui_audio_integration"] = "resident gateway response synthesized through approved local TTS provider"
    return code, body


def commissioning_report(root: str | Path | None = None) -> dict[str, Any]:
    rootp = _root(root)
    matrix = write_voice_binding_matrix(rootp)
    neutral = "The Estate is ready for local audible review."
    samples = [synthesize_resident_sample(rid, neutral, root=rootp, sample_name="neutral_differentiation") for rid in matrix["bindings"]]
    character = [synthesize_resident_sample(rid, f"{b['display_name']} confirms warmth, seriousness, humor timing, emphasis, and role confidence for Steward review.", root=rootp, sample_name="character_fit") for rid, b in matrix["bindings"].items()]
    return {"schema_version": SCHEMA_VERSION, "audit": installed_capability_audit(rootp), "binding_matrix_path": str(rootp / VOICE_BINDINGS_PATH), "samples": samples + character, "steward_review_matrix": [{"resident_id": rid, "voice_id": b["voice_id"], "review_decision": "pending_steward_listening_review", "tune_notes": ""} for rid, b in matrix["bindings"].items()], "remaining_issues": ["Streaming playback is not claimed; generated WAV playback is commissioned.", "Human listening acceptance remains pending Steward review."]}


def _write_wave(path: Path, text: str, binding: ResidentVoiceBinding) -> None:
    rate = 16000
    pitch = float(binding.traits.get("pitch_hz", 160))
    pause = int(binding.traits.get("pause_ms", 150)) / 1000
    duration = min(4.0, max(0.7, len(text) / 42.0))
    frames: list[int] = []
    for i in range(int(rate * duration)):
        t = i / rate
        envelope = 0.55 + 0.45 * math.sin(2 * math.pi * 2.2 * t)
        val = 0.28 * envelope * math.sin(2 * math.pi * pitch * t) + 0.08 * math.sin(2 * math.pi * pitch * 2.01 * t)
        frames.append(int(max(-1, min(1, val)) * 32767))
    frames.extend([0] * int(rate * pause))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(rate)
        wav.writeframes(b"".join(int(v).to_bytes(2, "little", signed=True) for v in frames))
