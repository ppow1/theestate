"""Open WebUI command bridge for governed engineering assignments.

The bridge lets an Open WebUI resident conversation initiate the existing
Helen/Grace engineering workflow. It deliberately creates only governed
artifacts in the already-implemented Helen workforce, Grace operations, and
Dispatch runtimes; it never starts a second scheduler, provider control plane,
or worker execution path.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime, format_grace_action
from estate.core.helen_workforce import HelenWorkforceStore, WorkforceAssessment, WorkforceRequest
from estate.core.paths import ESTATE_ROOT

COMMANDS = {"initiate_engineering_assignment", "engineering_assignment"}
COMMAND_PREFIXES = (
    "initiate engineering department assignment:",
    "start engineering department assignment:",
    "create engineering department assignment:",
)


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def detect_engineering_assignment_command(payload: dict[str, Any], user_message: str) -> dict[str, Any] | None:
    """Return command metadata when a chat turn explicitly requests assignment initiation."""
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    command = str(metadata.get("estate_command") or payload.get("estate_command") or "").strip().lower()
    if command in COMMANDS:
        objective = str(metadata.get("engineering_objective") or payload.get("engineering_objective") or user_message).strip()
        return {"objective": objective, "source": "metadata", "command": command}
    lowered = user_message.strip().lower()
    for prefix in COMMAND_PREFIXES:
        if lowered.startswith(prefix):
            objective = user_message.strip()[len(prefix):].strip() or "Governed Engineering Department assignment requested from Open WebUI."
            return {"objective": objective, "source": "chat_prefix", "command": "initiate_engineering_assignment"}
    return None


def initiate_engineering_assignment_from_chat(
    payload: dict[str, Any],
    *,
    user_message: str,
    session_id: str | None = None,
    root: Path | None = None,
) -> dict[str, Any] | None:
    """Create Helen staffing and Grace operational artifacts for one chat command."""
    command = detect_engineering_assignment_command(payload, user_message)
    if not command:
        return None
    objective_text = command["objective"]
    rootp = _root(root)
    store = HelenWorkforceStore(rootp)
    request = WorkforceRequest.create(
        request_type="staffing_request",
        subject_id="openwebui-engineering-assignment",
        subject_type="engineering_assignment",
        requesting_office="Steward via Open WebUI",
        summary=f"Staff a governed Engineering Department assignment requested from chat: {objective_text}",
        requested_outcome="Helen confirms a bounded local engineering worker can be assigned to Grace for governed operational handling.",
        source_artifacts=["collaboration/work_packages/pending/WP-0649_WebUI_Helen_Grace_Engineering_Workflow_Integration.md"],
        requires_steward_attention=False,
        metadata={"open_webui_session_id": session_id, "command_source": command["source"], "second_execution_system_created": False},
    )
    request_path = store.save_request(request)
    assessment = WorkforceAssessment.create(
        request_id=request.request_id,
        subject_id=request.subject_id,
        worker_factors=["chat request is bounded to an existing Engineering Department workflow"],
        institutional_factors=["Helen owns staffing evidence only", "Grace owns operational assignment", "Dispatch remains the handoff authority"],
        missing_evidence=[],
        recommendations=["staffing_action"],
        rationale="Helen records staffing readiness for a single governed Engineering Department assignment initiated from Open WebUI.",
        evidence_artifacts=[str(request_path.relative_to(rootp))],
        grace_operational_constraint_summary="Grace may create and track the governed assignment, but provider execution remains behind existing Dispatch and adapters.",
        metadata={"open_webui_session_id": session_id, "requested_objective": objective_text},
    )
    assessment_path = store.save_assessment(assessment)
    grace = GraceOperationsRuntime(rootp)
    objective = GraceObjective.create(
        requested_by="Steward via Open WebUI",
        title="Open WebUI Engineering Department assignment",
        summary=objective_text,
        work_package_id="WP-0649",
        owner="local-engineering-worker-001",
        checkpoint="Grace records assignment state; Chief Architect and Steward retain acceptance authority.",
        evidence=[str(request_path.relative_to(rootp)), str(assessment_path.relative_to(rootp))],
        metadata={"helen_assessment_id": assessment.assessment_id, "open_webui_session_id": session_id, "summary_safe": True, "open_webui_engineering_assignment": True},
    )
    action, paths = grace.conduct_objective(objective, request_dispatch=True)
    return {
        "command": command["command"],
        "objective": objective.to_dict(),
        "helen_request": request.to_dict(),
        "helen_assessment": assessment.to_dict(),
        "grace_action": action.to_dict(),
        "paths": {key: str(Path(value).relative_to(rootp)) if Path(value).is_absolute() else value for key, value in paths.items()},
        "summary": format_grace_action(action, paths),
        "provider_execution_performed": False,
        "second_execution_system_created": False,
    }
