"""Local OpenAI-compatible gateway for Estate residents."""
from __future__ import annotations
import json, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from estate.core.resident_interaction import process_chat, local_llm_status, _root

ACTIVE_RESIDENT_MODELS = {"estate/alfred": "alfred", "estate/helen": "helen"}
STATUS_PATH = Path("runtime/resident_gateway/status.json")


def models_payload(root=None) -> dict[str, Any]:
    return {"object":"list","data":[{"id": mid,"object":"model","created":0,"owned_by":"estate","estate":{"resident_id": rid,"privileged_actions_enabled":False}} for mid, rid in ACTIVE_RESIDENT_MODELS.items()]}


def chat_completion(payload: dict[str, Any], *, root=None) -> tuple[int, dict[str, Any]]:
    model = payload.get("model")
    if model not in ACTIVE_RESIDENT_MODELS:
        return 404, {"error":{"message":f"Unsupported Estate resident model: {model}","type":"invalid_request_error","code":"unsupported_model"}}
    if payload.get("stream") is True:
        return 400, {"error":{"message":"Streaming chat completions are not supported by the local Estate resident gateway.","type":"invalid_request_error","code":"streaming_unsupported"}}
    messages = payload.get("messages") or []
    user_message = "\n".join(str(m.get("content") or "") for m in messages if m.get("role") in {"user", "system"}).strip()
    session_id = payload.get("session_id") or (payload.get("metadata") or {}).get("session_id") or payload.get("conversation_id")
    result = process_chat(ACTIVE_RESIDENT_MODELS[model], user_message, session_id=session_id, action="conversation", root=root)
    turn = result["turn"]
    created = int(time.time())
    body = {"id":f"chatcmpl-{turn['turn_id']}","object":"chat.completion","created":created,"model":model,"choices":[{"index":0,"message":{"role":"assistant","content":turn["resident_response"]},"finish_reason":"stop"}],"usage":{"prompt_tokens":0,"completion_tokens":0,"total_tokens":0},"estate":{"resident_id":turn["resident_id"],"session_id":result["session_id"],"turn_id":turn["turn_id"],"fallback_used":turn["llm"].get("fallback_used"),"provider":turn["llm"].get("provider"),"model":turn["llm"].get("model"),"privileged_action_executed":False}}
    return 200, body


def gateway_status(root=None, host="127.0.0.1", port=11435) -> dict[str, Any]:
    rootp = _root(root)
    llm = {rid: local_llm_status(resident=rid, root=rootp) for rid in ACTIVE_RESIDENT_MODELS.values()}
    return {"kind":"estate_resident_gateway_status","gateway_available":"unknown_without_running_server_probe","host":host,"port":port,"base_url":f"http://{host}:{port}","available_resident_models":list(ACTIVE_RESIDENT_MODELS),"local_model_status":llm,"cloud_dependency":False}


class Handler(BaseHTTPRequestHandler):
    root: Path | None = None
    def _send(self, code:int, payload:dict[str,Any]):
        raw=json.dumps(payload, indent=2, sort_keys=True).encode()
        self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        if self.path.rstrip("/") == "/v1/models": self._send(200, models_payload(self.root)); return
        if self.path.rstrip("/") == "/status": self._send(200, gateway_status(self.root)); return
        self._send(404,{"error":{"message":"not found","code":"not_found"}})
    def do_POST(self):
        if self.path.rstrip("/") != "/v1/chat/completions": self._send(404,{"error":{"message":"not found","code":"not_found"}}); return
        try:
            length=int(self.headers.get("Content-Length") or "0"); payload=json.loads(self.rfile.read(length) or b"{}")
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
