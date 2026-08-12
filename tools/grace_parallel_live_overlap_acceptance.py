"""Detached ordinary-language live overlap probe for Grace roots."""
from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.request
import uuid

GATEWAY = "http://127.0.0.1:11435/v1/chat/completions"


def request(prompt: str, label: str) -> dict:
    session = f"grace-live-overlap-{label}-{uuid.uuid4().hex[:10]}"
    payload = {"model": "estate/grace", "messages": [{"role": "user", "content": prompt}], "metadata": {"session_id": session}, "stream": False}
    started = datetime.now(timezone.utc).isoformat()
    req = urllib.request.Request(GATEWAY, json.dumps(payload).encode(), {"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=720) as response:
        body = json.loads(response.read())
    finished = datetime.now(timezone.utc).isoformat()
    estate = body.get("estate") or {}
    return {"label": label, "session_id": session, "started_at": started, "finished_at": finished,
            "prompt": prompt, "consultation": estate.get("consultation"),
            "external_reasoning": estate.get("external_reasoning"),
            "response": (((body.get("choices") or [{}])[0].get("message") or {}).get("content") or "")[:4000]}


def main() -> int:
    prompts = {
        "B": "Grace, I want a second opinion on this bounded read-only question about the amber acceptance fixture: should an explicitly optional local listener be reported as degraded rather than failed? Give a concise evidence-oriented recommendation and do not execute or modify anything.",
        "C": "Grace, I want a second opinion on this bounded proposed violet acceptance-fixture correction. Stop before any action that would require my approval, identify exactly what decision or evidence you need from me, and do not execute or modify anything.",
    }
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(request, prompt, label) for label, prompt in prompts.items()]
        results = [future.result() for future in futures]
    run_dir = Path(__import__("sys").argv[1])
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "overlap-results.json").write_text(json.dumps({"results": results}, indent=2) + "\n", encoding="utf-8")
    (run_dir / "exit-code").write_text("0\n", encoding="utf-8")
    (run_dir / "completion.marker").write_text("GRACE_LIVE_OVERLAP_ACCEPTANCE_COMPLETE\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
