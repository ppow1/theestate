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


class PacketError(ValueError):
    """A packet failed deterministic safety or provenance validation."""


def artifact_identity(root: Path, relative: str) -> dict[str, Any]:
    path, relative = _safe_file(root, relative)
    head = git(root, "rev-parse", f"HEAD:{relative}") or None
    worktree = git(root, "hash-object", "--", relative) or None
    status = {line[3:].replace("\\", "/"): line[:2] for line in git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines() if len(line) > 3}
    return {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "git_blob": worktree, "head_git_blob": head, "worktree_state": "untracked" if head is None else ("dirty" if relative in status else "clean")}


def baseline(root: Path, paths: list[str]) -> dict[str, Any]:
    return {"repository_revision": git(root, "rev-parse", "HEAD") or "UNKNOWN", "artifacts": [artifact_identity(root, path) for path in paths]}


def _safe_file(root: Path, value: str) -> tuple[Path, str]:
    if not isinstance(value, str) or not value or "\\" in value:
        raise PacketError("changed file must be a non-empty POSIX repository-relative path")
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise PacketError(f"unsafe changed file path: {value}")
    path = root / rel
    if not path.exists() or not path.is_file():
        raise PacketError(f"changed file does not exist: {value}")
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise PacketError(f"changed file escapes repository: {value}") from exc
    if path.is_symlink():
        raise PacketError(f"changed file may not be a symlink: {value}")
    return path, rel.as_posix()


def create_packet(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    """Create a strict packet without mutating the caller's request."""
    root = root.resolve()
    payload = copy.deepcopy(request)
    if "change_id" not in payload and "packet_id" in payload:
        payload["change_id"] = payload["packet_id"]
    legacy_proposed = copy.deepcopy(payload.get("proposed_knowledge", []))
    legacy_affected = copy.deepcopy(payload.get("affected_checkpoints", []))
    legacy_probes = copy.deepcopy(payload.get("probes", []))
    derived_source = "author_provenance" not in payload and isinstance(payload.get("source"), dict)
    if derived_source:
        source = payload["source"]
        if not source.get("actor"): raise PacketError("source actor is required")
        payload["author_provenance"] = {"kind": {"ai": "EXTERNAL_AI", "automation": "DETERMINISTIC", "human": "HUMAN"}.get(str(source.get("kind", "")).lower(), "MIXED"), "actor": source.get("actor", "")}
    if payload.get("confidence") == "HIGH":
        payload["confidence"] = "SUPPORTED"
    if "preliminary_troubleshooting_notes" not in payload and isinstance(payload.get("proposed_knowledge"), list):
        payload["preliminary_troubleshooting_notes"] = [item.get("text", "") for item in payload["proposed_knowledge"] if isinstance(item, dict)]
    if legacy_affected and any(value == "UNKNOWN" for value in legacy_affected): raise PacketError("unknown checkpoint declaration")
    if legacy_probes and len(legacy_probes) != len(set(legacy_probes)): raise PacketError("duplicate probe declaration")
    if any(isinstance(item, dict) and item.get("state") not in {"CANDIDATE", "PROPOSED"} for item in legacy_proposed): raise PacketError("proposed knowledge cannot be promoted")
    if not derived_source and "author_provenance" in payload and isinstance(payload["author_provenance"], dict) and not payload["author_provenance"].get("actor"):
        payload["author_provenance"]["actor"] = "Estate software worker"
    legacy = {"packet_id", "component", "intended_behavior", "dependencies", "invariants", "failure_seams", "probes", "evidence", "boundaries", "affected_checkpoints", "source"}
    for key in legacy:
        payload.pop(key, None)
    declared = payload.get("changed_files")
    if not isinstance(declared, list) or not declared:
        raise PacketError("changed_files must be a non-empty array")
    if len(declared) != len(set(declared)):
        raise PacketError("changed_files contains duplicate declarations")
    artifacts = []
    normalized = []
    status = {line[3:].replace("\\", "/"): line[:2] for line in git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines() if len(line) > 3}
    for value in declared:
        path, rel = _safe_file(root, value)
        normalized.append(rel)
        head_blob = git(root, "rev-parse", f"HEAD:{rel}") or None
        worktree_blob = git(root, "hash-object", "--", rel) or None
        tracked = bool(git(root, "ls-files", "--error-unmatch", "--", rel))
        state = "UNTRACKED" if not tracked else ("DIRTY" if rel in status else "CLEAN")
        state_name = "UNTRACKED" if state == "UNTRACKED" else ("DIRTY" if state == "DIRTY" else "CLEAN")
        artifacts.append({"path": rel, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "head_git_blob": head_blob, "worktree_git_blob": worktree_blob, "state": state_name,
                          "worktree_state": state_name.lower()})
    payload["changed_files"] = normalized
    payload["changed_artifacts"] = artifacts
    payload.setdefault("packet_version", "1.0.0")
    payload.setdefault("source_revision", git(root, "rev-parse", "HEAD") or "UNKNOWN")
    payload.setdefault("implementation_revision", payload["source_revision"])
    if legacy_proposed: payload["proposed_knowledge"] = legacy_proposed
    errors = validate_impact_packet(payload, root=root)
    if errors:
        raise PacketError("invalid Diagnostic Impact Packet: " + "; ".join(errors))
    return payload


def preserve_candidate(root: Path, packet: dict[str, Any]) -> Path:
    """Persist valid packet knowledge as explicitly non-canonical candidate data."""
    errors = validate_impact_packet(packet, root=root)
    if errors:
        raise ValueError("invalid Diagnostic Impact Packet: " + "; ".join(errors))
    candidate = {"candidate_version": "1.0.0", "change_id": packet["change_id"],
                 "canonical_promotion": False, "packet": packet,
                 "proposed_knowledge": packet.get("proposed_knowledge", [])}
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


def local_ai_delta(root: Path, _reconciliation: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return bounded review input, never an authorization or promotion action."""
    from .knowledge import query_knowledge
    canonical = []
    checkpoint_path = root / "docs/operations/troubleshooting/checkpoints.json"
    if checkpoint_path.exists():
        try: canonical = [item.get("canonical_knowledge", {}) for item in json.loads(checkpoint_path.read_text(encoding="utf-8")).get("checkpoints", [])]
        except (OSError, ValueError): pass
    return {"delta_version": "1.0.0", "purpose": "LOCAL_AI_CANDIDATE_REVIEW",
            "may_advance_accepted_baseline": False, "may_promote_canonical_knowledge": False,
            "candidates": query_candidates(root), "knowledge_candidates": query_knowledge(root),
            "canonical_knowledge": canonical,
            "allowed_outputs": ["candidate_checkpoint_edits", "contradiction_report", "revalidation_request", "bounded_diagnostic_summary"],
            "forbidden_actions": ["promote_knowledge", "rewrite_canonical_cookbook", "execute_remediation", "reproduce_destructive_failure"]}


def reconcile(root: Path, baseline_path: Path, packet_paths: list[Path]) -> dict[str, Any]:
    """Compatibility projection for packet-focused reconciliation tests.

    Canonical checkpoint mutation remains owned by ``living.reconcile``; this
    helper only projects accepted candidate metadata and coverage.
    """
    root = root.resolve()
    accepted = json.loads(baseline_path.read_text(encoding="utf-8"))
    previous = {item["path"]: item for item in accepted.get("artifacts", [])}
    current = {path: artifact_identity(root, path) for path in previous if (root / path).exists()}
    changed = sorted(path for path, old in previous.items() if current.get(path, {}).get("sha256") != old.get("sha256"))
    accepted_packets, rejected, candidates, covered = [], [], [], set()
    for packet_path in packet_paths:
        try:
            packet = json.loads(packet_path.read_text(encoding="utf-8")); errors = validate_impact_packet(packet, root=root)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            packet, errors = {}, [str(exc)]
        for artifact in packet.get("changed_artifacts", []) if isinstance(packet, dict) else []:
            if isinstance(artifact, dict) and artifact.get("path"):
                try:
                    if artifact.get("sha256") != artifact_identity(root, artifact["path"])["sha256"]: errors.append(f"stale artifact identity: {artifact['path']}")
                except PacketError as exc: errors.append(str(exc))
        if errors:
            rejected.append({"path": str(packet_path), "errors": errors}); continue
        accepted_packets.append(packet["change_id"])
        covered.update(packet.get("changed_files", []))
        preserve_candidate(root, packet)
        candidates.append({"change_id": packet["change_id"], "implementation_revision": packet.get("implementation_revision"), "affected_checkpoints": packet.get("recommended_checkpoint_impacts", []), "probes": packet.get("preliminary_troubleshooting_notes", []), "evidence": packet.get("validation_evidence", []), "proposed_knowledge": packet.get("proposed_knowledge", []), "local_ai_interpretation_required": True, "canonical_promotion": False})
    uncovered = sorted(set(changed) - covered)
    checkpoint_ids = []
    checkpoint_path = root / "docs/operations/troubleshooting/checkpoints.json"
    if checkpoint_path.exists():
        try: checkpoint_ids = [item.get("id") or item.get("checkpoint_id") for item in json.loads(checkpoint_path.read_text(encoding="utf-8")).get("checkpoints", [])]
        except (OSError, ValueError): pass
    affected = [{"id": checkpoint, "state": "REVALIDATION_REQUIRED"} for checkpoint in checkpoint_ids if checkpoint]
    return {"accepted_packets": accepted_packets, "rejected_packets": rejected, "candidates": candidates, "uncovered_changes": uncovered, "affected_checkpoints": affected, "classification": "CHANGE_WITHOUT_DIAGNOSTIC_IMPACT_METADATA" if uncovered else None}
