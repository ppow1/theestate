"""Read-only Estate service catalog aggregation.

This module inventories existing operational services and command surfaces without
becoming the source of truth for service definitions.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

INPUT_ARTIFACTS = [
    "data/registry/services.json",
    "data/registry/capabilities.json",
    "data/registry/providers.json",
    "runtime/capabilities/estate_capability_registry.json",
    "runtime/validation/operational_validation_report.json",
    "runtime/readiness/operational_readiness_dashboard.json",
    "operations/readiness/operational_readiness_dashboard.md",
    "src/estate/cli/main.py",
]

COMMAND_SURFACES = [
    {"service_name": "Helen HR Employee Onboarding", "owner": "Human Resources", "resident": "Helen", "capabilities": ["employee.onboard", "personnel.registry", "mailbox.provision"], "commands": ["hr-onboard", "helen-onboard"], "interfaces": ["CLI"], "implementation_references": ["src/estate/core/hr_onboarding.py", "src/estate/cli/main.py"], "documentation_references": ["docs/onboarding/Helen_HR_Operational_Onboarding.md"]},
    {"service_name": "Mission Control Workspace", "owner": "Operations Center", "resident": "Alfred", "capabilities": ["mission.control", "operations.workspace"], "commands": ["operations-board", "daily-board", "steward-command-center"], "interfaces": ["CLI", "runtime artifacts"], "implementation_references": ["src/estate/core/mission_control_workspace.py", "src/estate/core/operations_board.py", "src/estate/core/steward_command_center.py", "src/estate/cli/main.py"], "documentation_references": ["docs/operations/Mission_Control_Workspace_v1.md", "docs/operations/Operations_Board_Runtime_Integration.md"]},
    {"service_name": "Operational Validation", "owner": "Validation", "resident": "Judy", "capabilities": ["validation.run", "work_package.validate", "readiness.report"], "commands": ["operational-validation", "estate-validate-local", "validate-work-package", "validation-metrics-dashboard", "validation-handoff-artifact-workflow", "validation-observations"], "interfaces": ["CLI", "PowerShell scripts", "runtime artifacts"], "implementation_references": ["src/estate/core/operational_validation.py", "src/estate/core/local_operational_validation.py", "src/estate/core/work_package_validation.py", "src/estate/cli/main.py"], "documentation_references": ["docs/operations/Operational_Validation_Reporting.md", "operations/validation/validation_handoff_artifact_workflow.md"]},
    {"service_name": "Notification Router", "owner": "Operations Center", "resident": "Alfred", "capabilities": ["notification.route", "steward.recall"], "commands": ["notification-router", "gotify-send-test"], "interfaces": ["CLI", "Gotify adapter"], "implementation_references": ["src/estate/core/notification_router.py", "src/estate/core/gotify_adapter.py", "src/estate/cli/main.py"], "documentation_references": []},
    {"service_name": "Mailbox Operations", "owner": "Collaboration", "resident": "Alfred", "capabilities": ["mailbox.index", "message.ack", "message.reply", "mailbox.sync"], "commands": ["mailbox-index", "mailbox-sync-duty", "message-ack", "message-reply", "worker-inboxes"], "interfaces": ["CLI", "collaboration mailboxes"], "implementation_references": ["src/estate/core/mailbox_index.py", "src/estate/core/mailbox_sync_duty.py", "src/estate/core/collaboration_messages.py", "src/estate/core/collaboration_ops.py", "src/estate/cli/main.py"], "documentation_references": ["docs/collaboration/Mailbox_Infrastructure_v1.md"]},
    {"service_name": "Worker Runtime Management", "owner": "Operations Center", "resident": "Alfred", "capabilities": ["worker.heartbeat", "worker.monitor", "worker.launch"], "commands": ["worker-heartbeat", "worker-runtime-summary", "worker-runtime-monitor", "autonomous-work-queue-scheduler"], "interfaces": ["CLI", "worker launch adapter"], "implementation_references": ["src/estate/core/worker_runtime_heartbeat.py", "src/estate/core/worker_runtime_monitor.py", "src/estate/core/autonomous_work_queue_scheduler.py", "src/estate/cli/main.py"], "documentation_references": ["docs/collaboration/Worker_Runtime_Contract_v1.md", "docs/collaboration/Local_Worker_Launch_Adapter_v1.md"]},
    {"service_name": "Alfred Orchestration", "owner": "Operations Center", "resident": "Alfred", "capabilities": ["alfred.plan", "alfred.execute", "alfred.request"], "commands": ["alfred", "alfred-request", "alfred-requests", "alfred-promote", "alfred-plan", "alfred-run", "alfred-execute", "alfred-status", "ask-alfred"], "interfaces": ["CLI", "runtime jobs"], "implementation_references": ["src/estate/core/alfred.py", "src/estate/cli/main.py"], "documentation_references": ["docs/alfred_v1_operator_completion.md", "docs/alfred_v1_status.md"]},
]


def _root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path, warnings):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_json", "path": str(path), "message": str(exc)})
        return None


def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("services", "capabilities", "items"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def _exists(root, rel):
    return (root / rel).exists()


def _validation_status(service, readiness):
    status = str(service.get("status", "unknown")).lower()
    if status in {"active", "operational"}:
        return "ready"
    if status in {"draft", "planned"}:
        return "metadata_only"
    if readiness and readiness.get("overall_status") in {"blocked", "degraded"}:
        return readiness.get("overall_status")
    return "unknown"


def generate_estate_service_catalog(root=None, write=True):
    root = _root(root)
    warnings = []
    inputs = {"used": [], "unavailable": []}
    artifacts = {}
    for rel in INPUT_ARTIFACTS:
        if _exists(root, rel):
            inputs["used"].append(rel)
            if rel.endswith(".json"):
                artifacts[rel] = _read_json(root / rel, warnings)
        else:
            inputs["unavailable"].append(rel)
    registry_services = _as_list(artifacts.get("data/registry/services.json"))
    caps = _as_list(artifacts.get("data/registry/capabilities.json"))
    providers = _as_list(artifacts.get("data/registry/providers.json"))
    readiness = artifacts.get("runtime/readiness/operational_readiness_dashboard.json")
    cap_by_service = {}
    for cap in caps:
        for ref in cap.get("related_services", []) or cap.get("services", []) or []:
            cap_by_service.setdefault(ref, []).append(cap.get("id") or cap.get("name"))
    catalog = []
    for i, svc in enumerate(registry_services, 1):
        sid = svc.get("id") or f"unidentified-service-{i}"
        meta_warnings = []
        for key in ("name", "owner", "status"):
            if not svc.get(key):
                meta_warnings.append({"type": f"missing_{key}", "service_id": sid, "message": f"Service {sid} is missing {key}."})
        warnings.extend(meta_warnings)
        catalog.append({
            "id": sid,
            "name": svc.get("name", sid),
            "owner": svc.get("owner", "Unknown"),
            "resident": svc.get("resident"),
            "capabilities": cap_by_service.get(sid, []),
            "interfaces": svc.get("interfaces", []),
            "command_aliases": svc.get("command_aliases", []),
            "operational_status": svc.get("status", "unknown"),
            "validation_status": _validation_status(svc, readiness),
            "source_artifact_links": ["data/registry/services.json"],
            "metadata_warnings": meta_warnings,
        })
    existing_names = {c["name"].lower() for c in catalog}
    for surface in COMMAND_SURFACES:
        refs = surface["implementation_references"] + surface["documentation_references"]
        if not any(_exists(root, r) for r in refs):
            continue
        missing = [r for r in refs if not _exists(root, r)]
        if missing:
            warnings.append({"type": "unresolved_source_link", "service_name": surface["service_name"], "paths": missing})
        if surface["service_name"].lower() in existing_names:
            continue
        catalog.append({
            "id": "derived:" + surface["service_name"].lower().replace(" ", "_"),
            "name": surface["service_name"],
            "owner": surface["owner"],
            "resident": surface["resident"],
            "capabilities": surface["capabilities"],
            "interfaces": surface["interfaces"],
            "command_aliases": surface["commands"],
            "operational_status": "implemented" if any(_exists(root, r) for r in surface["implementation_references"]) else "documented",
            "validation_status": "source_links_checked" if not missing else "source_link_warnings",
            "source_artifact_links": [r for r in refs if _exists(root, r)],
            "metadata_warnings": [],
        })
    payload = {"version": 1, "generated_at": _now(), "authority": "read_only_aggregation_not_source_of_truth", "summary": {"service_count": len(catalog), "registry_service_count": len(registry_services), "provider_count": len(providers), "warning_count": len(warnings)}, "services": catalog, "inputs": inputs, "warnings": warnings, "operations_center_integration": {"status": "supported_by_json_and_markdown_outputs", "json_output": "runtime/services/estate_service_catalog.json", "markdown_output": "operations/services/estate_service_catalog.md"}}
    if write:
        (root / "runtime/services").mkdir(parents=True, exist_ok=True)
        (root / "runtime/services/estate_service_catalog.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (root / "operations/services").mkdir(parents=True, exist_ok=True)
        (root / "operations/services/estate_service_catalog.md").write_text(format_estate_service_catalog(payload) + "\n", encoding="utf-8")
    return payload


def format_estate_service_catalog(payload):
    s = payload.get("summary", {})
    lines = ["# Estate Service Catalog", "", "Read-only aggregation. This report is not the source of truth and does not create a duplicate command registry.", "", f"Generated: {payload.get('generated_at')}", "", "## Summary", f"- Services: {s.get('service_count', 0)}", f"- Registry services: {s.get('registry_service_count', 0)}", f"- Warnings: {s.get('warning_count', 0)}", "", "## Services"]
    for svc in payload.get("services", []):
        lines += ["", f"### {svc.get('name')} ({svc.get('id')})", f"- Owner: {svc.get('owner')}", f"- Resident: {svc.get('resident') or 'Unassigned'}", f"- Operational status: {svc.get('operational_status')}", f"- Validation status: {svc.get('validation_status')}", f"- Capabilities: {', '.join(map(str, svc.get('capabilities') or [])) or 'None recorded'}", f"- Interfaces: {', '.join(map(str, svc.get('interfaces') or [])) or 'None recorded'}", f"- Command aliases: {', '.join(map(str, svc.get('command_aliases') or [])) or 'None recorded'}", f"- Source artifacts: {', '.join(map(str, svc.get('source_artifact_links') or [])) or 'None recorded'}"]
    if payload.get("warnings"):
        lines += ["", "## Warnings"]
        lines.extend(f"- {w.get('type')}: {w.get('message') or w.get('service_name') or ''}" for w in payload["warnings"])
    return "\n".join(lines)


def format_estate_service_catalog_summary(payload):
    s = payload.get("summary", {})
    return "\n".join(["Estate Service Catalog", f"Generated: {payload.get('generated_at')}", f"Services: {s.get('service_count', 0)}", f"Warnings: {s.get('warning_count', 0)}"])
