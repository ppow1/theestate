from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from estate.core.paths import ESTATE_ROOT

DEFAULT_COMPLETIONS_DIR = ESTATE_ROOT / "collaboration" / "work_packages" / "completions"
REQUIRED_COMPLETION_FIELDS = (
    "work_package_id",
    "codex_status",
    "completed_at",
    "branch",
    "pull_request_url",
    "summary",
    "files_changed",
    "tests_run",
    "known_limitations",
    "ready_for_ca_review",
    "merge_authority",
)
DONE_STATUSES = {"done", "completed"}


@dataclass(frozen=True)
class CompletionRecordCheck:
    path: str
    work_package_id: str | None
    is_complete: bool
    ready_for_ca_review: bool
    missing_fields: tuple[str, ...]
    errors: tuple[str, ...]
    record: dict[str, Any]


def completion_record_path(work_package_id: str, completions_dir: str | Path = DEFAULT_COMPLETIONS_DIR) -> Path:
    return Path(completions_dir) / f"{work_package_id}_codex_done.json"


def load_completion_record(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_completion_record(path: str | Path) -> CompletionRecordCheck:
    record_path = Path(path)
    errors: list[str] = []
    try:
        record = load_completion_record(record_path)
    except FileNotFoundError:
        return CompletionRecordCheck(str(record_path), None, False, False, REQUIRED_COMPLETION_FIELDS, ("record not found",), {})
    except json.JSONDecodeError as exc:
        return CompletionRecordCheck(str(record_path), None, False, False, REQUIRED_COMPLETION_FIELDS, (f"invalid json: {exc.msg}",), {})

    missing = tuple(field for field in REQUIRED_COMPLETION_FIELDS if field not in record)
    status = str(record.get("codex_status", "")).lower()
    ready = record.get("ready_for_ca_review") is True
    if missing:
        errors.append("missing required completion fields")
    if status not in DONE_STATUSES:
        errors.append("codex_status is not done")
    if not ready:
        errors.append("ready_for_ca_review is not true")

    return CompletionRecordCheck(
        path=str(record_path),
        work_package_id=record.get("work_package_id"),
        is_complete=not errors,
        ready_for_ca_review=ready,
        missing_fields=missing,
        errors=tuple(errors),
        record=record,
    )


def list_completion_records(completions_dir: str | Path = DEFAULT_COMPLETIONS_DIR) -> list[CompletionRecordCheck]:
    directory = Path(completions_dir)
    if not directory.exists():
        return []
    return [check_completion_record(path) for path in sorted(directory.glob("*_codex_done.json"))]


def completion_status(work_package_id: str, completions_dir: str | Path = DEFAULT_COMPLETIONS_DIR) -> CompletionRecordCheck:
    return check_completion_record(completion_record_path(work_package_id, completions_dir))


def format_completion_status(check: CompletionRecordCheck) -> str:
    lines = [f"Completion record: {check.path}"]
    lines.append(f"Work package: {check.work_package_id or '(unknown)'}")
    lines.append(f"Complete: {check.is_complete}")
    lines.append(f"Ready for CA review: {check.ready_for_ca_review}")
    if check.missing_fields:
        lines.append("Missing fields: " + ", ".join(check.missing_fields))
    if check.errors:
        lines.append("Errors: " + "; ".join(check.errors))
    return "\n".join(lines)
