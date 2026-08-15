"""Deterministic Estate troubleshooting comprehension views.

The authored model is deliberately small and explicit.  This module enriches
it with repository evidence, derives diagrams, and emits bounded provider
packets.  It does not infer runtime truth or promote candidate knowledge.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .knowledge import query_knowledge
from .living import canonical_json, git, sha256

SOURCE = Path("docs/operations/troubleshooting/comprehension.json")
MODEL_SCHEMA = Path("schemas/troubleshooting/comprehension_model_v1.schema.json")


class ComprehensionError(ValueError):
    """The comprehension model or requested scope is unsafe or invalid."""


def _ids(items: list[dict[str, Any]], field: str, label: str) -> list[str]:
    values = [item.get(field) for item in items]
    errors = []
    if any(not isinstance(value, str) or not value for value in values):
        errors.append(f"{label} identifiers must be non-empty strings")
    if len(values) != len(set(values)):
        errors.append(f"duplicate {label} identifier")
    if errors:
        raise ComprehensionError("; ".join(errors))
    return values


def validate_model(root: Path, model: dict[str, Any]) -> list[str]:
    """Validate structural references and source boundaries fail-closed."""
    errors: list[str] = []
    if not isinstance(model, dict):
        return ["model must be an object"]
    required = {"schema_version", "model_id", "components", "relationships", "workflows", "checkpoints", "failure_seams"}
    errors.extend(f"missing required field: {key}" for key in sorted(required - model.keys()))
    if model.get("schema_version") != "1.0":
        errors.append("schema_version must be 1.0")
    if not isinstance(model.get("model_id"), str) or not model.get("model_id"):
        errors.append("model_id must be non-empty")
    for key in ("components", "relationships", "workflows", "checkpoints", "failure_seams"):
        if not isinstance(model.get(key), list):
            errors.append(f"{key} must be an array")
    if errors:
        return errors
    try:
        components = {item["component_id"]: item for item in model["components"]}
        workflows = {item["workflow_id"]: item for item in model["workflows"]}
        checkpoints = {item["checkpoint_id"]: item for item in model["checkpoints"]}
        seams = {item["seam_id"]: item for item in model["failure_seams"]}
        _ids(model["components"], "component_id", "component")
        _ids(model["relationships"], "relationship_id", "relationship")
        _ids(model["workflows"], "workflow_id", "workflow")
        _ids(model["checkpoints"], "checkpoint_id", "checkpoint")
        _ids(model["failure_seams"], "seam_id", "failure seam")
    except (KeyError, TypeError, ComprehensionError) as exc:
        return [str(exc)]
    for component in components.values():
        for path in component.get("source_paths", []):
            if not _safe_source(root, path): errors.append(f"component source is missing or unsafe: {path}")
        for checkpoint in component.get("checkpoint_ids", []):
            if checkpoint not in checkpoints: errors.append(f"component references unknown checkpoint: {checkpoint}")
    for relationship in model["relationships"]:
        if relationship.get("source") not in components: errors.append(f"relationship source is unknown: {relationship.get('source')}")
        if relationship.get("target") not in components: errors.append(f"relationship target is unknown: {relationship.get('target')}")
        for path in relationship.get("evidence_refs", []):
            if not _safe_source(root, path): errors.append(f"relationship evidence is missing or unsafe: {path}")
    for workflow in workflows.values():
        if not workflow.get("component_ids"): errors.append(f"workflow has no components: {workflow.get('workflow_id')}")
        for component in workflow.get("component_ids", []):
            if component not in components: errors.append(f"workflow references unknown component: {component}")
        for checkpoint in workflow.get("checkpoint_ids", []):
            if checkpoint not in checkpoints: errors.append(f"workflow references unknown checkpoint: {checkpoint}")
        for path in workflow.get("source_paths", []):
            if not _safe_source(root, path): errors.append(f"workflow source is missing or unsafe: {path}")
    for checkpoint in checkpoints.values():
        if checkpoint.get("workflow_id") not in workflows: errors.append(f"checkpoint workflow is unknown: {checkpoint.get('checkpoint_id')}")
        if checkpoint.get("component_id") not in components: errors.append(f"checkpoint component is unknown: {checkpoint.get('checkpoint_id')}")
        for path in checkpoint.get("source_paths", []):
            if not _safe_source(root, path): errors.append(f"checkpoint source is missing or unsafe: {path}")
    for seam in seams.values():
        if seam.get("workflow_id") not in workflows: errors.append(f"failure seam workflow is unknown: {seam.get('seam_id')}")
        for component in seam.get("component_ids", []):
            if component not in components: errors.append(f"failure seam component is unknown: {component}")
        for checkpoint in seam.get("checkpoint_ids", []):
            if checkpoint not in checkpoints: errors.append(f"failure seam checkpoint is unknown: {checkpoint}")
        for path in seam.get("evidence_refs", []):
            if not _safe_source(root, path): errors.append(f"failure seam evidence is missing or unsafe: {path}")
    return errors


def _safe_source(root: Path, value: str) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return False
    candidate = root / path
    try:
        return candidate.is_file() and not candidate.is_symlink() and candidate.resolve().is_relative_to(root.resolve())
    except OSError:
        return False


def _source_evidence(root: Path, paths: set[str]) -> dict[str, dict[str, str]]:
    evidence: dict[str, dict[str, str]] = {}
    for value in sorted(paths):
        path = root / value
        head_blob = git(root, "rev-parse", f"HEAD:{value}") or None
        worktree_blob = git(root, "hash-object", "--", value) or None
        evidence[value] = {"sha256": sha256(path), "head_git_blob": head_blob or "LOCAL_REVISION", "worktree_git_blob": worktree_blob or "LOCAL_REVISION", "state": "CLEAN" if head_blob == worktree_blob else "MODIFIED"}
    return evidence


def _all_sources(model: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    for key in ("components", "workflows", "checkpoints"):
        for item in model[key]: paths.update(item.get("source_paths", []))
    for item in model["relationships"] + model["failure_seams"]:
        paths.update(item.get("evidence_refs", []))
    return paths


def _staleness(previous: dict[str, Any] | None, current: dict[str, dict[str, str]]) -> dict[str, Any]:
    if previous is None:
        return {"state": "CURRENT", "changed_sources": [], "revalidation_required": False}
    old = (previous or {}).get("provenance", {}).get("source_evidence", {})
    changed = sorted(path for path in set(old) | set(current) if old.get(path, {}).get("sha256") != current.get(path, {}).get("sha256"))
    return {"state": "REVALIDATION_REQUIRED" if changed else "CURRENT", "changed_sources": changed, "revalidation_required": bool(changed)}


def build_model(root: Path, output: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    authored = json.loads((root / SOURCE).read_text(encoding="utf-8"))
    errors = validate_model(root, authored)
    if errors: raise ComprehensionError("invalid authored comprehension model: " + "; ".join(errors))
    previous = None
    if output:
        prior = output / "model.json"
        if prior.exists():
            try: previous = json.loads(prior.read_text(encoding="utf-8"))
            except (OSError, ValueError): previous = None
    model = copy.deepcopy(authored)
    evidence = _source_evidence(root, _all_sources(model))
    model["provenance"] = {"repository_revision": git(root, "rev-parse", "HEAD") or "UNKNOWN", "branch": git(root, "branch", "--show-current") or "DETACHED", "worktree_dirty": bool(git(root, "status", "--porcelain=v1", "--untracked-files=all")), "source_evidence": evidence}
    model["staleness"] = _staleness(previous, evidence)
    if output:
        output.mkdir(parents=True, exist_ok=True)
        (output / "model.json").write_text(canonical_json(model), encoding="utf-8")
        (output / "staleness.json").write_text(canonical_json(model["staleness"]), encoding="utf-8")
        (output / "component-graph.mmd").write_text(render_mermaid(model, "components"), encoding="utf-8")
        for workflow in model["workflows"]:
            (output / f"workflow-{workflow['workflow_id']}.mmd").write_text(render_mermaid(model, workflow["workflow_id"]), encoding="utf-8")
    return model


def _select(model: dict[str, Any], scope: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    components = [x for x in model["components"] if x["component_id"] == scope]
    workflows = [x for x in model["workflows"] if x["workflow_id"] == scope or scope in x.get("component_ids", [])]
    checkpoint_ids = {x["checkpoint_id"] for w in workflows for x in model["checkpoints"] if x["checkpoint_id"] in w["checkpoint_ids"]}
    checkpoint_ids.update(x["checkpoint_id"] for x in model["checkpoints"] if x.get("component_id") == scope)
    checkpoints = [x for x in model["checkpoints"] if x["checkpoint_id"] in checkpoint_ids]
    seams = [x for x in model["failure_seams"] if x.get("workflow_id") in {w["workflow_id"] for w in workflows} or scope in x.get("component_ids", [])]
    return components, workflows, checkpoints, seams


def render_mermaid(model: dict[str, Any], scope: str = "components") -> str:
    revision = model.get("provenance", {}).get("repository_revision", "UNKNOWN")
    lines = ["flowchart LR", f"  %% source_revision: {revision}", f"  %% model_id: {model.get('model_id', 'UNKNOWN')}"]
    if scope == "components":
        for item in model["components"]: lines.append(f"  {item['component_id']}[{item['title']}]")
        for edge in model["relationships"]:
            if edge["source"] != edge["target"]: lines.append(f"  {edge['source']} -->|{edge['kind']}| {edge['target']}")
    else:
        workflows = [x for x in model["workflows"] if x["workflow_id"] == scope]
        for workflow in workflows:
            checkpoints = sorted((x for x in model["checkpoints"] if x["checkpoint_id"] in workflow["checkpoint_ids"]), key=lambda x: x["sequence"])
            for checkpoint in checkpoints: lines.append(f"  {checkpoint['checkpoint_id']}[{checkpoint['checkpoint_id']}: {checkpoint['expected_output']}]")
            for left, right in zip(checkpoints, checkpoints[1:]): lines.append(f"  {left['checkpoint_id']} --> {right['checkpoint_id']}")
            for seam in model["failure_seams"]:
                if seam["workflow_id"] == scope:
                    lines.append(f"  {seam['seam_id']}{{{seam['title']}}}")
                    for checkpoint in seam["checkpoint_ids"]: lines.append(f"  {checkpoint} -. failure seam .-> {seam['seam_id']}")
    return "\n".join(lines) + "\n"


def comprehension_packet(root: Path, model: dict[str, Any], scope: str) -> dict[str, Any]:
    components, workflows, checkpoints, seams = _select(model, scope)
    if not components and not workflows: raise ComprehensionError(f"unknown comprehension scope: {scope}")
    refs = {ref for item in components + workflows + checkpoints + seams for ref in item.get("source_paths", []) + item.get("evidence_refs", [])}
    knowledge_refs = {ref for item in components + checkpoints + seams for ref in item.get("knowledge_refs", [])}
    existing = query_knowledge(root)
    cookbook = json.loads((root / "docs/operations/troubleshooting/cookbook.json").read_text(encoding="utf-8"))
    linked = [x for x in cookbook.get("checkpoints", []) if x.get("checkpoint_id") in knowledge_refs]
    return {"contract":"estate.troubleshooting.comprehension.packet.v1","provider_neutral":True,"scope":scope,"source_revision":model["provenance"]["repository_revision"],"source_evidence":{ref:model["provenance"]["source_evidence"][ref] for ref in sorted(refs)},"components":components,"relationships":[x for x in model["relationships"] if x["source"] in {c["component_id"] for c in components} or x["target"] in {c["component_id"] for c in components}],"workflows":workflows,"checkpoints":checkpoints,"failure_seams":seams,"linked_cookbook_knowledge":linked,"linked_candidate_knowledge":[x for x in existing if any(ref in canonical_json(x) for ref in knowledge_refs)],"requested_analysis":["identify missing relationships or checkpoints","distinguish deterministic and candidate failure seams","propose non-destructive probes","identify stale understanding"],"allowed_outputs":["candidate_components","candidate_relationships","candidate_checkpoints","candidate_failure_seams","probe_recommendations","contradiction_report","revalidation_request","diagram_annotations"],"forbidden_actions":["mutate_canonical_model","promote_candidate_knowledge","advance_accepted_baseline","authorize_remediation","restart_or_reset_runtime","run_destructive_stress"]}


def query_model(model: dict[str, Any], phrase: str) -> list[dict[str, Any]]:
    needle = phrase.lower()
    result = []
    for key in ("components", "workflows", "checkpoints", "failure_seams"):
        for item in model[key]:
            if needle in canonical_json(item).lower(): result.append({"kind":key[:-1], "id": item.get(key[:-1] + "_id") or item.get("checkpoint_id") or item.get("seam_id"), "title":item.get("title") or item.get("expected_output")})
    return result
