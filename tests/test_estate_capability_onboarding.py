import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from estate.core.work_package_validation import validate_capability_onboarding_package


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/residents/resident_capability_manifest_v1.schema.json"
TEMPLATE = ROOT / "collaboration/work_packages/templates/ESTATE_CAPABILITY_ONBOARDING_IMPLEMENTATION_TEMPLATE.md"


def test_manifest_schema_is_closed_and_validates_complete_manifest():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    record = {
        "schema_version": "resident_capability_manifest_v1",
        "resident_id": "engineering",
        "owner": "Engineering",
        "capabilities": [{
            "capability_id": "engineering.repository_implementation",
            "version": "1.0.0",
            "maturity_level": 3,
            "current_availability": "available",
            "dispatchability": "dispatchable",
            "provider_bindings": [{"binding_kind": "provider", "provider_id": "codex.execution.cli", "adapter_reference": "codex-cli@1.0.0"}],
            "classification_ceiling": "internal",
            "authority": {"authorization_requirements": ["Grace/Helen/PTM/Dispatch"], "prohibited_actions": ["merge"]},
            "accepted_inputs": ["bounded repository task"],
            "accepted_outputs": ["declared artifact"],
            "limitations": ["no merge authority"],
            "evidence": [{"evidence_kind": "qualification", "source_reference": "runtime/helen/assessment.json", "state": "pass", "observed_at": "2026-07-31T00:00:00Z"}],
        }],
    }
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)


def test_manifest_schema_rejects_unknown_nested_authority():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    record = {"schema_version": "resident_capability_manifest_v1", "resident_id": "x", "owner": "X", "capabilities": [], "authority": "bypass"}
    assert list(Draft202012Validator(schema).iter_errors(record))


def test_manifest_schema_rejects_absolute_or_traversing_evidence_reference():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    record = {"schema_version": "resident_capability_manifest_v1", "resident_id": "engineering", "owner": "Engineering", "capabilities": [{"capability_id": "engineering.x", "version": "1.0.0", "maturity_level": 1, "current_availability": "unknown", "dispatchability": "not_dispatchable", "provider_bindings": [{"binding_kind": "resident_tool", "provider_id": "engineering.x", "adapter_reference": "resident-tool:x"}], "classification_ceiling": "internal", "authority": {"authorization_requirements": ["owner"], "prohibited_actions": ["merge"]}, "accepted_inputs": ["request"], "accepted_outputs": ["report"], "limitations": [], "evidence": [{"evidence_kind": "availability", "source_reference": "C:/outside.json", "state": "unknown", "observed_at": "2026-07-31T00:00:00Z"}]}]}
    assert list(Draft202012Validator(schema).iter_errors(record))


def test_onboarding_lint_accepts_canonical_template():
    result = validate_capability_onboarding_package(TEMPLATE)
    assert result["validation_status"] == "passed"
    assert result["missing_sections"] == []


def test_onboarding_lint_fails_incomplete_package(tmp_path):
    path = tmp_path / "incomplete.md"
    path.write_text("# package\nOwner: Engineering\n", encoding="utf-8")
    result = validate_capability_onboarding_package(path)
    assert result["validation_status"] == "failed"
    assert "scopes" in result["missing_sections"]


def test_onboarding_lint_rejects_placeholders_in_non_template(tmp_path):
    path = tmp_path / "package.md"
    path.write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    result = validate_capability_onboarding_package(path)
    assert result["validation_status"] == "failed"
    assert any(error["type"] == "unresolved_placeholders" for error in result["errors"])
