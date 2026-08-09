from pathlib import Path

import pytest

from estate.core.estate_population import (
    PopulationScopeError,
    _relative,
    _within_requested,
    load_scope,
    resolve_entry,
    validate_requested_scope,
)


ROOT = Path(__file__).resolve().parents[1]


def test_governed_scope_contract_has_explicit_sensitive_policies():
    scope = load_scope(ROOT)
    assert scope["scope_id"] == "ESTATE.REPOSITORY.GOVERNED.V1"
    policies = {entry["pattern"]: entry["policy"] for entry in scope["entries"]}
    assert policies["runtime"] == "EXCLUDED"
    assert policies["data"] == "METADATA_ONLY"
    assert policies["archive"] == "NO_CONTENT"
    assert policies["src"] == "STRUCTURAL_SCAN"
    assert resolve_entry(scope, "docs/operations/troubleshooting/generated/index.html")["policy"] == "EXCLUDED"


@pytest.mark.parametrize("value", ["C:\\", "A:\\other-project", "../other", "src/../../other"])
def test_scope_path_escape_fails_closed(value):
    with pytest.raises(PopulationScopeError):
        _relative(value)


def test_requested_scope_must_be_admitted_and_repository_root_is_verified():
    context = validate_requested_scope(ROOT, "src/estate/diagnostics")
    assert context["scope_id"] == "ESTATE.REPOSITORY.GOVERNED.V1"
    with pytest.raises(PopulationScopeError):
        validate_requested_scope(ROOT, "runtime")
    with pytest.raises(PopulationScopeError):
        validate_requested_scope(ROOT, "not-an-admitted-sibling")


def test_bounded_missing_detection_does_not_cross_requested_scope():
    assert _within_requested("src/estate/core/worker.py", "src/estate/core")
    assert not _within_requested("docs/README.md", "src/estate/core")
    assert _within_requested("docs/README.md", None)
