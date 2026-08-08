"""Detached live acceptance for Grace's ordinary-language second-opinion path."""

from __future__ import annotations

import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path


DB = Path(r"A:\theestate-data\consultations\consultations.db")
GATEWAY = "http://127.0.0.1:11435/v1/chat/completions"
SESSION = "grace-external-reasoning-acceptance-20260807"


def request(message: str) -> dict:
    payload = {
        "model": "estate/grace",
        "messages": [{"role": "user", "content": message}],
        "metadata": {"session_id": SESSION},
        "stream": False,
    }
    req = urllib.request.Request(
        GATEWAY,
        json.dumps(payload).encode("utf-8"),
        {"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=420) as response:
        return json.loads(response.read())


def counts() -> dict[str, int]:
    with sqlite3.connect(DB) as db:
        return {
            table: int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in (
                "consultations",
                "consultation_transport_attempts",
                "consultation_execution_requests",
                "consultation_execution_attempts",
            )
        }


def response_content(body: dict) -> str:
    return str((((body.get("choices") or [{}])[0]).get("message") or {}).get("content") or "")


def main() -> int:
    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runtime/evidence/grace-external-reasoning")
    run_dir.mkdir(parents=True, exist_ok=True)
    before = counts()
    recommendation_prompt = (
        "Give me one bounded architectural recommendation for making a local "
        "service restart reliably after a browser-session dependency is restored. "
        "Advisory reasoning only; do not execute anything."
    )
    second_opinion_prompt = "I want a second opinion on this, not from you."
    result: dict = {"session_id": SESSION, "before_counts": before}
    try:
        first = request(recommendation_prompt)
        second_payload = {
            "model": "estate/grace",
            "messages": [
                {"role": "user", "content": recommendation_prompt},
                {"role": "assistant", "content": response_content(first)},
                {"role": "user", "content": second_opinion_prompt},
            ],
            "metadata": {"session_id": SESSION},
            "stream": False,
        }
        req = urllib.request.Request(
            GATEWAY,
            json.dumps(second_payload).encode("utf-8"),
            {"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=420) as response:
            second = json.loads(response.read())
        result["first_response"] = {
            "content": response_content(first),
            "estate": first.get("estate", {}),
        }
        result["second_response"] = {
            "content": response_content(second),
            "estate": second.get("estate", {}),
        }
        result["after_counts"] = counts()
        result["execution_mutation"] = any(
            result["after_counts"][key] != before[key]
            for key in ("consultation_execution_requests", "consultation_execution_attempts")
        )
        external = (second.get("estate") or {}).get("external_reasoning") or {}
        result["acceptance"] = {
            "external_reasoning_performed": external.get("external_reasoning_performed") is True,
            "authoritative": external.get("completion_status") == "authoritative_response",
            "consultation_root": external.get("consultation_root"),
            "consultation_turn": external.get("consultation_turn"),
            "comms8_request_id": external.get("comms8_request_id"),
            "provider": external.get("provider"),
            "response_id": external.get("response_id"),
            "request_fingerprint_present": bool(external.get("request_fingerprint")),
            "no_execution_mutation": result["execution_mutation"] is False,
        }
        result["classification"] = (
            "GRACE_SECOND_OPINION_REASONING_PATH_READY"
            if all(result["acceptance"].values())
            else "GRACE_EXTERNAL_REASONING_ACCEPTANCE_FAILED"
        )
        (run_dir / "acceptance.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0 if result["classification"] == "GRACE_SECOND_OPINION_REASONING_PATH_READY" else 1
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["after_counts"] = counts()
        (run_dir / "acceptance.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
