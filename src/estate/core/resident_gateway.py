"""Local OpenAI-compatible gateway for Estate residents."""
from __future__ import annotations
import json, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable
from estate.core.resident_interaction import process_chat, local_llm_status, _root
from estate.core.multi_resident_room import create_room, invite_participant, accept_participant, submit_user_turn, plan_resident_turns, record_resident_turn
from estate.core.open_webui_multi_resident_gateway import DEFAULT_ROOM_MODEL, attributed_response_envelope, normalize_open_webui_request
from estate.core.resident_identity_composition import compose_resident_identity

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


def _chat_result(payload: dict[str, Any], *, root=None) -> tuple[str, dict[str, Any]]:
    model = payload.get("model")
    messages = payload.get("messages") or []
    user_message = "\n".join(str(m.get("content") or "") for m in messages if m.get("role") in {"user", "system"}).strip()
    session_id = payload.get("session_id") or (payload.get("metadata") or {}).get("session_id") or payload.get("conversation_id")
    result = process_chat(ACTIVE_RESIDENT_MODELS[model], user_message, session_id=session_id, action="conversation", root=root)
    return model, result


def _non_streaming_chat_completion(payload: dict[str, Any], *, root=None) -> tuple[int, dict[str, Any]]:
    model, result = _chat_result(payload, root=root)
    turn = result["turn"]
    created = int(time.time())
    body = {"id":f"chatcmpl-{turn['turn_id']}","object":"chat.completion","created":created,"model":model,"choices":[{"index":0,"message":{"role":"assistant","content":turn["resident_response"]},"finish_reason":"stop"}],"usage":{"prompt_tokens":0,"completion_tokens":0,"total_tokens":0},"estate":{"resident_id":turn["resident_id"],"session_id":result["session_id"],"turn_id":turn["turn_id"],"fallback_used":turn["llm"].get("fallback_used"),"provider":turn["llm"].get("provider"),"model":turn["llm"].get("model"),"privileged_action_executed":False}}
    return 200, body


def _streaming_chat_completion(payload: dict[str, Any], *, root=None) -> tuple[int, dict[str, Any]]:
    model, result = _chat_result(payload, root=root)
    turn = result["turn"]
    created = int(time.time())
    body = {"id":f"chatcmpl-{turn['turn_id']}","object":"chat.completion.chunk","created":created,"model":model,"choices":[{"index":0,"delta":{"role":"assistant","content":turn["resident_response"]},"finish_reason":None}],"estate":{"resident_id":turn["resident_id"],"session_id":result["session_id"],"turn_id":turn["turn_id"],"fallback_used":turn["llm"].get("fallback_used"),"provider":turn["llm"].get("provider"),"model":turn["llm"].get("model"),"privileged_action_executed":False}}
    return 200, body



def _room_chat_completion(payload: dict[str, Any], *, root=None) -> tuple[int, dict[str, Any]]:
    normalized = normalize_open_webui_request(payload)
    messages = normalized.get("messages") or []
    user_message = "\n".join(str(m.get("content") or "") for m in messages if m.get("role") in {"user", "system"}).strip()
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
    for plan in plan_resident_turns(room, user_turn_id, target_resident_ids=targets):
        participant_session_id = f"{normalized.get('session_id')}_{plan['resident_id']}" if normalized.get("session_id") else None
        composition = compose_resident_identity(plan["resident_id"], surface_id="conference-room-gateway", root=root, task_instructions=user_message, room_context=plan.get("context_packet"))
        result = process_chat(plan["resident_id"], user_message, session_id=participant_session_id, action="conversation", root=root)
        result["turn"]["identity_composition"] = composition
        turn = result["turn"]
        resident_turns.append({"resident_id": plan["resident_id"], "display_name": turn.get("resident_display_name") or plan.get("display_name"), "content": turn.get("resident_response", ""), "turn_id": turn.get("turn_id"), "identity_hash": (turn.get("identity_composition") or {}).get("identity_version_or_source_hash")})
        room = record_resident_turn(room, plan, text=turn.get("resident_response", ""), model_metadata=turn.get("llm") or {})
    body = attributed_response_envelope(model=DEFAULT_ROOM_MODEL, room_id=room["room_id"], resident_turns=resident_turns, stream=bool(payload.get("stream") is True))
    body["estate"]["room_snapshot"] = {"room_id": room["room_id"], "participant_count": len(targets), "turn_count": len(room.get("turns", [])), "privileged_action_executed": False}
    return 200, body

def chat_completion_stream(payload: dict[str, Any], *, root=None) -> tuple[int, Iterable[dict[str, Any]]]:
    code, body = chat_completion(payload, root=root)
    if code != 200:
        return code, [body]
    if body.get("object") != "chat.completion.chunk":
        return 200, [body]
    final = {"id":body["id"],"object":"chat.completion.chunk","created":body["created"],"model":body["model"],"choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}
    return 200, [body, final]


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
        self.send_response(200); self.send_header("Content-Type","text/event-stream; charset=utf-8"); self.send_header("Cache-Control","no-cache"); self.send_header("Connection","keep-alive"); self.end_headers()
        for chunk in chunks:
            self.wfile.write(f"data: {json.dumps(chunk, sort_keys=True)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")
    def do_GET(self):
        if self.path.rstrip("/") == "/v1/models": self._send(200, models_payload(self.root)); return
        if self.path.rstrip("/") == "/status": self._send(200, gateway_status(self.root)); return
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
