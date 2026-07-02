"""Daily Board and Parking Lot integration reporting.

This module creates a read-only operational planning view from existing Estate
artifacts. It does not promote parking-lot items or change governance state.
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

BOARD_INPUTS = [
    "operations/boards/daily_board.md",
    "operations/boards/active_work.md",
    "operations/boards/parking_lot.md",
    "operations/alfred/operational_briefing.md",
]
WORK_PACKAGE_DIRS = {
    "pending": "collaboration/work_packages/pending",
    "open": "collaboration/work_packages/open",
    "claimed": "collaboration/work_packages/claimed",
    "completed": "collaboration/work_packages/completed",
    "completions": "collaboration/work_packages/completions",
}
READY_REVIEW_WORDS = ("stable", "ready", "validated", "operational", "formalized")
WAITING_WORDS = ("after", "post-", "future", "when ", "until", "mature", "reopened")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def estate_root(root=None):
    return Path(root) if root is not None else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def _rel(path, root):
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _git_value(root, *args):
    try:
        result = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
        return result.stdout.strip() or None
    except Exception:
        return None


def _warn_missing(warnings, rel):
    warnings.append({"type": "missing_optional_artifact", "path": rel, "message": "Optional input artifact is unavailable."})


def _table_rows(markdown):
    rows = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and all(re.fullmatch(r":?-{1,}:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def parse_markdown_tables(markdown):
    """Return table dictionaries from simple GitHub-style markdown tables."""
    tables = []
    current_heading = "Untitled"
    lines = markdown.splitlines()
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if line.startswith("## "):
            current_heading = line[3:].strip()
        if line.startswith("|") and idx + 1 < len(lines) and set(lines[idx + 1].strip().replace("|", "").replace(":", "").strip()) <= {"-"}:
            block = [lines[idx], lines[idx + 1]]
            idx += 2
            while idx < len(lines) and lines[idx].strip().startswith("|"):
                block.append(lines[idx])
                idx += 1
            rows = _table_rows("\n".join(block))
            if rows:
                headers = rows[0]
                items = [dict(zip(headers, row)) for row in rows[1:] if row and row[0] != "-"]
                tables.append({"heading": current_heading, "headers": headers, "items": items})
            continue
        idx += 1
    return tables


def parse_parking_lot(path, root, warnings):
    if not path.exists():
        _warn_missing(warnings, _rel(path, root))
        return []
    tables = parse_markdown_tables(path.read_text(encoding="utf-8"))
    for table in tables:
        if table["heading"] == "Parking Lot Items":
            return table["items"]
    warnings.append({"type": "missing_table", "path": _rel(path, root), "message": "Parking Lot Items table was not found."})
    return []


def promotion_condition_status(item):
    """Classify condition text without changing item state."""
    condition = (item.get("Promotion Condition") or "").strip()
    target = (item.get("Target Milestone") or "").strip()
    text = f"{target} {condition}".lower()
    if not condition or condition == "-":
        return {"classification": "needs_condition", "reason": "No promotion condition is recorded."}
    if any(word in text for word in READY_REVIEW_WORDS) and not any(word in text for word in ("after", "post-", "future", "reopened")):
        return {"classification": "ready_for_review", "reason": "Condition refers to current stability/readiness signals and should be reviewed by humans."}
    if any(word in text for word in WAITING_WORDS):
        return {"classification": "deferred", "reason": "Condition depends on a later milestone or maturity signal."}
    return {"classification": "watch", "reason": "Condition exists but readiness is not obvious from artifacts."}


def _work_package_title(path):
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                return line.lstrip("# ").strip()
    except UnicodeDecodeError:
        pass
    return path.stem


def collect_work_packages(root, warnings):
    result = {}
    for state, rel in WORK_PACKAGE_DIRS.items():
        directory = root / rel
        if not directory.exists():
            _warn_missing(warnings, rel)
            result[state] = []
            continue
        paths = sorted(p for p in directory.iterdir() if p.is_file() and p.name != ".gitkeep")
        items = []
        for path in paths:
            item = {"id": path.stem.split("_")[0], "title": _work_package_title(path), "path": _rel(path, root)}
            if path.suffix == ".json":
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    item.update({"codex_status": data.get("codex_status"), "ready_for_ca_review": data.get("ready_for_ca_review")})
                except Exception as exc:
                    warnings.append({"type": "malformed_json", "path": _rel(path, root), "message": str(exc)})
            items.append(item)
        result[state] = items
    return result


def _board_section(path, heading, root, warnings):
    if not path.exists():
        _warn_missing(warnings, _rel(path, root))
        return []
    for table in parse_markdown_tables(path.read_text(encoding="utf-8")):
        if table["heading"] == heading:
            return table["items"]
    return []


def generate_daily_board_integration(root=None, write=True):
    root = estate_root(root)
    warnings = []
    parking_items = parse_parking_lot(root / "operations/boards/parking_lot.md", root, warnings)
    enriched_parking = []
    for item in parking_items:
        status = promotion_condition_status(item)
        enriched = dict(item)
        enriched["promotion_review"] = status
        enriched_parking.append(enriched)
    ready = [item for item in enriched_parking if item["promotion_review"]["classification"] == "ready_for_review"]
    work_packages = collect_work_packages(root, warnings)
    active_work = _board_section(root / "operations/boards/active_work.md", "Active Work", root, warnings)
    daily_today = _board_section(root / "operations/boards/daily_board.md", "Today", root, warnings)
    blocked = _board_section(root / "operations/boards/daily_board.md", "Blocked", root, warnings) + _board_section(root / "operations/boards/active_work.md", "Waiting", root, warnings)
    completed_review = [i for i in work_packages.get("completions", []) if i.get("ready_for_ca_review")]
    snapshot = {
        "version": 1,
        "generated_at": _now(),
        "repository": {"branch": _git_value(root, "rev-parse", "--abbrev-ref", "HEAD"), "commit": _git_value(root, "rev-parse", "HEAD")},
        "summary": {"active_work_items": len(active_work), "daily_items": len(daily_today), "pending_work_packages": len(work_packages.get("pending", [])), "completed_awaiting_review": len(completed_review), "blocked_items": len(blocked), "parking_lot_items": len(enriched_parking), "parking_lot_ready_for_review": len(ready), "warning_count": len(warnings)},
        "active_work": active_work,
        "daily_today": daily_today,
        "pending_codex_queue": work_packages.get("pending", []),
        "completed_awaiting_review": completed_review,
        "blocked_work": blocked,
        "parking_lot": {"items": enriched_parking, "ready_for_review": ready},
        "recommended_next_actions": [
            "Review completed work packages marked ready_for_ca_review before starting additional queue items.",
            "Use pending_codex_queue for active execution planning; keep Parking Lot items deferred until intentionally selected.",
            "Human-review parking_lot.ready_for_review; do not auto-promote from this report.",
        ],
        "warnings": warnings,
    }
    if write:
        out_json = root / "runtime/operations/daily_board_integration.json"
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        out_md = root / "operations/boards/daily_board_integration.md"
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(format_daily_board_integration_markdown(snapshot) + "\n", encoding="utf-8")
    return snapshot


def format_daily_board_integration_markdown(snapshot):
    lines = ["# Daily Board Integration", "", f"Generated: {snapshot.get('generated_at')}", "", "## Summary"]
    for key, value in snapshot.get("summary", {}).items():
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    lines.extend(["", "## Active Work Package Summary"])
    for item in snapshot.get("active_work", []):
        lines.append(f"- {item.get('ID')}: {item.get('Effort')} — {item.get('Status')} — next: {item.get('Next Action')}")
    lines.extend(["", "## Pending Codex Queue"])
    for item in snapshot.get("pending_codex_queue", []):
        lines.append(f"- {item.get('id')}: {item.get('title')} ({item.get('path')})")
    lines.extend(["", "## Completed Awaiting Review/Validation"])
    for item in snapshot.get("completed_awaiting_review", []):
        lines.append(f"- {item.get('id')}: {item.get('title')} ({item.get('path')})")
    lines.extend(["", "## Blocked Work"])
    if snapshot.get("blocked_work"):
        for item in snapshot["blocked_work"]:
            lines.append("- " + "; ".join(f"{k}: {v}" for k, v in item.items()))
    else:
        lines.append("- No blocked work found in available board tables.")
    lines.extend(["", "## Parking Lot Promotion Conditions"])
    for item in snapshot.get("parking_lot", {}).get("items", []):
        review = item.get("promotion_review", {})
        lines.append(f"- {item.get('ID')}: {item.get('Idea')} — {review.get('classification')} — {item.get('Promotion Condition')}")
    lines.extend(["", "## Parking Lot Items Ready for Review"])
    ready = snapshot.get("parking_lot", {}).get("ready_for_review", [])
    if ready:
        for item in ready:
            lines.append(f"- {item.get('ID')}: {item.get('Idea')}")
    else:
        lines.append("- None identified. No items were promoted.")
    lines.extend(["", "## Recommended Next Actions"])
    for action in snapshot.get("recommended_next_actions", []):
        lines.append(f"- {action}")
    lines.extend(["", "## Warnings"])
    if snapshot.get("warnings"):
        for warning in snapshot["warnings"]:
            lines.append(f"- {warning.get('type')}: {warning.get('path')} — {warning.get('message')}")
    else:
        lines.append("- No warnings.")
    return "\n".join(lines)


def format_daily_board_integration_summary(snapshot):
    summary = snapshot.get("summary", {})
    return "\n".join([
        "Daily Board Integration",
        f"Generated: {snapshot.get('generated_at')}",
        f"Pending work packages: {summary.get('pending_work_packages', 0)}",
        f"Completed awaiting review: {summary.get('completed_awaiting_review', 0)}",
        f"Parking lot ready for review: {summary.get('parking_lot_ready_for_review', 0)}",
        f"Warnings: {summary.get('warning_count', 0)}",
    ])
