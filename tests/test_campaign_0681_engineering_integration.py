from copy import deepcopy

from estate.core.campaign_momentum_observer import project_engineering_operations

NOW = "2026-07-18T12:00:00Z"


def signal(work_id, state, source_kind="work_package_record", reference=None, **extra):
    value = {
        "work_id": work_id,
        "state": state,
        "source_kind": source_kind,
        "reference": reference or f"collaboration/evidence/{work_id}-{state}.json",
        "effective_at": NOW,
    }
    value.update(extra)
    return value


def states(result):
    return {item["work_id"]: item["observed_state"] for item in result["work"]}


def test_projects_required_engineering_states_and_capacity():
    records = [
        signal("WP-A", "queued"),
        signal("WP-B", "active", "dispatch_record", lane="implementation-1", owner="Engineering"),
        signal("WP-C", "blocked"),
        signal("WP-D", "validating", "validation_record"),
        signal("WP-E", "accepted", "protected_acceptance"),
        signal("WP-F", "paused", "review_record"),
        signal("WP-G", "abandoned", "protected_abandonment"),
    ]
    result = project_engineering_operations(records, observed_at=NOW)
    assert states(result) == {
        "WP-A": "queued", "WP-B": "active", "WP-C": "blocked",
        "WP-D": "validating", "WP-E": "accepted", "WP-F": "paused",
        "WP-G": "abandoned",
    }
    assert result["capacity"] == {
        "active_work_count": 1, "queued_work_count": 1, "blocked_work_count": 1,
        "active_implementation_lanes": ["implementation-1"],
        "capacity_limit": None, "capacity_limit_known": False,
    }


def test_acceptance_requires_protected_record_and_outranks_runtime_claim():
    result = project_engineering_operations([
        signal("WP-A", "active", "runtime_claim", reference="runtime/status.json"),
        signal("WP-A", "accepted", "protected_acceptance", reference="collaboration/acceptance/WP-A.md"),
    ], observed_at=NOW)
    item = result["work"][0]
    assert item["observed_state"] == "accepted"
    assert item["confidence"] == "high"
    assert item["authorizes_action"] is False
    assert item["derived_view_only"] is True


def test_stale_undated_future_and_conflicting_signals_fail_closed():
    result = project_engineering_operations([
        signal("WP-A", "active", effective_at="2026-07-16T12:00:00Z"),
        signal("WP-B", "active", "dispatch_record", reference="one"),
        signal("WP-B", "blocked", "dispatch_record", reference="two"),
        signal("WP-C", "active", effective_at=None),
        signal("WP-D", "active", effective_at="2026-07-19T12:00:00Z"),
    ], observed_at=NOW)
    assert states(result) == {"WP-A": "indeterminate", "WP-B": "indeterminate", "WP-C": "indeterminate", "WP-D": "indeterminate"}
    assert set(result["limiting_dependencies"]) == {"WP-A", "WP-B", "WP-C", "WP-D"}


def test_missing_reference_unknown_source_and_identifier_fail_closed():
    no_reference = signal("WP-A", "active")
    no_reference["reference"] = ""
    result = project_engineering_operations([
        no_reference,
        signal("WP-B", "active", "dashboard"),
        signal("", "active"),
    ], observed_at=NOW)
    assert all(item["observed_state"] == "indeterminate" for item in result["work"])
    assert result["warnings"]


def test_projection_is_deterministic_and_does_not_mutate_signals():
    records = [signal("WP-B", "running", "dispatch_record"), signal("WP-A", "validation", "validation_record")]
    before = deepcopy(records)
    first = project_engineering_operations(records, observed_at=NOW)
    second = project_engineering_operations(reversed(records), observed_at=NOW)
    assert first == second
    assert records == before
    assert first["authority_notice"].startswith("Engineering governance")
