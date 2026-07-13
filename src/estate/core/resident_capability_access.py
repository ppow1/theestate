"""Staged resident capability and tool-access resolver for WP-4022.

This module is intentionally isolated from active runtime integration targets.
It is designed for later installation into resident authority, resident
interaction, CLI, and Office resident/status surfaces after conflict review.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from estate.core.resident_authority import check_authority
except Exception:  # pragma: no cover - staged fallback for isolated review
    check_authority = None  # type: ignore[assignment]

ROOT = Path(__file__).resolve().parents[4]
APPROVED = "approved"
DENIED = "denied"
UNAVAILABLE = "unavailable"
APPROVAL_REQUIRED = "approval_required"
UNKNOWN = "unknown_resident"

@dataclass(frozen=True)
class ToolSpec:
    key: str
    label: str
    category: str
    operation: str
    executable: str | None = None
    connector: str | None = None
    requires_approval: bool = False
    approval_reason: str | None = None
    description: str = ""

@dataclass(frozen=True)
class ResidentSpec:
    key: str
    display_name: str
    declared_capabilities: tuple[str, ...]
    approved_tools: tuple[str, ...]
    denied_tools: tuple[str, ...] = field(default_factory=tuple)
    candidate: bool = False

TOOL_SPECS: dict[str, ToolSpec] = {
    "local_search": ToolSpec("local_search", "Local repository search", "information", "search", executable="rg", description="Read-only local repository search."),
    "resident_chat": ToolSpec("resident_chat", "Resident chat", "interaction", "summarize", description="Resident conversation and summarization surface."),
    "mailbox_message_draft": ToolSpec("mailbox_message_draft", "Mailbox message artifact draft", "routing", "send-mailbox-message-artifact", requires_approval=True, approval_reason="Mailbox artifacts can affect workflows."),
    "work_package_draft": ToolSpec("work_package_draft", "Work-package draft", "planning", "create-work-package-draft", requires_approval=True, approval_reason="Work-package drafts require Steward review before becoming authoritative."),
    "runtime_presence_update": ToolSpec("runtime_presence_update", "Runtime presence update", "runtime", "update-resident-runtime-state", description="Bounded resident presence/state update."),
    "ollama_text": ToolSpec("ollama_text", "Local Ollama text generation", "model", "summarize", executable="ollama", connector="local_ollama", description="Local-only text generation when Ollama is installed and models are available."),
    "validation_command": ToolSpec("validation_command", "Validation command execution", "validation", "run-validation-command", executable="pytest", description="Validation command execution authority."),
    "merge_approval": ToolSpec("merge_approval", "Merge approval", "governance", "approve-merge-work", description="Merge approval authority."),
    "personnel_identity_modify": ToolSpec("personnel_identity_modify", "Personnel identity modification", "personnel", "modify-personnel-identity", description="Personnel identity changes."),
}

RESIDENT_SPECS: dict[str, ResidentSpec] = {
    "alfred": ResidentSpec("alfred", "Alfred", ("coordination", "routing", "steward_attention_protection", "resident_chat"), ("local_search", "resident_chat", "mailbox_message_draft", "work_package_draft", "runtime_presence_update", "ollama_text"), denied_tools=("validation_command", "merge_approval", "personnel_identity_modify")),
    "helen": ResidentSpec("helen", "Helen", ("workforce_fit", "capability_review", "resident_health", "assignment_advice"), ("local_search", "resident_chat", "mailbox_message_draft", "work_package_draft", "runtime_presence_update"), denied_tools=("validation_command", "merge_approval", "personnel_identity_modify", "ollama_text")),
    "grace": ResidentSpec("grace", "Grace", ("operational_service", "sequence_planning", "dispatch_handoff_request", "resident_chat"), ("resident_chat", "runtime_presence_update", "mailbox_message_draft", "work_package_draft"), denied_tools=("validation_command", "merge_approval", "personnel_identity_modify", "ollama_text"), candidate=False),
}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def resident_key(name: str) -> str:
    return "".join(ch for ch in str(name or "").lower() if ch.isalnum())

def _tool_available(tool: ToolSpec) -> tuple[bool, str | None]:
    if tool.executable and shutil.which(tool.executable) is None:
        return False, f"Required executable {tool.executable!r} was not found on PATH."
    return True, None

def _authority_decision(resident: str, operation: str) -> dict[str, Any]:
    if check_authority is None:
        return {"decision": APPROVAL_REQUIRED if operation in {"send-mailbox-message-artifact", "create-work-package-draft"} else APPROVED, "allowed": True, "requires_steward_approval": operation in {"send-mailbox-message-artifact", "create-work-package-draft"}, "reason": "staged fallback authority metadata"}
    return check_authority(resident, operation, audit=False, source_refs=["collaboration/workstreams/WP-4022/src/wp4022_resident_capabilities/resolver.py"])

def resolve_resident_capabilities(resident: str, *, requested_tools: list[str] | None = None) -> dict[str, Any]:
    """Resolve deterministic resident capabilities and tool access.

    Unknown residents receive no access. Requested undeclared tools are denied.
    Unavailable declared tools are reported as unavailable rather than approved.
    """
    key = resident_key(resident)
    spec = RESIDENT_SPECS.get(key)
    requested = requested_tools or sorted(TOOL_SPECS)
    if spec is None:
        return {"version": 1, "kind": "resident_capability_resolution", "generated_at": _now(), "resident": str(resident), "resident_key": key, "state": UNKNOWN, "declared_capabilities": [], "tool_access": [_tool_payload(None, t, DENIED, "Unknown resident; no resident capability or tool access is implied.") for t in requested], "approval_required_operations": [], "source_references": _sources()}
    access = [_resolve_tool(spec, t) for t in requested]
    return {"version": 1, "kind": "resident_capability_resolution", "generated_at": _now(), "resident": spec.display_name, "resident_key": spec.key, "state": "candidate" if spec.candidate else "active", "declared_capabilities": list(spec.declared_capabilities), "tool_access": access, "approval_required_operations": [a for a in access if a["state"] == APPROVAL_REQUIRED], "source_references": _sources()}

def _resolve_tool(spec: ResidentSpec, key: str) -> dict[str, Any]:
    tool = TOOL_SPECS.get(key)
    if tool is None:
        return _tool_payload(spec, key, DENIED, "Unknown tool; safe default denies access.")
    if key in spec.denied_tools or key not in spec.approved_tools:
        return _tool_payload(spec, key, DENIED, "Tool is not declared for this resident.", tool)
    available, unavailable_reason = _tool_available(tool)
    if not available:
        return _tool_payload(spec, key, UNAVAILABLE, unavailable_reason or "Tool is unavailable at runtime.", tool)
    authority = _authority_decision(spec.display_name, tool.operation)
    if authority.get("requires_steward_approval") or tool.requires_approval:
        return _tool_payload(spec, key, APPROVAL_REQUIRED, tool.approval_reason or authority.get("reason") or "Operation requires approval.", tool, authority)
    if not authority.get("allowed"):
        return _tool_payload(spec, key, DENIED, authority.get("reason") or "Authority check denied access.", tool, authority)
    return _tool_payload(spec, key, APPROVED, authority.get("reason") or "Declared and available.", tool, authority)

def _tool_payload(spec: ResidentSpec | None, key: str, state: str, reason: str, tool: ToolSpec | None = None, authority: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"tool": key, "label": tool.label if tool else key, "category": tool.category if tool else "unknown", "state": state, "approved": state == APPROVED, "available": state in {APPROVED, APPROVAL_REQUIRED}, "requires_approval": state == APPROVAL_REQUIRED, "reason": reason, "resident": spec.display_name if spec else None, "operation": tool.operation if tool else None, "connector": tool.connector if tool else None, "authority_decision": authority.get("decision") if authority else None}

def capability_display_payload(resident: str) -> dict[str, Any]:
    resolved = resolve_resident_capabilities(resident)
    return {"resident": resolved["resident"], "state": resolved["state"], "capabilities": resolved["declared_capabilities"], "tools": resolved["tool_access"], "badges": {"approved": sum(1 for t in resolved["tool_access"] if t["state"] == APPROVED), "approval_required": sum(1 for t in resolved["tool_access"] if t["state"] == APPROVAL_REQUIRED), "denied": sum(1 for t in resolved["tool_access"] if t["state"] == DENIED), "unavailable": sum(1 for t in resolved["tool_access"] if t["state"] == UNAVAILABLE)}}

def office_capability_payload() -> dict[str, Any]:
    return {"version": 1, "kind": "office_resident_capability_display", "generated_at": _now(), "residents": [capability_display_payload(k) for k in sorted(RESIDENT_SPECS)]}

def _sources() -> list[str]:
    return ["collaboration/work_packages/pending/WP-4022_Resident_Capability_and_Tool_Access_Integration.md", "src/estate/core/resident_authority.py", "src/estate/core/resident_interaction.py", "src/estate/core/office_resident_presence.py", "data/registry/residents.json", "data/registry/capabilities.json"]

if __name__ == "__main__":
    print(json.dumps(office_capability_payload(), indent=2, sort_keys=True))
