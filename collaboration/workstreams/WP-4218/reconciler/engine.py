"""Deterministic, offline and read-only reconciliation engine for WP-4218."""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "estate.engineering-queue/v1"
POLICY_VERSION = "wp4218-policy/v1"
LANES = {"Runtime", "Office UI", "Documentation", "Validation", "Registry", "AI Runtime", "Infrastructure", "Testing", "Governance"}
CLASSIFICATIONS = {"captured", "promoted", "authored_but_not_implemented", "partially_implemented", "implemented_but_not_validated", "implemented_and_complete", "blocked", "duplicate", "superseded", "stale", "ambiguous_requires_review"}
READINESS = {"ready", "ready_with_coordination", "blocked", "needs_definition", "needs_evidence", "needs_review", "in_progress", "validation", "complete", "superseded"}

class ReconciliationError(ValueError):
    """A source or generated record violated the staged contract."""

def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()

def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()

def _record(path: Path, raw: dict[str, Any], root: Path) -> dict[str, Any]:
    if not isinstance(raw, dict) or not raw.get("id") or not raw.get("title"):
        raise ReconciliationError(f"malformed source record: {path}")
    item = dict(raw)
    item["id"] = str(item["id"]).upper()
    item.setdefault("source_category", "work_package")
    item.setdefault("lifecycle_state", "pending")
    item.setdefault("dependencies", [])
    item.setdefault("touch_points", [])
    item.setdefault("evidence", {})
    item.setdefault("diagnostics", [])
    item["source_locator"] = path.relative_to(root).as_posix()
    item["source_digest"] = digest(raw)
    return item

def discover(root: Path) -> list[dict[str, Any]]:
    """Discover explicit JSON snapshots in stable order; Markdown is referenced, not copied."""
    root = root.resolve()
    if not root.is_dir():
        raise ReconciliationError(f"source root is not a directory: {root}")
    paths = sorted((p for p in root.rglob("*.json") if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
    records: list[dict[str, Any]] = []
    for path in paths:
        if "fixtures" in path.relative_to(root).parts:
            # Test evidence embedded in a checkout is never canonical live input.
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReconciliationError(f"malformed JSON source: {path}: {exc}") from exc
        if not isinstance(payload, dict) or "records" not in payload:
            # Unrelated repository JSON is not a source snapshot.
            continue
        values = payload.get("records", [])
        if not isinstance(values, list):
            raise ReconciliationError(f"source must contain a records array: {path}")
        records.extend(_record(path, value, root) for value in values)
    # The checkout adapter is deliberately conservative: only governed work-package and
    # board locations are inspected, and only explicit identifiers/headings are normalized.
    markdown_roots = [root / "collaboration/work_packages", root / "operations/boards"]
    for base in markdown_roots:
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md"), key=lambda p: p.relative_to(root).as_posix()):
            text = path.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"(?m)^#\s+(?P<id>WP-[A-Za-z0-9-]+)\s+(?:—|-)\s+(?P<title>.+?)\s*$", text)
            if not match:
                continue
            status = re.search(r"(?im)^- \*\*Status:\*\*\s*(.+)$", text)
            raw = {"id": match.group("id"), "title": match.group("title"), "source_category": "work_package", "lifecycle_state": status.group(1).strip().lower() if status else "unknown", "lane": "Governance", "evidence": {}}
            records.append(_record(path, raw, root))
    return sorted(records, key=lambda r: (r["id"], r["source_locator"], r["source_digest"]))

def _classification(r: dict[str, Any], duplicate: bool, cycle: bool, known_ids: set[str]) -> tuple[str, str, list[str]]:
    ev, diagnostics = r["evidence"], list(r["diagnostics"])
    deps = [str(x).upper() for x in r["dependencies"]]
    missing = sorted(set(deps) - known_ids)
    if missing: diagnostics.append("missing_dependency:" + ",".join(missing))
    if cycle: diagnostics.append("dependency_cycle")
    if r.get("ambiguous") or r.get("possible_supersedes"): return "ambiguous_requires_review", "needs_review", diagnostics
    if r.get("supersedes") and r.get("supersession_coverage", "full") == "full": return "superseded", "superseded", diagnostics
    if duplicate: return "duplicate", "needs_review", diagnostics
    if cycle or missing or r.get("blockers"): return "blocked", "blocked", diagnostics
    if r.get("stale"): return "stale", "blocked", diagnostics + ["stale_source"]
    if ev.get("implementation") and ev.get("validation") and ev.get("completion_receipt") and ev.get("merge"): return "implemented_and_complete", "complete", diagnostics
    if ev.get("implementation") and not ev.get("validation"): return "implemented_but_not_validated", "validation", diagnostics
    if ev.get("implemented_criteria", 0) and ev.get("implemented_criteria", 0) < ev.get("total_criteria", 1): return "partially_implemented", "in_progress", diagnostics
    if r["source_category"] == "parking_lot": return ("promoted" if r.get("work_package") else "captured"), ("needs_evidence" if r.get("work_package") else "needs_definition"), diagnostics
    return "authored_but_not_implemented", "ready", diagnostics

def _cycles(records: list[dict[str, Any]]) -> set[str]:
    graph = {r["id"]: [str(d).upper() for d in r["dependencies"]] for r in records}
    affected: set[str] = set()
    def visit(node: str, trail: list[str]) -> None:
        if node in trail:
            affected.update(trail[trail.index(node):]); return
        for nxt in graph.get(node, []): visit(nxt, trail + [node])
    for node in sorted(graph): visit(node, [])
    return affected

def _lane(r: dict[str, Any]) -> tuple[str, list[str]]:
    declared = r.get("lane")
    if declared in LANES: return declared, []
    paths = " ".join(r["touch_points"])
    matches = []
    for lane, pattern in (("Testing", r"(^|/)tests?/"), ("Documentation", r"(^|/)(docs|collaboration)/"), ("Registry", r"schema|registry"), ("Office UI", r"office|ui"), ("Runtime", r"(^|/)src/")):
        if re.search(pattern, paths, re.I): matches.append(lane)
    return (matches[0], matches[1:]) if len(matches) == 1 else ("Unknown", sorted(set(matches)))

def reconcile(records: list[dict[str, Any]], source_revision: str, generation_timestamp: str = "1970-01-01T00:00:00Z") -> dict[str, Any]:
    records = sorted(records, key=lambda r: (r["id"], r["source_locator"], r["source_digest"]))
    identities: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in records: identities[r.get("alias_of", r["id"])].append(r)
    cycle_ids, known = _cycles(records), {r["id"] for r in records}
    rows = []
    for r in records:
        duplicate = len(identities[r.get("alias_of", r["id"])]) > 1 or bool(r.get("probable_duplicate_of"))
        classification, readiness, diagnostics = _classification(r, duplicate, r["id"] in cycle_ids, known)
        lane, secondary = _lane(r)
        if lane == "Unknown": classification, readiness = "ambiguous_requires_review", "needs_review"
        touches = sorted(set(r["touch_points"]))
        risk_reasons = (["unknown_touch_points"] if not touches else []) + (["production_runtime"] if any(p.startswith("src/") for p in touches) else []) + (["broad_or_shared_touch_point"] if any("*" in p or p in {"src/", "collaboration/"} for p in touches) else [])
        risk = "high" if len(risk_reasons) > 1 else "medium" if risk_reasons else "low"
        blockers = sorted(set(r.get("blockers", []) + (["dependency_cycle"] if r["id"] in cycle_ids else []) + [d for d in diagnostics if d.startswith("missing_dependency")]))
        parallel = "unsafe" if risk in {"high", "critical"} or not touches else "conditional" if risk == "medium" else "safe"
        score = 100 if readiness == "ready" else 70 if readiness == "ready_with_coordination" else 20 if readiness in {"in_progress", "validation"} else 0
        score += int(r.get("institutional_priority", 0)); score -= {"low": 0, "medium": 10, "high": 25, "critical": 40}[risk]
        provenance = [{"source_locator": r["source_locator"], "content_digest": r["source_digest"], "adapter_version": "snapshot-json/v1"}]
        rows.append({"item_identifier": r["id"], "candidate_identifier": r.get("alias_of", r["id"]), "item_title": r["title"], "source_category": r["source_category"], "current_lifecycle_state": r["lifecycle_state"], "reconciliation_classification": classification, "readiness_classification": readiness, "priority": {"score": score, "band": "high" if score >= 80 else "normal" if score >= 40 else "held", "factors": ["readiness", "institutional_priority", "merge_risk"]}, "engineering_lane": {"primary": lane, "secondary": secondary}, "dependencies": sorted(set(str(x).upper() for x in r["dependencies"])), "blockers": blockers, "repository_touch_points": touches, "parallel_safety_classification": parallel, "parallel_group": r.get("wp4215_adapter", {}).get("group"), "merge_risk_classification": risk, "merge_risk_reasons": risk_reasons, "estimated_complexity": r.get("estimated_complexity", "unknown"), "duration_estimate_reference": r.get("wp4214_adapter", {}).get("reference"), "git_readiness_reference": r.get("wp4217_adapter", {}).get("reference"), "evidence_completeness": "complete" if classification == "implemented_and_complete" else "partial" if r["evidence"] else "missing", "diagnostics": sorted(set(diagnostics)), "source_evidence_references": [r["source_locator"]], "provenance": provenance})
    rows.sort(key=lambda x: (-x["priority"]["score"], x["merge_risk_classification"], x["item_identifier"], x["candidate_identifier"]))
    logical = {"queue_schema_version": SCHEMA_VERSION, "policy_version": POLICY_VERSION, "source_revision": source_revision, "rows": rows}
    content_hash = digest(logical)
    result = {**logical, "generation_identifier": content_hash[:20], "generation_timestamp": generation_timestamp, "deterministic_content_hash": content_hash, "advisory_only": True}
    validate_queue(result)
    return result

def validate_queue(queue: dict[str, Any]) -> None:
    required = {"queue_schema_version", "generation_identifier", "generation_timestamp", "source_revision", "rows", "deterministic_content_hash", "advisory_only"}
    missing = required - queue.keys()
    if missing or queue.get("queue_schema_version") != SCHEMA_VERSION or queue.get("advisory_only") is not True: raise ReconciliationError(f"invalid queue: missing={sorted(missing)}")
    for row in queue["rows"]:
        if row["reconciliation_classification"] not in CLASSIFICATIONS or row["readiness_classification"] not in READINESS: raise ReconciliationError("invalid classification")

def render_report(queue: dict[str, Any]) -> str:
    lines = ["# Advisory Engineering Reconciliation", "", f"Generation: `{queue['generation_identifier']}`", f"Source revision: `{queue['source_revision']}`", "", "| Priority | Item | Classification | Readiness | Lane | Risk |", "|---:|---|---|---|---|---|"]
    for r in queue["rows"]: lines.append(f"| {r['priority']['score']} | {r['item_identifier']} | {r['reconciliation_classification']} | {r['readiness_classification']} | {r['engineering_lane']['primary']} | {r['merge_risk_classification']} |")
    lines += ["", "> Advisory projection only. Review and update canonical evidence through its governing authority.", ""]
    return "\n".join(lines)
