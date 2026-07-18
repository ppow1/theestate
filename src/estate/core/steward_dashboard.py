"""Steward dashboard runtime view for The Estate.

The Steward dashboard is a human-facing runtime summary generated from existing
operational artifacts. It does not create governance, lifecycle states, or new
operational authority; it summarizes what existing Estate reports already know.
"""

import json
from copy import deepcopy
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

OPERATIONAL_SIGNAL_STATES = {"ready", "active", "blocked", "degraded", "failed", "protected", "stale", "indeterminate"}
SIGNAL_PRIORITY = {"failed": 100, "protected": 95, "blocked": 90, "indeterminate": 85, "stale": 80, "degraded": 70, "active": 50, "ready": 30}

OPTIONAL_JSON_INPUTS = [
    "runtime/operations/operations_board.json",
    "runtime/capabilities/capability_lifecycle_report.json",
    "collaboration/status/worker_inbox_summary.json",
    "runtime/audit/latest.json",
]

OPTIONAL_TEXT_INPUTS = [
    "operations/board/latest.md",
]

GLOB_JSON_INPUTS = [
    "collaboration/audit/results/*.json",
]


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def estate_root(root=None):
    if root is not None:
        return Path(root)
    cwd = Path.cwd()
    if (cwd / "runtime" / "operations" / "operations_board.json").is_file():
        return cwd
    if ESTATE_ROOT.exists():
        return ESTATE_ROOT
    return cwd


def _rel(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _read_json(path, root, warnings):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warnings.append({"type": "malformed_json", "path": _rel(path, root), "message": str(exc)})
        return None


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_inputs(root):
    warnings = []
    inputs = {"used": [], "unavailable": []}
    artifacts = {}

    for rel in OPTIONAL_JSON_INPUTS:
        path = root / rel
        if path.exists():
            data = _read_json(path, root, warnings)
            if data is not None:
                artifacts[rel] = data
                inputs["used"].append(rel)
        else:
            inputs["unavailable"].append(rel)
            warnings.append({"type": "missing_optional_artifact", "path": rel, "message": "Optional dashboard input artifact is unavailable."})

    for rel in OPTIONAL_TEXT_INPUTS:
        path = root / rel
        if path.exists():
            artifacts[rel] = path.read_text(encoding="utf-8")
            inputs["used"].append(rel)
        else:
            inputs["unavailable"].append(rel)
            warnings.append({"type": "missing_optional_artifact", "path": rel, "message": "Optional dashboard input artifact is unavailable."})

    for pattern in GLOB_JSON_INPUTS:
        found = sorted(root.glob(pattern))
        artifacts[pattern] = []
        if not found:
            inputs["unavailable"].append(pattern)
            warnings.append({"type": "missing_optional_artifact", "path": pattern, "message": "Optional dashboard input artifact is unavailable."})
            continue
        for path in found:
            data = _read_json(path, root, warnings)
            if data is not None:
                artifacts[pattern].append(data)
                inputs["used"].append(_rel(path, root))

    return artifacts, inputs, warnings


def _status_counts(items):
    counts = Counter()
    for item in items or []:
        if isinstance(item, dict):
            counts[str(item.get("status") or item.get("state") or item.get("result") or "unknown")] += 1
    return dict(sorted(counts.items()))


def _work_items_from_board(board):
    items = []
    for cap in board.get("capabilities", {}).get("items", []) if isinstance(board, dict) else []:
        status = str(cap.get("status") or "unknown")
        lifecycle = cap.get("lifecycle_state") or "missing"
        item = {"id": cap.get("id"), "title": cap.get("name"), "status": status, "lifecycle_state": lifecycle, "source": "operations_board.capabilities"}
        items.append(item)
    return items


def _categorize_work(items):
    active_terms = {"active", "implemented", "operationally validated", "institutionalized", "in_progress", "in progress", "open"}
    blocked_terms = {"blocked", "failed", "error"}
    review_terms = {"review", "review-pending", "review pending", "pending", "validation pending"}
    active, blocked, review = [], [], []
    for item in items:
        joined = " ".join(str(item.get(k) or "") for k in ("status", "lifecycle_state", "title")).lower()
        if any(term in joined for term in blocked_terms):
            blocked.append(item)
        elif any(term in joined for term in review_terms):
            review.append(item)
        elif any(term in joined for term in active_terms):
            active.append(item)
    return {"active": active, "blocked": blocked, "review_pending": review}


def _audit_status(artifacts):
    latest = artifacts.get("runtime/audit/latest.json") or {}
    board_audit = (artifacts.get("runtime/operations/operations_board.json") or {}).get("audit", {})
    results = artifacts.get("collaboration/audit/results/*.json", [])
    failures = [r for r in results if isinstance(r, dict) and "fail" in str(r.get("status") or r.get("result") or "").lower()]
    return {
        "latest_summary": latest.get("summary", latest) if isinstance(latest, dict) else {},
        "board_summary": board_audit,
        "audit_result_count": len(results),
        "audit_result_counts_by_status": _status_counts(results),
        "failed_audit_result_count": len(failures),
    }


def _worker_inbox_status(artifacts):
    inbox = artifacts.get("collaboration/status/worker_inbox_summary.json") or {}
    board = artifacts.get("runtime/operations/operations_board.json") or {}
    workers = inbox.get("workers") if isinstance(inbox, dict) else None
    if not workers:
        workers = board.get("workers", {}).get("known_workers", []) if isinstance(board, dict) else []
    return {
        "worker_count": inbox.get("worker_count", len(workers)) if isinstance(inbox, dict) else len(workers),
        "message_count": inbox.get("message_count") if isinstance(inbox, dict) else None,
        "workers": workers or [],
    }


def _capability_lifecycle_status(artifacts):
    report = artifacts.get("runtime/capabilities/capability_lifecycle_report.json") or {}
    board_caps = (artifacts.get("runtime/operations/operations_board.json") or {}).get("capabilities", {})
    summary = report.get("summary", {}) if isinstance(report, dict) else {}
    return {
        "summary": summary or {"capability_count": board_caps.get("count", 0), "counts_by_lifecycle_state": board_caps.get("lifecycle_counts", {})},
        "candidates": report.get("candidates", {}) if isinstance(report, dict) else {},
    }


def generate_steward_dashboard(root=None, write=True):
    root = estate_root(root)
    artifacts, inputs, warnings = _load_inputs(root)
    board = artifacts.get("runtime/operations/operations_board.json") or {}
    work_items = _work_items_from_board(board)
    work = _categorize_work(work_items)
    audit = _audit_status(artifacts)
    worker_inbox = _worker_inbox_status(artifacts)
    lifecycle = _capability_lifecycle_status(artifacts)

    steward_warnings = list(warnings)
    if audit["failed_audit_result_count"]:
        steward_warnings.append({"type": "audit_failure", "path": "collaboration/audit/results/*.json", "message": "One or more audit results indicate failure."})
    if work["blocked"]:
        steward_warnings.append({"type": "blocked_work", "path": "runtime/operations/operations_board.json", "message": "Blocked work is present in the Operations Board summary."})

    no_action = []
    if not work["blocked"]:
        no_action.append("No blocked work found in available Operations Board data.")
    if audit["failed_audit_result_count"] == 0:
        no_action.append("No failed audit result artifacts found.")

    dashboard = {
        "version": 1,
        "generated_at": _now(),
        "summary": {
            "overall_status": "attention" if steward_warnings else "ok",
            "source": "Existing Estate operational artifacts",
            "operations_board_available": bool(board),
            "warning_count": len(steward_warnings),
        },
        "current_operational_summary": {
            "operations_board_summary": board.get("summary", {}) if isinstance(board, dict) else {},
            "operations_board_markdown_available": "operations/board/latest.md" in artifacts,
        },
        "work": work,
        "audit_status": audit,
        "worker_inbox_status": worker_inbox,
        "capability_lifecycle_summary": lifecycle,
        "warnings_requiring_steward_attention": steward_warnings,
        "items_not_requiring_steward_action": no_action,
        "inputs": inputs,
    }

    if write:
        _write_json(root / "runtime" / "steward" / "dashboard.json", dashboard)
        md_path = root / "operations" / "steward" / "dashboard.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(format_steward_dashboard_markdown(dashboard) + "\n", encoding="utf-8")
    return dashboard


def _md_counted_items(items):
    if not items:
        return "- None known from available artifacts."
    return "\n".join(f"- {i.get('id') or 'unknown'}: {i.get('title') or 'Untitled'} — status={i.get('status')}, lifecycle={i.get('lifecycle_state')}" for i in items)


def format_steward_dashboard_summary(dashboard):
    s = dashboard.get("summary", {})
    return "\n".join([
        "Estate Steward Dashboard",
        f"Generated: {dashboard.get('generated_at')}",
        f"Status: {s.get('overall_status')}",
        f"Operations Board available: {s.get('operations_board_available')}",
        f"Warnings requiring Steward attention: {s.get('warning_count', 0)}",
    ])


def format_steward_dashboard_markdown(dashboard):
    s = dashboard.get("summary", {})
    work = dashboard.get("work", {})
    audit = dashboard.get("audit_status", {})
    inbox = dashboard.get("worker_inbox_status", {})
    lifecycle = dashboard.get("capability_lifecycle_summary", {})
    lines = [
        "# Estate Steward Dashboard",
        "",
        f"Generated: {dashboard.get('generated_at')}",
        "",
        "## Current Operational Summary",
        f"- Overall status: {s.get('overall_status')}",
        f"- Operations Board available: {s.get('operations_board_available')}",
        f"- Operations Board markdown available: {dashboard.get('current_operational_summary', {}).get('operations_board_markdown_available')}",
        f"- Warnings requiring Steward attention: {s.get('warning_count', 0)}",
        "",
        "## Active Work",
        _md_counted_items(work.get("active", [])),
        "",
        "## Blocked Work",
        _md_counted_items(work.get("blocked", [])),
        "",
        "## Review-Pending Work",
        _md_counted_items(work.get("review_pending", [])),
        "",
        "## Audit Status",
        f"- Audit result artifacts: {audit.get('audit_result_count', 0)}",
        f"- Failed audit result artifacts: {audit.get('failed_audit_result_count', 0)}",
        f"- Result counts by status: {audit.get('audit_result_counts_by_status', {})}",
        "",
        "## Worker Inbox Status",
        f"- Workers: {inbox.get('worker_count', 0)}",
        f"- Messages: {inbox.get('message_count') if inbox.get('message_count') is not None else 'unavailable'}",
        "",
        "## Capability Lifecycle Summary",
        f"- Summary: {lifecycle.get('summary', {})}",
        "",
        "## Warnings Requiring Steward Attention",
    ]
    warnings = dashboard.get("warnings_requiring_steward_attention", [])
    lines.extend(f"- {w.get('type')}: {w.get('path')} — {w.get('message')}" for w in warnings) if warnings else lines.append("- None")
    lines.extend(["", "## Items Not Requiring Steward Action"])
    no_action = dashboard.get("items_not_requiring_steward_action", [])
    lines.extend(f"- {item}" for item in no_action) if no_action else lines.append("- None recorded.")
    return "\n".join(lines)


def build_operational_visibility(signals, *, viewer, generated_at, max_items=100):
    """Build a bounded role-aware view over supplied canonical projections."""
    if not viewer.get("role") or not viewer.get("identity_evidence"):
        raise ValueError("viewer role and identity evidence are required")
    if max_items <= 0 or max_items > 500:
        raise ValueError("max_items must be between 1 and 500")
    allowed_classes = set(viewer.get("allowed_classifications") or ["Estate Internal"])
    items = []
    warnings = []
    for original in signals:
        signal = deepcopy(original)
        state = str(signal.get("state") or "indeterminate").lower()
        if state not in OPERATIONAL_SIGNAL_STATES:
            state = "indeterminate"
        refs = sorted({str(ref) for ref in signal.get("evidence_references") or [] if ref})
        local = list(signal.get("warnings") or [])
        if not signal.get("signal_id") or not refs:
            state = "indeterminate"
            local.append("status lacks stable identity or canonical drill-through evidence")
        classification = signal.get("classification") or "Estate Internal"
        redacted = classification not in allowed_classes
        protected = state == "protected" or bool(signal.get("protected_decision"))
        decision = None
        if protected:
            decision = {
                "requested_authority": signal.get("requested_authority"),
                "decision_question": None if redacted else signal.get("decision_question"),
                "evidence_references": refs,
            }
            if not decision["requested_authority"] or not signal.get("decision_question"):
                state = "indeterminate"
                local.append("protected decision lacks requested authority or decision question")
        controls = []
        for control in signal.get("controls") or []:
            if control.get("authorized") and viewer["role"] in (control.get("allowed_roles") or []):
                controls.append({"label": control.get("label"), "action_class": control.get("action_class"), "authority_reference": control.get("authority_reference")})
        item = {
            "signal_id": signal.get("signal_id"),
            "domain": signal.get("domain"),
            "title": "Restricted operational item" if redacted else signal.get("title"),
            "summary": "Details withheld by existing classification policy." if redacted else signal.get("summary"),
            "state": state,
            "freshness": signal.get("freshness") or "unknown",
            "confidence": signal.get("confidence") or "unknown",
            "observed_at": signal.get("observed_at"),
            "owner": signal.get("owner"),
            "evidence_references": refs,
            "warnings": sorted(set(local)),
            "protected_decision": decision,
            "controls": controls,
            "redacted": redacted,
            "classification": classification,
            "derived_view_only": True,
            "authorizes_action": False,
        }
        warnings.extend(f"{item['signal_id'] or '<missing>'}: {warning}" for warning in local)
        items.append(item)
    items.sort(key=lambda item: (-SIGNAL_PRIORITY[item["state"]], str(item["signal_id"])))
    truncated = len(items) > max_items
    items = items[:max_items]
    constraints = [item for item in items if item["state"] in {"failed", "protected", "blocked", "indeterminate", "stale", "degraded"}]
    return {
        "schema_version": "estate.steward-operational-visibility.v1",
        "generated_at": generated_at,
        "viewer": {"role": viewer["role"], "identity_evidence": list(viewer["identity_evidence"])},
        "information_architecture": ["highest_priority_constraints", "protected_decisions", "campaign_momentum", "health_and_readiness", "audit_and_evidence", "authorized_controls"],
        "highest_priority_constraints": constraints,
        "protected_decisions": [item for item in items if item["protected_decision"]],
        "signals": items,
        "summary": {"displayed": len(items), "truncated": truncated, "by_state": {state: sum(item["state"] == state for item in items) for state in sorted(OPERATIONAL_SIGNAL_STATES)}},
        "warnings": sorted(set(warnings + (["view truncated at configured performance bound"] if truncated else []))),
        "accessibility": {"status_not_color_only": True, "text_labels": True, "canonical_links_exposed": True},
        "derived_view_only": True,
        "authorizes_action": False,
    }
