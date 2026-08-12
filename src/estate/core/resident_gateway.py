"""Local OpenAI-compatible gateway for Estate residents."""
from __future__ import annotations
import base64, hashlib, json, os, re, time
from urllib.parse import unquote_to_bytes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4
from estate.core.resident_interaction import process_chat, local_llm_status, _root
from estate.core.multi_resident_room import create_room, invite_participant, accept_participant, submit_user_turn, plan_resident_turns, record_resident_turn
from estate.core.open_webui_multi_resident_gateway import DEFAULT_ROOM_MODEL, attributed_response_envelope, normalize_open_webui_request
from estate.core.resident_identity_composition import compose_resident_identity
from estate.core.openwebui_resident_package import resident_package
from estate.core.openwebui_engineering_workflow import detect_engineering_assignment_command, initiate_engineering_assignment_from_chat, detect_bounded_local_text_intent, execute_bounded_local_text_from_chat
from estate.core.grace_momentum_service import LoopbackGraceMomentumClient
from estate.core.grace_runtime_bridge import GraceRuntimeBridge
from estate.core.openwebui_grace_assignment import detect_grace_image_assignment, execute_grace_image_assignment
from estate.core.conference_room_lifecycle import (
    depart as conference_depart, invite as conference_invite,
    load_or_create_session, names_from_text, recognize_intent, save_session,
    set_backup as conference_set_backup, transfer as conference_transfer,
)

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
        payload["data"].append({"id": DEFAULT_ROOM_MODEL, "object":"model", "created":0, "owned_by":"estate", "name":"Estate conference room", "estate":{"surface":"multi_resident_room", "display_name":"Estate conference room", "office":"Estate conference room", "role":"Identity-preserving multi-resident conversation", "visual_state":"unavailable", "voice_state":"unavailable", "tts_available":False, "multi_resident_gateway_capable": True, "privileged_actions_enabled": False}})
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


def _grace_runtime_operation_response(payload: dict[str, Any], *, root=None) -> dict[str, Any] | None:
    """Ground Grace operational questions through the registered read boundary.

    This is a read-only compatibility handoff for resident backends that do not
    emit native OpenAI tool calls. Conversation-only turns remain on the normal
    resident path.
    """
    if payload.get("model") != "estate/grace":
        return None
    text = _latest_user_message(payload.get("messages") or [])
    # Preserve the existing explicit governed mutation path.  Runtime reads
    # must never intercept an assignment command merely because it mentions
    # operational terms such as "dispatch" or "objective".
    if detect_engineering_assignment_command(payload, text):
        return None
    # Explicit bounded execution is governed by the workflow below. It must
    # take precedence over this read-only compatibility layer even when the
    # request mentions ordinary operational words such as "checkpoint" or
    # "provider".
    bounded_intent = detect_bounded_local_text_intent(payload, text)
    if bounded_intent.get("state") == "execution_requested":
        return None
    explicit_runtime_operations = (
        "list_grace_runtime_operations",
        "get_runtime_readiness",
        "get_runtime_availability",
        "get_replay_cursor",
        "get_current_objective",
    )

    has_explicit_runtime_operation = any(
        operation_name in text.lower()
        for operation_name in explicit_runtime_operations
    )

    has_runtime_keyword = re.search(
        r"\b(objective|readiness|availability|replay|checkpoint|dispatch|provider|reconciliation|validation|receipt|completion|blocker|operational state|runtime operations)\b",
        text,
        re.I,
    )

    if not has_explicit_runtime_operation and not has_runtime_keyword:
        return None
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    claims = {"iss": "estate-control", "sub": str(metadata.get("user_id") or "openwebui-grace"), "office": "Grace", "authority_source": "openwebui/grace-runtime-bridge", "active": True}
    endpoint = os.environ.get("ESTATE_GRACE_MOMENTUM_URL", "http://127.0.0.1:8766")
    try:
        bridge = GraceRuntimeBridge(LoopbackGraceMomentumClient(endpoint, claims, timeout_seconds=2.0))
        lower = text.lower()

        # Exact registered operation names take precedence over natural-language
        # keyword inference. Underscores are word characters, so a \b-based
        # keyword search does not recognize names such as
        # get_current_objective or get_runtime_readiness.
        explicit_operations = (
            ("list_grace_runtime_operations", bridge.list_grace_runtime_operations),
            ("get_runtime_readiness", bridge.get_runtime_readiness),
            ("get_runtime_availability", bridge.get_runtime_availability),
            ("get_replay_cursor", bridge.get_replay_cursor),
            ("get_current_objective", bridge.get_current_objective),
        )

        explicit_handler = next(
            (
                handler
                for operation_name, handler in explicit_operations
                if operation_name in lower
            ),
            None,
        )

        if explicit_handler is not None:
            result = explicit_handler()
        elif "operation" in lower and "list" in lower:
            result = bridge.list_grace_runtime_operations()
        elif re.search(r"\breadiness\b", lower):
            result = bridge.get_runtime_readiness()
        elif re.search(r"\b(replay|cursor)\b", lower):
            result = bridge.get_replay_cursor()
        elif re.search(r"\bobjective\b", lower):
            result = bridge.get_current_objective()
        else:
            result = {
                "schema_version": "estate.grace-runtime-bridge.v1",
                "status": "AUTHORITATIVE_RESULT",
                "source_system": "grace-momentum-runtime",
                "source_operation": "get_runtime_availability",
                "payload": {
                    "availability": bridge.get_runtime_availability(),
                    "current_objective": bridge.get_current_objective(),
                },
            }
        return result
    except Exception as exc:
        return {"schema_version": "estate.grace-runtime-bridge.v1", "status": "RUNTIME_UNAVAILABLE", "error": {"code": "runtime_unavailable", "message": str(exc)}}


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


def _grace_operational_memory_completion(payload: dict[str, Any], *, user_message: str, root=None) -> dict[str, Any] | None:
    if payload.get("model") != "estate/grace":
        return None
    from estate.core.grace_operational_memory import (
        build_composite_operational_evidence, classify_operational_request,
        composite_response_complete, enforce_terminal_provenance_status,
        read_operational_snapshot, render_operational_snapshot,
        render_provenance_composite,
    )
    mode = classify_operational_request(user_message)
    if not mode["requires_operational_read"]:
        return None
    snapshot = read_operational_snapshot()
    if mode["mode"] == "grounded_composite_reasoning":
        evidence = build_composite_operational_evidence(snapshot, user_message)
        from estate.core.resident_interaction import process_chat
        result = process_chat("grace", user_message, participant_role="Steward", action="conversation",
                              root=root, reasoning_evidence=evidence, persist=False)
        content = str((result.get("turn") or {}).get("resident_response") or "")
        repair_attempted = False
        if not composite_response_complete(content, user_message):
            repair_attempted = True
            repair_prompt = (user_message + "\n\nBounded response repair: answer every original numbered obligation, "
                             "use the supplied authoritative evidence, distinguish executed/recommended/requested/pending, "
                             "and end with exactly one requested terminal classification. Do not claim an action without evidence.")
            repaired = process_chat("grace", repair_prompt, participant_role="Steward", action="conversation",
                                    root=root, reasoning_evidence=evidence, persist=False)
            content = str((repaired.get("turn") or {}).get("resident_response") or "")
        if not composite_response_complete(content, user_message):
            content = render_provenance_composite(snapshot) if "provenance" in user_message.lower() or "did you" in user_message.lower() else (content + "\n\nINCOMPLETE_RESPONSE_UNAVAILABLE")
        content = enforce_terminal_provenance_status(content, user_message, evidence)
        return {
            "id": f"chatcmpl-operational-composite-{hashlib.sha256(user_message.encode('utf-8')).hexdigest()[:16]}",
            "object": "chat.completion",
            "created": int(time.time()), "model": payload.get("model"),
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "estate": {"resident_id": "grace", "privileged_action_executed": False,
                        "claim_provenance": "authoritative_read",
                        "operational_memory": {**snapshot, "runtime_bridge_invoked": True, "native_tool_call": False},
                        "composite_reasoning": {"mode": mode["mode"], "original_request_preserved": True,
                                                "model_reasoning_attempted": True, "completeness_repair_attempted": repair_attempted,
                                                "evidence": evidence, "final_response_complete": composite_response_complete(content, user_message)}},
        }
    return {
        "id": f"chatcmpl-operational-memory-{hashlib.sha256(user_message.encode('utf-8')).hexdigest()[:16]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": payload.get("model"),
        "choices": [{"index": 0, "message": {"role": "assistant", "content": render_operational_snapshot(snapshot)}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "estate": {"resident_id": "grace", "privileged_action_executed": False,
                    "claim_provenance": "authoritative_read",
                    "operational_memory": {**snapshot, "runtime_bridge_invoked": True, "native_tool_call": False}},
    }


def _mcp_function_specs(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return only Comms8 functions explicitly supplied by Open WebUI."""
    specs: dict[str, dict[str, Any]] = {}
    for item in payload.get("tools") or []:
        if not isinstance(item, dict):
            continue
        function = item.get("function") if isinstance(item.get("function"), dict) else item
        name = function.get("name") if isinstance(function, dict) else None
        if isinstance(name, str) and "estate_comms8_" in name:
            specs[name] = function
    return specs


def _mcp_arguments(tool_name: str, text: str) -> dict[str, Any] | None:
    """Parse only explicit MCP arguments; never invent a request identity."""
    def quoted(key: str) -> str | None:
        match = re.search(rf"(?:[\"']?{key}[\"']?)\s*[:=]\s*[\"']([^\"']+)[\"']", text, re.I)
        return match.group(1) if match else None

    if tool_name.endswith("estate_comms8_list_requests"):
        match = re.search(r"claim_next\s*[:=]\s*(true|false)", text, re.I)
        return {"claim_next": match.group(1).lower() == "true"} if match else {"claim_next": False}
    if tool_name.endswith("estate_comms8_read_request"):
        request_id = quoted("request_id")
        if request_id is None:
            match = re.search(r"\bec8-[0-9a-f]{8,}\b", text, re.I)
            request_id = match.group(0) if match else None
        return {"request_id": request_id} if request_id else None
    if tool_name.endswith("estate_comms8_create_reasoning_request"):
        workflow_id = quoted("workflow_id")
        objective = quoted("objective")
        idempotency_key = quoted("idempotency_key")
        if not all((workflow_id, objective, idempotency_key)):
            return None
        input_data = {}
        input_match = re.search(r"input_data\s*[:=]\s*(\{.*?\})", text, re.I | re.S)
        if input_match:
            try:
                parsed = json.loads(input_match.group(1).replace("'", '"'))
                if isinstance(parsed, dict):
                    input_data = parsed
            except (TypeError, ValueError):
                return None
        return {"workflow_id": workflow_id, "objective": objective, "input_data": input_data, "idempotency_key": idempotency_key}
    return None


def _mcp_tool_request_response(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Emit a native tool call for an explicit Comms8 request, never its result."""
    if payload.get("model") not in {"estate/grace", "estate/grace-grounded-test"}:
        return None
    text = _latest_user_message(payload.get("messages") or [])
    specs = _mcp_function_specs(payload)
    requested_name = next((name for name in specs if name in text), None)
    if requested_name is None:
        lower = text.lower()
        if "estate" in lower and "comms8" in lower:
            if re.search(r"\b(read|retrieve|look\s+up|show)\b", lower):
                requested_name = next((name for name in specs if name.endswith("estate_comms8_read_request")), None)
            elif re.search(r"\b(list|queue|queued)\b", lower):
                requested_name = next((name for name in specs if name.endswith("estate_comms8_list_requests")), None)
    if requested_name is None:
        if "comms8" in text.lower() and re.search(r"\b(claim|claimed|acknowledge|acknowledged|respond|responded|resolve|resolved|created|submitted|completed|located)\b", text, re.I):
            return {"id": f"chatcmpl-grace-mcp-unavailable-{int(time.time()*1000)}", "object": "chat.completion", "created": int(time.time()), "model": payload.get("model"), "choices": [{"index": 0, "message": {"role": "assistant", "content": "I cannot report a Comms8 lifecycle change because no enabled Comms8 function call was emitted."}, "finish_reason": "stop"}], "estate": {"resident_id": "grace", "mcp_invocation": "not_attempted", "reason": "native_tool_call_required"}}
        return None
    arguments = _mcp_arguments(requested_name, text)
    if arguments is None:
        return {"id": f"chatcmpl-grace-mcp-missing-{int(time.time()*1000)}", "object": "chat.completion", "created": int(time.time()), "model": payload.get("model"), "choices": [{"index": 0, "message": {"role": "assistant", "content": f"I cannot invoke {requested_name}: explicit required arguments were not supplied."}, "finish_reason": "stop"}], "estate": {"resident_id": "grace", "mcp_invocation": "not_attempted", "reason": "explicit_arguments_required"}}
    return {"id": f"chatcmpl-grace-mcp-call-{int(time.time()*1000)}", "object": "chat.completion", "created": int(time.time()), "model": payload.get("model"), "choices": [{"index": 0, "message": {"role": "assistant", "content": None, "tool_calls": [{"id": f"call-{uuid4().hex[:16]}", "type": "function", "function": {"name": requested_name, "arguments": json.dumps(arguments, separators=(",", ":"))}}]}, "finish_reason": "tool_calls"}], "estate": {"resident_id": "grace", "mcp_invocation": "delegated_to_openwebui"}}


def _mcp_tool_result_response(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Return the latest MCP tool result verbatim; do not synthesize its contents."""
    messages = payload.get("messages") or []
    last_user = max((index for index, message in enumerate(messages) if isinstance(message, dict) and message.get("role") == "user"), default=-1)
    results = [message for message in messages[last_user + 1:] if isinstance(message, dict) and message.get("role") == "tool"]
    if not results:
        return None
    content = results[-1].get("content", "")
    if not isinstance(content, str):
        content = json.dumps(content, sort_keys=True)
    return {"id": f"chatcmpl-grace-mcp-result-{int(time.time()*1000)}", "object": "chat.completion", "created": int(time.time()), "model": payload.get("model"), "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}], "estate": {"resident_id": "grace", "mcp_result": "authoritative_tool_result"}}


def _engineering_assignment_content(workflow: dict[str, Any]) -> str:
    return (
        "Engineering Department assignment initiated through the existing Helen workforce, "
        "Grace operations, and Dispatch runtimes. No provider or worker execution was performed. "
        "No second execution system was created.\n\n"
        + workflow["summary"]
    )


def _bounded_conversation_context(payload: dict[str, Any], *, latest_user: str) -> str:
    parts = []
    messages = payload.get("messages") or []
    # Keep only the bounded referent immediately preceding the delegation.
    # The final assistant turn is Grace's recommendation; the preceding user
    # turn is the question it answers.  System/developer material is excluded.
    prior = [message for message in messages if isinstance(message, dict) and message.get("role") in {"user", "assistant"}]
    if prior and prior[-1].get("role") == "user" and _message_text(prior[-1].get("content")).strip() == latest_user:
        prior = prior[:-1]
    prior = prior[-4:]
    for message in prior:
        role = str(message.get("role") or "")
        content = _message_text(message.get("content"))
        if not content:
            continue
        parts.append(f"{role}: {content[:1200]}")
    return "\n".join(parts)[-3600:]


def _second_opinion_context(payload: dict[str, Any], *, latest_user: str, session_id: str | None) -> dict[str, Any] | None:
    """Resolve the bounded conversational referent before consultation allocation."""
    if "second opinion on this" not in " ".join(str(latest_user).lower().split()):
        return None
    messages = [message for message in payload.get("messages") or []
                if isinstance(message, dict) and message.get("role") in {"user", "assistant"}]
    if messages and messages[-1].get("role") == "user" and _message_text(messages[-1].get("content")).strip() == latest_user:
        messages = messages[:-1]
    if not messages or messages[-1].get("role") != "assistant":
        return None
    recommendation = _message_text(messages[-1].get("content")).strip()
    preceding_user = next((_message_text(item.get("content")).strip() for item in reversed(messages[:-1])
                           if item.get("role") == "user"), "")
    if not recommendation or not preceding_user:
        return None
    bounded = _bounded_conversation_context(payload, latest_user=latest_user)
    return {
        "purpose": "independent_second_opinion",
        "proposition": preceding_user[:1200],
        "current_recommendation": recommendation[:1200],
        "constraints": [],
        "requested_analysis": [
            "evaluate Grace's recommendation independently",
            "identify agreement, disagreement, missed risks, and new insight",
        ],
        "bounded_context": bounded,
        "source_interaction": {"session_id": session_id, "message_count": len(messages)},
    }


def _grace_consultation_chat_completion(payload: dict[str, Any], *, user_message: str,
                                        session_id: str | None, stream: bool = False) -> dict[str, Any] | None:
    """Handle external reasoning only through the authoritative consultation loop."""
    if payload.get("model") != "estate/grace":
        return None
    from estate.core.grace_consultation_loop import (
        GraceConsultationLoop,
        external_reasoning_claim_present,
        external_reasoning_provenance,
        is_explicit_delegation_request,
    )
    if not is_explicit_delegation_request(user_message):
        return None
    loop = GraceConsultationLoop()
    prior_context = _bounded_conversation_context(payload, latest_user=user_message)
    second_opinion_context = _second_opinion_context(payload, latest_user=user_message, session_id=session_id)
    delegation_text = (
        f"{user_message}\n\nBounded prior conversation context:\n{prior_context}"
        if prior_context else user_message
    )
    parent_logical_id = None
    if prior_context:
        existing = [
            item for status in ("open", "awaiting_reasoning", "claimed", "reasoning", "continuation_required")
            for item in loop.store.search(status=status)
            if item.objective == user_message.strip()
        ]
        parent_logical_id = max(existing, key=lambda item: item.updated_at, default=None)
        parent_logical_id = parent_logical_id.logical_consultation_id if parent_logical_id else None
    try:
        result = loop.delegate(
            delegation_text,
            session_id=session_id,
            parent_logical_id=parent_logical_id,
            tags=("grace", "reasoning"),
            second_opinion_context=second_opinion_context,
        )
        provenance = external_reasoning_provenance(result, user_message)
        if not provenance["external_reasoning_performed"]:
            content = (
                "External reasoning: Performed: No\n"
                "Attempted: Yes\n"
                "Failure: authoritative reasoning response unavailable."
            )
        else:
            content = str(result.get("response") or "")
    except Exception as exc:
        # Preserve the authoritative allocation identity on failed transport
        # or provider attempts.  A failure may prove that a consultation was
        # allocated, but never proves that a provider conclusion exists.
        candidates = [
            item for status in ("open", "awaiting_reasoning", "claimed", "reasoning", "continuation_required")
            for item in loop.store.search(status=status)
            if item.objective in (user_message.strip(), delegation_text)
        ]
        attempted = max(candidates, key=lambda item: item.updated_at, default=None)
        provenance = {
            "external_reasoning_performed": False,
            "attempted": True,
            "request_fingerprint": hashlib.sha256(user_message.strip().encode("utf-8")).hexdigest(),
            "consultation_root": attempted.root_logical_id if attempted else None,
            "consultation_turn": attempted.logical_consultation_id if attempted else None,
            "consultation_status": attempted.status if attempted else "unavailable",
            "comms8_request_id": attempted.ec8_request_id if attempted else None,
            "provider": None,
            "response_id": None,
            "completion_status": "failed",
            "failure": str(exc).split(":", 1)[0][:120],
            "contribution": None,
        }
        content = (
            "External reasoning: Performed: No\n"
            "Attempted: Yes\n"
            f"Failure: {provenance['failure']}. No provider conclusion is available."
        )
    if not provenance["external_reasoning_performed"] and external_reasoning_claim_present(content):
        content = (
            "External reasoning: Performed: No\n"
            "No authoritative consultation/provider evidence is available; no external conclusion is asserted."
        )
    body = {
        "id": f"chatcmpl-external-reasoning-{provenance.get('consultation_turn') or 'unavailable'}",
        "object": "chat.completion.chunk" if stream else "chat.completion",
        "created": int(time.time()),
        "model": payload.get("model"),
        "choices": [{
            "index": 0,
            ("delta" if stream else "message"): {"role": "assistant", "content": content},
            "finish_reason": None if stream else "stop",
        }],
        "estate": {
            "external_reasoning": provenance,
            "consultation": {
                "logical_consultation_id": provenance.get("consultation_turn"),
                "root_logical_id": provenance.get("consultation_root"),
                "ec8_request_id": provenance.get("comms8_request_id"),
                "response_id": provenance.get("response_id"),
                "worker": provenance.get("provider"),
                "status": provenance.get("consultation_status"),
                "authoritative": provenance.get("external_reasoning_performed", False),
            },
            "privileged_action_executed": False,
        },
    }
    return body
def _bounded_local_text_content(workflow: dict[str, Any]) -> str:
    if workflow.get("state") == "execution_completed":
        result_metadata = workflow.get("execution", {}).get("result", {}).get("metadata", {})
        placement = workflow.get("placement", {}).get("selected")
        actual_resource = result_metadata.get("actual_runtime_resource_id")
        actual_uuid = result_metadata.get("actual_runtime_gpu_uuid") or result_metadata.get("runtime_bound_gpu_uuid")
        return json.dumps({"status": "completed", "provider": "qwen.local.text", "runtime_lane": workflow.get("lane", {}).get("runtime_lane_id"), "physical_resource": actual_resource, "gpu_uuid": actual_uuid, "intended_physical_resource": placement, "intended_gpu_uuid": result_metadata.get("configured_required_gpu_uuid"), "actual_runtime_resource": actual_resource, "actual_runtime_gpu_uuid": actual_uuid, "placement_match": result_metadata.get("placement_match"), "summary": workflow.get("execution", {}).get("result", {}).get("summary", "bounded local text task completed")}, sort_keys=True)
    return json.dumps({"status": workflow.get("state", "execution_blocked"), "reason": workflow.get("reason") or workflow.get("execution", {}).get("handoff", {}).get("errors") or "governed execution did not complete"}, sort_keys=True)


def _engineering_assignment_estate_envelope(model: str, session_id: str | None, workflow: dict[str, Any]) -> dict[str, Any]:
    return {
        "resident_id": ACTIVE_RESIDENT_MODELS[model],
        "session_id": session_id,
        "privileged_action_executed": False,
        "provider_execution_performed": False,
        "second_execution_system_created": False,
        "engineering_assignment": workflow,
    }


def _guard_unproven_external_claim(content: str) -> str:
    """Prevent ordinary resident prose from fabricating provider review."""
    from estate.core.grace_consultation_loop import external_reasoning_claim_present
    if external_reasoning_claim_present(content):
        return (
            "External reasoning: Performed: No\n"
            "No authoritative consultation/provider evidence is available; "
            "no external conclusion is asserted."
        )
    return content


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


def _bounded_local_text_chat_completion(payload: dict[str, Any], *, user_message: str, session_id: str | None, root=None, stream: bool = False) -> dict[str, Any] | None:
    intent = detect_bounded_local_text_intent(payload, user_message)
    if intent["state"] == "conversation_only":
        return None
    workflow = execute_bounded_local_text_from_chat(payload, user_message=user_message, session_id=session_id, root=root)
    if workflow is None:
        return None
    content = _bounded_local_text_content(workflow)
    envelope = {"resident_id": "grace", "session_id": session_id, "bounded_local_text": workflow, "provider_execution_performed": bool(workflow.get("provider_execution_performed")), "privileged_action_executed": False, "second_execution_system_created": False}
    body = {"id": f"chatcmpl-grace-bounded-{workflow.get('objective', {}).get('objective_id', int(time.time()))}", "object": "chat.completion", "created": int(time.time()), "model": payload.get("model"), "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}, "estate": envelope}
    if stream:
        body["object"] = "chat.completion.chunk"
        body["choices"][0] = {"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": "stop"}
    return body


def _grace_image_assignment_chat_completion(payload: dict[str, Any], *, user_message: str, session_id: str | None, stream: bool = False) -> dict[str, Any] | None:
    if not detect_grace_image_assignment(payload.get("model"), user_message):
        return None
    result = execute_grace_image_assignment(payload, user_message=user_message, session_id=session_id)
    content = json.dumps(result, sort_keys=True)
    estate = {"resident_id": "grace", "assignment_execution": result, "authoritative_runtime": True, "runtime_status": result.get("disposition"), "privileged_action_executed": False}
    if stream:
        return {"id": f"chatcmpl-{result.get('assignment_id', uuid4().hex)}", "object": "chat.completion.chunk", "created": int(time.time()), "model": payload.get("model"), "choices": [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": None}], "estate": estate}
    return {"id": f"chatcmpl-{result.get('assignment_id', uuid4().hex)}", "object": "chat.completion", "created": int(time.time()), "model": payload.get("model"), "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}, "estate": estate}


def _non_streaming_chat_completion(payload: dict[str, Any], *, root=None) -> tuple[int, dict[str, Any]]:
    model = payload.get("model")
    user_message = _latest_user_message(payload.get("messages") or [])
    if not user_message:
        return 400, {"error":{"message":"A non-empty user message is required.","type":"invalid_request_error","code":"missing_user_message"}}
    runtime_result = _grace_runtime_operation_response(payload, root=root)
    if runtime_result is not None:
        return 200, {"id": f"chatcmpl-grace-runtime-{int(time.time()*1000)}", "object": "chat.completion", "created": int(time.time()), "model": model,
                      "choices": [{"index": 0, "message": {"role": "assistant", "content": json.dumps(runtime_result, sort_keys=True)}, "finish_reason": "stop"}],
                      "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                      "estate": {"resident_id": "grace", "authoritative_runtime": True, "runtime_source": "grace-momentum-runtime", "runtime_status": runtime_result.get("status")}}
    session_id, _session_field = _session_id_from_payload(payload)
    image_assignment = _grace_image_assignment_chat_completion(payload, user_message=user_message, session_id=session_id)
    if image_assignment is not None:
        return 200, image_assignment
    operational_body = _grace_operational_memory_completion(payload, user_message=user_message, root=root)
    if operational_body is not None:
        return 200, operational_body
    consultation_body = _grace_consultation_chat_completion(payload, user_message=user_message, session_id=session_id)
    if consultation_body is not None:
        return 200, consultation_body
    bounded_text = _bounded_local_text_chat_completion(payload, user_message=user_message, session_id=session_id, root=root)
    if bounded_text is not None:
        return 200, bounded_text
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
        audio = synthesize_resident_sample(turn["resident_id"], turn["resident_response"], root=root, sample_name=f"{turn['turn_id']}", turn_id=turn["turn_id"])
    content = _guard_unproven_external_claim(turn["resident_response"])
    body = {"id":f"chatcmpl-{turn['turn_id']}","object":"chat.completion","created":created,"model":model,"choices":[{"index":0,"message":{"role":"assistant","content":content},"finish_reason":"stop"}],"usage":{"prompt_tokens":0,"completion_tokens":0,"total_tokens":0},"estate":{"resident_id":turn["resident_id"],"session_id":result["session_id"],"turn_id":turn["turn_id"],"fallback_used":turn["llm"].get("fallback_used"),"provider":turn["llm"].get("provider"),"model":turn["llm"].get("model"),"privileged_action_executed":False,"identity_hash":package["identity_source_hash"],"identity_schema_version":package["identity_schema_version"],"identity_failed_closed":package["identity_failed_closed"],"identity_sources":package["identity_sources"],"resident_package":package,"voice":{"state":package["voice_state"],"engine":package["voice_engine"],"voice_id":package["voice_id"],"speed":package["voice_speed"],"approval_state":package["voice_approval_state"],"tts_available":package["tts_available"]},"visual":{"state":package["visual_state"],"avatar_uri":package["avatar_uri"],"provenance":package["visual_provenance"]},"audio":audio}}
    _attach_optional_gateway_diagnostics(body, result)
    return 200, body


def _streaming_chat_completion(payload: dict[str, Any], *, root=None) -> tuple[int, dict[str, Any]]:
    user_message = _latest_user_message(payload.get("messages") or [])
    if not user_message:
        return 400, {"error":{"message":"A non-empty user message is required.","type":"invalid_request_error","code":"missing_user_message"}}
    runtime_result = _grace_runtime_operation_response(payload, root=root)
    if runtime_result is not None:
        return 200, {"id": f"chatcmpl-grace-runtime-{int(time.time()*1000)}", "object": "chat.completion.chunk", "created": int(time.time()), "model": payload.get("model"),
                      "choices": [{"index": 0, "delta": {"role": "assistant", "content": json.dumps(runtime_result, sort_keys=True)}, "finish_reason": "stop"}],
                      "estate": {"resident_id": "grace", "authoritative_runtime": True, "runtime_source": "grace-momentum-runtime", "runtime_status": runtime_result.get("status")}}
    session_id, _session_field = _session_id_from_payload(payload)
    image_assignment = _grace_image_assignment_chat_completion(payload, user_message=user_message, session_id=session_id, stream=True)
    if image_assignment is not None:
        return 200, image_assignment
    operational_body = _grace_operational_memory_completion(payload, user_message=user_message, root=root)
    if operational_body is not None:
        operational_body["object"] = "chat.completion.chunk"
        operational_body["choices"][0]["delta"] = operational_body["choices"][0].pop("message")
        return 200, operational_body
    consultation_body = _grace_consultation_chat_completion(payload, user_message=user_message, session_id=session_id, stream=True)
    if consultation_body is not None:
        return 200, consultation_body
    bounded_text = _bounded_local_text_chat_completion(payload, user_message=user_message, session_id=session_id, root=root, stream=True)
    if bounded_text is not None:
        return 200, bounded_text
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
    content = _guard_unproven_external_claim(turn["resident_response"])
    body = {"id":f"chatcmpl-{turn['turn_id']}","object":"chat.completion.chunk","created":created,"model":model,"choices":[{"index":0,"delta":{"role":"assistant","content":content},"finish_reason":None}],"estate":{"resident_id":turn["resident_id"],"session_id":result["session_id"],"turn_id":turn["turn_id"],"fallback_used":turn["llm"].get("fallback_used"),"provider":turn["llm"].get("provider"),"model":turn["llm"].get("model"),"privileged_action_executed":False,"identity_hash":(turn.get("identity_composition") or {}).get("identity_version_or_source_hash"),"identity_schema_version":(turn.get("identity_composition") or {}).get("schema_version"),"identity_failed_closed":(turn.get("identity_composition") or {}).get("failed_closed")}}
    _attach_optional_gateway_diagnostics(body, result)
    return 200, body



def _room_chat_completion(payload: dict[str, Any], *, root=None) -> tuple[int, dict[str, Any]]:
    normalized = normalize_open_webui_request(payload)
    messages = normalized.get("messages") or []
    user_message = _latest_user_message(messages)
    if not user_message:
        user_message = "Multi-resident room request received."
    session_id = normalized.get("session_id")
    if not session_id:
        # Compatibility for non-Open-WebUI callers; Open WebUI supplies a stable id.
        session_id = f"ephemeral-{hashlib.sha256(user_message.encode()).hexdigest()[:16]}"
    state, created = load_or_create_session(session_id, root)
    intent = recognize_intent(user_message, root)
    requested = [rid for rid in normalized.get("resident_targets") or [] if rid in ACTIVE_RESIDENT_MODELS.values()]
    targets: list[str] = []
    acknowledgements: set[str] = set()
    scripted: list[dict[str, str]] = []
    try:
        if created and requested:
            conference_invite(state,requested,root)
            targets.extend(rid for rid in requested if rid in state["active_participants"])
        elif created:
            moderator = state["current_moderator"]
            scripted.append({"resident_id":moderator,"display_name":moderator.title(),"content":"The conference room is open, Steward. I am serving as moderator. No other residents are currently present. Who would you like me to invite?"})
        elif intent["intent"] == "invite":
            admitted = conference_invite(state, intent.get("residents", []), root)
            if not admitted:
                raise ValueError("invitation named no eligible resident who was absent")
            targets.extend(admitted)
            acknowledgements.update(admitted)
            # Compound instructions are applied only after each admission is acknowledged.
            lower = user_message.lower(); names = names_from_text(user_message, root)
            if ("transfer" in lower or "take over" in lower) and admitted:
                target = next((n.lower() for n in names if n.lower() in admitted), admitted[-1])
                conference_transfer(state, target, root)
                scripted.append({"resident_id":target,"display_name":target.title(),"content":"I acknowledge the transfer and am now serving as moderator."})
                if "then leave" in lower or "and then leave" in lower:
                    former = state["default_moderator_at_creation"]
                    if former in state["active_participants"] and former != target:
                        conference_depart(state, former, root=root)
        elif intent["intent"] == "roster":
            moderator=state.get("current_moderator") or "estate"
            present=", ".join(r.title() for r in state["active_participants"])
            scripted.append({"resident_id":moderator,"display_name":moderator.title(),"content":f"Currently present: {present}."})
        elif intent["intent"] == "moderator_status":
            moderator=state.get("current_moderator")
            content=f"{moderator.title()} is the current moderator." if moderator else "There is no current moderator; moderator-dependent operations are paused pending Steward direction."
            speaker=moderator or state["active_participants"][1]
            scripted.append({"resident_id":speaker,"display_name":speaker.title(),"content":content})
        elif intent["intent"] == "set_backup":
            rid=conference_set_backup(state,intent["resident"],root)
            scripted.append({"resident_id":state["current_moderator"],"display_name":state["current_moderator"].title(),"content":f"{rid.title()} is designated backup moderator and remains a regular participant until activated."})
        elif intent["intent"] == "assign_roles":
            moderator=conference_transfer(state,intent["moderator"],root)
            backup=conference_set_backup(state,intent["backup"],root)
            scripted.append({"resident_id":moderator,"display_name":moderator.title(),"content":f"I am now serving as moderator. {backup.title()} is designated backup and remains a regular participant until activated."})
        elif intent["intent"] == "clear_backup":
            conference_set_backup(state,None,root)
            scripted.append({"resident_id":state["current_moderator"],"display_name":state["current_moderator"].title(),"content":"The backup moderator designation is cleared."})
        elif intent["intent"] == "transfer":
            rid=conference_transfer(state,intent["resident"],root)
            scripted.append({"resident_id":rid,"display_name":rid.title(),"content":"I acknowledge the transfer and am now serving as moderator."})
        elif intent["intent"] in {"depart","remove"}:
            result=conference_depart(state,intent["resident"],removed=intent["intent"]=="remove",root=root)
            speaker=result.get("successor") or state.get("current_moderator")
            content=f"{result['resident_id'].title()} has left the conference."
            if result.get("successor"): content += f" {result['successor'].title()} has succeeded as moderator."
            elif state.get("current_moderator") is None: content += " Moderator-dependent operations are paused pending Steward direction."
            if speaker: scripted.append({"resident_id":speaker,"display_name":speaker.title(),"content":content})
        elif intent["intent"] == "close":
            state["status"]="closed"
            scripted.append({"resident_id":state.get("current_moderator") or state["active_participants"][1],"display_name":(state.get("current_moderator") or state["active_participants"][1]).title(),"content":"The conference is closed by Steward direction."})
        else:
            addressed=intent.get("residents") or requested
            targets=[rid for rid in addressed if rid in state["active_participants"]]
            if not targets and state.get("current_moderator") in state["active_participants"]: targets=[state["current_moderator"]]
        save_session(state, root)
    except ValueError as exc:
        state["audit_events"].append({"event":"operation_rejected","reason":str(exc),"initiating_authority":"steward"})
        save_session(state,root)
        return 409,{"error":{"message":str(exc),"type":"invalid_request_error","code":"conference_operation_rejected"},"estate":{"conference_state":state}}
    room = create_room(display_name="Open WebUI Estate room", created_by="steward", session_reference={"session_id": session_id})
    active_residents=[rid for rid in state["active_participants"] if rid != "steward"]
    for rid in active_residents:
        room = invite_participant(room, participant_id=rid, kind="resident", display_name=rid.title())
        room = accept_participant(room, rid)
    if scripted:
        body=attributed_response_envelope(model=DEFAULT_ROOM_MODEL,room_id=state["room_id"],resident_turns=scripted,stream=bool(payload.get("stream") is True))
        body["estate"]["conference_state"] = state
        return 200,body
    room = submit_user_turn(room, text=user_message, submitted_by="openwebui", idempotency_key=normalized.get("session_id") or user_message, target_resident_ids=targets)
    user_turn_id = room["pending_questions"][-1]["user_turn_id"]
    resident_turns = []
    attachments = _gateway_attachments(payload)
    for plan in plan_resident_turns(room, user_turn_id, target_resident_ids=targets):
        participant_session_id = f"{normalized.get('session_id')}_{plan['resident_id']}" if normalized.get("session_id") else None
        dispatched_message = ("You have been admitted to this conference. Acknowledge your own admission briefly as yourself; do not speak for or acknowledge any other resident."
                              if plan["resident_id"] in acknowledgements else user_message)
        composition = compose_resident_identity(plan["resident_id"], surface_id="conference-room-gateway", root=root, task_instructions=dispatched_message, room_context=plan.get("context_packet"))
        result = process_chat(
            plan["resident_id"],
            dispatched_message,
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
    body["estate"]["room_snapshot"] = {"room_id": state["room_id"], "participant_count": len(active_residents), "turn_count": len(room.get("turns", [])), "privileged_action_executed": False}
    body["estate"]["conference_state"] = state
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
        if self.path.startswith("/v1/estate/residents/") and self.path.rstrip("/").endswith("/ready"):
            rid=self.path.split("/")[4].lower()
            model=f"estate/{rid}"
            if model not in ACTIVE_RESIDENT_MODELS: self._send(404,{"error":{"message":"resident not found","code":"resident_not_found"}}); return
            package=resident_package(model, rid, self.root)
            self._send(200,{"resident_id":rid,"ready_state":package["ready_state"],"resident_package":package}); return
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
