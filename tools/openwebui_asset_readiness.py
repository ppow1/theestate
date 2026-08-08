"""Read-only canonical Open WebUI frontend asset readiness probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CRITICAL_ASSETS = (
    "/static/loader.js",
    "/static/custom.css",
    "/static/splash.png",
)


def probe(url: str, timeout: float = 5.0) -> dict:
    root = url.rstrip("/")
    result = {"url": root, "root": None, "assets": [], "status": "UNKNOWN"}
    try:
        with urlopen(Request(root + "/", method="GET"), timeout=timeout) as response:
            body = response.read(4096)
            result["root"] = {"status": response.status, "content_type": response.headers.get("Content-Type"), "bytes_sampled": len(body)}
    except (HTTPError, URLError, TimeoutError) as exc:
        result["root"] = {"status": getattr(exc, "code", None), "error": str(exc)}
        result["status"] = "OPENWEBUI_UNAVAILABLE"
        return result
    for asset in CRITICAL_ASSETS:
        entry = {"path": asset}
        try:
            with urlopen(Request(root + asset, method="GET"), timeout=timeout) as response:
                entry.update(status=response.status, content_type=response.headers.get("Content-Type"), content_length=response.headers.get("Content-Length"))
        except (HTTPError, URLError, TimeoutError) as exc:
            entry.update(status=getattr(exc, "code", None), error=str(exc))
        result["assets"].append(entry)
    result["status"] = "OPENWEBUI_READY" if result["root"].get("status") == 200 and all(item.get("status") == 200 for item in result["assets"]) else "OPENWEBUI_NOT_READY"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8080")
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args()
    result = probe(args.url, args.timeout)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "OPENWEBUI_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
