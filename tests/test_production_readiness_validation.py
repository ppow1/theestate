import json
from pathlib import Path

from estate.core.production_readiness_validation import (
    calculate_production_readiness,
    generate_production_readiness_report,
    generate_validation_coverage_manifest,
    validate_receipt,
)
from estate.core.work_package_validation import get_validation_recipe


def write_json(root: Path, rel: str, data: dict):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data), encoding="utf-8")


def complete_receipt(wp="WP-0001"):
    return {
        "work_package_id": wp,
        "codex_status": "done",
        "completed_at": "2026-07-04T00:00:00+00:00",
        "branch": "work",
        "pull_request_url": "https://example.invalid/pr/1",
        "summary": ["done"],
        "files_changed": ["src/example.py"],
        "tests_run": ["pytest"],
        "known_limitations": [],
        "ready_for_ca_review": True,
        "merge_authority": "ca_verified_auto_merge_allowed",
    }


def test_completion_artifact_receipt_parsing_and_complete_status(tmp_path):
    write_json(tmp_path, "collaboration/work_packages/completions/WP-0001_codex_done.json", complete_receipt())
    receipt = validate_receipt("WP-0001", tmp_path)
    assert receipt["receipt_status"] == "complete"
    assert receipt["completion_artifact_path"].endswith("WP-0001_codex_done.json")


def test_missing_and_incomplete_completion_artifacts(tmp_path):
    assert validate_receipt("WP-0002", tmp_path)["receipt_status"] == "missing"
    data = complete_receipt("WP-0003")
    del data["tests_run"]
    write_json(tmp_path, "collaboration/work_packages/completions/WP-0003_codex_done.json", data)
    receipt = validate_receipt("WP-0003", tmp_path)
    assert receipt["receipt_status"] == "incomplete"
    assert "tests_run" in receipt["receipt_gaps"]


def test_production_readiness_rules():
    receipt = {"receipt_status": "complete", "blocking_reasons": [], "non_blocking_findings": ["local PR metadata unavailable"]}
    assert calculate_production_readiness("passed", receipt)["production_ready"] is True
    assert calculate_production_readiness("failed", receipt)["production_ready"] is False
    assert calculate_production_readiness("no_recipe", receipt)["production_ready"] is False
    missing = {"receipt_status": "missing", "blocking_reasons": ["missing"], "non_blocking_findings": []}
    assert calculate_production_readiness("passed", missing)["production_ready"] is False


def test_manifest_and_report_generation_handle_legacy_artifacts(tmp_path):
    write_json(tmp_path, "collaboration/work_packages/completions/WP-0004_legacy.json", {"legacy": True})
    write_json(tmp_path, "collaboration/work_packages/completions/WP-0005_codex_done.json", complete_receipt("WP-0005"))
    write_json(tmp_path, "runtime/validation/work_packages/WP-0005_validation.json", {"validation_status": "passed"})
    manifest = generate_validation_coverage_manifest(tmp_path, write=True)
    assert (tmp_path / "runtime/validation/validation_coverage_manifest.json").exists()
    assert any(e["work_package_id"] == "WP-0004" and e["receipt_status"] == "incomplete" for e in manifest["work_packages"])
    report = generate_production_readiness_report(tmp_path, write=True)
    assert report["total_work_packages_scanned"] >= 2
    assert (tmp_path / "operations/validation/production_readiness_report.md").exists()


def test_wp_0095_recipe_registered():
    assert get_validation_recipe("WP-0095") is not None


def test_wp_0102_receipt_complete_with_not_applicable_pull_request_metadata(tmp_path):
    data = complete_receipt("WP-0102")
    data.pop("pull_request_url")
    data["pull_request_not_applicable_reason"] = "Local-only validation repair awaiting harness PR creation."
    write_json(tmp_path, "collaboration/work_packages/completions/WP-0102_codex_done.json", data)
    receipt = validate_receipt("WP-0102", tmp_path)
    assert receipt["receipt_status"] == "complete"
    assert receipt["receipt_gaps"] == []


def test_wp_0103_non_blocking_scoped_boundary_receipt_complete(tmp_path):
    data = complete_receipt("WP-0103")
    data["known_limitations"] = []
    data["non_blocking_known_limitations"] = ["WP-0086 and later pending backlog files were intentionally outside WP-0103 scope."]
    write_json(tmp_path, "collaboration/work_packages/completions/WP-0103_codex_done.json", data)
    receipt = validate_receipt("WP-0103", tmp_path)
    readiness = calculate_production_readiness("passed", receipt)
    assert receipt["receipt_status"] == "complete"
    assert readiness["production_ready"] is True


def test_production_readiness_report_generation_for_wp_0102_and_wp_0103(tmp_path):
    for wp in ("WP-0102", "WP-0103"):
        write_json(tmp_path, f"collaboration/work_packages/completions/{wp}_codex_done.json", complete_receipt(wp))
        write_json(tmp_path, f"runtime/validation/work_packages/{wp}_validation.json", {"validation_status": "passed"})
    report = generate_production_readiness_report(tmp_path, write=True)
    ready = {entry["work_package_id"] for entry in report["ready_for_chief_architect_production_readiness_acceptance"]}
    assert "WP-0102" in ready
    assert "WP-0103" in ready
