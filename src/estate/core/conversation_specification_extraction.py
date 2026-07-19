"""Extract review-only WP specification candidates from WP-4208 bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

from estate.core.conversation_archive_ingestion import _write_atomic, ingest

SCHEMA_VERSION = "estate.conversation-specification-extraction/v1"
WP_HEADING = re.compile(r"(?im)^#{1,6}\s+(WP-(\d{4}))\s*(?:[—–:-]\s*)([^\n#]+)$")
MALFORMED_HEADING = re.compile(r"(?im)^#{1,6}\s+WP\s*[- ]?\s*(\d{1,3}|\d{5,})\b")
PATH = re.compile(r"(?im)^(?:proposed\s+)?destination\s*:\s*`?([^`\n]+)`?\s*$")


class SpecificationError(ValueError):
    """The review bundle does not satisfy its declared extraction contract."""


def parse_expected(value: str) -> list[str]:
    """Parse WP-4107..WP-4116, WP-4107:WP-4116, or a comma list."""
    match = re.fullmatch(r"\s*WP-(\d{4})\s*(?:\.\.|:|through|-)\s*WP-(\d{4})\s*", value, re.I)
    if match:
        start, end = map(int, match.groups())
        if start > end:
            raise SpecificationError("expected range starts after it ends")
        return [f"WP-{number:04d}" for number in range(start, end + 1)]
    values = [item.strip().upper() for item in value.split(",") if item.strip()]
    if not values or any(not re.fullmatch(r"WP-\d{4}", item) for item in values):
        raise SpecificationError("expected must be a bounded WP range or comma-separated WP identifiers")
    return list(dict.fromkeys(values))


def _classify(role: str, plain: str, formatted: str) -> str:
    lower = plain.lower().strip()
    if role == "assistant" and WP_HEADING.search(formatted):
        return "assistant_runtime_canon"
    if role == "user" and lower in {"go", "continue", "proceed"}:
        return "automatic_go"
    if role == "user" and ("steward" in lower or "implement" in lower or "work package" in lower):
        return "steward_instruction"
    if role == "user" and ("startup" in lower or "continuation" in lower or "resume" in lower):
        return "continuation_startup_seed"
    if role == "assistant" and any(word in lower for word in ("complete", "handoff", "ready for review")):
        return "completion_handoff"
    return "unrelated_discussion"


def _destination(repository_root: Path, wp: str, title: str, explicit: str | None) -> tuple[str | None, list[str]]:
    diagnostics: list[str] = []
    if explicit:
        candidate = explicit.strip()
        if candidate.startswith("/") or ".." in Path(candidate).parts:
            return None, ["unsafe_destination"]
        if candidate.startswith("collaboration/work_packages/pending/"):
            return None, ["pending_definition_overwrite"]
        return candidate, diagnostics
    pending = sorted((repository_root / "collaboration/work_packages/pending").glob(f"{wp}_*.md"))
    if len(pending) > 1:
        return None, ["ambiguous_destination"]
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")
    name = pending[0].name if pending else f"{wp}_{slug}.md"
    return f"collaboration/work_packages/specifications/{name}", diagnostics


def extract_specifications(bundle: Path, expected: list[str], output_root: Path, *, repository_root: Path) -> Path:
    """Create a deterministic review bundle; never writes a proposed destination."""
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    records = [json.loads(line) for line in (bundle / "messages.jsonl").read_text(encoding="utf-8").splitlines()]
    run_seed = manifest["source"]["sha256"] + "\n" + ",".join(expected)
    run_id = hashlib.sha256(run_seed.encode()).hexdigest()[:16]
    run_dir = output_root / run_id
    mapped: dict[str, list[dict[str, object]]] = {}
    classifications = []
    diagnostics: list[dict[str, object]] = []
    for record in records:
        formatted = record.get("formatted_text", "")
        kind = _classify(record["role"], record["text"], formatted)
        classifications.append({"sequence": record["sequence"], "source_message_id": record["source_message_id"], "classification": kind})
        if MALFORMED_HEADING.search(formatted):
            diagnostics.append({"code": "malformed_wp_heading", "sequence": record["sequence"]})
        if kind != "assistant_runtime_canon":
            continue
        matches = list(WP_HEADING.finditer(formatted))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(formatted)
            content = formatted[match.start():end].strip() + "\n"
            problems = []
            if content.count("```") % 2:
                problems.append("truncated_assistant_response")
            body = content.split("\n", 1)[1] if "\n" in content else ""
            if body and "\n\n" not in body and not re.search(r"(?m)^(?:[-*] |\| |```|\s{2,}\S)", body):
                problems.append("collapsed_formatting")
            explicit_match = PATH.search(content)
            destination, destination_problems = _destination(repository_root, match.group(1).upper(), match.group(3).strip(), explicit_match.group(1) if explicit_match else None)
            problems.extend(destination_problems)
            item = {"wp_id": match.group(1).upper(), "title": match.group(3).strip(), "content": content,
                    "proposed_destination": destination, "diagnostics": problems,
                    "provenance": {"source_archive_sha256": manifest["source"]["sha256"],
                                   "conversation_location": manifest["source"].get("content_location", ""),
                                   "source_message_id": record["source_message_id"], "source_sequence": record["sequence"],
                                   "extraction_run": run_id, "wp_identifier": match.group(1).upper()}}
            mapped.setdefault(item["wp_id"], []).append(item)
    found = sorted(wp for wp in expected if wp in mapped)
    missing = [wp for wp in expected if wp not in mapped]
    duplicates = sorted(wp for wp in expected if len(mapped.get(wp, [])) > 1)
    unexpected = sorted(wp for wp in mapped if wp not in expected)
    ambiguous = sorted(wp for wp, items in mapped.items() if any(i["diagnostics"] for i in items))
    for wp in missing:
        diagnostics.append({"code": "missing_expected_wp", "wp_id": wp})
    for wp in duplicates:
        diagnostics.append({"code": "duplicate_wp_output", "wp_id": wp})
    candidates = [items[0] for wp, items in sorted(mapped.items()) if wp in expected and len(items) == 1]
    for item in candidates:
        path = run_dir / "candidates" / f"{item['wp_id']}.md"
        _write_atomic(path, item["content"])
        item["staging_artifact"] = str(path.relative_to(run_dir))
        item["content_sha256"] = hashlib.sha256(item["content"].encode()).hexdigest()
        del item["content"]
    report = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "status": "valid" if not missing and not duplicates and not ambiguous and not diagnostics else "review_blocked",
              "canonical_status": "non_canonical_review_material", "expected": expected, "found": found, "missing": missing,
              "duplicates": duplicates, "ambiguous": ambiguous, "unexpected": unexpected, "message_classifications": classifications,
              "candidates": candidates, "diagnostics": diagnostics,
              "source": {"ingestion_bundle": str(bundle), "archive_sha256": manifest["source"]["sha256"]}}
    _write_atomic(run_dir / "validation_report.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    validate_extraction(run_dir)
    return run_dir


def validate_extraction(run_dir: Path) -> dict[str, object]:
    report = json.loads((run_dir / "validation_report.json").read_text())
    if report.get("schema_version") != SCHEMA_VERSION or set(report["expected"]) != set(report["found"] + report["missing"]):
        raise SpecificationError("invalid coverage report")
    for candidate in report["candidates"]:
        destination = candidate.get("proposed_destination") or ""
        if destination.startswith("collaboration/work_packages/pending/"):
            raise SpecificationError("candidate would overwrite a pending definition")
        content = (run_dir / candidate["staging_artifact"]).read_bytes()
        if hashlib.sha256(content).hexdigest() != candidate["content_sha256"]:
            raise SpecificationError("candidate integrity validation failed")
    return {"valid": report["status"] == "valid", "run_id": report["run_id"], "coverage": f"{len(report['found'])}/{len(report['expected'])}"}


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected", required=True, help="e.g. WP-4107..WP-4116 or WP-4127,WP-4128")
    parser.add_argument("--ingestion-root", type=Path, default=Path("ingestion/conversations/derived"))
    parser.add_argument("--output-root", type=Path, default=Path("staging/conversation_specifications"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    bundle = ingest(args.archive, args.ingestion_root, repository_root=args.repository_root)
    run = extract_specifications(bundle, parse_expected(args.expected), args.output_root, repository_root=args.repository_root)
    result = validate_extraction(run)
    print(json.dumps({**result, "output": str(run)}, sort_keys=True))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
