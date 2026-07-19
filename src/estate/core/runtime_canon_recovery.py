"""WP-4212 pending-definition matched runtime-canon recovery.

Conversation output is evidence, pending definitions are authority, and everything
rendered by this module is non-canonical review material.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from estate.core.conversation_archive_ingestion import _write_atomic, ingest

SCHEMA_VERSION = "estate.runtime-canon-recovery/v1"
GENERATOR_VERSION = "WP-4212/1.0"
GENERATED_AT = "1970-01-01T00:00:00Z"  # deliberately stable for reproducible evidence
NUMBERED = re.compile(r"\bWP[- _](\d{4})\b", re.I)
NAMED = re.compile(r"\b(?:WP|CORE|OPS)-[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+\b")
HEADING = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*|\*{1,2}\s*)?(?:runtime canon\s*[—–:-]\s*)?"
    r"(?:(?:supporting (?:design|document)(?: for)?|grounded in)\s+)?"
    r"((?:WP[- _]\d{4})|(?:(?:WP|CORE|OPS)-[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+))\b"
    r"[^\n]{0,100}(?:runtime canon|supporting (?:runtime canon|design|document))?",
)
SECTION = re.compile(r"(?m)^#{1,6}\s+(.+?)\s*$")

DIAGNOSTIC_CODES = frozenset({
    "duplicate_pending_work_package_identifier", "malformed_pending_work_package_identifier",
    "pending_filename_body_identifier_mismatch", "unreadable_pending_definition",
    "substantive_candidate_detected", "identifier_only_false_positive",
    "candidate_identifier_unmatched", "candidate_identifier_ambiguous", "candidate_definition_invalid",
    "candidate_partial", "candidate_substantially_complete", "candidate_complete",
    "candidate_likely_truncated", "candidate_confirmed_truncated",
    "candidate_contradicts_definition", "candidate_contains_unsupported_claim",
    "duplicate_candidate", "near_duplicate_candidate", "competing_complete_candidates",
    "preferred_candidate_selected", "supporting_document_staged",
    "supporting_document_destination_unresolved", "automatic_promotion_prohibited",
    "assignment_scope_violation_secondary", "assignment_diagnostic_did_not_block_extraction",
})


def _sha(text: str | bytes) -> str:
    return hashlib.sha256(text if isinstance(text, bytes) else text.encode("utf-8")).hexdigest()


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def normalize_identifier(value: str) -> tuple[str | None, str]:
    value = value.strip().upper().replace("_", "-").replace(" ", "-")
    match = re.fullmatch(r"WP-(\d{4})", value)
    if match:
        return f"WP-{match.group(1)}", "numbered"
    if re.fullmatch(r"(?:WP|CORE|OPS)-[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+", value):
        return value, "named"
    return None, "malformed"


def diagnostic(code: str, message: str, severity: str = "review", **context: Any) -> dict[str, Any]:
    return {"code": code, "severity": severity, "message": message, "context": context}


@dataclass
class PendingWorkPackageIndex:
    root: Path
    records: list[dict[str, Any]] = field(default_factory=list)
    diagnostics: list[dict[str, Any]] = field(default_factory=list)

    def build(self) -> "PendingWorkPackageIndex":
        for path in sorted(self.root.glob("*.md"), key=lambda p: p.name.casefold()):
            filename_token = path.stem.split("_", 1)[0]
            filename_id, identifier_type = normalize_identifier(filename_token)
            problems: list[dict[str, Any]] = []
            try:
                body = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                problems.append(diagnostic("unreadable_pending_definition", str(exc), "fatal", path=str(path)))
                body = ""
            first_heading = next((m.group(1).strip() for m in SECTION.finditer(body)), "")
            body_match = NUMBERED.search(first_heading) or NAMED.search(first_heading)
            body_raw = body_match.group(0) if body_match else ""
            body_id, _ = normalize_identifier(body_raw) if body_raw else (None, "malformed")
            if not filename_id:
                problems.append(diagnostic("malformed_pending_work_package_identifier", "Filename has no approved identifier.", "fatal", filename=path.name))
            if filename_id and body_id and filename_id != body_id:
                problems.append(diagnostic("pending_filename_body_identifier_mismatch", "Filename and leading body identifier disagree.", "fatal", filename_identifier=filename_id, body_identifier=body_id))
            if filename_id and not body_id:
                problems.append(diagnostic("pending_filename_body_identifier_mismatch", "Leading heading has no reliable identifier.", "fatal", filename_identifier=filename_id))
            record = {
                "work_package_id": filename_id or filename_token, "canonical_identifier": filename_id,
                "title": re.sub(r"^(?:WP[- _]\d{4}|[^_]+)[_\s—–:-]*", "", first_heading or path.stem).strip(),
                "path": path.as_posix(), "filename": path.name, "content_sha256": _sha(body),
                "filename_identifier": filename_id, "body_identifier": body_id,
                "filename_body_consistent": bool(filename_id and body_id and filename_id == body_id),
                "identifier_type": identifier_type, "index_status": "invalid" if problems else "valid",
                "validation_diagnostics": problems, "content": body,
            }
            self.records.append(record); self.diagnostics.extend(problems)
        groups: dict[str, list[dict[str, Any]]] = {}
        for record in self.records:
            if record["canonical_identifier"]:
                groups.setdefault(record["canonical_identifier"], []).append(record)
        for identifier, records in sorted(groups.items()):
            if len(records) > 1:
                item = diagnostic("duplicate_pending_work_package_identifier", "Multiple pending definitions resolve to one identifier.", "fatal", identifier=identifier, paths=[r["path"] for r in records])
                self.diagnostics.append(item)
                for record in records:
                    record["index_status"] = "ambiguous"; record["validation_diagnostics"].append(item)
        return self

    def resolve(self, identifier: str) -> tuple[str, dict[str, Any] | None]:
        normalized, kind = normalize_identifier(identifier)
        if not normalized:
            return "malformed_identifier", None
        matches = [r for r in self.records if r["canonical_identifier"] == normalized]
        if not matches:
            return ("named_identifier_not_approved" if kind == "named" else "unmatched_identifier"), None
        if len(matches) > 1 or any(r["index_status"] == "ambiguous" for r in matches):
            return "ambiguous_identifier", None
        if matches[0]["index_status"] != "valid":
            return "pending_definition_invalid", matches[0]
        return "matched_unique", matches[0]

    def public_records(self) -> list[dict[str, Any]]:
        return [{k: v for k, v in record.items() if k != "content"} for record in self.records]


class RuntimeCanonCandidateDetector:
    def detect(self, record: dict[str, Any], source: dict[str, Any], previous: dict[str, Any] | None, following: dict[str, Any] | None) -> dict[str, Any] | None:
        if record.get("role") != "assistant":
            return None
        text = record.get("formatted_text") or record.get("text", "")
        ids = list(HEADING.finditer(text))
        fallback = NUMBERED.search(text[:300]) or NAMED.search(text[:300])
        identifier = ids[0].group(1) if ids else (fallback.group(0) if fallback else None)
        words = re.findall(r"\b\w+\b", text)
        sections = SECTION.findall(text)
        implementation_terms = sorted({term for term in ("schema", "runtime", "test", "validation", "boundary", "diagnostic", "CLI", "integration", "acceptance", "must") if re.search(rf"\b{re.escape(term)}\b", text, re.I)})
        quoted_seed = len(re.findall(r"(?m)^\s*>", text)) >= 3 or "authoritative work package" in text.lower() and "implement" in text.lower()
        declaration = bool(re.search(r"\b(?:I will|will now|plan to)\s+(?:produce|write|implement)\b", text, re.I))
        substantive = bool(identifier and len(words) >= 80 and (len(sections) >= 2 or len(implementation_terms) >= 4) and not quoted_seed and not declaration)
        signals = {"leading_identifier": bool(fallback), "recognized_heading": bool(ids), "word_count": len(words), "section_count": len(sections), "implementation_terms": implementation_terms, "quoted_seed": quoted_seed, "future_declaration": declaration}
        if not identifier:
            return None
        normalized_id, _ = normalize_identifier(identifier)
        normalized = _normalized(text)
        reasons = [] if substantive else (["quoted_or_startup_seed"] if quoted_seed else ["insufficient_substantive_structure"])
        provenance = record.get("provenance", {})
        return {
            "candidate_id": _sha(source["sha256"] + ":" + str(record["sequence"]) + ":" + normalized)[:20],
            "candidate_wp_identifier": normalized_id or identifier, "detected": substantive,
            "decision": "substantive_candidate_detected" if substantive else "identifier_only_false_positive",
            "rejection_reasons": reasons, "detector_signals": signals,
            "source_archive": source.get("path", ""), "source_archive_sha256": source["sha256"],
            "conversation_identifier": source.get("content_location") or source["sha256"][:16],
            "source_message_sequence": record["sequence"], "source_message_id": record.get("source_message_id"),
            "source_role": record["role"], "original_text": text, "normalized_text": normalized,
            "line_boundaries": {"start": provenance.get("line_start"), "end": provenance.get("line_end")},
            "character_boundaries": {"start": 0, "end": len(text)},
            "preceding_message_reference": previous.get("source_message_id") if previous else None,
            "following_message_reference": following.get("source_message_id") if following else None,
            "candidate_hash": _sha(normalized), "parser_version": GENERATOR_VERSION,
            "extraction_timestamp": GENERATED_AT, "segments": [{"sequence": record["sequence"], "hash": record.get("formatted_text_sha256") or record.get("text_sha256")}],
            "join_reason": "single_complete_assistant_message", "assignment_diagnostics": [],
        }


DIMENSIONS = {
    "purpose": "purpose", "objective": "objective", "governing principle": "governing_principles",
    "scope": "scope", "required implementation": "required_implementation_areas", "deliverable": "required_deliverables",
    "persistent": "persistent_records", "schema": "schemas", "runtime": "runtime_behavior",
    "decision": "decision_logic", "escalation": "escalation_logic", "boundar": "boundaries",
    "prohibited": "prohibited_behavior", "integration": "integrations", "audit": "audit_surfaces",
    "review": "review_surfaces", "diagnostic": "diagnostic_handling", "operator": "operator_documentation",
    "cli": "cli_behavior", "unit test": "unit_tests", "integration test": "integration_tests",
    "regression": "regression_tests", "validation": "validation_scenarios", "anti-pattern": "anti_patterns",
    "completion": "completion_criteria", "acceptance": "acceptance_criteria",
}


class WorkPackageDefinitionParser:
    def parse(self, definition: dict[str, Any]) -> list[dict[str, Any]]:
        text = definition["content"]; lines = text.splitlines(); headings = [(i + 1, m.group(1).strip()) for i, line in enumerate(lines) if (m := re.match(r"^#{2,6}\s+(.+?)\s*$", line))]
        result = []
        for pos, (start, heading) in enumerate(headings):
            end = headings[pos + 1][0] - 1 if pos + 1 < len(headings) else len(lines)
            lower = heading.lower(); dimension = next((value for key, value in DIMENSIONS.items() if key in lower), re.sub(r"[^a-z0-9]+", "_", lower).strip("_"))
            requirement = "\n".join(lines[start:end]).strip()
            mode = "prohibited" if "must not" in requirement.lower() or "prohibited" in lower else "conditional" if re.search(r"\b(if|when|where)\b", requirement, re.I) else "advisory" if re.search(r"\b(may|should)\b", requirement, re.I) and "must" not in requirement.lower() else "mandatory"
            result.append({"original_heading": heading, "normalized_dimension": dimension, "source_line_range": [start, end], "requirement_text": requirement, "criticality": "critical" if mode in {"mandatory", "prohibited"} else "normal", "requirement_mode": mode})
        return result


class CandidateTruncationDetector:
    def assess(self, text: str, definition_length: int = 0) -> dict[str, Any]:
        signals = []
        if text.count("```") % 2: signals.append("unmatched_fenced_code_block")
        if re.search(r"(?:continued below|to be continued|next (?:I will|section is))\s*[.:]?$", text.strip(), re.I): signals.append("absent_continuation")
        if re.search(r"(?:and|or|including|such as|follows|then)\s*[:;,—-]?\s*$", text.strip(), re.I): signals.append("abrupt_transition_ending")
        if re.search(r"(?m)^\s*\d+[.)]\s+[^\n]*[:;,]\s*$", text): signals.append("unfinished_numbered_section")
        if text.rstrip().endswith(("-", "•")): signals.append("unfinished_bullet")
        if definition_length and len(text) < min(300, definition_length * .05): signals.append("implausibly_short")
        status = "confirmed_truncated" if "unmatched_fenced_code_block" in signals or "absent_continuation" in signals else "likely_truncated" if signals else "not_truncated"
        return {"status": status, "signals": signals}


class CandidateCompletenessEvaluator:
    def __init__(self) -> None: self.truncation = CandidateTruncationDetector()
    def evaluate(self, candidate: dict[str, Any], definition: dict[str, Any], dimensions: list[dict[str, Any]]) -> dict[str, Any]:
        text = candidate["original_text"]; lower = text.lower(); trunc = self.truncation.assess(text, len(definition["content"]))
        required = [d for d in dimensions if d["requirement_mode"] in {"mandatory", "prohibited"}]
        covered, partial, missing, conflicts = [], [], [], []
        for dim in required:
            name = dim["normalized_dimension"]; tokens = [t for t in re.findall(r"[a-z]{4,}", dim["original_heading"].lower()) if t not in {"required", "behavior", "criteria"}]
            hits = sum(token in lower for token in tokens)
            if hits >= max(1, len(tokens) // 2): covered.append(name)
            elif hits: partial.append(name)
            else: missing.append(name)
            if dim["requirement_mode"] == "prohibited" and re.search(r"\b(?:automatically promote|overwrite pending|canonical(?:ly)?)\b", lower) and "not " not in lower:
                conflicts.append(name)
        unsupported = [m.group(0) for m in re.finditer(r"\b(?:fully complete|all requirements (?:are )?met|production ready)\b", text, re.I)] if missing else []
        ratio = len(covered) / max(1, len(required))
        if trunc["status"] != "not_truncated": assessment = "truncated_candidate"
        elif conflicts: assessment = "partial_supporting_document"
        elif not missing and ratio >= .85: assessment = "complete_supporting_document"
        elif ratio >= .65 and not unsupported: assessment = "substantially_complete_review_required"
        else: assessment = "partial_supporting_document"
        disposition = "stage_proposed" if assessment == "complete_supporting_document" and not unsupported else "review_blocked"
        return {"candidate_id": candidate["candidate_id"], "candidate_identifier": candidate["candidate_wp_identifier"], "matching_definition_path": definition["path"], "matching_definition_hash": definition["content_sha256"], "assessment": assessment, "confidence": "high" if assessment in {"complete_supporting_document", "truncated_candidate"} else "medium", "required_dimensions": [d["normalized_dimension"] for d in required], "covered_dimensions": sorted(set(covered)), "partially_covered_dimensions": sorted(set(partial)), "missing_dimensions": sorted(set(missing)), "coverage_score": round(ratio * 100, 2), "prohibited_behavior_conflicts": conflicts, "unsupported_claims": unsupported, "contradiction_findings": conflicts, "truncation_status": trunc["status"], "truncation_signals": trunc["signals"], "review_requirement": True, "preservation_disposition": disposition, "rationale": f"Substantive comparison covered {len(covered)} of {len(required)} mandatory/prohibited dimensions; mandatory omissions and truncation override score."}


class CandidateReconciler:
    def reconcile(self, candidates: list[dict[str, Any]], assessments: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for candidate in candidates: groups.setdefault(candidate["candidate_wp_identifier"], []).append(candidate)
        output = []
        for identifier, items in sorted(groups.items()):
            relations = []; competing = False
            for i, left in enumerate(items):
                for right in items[i + 1:]:
                    ratio = difflib.SequenceMatcher(None, left["normalized_text"], right["normalized_text"]).ratio()
                    kind = "exact_duplicate" if left["candidate_hash"] == right["candidate_hash"] else "formatting_only_duplicate" if _normalized(left["original_text"]).casefold() == _normalized(right["original_text"]).casefold() else "near_duplicate" if ratio >= .85 else "independent_alternative"
                    relations.append({"left": left["candidate_id"], "right": right["candidate_id"], "relationship": kind, "similarity": round(ratio, 4)})
                    if kind == "independent_alternative" and all(assessments.get(x["candidate_id"], {}).get("assessment") == "complete_supporting_document" for x in (left, right)): competing = True
            ranked = sorted(items, key=lambda c: (assessments.get(c["candidate_id"], {}).get("assessment") == "complete_supporting_document", assessments.get(c["candidate_id"], {}).get("truncation_status") == "not_truncated", assessments.get(c["candidate_id"], {}).get("coverage_score", 0), -len(assessments.get(c["candidate_id"], {}).get("unsupported_claims", [])), c["candidate_id"]), reverse=True)
            preferred = ranked[0]["candidate_id"] if ranked and not competing else None
            output.append({"work_package_identifier": identifier, "candidate_ids": sorted(c["candidate_id"] for c in items), "relations": relations, "duplicate_group": any("duplicate" in r["relationship"] for r in relations), "competing_group": competing, "preferred_candidate_id": preferred, "selection_reason": "best authoritative coverage and non-truncated provenance" if preferred else "human selection required for competing complete candidates"})
        return output


class SupportingDocumentRenderer:
    def render(self, run: Path, candidate: dict[str, Any], definition: dict[str, Any], assessment: dict[str, Any], disposition: str) -> dict[str, Any]:
        path = run / "supporting_documents" / f"{candidate['candidate_wp_identifier']}_{candidate['candidate_id']}.md"
        preamble = ["---", f"work_package_id: {candidate['candidate_wp_identifier']}", f"work_package_title: {json.dumps(definition['title'])}", f"authoritative_definition: {definition['path']}", f"authoritative_definition_sha256: {definition['content_sha256']}", f"source_archive: {json.dumps(candidate['source_archive'])}", f"source_conversation: {json.dumps(candidate['conversation_identifier'])}", f"source_message_sequence: {candidate['source_message_sequence']}", f"candidate_sha256: {candidate['candidate_hash']}", f"extraction_timestamp: {candidate['extraction_timestamp']}", f"assessment: {assessment['assessment']}", f"reconciliation_disposition: {disposition}", "review_state: proposed_non_canonical", "canonical: false", "---", "", "> This recovered artifact is non-canonical until explicitly reviewed and approved.", "", candidate["original_text"].replace("\r\n", "\n").replace("\r", "\n")]
        content = "\n".join(preamble).rstrip() + "\n"; _write_atomic(path, content)
        return {"candidate_id": candidate["candidate_id"], "work_package_identifier": candidate["candidate_wp_identifier"], "staging_path": path.relative_to(run).as_posix(), "proposed_destination": f"collaboration/work_packages/specifications/{path.name}", "artifact_sha256": _sha(content), "promotion_status": "blocked_pending_human_review", "canonical": False}


class RuntimeCanonRecoveryPipeline:
    def __init__(self, repository_root: Path, pending_root: Path, output_root: Path) -> None:
        self.repository_root, self.pending_root, self.output_root = repository_root, pending_root, output_root

    def run(self, inputs: list[Path], *, ingestion_root: Path | None = None, identifier_filter: str | None = None, dry_run: bool = False) -> Path:
        ingestion_root = ingestion_root or self.output_root / "ingested"
        bundles = []
        for item in inputs:
            expanded = sorted(p for p in item.iterdir() if p.is_file()) if item.is_dir() and not (item / "manifest.json").exists() else [item]
            for source in expanded:
                bundles.append(source if source.is_dir() and (source / "manifest.json").exists() else ingest(source, ingestion_root, repository_root=self.repository_root))
        manifests = [json.loads((b / "manifest.json").read_text(encoding="utf-8")) for b in bundles]
        input_hashes = sorted(m["source"]["sha256"] for m in manifests); run_id = _sha("\n".join(input_hashes) + SCHEMA_VERSION)[:16]; run = self.output_root / run_id
        index = PendingWorkPackageIndex(self.pending_root).build(); detector = RuntimeCanonCandidateDetector(); decisions = []; messages_count = assistant_count = 0
        for bundle, manifest in sorted(zip(bundles, manifests), key=lambda x: x[1]["source"]["sha256"]):
            records = [json.loads(line) for line in (bundle / "messages.jsonl").read_text(encoding="utf-8").splitlines() if line]
            messages_count += len(records)
            for pos, record in enumerate(records):
                assistant_count += record.get("role") == "assistant"
                decision = detector.detect(record, manifest["source"], records[pos - 1] if pos else None, records[pos + 1] if pos + 1 < len(records) else None)
                if decision and (not identifier_filter or decision["candidate_wp_identifier"] == identifier_filter.upper()): decisions.append(decision)
        candidates = [d for d in decisions if d["detected"]]; matches = []; assessments_list = []; assessment_map = {}; parser = WorkPackageDefinitionParser(); evaluator = CandidateCompletenessEvaluator()
        for candidate in candidates:
            state, definition = index.resolve(candidate["candidate_wp_identifier"])
            matches.append({"candidate_id": candidate["candidate_id"], "candidate_identifier": candidate["candidate_wp_identifier"], "resolution_state": state, "definition_path": definition["path"] if definition else None, "definition_hash": definition["content_sha256"] if definition else None, "likely_causes": [] if state == "matched_unique" else ["typographical number", "work package moved out of pending", "incorrect assistant heading", "named package without approved mapping", "repository inconsistency"]})
            if state == "matched_unique" and definition:
                assessment = evaluator.evaluate(candidate, definition, parser.parse(definition)); assessments_list.append(assessment); assessment_map[candidate["candidate_id"]] = assessment
            else:
                assessment = {"candidate_id": candidate["candidate_id"], "candidate_identifier": candidate["candidate_wp_identifier"], "assessment": "cannot_assess_definition", "preservation_disposition": "blocked", "truncation_status": "cannot_determine", "rationale": f"Definition resolution was {state}."}; assessments_list.append(assessment); assessment_map[candidate["candidate_id"]] = assessment
        reconciliation = CandidateReconciler().reconcile(candidates, assessment_map); manifest_items = []
        definitions = {r["canonical_identifier"]: r for r in index.records if r["canonical_identifier"]}
        for group in reconciliation:
            preferred = group["preferred_candidate_id"]
            if not preferred: continue
            candidate = next(c for c in candidates if c["candidate_id"] == preferred); assessment = assessment_map[preferred]
            if assessment["preservation_disposition"] == "stage_proposed" and not dry_run:
                manifest_items.append(SupportingDocumentRenderer().render(run, candidate, definitions[candidate["candidate_wp_identifier"]], assessment, "preferred_candidate_selected"))
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repository_root, text=True, capture_output=True, check=False).stdout.strip() or "unknown"
        diagnostics = [*index.diagnostics]
        common = {"schema_version": SCHEMA_VERSION, "generator_version": GENERATOR_VERSION, "repository_commit": commit, "run_identifier": run_id, "input_identifiers_and_hashes": [{"path": m["source"]["path"], "sha256": m["source"]["sha256"]} for m in sorted(manifests, key=lambda x: x["source"]["sha256"])], "generated_timestamp": GENERATED_AT, "diagnostic_summary": {"fatal": sum(d["severity"] == "fatal" for d in diagnostics), "review": sum(d["severity"] == "review" for d in diagnostics)}}
        artifacts = {"pending_work_package_index.json": {**common, "records": index.public_records(), "diagnostics": diagnostics}, "runtime_canon_candidates.json": {**common, "decisions": decisions}, "definition_match_report.json": {**common, "matches": matches}, "candidate_assessment_report.json": {**common, "assessments": assessments_list}, "candidate_reconciliation_report.json": {**common, "groups": reconciliation}, "supporting_document_manifest.json": {**common, "artifacts": manifest_items, "automatic_promotion_permitted": False}}
        for name, payload in artifacts.items(): _write_atomic(run / name, json.dumps(payload, indent=2, sort_keys=True) + "\n")
        counts = {"archives_processed": len(bundles), "messages_parsed": messages_count, "assistant_messages_scanned": assistant_count, "candidates_detected": len(candidates), "unique_pending_matches": sum(m["resolution_state"] == "matched_unique" for m in matches), "unmatched_identifiers": sum(m["resolution_state"] != "matched_unique" for m in matches), "complete_candidates": sum(a["assessment"] == "complete_supporting_document" for a in assessments_list), "partial_candidates": sum(a["assessment"] in {"partial_supporting_document", "substantially_complete_review_required"} for a in assessments_list), "truncated_candidates": sum(a.get("assessment") == "truncated_candidate" for a in assessments_list), "duplicate_groups": sum(g["duplicate_group"] for g in reconciliation), "competing_groups": sum(g["competing_group"] for g in reconciliation), "supporting_documents_staged": len(manifest_items), "review_blocks": sum(a.get("preservation_disposition") != "stage_proposed" for a in assessments_list), "fatal_diagnostics": common["diagnostic_summary"]["fatal"]}
        report = ["# Runtime Canon Recovery Report", "", "> Derived non-canonical review material; automatic promotion is prohibited.", "", f"Run: `{run_id}`", "", "## Counts", ""] + [f"- {k}: {v}" for k, v in counts.items()] + ["", "## Candidates", ""] + [f"- `{a['candidate_identifier']}`: **{a['assessment']}** — {a['rationale']}" for a in assessments_list]
        _write_atomic(run / "runtime_canon_recovery_report.md", "\n".join(report) + "\n")
        blocks = ["# Promotion Block Report", "", "> Automatic canonical promotion is prohibited.", ""] + [f"- `{a['candidate_identifier']}`: {a['assessment']}" for a in assessments_list if a.get("preservation_disposition") != "stage_proposed"]
        _write_atomic(run / "promotion_block_report.md", "\n".join(blocks or ["- None beyond mandatory human approval."]) + "\n")
        _write_atomic(run / "summary.json", json.dumps({**counts, "output": str(run), "run_identifier": run_id}, sort_keys=True) + "\n")
        return run


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("inputs", nargs="+", type=Path); parser.add_argument("--repository-root", type=Path, default=Path.cwd()); parser.add_argument("--pending-root", type=Path); parser.add_argument("--output-root", type=Path, default=Path("staging/runtime_canon_recovery")); parser.add_argument("--ingestion-root", type=Path); parser.add_argument("--identifier-filter"); parser.add_argument("--dry-run", action="store_true"); parser.add_argument("--strict", action="store_true"); parser.add_argument("--machine-readable", action="store_true")
    args = parser.parse_args(argv); pending = args.pending_root or args.repository_root / "collaboration/work_packages/pending"
    try: run = RuntimeCanonRecoveryPipeline(args.repository_root, pending, args.output_root).run(args.inputs, ingestion_root=args.ingestion_root, identifier_filter=args.identifier_filter, dry_run=args.dry_run)
    except (OSError, ValueError, json.JSONDecodeError) as exc: print(json.dumps({"fatal_error": str(exc)}, sort_keys=True)); return 3
    summary = json.loads((run / "summary.json").read_text()); print(json.dumps(summary, sort_keys=True) if args.machine_readable else "\n".join(f"{k}: {v}" for k, v in summary.items()))
    return 2 if args.strict and (summary["fatal_diagnostics"] or summary["review_blocks"]) else (3 if summary["fatal_diagnostics"] else 0)


if __name__ == "__main__": raise SystemExit(main())
