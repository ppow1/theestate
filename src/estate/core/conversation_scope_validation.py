"""WP-4211 deterministic Steward-scope and runtime-canon review validator."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

from estate.core.conversation_archive_ingestion import _write_atomic, ingest

SCHEMA_VERSION = "estate.conversation-scope-validation/v1"
RANGE = re.compile(r"\bWP[- ](\d{4})\s*(?:\.\.|through|to|[-–—:])\s*(?:WP[- ]?)?(\d{4})\b", re.I)
WP = re.compile(r"\bWP[- ](\d{4})\b", re.I)
NAMED_WP = re.compile(r"\bWP-[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+\b")
CANON_HEADING = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*|\*{1,2}\s*|(?:work\s+package|runtime\s+canon)\s*[:#-]?\s*)?"
    r"(WP[- ]\d{4})\b(?:\s*\*{1,2})?(?:\s*[-–—:]|\s*$)"
)
CORRECTION = re.compile(r"\b(correct(?:ion|ed)?|instead|supersed(?:e|es|ed)|replace|not\s+WP|scope\s+is|reassign)\b", re.I)
GO = re.compile(r"^\s*(?:go|continue|proceed|execute)(?:\s+(?:now|it|the assignment))?[.!]?\s*$", re.I)
CLAIM = re.compile(r"\b(complete(?:d)?|all\s+done|ready\s+for\s+review|stop\s+condition|nothing\s+(?:else|remains)|assignment\s+is\s+complete)\b", re.I)
REFUSAL = re.compile(r"\b(?:cannot|can't|will not|won't|unable to|need (?:you|confirmation)|before I (?:can|continue)|not (?:yet )?proceed)\b", re.I)


def _ids(text: str) -> list[str]:
    result: list[str] = []
    occupied: list[tuple[int, int]] = []
    for match in RANGE.finditer(text):
        start, end = map(int, match.groups())
        if start <= end and end - start <= 500:
            result.extend(f"WP-{number:04d}" for number in range(start, end + 1))
            occupied.append(match.span())
    for match in WP.finditer(text):
        if not any(a <= match.start() < b for a, b in occupied):
            result.append(f"WP-{int(match.group(1)):04d}")
    result.extend(match.group(0) for match in NAMED_WP.finditer(text))
    return list(dict.fromkeys(result))


def _corrected_ids(text: str, fallback: list[str]) -> list[str]:
    """Use the final bounded declaration in a correction, not the rejected old range."""
    ranges = list(RANGE.finditer(text))
    if not ranges:
        return fallback
    match = ranges[-1]
    start, end = map(int, match.groups())
    if start > end:
        return fallback
    corrected = [f"WP-{number:04d}" for number in range(start, end + 1)]
    corrected.extend(wp_id for wp_id in fallback if not WP.fullmatch(wp_id))
    return list(dict.fromkeys(corrected))


def validate_scope(bundle: Path, output_root: Path) -> Path:
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    records = [json.loads(line) for line in (bundle / "messages.jsonl").read_text(encoding="utf-8").splitlines()]
    run_id = hashlib.sha256((manifest["source"]["sha256"] + "\nWP-4211\n" + SCHEMA_VERSION).encode()).hexdigest()[:16]
    run = output_root / run_id
    scope: list[str] = []
    timeline: list[dict[str, object]] = []
    execution: list[dict[str, object]] = []
    diagnostics: list[dict[str, object]] = []
    produced: set[str] = set()
    go_since_output: list[int] = []

    def diag(code: str, sequence: int, explanation: str, **extra: object) -> None:
        diagnostics.append({"code": code, "severity": "review_blocking", "sequence": sequence,
                            "explanation": explanation, **extra})

    for record in records:
        sequence, role = record["sequence"], record["role"]
        plain, formatted = record["text"], record.get("formatted_text", record["text"])
        mentioned = _ids(plain)
        provenance = {"source_message_id": record.get("source_message_id"), "source_sequence": sequence,
                      "message_sha256": record["text_sha256"], **record.get("provenance", {})}
        if role == "user" and mentioned:
            corrected = bool(CORRECTION.search(plain))
            if corrected:
                mentioned = _corrected_ids(plain, mentioned)
            previous = list(scope)
            # A bounded Steward statement is authoritative; correction language makes supersession explicit.
            scope = mentioned
            superseded = next(
                (event["sequence"] for event in reversed(timeline)
                 if event["event"] in {"scope_assignment", "scope_correction"}),
                None,
            )
            timeline.append({"event": "scope_correction" if corrected else "scope_assignment",
                             "sequence": sequence, "previous_scope": previous, "active_scope": scope,
                             "supersedes_sequence": superseded if corrected else None,
                             "authority": "steward", "provenance": provenance})
        elif role == "assistant" and mentioned and scope and ("scope" in plain.lower() or "assign" in plain.lower()):
            accurate = set(mentioned) == set(scope)
            timeline.append({"event": "assistant_restatement", "sequence": sequence,
                             "stated_scope": mentioned, "active_scope": list(scope), "authoritative": False,
                             "accurate": accurate, "provenance": provenance})
            if not accurate:
                diag("contradictory_assistant_scope_statement", sequence,
                     "Assistant scope restatement contradicts the active Steward assignment.",
                     stated_scope=mentioned, active_scope=list(scope))
                if timeline and any(e["event"] == "scope_correction" for e in timeline):
                    diag("ignored_scope_correction", sequence,
                         "Assistant continued to state a scope superseded by an explicit Steward correction.",
                         stated_scope=mentioned, active_scope=list(scope))
        if role == "user" and GO.fullmatch(plain):
            if go_since_output:
                diag("repeated_go_without_expected_output", sequence,
                     "A repeated go command followed no in-scope runtime-canon production.",
                     previous_go_sequence=go_since_output[-1], active_scope=list(scope))
            go_since_output.append(sequence)
            execution.append({"event": "go_command", "sequence": sequence, "active_scope": list(scope), "provenance": provenance})
        if role == "assistant":
            heading_matches = list(CANON_HEADING.finditer(formatted))
            headings = [f"WP-{int(m.group(1).replace(' ', '-').split('-')[1]):04d}" for m in heading_matches]
            for heading_index, (wp_id, heading_match) in enumerate(zip(headings, heading_matches)):
                in_scope = wp_id in scope
                execution.append({"event": "runtime_canon", "sequence": sequence, "wp_id": wp_id,
                                  "active_scope": list(scope), "in_scope": in_scope, "provenance": provenance})
                produced.add(wp_id)
                if in_scope:
                    go_since_output.clear()
                else:
                    diag("out_of_scope_runtime_canon", sequence,
                         "Runtime canon was produced outside the active Steward scope.", wp_id=wp_id, active_scope=list(scope))
                    diag("unexpected_work_package", sequence,
                         "A runtime-canon work package was not expected by the active assignment.", wp_id=wp_id)
                    diag("assignment_scope_violation", sequence,
                         "Runtime-canon generation violated the authoritative Steward assignment.",
                         wp_id=wp_id, active_scope=list(scope))
                section_end = heading_matches[heading_index + 1].start() if heading_index + 1 < len(heading_matches) else len(formatted)
                trailing_text = formatted[heading_match.end():section_end]
                if heading_index == len(headings) - 1 and len(re.findall(r"\b\w+\b", trailing_text)) < 20:
                    execution[-1]["completeness"] = "incomplete_or_truncated"
                    diag("incomplete_or_truncated_runtime_canon", sequence,
                         "The final detected runtime canon has insufficient body content and may be truncated.",
                         wp_id=wp_id)
            if REFUSAL.search(plain) and go_since_output:
                diag("execution_refusal_after_go", sequence,
                     "Assistant refused or deferred execution after an explicit go command.", active_scope=list(scope))
            if CLAIM.search(plain):
                missing_now = sorted(set(scope) - produced)
                if missing_now:
                    diag("unsupported_completion_or_stop_claim", sequence,
                         "Completion or stop-condition claim is unsupported while assigned packages are missing.",
                         missing=missing_now)
                    if re.search(r"\bstop\s+condition\b", plain, re.I):
                        diag("stale_or_invalid_stop_condition", sequence,
                             "Stop-condition reasoning is invalid while the active corrected scope remains unproduced.",
                             missing=missing_now, active_scope=list(scope))

    final_scope = list(scope)
    missing = sorted(set(final_scope) - produced)
    unexpected = sorted(produced - set(final_scope))
    for wp_id in missing:
        diag("missing_expected_work_package", records[-1]["sequence"] if records else 0,
             "The final superseding Steward assignment has no detected runtime canon.", wp_id=wp_id)
    status = "review_blocked" if diagnostics else "review_required"
    message_provenance = [
        {"source_message_id": record.get("source_message_id"), "source_sequence": record["sequence"],
         "message_sha256": record["text_sha256"], **record.get("provenance", {})}
        for record in records
    ]
    common = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "status": status,
              "canonical_status": "non_canonical_review_material", "promotion_permitted": False,
              "source": {"ingestion_bundle": str(bundle), "source_sha256": manifest["source"]["sha256"]},
              "source_message_provenance": message_provenance}
    artifacts = {
        "scope_timeline.json": {**common, "final_scope": final_scope, "events": timeline},
        "execution_timeline.json": {**common, "events": execution},
        "scope_validation_report.json": {**common, "expected": final_scope,
                                         "found_expected": sorted(produced & set(final_scope)),
                                         "produced": sorted(produced),
                                         "missing": missing, "unexpected": unexpected,
                                         "review_blocking_count": len(diagnostics)},
        "conversation_diagnostics.json": {**common, "diagnostics": diagnostics},
    }
    for name, payload in artifacts.items():
        _write_atomic(run / name, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    codes = sorted({item["code"] for item in diagnostics})
    markdown = ["# Conversation Promotion Block Report", "", f"Status: **{status}**", "",
                "> Non-canonical review material. Automatic promotion is prohibited.", "",
                f"Source SHA-256: `{manifest['source']['sha256']}`", f"Run: `{run_id}`", "",
                "## Source-message provenance", ""]
    markdown += [f"- Sequence {item['source_sequence']}: `{item['message_sha256']}`" for item in message_provenance]
    markdown += ["",
                "## Review-blocking diagnostics", ""]
    markdown += [f"- `{code}`" for code in codes] or ["- None detected; human review remains required."]
    _write_atomic(run / "promotion_block_report.md", "\n".join(markdown) + "\n")
    return run


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("conversation", type=Path)
    parser.add_argument("--ingestion-root", type=Path, default=Path("ingestion/conversations/derived"))
    parser.add_argument("--output-root", type=Path, default=Path("staging/conversation_scope_validation"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    bundle = ingest(args.conversation, args.ingestion_root, repository_root=args.repository_root)
    run = validate_scope(bundle, args.output_root)
    report = json.loads((run / "scope_validation_report.json").read_text())
    print(json.dumps({"output": str(run), "status": report["status"], "run_id": report["run_id"]}, sort_keys=True))
    return 2 if report["status"] == "review_blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
