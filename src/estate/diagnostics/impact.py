"""Diagnostic Impact Packet creation, validation, and reconciliation.

Only repository-relative paths and content identities cross this boundary.  Packet
text is retained as candidate material; this module never edits the cookbook.
"""

from __future__ import annotations

import datetime as dt
import fnmatch
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

CONFIDENCE = {"LOW", "MEDIUM", "HIGH"}
SOURCE_KINDS = {"human", "ai", "automation"}
PROPOSAL_STATES = {"CANDIDATE", "PROPOSED"}


class PacketError(ValueError):
    """A fail-closed packet validation error."""


def _git(root: Path, *args: str) -> str | None:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else None


def _path(root: Path, value: str, *, must_exist: bool = True) -> Path:
    if not value or Path(value).is_absolute() or ".." in Path(value).parts:
        raise PacketError(f"unsafe repository path: {value!r}")
    resolved = (root / value).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise PacketError(f"path escapes repository: {value!r}") from exc
    if must_exist and (not resolved.is_file() or resolved.is_symlink()):
        raise PacketError(f"changed path is not a regular repository file: {value!r}")
    return resolved


def artifact_identity(root: Path, path: str) -> dict[str, Any]:
    target = _path(root, path)
    data = target.read_bytes()
    tracked = _git(root, "ls-files", "--error-unmatch", "--", path) is not None
    head_blob = _git(root, "rev-parse", f"HEAD:{path}") if tracked else None
    worktree_blob = _git(root, "hash-object", "--", path)
    status = "untracked" if not tracked else ("clean" if head_blob == worktree_blob else "dirty")
    return {
        "path": path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "git_blob": worktree_blob,
        "head_git_blob": head_blob,
        "worktree_state": status,
    }


def load_checkpoints(root: Path) -> list[dict[str, Any]]:
    return json.loads((root / "docs/operations/troubleshooting/checkpoints.json").read_text())["checkpoints"]


def _strings(packet: dict[str, Any], names: tuple[str, ...]) -> None:
    for name in names:
        value = packet.get(name)
        if not isinstance(value, list) or not value or any(not isinstance(v, str) or not v.strip() for v in value):
            raise PacketError(f"{name} must be a non-empty list of non-empty strings")
        if len(value) != len(set(value)):
            raise PacketError(f"{name} contains duplicate declarations")


def validate_packet(root: Path, packet: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(packet, dict) or packet.get("schema_version") != "1.0":
        raise PacketError("unsupported or missing schema_version")
    for name in ("packet_id", "component", "intended_behavior"):
        if not isinstance(packet.get(name), str) or not packet[name].strip():
            raise PacketError(f"missing required {name}")
    _strings(packet, ("dependencies", "invariants", "failure_seams", "probes", "evidence", "boundaries"))
    artifacts = packet.get("changed_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise PacketError("changed_artifacts must not be empty")
    paths = [item.get("path") for item in artifacts if isinstance(item, dict)]
    if len(paths) != len(artifacts) or len(paths) != len(set(paths)):
        raise PacketError("changed_artifacts must have unique path declarations")
    for supplied in artifacts:
        actual = artifact_identity(root, supplied["path"])
        if supplied.get("sha256") != actual["sha256"] or supplied.get("git_blob") != actual["git_blob"]:
            raise PacketError(f"artifact provenance does not match worktree: {supplied['path']}")
        if supplied.get("worktree_state") not in {"clean", "dirty", "untracked"}:
            raise PacketError(f"invalid worktree state: {supplied['path']}")
    known = {entry["id"] for entry in load_checkpoints(root)}
    affected = packet.get("affected_checkpoints")
    if not isinstance(affected, list) or len(affected) != len(set(affected)):
        raise PacketError("affected_checkpoints must be a unique list")
    unknown = sorted(set(affected) - known)
    if unknown:
        raise PacketError(f"unknown checkpoint(s): {', '.join(unknown)}")
    proposals = packet.get("proposed_knowledge")
    if not isinstance(proposals, list):
        raise PacketError("proposed_knowledge must be a list")
    for proposal in proposals:
        if not isinstance(proposal, dict) or proposal.get("state") not in PROPOSAL_STATES or not proposal.get("text"):
            raise PacketError("each proposal requires state CANDIDATE/PROPOSED and text")
    if packet.get("confidence") not in CONFIDENCE:
        raise PacketError("confidence must be LOW, MEDIUM, or HIGH")
    source = packet.get("source")
    if not isinstance(source, dict) or source.get("kind") not in SOURCE_KINDS or not source.get("actor") or not source.get("created_at"):
        raise PacketError("source requires authorized kind, actor, and created_at provenance")
    revision = packet.get("implementation_revision")
    if not isinstance(revision, dict) or not revision.get("git_revision") or not isinstance(revision.get("worktree_dirty"), bool):
        raise PacketError("implementation_revision provenance is required")
    if _git(root, "cat-file", "-e", f"{revision['git_revision']}^{{commit}}") is None:
        raise PacketError("implementation_revision is not available in this repository")
    for supplied in artifacts:
        historical = _git(root, "rev-parse", f"{revision['git_revision']}:{supplied['path']}")
        if supplied.get("head_git_blob") != historical:
            raise PacketError(f"head Git blob contradicts implementation revision: {supplied['path']}")
        expected_state = "untracked" if historical is None else ("clean" if historical == supplied["git_blob"] else "dirty")
        if supplied["worktree_state"] != expected_state:
            raise PacketError(f"worktree state contradicts blob provenance: {supplied['path']}")
    return packet


def create_packet(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    changed = request.pop("changed_files", None)
    if not isinstance(changed, list) or not changed:
        raise PacketError("changed_files must be a non-empty list")
    packet = {
        "schema_version": "1.0",
        **request,
        "changed_artifacts": [artifact_identity(root, path) for path in changed],
        "implementation_revision": {
            "git_revision": _git(root, "rev-parse", "HEAD"),
            "worktree_dirty": bool(_git(root, "status", "--porcelain")),
        },
    }
    packet.setdefault("source", {})
    packet["source"].setdefault("created_at", dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat())
    return validate_packet(root, packet)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def reconcile(root: Path, baseline_path: Path, packet_paths: list[Path]) -> dict[str, Any]:
    baseline = _read_json(baseline_path)
    current = {path: artifact_identity(root, path) for path in sorted(baseline["artifacts"])}
    changed = [path for path in current if current[path]["sha256"] != baseline["artifacts"][path]["sha256"]]
    accepted, rejected = [], []
    for path in sorted(packet_paths, key=lambda p: str(p)):
        try:
            packet = validate_packet(root, _read_json(path))
            accepted.append(packet)
        except (OSError, json.JSONDecodeError, PacketError) as exc:
            rejected.append({"path": str(path), "reason": str(exc)})
    covered = {a["path"] for p in accepted for a in p["changed_artifacts"]}
    checkpoints = load_checkpoints(root)
    affected = sorted({c["id"] for c in checkpoints for path in changed if any(fnmatch.fnmatch(path, g) for g in c["artifact_globs"])} | {c for p in accepted for c in p["affected_checkpoints"]})
    candidates = [{"packet_id": p["packet_id"], "implementation_revision": p["implementation_revision"], "changed_artifacts": p["changed_artifacts"], "affected_checkpoints": p["affected_checkpoints"], "probes": p["probes"], "evidence": p["evidence"], "proposed_knowledge": p["proposed_knowledge"], "local_ai_interpretation_required": True, "canonical_promotion": False} for p in accepted]
    uncovered = sorted(set(changed) - covered)
    return {
        "schema_version": "1.0", "accepted_baseline": baseline["git_revision"],
        "current_revision": _git(root, "rev-parse", "HEAD"), "changed_artifacts": [current[p] for p in changed],
        "accepted_packets": [p["packet_id"] for p in accepted], "rejected_packets": rejected,
        "uncovered_changes": uncovered, "classification": "CHANGE_WITHOUT_DIAGNOSTIC_IMPACT_METADATA" if uncovered else None,
        "affected_checkpoints": [{"id": c, "state": "REVALIDATION_REQUIRED"} for c in affected],
        "candidates": candidates, "canonical_cookbook_modified": False,
    }


def baseline(root: Path, paths: list[str]) -> dict[str, Any]:
    return {"schema_version": "1.0", "git_revision": _git(root, "rev-parse", "HEAD"), "artifacts": {p: artifact_identity(root, p) for p in sorted(paths)}}


def local_ai_delta(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    checkpoint_by_id = {c["id"]: c for c in load_checkpoints(root)}
    ids = [c["id"] for c in result["affected_checkpoints"]]
    return {"contract": "estate.local_ai_diagnostic_delta.v1", "accepted_baseline": result["accepted_baseline"], "current_revision": result["current_revision"], "changed_artifacts": result["changed_artifacts"], "accepted_packets": result["candidates"], "affected_checkpoints": [checkpoint_by_id[i] for i in ids], "canonical_knowledge": [checkpoint_by_id[i]["canonical_knowledge"] for i in ids], "evidence_references": sorted({e for c in result["candidates"] for e in c["evidence"]}), "allowed_outputs": ["applicability_assessment", "candidate_checkpoint_edits", "missing_dependencies", "missing_probes", "potential_conflicts", "revalidation_recommendations"], "forbidden_actions": ["advance_accepted_baseline", "rewrite_canonical_cookbook", "authorize_remediation", "mark_validated_from_model_opinion"]}
