import json
import os
import sys
import stat
from pathlib import Path
import textwrap
import wave

from estate.core.resident_voice_commissioning import (
    audio_metadata_for_request,
    commissioning_report,
    installed_capability_audit,
    live_resident_voice_bindings,
    safe_audio_path,
    synthesize_open_webui_resident_response,
    synthesize_resident_sample,
)


def _install_fake_tts(tmp_path, monkeypatch):
    script = tmp_path / "fake_tts.py"
    script.write_text(textwrap.dedent("""
        #!/usr/bin/env python3
        import math, sys, wave
        out = sys.argv[1]
        rate = 16000
        frames = [int(0.15 * math.sin(2 * math.pi * 220 * (i / rate)) * 32767) for i in range(rate // 4)]
        with wave.open(out, "wb") as wav:
            wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(rate)
            wav.writeframes(b"".join(int(v).to_bytes(2, "little", signed=True) for v in frames))
    """), encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("ESTATE_TTS_COMMAND", f"{sys.executable} {script}")
    return script


def test_audit_reports_intelligible_tts_availability_truthfully(tmp_path, monkeypatch):
    monkeypatch.delenv("ESTATE_TTS_COMMAND", raising=False)
    audit = installed_capability_audit(tmp_path)
    assert audit["provider"] == "estate.local.kokoro"
    assert audit["repository_placeholders_distinguished"] is True
    assert audit["placeholder_waveforms_commissioned_as_speech"] is False
    assert "health_check" in audit


def test_live_gateway_residents_have_distinct_voice_bindings():
    bindings = live_resident_voice_bindings()
    assert {"helen", "grace"} <= set(bindings)
    assert "alfred" not in bindings
    voice_ids = [binding.voice_id for binding in bindings.values()]
    assert len(voice_ids) == len(set(voice_ids))


def test_synthesis_creates_playable_wav_sample(tmp_path, monkeypatch):
    _install_fake_tts(tmp_path, monkeypatch)
    result = synthesize_resident_sample("helen", "The Estate is ready for local audible review.", root=tmp_path, sample_name="check")
    assert result["ok"] is True
    with wave.open(result["audio_path"], "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() in {16000, 24000}
        assert wav.getnframes() > 0


def test_open_webui_response_gets_local_audio_binding(tmp_path, monkeypatch):
    _install_fake_tts(tmp_path, monkeypatch)
    code, body = synthesize_open_webui_resident_response({"model": "estate/helen", "messages": [{"role": "user", "content": "Who are you?"}]}, root=tmp_path)
    assert code == 200
    assert body["estate"]["resident_id"] == "helen"
    assert body["estate"]["audio"]["ok"] is True


def test_commissioning_report_writes_matrix_and_samples(tmp_path, monkeypatch):
    _install_fake_tts(tmp_path, monkeypatch)
    report = commissioning_report(tmp_path)
    assert report["audit"]["health_check"]["ok"] is True
    matrix = json.loads((tmp_path / "runtime/voice/resident_voice_bindings.json").read_text())
    assert "helen" in matrix["bindings"] and "grace" in matrix["bindings"]
    assert all(sample["ok"] for sample in report["samples"])


def test_open_webui_audio_metadata_playback_and_path_safety(tmp_path, monkeypatch):
    _install_fake_tts(tmp_path, monkeypatch)
    code, body = synthesize_open_webui_resident_response({"model": "estate/helen", "messages": [{"role": "user", "content": "Speak."}]}, root=tmp_path)
    assert code == 200
    audio = body["estate"]["audio"]
    assert audio["ok"] is True
    assert audio["audio_url"].startswith("/v1/estate/audio/helen/")
    filename = Path(audio["audio_path"]).name
    meta_code, meta, served = audio_metadata_for_request("helen", filename, root=tmp_path)
    assert meta_code == 200
    assert meta["mime_type"] == "audio/wav"
    assert served is not None and served.exists()
    with wave.open(str(served), "rb") as wav:
        assert wav.getnframes() > 0
    traversal_code, _, traversal_path = audio_metadata_for_request("helen", "../secret.wav", root=tmp_path)
    assert traversal_code == 404
    assert traversal_path is None


def test_no_fake_audio_created_on_synthesis_failure(tmp_path, monkeypatch):
    failing = tmp_path / "fail_tts.py"
    failing.write_text("import sys; sys.exit(7)\n", encoding="utf-8")
    monkeypatch.delenv("ESTATE_KOKORO_COMMAND", raising=False)
    monkeypatch.delenv("ESTATE_KOKORO_PYTHON", raising=False)
    monkeypatch.setenv("ESTATE_TTS_COMMAND", f"{sys.executable} {failing}")
    result = synthesize_resident_sample("helen", "This should fail.", root=tmp_path, sample_name="failure")
    assert result["ok"] is False
    assert result["placeholder_generated"] is False
    assert not safe_audio_path(tmp_path, "helen", "failure").exists()
