from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wp4022_resident_capabilities.resolver import (  # noqa: E402
    APPROVAL_REQUIRED,
    DENIED,
    UNKNOWN,
    capability_display_payload,
    office_capability_payload,
    resolve_resident_capabilities,
)


def by_tool(payload, key):
    return next(item for item in payload["tool_access"] if item["tool"] == key)


def test_alfred_gets_declared_routing_tools_but_not_validation_or_merge():
    payload = resolve_resident_capabilities("Alfred", requested_tools=["local_search", "mailbox_message_draft", "validation_command", "merge_approval"])
    assert payload["resident"] == "Alfred"
    assert "routing" in payload["declared_capabilities"]
    assert by_tool(payload, "mailbox_message_draft")["state"] == APPROVAL_REQUIRED
    assert by_tool(payload, "validation_command")["state"] == DENIED
    assert by_tool(payload, "merge_approval")["state"] == DENIED


def test_helen_has_workforce_capabilities_without_undeclared_ollama_access():
    payload = resolve_resident_capabilities("Helen", requested_tools=["local_search", "ollama_text", "personnel_identity_modify"])
    assert "workforce_fit" in payload["declared_capabilities"]
    assert by_tool(payload, "local_search")["state"] in {"approved", "unavailable"}
    assert by_tool(payload, "ollama_text")["state"] == DENIED
    assert by_tool(payload, "personnel_identity_modify")["state"] == DENIED


def test_grace_candidate_is_limited_and_deterministic():
    first = resolve_resident_capabilities("Grace", requested_tools=["resident_chat", "work_package_draft", "runtime_presence_update"])
    second = resolve_resident_capabilities("grace", requested_tools=["resident_chat", "work_package_draft", "runtime_presence_update"])
    assert first["state"] == "candidate"
    assert first["declared_capabilities"] == second["declared_capabilities"]
    assert by_tool(first, "resident_chat")["state"] == DENIED
    assert by_tool(first, "work_package_draft")["state"] == DENIED
    assert by_tool(first, "runtime_presence_update")["state"] == DENIED


def test_unknown_resident_receives_no_implied_access():
    payload = resolve_resident_capabilities("Unknown Resident", requested_tools=["local_search", "resident_chat"])
    assert payload["state"] == UNKNOWN
    assert payload["declared_capabilities"] == []
    assert all(tool["state"] == DENIED for tool in payload["tool_access"])


def test_display_payloads_include_truthful_badges_and_office_surface():
    display = capability_display_payload("Alfred")
    assert display["badges"]["approval_required"] >= 1
    office = office_capability_payload()
    assert office["kind"] == "office_resident_capability_display"
    assert {resident["resident"] for resident in office["residents"]} == {"Alfred", "Grace", "Helen"}
