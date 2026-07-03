import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from estate.core.alfred import plan_goal
from estate.core.paths import ESTATE_ROOT


VOICE_RUNTIME_DIR = ESTATE_ROOT / "runtime" / "voice"


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class VoiceProfile:
    profile_id: str
    resident_id: str
    display_name: str
    preferred_tts_voice: str | None = None
    locale: str = "en-US"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SpeechToTextResult:
    text: str
    confidence: float | None = None
    segments: list[dict[str, Any]] = field(default_factory=list)
    provider: str = "mock"


@dataclass(frozen=True)
class TextToSpeechResult:
    text: str
    audio_path: str | None = None
    provider: str = "mock"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SillyTavernExchange:
    character: str
    prompt: str
    response: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VoiceSession:
    session_id: str
    profile: VoiceProfile
    started_at: str = field(default_factory=_now)
    ended_at: str | None = None
    interactions: list[dict[str, Any]] = field(default_factory=list)

    def record(self, event_type: str, payload: dict[str, Any]):
        event = {"at": _now(), "event_type": event_type, "payload": payload}
        self.interactions.append(event)
        return event

    def close(self):
        self.ended_at = _now()
        return self


class SpeechToTextAdapter(Protocol):
    provider_id: str

    def transcribe(self, audio: bytes | Path, *, profile: VoiceProfile | None = None) -> SpeechToTextResult:
        ...


class TextToSpeechAdapter(Protocol):
    provider_id: str

    def synthesize(self, text: str, *, profile: VoiceProfile | None = None) -> TextToSpeechResult:
        ...


class SillyTavernAdapter(Protocol):
    provider_id: str

    def exchange(self, prompt: str, *, character: str, profile: VoiceProfile | None = None) -> SillyTavernExchange:
        ...


class MockSpeechToTextAdapter:
    provider_id = "mock.stt"

    def __init__(self, text=""):
        self.text = text

    def transcribe(self, audio, *, profile=None):
        return SpeechToTextResult(text=self.text, confidence=1.0, provider=self.provider_id)


class MockTextToSpeechAdapter:
    provider_id = "mock.tts"

    def synthesize(self, text, *, profile=None):
        return TextToSpeechResult(text=text, provider=self.provider_id, metadata={"profile_id": getattr(profile, "profile_id", None)})


class MockSillyTavernAdapter:
    provider_id = "mock.sillytavern"

    def exchange(self, prompt, *, character, profile=None):
        return SillyTavernExchange(character=character, prompt=prompt, response=f"{character}: {prompt}")


class VoiceEngineNotConfigured(RuntimeError):
    pass


class VoiceIntegrationFramework:
    def __init__(self, *, stt=None, tts=None, sillytavern=None, root=None):
        self.stt = stt
        self.tts = tts
        self.sillytavern = sillytavern
        self.root = Path(root) if root is not None else ESTATE_ROOT

    def start_session(self, profile: VoiceProfile, session_id: str | None = None):
        sid = session_id or "voice_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return VoiceSession(session_id=sid, profile=profile)

    def transcribe(self, session: VoiceSession, audio):
        if self.stt is None:
            session.record("stt_unconfigured", {"ok": False, "reason": "no_stt_adapter_configured"})
            return {"ok": False, "reason": "no_stt_adapter_configured"}
        result = self.stt.transcribe(audio, profile=session.profile)
        session.record("speech_to_text", asdict(result))
        return {"ok": True, "result": result}

    def speak(self, session: VoiceSession, text):
        if self.tts is None:
            session.record("tts_unconfigured", {"ok": False, "reason": "no_tts_adapter_configured", "text": text})
            return {"ok": False, "reason": "no_tts_adapter_configured"}
        result = self.tts.synthesize(text, profile=session.profile)
        session.record("text_to_speech", asdict(result))
        return {"ok": True, "result": result}

    def plan_spoken_command(self, session: VoiceSession, spoken_text: str):
        plan = plan_goal(spoken_text)
        session.record("estate_command_plan", {"spoken_text": spoken_text, "authority_path": "alfred.plan_goal", "plan": plan})
        return plan

    def sillytavern_exchange(self, session: VoiceSession, prompt, *, character="Alfred"):
        if self.sillytavern is None:
            session.record("sillytavern_unconfigured", {"ok": False, "reason": "no_sillytavern_adapter_configured"})
            return {"ok": False, "reason": "no_sillytavern_adapter_configured"}
        result = self.sillytavern.exchange(prompt, character=character, profile=session.profile)
        session.record("sillytavern_exchange", asdict(result))
        return {"ok": True, "result": result}

    def write_transcript(self, session: VoiceSession, *, significant=True):
        transcript_dir = self.root / "runtime" / "voice" / "transcripts"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "session_id": session.session_id,
            "profile": asdict(session.profile),
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "significant": significant,
            "audit_artifact": bool(significant),
            "interactions": session.interactions,
        }
        path = transcript_dir / f"{session.session_id}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return {"ok": True, "path": str(path), "transcript": payload}
