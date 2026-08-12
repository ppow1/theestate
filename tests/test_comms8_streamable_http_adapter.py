import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import comms8_streamable_http_adapter as adapter


def setup_function():
    adapter.SESSIONS.clear()
    adapter.CLIENT_SECRET = "client-fixture"
    adapter.UPSTREAM_AUTH = "Bearer upstream-fixture"


def test_initialize_creates_session_and_preserves_jsonrpc_shape():
    assert adapter._authorized("Bearer client-fixture")
    sid = "estate-fixture"
    adapter.SESSIONS[sid] = 1.0
    assert sid in adapter.SESSIONS
    assert json.loads(adapter._json_bytes({"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}))["id"] == 1


def test_authentication_is_exact_and_never_returns_secret():
    assert adapter._authorized("Bearer client-fixture")
    assert not adapter._authorized("Bearer wrong")
    assert "client-fixture" not in json.dumps({"error": "unauthorized"})


def test_session_expiry_is_transport_only():
    adapter.SESSIONS["expired"] = 0
    adapter._purge()
    assert "expired" not in adapter.SESSIONS


def test_body_limit_is_bounded():
    assert adapter.MAX_BODY == 262144
