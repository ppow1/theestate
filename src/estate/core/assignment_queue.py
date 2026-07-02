"""Assignment queue generation for Estate work packages."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from estate.core.paths import ESTATE_ROOT

WORK_PACKAGE_DIRS = [
    "collaboration/work_packages/pending",
    "collaboration/work_packages/open",
    "collaboration/work_packages/claimed",
    "collaboration/work_packages/completed",
]

ID_RE = re.compile(r"(WP-(?:\d{4}|[A-Z]+-\d{3}))")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$")
FIELD_RE = re.compile(r"^\s*(?:[-*]\s*)?\*\*(mode|owner|state|status|next action|next_action|blockers?|blocked by|dependencies)\*\*\s*:?\s*(.*)$", re.I)
PLAIN_FIELD_RE = re.compile(r"^\s*(mode|owner|state|status|next action|next_action|blockers?|blocked by|dependencies)\s*:\s*(.+)$", re.I)
BULLET_RE = re.compile(r"^\s*[-*]\s+(?:\[[ xX]\]\s*)?(.+?)\s*$")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _rel(path, root):
    return str(path.relative_to(root)).replace("\\", "/")


def _split_values(text):
    text = (text or "").strip().strip(".").strip()
    if not text or text.lower() in {"none", "n/a", "na", "no", "not applicable"}:
        return []
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    return [part.strip().strip('"\'`') for part in re.split(r"[,;]", text) if part.strip()]


def _section_values(lines, heading_names):
    values = []
    names = {name.lower() for name in heading_names}
    for i, line in enumerate(lines):
        m = HEADING_RE.match(line)
        if not m or m.group(1).strip().lower() not in names:
            continue
        for body in lines[i + 1:]:
            if HEADING_RE.match(body):
                break
            b = BULLET_RE.match(body)
            if b:
                val = b.group(1).strip()
                if val.lower() not in {"none", "n/a", "na"}:
                    values.append(val)
            elif body.strip() and not body.strip().startswith("```"):
                # Keep short prose blockers/next actions as actionable text.
                values.append(body.strip())
        break
    return values


def _first_section_text(lines, heading_names):
    vals = _section_values(lines, heading_names)
    return vals[0] if vals else None


def _field_value(lines, names):
    wanted = {name.lower() for name in names}
    for line in lines:
        for regex in (FIELD_RE, PLAIN_FIELD_RE):
            m = regex.match(line)
            if m and m.group(1).strip().lower().replace("_", " ") in wanted:
                return m.group(2).strip()
    return None


def _completion_ids(root):
    ids = set()
    completion_dir = root / "collaboration" / "work_packages" / "completions"
    for path in completion_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        wp_id = data.get("work_package_id") or (ID_RE.search(path.name).group(1) if ID_RE.search(path.name) else None)
        if wp_id and data.get("codex_status", "done") == "done":
            ids.add(wp_id)
    return ids


def _parse_package(root, path, completed_ids, generated_at):
    rel = _rel(path, root)
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    id_match = ID_RE.search(path.name) or ID_RE.search(text)
    wp_id = id_match.group(1) if id_match else path.stem
    mode = (_field_value(lines, ["mode"]) or "").strip().strip(".") or ("SERIES" if "SERIES" in path.name.upper() else "UNKNOWN")
    owner = (_field_value(lines, ["owner"]) or "").strip().strip(".")
    deps = _split_values(_field_value(lines, ["dependencies"]) or "") or _section_values(lines, ["Dependencies", "Depends On", "Blocked By"])
    blockers = _split_values(_field_value(lines, ["blockers", "blocked by"]) or "") or _section_values(lines, ["Blockers", "Blocked By"])
    next_action = (_field_value(lines, ["next action", "next_action"]) or _first_section_text(lines, ["Next Action", "Codex Command"]) or "Review work package and execute the stated mission.").strip()
    state = (_field_value(lines, ["state", "status"]) or "").strip().strip(".").lower()
    if wp_id in completed_ids or "/completed/" in f"/{rel}/":
        state = "completed"
    elif blockers:
        state = "blocked"
    elif "/claimed/" in f"/{rel}/":
        state = "claimed"
    elif "/open/" in f"/{rel}/":
        state = "open"
    elif not state:
        state = "pending"
    warnings = []
    if not owner:
        warnings.append({"type": "missing_owner", "work_package_id": wp_id, "path": rel, "message": f"{wp_id} has no explicit owner."})
        owner = "unassigned"
    return {
        "work_package_id": wp_id,
        "path": rel,
        "mode": mode,
        "owner": owner,
        "state": state,
        "dependencies": deps,
        "next_action": next_action,
        "blockers": blockers,
        "last_updated": generated_at,
    }, warnings


def generate_assignment_queue(root=None, write=True):
    root = Path(root) if root else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())
    generated_at = _now()
    completed_ids = _completion_ids(root)
    entries, warnings = [], []
    for directory in WORK_PACKAGE_DIRS:
        base = root / directory
        if not base.exists():
            continue
        for path in sorted(base.glob("*.md")):
            if path.name == "README.md":
                continue
            entry, entry_warnings = _parse_package(root, path, completed_ids, generated_at)
            entries.append(entry)
            warnings.extend(entry_warnings)
    state_order = {"blocked": 0, "pending": 1, "open": 2, "claimed": 3, "completed": 4}
    entries.sort(key=lambda e: (state_order.get(e["state"], 9), e["work_package_id"]))
    payload = {"version": 1, "generated_at": generated_at, "summary": {"work_package_count": len(entries), "warning_count": len(warnings), "blocked_count": sum(1 for e in entries if e["state"] == "blocked"), "unassigned_count": sum(1 for e in entries if e["owner"] == "unassigned")}, "work_packages": entries, "warnings": warnings}
    if write:
        out = root / "runtime" / "work_packages" / "assignment_queue.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md = root / "operations" / "work_packages" / "assignment_queue.md"
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(format_assignment_queue_markdown(payload), encoding="utf-8")
    return payload


def format_assignment_queue_markdown(queue):
    lines = ["# Estate Assignment Queue", "", f"Generated: {queue['generated_at']}", "", "## Summary", "", f"- Work packages: {queue['summary']['work_package_count']}", f"- Blocked: {queue['summary']['blocked_count']}", f"- Unassigned: {queue['summary']['unassigned_count']}", f"- Warnings: {queue['summary']['warning_count']}", "", "## Queue", "", "| Work Package | Mode | Owner | State | Dependencies | Blockers | Next Action |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for e in queue["work_packages"]:
        deps = "<br>".join(e["dependencies"]) if e["dependencies"] else "None"
        blockers = "<br>".join(e["blockers"]) if e["blockers"] else "None"
        lines.append(f"| [{e['work_package_id']}](../../{e['path']}) | {e['mode']} | {e['owner']} | {e['state']} | {deps} | {blockers} | {e['next_action']} |")
    if queue["warnings"]:
        lines += ["", "## Warnings", ""]
        for w in queue["warnings"]:
            lines.append(f"- {w['type']}: {w['message']} ({w['path']})")
    return "\n".join(lines) + "\n"
