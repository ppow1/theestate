"""Deterministic, review-only validation of WP-4209 candidate bundles.

This layer consumes extraction output as evidence.  It never edits the input,
pending definitions, or proposed repository destinations.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Iterable

from estate.core.conversation_specification_extraction import SCHEMA_VERSION as EXTRACTION_SCHEMA
from estate.core.conversation_specification_extraction import parse_expected

SCHEMA_VERSION = "estate.conversation-specification-reconciliation/v1"
NONCANONICAL = "non_canonical_review_required"
WP = re.compile(r"^WP-\d{4}$")
HEADING = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")
EMPTY = re.compile(r"^(?:tbd|todo|none|n/?a|pending|placeholder|[-–—]|\.\.\.)[.!]?$", re.I)
CLAIM = re.compile(r"\b(?:implemented|tests? pass(?:ed)?|validated|completed|closed|production.ready)\b", re.I)
AREAS = {
    "policy_and_governing_principles": ("policy", "principle", "authority", "governance"),
    "schemas_and_persistent_records": ("schema", "record", "manifest", "persistent"),
    "runtime_behavior": ("runtime", "behavior", "workflow", "operation"),
    "decision_and_escalation_logic": ("decision", "escalation", "conflict"),
    "boundaries_and_prohibited_behavior": ("boundar", "prohibit", "must never", "excluded"),
    "estate_system_integrations": ("integration", "estate system", "interface", "depend"),
    "audit_and_review_surfaces": ("audit", "review", "provenance"),
    "diagnostics_and_failure_handling": ("diagnostic", "failure", "error", "blocked"),
    "operator_documentation": ("operator", "documentation", "command", "cli"),
    "unit_tests": ("unit test",), "integration_tests": ("integration test",),
    "validation_scenarios": ("validation", "scenario"),
    "anti_patterns": ("anti-pattern", "antipattern"),
    "completion_criteria": ("completion", "acceptance criteria"),
}


class ReconciliationError(ValueError):
    """An input violates the review bundle contract."""


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as stream:
        stream.write(text)
        temporary = Path(stream.name)
    temporary.replace(path)


def _sections(text: str) -> dict[str, str]:
    matches = list(HEADING.finditer(text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        key = re.sub(r"[^a-z0-9]+", "_", match.group(2).lower()).strip("_")
        body = text[match.end():end].strip()
        result[key] = body
    return result


def _substantive(text: str) -> bool:
    plain = re.sub(r"[`#>*_|-]", " ", text).strip()
    return len(re.findall(r"[A-Za-z0-9]+", plain)) >= 5 and not EMPTY.fullmatch(plain)


def _pending_file(root: Path, wp: str) -> Path:
    matches = sorted(root.glob(f"{wp}_*.md"))
    if len(matches) != 1:
        raise ReconciliationError(f"{wp}: expected exactly one authoritative pending definition, found {len(matches)}")
    return matches[0]


def _structural(content: str, authoritative: str) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    lower = content.lower()
    auth_lower = authoritative.lower()
    sections = _sections(content)
    assessments: list[dict[str, object]] = []
    diagnostics: list[dict[str, str]] = []
    for area, terms in AREAS.items():
        applicable = any(term in auth_lower for term in terms)
        mapped = [name for name, body in sections.items()
                  if any(term.replace("-", " ") in (name.replace("_", " ").replace("-", " ") + " " + body.lower())
                         for term in terms)]
        substantive = [name for name in mapped if _substantive(sections[name])]
        if not applicable:
            status = "not_applicable"
        elif not mapped:
            status = "absent"
        elif not substantive:
            status = "present_substantively_empty"
        elif len(substantive) < len(mapped) or sum(len(sections[n].split()) for n in substantive) < 20:
            status = "partial"
        else:
            status = "complete"
        assessments.append({"area": area, "status": status, "mapped_sections": mapped,
                            "rule": "deterministic_keyword_and_substance_v1"})
        if status in {"absent", "present_substantively_empty", "partial"}:
            diagnostics.append({"code": f"runtime_area_{status}", "area": area})
    for match in CLAIM.finditer(content):
        window = content[max(0, match.start() - 80):match.end() + 100]
        if not re.search(r"(?:evidence|commit|sha|pytest|test report|artifact)\s*[:#]", window, re.I):
            diagnostics.append({"code": "unsupported_completion_claim", "detail": match.group(0)})
    return assessments, diagnostics


def _contradictions(left: str, right: str) -> list[dict[str, str]]:
    opposites = (("must ", "must not "), ("shall ", "shall not "),
                 ("automatic", "manual"), ("enabled", "disabled"), ("allow", "prohibit"))
    found = []
    a, b = left.lower(), right.lower()
    for positive, negative in opposites:
        if (positive in a and negative in b) or (negative in a and positive in b):
            found.append({"left_term": positive.strip(), "right_term": negative.strip(),
                          "classification": "potential_direct_contradiction"})
    return found


def _validate_destination(destination: object, repository_root: Path, pending_root: Path) -> dict[str, object]:
    if not isinstance(destination, str) or not destination.strip():
        return {"status": "ambiguous_destination", "blocking": True}
    path = Path(destination)
    if path.is_absolute() or ".." in path.parts:
        return {"status": "ambiguous_destination", "blocking": True}
    pending_rel = pending_root.resolve().relative_to(repository_root.resolve())
    if path == pending_rel or pending_rel in path.parents:
        return {"status": "pending_definition_overwrite", "blocking": True}
    target = repository_root / path
    if target.exists():
        return {"status": "existing_destination_collision", "blocking": True,
                "existing_sha256": _hash(target.read_bytes()) if target.is_file() else None}
    return {"status": "create_new_file", "blocking": False}


def reconcile_bundles(bundle_paths: list[Path], expected: list[str], output_root: Path, *,
                      repository_root: Path, pending_root: Path | None = None,
                      generate_drafts: bool = False) -> Path:
    """Validate bundles together and create an immutable review-output snapshot."""
    if not bundle_paths:
        raise ReconciliationError("at least one WP-4209 bundle is required")
    pending_root = pending_root or repository_root / "collaboration/work_packages/pending"
    loaded: list[dict[str, object]] = []
    bundle_sources = []
    invalid: set[str] = set()
    diagnostics: list[dict[str, object]] = []
    for bundle in sorted((p.resolve() for p in bundle_paths), key=str):
        report_path = bundle / "validation_report.json"
        report_bytes = report_path.read_bytes()
        report = json.loads(report_bytes)
        if report.get("schema_version") != EXTRACTION_SCHEMA:
            raise ReconciliationError(f"{bundle}: unsupported extraction schema")
        if report.get("canonical_status") != "non_canonical_review_material":
            raise ReconciliationError(f"{bundle}: candidate bundle is not explicitly non-canonical")
        run = report.get("run_id")
        archive_hash = (report.get("source") or {}).get("archive_sha256")
        if not isinstance(run, str) or not run or not re.fullmatch(r"[a-f0-9]{64}", str(archive_hash)):
            raise ReconciliationError(f"{bundle}: incomplete run/source provenance")
        bundle_sources.append({"bundle": str(bundle), "extraction_run_id": run,
                               "source_archive_sha256": archive_hash,
                               "validation_report_sha256": _hash(report_bytes)})
        for raw in report.get("candidates", []):
            item = dict(raw)
            wp = item.get("wp_id")
            provenance = item.get("provenance") or {}
            reasons = [f"upstream_{code}" for code in item.get("diagnostics", [])]
            if not isinstance(wp, str) or not WP.fullmatch(wp): reasons.append("invalid_wp_identifier")
            if provenance.get("wp_identifier") != wp or provenance.get("extraction_run") != run or provenance.get("source_archive_sha256") != archive_hash:
                reasons.append("provenance_mismatch")
            artifact = bundle / str(item.get("staging_artifact", ""))
            content = artifact.read_bytes() if artifact.is_file() else b""
            if not content or _hash(content) != item.get("content_sha256"): reasons.append("candidate_hash_tampering")
            item.update({"bundle": str(bundle), "extraction_run_id": run, "source_archive_sha256": archive_hash,
                         "content": content.decode("utf-8", errors="replace"), "intake_diagnostics": reasons})
            if reasons and isinstance(wp, str): invalid.add(wp)
            loaded.append(item)
    seed = _json({"schema": SCHEMA_VERSION, "expected": expected, "sources": bundle_sources,
                  "candidates": [{k: x.get(k) for k in ("wp_id", "content_sha256", "extraction_run_id", "source_archive_sha256", "proposed_destination")} for x in loaded]})
    run_id = _hash(seed.encode())[:20]
    run_dir = output_root / run_id
    temp = Path(tempfile.mkdtemp(prefix=f".{run_id}-", dir=output_root.parent if output_root.parent.exists() else None))
    build = temp / run_id
    build.mkdir(parents=True)
    assessments = []
    groups: dict[str, list[dict[str, object]]] = {}
    for item in loaded:
        wp = str(item.get("wp_id"))
        groups.setdefault(wp, []).append(item)
        authority = None
        authority_hash = None
        local_diags = list(item["intake_diagnostics"])
        structure: list[dict[str, object]] = []
        try:
            authority_path = _pending_file(pending_root, wp)
            authority = str(authority_path.relative_to(repository_root))
            authority_text = authority_path.read_text(encoding="utf-8")
            authority_hash = _hash(authority_text.encode())
            structure, structural_diags = _structural(str(item["content"]), authority_text)
            local_diags.extend(d["code"] for d in structural_diags)
        except (ReconciliationError, ValueError) as exc:
            local_diags.append("authoritative_definition_unavailable")
            diagnostics.append({"code": "authoritative_definition_unavailable", "wp_id": wp, "detail": str(exc)})
        destination = _validate_destination(item.get("proposed_destination"), repository_root, pending_root)
        if destination["blocking"]: local_diags.append(str(destination["status"]))
        assessments.append({"schema_version": SCHEMA_VERSION, "reconciliation_run_id": run_id, "wp_id": wp,
            "candidate_content_sha256": item.get("content_sha256"), "source_archive_sha256": item.get("source_archive_sha256"),
            "extraction_run_id": item.get("extraction_run_id"), "provenance": item.get("provenance"),
            "authoritative_definition": authority, "authoritative_definition_sha256": authority_hash,
            "runtime_canon_assessment": structure, "destination_assessment": destination,
            "diagnostics": sorted(set(local_diags)), "review_status": "blocked" if local_diags else "ready_for_human_review"})
    comparisons = []
    statuses: dict[str, str] = {}
    drafts: dict[str, str] = {}
    for wp, items in sorted(groups.items()):
        if wp in invalid or any(a["review_status"] == "blocked" for a in assessments if a["wp_id"] == wp):
            status = "review_blocked"
        elif len(items) == 1:
            status = "single_candidate"
        elif len({x["content_sha256"] for x in items}) == 1:
            status = "duplicate_identical"
        else:
            conflicts = []
            for i, left in enumerate(items):
                for right in items[i + 1:]: conflicts.extend(_contradictions(str(left["content"]), str(right["content"])))
            section_maps = [_sections(str(x["content"])) for x in items]
            overlap_conflict = any(len({m[name].strip() for m in section_maps if name in m}) > 1
                                   for name in set.intersection(*(set(m) for m in section_maps)) if name not in {""})
            status = "duplicate_material_conflict" if conflicts or overlap_conflict else "duplicate_compatible_merge_possible"
        statuses[wp] = status
        records = []
        for i, left in enumerate(items):
            for right in items[i + 1:]:
                ls, rs = _sections(str(left["content"])), _sections(str(right["content"]))
                records.append({"left_sha256": left["content_sha256"], "right_sha256": right["content_sha256"],
                    "similarity": round(difflib.SequenceMatcher(None, str(left["content"]), str(right["content"])).ratio(), 6),
                    "left_unique_sections": sorted(set(ls) - set(rs)), "right_unique_sections": sorted(set(rs) - set(ls)),
                    "changed_sections": sorted(k for k in set(ls) & set(rs) if ls[k].strip() != rs[k].strip()),
                    "contradictions": _contradictions(str(left["content"]), str(right["content"]))})
        comparisons.append({"wp_id": wp, "status": status, "candidate_count": len(items),
                            "candidate_provenance": [x.get("provenance") for x in items], "pairwise": records})
        if generate_drafts and status == "duplicate_compatible_merge_possible":
            merged: dict[str, tuple[str, str]] = {}
            for item in sorted(items, key=lambda x: str(x["content_sha256"])):
                for section, body in _sections(str(item["content"])).items(): merged.setdefault(section, (body, str(item["content_sha256"])))
            text = f"# {wp} — Reconciled Review Draft\n\n> NON-CANONICAL; HUMAN REVIEW REQUIRED. Reconciliation run `{run_id}`.\n"
            for section, (body, source_hash) in merged.items():
                text += f"\n## {section.replace('_', ' ').title()}\n\n<!-- source-sha256: {source_hash} -->\n{body}\n"
            drafts[wp] = text
            _atomic(build / "reconciled_candidates" / f"{wp}.md", text)
    found = sorted(wp for wp in groups if WP.fullmatch(wp))
    coverage = {"schema_version": SCHEMA_VERSION, "reconciliation_run_id": run_id, "source_hashes": bundle_sources,
                "expected": expected, "found": sorted(set(found) & set(expected)), "missing": sorted(set(expected) - set(found)),
                "duplicated": sorted(wp for wp in expected if len(groups.get(wp, [])) > 1),
                "unexpected": sorted(set(found) - set(expected)), "invalid": sorted(invalid),
                "blocked": sorted(wp for wp, status in statuses.items() if status in {"review_blocked", "duplicate_material_conflict"}),
                "ready_for_human_review": sorted(wp for wp, status in statuses.items() if status not in {"review_blocked", "duplicate_material_conflict"})}
    destination_groups: dict[str, list[str]] = {}
    for item in loaded:
        if item.get("proposed_destination"): destination_groups.setdefault(str(item["proposed_destination"]), []).append(str(item["wp_id"]))
    collisions = {path: ids for path, ids in destination_groups.items() if len(set(ids)) > 1}
    if collisions:
        diagnostics.append({"code": "cross_candidate_destination_collision", "destinations": collisions})
        coverage["blocked"] = sorted(set(coverage["blocked"]) | {x for ids in collisions.values() for x in ids})
    promotion = {"schema_version": SCHEMA_VERSION, "reconciliation_run_id": run_id, "canonical_status": NONCANONICAL,
                 "source_hashes": bundle_sources, "mode": "review_only_no_writes", "actions": [
                     {"wp_id": wp, "candidate_sha256": item["content_sha256"], "proposed_destination": item.get("proposed_destination"),
                      "destination_status": next(a["destination_assessment"]["status"] for a in assessments if a["candidate_content_sha256"] == item["content_sha256"]),
                      "action": "human_review_required", "automatic_promotion": False}
                     for wp, items in sorted(groups.items()) for item in items]}
    _atomic(build / "coverage_report.json", _json(coverage))
    _atomic(build / "candidate_assessments.jsonl", "".join(json.dumps(x, sort_keys=True) + "\n" for x in assessments))
    _atomic(build / "duplicate_comparisons.json", _json({"schema_version": SCHEMA_VERSION, "reconciliation_run_id": run_id, "source_hashes": bundle_sources, "comparisons": comparisons}))
    _atomic(build / "promotion_plan.json", _json(promotion))
    _atomic(build / "diagnostics.json", _json({"schema_version": SCHEMA_VERSION, "reconciliation_run_id": run_id, "source_hashes": bundle_sources, "diagnostics": diagnostics}))
    blocking = bool(coverage["missing"] or coverage["unexpected"] or coverage["invalid"] or coverage["blocked"])
    report_lines = ["# Conversation Specification Reconciliation Report", "", f"Run: `{run_id}`", "",
                    "**NON-CANONICAL — HUMAN REVIEW REQUIRED. No promotion or repository destination write occurred.**", "",
                    "Source evidence:", ""]
    report_lines += [f"- archive `{source['source_archive_sha256']}`; extraction run `{source['extraction_run_id']}`; report `{source['validation_report_sha256']}`"
                     for source in bundle_sources]
    report_lines += ["",
                    f"Status: `{'review_blocked' if blocking else 'ready_for_human_review'}`", "", "## Coverage", "",
                    f"- Expected: {', '.join(expected) or 'none'}", f"- Found: {', '.join(coverage['found']) or 'none'}",
                    f"- Missing: {', '.join(coverage['missing']) or 'none'}", f"- Blocked: {', '.join(coverage['blocked']) or 'none'}", "", "## Reconciliation", ""]
    report_lines += [f"- {wp}: `{status}`" for wp, status in sorted(statuses.items())]
    _atomic(build / "reconciliation_report.md", "\n".join(report_lines) + "\n")
    artifacts = {}
    for path in sorted(p for p in build.rglob("*") if p.is_file()): artifacts[str(path.relative_to(build))] = _hash(path.read_bytes())
    manifest = {"schema_version": SCHEMA_VERSION, "reconciliation_run_id": run_id, "canonical_status": NONCANONICAL,
                "status": "review_blocked" if blocking else "ready_for_human_review", "source_hashes": bundle_sources,
                "artifacts": artifacts, "safety": {"inputs_modified": False, "pending_definitions_modified": False,
                "canonical_destinations_written": False, "automatic_promotion": False}}
    _atomic(build / "reconciliation_manifest.json", _json(manifest))
    output_root.mkdir(parents=True, exist_ok=True)
    if run_dir.exists(): shutil.rmtree(run_dir)
    build.replace(run_dir)
    shutil.rmtree(temp, ignore_errors=True)
    return run_dir


def validate_reconciliation(run_dir: Path) -> dict[str, object]:
    manifest = json.loads((run_dir / "reconciliation_manifest.json").read_text())
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("canonical_status") != NONCANONICAL:
        raise ReconciliationError("invalid reconciliation manifest")
    for relative, digest in manifest.get("artifacts", {}).items():
        path = run_dir / relative
        if not path.is_file() or _hash(path.read_bytes()) != digest: raise ReconciliationError(f"artifact integrity failure: {relative}")
    return {"valid": True, "run_id": manifest["reconciliation_run_id"], "status": manifest["status"]}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundles", nargs="+", type=Path)
    parser.add_argument("--expected", required=True)
    parser.add_argument("--output-root", type=Path, default=Path("staging/conversation_reconciliation"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--pending-root", type=Path)
    parser.add_argument("--generate-compatible-drafts", action="store_true")
    args = parser.parse_args(argv)
    run = reconcile_bundles(args.bundles, parse_expected(args.expected), args.output_root,
                            repository_root=args.repository_root, pending_root=args.pending_root,
                            generate_drafts=args.generate_compatible_drafts)
    result = validate_reconciliation(run)
    print(json.dumps({**result, "output": str(run)}, sort_keys=True))
    return 2 if result["status"] == "review_blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
