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
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import re
from uuid import uuid4

from estate.core.compute_resources import ComputeReservationLedger, ComputeResourceRequirements, collect_nvidia_smi, select_resource, write_compute_projection
from estate.core.grace_operations_runtime import GraceObjective, GraceOperationsRuntime, format_grace_action
from estate.core.helen_workforce import HelenWorkforceStore, WorkforceAssessment, WorkforceRequest
from estate.core.grace_helen_engineering_composition import GraceHelenEngineeringComposition
from estate.core.gpu_runtime_lanes import endpoint_health, load_registered_lanes, select_runtime_lane
from estate.core.gpu_runtime_lifecycle import ensure_runtime_lane_ready
from estate.core.governed_execution_runtime_state import ensure_governed_execution_runtime_state
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
BOUNDED_TEXT_ACTION_PATTERN = re.compile(r"\b(?:run|execute|use)\b", re.I)
BOUNDED_TEXT_SIZE_PATTERN = re.compile(r"\b(?:small|tiny|bounded)\b", re.I)
BOUNDED_TEXT_LOCAL_PATTERN = re.compile(r"\blocal(?:ly)?\b", re.I)
BOUNDED_TEXT_TASK_PATTERN = re.compile(r"\b(?:text(?:[- ]generation)?|generation)\s*task\b|\btext execution\b", re.I)
BOUNDED_TEXT_GOVERNED_PATTERN = re.compile(r"\bgoverned\b", re.I)
UNSAFE_LOCAL_ACTION_PATTERN = re.compile(r"\b(?:benchmark|stress|delete|remove|powershell|shell)\b", re.I)
PARALLEL_COUNT_PATTERN = re.compile(r"\b(?:two|2|pair\s+of)\b", re.I)
PARALLEL_CONCURRENCY_PATTERN = re.compile(r"\b(?:concurrent(?:ly)?|parallel|at\s+the\s+same\s+time|simultaneous(?:ly)?)\b", re.I)
PARALLEL_TASK_PATTERN = re.compile(r"\b(?:local\s+)?text(?:[- ]generation)?\s+tasks?\b|\btext execution\b", re.I)
PARALLEL_GOVERNED_PATTERN = re.compile(r"\bgoverned\b|\bqualified\s+(?:gpu\s+)?lanes?\b", re.I)
PARALLEL_QUALIFIED_LANE_PATTERN = re.compile(r"\b(?:4090|p100)\b", re.I)
PARALLEL_UNKNOWN_LANE_PATTERN = re.compile(r"\b(?:a100|v100|t4|3090|p40|other\s+gpu|both\s+gpus)\b", re.I)
P100_RESOURCE_PATTERNS = (
    re.compile(r"\bgoverned\s+p100\s+compute\s+(?:lane|resource)\b", re.I),
    re.compile(r"\btesla\s+p100\b", re.I),
    re.compile(r"\bp100\s+(?:compute\s+)?(?:lane|resource)\b", re.I),
)
RAW_PLACEMENT_PATTERN = re.compile(r"\bGPU-[0-9a-f]{8,}(?:-[0-9a-f-]+)?\b|\bqwen\.local\.text\.[a-z0-9.-]+\b", re.I)
UNRESOLVED_PLACEMENT_PATTERN = re.compile(r"\b(?:use|using|run\s+on|execute\s+on)\b.{0,80}\b(?:gpu|compute\s+(?:lane|resource)|tesla|rtx)\b", re.I)


def _root(root: Path | None = None) -> Path:
    return root or (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _provider_config(root: Path, relative: str) -> dict[str, Any] | None:
    """Load a model-specific provider instance; never substitute a generic one."""
    path = root / relative
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
        return config if isinstance(config, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def _qwen_minimum_safe_vram_mib(root: Path) -> int | None:
    config = _provider_config(root, "config/providers/qwen_local_text.json")
    value = config.get("minimum_safe_vram_mib") if config else None
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 else None


def _target_lane(root: Path, observations: list[Any]) -> tuple[Any, dict[str, Any], Any] | None:
    lanes = load_registered_lanes(root)
    requested = os.environ.get("ESTATE_GOVERNED_LOCAL_TEXT_LANE", "").strip()
    if requested:
        lane = next((item for item in lanes if item.runtime_lane_id == requested), None)
        if lane is None:
            return None
        config = _provider_config(root, lane.provider_config_path)
        selected = next((row for row in observations if row.nvidia_uuid == lane.gpu_uuid and row.resource_id == lane.compute_resource_id), None)
        return (lane, config, selected) if config and selected else None
    preferred = next((row for row in observations if "4090" in row.name), None)
    lane = next((item for item in lanes if item.provider_id == "qwen.local.text" and item.model_identity == "qwen3:8b" and (not preferred or item.gpu_uuid == preferred.nvidia_uuid)), None)
    config = _provider_config(root, lane.provider_config_path if lane else "config/providers/qwen_local_text.json") if lane else None
    return (lane, config, preferred) if lane and config and preferred else None


def detect_bounded_compute_resource_intent(user_message: str) -> dict[str, Any]:
    """Resolve only narrow symbolic placement language; never trust raw IDs."""
    text = str(user_message or "").strip()
    if RAW_PLACEMENT_PATTERN.search(text):
        return {"state": "blocked", "reason": "raw GPU UUID or runtime lane text is not a trusted placement selector"}
    if any(pattern.search(text) for pattern in P100_RESOURCE_PATTERNS):
        return {"state": "required", "symbol": "p100", "source": "registered_compute_resource_symbol"}
    if UNRESOLVED_PLACEMENT_PATTERN.search(text):
        return {"state": "blocked", "reason": "physical compute selector is unknown or unsupported"}
    return {"state": "none"}


def _target_symbolic_lane(root: Path, observations: list[Any], symbol: str) -> tuple[Any, dict[str, Any], Any] | None:
    if symbol != "p100":
        return None
    physical = next((row for row in observations if "tesla p100" in str(row.name).lower()), None)
    if physical is None:
        return None
    lanes = load_registered_lanes(root)
    lane = next((item for item in lanes if item.provider_id == "qwen.local.text" and item.gpu_uuid == physical.nvidia_uuid and item.compute_resource_id == physical.resource_id), None)
    config = _provider_config(root, lane.provider_config_path) if lane else None
    return (lane, config, physical) if lane and config else None


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
    if UNSAFE_LOCAL_ACTION_PATTERN.search(lowered):
        return {"state": "execution_blocked", "reason": "unsafe local action is outside bounded text-task execution"}
    parallel_bounded_text = (
        PARALLEL_COUNT_PATTERN.search(lowered)
        and PARALLEL_CONCURRENCY_PATTERN.search(lowered)
        and PARALLEL_TASK_PATTERN.search(lowered)
        and PARALLEL_GOVERNED_PATTERN.search(lowered)
        and (BOUNDED_TEXT_LOCAL_PATTERN.search(lowered) or PARALLEL_QUALIFIED_LANE_PATTERN.search(lowered))
    )
    if parallel_bounded_text:
        if PARALLEL_UNKNOWN_LANE_PATTERN.search(lowered):
            return {"state": "execution_blocked", "reason": "parallel request names an unsupported or ambiguous runtime lane"}
        return {
            "state": "execution_requested",
            "intent": "parallel_bounded_local_text",
            "source": "semantic_parallel_chat_intent",
            "task_specs": _parallel_bounded_text_task_specs(),
        }
    if any(lowered.startswith(prefix) for prefix in BOUNDED_TEXT_PREFIXES):
        return {"state": "execution_requested", "intent": "bounded_local_text", "source": "explicit_chat_prefix"}
    semantic_bounded_text = all(
        pattern.search(lowered)
        for pattern in (
            BOUNDED_TEXT_ACTION_PATTERN,
            BOUNDED_TEXT_SIZE_PATTERN,
            BOUNDED_TEXT_LOCAL_PATTERN,
            BOUNDED_TEXT_TASK_PATTERN,
        )
    ) and (BOUNDED_TEXT_GOVERNED_PATTERN.search(lowered) or re.search(r"\btext[- ]generation\b", lowered))
    if semantic_bounded_text and not UNSAFE_LOCAL_ACTION_PATTERN.search(lowered):
        return {"state": "execution_requested", "intent": "bounded_local_text", "source": "semantic_chat_intent"}
    if BOUNDED_TEXT_ACTION_PATTERN.search(lowered):
        return {"state": "execution_blocked", "reason": "execution wording is ambiguous; use an explicit bounded local text task request"}
    return {"state": "conversation_only", "reason": "no executable intent detected"}


def _parallel_bounded_text_task_specs() -> list[dict[str, Any]]:
    """Return the fixed, already-qualified two-lane UI parallel contract."""
    return [
        {
            "task_id": "rtx4090",
            "runtime_lane_id": "qwen.local.text.4090",
            "gpu_symbol": "rtx4090",
            "model": "qwen3:8b",
            "context_limit": None,
            "output_cap": None,
            "concurrency": 1,
        },
        {
            "task_id": "p100",
            "runtime_lane_id": "qwen.local.text.p100-1",
            "gpu_symbol": "p100",
            "model": "llama3.2:3b",
            "context_limit": 1024,
            "output_cap": 32,
            "concurrency": 1,
        },
    ]


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
    try:
        ensure_governed_execution_runtime_state(rootp)
    except (OSError, RuntimeError, ValueError) as exc:
        return {"state": "execution_blocked", "reason": f"governed execution runtime state is unavailable: {exc}", "provider_execution_performed": False}
    observations = collect_nvidia_smi()
    if not observations:
        return {"state": "execution_blocked", "reason": "fresh physical compute evidence is unavailable", "provider_execution_performed": False}
    write_compute_projection(observations, rootp)
    resource_intent = detect_bounded_compute_resource_intent(user_message)
    if resource_intent["state"] == "blocked":
        return {"state": "execution_blocked", "reason": resource_intent["reason"], "resource_intent": resource_intent, "provider_execution_performed": False}
    target = _target_symbolic_lane(rootp, observations, resource_intent["symbol"]) if resource_intent["state"] == "required" else _target_lane(rootp, observations)
    if not target:
        return {"state": "execution_blocked", "reason": "governed local-text target lane or its physical resource is unavailable", "resource_intent": resource_intent, "provider_execution_performed": False}
    lane, config, target_observation = target
    minimum_safe_vram_mib = lane.minimum_vram_mib or config.get("minimum_safe_vram_mib")
    if not isinstance(minimum_safe_vram_mib, int) or minimum_safe_vram_mib < 1:
        return {"state": "execution_blocked", "reason": "model-specific safe VRAM admission requirement is unavailable", "provider_execution_performed": False}
    requirements = ComputeResourceRequirements(requires_gpu=True, minimum_vram_mib=minimum_safe_vram_mib, preferred_gpu_uuid=lane.gpu_uuid, required_gpu_uuid=lane.gpu_uuid, required_resource_id=lane.compute_resource_id, freshness_seconds=120)
    placement = select_resource(observations, requirements)
    if not placement.get("eligible") or not placement.get("selected"):
        return {"state": "execution_blocked", "reason": placement.get("reason", "no eligible GPU"), "placement": placement, "provider_execution_performed": False}
    selected = next(row for row in observations if row.resource_id == placement["selected"])
    lane_selection = select_runtime_lane([lane], provider_id="qwen.local.text", model_identity=lane.model_identity, required_gpu_uuid=selected.nvidia_uuid, required_resource_id=selected.resource_id)
    if not lane_selection.get("eligible"):
        return {"state": "execution_blocked", "reason": "no registered runtime lane matches the selected physical GPU", "placement": placement, "lane_selection": lane_selection, "provider_execution_performed": False}
    lane_readiness = ensure_runtime_lane_ready(rootp, lane)
    lane_health = lane_readiness.get("health", {})
    if lane_readiness.get("status") != "READY":
        return {"state": "execution_blocked", "reason": lane_readiness.get("reason", "selected runtime lane could not be made ready"), "lane_id": lane.runtime_lane_id, "lane_health": lane_health, "lane_readiness": lane_readiness, "provider_execution_performed": False}
    objective = GraceObjective.create(requested_by="Steward via Open WebUI", title="Bounded local text task", summary=user_message.strip(), work_package_id="WP-0649", owner="qwen-local-text", checkpoint="Grace records provider receipt and physical placement evidence; acceptance remains with Engineering and the Steward.", metadata={"summary_safe": True, "openwebui_bounded_local_text": True, "resource_intent": resource_intent, "compute_resource_requirements": requirements.to_dict()})
    artifact_path = f"docs/operations/examples/grace_bounded_local_text_{objective.objective_id}.md"
    receipt_path = f"runtime/engineering_adapter_receipts/grace_bounded_local_text_{objective.objective_id}.json"
    provider_config_path = lane.provider_config_path
    authority = {"allowed_read_paths": ["docs/operations/Governed_Qwen_Local_Text_Provider.md", provider_config_path], "allowed_write_paths": [artifact_path, receipt_path], "expected_outputs": [artifact_path, receipt_path], "runtime_lane_id": lane.runtime_lane_id, "compute_resource_requirements": requirements.to_dict()}
    objective.metadata["execution_authority"] = authority
    grace = GraceOperationsRuntime(rootp)
    action, paths = grace.conduct_objective(objective)
    action_record = json.loads((rootp / paths["action"]).read_text(encoding="utf-8"))
    health_path = rootp / f"runtime/provider_health/grace_qwen_{objective.objective_id}.json"
    health_path.parent.mkdir(parents=True, exist_ok=True)
    health_path.write_text(json.dumps({"provider_id": "qwen.local.text", "runtime_lane_id": lane.runtime_lane_id, "endpoint_health": lane_health, "observed_at": utc_now()}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    inquiry = GraceHelenEngineeringComposition(rootp).request_capability(objective.objective_id, "text_generation", constraints=["bounded artifact", "one provider receipt", "UUID-pinned runtime lane"])
    comp = GraceHelenEngineeringComposition(rootp)
    determination = comp.determine_capability(inquiry["capability_request_id"], disposition="qualified_and_available", worker_profile_id="qwen-local-text", qualification_evidence=[provider_config_path, str(health_path.relative_to(rootp)).replace("\\", "/")], availability_evidence=[str(health_path.relative_to(rootp)).replace("\\", "/")], capacity_evidence=["runtime/compute_resources/gpus.json"], provider_health_evidence=[str(health_path.relative_to(rootp)).replace("\\", "/")], evidence_observed_at=utc_now())
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


def execute_parallel_bounded_local_text_from_chat(payload: dict[str, Any], *, user_message: str, session_id: str | None = None, root: Path | None = None) -> dict[str, Any] | None:
    """Run exactly the two qualified local-text lanes through the existing governed executor."""
    intent = detect_bounded_local_text_intent(payload, user_message)
    if intent.get("state") != "execution_requested" or intent.get("intent") != "parallel_bounded_local_text":
        return intent if intent.get("state") == "execution_blocked" else None
    specs = intent["task_specs"]
    task_messages = {
        "rtx4090": "Run a small governed local text task and return one short result.",
        "p100": "Run a small governed local text task using the governed P100 compute lane and return one short result.",
    }

    def run(spec: dict[str, Any]) -> dict[str, Any]:
        task_payload = dict(payload)
        metadata = dict(payload.get("metadata") or {})
        metadata["parallel_task_id"] = spec["task_id"]
        metadata["parallel_runtime_lane_id"] = spec["runtime_lane_id"]
        task_payload["metadata"] = metadata
        return execute_bounded_local_text_from_chat(
            task_payload,
            user_message=task_messages[spec["task_id"]],
            session_id=session_id,
            root=root,
        ) or {"state": "execution_blocked", "reason": "parallel task returned no governed result", "provider_execution_performed": False}

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="grace-parallel-text") as pool:
        results = list(pool.map(run, specs))
    completed = all(item.get("state") == "execution_completed" for item in results)
    return {
        "state": "execution_completed" if completed else "execution_failed",
        "intent": intent,
        "parallel": True,
        "task_specs": specs,
        "tasks": results,
        "provider_execution_performed": completed,
        "session_id": session_id,
    }


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
