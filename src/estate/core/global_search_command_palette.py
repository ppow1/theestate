"""Unified local Global Search and Command Palette for Estate artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from estate.core.institutional_search import build_institutional_search_index
from estate.core.paths import ESTATE_ROOT

PALETTE_INDEX_PATH = Path("runtime/search/global_command_palette.json")

COMMANDS = [
    {"id": "navigate.home", "title": "Navigate: Home", "category": "navigation", "operation": "activate_tab", "target": "home", "available": True},
    {"id": "navigate.work-packages", "title": "Navigate: Work Packages", "category": "navigation", "operation": "activate_tab", "target": "work-packages", "available": True},
    {"id": "navigate.daily-board", "title": "Navigate: Daily Board", "category": "navigation", "operation": "activate_tab", "target": "daily-board", "available": True},
    {"id": "navigate.parking-lot", "title": "Navigate: Parking Lot", "category": "navigation", "operation": "activate_tab", "target": "parking", "available": True},
    {"id": "navigate.mailboxes", "title": "Navigate: Mailboxes", "category": "navigation", "operation": "activate_tab", "target": "mailboxes", "available": True},
    {"id": "notification-center", "title": "Open Notification Center", "category": "navigation", "operation": "activate_tab", "target": "recalls", "available": True},
    {"id": "navigate.notification-center", "title": "Navigate: Notification Center", "category": "navigation", "operation": "activate_tab", "target": "recalls", "available": True},
    {"id": "navigate.residents", "title": "Navigate: Residents", "category": "navigation", "operation": "activate_tab", "target": "alfred", "available": True},
    {"id": "navigate.validation", "title": "Navigate: Validation", "category": "navigation", "operation": "activate_tab", "target": "validation", "available": True},
    {"id": "navigate.settings", "title": "Navigate: Settings", "category": "navigation", "operation": "activate_tab", "target": "settings", "available": True},
    {"id": "command.refresh-status", "title": "Refresh status and activity console", "category": "command", "operation": "refresh_chrome", "available": True},
    {"id": "cli.estate-search", "title": "Run Estate institutional search", "category": "command", "operation": "existing_cli", "cli": "estate-search <query>", "available": True},
    {"id": "cli.assignment-queue", "title": "Generate assignment queue", "category": "command", "operation": "existing_cli", "cli": "assignment-queue", "available": True},
    {"id": "cli.worker-runtime-summary", "title": "Generate worker runtime summary", "category": "command", "operation": "existing_cli", "cli": "worker-runtime-summary", "available": True},
    {"id": "command.ai-interpret", "title": "Interpret this request with AI", "category": "unavailable", "operation": "unavailable", "available": False, "unavailable_reason": "WP-0054 forbids invented AI interpretation; use explicit registered commands only."},
]

DOMAIN_RULES = [
    ("collaboration/work_packages/", "work_package"),
    ("data/registry/missions", "mission"),
    ("collaboration/mailboxes/", "mailbox"),
    ("collaboration/messages/", "mailbox"),
    ("residents/", "resident"),
    ("data/objects/RES-", "resident"),
    ("operations/boards/daily_board", "daily_board"),
    ("operations/briefings/morning_briefing", "daily_board"),
    ("operations/boards/parking_lot", "parking_lot"),
    ("operations/validation/", "validation"),
    ("runtime/validation/", "validation"),
    ("docs/", "documentation"),
]

SUPPLEMENTAL_LOCATIONS = [
    "data/registry/missions.json",
    "data/registry/residents.json",
    "data/objects",
    "residents",
]


def _root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _domain(path: str, artifact_type: str) -> str:
    for prefix, domain in DOMAIN_RULES:
        if path.startswith(prefix):
            return domain
    if artifact_type == "document":
        return "documentation"
    return artifact_type or "artifact"


def _record_to_item(record: dict[str, Any]) -> dict[str, Any]:
    path = str(record.get("path", ""))
    domain = _domain(path, str(record.get("artifact_type", "artifact")))
    return {
        "kind": "artifact",
        "domain": domain,
        "title": record.get("title") or path,
        "path": path,
        "excerpt": record.get("excerpt", ""),
        "authoritative": bool(record.get("authoritative")),
        "policy_classification": record.get("policy_classification"),
        "action": {"operation": "open_artifact", "target": path, "available": True},
    }


def build_global_palette(root: str | Path | None = None, write: bool = True) -> dict[str, Any]:
    base = _root(root)
    index = build_institutional_search_index(base, write=True)
    records = list(index.get("records", []))
    seen = {record.get("path") for record in records}
    for location in SUPPLEMENTAL_LOCATIONS:
        path = base / location
        if not path.exists():
            continue
        candidates = [path] if path.is_file() else sorted(child for child in path.rglob("*") if child.is_file() and child.suffix.lower() in {".md", ".json", ".txt"})
        for candidate in candidates:
            rel = str(candidate.relative_to(base)).replace("\\", "/")
            if rel in seen:
                continue
            seen.add(rel)
            try:
                text = candidate.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            title = rel
            if candidate.suffix == ".json":
                try:
                    payload = json.loads(text)
                    if isinstance(payload, dict):
                        title = str(payload.get("title") or payload.get("name") or payload.get("display_name") or payload.get("id") or rel)
                except json.JSONDecodeError:
                    pass
            else:
                title = next((line.lstrip("#").strip() for line in text.splitlines() if line.strip().startswith("#")), rel)
            records.append({"path": rel, "title": title, "artifact_type": "artifact", "excerpt": text[:220], "authoritative": True, "policy_classification": "source_artifact"})
    artifacts = [_record_to_item(record) for record in records]
    commands = [{"kind": "command", "domain": "command", **command} for command in COMMANDS]
    payload = {
        "generated_at": _now(),
        "index_path": str(PALETTE_INDEX_PATH),
        "local_only": True,
        "verbosity_default": "normal",
        "domains": sorted({item["domain"] for item in artifacts} | {"command"}),
        "commands": commands,
        "artifacts": artifacts,
        "record_count": len(artifacts) + len(commands),
        "warnings": index.get("warnings", []),
    }
    if write:
        out = base / PALETTE_INDEX_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def search_global_palette(query: str, root: str | Path | None = None, refresh: bool = True) -> dict[str, Any]:
    base = _root(root)
    palette_path = base / PALETTE_INDEX_PATH
    palette = build_global_palette(base, write=True) if refresh or not palette_path.exists() else json.loads(palette_path.read_text(encoding="utf-8"))
    terms = [term.lower() for term in query.split() if term]
    items = palette.get("commands", []) + palette.get("artifacts", [])
    matches = []
    for item in items:
        haystack = " ".join(str(item.get(k, "")) for k in ("id", "title", "domain", "path", "excerpt", "category", "cli")).lower()
        if not terms or all(term in haystack for term in terms):
            matches.append(item)
    return {"query": query, "match_count": len(matches), "matches": matches, "warnings": palette.get("warnings", []), "index_path": str(PALETTE_INDEX_PATH)}


def execute_registered_command(command_id: str) -> dict[str, Any]:
    command = next((cmd for cmd in COMMANDS if cmd["id"] == command_id), None)
    if command is None:
        return {"ok": False, "command_id": command_id, "status": "unavailable", "message": "Command is not registered."}
    if not command.get("available"):
        return {"ok": False, "command_id": command_id, "status": "unavailable", "message": command.get("unavailable_reason", "Command is unavailable.")}
    return {"ok": True, "command_id": command_id, "status": "ready", "operation": command.get("operation"), "target": command.get("target"), "cli": command.get("cli"), "message": "Command is registered; execute through the existing operation handler."}


def format_palette_report(result: dict[str, Any]) -> str:
    lines = ["Estate Global Search and Command Palette", f"Query: {result.get('query', '')}", f"Matches: {result.get('match_count', 0)}"]
    for warning in result.get("warnings", []):
        lines.append(f"WARNING: {warning}")
    for match in result.get("matches", [])[:30]:
        status = "available" if match.get("available", True) else "unavailable"
        label = match.get("title") or match.get("id") or match.get("path")
        lines.append(f"- [{match.get('kind')}/{match.get('domain')}] {label} ({status})")
        if match.get("path"):
            lines.append(f"  path: {match['path']}")
        if not match.get("available", True):
            lines.append(f"  unavailable: {match.get('unavailable_reason', 'Command unavailable.')}")
    return "\n".join(lines)
