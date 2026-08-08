import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, r"A:\AI\OpenWebUI\.venv\Lib\site-packages")
from open_webui.utils.mcp.client import MCPClient

SECRETS = Path(r"A:\theestate-data\live\comms8\secrets.env")
OUT = Path(r"A:\theestate-data\live-estate-blue-promotion-20260806\live-openwebui-adapter-health.json")

def secret():
    return next(x.split("=", 1)[1] for x in SECRETS.read_text().splitlines() if x.startswith("ESTATE_COMMS8_LIVE_CLIENT_SECRET="))

async def main():
    rows = []
    for i in range(3):
        c = MCPClient()
        await c.connect("https://estate-comms8-live.ionoge.com/mcp", headers={"Authorization": "Bearer " + secret()})
        specs = await c.list_tool_specs()
        result = await c.call_tool("estate_comms8_list_requests", {"state": "queued"})
        rows.append({"iteration": i + 1, "tool_count": len(specs or []), "tool_names": [x["name"] for x in specs or []], "read_only_result_present": bool(result)})
        await c.disconnect()
    OUT.write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps({"iterations": len(rows), "tool_counts": [x["tool_count"] for x in rows], "read_only": all(x["read_only_result_present"] for x in rows)}))

asyncio.run(main())
