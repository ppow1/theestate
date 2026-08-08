"""Transport-only Streamable HTTP compatibility boundary for Estate Comms8.

The adapter owns only short-lived MCP transport sessions. It forwards the
unchanged JSON-RPC payload to the accepted Comms8 HTTP service and never
interprets tool names, arguments, or results.
"""
from __future__ import annotations

import hmac
import json
import os
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


UPSTREAM = os.environ.get("ESTATE_COMMS8_ADAPTER_UPSTREAM_URL", "http://127.0.0.1:11808/mcp")
LISTEN_HOST = os.environ.get("ESTATE_COMMS8_ADAPTER_LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("ESTATE_COMMS8_ADAPTER_LISTEN_PORT", "11812"))
CLIENT_SECRET = os.environ.get("ESTATE_COMMS8_ADAPTER_CLIENT_SECRET", "")
UPSTREAM_AUTH = os.environ.get("ESTATE_COMMS8_ADAPTER_UPSTREAM_AUTH", "")
SESSION_TTL = int(os.environ.get("ESTATE_COMMS8_ADAPTER_SESSION_TTL", "1800"))
MAX_BODY = int(os.environ.get("ESTATE_COMMS8_ADAPTER_MAX_BODY", "262144"))
TRACE_PATH = os.environ.get("ESTATE_COMMS8_ADAPTER_TRACE_PATH", "")
PROTOCOL = "2024-11-05"
SESSIONS: dict[str, float] = {}


def _trace(payload: dict) -> None:
    if not TRACE_PATH:
        return
    try:
        with open(TRACE_PATH, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, separators=(",", ":")) + "\n")
    except OSError:
        pass


def _purge() -> None:
    cutoff = time.monotonic() - SESSION_TTL
    for key, value in list(SESSIONS.items()):
        if value < cutoff:
            SESSIONS.pop(key, None)


def _authorized(value: str) -> bool:
    if not CLIENT_SECRET:
        return False
    expected = f"Bearer {CLIENT_SECRET}"
    return bool(value) and hmac.compare_digest(value, expected)


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class AdapterHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: object) -> None:
        # Do not include headers, bodies, URLs containing credentials, or args.
        print(f"comms8-adapter {self.command} {self.path.split('?', 1)[0]} {args[1]}", flush=True)

    def _send(self, status: int, body: bytes = b"", content_type: str = "application/json", session: str | None = None) -> None:
        _trace({"event": "mcp_response", "status": status, "content_type": content_type, "bytes": len(body), "session_present": bool(session)})
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        if session:
            self.send_header("Mcp-Session-Id", session)
            self.send_header("Mcp-Protocol-Version", PROTOCOL)
        self.end_headers()
        if body:
            self.wfile.write(body)
            self.wfile.flush()

    def _error(self, status: int, code: str) -> None:
        self._send(status, _json_bytes({"error": code}))

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send(200, _json_bytes({"status": "ok", "service": "estate-comms8-streamable-http-adapter"}))
            return
        self._error(404, "not_found")

    def do_DELETE(self) -> None:
        _purge()
        session = self.headers.get("Mcp-Session-Id", "")
        if not _authorized(self.headers.get("Authorization", "")):
            self._error(401, "unauthorized")
            return
        if session:
            SESSIONS.pop(session, None)
        self._send(200)

    def do_POST(self) -> None:
        _purge()
        if not _authorized(self.headers.get("Authorization", "")):
            self._error(401, "unauthorized")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._error(400, "invalid_content_length")
            return
        if length < 0 or length > MAX_BODY:
            self._error(413, "body_too_large")
            return
        try:
            raw = self.rfile.read(length)
            message = json.loads(raw.decode("utf-8"))
        except Exception:
            self._error(400, "malformed_json")
            return
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not message.get("method"):
            self._error(400, "invalid_jsonrpc")
            return

        method = message["method"]
        _trace({"event": "mcp_request", "method": method, "tool_name": (message.get("params") or {}).get("name") if isinstance(message.get("params"), dict) else None, "has_id": "id" in message})
        session = self.headers.get("Mcp-Session-Id", "")
        if method == "initialize":
            session = f"estate-{secrets.token_urlsafe(18)}"
            SESSIONS[session] = time.monotonic()
        elif method.startswith("notifications/"):
            if not session or session not in SESSIONS:
                self._error(400, "invalid_session")
                return
            SESSIONS[session] = time.monotonic()
            self._send(202, session=session)
            return
        elif not session or session not in SESSIONS:
            self._error(400, "invalid_session")
            return
        else:
            SESSIONS[session] = time.monotonic()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Connection": "close",
        }
        if UPSTREAM_AUTH:
            headers["Authorization"] = UPSTREAM_AUTH
        request = Request(UPSTREAM, data=raw, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=20) as response:
                body = response.read(MAX_BODY + 1)
                if len(body) > MAX_BODY:
                    self._error(502, "upstream_body_too_large")
                    return
                response_type = response.headers.get("Content-Type", "application/json")
                self._send(response.status, body, response_type, session)
        except HTTPError as error:
            body = error.read(MAX_BODY + 1)
            self._send(error.code, body[:MAX_BODY], error.headers.get("Content-Type", "application/json"), session)
        except (URLError, TimeoutError, OSError):
            self._error(502, "upstream_unavailable")


def main() -> None:
    if not CLIENT_SECRET or not UPSTREAM_AUTH:
        raise SystemExit("adapter credentials must be supplied through environment variables")
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), AdapterHandler)
    print(f"Estate Comms8 Streamable HTTP adapter listening on {LISTEN_HOST}:{LISTEN_PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
