import json
import wave

from estate.core.resident_voice_commissioning import (
    commissioning_report,
    installed_capability_audit,
    live_resident_voice_bindings,
    synthesize_open_webui_resident_response,
    synthesize_resident_sample,
)


def test_audit_reports_verified_local_tts_engine(tmp_path):
    audit = installed_capability_audit(tmp_path)
    assert audit["health_check"]["ok"] is True
    assert audit["provider"] == "estate.local.waveform.tts"
    assert audit["repository_placeholders_distinguished"] is True


def test_live_gateway_residents_have_distinct_voice_bindings():
    bindings = live_resident_voice_bindings()
    assert {"alfred", "helen", "ingrid", "grace", "evelyn"} <= set(bindings)
    voice_ids = [binding.voice_id for binding in bindings.values()]
    assert len(voice_ids) == len(set(voice_ids))


def test_synthesis_creates_playable_wav_sample(tmp_path):
    result = synthesize_resident_sample("ingrid", "The Estate is ready for local audible review.", root=tmp_path, sample_name="check")
    assert result["ok"] is True
    with wave.open(result["audio_path"], "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == 16000
        assert wav.getnframes() > 0


def test_open_webui_response_gets_local_audio_binding(tmp_path):
    code, body = synthesize_open_webui_resident_response({"model": "estate/helen", "messages": [{"role": "user", "content": "Who are you?"}]}, root=tmp_path)
    assert code == 200
    assert body["estate"]["resident_id"] == "helen"
    assert body["estate"]["audio"]["ok"] is True


def test_commissioning_report_writes_matrix_and_samples(tmp_path):
    report = commissioning_report(tmp_path)
    assert report["audit"]["health_check"]["ok"] is True
    matrix = json.loads((tmp_path / "runtime/voice/resident_voice_bindings.json").read_text())
    assert "alfred" in matrix["bindings"]
    assert all(sample["ok"] for sample in report["samples"])
