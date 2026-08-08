"""Sanitized direct MCP transport probe for the Estate compatibility seam."""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


SECRET_FILE = Path(r"A:\theestate-data\live\comms8\secrets.env")


def secret():
    for line in SECRET_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("ESTATE_COMMS8_LIVE_CLIENT_SECRET="):
            return line.split("=", 1)[1]
    raise RuntimeError("client secret not found")


def request(url, method="POST", body=None, session=None, timeout=15):
    headers = {
        "Authorization": "Bearer " + secret(),
        "Accept": "application/json, text/event-stream",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            first = response.read(1)
            return {
                "status": response.status,
                "content_type": response.headers.get("Content-Type"),
                "session": bool(response.headers.get("Mcp-Session-Id")),
                "protocol": response.headers.get("MCP-Protocol-Version"),
                "first_byte": first.decode("utf-8", "replace"),
                "elapsed_ms": round((time.time() - started) * 1000),
            }, response.headers.get("Mcp-Session-Id")
    except urllib.error.HTTPError as exc:
        return {
            "status": exc.code,
            "content_type": exc.headers.get("Content-Type"),
            "session": bool(exc.headers.get("Mcp-Session-Id")),
            "protocol": exc.headers.get("MCP-Protocol-Version"),
            "first_byte": exc.read(1).decode("utf-8", "replace"),
            "elapsed_ms": round((time.time() - started) * 1000),
        }, exc.headers.get("Mcp-Session-Id")


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://estate-comms8-live.ionoge.com/mcp"
    init, session = request(url, body={
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "estate-transport-probe", "version": "1"}},
    })
    notification, _ = request(url, body={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, session=session)
    tools, _ = request(url, body={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, session=session)
    stream, _ = request(url, method="GET", session=session, timeout=5)
    closed, _ = request(url, method="DELETE", session=session)
    print(json.dumps({"url": url, "initialize": init, "notification": notification,
                      "tools_list": tools, "get_stream": stream, "delete": closed}, sort_keys=True))


if __name__ == "__main__":
    main()
