import asyncio
import json
from pathlib import Path
import sys

sys.path.insert(0, r"A:\AI\OpenWebUI\.venv\Lib\site-packages")
from open_webui.utils.mcp.client import MCPClient

SECRETS = Path(r"A:\theestate-data\candidate-blue-runtime\comms8-package4-ingress\candidate-secrets.env")
OUT = Path(r"A:\theestate-data\openwebui-comms8-streamable-http-adapter-20260806\openwebui-blue-result.json")

def secret():
    for line in SECRETS.read_text().splitlines():
        if line.startswith("ESTATE_COMMS8_CANDIDATE_SECRET="):
            return line.split("=", 1)[1]
    raise RuntimeError("credential role absent")

async def verify(url):
    c = MCPClient()
    await c.connect(url, headers={"Authorization": "Bearer " + secret()})
    specs = await c.list_tool_specs()
    result = await c.call_tool("estate_comms8_list_requests", {"state": "queued"})
    await c.disconnect()
    return {"url": url, "tool_count": len(specs or []), "tool_names": [x["name"] for x in specs or []], "read_only_result_present": bool(result)}

async def main():
    rows = [await verify("http://127.0.0.1:11812/mcp")]
    OUT.write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps([{k: v for k, v in row.items() if k != "url"} for row in rows]))

asyncio.run(main())
