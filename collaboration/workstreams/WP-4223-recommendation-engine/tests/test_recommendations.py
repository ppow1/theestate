from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from recommendation_engine import RecommendationError, compare, explain, recommend, validate_inputs


def fixture(name="healthy_campaign"):
    return json.loads((ROOT / "fixtures" / f"{name}.json").read_text())


def test_deterministic_repeated_execution_and_input_immutability():
    source = fixture(); before = copy.deepcopy(source)
    first = recommend(source)
    assert first == recommend(source)
    assert source == before
    assert first["deterministic_content_hash"] == recommend(copy.deepcopy(source))["deterministic_content_hash"]


def test_all_sets_are_present_and_explain_has_provenance():
    result = recommend(fixture())
    assert len(result["recommendation_sets"]) == 10
    item = explain(result, "highest_value_next_work:WP-FAST")
    assert item["provenance"]["queue_generation_identifier"] == "fixture-gen"
    assert item["score"] == sum(part["value"] for part in item["score_components"])


def test_tie_breaking_and_compare_are_stable():
    data = fixture("healthy_campaign")
    ranked = recommend(data)["recommendation_sets"]["highest_value_next_work"]
    # Equal-score parallel members use their identifiers, never input order.
    assert [x["item_identifiers"][0] for x in ranked[1:]] == ["WP-PAR-A", "WP-PAR-B"]
    result = recommend(data)
    value = compare(result, "highest_value_next_work:WP-PAR-B", "highest_value_next_work:WP-PAR-A")
    assert value["higher_ranked"] == "highest_value_next_work:WP-PAR-A"


def test_degraded_optional_providers_do_not_block_advice():
    data = fixture(); data["health"] = "degraded"; data["degradation_reasons"] = ["wp4214_duration:artifact_not_found"]
    data["provider_payloads"] = {}
    result = recommend(data)
    assert result["provider_health"] == "degraded"
    assert result["diagnostics"] == ["wp4214_duration:artifact_not_found"]


def test_missing_duration_excludes_quick_win_but_not_next_work():
    data = fixture(); data["provider_payloads"] = {}
    result = recommend(data)["recommendation_sets"]
    assert result["quick_wins"] == []
    assert result["highest_value_next_work"]


def test_missing_git_readiness_is_explicit_score_component():
    data = fixture(); data["dashboard_snapshot"]["panels"]["execution_queue"]["records"][0]["git_readiness_reference"] = None
    item = explain(recommend(data), "highest_value_next_work:WP-FAST")
    assert any(x["rule"] == "missing_git" and x["value"] == -5 for x in item["score_components"])


@pytest.mark.parametrize("value,message", [({}, "unsupported integration"), ({"integration_schema_version":"estate.engineering-dashboard-integration/v1","dashboard_snapshot":{}}, "unsupported snapshot")])
def test_malformed_queue_and_unsupported_versions(value, message):
    assert any(message in error for error in validate_inputs(value))
    with pytest.raises(RecommendationError): recommend(value)


def test_duplicate_identifier_is_malformed():
    data = fixture(); rows = data["dashboard_snapshot"]["panels"]["execution_queue"]["records"]; rows.append(copy.deepcopy(rows[0]))
    assert "duplicate item_identifier" in ";".join(validate_inputs(data))


@pytest.mark.parametrize("name", ["healthy_campaign", "blocked_campaign", "dependency_cycle", "merge_heavy_campaign", "validation_heavy_campaign", "empty_queue", "stale_queue", "conflicting_priorities"])
def test_representative_fixtures_validate_and_execute(name):
    assert not validate_inputs(fixture(name))
    assert recommend(fixture(name))["advisory_only"] is True


def test_parallel_group_is_advisory_group_not_assignment():
    groups = recommend(fixture())["recommendation_sets"]["parallel_work_groups"]
    assert groups[0]["item_identifiers"] == ["WP-PAR-A", "WP-PAR-B"]
    assert "assignee" not in json.dumps(groups)


def test_cli_recommend_explain_compare_validate():
    path = ROOT / "fixtures" / "healthy_campaign.json"
    commands = [
        ["validate"], ["recommend"], ["explain", "highest_value_next_work:WP-FAST"],
        ["compare", "highest_value_next_work:WP-PAR-A", "highest_value_next_work:WP-PAR-B"],
    ]
    for parts in commands:
        completed = subprocess.run([sys.executable, str(ROOT / "recommend.py"), parts[0], str(path), *parts[1:]], capture_output=True, text=True)
        assert completed.returncode == 0, completed.stderr
        json.loads(completed.stdout)


def test_existing_wp4222_snapshot_is_consumed_without_duplication():
    integration = json.loads((ROOT.parents[0] / "WP-4222/examples/integration_snapshot_v1.json").read_text())
    assert recommend(integration)["source_integration_hash"] == integration["deterministic_content_hash"]
