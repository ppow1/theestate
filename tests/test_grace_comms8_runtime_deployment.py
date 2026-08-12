from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "deploy_grace_comms8_runtime.ps1"


def test_deployment_is_selective_and_contains_accepted_surface():
    text = SCRIPT.read_text(encoding="utf-8")
    required = [
        "autonomous_chatgpt_mailbox_worker.py",
        "grace_consultation_loop.py",
        "consultation_store.py",
        "openwebui_resident_surface.py",
        "resident_gateway.py",
        "chatgpt_mailbox_worker_browser.cjs",
        "comms8_streamable_http_adapter.py",
    ]
    assert all(name in text for name in required)
    assert "repository wholesale" in text
    assert "Copy-Item" in text


def test_grace_catalog_contract_is_canonical():
    source = (ROOT / "src/estate/core/openwebui_resident_surface.py").read_text(encoding="utf-8")
    for name in (
        "grace_runtime_bridge",
        "estate_comms8_create_reasoning_request",
        "estate_comms8_list_requests",
        "estate_comms8_read_request",
        "estate_comms8_claim_request",
        "estate_comms8_acknowledge_request",
        "estate_comms8_respond_request",
        "estate_comms8_resolve_request",
    ):
        assert name in source
