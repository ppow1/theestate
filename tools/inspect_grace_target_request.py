import asyncio, json
from pathlib import Path
import sys
sys.path.insert(0, r"A:\AI\OpenWebUI\.venv\Lib\site-packages")
from open_webui.utils.mcp.client import MCPClient

SECRET = Path(r"A:\theestate-data\live\comms8\secrets.env")
WORKFLOW = "estate-comms8-live-grace-chatgpt-roundtrip-test"
IDEMP = "grace-chatgpt-roundtrip-20260807-01"

def secret():
    for line in SECRET.read_text().splitlines():
        if line.startswith("ESTATE_COMMS8_LIVE_CLIENT_SECRET="):
            return line.split("=", 1)[1]
    raise RuntimeError("Live client secret missing")

def unwrap(value):
    if isinstance(value, list) and value and isinstance(value[0], dict) and "text" in value[0]:
        try: return json.loads(value[0]["text"])
        except Exception: return value
    return value

def matches(value):
    if isinstance(value, dict):
        blob = json.dumps(value, sort_keys=True)
        if WORKFLOW in blob or IDEMP in blob: return [value]
        return sum((matches(v) for v in value.values()), [])
    if isinstance(value, list): return sum((matches(v) for v in value), [])
    return []

async def inspect(url):
    c = MCPClient()
    await c.connect(url, headers={"Authorization": "Bearer " + secret()})
    all_requests = unwrap(await c.call_tool("estate_comms8_list_requests", {}))
    targeted = matches(all_requests)
    result = {"url": url, "target_matches": targeted, "match_count": len(targeted)}
    await c.disconnect()
    return result

async def main():
    results = []
    for url in ["http://127.0.0.1:11811/mcp", "https://estate-comms8-live.ionoge.com/mcp"]:
        results.append(await inspect(url))
    evidence = {"classification": "NO_REQUEST_CREATED_BY_BLANK_TURNS", "workflow_id": WORKFLOW, "idempotency_key": IDEMP, "inventories": results}
    out = Path(r"A:\theestate-data\grace-comms8-live-dispatch-repair-20260807\initial-request-inventory.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))

asyncio.run(main())
