"""Open WebUI multi-resident gateway integration helpers.

These helpers normalize Open WebUI/OpenAI-style room requests and shape
identity-preserving multi-resident response envelopes for the canonical resident
gateway without creating a duplicate gateway or authority path.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable
import json
import time

SUPPORTED_OBJECT = "estate.open_webui.multi_resident_gateway_plan.v1"
DEFAULT_ROOM_MODEL = "estate/conference-room"


@dataclass(frozen=True)
class ResidentDescriptor:
    resident_id: str
    model_id: str
    display_name: str
    role: str = "resident"
    available: bool = True

    def to_openai_model(self) -> dict[str, Any]:
        return {
            "id": self.model_id,
            "object": "model",
            "created": 0,
            "owned_by": "estate",
            "estate": {
                "resident_id": self.resident_id,
                "display_name": self.display_name,
                "role": self.role,
                "multi_resident_gateway_capable": True,
                "privileged_actions_enabled": False,
            },
        }


@dataclass(frozen=True)
class GatewayIntegrationPlan:
    residents: tuple[ResidentDescriptor, ...]
    room_model_id: str = DEFAULT_ROOM_MODEL
    staged: bool = False
    installed: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)

    def model_catalog(self) -> dict[str, Any]:
        models = [resident.to_openai_model() for resident in self.residents]
        models.append({
            "id": self.room_model_id,
            "object": "model",
            "created": 0,
            "owned_by": "estate",
            "estate": {
                "surface": "multi_resident_room",
                "display_name": "Estate multi-resident room",
                "multi_resident_gateway_capable": True,
                "privileged_actions_enabled": False,
                "staged_work_is_installed": True,
            },
        })
        return {"object": "list", "data": models, "estate": self.status()}

    def status(self) -> dict[str, Any]:
        return {
            "object": SUPPORTED_OBJECT,
            "staged": self.staged,
            "installed": self.installed,
            "resident_count": len(self.residents),
            "room_model_id": self.room_model_id,
            "notes": list(self.notes),
        }


def default_plan() -> GatewayIntegrationPlan:
    return GatewayIntegrationPlan(
        residents=(
            ResidentDescriptor("alfred", "estate/alfred", "Alfred", "Estate Butler"),
            ResidentDescriptor("helen", "estate/helen", "Helen", "Operations Director"),
            ResidentDescriptor("ingrid", "estate/ingrid", "Ingrid", "Privacy and Governance"),
            ResidentDescriptor("grace", "estate/grace", "Grace", "Steward-appointed Director"),
        ),
        notes=(
            "Open WebUI compatibility is installed through the canonical Estate resident gateway.",
            "Room requests route through the canonical gateway and active room core without privileged action execution.",
        ),
    )


def normalize_open_webui_request(payload: dict[str, Any], *, default_model: str = DEFAULT_ROOM_MODEL) -> dict[str, Any]:
    """Normalize an Open WebUI/OpenAI-style chat payload without executing it."""
    messages = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    targets = metadata.get("resident_targets") or payload.get("resident_targets") or []
    if isinstance(targets, str):
        targets = [targets]
    normalized_targets = [str(target).strip().lower() for target in targets if str(target).strip()]
    return {
        "model": str(payload.get("model") or default_model),
        "stream": bool(payload.get("stream") is True),
        "messages": [
            {"role": str(msg.get("role") or "user"), "content": str(msg.get("content") or "")}
            for msg in messages
            if isinstance(msg, dict)
        ],
        "room_id": str(metadata.get("room_id") or payload.get("room_id") or ""),
        "session_id": str(metadata.get("session_id") or payload.get("session_id") or payload.get("conversation_id") or ""),
        "resident_targets": normalized_targets,
        "gateway_execution": "canonical_resident_gateway",
    }


def attributed_response_envelope(*, model: str, room_id: str, resident_turns: Iterable[dict[str, Any]], stream: bool = False) -> dict[str, Any]:
    """Build an OpenAI-compatible response with identity-preserving content."""
    turns = list(resident_turns)
    created = int(time.time())
    content = "\n\n".join(
        f"{turn.get('display_name') or turn.get('resident_id')}: {turn.get('content', '')}".strip()
        for turn in turns
    )
    choice_key = "delta" if stream else "message"
    body_choice = {"role": "assistant", "content": content}
    return {
        "id": f"chatcmpl-staged-{room_id or 'room'}",
        "object": "chat.completion.chunk" if stream else "chat.completion",
        "created": created,
        "model": model,
        "choices": [{"index": 0, choice_key: body_choice, "finish_reason": None if stream else "stop"}],
        "estate": {
            "room_id": room_id,
            "resident_turns": turns,
            "attribution_preserved": True,
            "privileged_action_executed": False,
            "gateway_execution": "canonical_resident_gateway",
        },
    }


def sse_lines(body: dict[str, Any]) -> list[str]:
    final = {"id": body["id"], "object": "chat.completion.chunk", "created": body["created"], "model": body["model"], "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
    return [f"data: {json.dumps(body, sort_keys=True)}", f"data: {json.dumps(final, sort_keys=True)}", "data: [DONE]"]
