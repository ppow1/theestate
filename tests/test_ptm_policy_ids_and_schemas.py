import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from estate.core.ptm_ids import ULID_ALPHABET, is_valid_ptm_id, new_ptm_id, new_ulid
from estate.core.ptm_policy import (
    POLICY_PATH,
    POLICY_SCHEMA_PATH,
    evaluate_evidence,
    load_freshness_policy,
)
from estate.core.ptm_production_readiness import (
    PtmReadinessError,
    append_ptm_event,
    digest,
)
from estate.core.ptm_waiver_authority import (
    REGISTRY_PATH,
    REGISTRY_SCHEMA_PATH,
    load_waiver_registry,
    validate_waiver_authority,
)


ROOT = Path(__file__).parents[1]
NOW = "2026-07-31T12:00:00Z"


def _schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_waiver(registry: dict, **overrides: object) -> dict:
    value = {
        "waiver_id": "waiver_01",
        "granting_authority": "steward",
        "waiver_type": "dependency",
        "scope": {"objective_id": "obj-1", "package_id": "pkg-1", "task_id": "task-1"},
        "reason": "bounded test waiver",
        "granted_at": NOW,
        "expires_at": "2026-07-31T13:00:00Z",
        "authority_registry_id": registry["registry_id"],
        "authority_registry_version": registry["registry_version"],
        "authority_registry_digest": registry["registry_digest"],
    }
    value.update(overrides)
    return value


def test_canonical_policy_and_registry_are_closed_draft_2020_12_records():
    policy = load_freshness_policy(ROOT, observed_at=NOW)
    registry = load_waiver_registry(ROOT, observed_at=NOW)
    for record, schema_path in (
        (policy, ROOT / POLICY_SCHEMA_PATH),
        (registry, ROOT / REGISTRY_SCHEMA_PATH),
    ):
        schema = _schema(schema_path)
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)


def test_policy_digest_is_stable_and_binds_policy_identity():
    first = load_freshness_policy(ROOT, observed_at=NOW)
    second = load_freshness_policy(ROOT, observed_at=NOW)
    assert first["policy_digest"] == second["policy_digest"]
    unsigned = dict(first)
    unsigned.pop("policy_digest")
    assert first["policy_digest"] == digest(unsigned)
    assert first["policy_id"] == "ptm-readiness-freshness-v1"
    assert first["policy_version"] == "1.0.0"


@pytest.mark.parametrize(
    ("evidence_class", "expected_age"),
    [
        ("capability_or_availability", 900),
        ("capacity", 900),
        ("provider_health", 300),
        ("current_authorization", 900),
        ("readiness_gate", 300),
    ],
)
def test_policy_evidence_classes_enforce_declared_age(evidence_class, expected_age):
    policy = load_freshness_policy(ROOT, observed_at=NOW)
    assert policy["evidence_classes"][evidence_class]["maximum_age_seconds"] == expected_age
    evidence = {"observed_at": "2026-07-31T11:00:00Z"}
    assert evaluate_evidence(policy, evidence, evidence_class=evidence_class, observed_at=NOW)


def test_accepted_completion_has_no_automatic_elapsed_expiry_but_missing_timestamp_fails_closed():
    policy = load_freshness_policy(ROOT, observed_at=NOW)
    fresh = {"observed_at": "2020-01-01T00:00:00Z"}
    assert evaluate_evidence(policy, fresh, evidence_class="accepted_dependency_completion", observed_at=NOW) == []
    assert evaluate_evidence(policy, {}, evidence_class="accepted_dependency_completion", observed_at=NOW)


def test_policy_rejects_missing_malformed_unknown_and_future_records(tmp_path):
    with pytest.raises(PtmReadinessError, match="missing or malformed"):
        load_freshness_policy(tmp_path, observed_at=NOW)
    (tmp_path / POLICY_PATH).parent.mkdir(parents=True)
    (tmp_path / POLICY_SCHEMA_PATH).parent.mkdir(parents=True)
    (tmp_path / POLICY_PATH).write_text("{}", encoding="utf-8")
    (tmp_path / POLICY_SCHEMA_PATH).write_text((ROOT / POLICY_SCHEMA_PATH).read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(PtmReadinessError, match="schema invalid"):
        load_freshness_policy(tmp_path, observed_at=NOW)
    future = json.loads((ROOT / POLICY_PATH).read_text(encoding="utf-8"))
    future["effective_at"] = "2027-01-01T00:00:00Z"
    (tmp_path / POLICY_PATH).write_text(json.dumps(future), encoding="utf-8")
    with pytest.raises(PtmReadinessError, match="not yet effective"):
        load_freshness_policy(tmp_path, observed_at=NOW)


def test_waiver_authority_accepts_steward_and_rejects_undelegated_or_broad_authority():
    registry = load_waiver_registry(ROOT, observed_at=NOW)
    assert validate_waiver_authority(registry, _valid_waiver(registry), objective_id="obj-1", package_id="pkg-1", task_id="task-1", observed_at=NOW) == []
    revoked = _valid_waiver(registry, granting_authority="chief-architect-delegation")
    assert validate_waiver_authority(registry, revoked, objective_id="obj-1", package_id="pkg-1", task_id="task-1", observed_at=NOW)
    broad = _valid_waiver(registry, scope={"objective_id": "*", "package_id": "*", "task_id": "*"})
    assert validate_waiver_authority(registry, broad, objective_id="obj-1", package_id="pkg-1", task_id="task-1", observed_at=NOW)


def test_waiver_expiry_and_registry_digest_drift_fail_closed():
    registry = load_waiver_registry(ROOT, observed_at=NOW)
    too_long = _valid_waiver(registry, expires_at="2026-08-02T13:00:00Z")
    assert validate_waiver_authority(registry, too_long, objective_id="obj-1", package_id="pkg-1", task_id="task-1", observed_at=NOW)
    drifted = copy.deepcopy(registry)
    drifted["registry_digest"] = "0" * 64
    assert validate_waiver_authority(drifted, _valid_waiver(registry), objective_id="obj-1", package_id="pkg-1", task_id="task-1", observed_at=NOW)


def test_shared_ids_are_crockford_ulids_timestamped_and_monotonic():
    values = [new_ulid(now_ms=1_000) for _ in range(100)]
    assert len(set(values)) == len(values)
    assert all(len(value) == 26 and set(value) <= set(ULID_ALPHABET) for value in values)
    assert values == sorted(values)
    assert is_valid_ptm_id("evt_" + values[-1], "evt")
    assert not is_valid_ptm_id("evt_invalid", "evt")
    assert new_ptm_id("res", now_ms=999).startswith("res_")


def test_shared_ids_remain_unique_under_clock_rollback_and_threads():
    rolled = new_ulid(now_ms=1)
    after_rollback = new_ulid(now_ms=0)
    assert after_rollback > rolled
    with ThreadPoolExecutor(max_workers=8) as pool:
        values = list(pool.map(lambda _: new_ulid(now_ms=2_000), range(400)))
    assert len(set(values)) == 400


def test_event_id_is_canonical_and_ledger_sequence_not_id_order(tmp_path):
    first = append_ptm_event(tmp_path, event_type="test", aggregate_type="task", aggregate_id="task-1", stream_id="task:task-1", actor_ref="test", authority_refs=[], source_refs=[], payload_schema="test.v1", payload={}, idempotency_key="one", occurred_at=NOW, event_id="evt_" + new_ulid(now_ms=2_000))
    second = append_ptm_event(tmp_path, event_type="test", aggregate_type="task", aggregate_id="task-1", stream_id="task:task-1", actor_ref="test", authority_refs=[], source_refs=[], payload_schema="test.v1", payload={}, idempotency_key="two", occurred_at=NOW, event_id="evt_" + new_ulid(now_ms=1))
    assert first["sequence_number"] == 1
    assert second["sequence_number"] == 2
    with pytest.raises(PtmReadinessError, match="canonical event ID"):
        append_ptm_event(tmp_path, event_type="test", aggregate_type="task", aggregate_id="task-1", stream_id="task:task-1", actor_ref="test", authority_refs=[], source_refs=[], payload_schema="test.v1", payload={}, idempotency_key="bad", occurred_at=NOW, event_id="not-an-event-id")


def test_concurrent_stream_lock_fails_closed_without_second_sequence(tmp_path):
    lock = tmp_path / "runtime/ptm/ledger/events/.locks/task_task-1"
    lock.mkdir(parents=True)
    with pytest.raises(PtmReadinessError, match="concurrently"):
        append_ptm_event(tmp_path, event_type="test", aggregate_type="task", aggregate_id="task-1", stream_id="task:task-1", actor_ref="test", authority_refs=[], source_refs=[], payload_schema="test.v1", payload={}, idempotency_key="one", occurred_at=NOW)
    assert not list((tmp_path / "runtime/ptm/ledger/events").rglob("*.json"))
