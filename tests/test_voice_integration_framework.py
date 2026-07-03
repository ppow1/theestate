import json

from estate.core.voice import (
    MockSillyTavernAdapter,
    MockSpeechToTextAdapter,
    MockTextToSpeechAdapter,
    SpeechToTextAdapter,
    TextToSpeechAdapter,
    VoiceIntegrationFramework,
    VoiceProfile,
)


def profile():
    return VoiceProfile(profile_id="voice-alfred", resident_id="RES-000001", display_name="Alfred")


def test_adapter_interfaces_and_mock_providers_work_at_runtime():
    stt: SpeechToTextAdapter = MockSpeechToTextAdapter("summarize the morning briefing")
    tts: TextToSpeechAdapter = MockTextToSpeechAdapter()
    framework = VoiceIntegrationFramework(stt=stt, tts=tts, sillytavern=MockSillyTavernAdapter())
    session = framework.start_session(profile(), session_id="voice_test")

    transcription = framework.transcribe(session, b"audio")
    speech = framework.speak(session, "Ready for review.")
    exchange = framework.sillytavern_exchange(session, "Report status", character="Alfred")

    assert transcription["ok"] is True
    assert transcription["result"].text == "summarize the morning briefing"
    assert speech["result"].provider == "mock.tts"
    assert exchange["result"].response == "Alfred: Report status"
    assert [event["event_type"] for event in session.interactions] == ["speech_to_text", "text_to_speech", "sillytavern_exchange"]


def test_spoken_commands_use_alfred_authority_path_without_execution():
    framework = VoiceIntegrationFramework(stt=MockSpeechToTextAdapter("plan a code review"))
    session = framework.start_session(profile(), session_id="voice_command")

    plan = framework.plan_spoken_command(session, "plan a code review")

    assert plan["goal"] == "plan a code review"
    assert session.interactions[-1]["event_type"] == "estate_command_plan"
    assert session.interactions[-1]["payload"]["authority_path"] == "alfred.plan_goal"


def test_transcript_generation_creates_written_audit_artifact(tmp_path):
    framework = VoiceIntegrationFramework(stt=MockSpeechToTextAdapter("summarize"), root=tmp_path)
    session = framework.start_session(profile(), session_id="voice_audit")
    framework.transcribe(session, b"audio")
    session.close()

    result = framework.write_transcript(session)
    transcript = json.loads((tmp_path / "runtime/voice/transcripts/voice_audit.json").read_text())

    assert result["ok"] is True
    assert transcript["audit_artifact"] is True
    assert transcript["interactions"][0]["event_type"] == "speech_to_text"


def test_no_voice_engine_configured_degrades_gracefully():
    framework = VoiceIntegrationFramework()
    session = framework.start_session(profile(), session_id="voice_missing")

    stt = framework.transcribe(session, b"audio")
    tts = framework.speak(session, "Hello")
    tavern = framework.sillytavern_exchange(session, "Hello")

    assert stt == {"ok": False, "reason": "no_stt_adapter_configured"}
    assert tts == {"ok": False, "reason": "no_tts_adapter_configured"}
    assert tavern == {"ok": False, "reason": "no_sillytavern_adapter_configured"}
    assert [event["event_type"] for event in session.interactions] == ["stt_unconfigured", "tts_unconfigured", "sillytavern_unconfigured"]
