"""Operations Board runtime aggregation for The Estate.

The board is an operational view generated from existing artifacts. It does not
create or redefine governance, lifecycle states, offices, or communication bus
semantics.
"""

import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

VALID_LIFECYCLE_STATES = {
    "Designed",
    "Implemented",
    "Operationally Validated",
    "Institutionalized",
}

OPTIONAL_INPUTS = [
    "collaboration/status/worker_inbox_summary.json",
    "runtime/collaboration/routing/latest.json",
    "runtime/audit/latest.json",
    "data/registry/capabilities.json",
    "data/registry/services.json",
    "data/registry/residents.json",
]

GLOB_INPUTS = [
    "runtime/collaboration/worker_inboxes/*.json",
    "collaboration/audit/results/*.json",
]


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def estate_root(root=None):
    if root is not None:
        return Path(root)
    if ESTATE_ROOT.exists():
        return ESTATE_ROOT
    return Path.cwd()


def _rel(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path, root, warnings):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({
            "type": "malformed_json",
            "path": _rel(path, root),
            "message": str(exc),
        })
        return None


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _git_value(root, *args):
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("items", "capabilities", "services", "residents", "providers", "results"):
            if isinstance(value.get(key), list):
                return value[key]
    return []


def _count_status(items):
    counts = Counter()
    for item in items:
        if isinstance(item, dict):
            counts[str(item.get("status") or item.get("state") or "unknown")] += 1
        else:
            counts["unknown"] += 1
    return dict(sorted(counts.items()))


def _collect_collaboration(root, artifacts, warnings):
    summary = artifacts.get("collaboration/status/worker_inbox_summary.json") or {}
    routing = artifacts.get("runtime/collaboration/routing/latest.json") or {}
    inboxes = artifacts.get("runtime/collaboration/worker_inboxes/*.json", [])

    workers = []
    for worker in summary.get("workers", []) if isinstance(summary, dict) else []:
        messages = worker.get("messages", []) if isinstance(worker, dict) else []
        invalid = [m for m in messages if isinstance(m, dict) and m.get("valid") is False]
        workers.append({
            "worker": worker.get("worker"),
            "message_count": worker.get("message_count", len(messages)),
            "pending_messages": len(messages),
            "invalid_messages": len(invalid),
        })

    # If only per-worker inbox files exist, use them as a fallback.
    known = {w.get("worker") for w in workers}
    for inbox in inboxes:
        if not isinstance(inbox, dict):
            continue
        worker_name = inbox.get("worker")
        if worker_name in known:
            continue
        messages = inbox.get("messages", []) if isinstance(inbox.get("messages", []), list) else []
        workers.append({
            "worker": worker_name,
            "message_count": len(messages),
            "pending_messages": len(messages),
            "invalid_messages": len([m for m in messages if isinstance(m, dict) and m.get("valid") is False]),
        })

    routing_errors = routing.get("errors", []) if isinstance(routing, dict) else []
    return {
        "open_message_count": routing.get("open_messages") if isinstance(routing, dict) else None,
        "routed_message_count": len(routing.get("decisions", [])) if isinstance(routing, dict) else None,
        "worker_inbox_count": len(inboxes),
        "worker_count": len(workers),
        "workers": workers,
        "routing_errors": routing_errors,
    }


def _collect_audit(artifacts):
    latest = artifacts.get("runtime/audit/latest.json") or {}
    result_files = artifacts.get("collaboration/audit/results/*.json", [])
    results = []
    for item in result_files:
        if isinstance(item, list):
            results.extend(item)
        elif isinstance(item, dict):
            results.append(item)
    failed = []
    malformed = []
    for item in results:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or item.get("result") or "").lower()
        if "fail" in status or status == "failed":
            failed.append(item)
        if "malformed" in json.dumps(item).lower():
            malformed.append(item)
    return {
        "latest_summary": latest.get("summary", latest) if isinstance(latest, dict) else {},
        "result_count": len(results),
        "result_counts_by_status": _count_status(results),
        "failed_audit_requests": len(failed),
        "malformed_audit_request_results": len(malformed),
    }


def _collect_capabilities(artifacts, warnings):
    capabilities = _as_list(artifacts.get("data/registry/capabilities.json"))
    rows = []
    for cap in capabilities:
        if not isinstance(cap, dict):
            continue
        lifecycle = cap.get("lifecycle_state") or cap.get("lifecycle")
        if lifecycle is None:
            warnings.append({
                "type": "missing_lifecycle_state",
                "path": "data/registry/capabilities.json",
                "message": f"Capability {cap.get('id') or cap.get('name')} has no lifecycle_state field.",
            })
        elif lifecycle not in VALID_LIFECYCLE_STATES:
            warnings.append({
                "type": "invalid_lifecycle_state",
                "path": "data/registry/capabilities.json",
                "message": f"Capability {cap.get('id') or cap.get('name')} uses non-standard lifecycle state: {lifecycle}.",
            })
        rows.append({
            "id": cap.get("id"),
            "name": cap.get("name"),
            "status": cap.get("status"),
            "lifecycle_state": lifecycle,
        })
    return {"count": len(rows), "items": rows, "lifecycle_counts": _count_status([{"status": r.get("lifecycle_state") or "missing"} for r in rows])}


def _collect_services_residents(artifacts):
    services = _as_list(artifacts.get("data/registry/services.json"))
    residents = _as_list(artifacts.get("data/registry/residents.json"))
    providers = _as_list(artifacts.get("data/registry/providers.json")) if "data/registry/providers.json" in artifacts else []
    return {
        "service_count": len(services),
        "resident_count": len(residents),
        "provider_count": len(providers),
        "service_status_counts": _count_status(services),
        "resident_status_counts": _count_status(residents),
        "provider_status_counts": _count_status(providers),
    }


def generate_operations_board(root=None, write=True):
    root = estate_root(root)
    warnings = []
    inputs = {"used": [], "unavailable": []}
    artifacts = {}

    for rel in OPTIONAL_INPUTS + ["data/registry/providers.json"]:
        path = root / rel
        if path.exists():
            data = _read_json(path, root, warnings)
            if data is not None:
                artifacts[rel] = data
                inputs["used"].append(rel)
        else:
            inputs["unavailable"].append(rel)
            warnings.append({"type": "missing_optional_artifact", "path": rel, "message": "Optional input artifact is unavailable."})

    for pattern in GLOB_INPUTS:
        found = sorted(root.glob(pattern))
        if not found:
            inputs["unavailable"].append(pattern)
            warnings.append({"type": "missing_optional_artifact", "path": pattern, "message": "Optional input artifact is unavailable."})
            artifacts[pattern] = []
            continue
        artifacts[pattern] = []
        for path in found:
            data = _read_json(path, root, warnings)
            if data is not None:
                artifacts[pattern].append(data)
                inputs["used"].append(_rel(path, root))

    collaboration = _collect_collaboration(root, artifacts, warnings)
    audit = _collect_audit(artifacts)
    capabilities = _collect_capabilities(artifacts, warnings)
    services_residents = _collect_services_residents(artifacts)

    warning_count = len(warnings)
    missing_count = len([w for w in warnings if w.get("type") == "missing_optional_artifact"])
    overall_status = "warning" if warning_count else "ok"
    snapshot = {
        "version": 1,
        "generated_at": _now(),
        "repository": {"branch": _git_value(root, "rev-parse", "--abbrev-ref", "HEAD"), "commit": _git_value(root, "rev-parse", "HEAD")},
        "summary": {"overall_status": overall_status, "missing_artifact_count": missing_count, "warning_count": warning_count},
        "inputs": inputs,
        "collaboration": collaboration,
        "workers": {"known_workers": collaboration["workers"]},
        "audit": audit,
        "capabilities": capabilities,
        "services_and_residents": services_residents,
        "warnings": warnings,
    }
    markdown = format_operations_board_markdown(snapshot)
    if write:
        _write_json(root / "runtime" / "operations" / "operations_board.json", snapshot)
        md_path = root / "operations" / "board" / "latest.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown + "\n", encoding="utf-8")
    return snapshot


def format_operations_board_summary(snapshot):
    s = snapshot.get("summary", {})
    lines = [
        "Estate Operations Board",
        f"Generated: {snapshot.get('generated_at')}",
        f"Status: {s.get('overall_status')}",
        f"Missing artifacts: {s.get('missing_artifact_count', 0)}",
        f"Warnings: {s.get('warning_count', 0)}",
        f"Workers: {snapshot.get('collaboration', {}).get('worker_count', 0)}",
    ]
    return "\n".join(lines)


def format_operations_board_markdown(snapshot):
    repo = snapshot.get("repository", {})
    summary = snapshot.get("summary", {})
    collab = snapshot.get("collaboration", {})
    audit = snapshot.get("audit", {})
    caps = snapshot.get("capabilities", {})
    sr = snapshot.get("services_and_residents", {})
    lines = [
        "# Estate Operations Board",
        "",
        f"Generated: {snapshot.get('generated_at')}",
        "",
        "## Summary",
        f"- Repository branch: {repo.get('branch') or 'unavailable'}",
        f"- Current commit: {repo.get('commit') or 'unavailable'}",
        f"- Overall status: {summary.get('overall_status')}",
        f"- Missing artifact count: {summary.get('missing_artifact_count', 0)}",
        f"- Warning count: {summary.get('warning_count', 0)}",
        "",
        "## Collaboration",
        f"- Open messages: {collab.get('open_message_count') if collab.get('open_message_count') is not None else 'unavailable'}",
        f"- Routed messages: {collab.get('routed_message_count') if collab.get('routed_message_count') is not None else 'unavailable'}",
        f"- Worker inbox files: {collab.get('worker_inbox_count', 0)}",
        f"- Routing errors: {len(collab.get('routing_errors', []))}",
        "",
        "## Workers",
    ]
    workers = snapshot.get("workers", {}).get("known_workers", [])
    if workers:
        for worker in workers:
            lines.append(f"- {worker.get('worker')}: {worker.get('message_count', 0)} message(s), {worker.get('pending_messages', 0)} pending, {worker.get('invalid_messages', 0)} invalid")
    else:
        lines.append("- No worker status artifacts available.")
    lines.extend([
        "",
        "## Audit",
        f"- Audit result files: {audit.get('result_count', 0)}",
        f"- Failed audit requests: {audit.get('failed_audit_requests', 0)}",
        f"- Malformed audit request results: {audit.get('malformed_audit_request_results', 0)}",
        f"- Result counts by status: {audit.get('result_counts_by_status', {})}",
        "",
        "## Capabilities",
        f"- Capability count: {caps.get('count', 0)}",
        f"- Lifecycle counts: {caps.get('lifecycle_counts', {})}",
    ])
    for cap in caps.get("items", []):
        lines.append(f"- {cap.get('id')}: {cap.get('name')} — status={cap.get('status') or 'unavailable'}, lifecycle={cap.get('lifecycle_state') or 'missing'}")
    lines.extend([
        "",
        "## Services and Residents",
        f"- Services: {sr.get('service_count', 0)}",
        f"- Residents: {sr.get('resident_count', 0)}",
        f"- Providers: {sr.get('provider_count', 0)}",
        f"- Service status counts: {sr.get('service_status_counts', {})}",
        f"- Resident status counts: {sr.get('resident_status_counts', {})}",
        f"- Provider status counts: {sr.get('provider_status_counts', {})}",
        "",
        "## Warnings",
    ])
    if snapshot.get("warnings"):
        for warning in snapshot["warnings"]:
            lines.append(f"- {warning.get('type')}: {warning.get('path')} — {warning.get('message')}")
    else:
        lines.append("- No warnings.")
    return "\n".join(lines)
