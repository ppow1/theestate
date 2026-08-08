"""Venv-owned Live MCP call seam for the system-Python Resident Gateway."""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import sys

# The MCP client imports Open WebUI configuration modules that require the
# process-local secret even though this helper never opens an Open WebUI
# server or accesses its database.  Keep this dependency local to the
# short-lived helper; it is not an Estate or Comms8 credential.
os.environ.setdefault("WEBUI_SECRET_KEY", "estate-grace-live-mcp-client-boundary")
from open_webui.utils.mcp.client import MCPClient


URL = "https://estate-comms8-live.ionoge.com/mcp"
SECRET_PATH = Path(r"A:\theestate-data\live\comms8\secrets.env")


def _secret() -> str:
    for line in SECRET_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("ESTATE_COMMS8_LIVE_CLIENT_SECRET="):
            return line.split("=", 1)[1]
    raise RuntimeError("live_credential_unavailable")


async def _call(method: str, arguments: dict) -> object:
    client = MCPClient()
    await client.connect(URL, headers={"Authorization": "Bearer " + _secret()})
    try:
        result = await client.call_tool(method, arguments)
        if isinstance(result, list) and result and isinstance(result[0], dict) and "text" in result[0]:
            return json.loads(result[0]["text"])
        return result
    finally:
        await client.disconnect()


if __name__ == "__main__":
    request = json.loads(sys.stdin.read())
    print(json.dumps(asyncio.run(_call(request["method"], request.get("arguments") or {})), sort_keys=True))
