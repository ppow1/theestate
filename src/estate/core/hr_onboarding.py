"""Helen HR employee onboarding orchestration.

This module composes the existing personnel registry, mailbox infrastructure,
onboarding manifests, document registry, and resolver into one conservative
local workflow. It does not create a parallel identity or mailbox authority.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from estate.core.mailbox_index import ensure_mailbox_directories, generate_mailbox_index, mailbox_directory_name
from estate.core.personnel_identity import resolve_personnel_identity
from estate.core.paths import ESTATE_ROOT

VALID_PACKAGE_TYPES = {"worker", "chief_architect", "standard"}
REQUIRED_DOCUMENTS = {
    "worker": ["docs/operations/Onboarding_Checklist_v1.md", "docs/onboarding/Worker_Onboarding_Manifest.md", "docs/onboarding/worker_onboarding_manifest.json"],
    "chief_architect": ["docs/operations/Onboarding_Checklist_v1.md", "docs/onboarding/Chief_Architect_Onboarding_Manifest.md", "docs/onboarding/chief_architect_onboarding_manifest.json"],
    "standard": ["docs/operations/Onboarding_Checklist_v1.md", "docs/governance/Estate_Orientation_Handbook.md"],
}
HISTORICAL_MEMORANDA = [
    "collaboration/messages/msg_ca2_20260701_0003_ca4_onboarding_packet.md",
]


def _root(root=None):
    return Path(root) if root else ESTATE_ROOT


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json_list(path):
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON list")
    return payload


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _relative(root, path):
    return str(Path(path).relative_to(root)).replace("\\", "/")


def _step(name, status="completed", detail=None, artifact=None):
    item = {"step": name, "status": status}
    if detail:
        item["detail"] = detail
    if artifact:
        item["artifact"] = artifact
    return item


def _message_id(employee_id, name):
    safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(name)).strip("_") or "employee"
    return f"msg_helen_onboarding_employee_{int(employee_id):04d}_{safe}"


def run_employee_onboarding(*, name, department, office, role, classification, package_type="worker", steward_authorization=None, root=None, dry_run=False):
    base = _root(root)
    result = {
        "ok": False,
        "generated_at": _now(),
        "actor": "Helen / Human Resources",
        "work_package_id": "WP-0080",
        "dry_run": bool(dry_run),
        "input": {"name": name, "department": department, "office": office, "role": role, "classification": classification, "package_type": package_type},
        "steps": [],
        "warnings": [],
        "artifacts": {},
    }

    required = {"name": name, "department": department, "office": office, "role": role, "classification": classification, "steward_authorization": steward_authorization}
    missing = [key for key, value in required.items() if not str(value or "").strip()]
    if missing:
        result["error"] = f"missing required input(s): {', '.join(missing)}"
        result["steps"].append(_step("validate_inputs", "failed", result["error"]))
        return result
    if package_type not in VALID_PACKAGE_TYPES:
        result["error"] = f"unsupported onboarding package type: {package_type}"
        result["steps"].append(_step("validate_inputs", "failed", result["error"]))
        return result
    if str(steward_authorization).strip().lower() in {"no", "none", "false", "unauthorized"}:
        result["error"] = "Steward authorization evidence is required before Helen may issue an employee identity."
        result["steps"].append(_step("confirm_steward_authorization", "failed", result["error"]))
        return result
    result["steps"].append(_step("confirm_steward_authorization", detail=str(steward_authorization)))

    personnel_path = base / "data" / "registry" / "personnel.json"
    personnel = _read_json_list(personnel_path)
    normalized_name = name.strip().casefold()
    duplicates = [entry for entry in personnel if str(entry.get("display_name", "")).strip().casefold() == normalized_name]
    if duplicates:
        result["error"] = f"personnel entry already exists for {name}"
        result["steps"].append(_step("protect_existing_personnel", "failed", result["error"]))
        return result
    next_id = max(int(entry.get("employee_id", -1)) for entry in personnel) + 1 if personnel else 1
    mailbox_id = next_id
    if any(int(entry.get("mailbox_id", -999999)) == mailbox_id for entry in personnel if entry.get("mailbox_id") is not None):
        result["error"] = f"mailbox {mailbox_id} is already assigned in personnel registry"
        result["steps"].append(_step("protect_existing_mailbox", "failed", result["error"]))
        return result
    result["employee_id"] = next_id
    result["mailbox_id"] = mailbox_id
    result["steps"].append(_step("determine_next_employee_id", detail=f"Employee ID {next_id}; mailbox {mailbox_id}"))

    mailbox_root = base / "collaboration" / "mailboxes" / mailbox_directory_name(mailbox_id)
    if mailbox_root.exists() and any(mailbox_root.iterdir()):
        result["error"] = f"mailbox directory already exists and is not empty: {_relative(base, mailbox_root)}"
        result["steps"].append(_step("protect_existing_mailbox_directory", "failed", result["error"]))
        return result

    msg = {
        "id": _message_id(next_id, name),
        "created_at": _now(),
        "created_by": "Helen",
        "source": "Human Resources",
        "destination": f"mailbox.{mailbox_id}",
        "destination_employee_id": next_id,
        "destination_mailbox_id": mailbox_id,
        "status": "open",
        "requires_ack": True,
        "ack_status": "pending",
        "related_artifact": "docs/operations/Onboarding_Checklist_v1.md",
        "payload": {
            "title": f"Employee onboarding packet for {name.strip()}",
            "summary": f"HR onboarding packet for {role.strip()} in {office.strip()}.",
            "package_type": package_type,
            "classification": classification.strip(),
            "steward_authorization_evidence": str(steward_authorization),
            "artifact_refs": [],
            "historical_memoranda": [],
        },
    }
    message_path = base / "collaboration" / "messages" / f"{msg['id']}.json"
    if message_path.exists():
        result["error"] = f"onboarding packet already exists: {_relative(base, message_path)}"
        result["steps"].append(_step("protect_existing_onboarding_packet", "failed", result["error"]))
        return result

    entry = {
        "employee_id": next_id,
        "display_name": name.strip(),
        "current_title": role.strip(),
        "current_office": office.strip(),
        "department": department.strip(),
        "mailbox_id": mailbox_id,
        "security_clearance": classification.strip(),
        "status": "onboarding",
        "notes": f"Created by Helen HR onboarding orchestrator with Steward authorization evidence: {steward_authorization}",
    }
    personnel.append(entry)
    if not dry_run:
        _write_json(personnel_path, sorted(personnel, key=lambda item: int(item.get("employee_id", 0))))
    result["steps"].append(_step("create_personnel_registry_entry", artifact=_relative(base, personnel_path)))
    if not dry_run:
        created_dirs = ensure_mailbox_directories(base)
    else:
        created_dirs = [f"collaboration/mailboxes/{mailbox_directory_name(mailbox_id)}/{child}" for child in ("inbox", "sent", "archive")]
    result["steps"].append(_step("create_mailbox_folders", detail=f"Ensured {len(created_dirs)} mailbox folders"))

    docs = REQUIRED_DOCUMENTS[package_type]
    if package_type == "chief_architect":
        docs = docs + HISTORICAL_MEMORANDA
    existing_docs = [path for path in docs if (base / path).exists()]
    missing_docs = [path for path in docs if not (base / path).exists()]
    if missing_docs:
        result["warnings"].extend(f"missing onboarding document: {path}" for path in missing_docs)
    result["steps"].append(_step("identify_required_documents", detail=f"{len(existing_docs)} available; {len(missing_docs)} missing"))

    msg["payload"]["artifact_refs"] = existing_docs
    msg["payload"]["historical_memoranda"] = [path for path in HISTORICAL_MEMORANDA if path in existing_docs]
    if not dry_run:
        _write_json(message_path, msg)
    result["artifacts"]["onboarding_packet"] = _relative(base, message_path)
    result["steps"].append(_step("deliver_onboarding_packet", artifact=_relative(base, message_path)))

    if not dry_run:
        index = generate_mailbox_index(base)
        result["steps"].append(_step("update_mailbox_index", artifact="collaboration/mailboxes/index.json"))
    else:
        index = {"messages": []}
        result["steps"].append(_step("update_mailbox_index", "skipped", "dry run"))

    resolution = resolve_personnel_identity(f"employee.{next_id}", base) if not dry_run else {"resolved": True, "warnings": []}
    mailbox_visible = any(item.get("destination_mailbox_id") == mailbox_id and item.get("message_id") == msg["id"] for item in index.get("messages", [])) if not dry_run else True
    result["resolver_confirmation"] = resolution
    result["mailbox_index_visible"] = mailbox_visible
    status = "completed" if resolution.get("resolved") and mailbox_visible else "failed"
    result["steps"].append(_step("verify_resolver_and_mailbox_visibility", status, f"resolver={resolution.get('resolved')} mailbox_index={mailbox_visible}"))
    result["ok"] = status == "completed"

    run_path = base / "operations" / "hr" / "onboarding_runs" / f"employee_{next_id:04d}_{_message_id(next_id, name)}.json"
    latest_path = base / "runtime" / "hr" / "onboarding_result.json"
    result["artifacts"]["run_result"] = _relative(base, run_path)
    result["artifacts"]["latest_result"] = _relative(base, latest_path)
    result["steps"].append(_step("produce_auditable_result", artifact=_relative(base, run_path)))
    if not dry_run:
        _write_json(run_path, result)
        _write_json(latest_path, result)
    return result


def format_onboarding_result(result):
    lines = ["Helen Employee Onboarding Orchestrator", f"OK: {result.get('ok')}"]
    if result.get("employee_id") is not None:
        lines.append(f"Employee ID: {result['employee_id']}")
        lines.append(f"Mailbox ID: {mailbox_directory_name(result['mailbox_id'])}")
    if result.get("error"):
        lines.append(f"Error: {result['error']}")
    for step in result.get("steps", []):
        detail = f" — {step.get('detail')}" if step.get("detail") else ""
        lines.append(f"{step['status']}: {step['step']}{detail}")
    for artifact in result.get("artifacts", {}).values():
        lines.append(f"Artifact: {artifact}")
    for warning in result.get("warnings", []):
        lines.append(f"Warning: {warning}")
    return "\n".join(lines)
