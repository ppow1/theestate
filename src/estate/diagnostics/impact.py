"""Diagnostic Impact Packet creation and candidate-knowledge projections.

Packet authoring belongs here; reconciliation and baseline authority deliberately
remain in :mod:`estate.diagnostics.living`.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from .living import canonical_json, git, validate_impact_packet

CANDIDATE_DIR = Path("operations/diagnostics/candidates")


def _safe_file(root: Path, value: str) -> tuple[Path, str]:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("changed file must be a non-empty POSIX repository-relative path")
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe changed file path: {value}")
    path = root / rel
    if not path.exists() or not path.is_file():
        raise ValueError(f"changed file does not exist: {value}")
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"changed file escapes repository: {value}") from exc
    if path.is_symlink():
        raise ValueError(f"changed file may not be a symlink: {value}")
    return path, rel.as_posix()


def create_packet(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    """Create a strict packet without mutating the caller's request."""
    root = root.resolve()
    payload = copy.deepcopy(request)
    declared = payload.get("changed_files")
    if not isinstance(declared, list) or not declared:
        raise ValueError("changed_files must be a non-empty array")
    if len(declared) != len(set(declared)):
        raise ValueError("changed_files contains duplicate declarations")
    artifacts = []
    normalized = []
    status = {line[3:].replace("\\", "/"): line[:2] for line in git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines() if len(line) > 3}
    for value in declared:
        path, rel = _safe_file(root, value)
        normalized.append(rel)
        head_blob = git(root, "rev-parse", f"HEAD:{rel}") or None
        worktree_blob = git(root, "hash-object", "--", rel) or None
        state = "UNTRACKED" if head_blob is None else ("DIRTY" if rel in status else "CLEAN")
        artifacts.append({"path": rel, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "head_git_blob": head_blob, "worktree_git_blob": worktree_blob, "state": state})
    payload["changed_files"] = normalized
    payload["changed_artifacts"] = artifacts
    payload.setdefault("packet_version", "1.0.0")
    payload.setdefault("source_revision", git(root, "rev-parse", "HEAD") or "UNKNOWN")
    payload.setdefault("implementation_revision", payload["source_revision"])
    errors = validate_impact_packet(payload, root=root)
    if errors:
        raise ValueError("invalid Diagnostic Impact Packet: " + "; ".join(errors))
    return payload


def preserve_candidate(root: Path, packet: dict[str, Any]) -> Path:
    """Persist valid packet knowledge as explicitly non-canonical candidate data."""
    errors = validate_impact_packet(packet, root=root)
    if errors:
        raise ValueError("invalid Diagnostic Impact Packet: " + "; ".join(errors))
    candidate = {"candidate_version": "1.0.0", "change_id": packet["change_id"],
                 "canonical_promotion": False, "packet": packet}
    destination = root / CANDIDATE_DIR / f"{packet['change_id']}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(canonical_json(candidate), encoding="utf-8")
    return destination


def query_candidates(root: Path, phrase: str | None = None) -> list[dict[str, Any]]:
    values = []
    for path in sorted((root / CANDIDATE_DIR).glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        item["candidate_path"] = path.relative_to(root).as_posix()
        if not phrase or phrase.lower() in canonical_json(item).lower():
            values.append(item)
    return values


def local_ai_delta(root: Path) -> dict[str, Any]:
    """Return bounded review input, never an authorization or promotion action."""
    return {"delta_version": "1.0.0", "purpose": "LOCAL_AI_CANDIDATE_REVIEW",
            "may_advance_accepted_baseline": False, "may_promote_canonical_knowledge": False,
            "candidates": query_candidates(root)}
