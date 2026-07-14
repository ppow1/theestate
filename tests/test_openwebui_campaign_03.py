import wave
from pathlib import Path

from estate.core.openwebui_resident_package import resident_package, visual_projection
from estate.core.resident_gateway import chat_completion, models_payload
from estate.core.resident_voice_commissioning import (
    build_kokoro_command,
    commissioned_voice_projection,
    discover_kokoro,
    safe_audio_path,
    synthesize_resident_sample,
    audio_metadata_for_request,
)


def test_canonical_helen_and_grace_bindings():
    helen = commissioned_voice_projection("helen")
    grace = commissioned_voice_projection("grace")
    assert helen["voice_state"] == "canonical"
    assert helen["voice_id"] == "af_bella"
    assert helen["voice_speed"] == 0.92
    assert grace["voice_state"] == "canonical"
    assert grace["voice_id"] == "af_jessica"
    assert grace["voice_speed"] == 1.0


def test_uncommissioned_resident_truth_state():
    alfred = commissioned_voice_projection("alfred")
    assert alfred["voice_state"] == "uncommissioned"
    assert alfred["voice_id"] is None
    assert alfred["tts_available"] is False


def test_resident_package_projection_and_catalog():
    package = resident_package("estate/helen", "helen")
    assert package["display_name"] == "Helen"
    assert package["identity_source_hash"]
    assert package["voice_id"] == "af_bella"
    catalog = models_payload()
    estate_helen = next(m for m in catalog["data"] if m["id"] == "estate/helen")
    assert estate_helen["name"] == "Helen"
    assert estate_helen["estate"]["resident_gateway_capable"] is True
    assert estate_helen["estate"]["privileged_actions_enabled"] is False


def test_identity_visual_and_response_envelope_metadata(tmp_path):
    code, body = chat_completion({"model":"estate/grace","messages":[{"role":"user","content":"Instantiate Grace."}]}, root=tmp_path)
    assert code == 200
    estate = body["estate"]
    assert estate["identity_hash"]
    assert estate["identity_schema_version"]
    assert estate["voice"]["voice_id"] == "af_jessica"
    assert "visual" in estate
    assert estate["privileged_action_executed"] is False


def test_visual_truth_state_behavior():
    visual = visual_projection("helen", "Helen")
    assert visual["visual_state"] in {"canonical", "provisional", "placeholder", "restricted", "unavailable"}
    if visual["visual_state"] != "canonical":
        assert visual["avatar_uri"] is None


def test_kokoro_command_construction_and_failure_path(tmp_path):
    out = tmp_path / "out.wav"
    cmd = build_kokoro_command({"argv":["python"]}, "hello", out, "af_bella", 0.92)
    assert cmd[:3] == ["python", "-m", "kokoro"]
    assert "--output-file" in cmd or "-o" in cmd
    assert "--output" not in cmd
    assert "af_bella" in cmd
    result = synthesize_resident_sample("alfred", "hello", root=tmp_path)
    assert result["ok"] is False
    assert result["placeholder_generated"] is False


def test_generated_file_validation_and_audio_contract(tmp_path):
    path = safe_audio_path(tmp_path, "helen", "turn.wav")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(24000); wav.writeframes(b"\x00\x00" * 10)
    code, meta, served = audio_metadata_for_request("helen", "turn.wav", root=tmp_path)
    assert code == 200
    assert meta["mime_type"] == "audio/wav"
    assert served == path
    code, _, _ = audio_metadata_for_request("helen", "../secret.wav", root=tmp_path)
    assert code == 404


def test_kokoro_env_preserves_raw_windows_path_and_parses_quoted_command(monkeypatch):
    raw = r"A:\AI\TTS\kokoro_py311\Scripts\python.exe"
    monkeypatch.setenv("ESTATE_KOKORO_COMMAND", raw)
    engine = discover_kokoro()
    assert engine["argv"] == [raw]
    assert engine["executable"] == raw

    quoted = f'"{raw}" --flag value'
    monkeypatch.setenv("ESTATE_KOKORO_COMMAND", quoted)
    engine = discover_kokoro()
    assert engine["argv"][0] == raw
    assert engine["argv"][1:] == ["--flag", "value"]


def test_kokoro_command_uses_supported_output_flag_for_python_and_exe(tmp_path):
    out = tmp_path / "out.wav"
    py_cmd = build_kokoro_command({"engine":"kokoro", "argv":["python.exe"]}, "hello", out, "af_bella", 0.92)
    assert py_cmd[:3] == ["python.exe", "-m", "kokoro"]
    assert "--output-file" in py_cmd or "-o" in py_cmd
    assert "--output" not in py_cmd

    exe_cmd = build_kokoro_command({"engine":"kokoro", "argv":["kokoro.exe"]}, "hello", out, "af_jessica", 1.0)
    assert exe_cmd[0] == "kokoro.exe"
    assert "--output-file" in exe_cmd or "-o" in exe_cmd
    assert "--output" not in exe_cmd
