"""Local OpenAI-compatible gateway for Estate residents."""
from __future__ import annotations
import base64, hashlib, json, os, time
from urllib.parse import unquote_to_bytes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from estate.core.resident_interaction import process_chat, local_llm_status, _root
from estate.core.multi_resident_room import create_room, invite_participant, accept_participant, submit_user_turn, plan_resident_turns, record_resident_turn
from estate.core.open_webui_multi_resident_gateway import DEFAULT_ROOM_MODEL, attributed_response_envelope, normalize_open_webui_request
from estate.core.resident_identity_composition import compose_resident_identity
from estate.core.openwebui_resident_package import resident_package
from estate.core.openwebui_engineering_workflow import initiate_engineering_assignment_from_chat

ACTIVE_RESIDENT_MODELS = {
    "estate/alfred": "alfred",
    "estate/helen": "helen",
    "estate/ingrid": "ingrid",
    "estate/grace": "grace",
    "estate/evelyn": "evelyn",
    "estate/eleanor": "eleanor",
    "estate/marie": "marie",
    "estate/judy": "judy",
}
STATUS_PATH = Path("runtime/resident_gateway/status.json")


def models_payload(root=None) -> dict[str, Any]:
    # Prefer the resident-first Open WebUI catalog when its richer metadata is
    # available; keep this gateway as the single canonical execution path.
    try:
        from estate.core.openwebui_resident_surface import resident_model_catalog
        payload = resident_model_catalog(root)
        payload["data"].append({"id": DEFAULT_ROOM_MODEL, "object":"model", "created":0, "owned_by":"estate", "estate":{"surface":"multi_resident_room", "display_name":"Estate multi-resident room", "multi_resident_gateway_capable": True, "privileged_actions_enabled": False}})
        return payload
    except Exception:
        data = [{"id": mid,"object":"model","created":0,"owned_by":"estate","estate":{"resident_id": rid,"privileged_actions_enabled":False}} for mid, rid in ACTIVE_RESIDENT_MODELS.items()]
        data.append({"id": DEFAULT_ROOM_MODEL, "object":"model", "created":0, "owned_by":"estate", "estate":{"surface":"multi_resident_room", "multi_resident_gateway_capable": True, "privileged_actions_enabled": False}})
        return {"object":"list","data":data}


def chat_completion(payload: dict[str, Any], *, root=None) -> tuple[int, dict[str, Any]]:
    model = payload.get("model")
    if model == DEFAULT_ROOM_MODEL:
        return _room_chat_completion(payload, root=root)
    if model not in ACTIVE_RESIDENT_MODELS:
        return 404, {"error":{"message":f"Unsupported Estate resident model: {model}","type":"invalid_request_error","code":"unsupported_model"}}
    if payload.get("stream") is True:
        return _streaming_chat_completion(payload, root=root)
    return _non_streaming_chat_completion(payload, root=root)


def _message_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") in {"text", "input_text"}:
                parts.append(str(item.get("text") or ""))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(content or "")


def _latest_user_message(messages: Any) -> str:
    if not isinstance(messages, list):
        return ""
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            text = _message_text(message.get("content")).strip()
            if text:
                return text
    return ""


def _data_url_attachment(url: str, *, filename: str | None = None) -> dict[str, Any] | None:
    """Translate an OpenAI image data URL without retaining it in diagnostics."""
    if not url.startswith("data:image/") or "," not in url:
        return None
    header, encoded = url.split(",", 1)
    mime_type = header[5:].split(";", 1)[0].lower()
    if ";base64" in header.lower():
        # Validate here so malformed Open WebUI content fails as a client error,
        # rather than being copied into a prompt or a diagnostic report.
        base64.b64decode(encoded, validate=True)
        data_base64 = encoded
    else:
        data_base64 = base64.b64encode(unquote_to_bytes(encoded)).decode("ascii")
    return {"kind": "image", "source": "open_webui", "mime_type": mime_type,
            "original_filename": filename or "image", "data_base64": data_base64}


def _normalize_gateway_attachment(candidate: Any) -> dict[str, Any] | None:
    if not isinstance(candidate, dict):
        return None
    wrapped = candidate.get("file") if isinstance(candidate.get("file"), dict) else candidate
    filename = wrapped.get("name") or wrapped.get("filename") or wrapped.get("original_filename")
    mime_type = wrapped.get("mime_type") or wrapped.get("content_type") or wrapped.get("type")
    image_url = wrapped.get("image_url") or wrapped.get("url")
    if isinstance(image_url, dict):
        image_url = image_url.get("url")
    if isinstance(image_url, str):
        normalized = _data_url_attachment(image_url, filename=filename)
        if normalized:
            return normalized
    data = wrapped.get("data_base64") or wrapped.get("file_data") or wrapped.get("data")
    if isinstance(data, str) and data.startswith("data:image/"):
        return _data_url_attachment(data, filename=filename)
    if isinstance(data, str) and (str(mime_type or "").lower().startswith("image/") or candidate.get("kind") == "image"):
        return {"kind": "image", "source": "open_webui", "mime_type": str(mime_type).lower(),
                "original_filename": filename or "image", "data_base64": data}
    storage_path = wrapped.get("storage_path") or wrapped.get("path")
    if storage_path and (str(mime_type or "").lower().startswith("image/") or candidate.get("kind") == "image"):
        return {"kind": "image", "source": "stored_local_attachment", "mime_type": str(mime_type).lower(),
                "original_filename": filename or Path(str(storage_path)).name, "storage_path": str(storage_path)}
    return None


def _gateway_attachments(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract Open WebUI/OpenAI attachment variants from the latest user turn."""
    candidates: list[Any] = []
    messages = payload.get("messages") if isinstance(payload.get("messages"), list) else []
    for message in reversed(messages):
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        content = message.get("content")
        if isinstance(content, list):
            candidates.extend(item for item in content if isinstance(item, dict) and item.get("type") in {"image_url", "input_image", "image", "file", "input_file"})
        for field in ("attachments", "files"):
            if isinstance(message.get(field), list):
                candidates.extend(message[field])
        break
    for field in ("attachments", "files"):
        if isinstance(payload.get(field), list):
            candidates.extend(payload[field])
    normalized = []
    for candidate in candidates:
        item = _normalize_gateway_attachment(candidate)
        if item:
            normalized.append(item)
    return normalized


def _session_id_from_payload(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    candidates = (
        ("payload.session_id", payload.get("session_id")),
        ("metadata.session_id", metadata.get("session_id")),
        ("payload.conversation_id", payload.get("conversation_id")),
        ("metadata.chat_id", metadata.get("chat_id")),
        ("metadata.conversation_id", metadata.get("conversation_id")),
        ("payload.chat_id", payload.get("chat_id")),
    )
    for field, value in candidates:
        text = str(value or "").strip()
        if text:
            return text, field
    return None, None


def _safe_preview(text: str) -> str:
    return str(text or "").replace("\n", " ")[:80]


def _gateway_diagnostics(payload: dict[str, Any], user_message: str, session_field: str | None, result: dict[str, Any]) -> dict[str, Any]:
    turn = result.get("turn") or {}
    llm = turn.get("llm") or {}
    return {
        "model": payload.get("model"),
        "stream": bool(payload.get("stream") is True),
        "message_count": len(payload.get("messages") or []) if isinstance(payload.get("messages"), list) else 0,
        "latest_user_message_sha256": hashlib.sha256(user_message.encode("utf-8")).hexdigest() if user_message else None,
        "latest_user_message_preview": _safe_preview(user_message) if os.environ.get("ESTATE_RESIDENT_GATEWAY_DIAGNOSTIC_PREVIEW") == "1" else None,
        "session_identifier_field": session_field,
        "provider": llm.get("provider"),
        "fallback_used": llm.get("fallback_used"),
    }




def _attach_optional_gateway_diagnostics(body: dict[str, Any], result: dict[str, Any]) -> None:
    diagnostics = result.get("gateway_diagnostics")
    if diagnostics:
        body.setdefault("estate", {})["gateway_diagnostics"] = diagnostics


def _chat_result(payload: dict[str, Any], *, root=None) -> tuple[int, str | None, dict[str, Any]]:
    model = payload.get("model")
    user_message = _latest_user_message(payload.get("messages") or [])
    if not user_message:
        return 400, None, {"error":{"message":"A non-empty user message is required.","type":"invalid_request_error","code":"missing_user_message"}}
    session_id, session_field = _session_id_from_payload(payload)
    result = process_chat(ACTIVE_RESIDENT_MODELS[model], user_message, session_id=session_id, participant_role="Steward", action="conversation", root=root, attachments=_gateway_attachments(payload))
    if os.environ.get("ESTATE_RESIDENT_GATEWAY_DIAGNOSTICS") == "1":
        result.setdefault("gateway_diagnostics", _gateway_diagnostics(payload, user_message, session_field, result))
    return 200, model, result


def _engineering_assignment_content(workflow: dict[str, Any]) -> str:
    return (
        "Engineering Department assignment initiated through the existing Helen workforce, "
        "Grace operations, and Dispatch runtimes. No provider or worker execution was performed. "
        "No second execution system was created.\n\n"
        + workflow["summary"]
    )


def _engineering_assignment_estate_envelope(model: str, session_id: str | None, workflow: dict[str, Any]) -> dict[str, Any]:
    return {
        "resident_id": ACTIVE_RESIDENT_MODELS[model],
        "session_id": session_id,
        "privileged_action_executed": False,
        "provider_execution_performed": False,
        "second_execution_system_created": False,
        "engineering_assignment": workflow,
    }


def _engineering_assignment_chat_completion(
    payload: dict[str, Any],
    *,
    user_message: str,
    session_id: str | None,
    root=None,
    stream: bool = False,
) -> dict[str, Any] | None:
    workflow = initiate_engineering_assignment_from_chat(payload, user_message=user_message, session_id=session_id, root=root)
    if workflow is None:
        return None
    model = payload.get("model")
    created = int(time.time())
    content = _engineering_assignment_content(workflow)
    if stream:
        return {
            "id": f"chatcmpl-{workflow['grace_action']['action_id']}",
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": None}],
            "estate": _engineering_assignment_estate_envelope(model, session_id, workflow),
        }
    return {
        "id": f"chatcmpl-{workflow['grace_action']['action_id']}",
        "object": "chat.completion",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "estate": _engineering_assignment_estate_envelope(model, session_id, workflow),
    }


def _non_streaming_chat_completion(payload: dict[str, Any], *, root=None) -> tuple[int, dict[str, Any]]:
    model = payload.get("model")
    user_message = _latest_user_message(payload.get("messages") or [])
    if not user_message:
        return 400, {"error":{"message":"A non-empty user message is required.","type":"invalid_request_error","code":"missing_user_message"}}
    session_id, _session_field = _session_id_from_payload(payload)
    workflow_body = _engineering_assignment_chat_completion(payload, user_message=user_message, session_id=session_id, root=root)
    if workflow_body is not None:
        return 200, workflow_body
    code, model, result = _chat_result(payload, root=root)
    if code != 200:
        return code, result
    turn = result["turn"]
    created = int(time.time())
    package = resident_package(model, turn["resident_id"], root)
    audio = {"requested": bool((payload.get("metadata") or {}).get("synthesize_audio") or payload.get("synthesize_audio")), "state": "not_requested"}
    if audio["requested"]:
        from estate.core.resident_voice_commissioning import synthesize_resident_sample
        audio = synthesize_resident_sample(turn["resident_id"], turn["resident_response"], root=root, sample_name=f"{turn['turn_id']}")
    body = {"id":f"chatcmpl-{turn['turn_id']}","object":"chat.completion","created":created,"model":model,"choices":[{"index":0,"message":{"role":"assistant","content":turn["resident_response"]},"finish_reason":"stop"}],"usage":{"prompt_tokens":0,"completion_tokens":0,"total_tokens":0},"estate":{"resident_id":turn["resident_id"],"session_id":result["session_id"],"turn_id":turn["turn_id"],"fallback_used":turn["llm"].get("fallback_used"),"provider":turn["llm"].get("provider"),"model":turn["llm"].get("model"),"privileged_action_executed":False,"identity_hash":package["identity_source_hash"],"identity_schema_version":package["identity_schema_version"],"identity_failed_closed":package["identity_failed_closed"],"identity_sources":package["identity_sources"],"resident_package":package,"voice":{"state":package["voice_state"],"engine":package["voice_engine"],"voice_id":package["voice_id"],"speed":package["voice_speed"],"approval_state":package["voice_approval_state"],"tts_available":package["tts_available"]},"visual":{"state":package["visual_state"],"avatar_uri":package["avatar_uri"],"provenance":package["visual_provenance"]},"audio":audio}}
    _attach_optional_gateway_diagnostics(body, result)
    return 200, body


def _streaming_chat_completion(payload: dict[str, Any], *, root=None) -> tuple[int, dict[str, Any]]:
    user_message = _latest_user_message(payload.get("messages") or [])
    if not user_message:
        return 400, {"error":{"message":"A non-empty user message is required.","type":"invalid_request_error","code":"missing_user_message"}}
    session_id, _session_field = _session_id_from_payload(payload)
    workflow_body = _engineering_assignment_chat_completion(
        payload, user_message=user_message, session_id=session_id, root=root, stream=True
    )
    if workflow_body is not None:
        return 200, workflow_body
    code, model, result = _chat_result(payload, root=root)
    if code != 200:
        return code, result
    turn = result["turn"]
    created = int(time.time())
    body = {"id":f"chatcmpl-{turn['turn_id']}","object":"chat.completion.chunk","created":created,"model":model,"choices":[{"index":0,"delta":{"role":"assistant","content":turn["resident_response"]},"finish_reason":None}],"estate":{"resident_id":turn["resident_id"],"session_id":result["session_id"],"turn_id":turn["turn_id"],"fallback_used":turn["llm"].get("fallback_used"),"provider":turn["llm"].get("provider"),"model":turn["llm"].get("model"),"privileged_action_executed":False,"identity_hash":(turn.get("identity_composition") or {}).get("identity_version_or_source_hash"),"identity_schema_version":(turn.get("identity_composition") or {}).get("schema_version"),"identity_failed_closed":(turn.get("identity_composition") or {}).get("failed_closed")}}
    _attach_optional_gateway_diagnostics(body, result)
    return 200, body



def _room_chat_completion(payload: dict[str, Any], *, root=None) -> tuple[int, dict[str, Any]]:
    normalized = normalize_open_webui_request(payload)
    messages = normalized.get("messages") or []
    user_message = _latest_user_message(messages)
    if not user_message:
        user_message = "Multi-resident room request received."
    targets = [rid for rid in normalized.get("resident_targets") or [] if rid in ACTIVE_RESIDENT_MODELS.values()]
    if not targets:
        targets = ["alfred", "helen", "ingrid"]
    room = create_room(display_name="Open WebUI Estate room", created_by="openwebui", session_reference={"session_id": normalized.get("session_id")})
    for rid in targets:
        room = invite_participant(room, participant_id=rid, kind="resident", display_name=rid.title())
        room = accept_participant(room, rid)
    room = submit_user_turn(room, text=user_message, submitted_by="openwebui", idempotency_key=normalized.get("session_id") or user_message, target_resident_ids=targets)
    user_turn_id = room["pending_questions"][-1]["user_turn_id"]
    resident_turns = []
    attachments = _gateway_attachments(payload)
    for plan in plan_resident_turns(room, user_turn_id, target_resident_ids=targets):
        participant_session_id = f"{normalized.get('session_id')}_{plan['resident_id']}" if normalized.get("session_id") else None
        composition = compose_resident_identity(plan["resident_id"], surface_id="conference-room-gateway", root=root, task_instructions=user_message, room_context=plan.get("context_packet"))
        result = process_chat(
            plan["resident_id"],
            user_message,
            session_id=participant_session_id,
            participant_role="Steward",
            action="conversation",
            root=root,
            attachments=attachments,
            identity_composition=composition,
        )
        turn = result["turn"]
        resident_turns.append({"resident_id": plan["resident_id"], "display_name": turn.get("resident_display_name") or plan.get("display_name"), "content": turn.get("resident_response", ""), "turn_id": turn.get("turn_id"), "identity_hash": (turn.get("identity_composition") or {}).get("identity_version_or_source_hash")})
        room = record_resident_turn(room, plan, text=turn.get("resident_response", ""), model_metadata=turn.get("llm") or {})
    body = attributed_response_envelope(model=DEFAULT_ROOM_MODEL, room_id=room["room_id"], resident_turns=resident_turns, stream=bool(payload.get("stream") is True))
    body["estate"]["room_snapshot"] = {"room_id": room["room_id"], "participant_count": len(targets), "turn_count": len(room.get("turns", [])), "privileged_action_executed": False}
    return 200, body

def _content_delta_chunks(body: dict[str, Any]) -> Iterable[dict[str, Any]]:
    choice = body["choices"][0]
    content = str((choice.get("delta") or {}).get("content") or "")
    first = dict(body)
    first["choices"] = [{"index":0,"delta":{"role":"assistant"},"finish_reason":None}]
    yield first
    if content:
        chunk = max(1, min(160, len(content)))
        for start in range(0, len(content), chunk):
            part = content[start:start + chunk]
            yield {"id":body["id"],"object":"chat.completion.chunk","created":body["created"],"model":body["model"],"choices":[{"index":0,"delta":{"content":part},"finish_reason":None}]}


def chat_completion_stream(payload: dict[str, Any], *, root=None) -> tuple[int, Iterable[dict[str, Any]]]:
    code, body = chat_completion(payload, root=root)
    if code != 200:
        return code, [body]
    if body.get("object") != "chat.completion.chunk":
        return 200, [body]
    final = {"id":body["id"],"object":"chat.completion.chunk","created":body["created"],"model":body["model"],"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}
    return 200, [*_content_delta_chunks(body), final]


def gateway_status(root=None, host="127.0.0.1", port=11435) -> dict[str, Any]:
    rootp = _root(root)
    llm = {rid: local_llm_status(resident=rid, root=rootp) for rid in ACTIVE_RESIDENT_MODELS.values()}
    return {"kind":"estate_resident_gateway_status","gateway_available":"unknown_without_running_server_probe","host":host,"port":port,"base_url":f"http://{host}:{port}","available_resident_models":list(ACTIVE_RESIDENT_MODELS),"local_model_status":llm,"cloud_dependency":False}


class Handler(BaseHTTPRequestHandler):
    root: Path | None = None
    def _send(self, code:int, payload:dict[str,Any]):
        raw=json.dumps(payload, indent=2, sort_keys=True).encode()
        self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def _send_sse(self, chunks: Iterable[dict[str, Any]]):
        self.send_response(200); self.send_header("Content-Type","text/event-stream; charset=utf-8"); self.send_header("Cache-Control","no-cache"); self.send_header("Connection","close"); self.end_headers()
        for chunk in chunks:
            self.wfile.write(f"data: {json.dumps(chunk, sort_keys=True)}\n\n".encode())
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()
        self.close_connection = True
    def do_GET(self):
        if self.path.rstrip("/") == "/v1/models": self._send(200, models_payload(self.root)); return
        if self.path.rstrip("/") == "/status": self._send(200, gateway_status(self.root)); return
        if self.path.startswith("/v1/estate/audio/"):
            from estate.core.resident_voice_commissioning import audio_metadata_for_request
            parts = self.path.split("/", 5)
            tail = parts[5] if len(parts) > 5 else ""
            bits = tail.split("/", 1)
            code, meta, path = audio_metadata_for_request(bits[0] if bits else "", bits[1] if len(bits) > 1 else "", root=self.root)
            if code != 200 or path is None: self._send(code, meta); return
            raw = path.read_bytes(); self.send_response(200); self.send_header("Content-Type","audio/wav"); self.send_header("Content-Length",str(len(raw))); self.send_header("X-Estate-Audio-Metadata", json.dumps(meta, sort_keys=True)); self.end_headers(); self.wfile.write(raw); return
        self._send(404,{"error":{"message":"not found","code":"not_found"}})
    def do_POST(self):
        if self.path.rstrip("/") != "/v1/chat/completions": self._send(404,{"error":{"message":"not found","code":"not_found"}}); return
        try:
            length=int(self.headers.get("Content-Length") or "0"); payload=json.loads(self.rfile.read(length) or b"{}")
            if payload.get("stream") is True:
                code, chunks=chat_completion_stream(payload, root=self.root)
                if code == 200: self._send_sse(chunks)
                else: self._send(code, list(chunks)[0])
            else:
                code, body=chat_completion(payload, root=self.root); self._send(code, body)
        except Exception as exc:
            self._send(500,{"error":{"message":f"gateway error: {type(exc).__name__}","code":"gateway_error"}})
    def log_message(self, fmt, *args):
        return


def serve(host="127.0.0.1", port=11435, root=None):
    Handler.root = _root(root)
    server = ThreadingHTTPServer((host, int(port)), Handler)
    status = gateway_status(root, host, port); status["gateway_available"]="running"; status["pid"] = None
    p = _root(root)/STATUS_PATH; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(status, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    server.serve_forever()
