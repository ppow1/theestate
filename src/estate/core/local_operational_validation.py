"""Local operational validation runner for generated Estate projections.

This runner coordinates existing read/projection generators after pulls, merges,
or completed work packages. It writes only generated validation reports and never
edits authoritative ledgers or devlogs.
"""

from __future__ import annotations

import json
import subprocess
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from estate.core.alfred import alfred_briefing
from estate.core.capability_lifecycle import generate_capability_lifecycle_report
from estate.core.check_updates import generate_check_updates
from estate.core.collaboration_ops import run_routing_engine, watch_worker_inboxes
from estate.core.daily_board_integration import generate_daily_board_integration
from estate.core.dependency_graph import generate_dependency_graph
from estate.core.mailbox_index import generate_mailbox_index, mailbox_index_summary
from estate.core.operational_validation import generate_operational_validation_report
from estate.core.paths import ESTATE_ROOT

JSON_OUTPUT = "runtime/validation/local_operational_validation_run.json"
MARKDOWN_OUTPUT = "operations/validation/local_operational_validation_run.md"
AUTHORITATIVE_SOURCES = [
    "data/registry/**/*.json",
    "collaboration/messages/*.json",
    "collaboration/work_packages/**/*.md",
    "collaboration/work_packages/completions/*.json",
    "operations/boards/*.md",
    "docs/**/*.md",
]
GENERATED_PROJECTIONS = [
    "collaboration/mailboxes/index.json",
    "collaboration/status/worker_inbox_summary.json",
    "runtime/collaboration/routing/latest.json",
    "runtime/updates/check_updates_latest.json",
    "operations/updates/check_updates_latest.md",
    "operations/alfred/operational_briefing.md",
    "runtime/operations/daily_board_integration.json",
    "operations/boards/daily_board_integration.md",
    "runtime/capabilities/capability_lifecycle_report.json",
    "runtime/dependencies/dependency_graph.json",
    "runtime/validation/operational_validation_report.json",
    "operations/validation/operational_validation_report.md",
    JSON_OUTPUT,
    MARKDOWN_OUTPUT,
]
OPTIONAL_ARTIFACTS = [
    "collaboration/messages",
    "collaboration/work_packages/completions",
    "operations/boards/daily_board.md",
    "operations/boards/active_work.md",
    "operations/boards/parking_lot.md",
]


def estate_root(root: str | Path | None = None) -> Path:
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.is_absolute() and ESTATE_ROOT.exists() else Path.cwd())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _git_value(root: Path, *args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip() or None
    except Exception:
        return None


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _step(name: str, description: str, func: Callable[[], Any], optional: bool = False) -> dict[str, Any]:
    try:
        result = func()
        warnings = []
        if isinstance(result, dict):
            warnings = result.get("warnings") or result.get("errors") or []
        return {"name": name, "description": description, "status": "ok", "optional": optional, "warning_count": len(warnings), "warnings": warnings, "summary": _summarize_result(result)}
    except Exception as exc:
        return {"name": name, "description": description, "status": "warning" if optional else "failed", "optional": optional, "error": {"type": exc.__class__.__name__, "message": str(exc), "traceback": traceback.format_exc(limit=5)}}


def _summarize_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {"type": type(result).__name__}
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    keys = ["version", "generated_at", "open_messages", "worker_count", "message_count"]
    compact = {k: result[k] for k in keys if k in result}
    compact.update(summary)
    return compact


def _missing_optional_artifacts(root: Path) -> list[dict[str, str]]:
    warnings = []
    for rel in OPTIONAL_ARTIFACTS:
        if not (root / rel).exists():
            warnings.append({"type": "missing_optional_artifact", "path": rel, "message": "Optional local validation input is unavailable."})
    return warnings


def generate_local_operational_validation_run(root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    root = estate_root(root)
    before_ledger = (root / "estate_ledger" / "ledger.md").read_text(encoding="utf-8") if (root / "estate_ledger" / "ledger.md").exists() else None
    before_devlog = (root / "development" / "devlog.md").read_text(encoding="utf-8") if (root / "development" / "devlog.md").exists() else None

    steps = [
        _step("mailbox_index", "Regenerate mailbox index and worker mailbox surfaces.", lambda: {"summary": mailbox_index_summary(generate_mailbox_index(root))}),
        _step("routing_decisions", "Regenerate collaboration routing decisions.", lambda: run_routing_engine(root)),
        _step("worker_inbox_summary", "Regenerate worker inbox summaries.", lambda: watch_worker_inboxes(root)),
        _step("check_updates", "Regenerate Check for Updates briefing.", lambda: generate_check_updates(actor="steward", root=root)),
        _step("alfred_operational_briefing", "Regenerate Alfred operational briefing.", lambda: alfred_briefing(root=root)),
        _step("daily_board_integration", "Regenerate Operations/Daily Board integration.", lambda: generate_daily_board_integration(root)),
        _step("capability_lifecycle", "Regenerate capability lifecycle report.", lambda: generate_capability_lifecycle_report(root)),
        _step("dependency_graph", "Regenerate dependency graph.", lambda: generate_dependency_graph(root)),
        _step("operational_validation", "Regenerate operational validation report.", lambda: generate_operational_validation_report(root)),
    ]
    warnings = _missing_optional_artifacts(root)
    for step in steps:
        warnings.extend(step.get("warnings") or [])
        if step["status"] == "failed":
            warnings.append({"type": "failed_sub_step", "step": step["name"], "message": step.get("error", {}).get("message", "Sub-step failed.")})

    ledger_unchanged = before_ledger == ((root / "estate_ledger" / "ledger.md").read_text(encoding="utf-8") if (root / "estate_ledger" / "ledger.md").exists() else None)
    devlog_unchanged = before_devlog == ((root / "development" / "devlog.md").read_text(encoding="utf-8") if (root / "development" / "devlog.md").exists() else None)
    report = {
        "version": 1,
        "generated_at": _now(),
        "repository": {"branch": _git_value(root, "rev-parse", "--abbrev-ref", "HEAD"), "commit": _git_value(root, "rev-parse", "HEAD")},
        "policy": {"authoritative_sources": AUTHORITATIVE_SOURCES, "generated_projections": GENERATED_PROJECTIONS, "ledger_unchanged": ledger_unchanged, "devlog_unchanged": devlog_unchanged},
        "summary": {"step_count": len(steps), "failed_steps": sum(1 for s in steps if s["status"] == "failed"), "warning_count": len(warnings), "ok": all(s["status"] != "failed" for s in steps) and ledger_unchanged and devlog_unchanged},
        "steps": steps,
        "warnings": warnings,
        "outputs": {"json": JSON_OUTPUT, "markdown": MARKDOWN_OUTPUT},
    }
    if write:
        _write_json(root / JSON_OUTPUT, report)
        md = root / MARKDOWN_OUTPUT
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(format_local_operational_validation_markdown(report) + "\n", encoding="utf-8")
    return report


def format_local_operational_validation_markdown(report: dict[str, Any]) -> str:
    lines = ["# Local Operational Validation Run", "", f"Generated: {report.get('generated_at')}", "", "## Summary"]
    for k, v in report.get("summary", {}).items():
        lines.append(f"- {k.replace('_', ' ').title()}: {v}")
    lines.extend(["", "## Source Boundary", "", "### Authoritative Sources"])
    lines += [f"- {item}" for item in report.get("policy", {}).get("authoritative_sources", [])]
    lines.extend(["", "### Generated Projections"])
    lines += [f"- {item}" for item in report.get("policy", {}).get("generated_projections", [])]
    lines.extend(["", "## Steps"])
    for step in report.get("steps", []):
        lines.append(f"- {step.get('name')}: {step.get('status')} ({step.get('description')})")
        if step.get("error"):
            lines.append(f"  - Error: {step['error'].get('type')}: {step['error'].get('message')}")
    lines.extend(["", "## Warnings"])
    lines += [f"- {w.get('type')}: {w.get('path') or w.get('step', '')} — {w.get('message', '')}" for w in report.get("warnings", [])] or ["- No warnings."]
    return "\n".join(lines)


def format_local_operational_validation_summary(report: dict[str, Any]) -> str:
    s = report.get("summary", {})
    return "\n".join(["Local Operational Validation Run", f"Steps: {s.get('step_count', 0)}", f"Failed steps: {s.get('failed_steps', 0)}", f"Warnings: {s.get('warning_count', 0)}", f"OK: {s.get('ok')}"])
