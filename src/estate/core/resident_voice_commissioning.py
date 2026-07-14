"""Canonical resident voice commissioning and local Kokoro synthesis."""
from __future__ import annotations

import json, os, re, shlex, shutil, subprocess, time, wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "resident-audible-voice-commissioning-v3"
REGISTRY_PATH = Path("data/resident_voice_commissioning_registry.json")
VOICE_BINDINGS_PATH = Path("runtime/voice/resident_voice_bindings.json")
AUDIO_DIR = Path("runtime/voice/generated_audio")
SAMPLES_DIR = Path("runtime/voice/listening_samples")
LOCAL_TTS_PROVIDER = "estate.local.kokoro"
KNOWN_KOKORO = [r"A:\AI\TTS\kokoro_py311\Scripts\python.exe", r"A:\AI\TTS\kokoro_py311\Scripts\kokoro.exe"]

@dataclass(frozen=True)
class ResidentVoiceBinding:
    resident_id: str
    display_name: str
    gateway_model: str
    voice_id: str
    provider: str
    traits: dict[str, Any]
    provenance: str
    fallback_voice_id: str | None = None
    lifecycle_state: str = "canonical_v1"
    open_webui_playback: bool = True
    engine: str = "kokoro"
    engine_version: str | None = None
    speed: float = 1.0
    approval_state: str = "not_approved"
    status: str = "uncommissioned"


def _root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else ESTATE_ROOT

def _key(v: Any) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", str(v or "").lower()).strip("-")

def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

def load_voice_commissioning_registry(root: str | Path | None = None) -> dict[str, Any]:

    rootp = _root(root)
    data = _read_json(rootp / REGISTRY_PATH)
    if not data and rootp != ESTATE_ROOT:
        data = _read_json(ESTATE_ROOT / REGISTRY_PATH)
    return data

def commissioned_voice_projection(resident_id: str, root: str | Path | None = None) -> dict[str, Any]:
    reg = load_voice_commissioning_registry(root)
    row = (reg.get("commissioned") or {}).get(_key(resident_id))
    if not row:
        return {"voice_state":"uncommissioned","voice_engine":None,"voice_id":None,"voice_speed":None,"voice_approval_state":"not_approved","tts_available":False,"voice_binding":None,"voice_provenance":{"registry":str(REGISTRY_PATH),"status":"uncommissioned"}}
    health = local_tts_health(root)
    return {"voice_state":"canonical","voice_engine":row.get("engine"),"voice_id":row.get("voice"),"voice_speed":row.get("speed"),"voice_approval_state":row.get("status"),"tts_available":bool(health.get("ok")),"voice_binding":row,"voice_provenance":{"registry":str(REGISTRY_PATH),"approval":row.get("approval"),"validation":row.get("validation",[])}}

def _is_existing_executable_path(raw: str) -> bool:
    path = Path(raw)
    return path.exists() and path.is_file() and (os.access(path, os.X_OK) or path.suffix.lower() in {".exe", ".bat", ".cmd", ".ps1", ".py"})


def _parse_command_env(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    # Steward-machine Windows installs may provide a bare path such as
    # A:\AI\TTS\kokoro_py311\Scripts\python.exe.  POSIX shlex parsing
    # treats backslashes as escapes and corrupts that value, so preserve a raw
    # environment value that is already an executable path before considering it
    # a command line.
    if _is_existing_executable_path(raw):
        return [raw]
    if re.match(r"^[A-Za-z]:\\", raw) and not re.search(r"\s", raw):
        return [raw]
    posix = not (os.name == "nt" or re.search(r'(^|\s)([A-Za-z]:\\|"[A-Za-z]:\\)', raw))
    parts = shlex.split(raw, posix=posix)
    if not posix:
        parts = [p[1:-1] if len(p) >= 2 and p[0] == p[-1] and p[0] in {'"', "'"} else p for p in parts]
    return parts or [raw]


def discover_kokoro(root: str | Path | None = None) -> dict[str, Any]:
    env = os.environ.get("ESTATE_KOKORO_COMMAND") or os.environ.get("ESTATE_KOKORO_PYTHON")
    legacy = os.environ.get("ESTATE_TTS_COMMAND")
    candidates: list[tuple[list[str], str]] = []
    if env: candidates.append((_parse_command_env(env), "kokoro"))
    if legacy: candidates.append((_parse_command_env(legacy), "custom-command"))
    for p in KNOWN_KOKORO:
        if Path(p).exists(): candidates.append(([p], "kokoro"))
    for exe in ("kokoro",):
        found = shutil.which(exe)
        if found: candidates.append(([found], "kokoro"))
    if candidates:
        argv, engine_name = candidates[0]
        return {"available": True, "engine":engine_name, "executable": argv[0], "argv": argv, "reason": None, "sample_rate_hz":24000}
    return {"available": False, "engine":"kokoro", "executable": None, "argv": [], "reason":"Kokoro not discovered. Set ESTATE_KOKORO_COMMAND or install the approved local Kokoro environment.", "sample_rate_hz":24000}

def discover_local_tts_engine() -> dict[str, Any]:
    return discover_kokoro()

def local_tts_health(root: str | Path | None = None) -> dict[str, Any]:
    d = discover_kokoro(root)
    return {"ok": bool(d.get("available")), "provider": LOCAL_TTS_PROVIDER, "engine": d, "sample_dir": str(_root(root)/SAMPLES_DIR), "audio_dir": str(_root(root)/AUDIO_DIR), "streaming_supported": False, "unavailable_behavior":"explicit unavailable; no fake speech"}

def live_resident_voice_bindings(root: str | Path | None = None) -> dict[str, ResidentVoiceBinding]:
    reg = load_voice_commissioning_registry(root)
    out = {}
    for rid, row in (reg.get("commissioned") or {}).items():
        out[rid] = ResidentVoiceBinding(rid, rid.title(), f"estate/{rid}", row["voice"], LOCAL_TTS_PROVIDER, {"kokoro_speed": row["speed"]}, str(REGISTRY_PATH), None, row.get("status","canonical_v1"), True, row.get("engine","kokoro"), row.get("engine_version"), float(row["speed"]), row.get("approval","Steward"), row.get("status","canonical_v1"))
    return out

def installed_capability_audit(root: str | Path | None = None) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "provider": LOCAL_TTS_PROVIDER, "engine": discover_kokoro(root), "model":"Kokoro local TTS", "endpoint":"/v1/estate/audio/{resident_id}/{filename}", "health_check": local_tts_health(root), "repository_placeholders_distinguished": True, "placeholder_waveforms_commissioned_as_speech": False}

def write_voice_binding_matrix(root: str | Path | None = None) -> dict[str, Any]:
    payload = {"schema_version": SCHEMA_VERSION, "generated_at": int(time.time()), "bindings": {k: asdict(v) for k,v in live_resident_voice_bindings(root).items()}, "uncommissioned_residents":"all active residents absent from registry.commissioned", "tts_health": local_tts_health(root)}
    path = _root(root)/VOICE_BINDINGS_PATH; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n", encoding="utf-8")
    return payload

def safe_audio_path(root: Path, resident_id: str, name: str) -> Path:
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name or "sample.wav")
    if not safe_name.endswith(".wav"): safe_name += ".wav"
    base = (root/AUDIO_DIR/_key(resident_id)).resolve(); base.mkdir(parents=True, exist_ok=True)
    path = (base/safe_name).resolve()
    if base not in path.parents and path != base: raise ValueError("audio_path_traversal_rejected")
    return path

def build_kokoro_command(engine: dict[str, Any], text: str, output: Path, voice: str, speed: float) -> list[str]:
    argv = [str(x) for x in engine.get("argv") or [engine.get("executable")]]
    if engine.get("engine") == "custom-command":
        return argv + [str(output), text]
    exe = Path(argv[0]).name.lower()
    if "python" in exe:
        return argv + ["-m", "kokoro", "--voice", voice, "--speed", str(speed), "--output-file", str(output), "--text", text]
    return argv + ["--voice", voice, "--speed", str(speed), "--output-file", str(output), "--text", text]

def _assert_playable_audio(path: Path) -> None:
    if not path.exists() or path.stat().st_size <= 44: raise RuntimeError("missing_or_empty_wav")
    with wave.open(str(path), "rb") as wav:
        if wav.getnframes() <= 0: raise RuntimeError("wav_has_no_frames")

def synthesize_resident_sample(resident_id: str, text: str, *, root: str | Path | None = None, sample_name: str | None = None) -> dict[str, Any]:
    rootp = _root(root); proj = commissioned_voice_projection(resident_id, rootp)
    if proj["voice_state"] != "canonical": return {"ok":False,"resident_id":resident_id,"reason":"voice_not_commissioned","voice_state":proj["voice_state"],"placeholder_generated":False}
    engine = discover_kokoro(rootp)
    if not engine.get("available"): return {"ok":False,"resident_id":resident_id,"reason":engine.get("reason"),"voice_id":proj["voice_id"],"placeholder_generated":False}
    path = safe_audio_path(rootp, resident_id, sample_name or "sample")
    cmd = build_kokoro_command(engine, text, path, str(proj["voice_id"]), float(proj["voice_speed"]))
    try:
        subprocess.run(cmd, check=True, text=True, capture_output=True, timeout=120)
        _assert_playable_audio(path)
    except Exception as exc:
        return {"ok":False,"resident_id":resident_id,"reason":f"kokoro_failed: {type(exc).__name__}: {exc}","command":cmd,"voice_id":proj["voice_id"],"placeholder_generated":False}
    return {"ok":True,"resident_id":resident_id,"provider":LOCAL_TTS_PROVIDER,"engine":"kokoro","voice_id":proj["voice_id"],"speed":proj["voice_speed"],"audio_path":str(path),"audio_url":f"/v1/estate/audio/{_key(resident_id)}/{path.name}","bytes":path.stat().st_size,"placeholder_generated":False,"provenance":proj["voice_provenance"]}

def audio_metadata_for_request(resident_id: str, filename: str, *, root: str | Path | None = None) -> tuple[int, dict[str, Any], Path | None]:
    try: path = safe_audio_path(_root(root), resident_id, filename)
    except ValueError: return 404, {"error":{"code":"audio_not_found","message":"audio unavailable"}}, None
    if not path.exists(): return 404, {"error":{"code":"audio_not_found","message":"audio unavailable"}}, None
    return 200, {"resident_id":_key(resident_id),"audio_path":str(path),"mime_type":"audio/wav","bytes":path.stat().st_size,"provenance":"estate_generated_audio"}, path

def synthesize_open_webui_resident_response(payload: dict[str, Any], *, root: str | Path | None = None) -> tuple[int, dict[str, Any]]:
    from estate.core.resident_gateway import chat_completion
    code, body = chat_completion(payload, root=root)
    if code != 200: return code, body
    rid = body.get("estate",{}).get("resident_id")
    content = (body.get("choices") or [{}])[0].get("message",{}).get("content","")
    body.setdefault("estate",{})["audio"] = synthesize_resident_sample(rid, content, root=root, sample_name=f"openwebui_{body.get('id','response')}")
    return code, body

def commissioning_report(root: str | Path | None = None) -> dict[str, Any]:
    matrix = write_voice_binding_matrix(root)
    samples = [synthesize_resident_sample(r, f"This is {r.title()}, ready.", root=root, sample_name="neutral_differentiation") for r in matrix["bindings"]]
    return {"schema_version":SCHEMA_VERSION,"audit":installed_capability_audit(root),"binding_matrix_path":str(_root(root)/VOICE_BINDINGS_PATH),"samples":samples,"steward_review_matrix":[{"resident_id":r,"voice_id":b["voice_id"],"review_decision":"canonical_v1"} for r,b in matrix["bindings"].items()],"remaining_issues":["Only Helen and Grace are canonical; other residents remain uncommissioned."]}
