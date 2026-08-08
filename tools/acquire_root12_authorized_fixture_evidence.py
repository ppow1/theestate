"""Acquire the one Steward-authorized deterministic fixture evidence read."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"A:\theestate")
FIXTURE = ROOT / "Temp" / "cme-execution-fixtures" / "full-loop-20260807" / "fixture.json"
INVARIANT = FIXTURE.with_name("INVARIANT.md")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    # This operation is deliberately exact-scope: no discovery and no writes
    # to the fixture or repository are permitted.
    fixture_text = FIXTURE.read_text(encoding="utf-8")
    invariant_text = INVARIANT.read_text(encoding="utf-8")
    fixture = json.loads(fixture_text)
    required = {"actual", "expected", "name", "status"}
    if set(fixture) != required:
        raise ValueError("fixture_schema_changed")
    expected_valid = fixture["actual"] == fixture["expected"] and fixture["status"] == "valid"
    receipt = {
        "schema": "estate.authorized.fixture.evidence.v1",
        "acquisition_type": "bounded_read_only_fixture_evidence",
        "acquired_at": now(),
        "authorization": {
            "actor": "Steward",
            "decision": "ONE additional bounded READ-ONLY fixture-evidence acquisition",
            "escalation_id": "esc-cc905d159a554863",
        },
        "lineage": {
            "consultation_root": "12.00",
            "current_turn": "12.03",
            "execution_request_id": "exec-f16799a5439b",
            "reasoning_result": "MORE_REASONING_REQUIRED",
        },
        "source": {
            "fixture_path": str(FIXTURE),
            "invariant_path": str(INVARIANT),
            "fixture_sha256": __import__("hashlib").sha256(fixture_text.encode("utf-8")).hexdigest(),
            "invariant_sha256": __import__("hashlib").sha256(invariant_text.encode("utf-8")).hexdigest(),
            "fixture_content": fixture,
            "invariant_text": invariant_text.strip(),
        },
        "expected": {
            "invariant": "fixture.json is valid only when actual equals expected and status is valid",
            "fields": {"actual": fixture["expected"], "expected": fixture["expected"], "status": "valid"},
        },
        "observed": {"fields": fixture},
        "comparison": {
            "actual_equals_expected": fixture["actual"] == fixture["expected"],
            "status_is_valid": fixture["status"] == "valid",
            "equal": expected_valid,
            "result": "PASS" if expected_valid else "FAIL",
        },
        "scope_assertion": {
            "read_paths": [str(FIXTURE), str(INVARIANT)],
            "write_paths": [str(args.output)],
            "fixture_modified": False,
            "execution_launched": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
