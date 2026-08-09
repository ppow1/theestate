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
import hashlib
import json
from uuid import uuid4

from estate.core.compute_resources import ComputeReservationLedger, ComputeResourceRequirements, collect_nvidia_smi, select_resource, write_compute_projection
from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime, format_grace_action
from estate.core.helen_workforce import HelenWorkforceStore, WorkforceAssessment, WorkforceRequest
from estate.core.grace_helen_engineering_composition import GraceHelenEngineeringComposition
from estate.core.gpu_runtime_lanes import endpoint_health, load_registered_lanes, select_runtime_lane
from estate.core.ptm_production_readiness import append_ptm_event
from estate.core.execution_provider_adapter import utc_now
from estate.core.paths import ESTATE_ROOT

COMMANDS = {"initiate_engineering_assignment", "engineering_assignment"}
COMMAND_PREFIXES = (
    "initiate engineering department assignment:",
    "start engineering department assignment:",
    "create engineering department assignment:",
)
BOUNDED_TEXT_PREFIXES = (
    "run a small bounded local text task",
    "run a bounded local text task",
    "execute a bounded local text task",
)


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _qwen_minimum_safe_vram_mib(root: Path) -> int | None:
    """Load the model-specific admission floor; never substitute a generic floor."""
    path = root / "config/providers/qwen_local_text.json"
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
        value = config.get("minimum_safe_vram_mib")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            return None
        return int(value)
    except (OSError, ValueError, TypeError):
        return None


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


def detect_bounded_local_text_intent(payload: dict[str, Any], user_message: str) -> dict[str, Any]:
    """Classify only the explicit, narrow local-text execution command."""
    model = str(payload.get("model") or "")
    text = str(user_message or "").strip()
    lowered = text.lower()
    if lowered.startswith("grace,") or lowered.startswith("grace:"):
        lowered = lowered.split(":", 1)[1] if lowered.startswith("grace:") else lowered.split(",", 1)[1].lstrip()
    if model not in {"estate/grace", "estate/grace-grounded-test"}:
        return {"state": "conversation_only", "reason": "resident is not Grace"}
    if any(lowered.startswith(prefix) for prefix in BOUNDED_TEXT_PREFIXES):
        return {"state": "execution_requested", "intent": "bounded_local_text", "source": "explicit_chat_prefix"}
    if "execute" in lowered or "run " in lowered:
        return {"state": "execution_blocked", "reason": "execution wording is ambiguous; use an explicit bounded local text task request"}
    return {"state": "conversation_only", "reason": "no executable intent detected"}


def _readiness_event(rootp: Path, objective: GraceObjective) -> dict[str, Any]:
    source = rootp / "runtime/compute_resources/gpus.json"
    source_ref = {"source_path": str(source.relative_to(rootp)).replace("\\", "/"), "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "adapter_name": "compute-resource-runtime", "adapter_version": "estate.compute-resources.v1"}
    observed = utc_now()
    return append_ptm_event(
        rootp,
        event_type="task.readiness_inputs",
        aggregate_type="task",
        aggregate_id=f"task-{objective.objective_id}",
        stream_id=f"task:task-{objective.objective_id}",
        actor_ref="Grace governed local text execution",
        authority_refs=["PTM", "GraceHelenEngineeringComposition"],
        source_refs=[source_ref],
        payload_schema="estate.ptm.readiness-input.v1",
        payload={"objective_id": objective.objective_id, "task_id": f"task-{objective.objective_id}", "enabling_project_id": "project-local-text", "dependencies": [{"dependency_id": "compute-resource-evidence", "state": "satisfied", "observed_at": observed}], "gate_checks": [{"name": "compute-resource-health", "state": "pass", "observed_at": observed}], "source_references": [source_ref]},
        idempotency_key=f"grace-bounded-text:{objective.objective_id}",
        occurred_at=observed,
    )


def execute_bounded_local_text_from_chat(payload: dict[str, Any], *, user_message: str, session_id: str | None = None, root: Path | None = None) -> dict[str, Any] | None:
    intent = detect_bounded_local_text_intent(payload, user_message)
    if intent["state"] != "execution_requested":
        return intent if intent["state"] == "execution_blocked" else None
    rootp = _root(root)
    minimum_safe_vram_mib = _qwen_minimum_safe_vram_mib(rootp)
    if minimum_safe_vram_mib is None:
        return {"state": "execution_blocked", "reason": "model-specific safe VRAM admission requirement is unavailable", "provider_execution_performed": False}
    observations = collect_nvidia_smi()
    if not observations:
        return {"state": "execution_blocked", "reason": "fresh physical compute evidence is unavailable", "provider_execution_performed": False}
    write_compute_projection(observations, rootp)
    preferred = next((row.nvidia_uuid for row in observations if "4090" in row.name), None)
    requirements = ComputeResourceRequirements(requires_gpu=True, minimum_vram_mib=minimum_safe_vram_mib, preferred_gpu_uuid=preferred, freshness_seconds=120)
    placement = select_resource(observations, requirements)
    if not placement.get("eligible") or not placement.get("selected"):
        return {"state": "execution_blocked", "reason": placement.get("reason", "no eligible GPU"), "placement": placement, "provider_execution_performed": False}
    selected = next(row for row in observations if row.resource_id == placement["selected"])
    lanes = load_registered_lanes(rootp)
    lane_selection = select_runtime_lane(lanes, provider_id="qwen.local.text", model_identity="qwen3:8b", required_gpu_uuid=selected.nvidia_uuid, required_resource_id=selected.resource_id)
    lane = next((row for row in lanes if row.runtime_lane_id == lane_selection.get("selected")), None)
    if lane is None:
        return {"state": "execution_blocked", "reason": "no registered runtime lane matches the selected physical GPU", "placement": placement, "lane_selection": lane_selection, "provider_execution_performed": False}
    lane_health = endpoint_health(lane)
    if not lane_health.get("healthy"):
        return {"state": "execution_blocked", "reason": "selected runtime lane is not healthy", "lane_id": lane.runtime_lane_id, "lane_health": lane_health, "provider_execution_performed": False}
    objective = GraceObjective.create(requested_by="Steward via Open WebUI", title="Bounded local text task", summary=user_message.strip(), work_package_id="WP-0649", owner="qwen-local-text", checkpoint="Grace records provider receipt and physical placement evidence; acceptance remains with Engineering and the Steward.", metadata={"summary_safe": True, "openwebui_bounded_local_text": True})
    artifact_path = f"docs/operations/examples/grace_bounded_local_text_{objective.objective_id}.md"
    receipt_path = f"runtime/engineering_adapter_receipts/grace_bounded_local_text_{objective.objective_id}.json"
    authority = {"allowed_read_paths": ["docs/operations/Governed_Qwen_Local_Text_Provider.md", "config/providers/qwen_local_text.json"], "allowed_write_paths": [artifact_path, receipt_path], "expected_outputs": [artifact_path, receipt_path], "runtime_lane_id": lane.runtime_lane_id}
    objective.metadata["execution_authority"] = authority
    grace = GraceOperationsRuntime(rootp)
    action, paths = grace.conduct_objective(objective)
    action_record = json.loads((rootp / paths["action"]).read_text(encoding="utf-8"))
    health_path = rootp / f"runtime/provider_health/grace_qwen_{objective.objective_id}.json"
    health_path.parent.mkdir(parents=True, exist_ok=True)
    health_path.write_text(json.dumps({"provider_id": "qwen.local.text", "runtime_lane_id": lane.runtime_lane_id, "endpoint_health": lane_health, "observed_at": utc_now()}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    inquiry = GraceHelenEngineeringComposition(rootp).request_capability(objective.objective_id, "text_generation", constraints=["bounded artifact", "one provider receipt", "UUID-pinned runtime lane"])
    comp = GraceHelenEngineeringComposition(rootp)
    determination = comp.determine_capability(inquiry["capability_request_id"], disposition="qualified_and_available", worker_profile_id="qwen-local-text", qualification_evidence=["config/providers/qwen_local_text.json", str(health_path.relative_to(rootp)).replace("\\", "/")], availability_evidence=[str(health_path.relative_to(rootp)).replace("\\", "/")], capacity_evidence=["runtime/compute_resources/gpus.json"], provider_health_evidence=[str(health_path.relative_to(rootp)).replace("\\", "/")], evidence_observed_at=utc_now())
    event = _readiness_event(rootp, objective)
    reservation_id = f"gpu-reservation-{objective.objective_id}"
    ComputeReservationLedger(rootp).reserve(reservation_id=reservation_id, resource_id=selected.resource_id, workload_id=objective.objective_id, minimum_vram_mib=requirements.minimum_vram_mib)
    requirements = ComputeResourceRequirements(**{**requirements.__dict__, "required_gpu_uuid": selected.nvidia_uuid, "required_resource_id": selected.resource_id, "reservation_reference": reservation_id, "evidence_reference": "runtime/compute_resources/gpus.json"})
    try:
        governed = comp.governed_commission_and_dispatch(objective.objective_id, determination["determination_id"], grace_action_id=action.action_id, operations_decision_id=action_record["metadata"]["operations_decision_id"], bounded_objective=objective.summary, acceptance_criteria=["one bounded text artifact", "one provider receipt", "allocated UUID equals runtime lane UUID"], ptm_source_high_watermark=event["event_id"], ptm_task_or_package_id=f"task-{objective.objective_id}", enabling_project_id="project-local-text", provider_id="qwen.local.text", provider_type="execution", adapter_reference="qwen-local-ollama-text-adapter@1.0.0", execution_metadata=authority, compute_resource_requirements=requirements.to_dict(), idempotency_key=f"grace-bounded-text:{objective.objective_id}")
        execution = comp.execute_registered_dispatch(governed["dispatch"]["dispatch_id"], governed["authorization"]["authorization_id"], objective.objective_id)
    finally:
        ComputeReservationLedger(rootp).release(reservation_id)
    return {"state": "execution_completed" if execution.get("status") == "completed" else "execution_failed", "intent": intent, "objective": objective.to_dict(), "grace_action": action.to_dict(), "placement": placement, "lane": lane.to_dict(), "governed": governed, "execution": execution, "provider_execution_performed": execution.get("status") == "completed", "session_id": session_id}


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
