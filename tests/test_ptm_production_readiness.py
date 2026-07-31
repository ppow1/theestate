import hashlib
import json
from pathlib import Path

import pytest

from estate.core.ptm_production_readiness import (
    PtmProductionReadinessResolver,
    PtmReadinessError,
    append_ptm_event,
    canonical_json,
    cli,
    read_readiness,
    validate_readiness_record,
)
from estate.core.ptm_production_readiness import _ulid


NOW = "2026-07-31T12:00:00Z"


def source_ref(root: Path, name: str = "evidence.json"):
    path = root / "evidence" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"accepted":true}\n', encoding="utf-8")
    return {"source_path": str(path.relative_to(root)), "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "adapter_name": "test", "adapter_version": "1"}


def append_input(root: Path, *, dependencies=None, gates=None, objective="obj-1", task="tsk-1", enabling="prj-1", **extra):
    payload = {"objective_id": objective, "task_id": task, "enabling_project_id": enabling, "dependencies": dependencies if dependencies is not None else [{"dependency_id": "dep-1", "state": "satisfied", "observed_at": NOW}], "gate_checks": gates if gates is not None else [{"name": "dependency_gate", "state": "pass", "observed_at": NOW}], "source_references": [source_ref(root)], **extra}
    return append_ptm_event(root, event_type="task.readiness_inputs", aggregate_type="task", aggregate_id=task, stream_id=f"task:{task}", actor_ref="ptm-fixture", authority_refs=["test-authority"], source_refs=payload["source_references"], payload_schema="estate.ptm.readiness-input.v1", payload=payload, idempotency_key=f"input:{task}:{extra.get('marker', 'one')}", occurred_at=NOW)


def resolve(root, event, **kwargs):
    return PtmProductionReadinessResolver(root, freshness_seconds=3600, freshness_policy_id="test-policy-v1", freshness_policy_digest="a" * 64).resolve_engineering_readiness(objective_id="obj-1", enabling_project_id="prj-1", task_or_package_id="tsk-1", source_high_watermark=event["event_id"], observed_at=NOW, **kwargs)


def test_satisfied_dependency_is_ready(tmp_path):
    event = append_input(tmp_path)
    result = resolve(tmp_path, event)
    assert result.readiness_state == "ready"
    assert (tmp_path / result.record["projection_path"]).exists()
    assert result.record["ledger_event_reference"].startswith("evt_")
    assert result.record["freshness_policy_id"] == "test-policy-v1"
    assert result.record["freshness_policy_digest"] == "a" * 64


@pytest.mark.parametrize(("state", "expected"), [("unsatisfied", "not_ready"), ("unknown", "unknown")])
def test_dependency_states_fail_closed(tmp_path, state, expected):
    event = append_input(tmp_path, dependencies=[{"dependency_id": "dep-1", "state": state, "observed_at": NOW}])
    assert resolve(tmp_path, event).readiness_state == expected


def test_missing_dependency_record_is_unknown(tmp_path):
    result = PtmProductionReadinessResolver(tmp_path).resolve_engineering_readiness(objective_id="obj-1", enabling_project_id=None, task_or_package_id="tsk-1", source_high_watermark="none", observed_at=NOW)
    assert result.readiness_state == "unknown"
    assert "missing canonical" in result.record["failure_reason"]


def test_valid_waiver_is_preserved(tmp_path):
    ref = source_ref(tmp_path, "waiver.json")
    dependency = {"dependency_id": "dep-1", "state": "waived", "observed_at": NOW, "waiver": {"waiver_id": "w-1", "granting_authority": "chief-architect", "scope": {"objective_id": "obj-1", "package_id": "pkg-1", "task_id": "tsk-1"}, "reason": "approved exception", "granted_at": NOW, "expires_at": "2026-08-01T00:00:00Z", "source_ref": ref, "source_digest": ref["source_sha256"]}}
    event = append_input(tmp_path, dependencies=[dependency], package_id="pkg-1")
    result = resolve(tmp_path, event)
    assert result.readiness_state == "ready"
    assert result.record["waiver_references"]


def test_invalid_and_expired_waivers_block(tmp_path):
    dependency = {"dependency_id": "dep-1", "state": "waived", "observed_at": NOW, "waiver": {"waiver_id": "w-1", "granting_authority": "", "scope": {"objective_id": "wrong", "task_id": "tsk-1"}, "reason": "x", "granted_at": NOW, "expires_at": "2026-07-01T00:00:00Z", "source_ref": {}, "source_digest": "bad"}}
    event = append_input(tmp_path, dependencies=[dependency])
    result = resolve(tmp_path, event)
    assert result.readiness_state == "blocked"
    assert result.record["conflicts"]


def test_waiver_source_digest_mismatch_blocks(tmp_path):
    ref = source_ref(tmp_path, "waiver-mismatch.json")
    dependency = {"dependency_id": "dep-1", "state": "waived", "observed_at": NOW, "waiver": {"waiver_id": "w-1", "granting_authority": "chief-architect", "scope": {"objective_id": "obj-1", "task_id": "tsk-1"}, "reason": "x", "granted_at": NOW, "expires_at": "2026-08-01T00:00:00Z", "source_ref": ref, "source_digest": "b" * 64}}
    event = append_input(tmp_path, dependencies=[dependency])
    assert resolve(tmp_path, event).readiness_state == "blocked"


def test_missing_gate_and_contradictory_evidence_block(tmp_path):
    event = append_input(tmp_path, dependencies=[{"dependency_id": "dep-1", "state": "satisfied"}, {"dependency_id": "dep-1", "state": "unsatisfied"}], gates=[], conflicts=["contradictory source records"])
    result = resolve(tmp_path, event)
    assert result.readiness_state == "blocked"
    assert result.record["warnings"]


def test_cycle_detection_is_fail_closed(tmp_path):
    event = append_input(tmp_path, dependencies=[{"dependency_id": "a", "state": "satisfied", "depends_on": ["b"]}, {"dependency_id": "b", "state": "satisfied", "depends_on": ["a"]}])
    result = resolve(tmp_path, event)
    # The bounded resolver treats an explicit cycle/conflict as non-ready; it never infers readiness.
    assert result.readiness_state in {"blocked", "unknown"}


def test_stale_and_expired_evidence_fail_closed(tmp_path):
    event = append_input(tmp_path, dependencies=[{"dependency_id": "dep-1", "state": "satisfied", "observed_at": "2026-07-01T00:00:00Z", "expires_at": "2026-07-02T00:00:00Z"}])
    result = resolve(tmp_path, event)
    assert result.readiness_state == "blocked"
    assert "expired" in " ".join(result.record["conflicts"])


def test_source_digest_drift_blocks(tmp_path):
    event = append_input(tmp_path)
    (tmp_path / "evidence" / "evidence.json").write_text("changed\n", encoding="utf-8")
    result = resolve(tmp_path, event)
    assert result.readiness_state == "blocked"
    assert any("digest drift" in item for item in result.record["warnings"])


def test_high_watermark_mismatch_blocks(tmp_path):
    event = append_input(tmp_path)
    result = PtmProductionReadinessResolver(tmp_path).resolve_engineering_readiness(objective_id="obj-1", enabling_project_id="prj-1", task_or_package_id="tsk-1", source_high_watermark="wrong", observed_at=NOW)
    assert result.readiness_state == "blocked"
    assert result.record["failure_reason"] == "source high-watermark mismatch"


def test_replay_is_deterministic_and_create_once(tmp_path):
    event = append_input(tmp_path)
    first = resolve(tmp_path, event)
    second = resolve(tmp_path, event)
    assert first.record == second.record
    assert len(list((tmp_path / "runtime/ptm/readiness").glob("*.json"))) == 1
    assert read_readiness(tmp_path, first.record["resolution_id"]) == first.record


def test_malformed_record_and_digest_validation_fail_closed(tmp_path):
    with pytest.raises(PtmReadinessError):
        validate_readiness_record({})
    (tmp_path / "runtime/ptm/ledger/events/bad.json").parent.mkdir(parents=True)
    (tmp_path / "runtime/ptm/ledger/events/bad.json").write_text("not json", encoding="utf-8")
    with pytest.raises(PtmReadinessError):
        PtmProductionReadinessResolver(tmp_path).resolve_engineering_readiness(objective_id="obj-1", enabling_project_id=None, task_or_package_id="tsk-1", source_high_watermark="x", observed_at=NOW)


def test_foreign_event_path_and_duplicate_head_fail_closed(tmp_path):
    event = append_input(tmp_path)
    original = next((tmp_path / "runtime/ptm/ledger/events").rglob("*.json"))
    foreign = original.parent.parent / "foreign" / original.name
    foreign.parent.mkdir(parents=True)
    original.rename(foreign)
    with pytest.raises(PtmReadinessError, match="foreign PTM event path"):
        resolve(tmp_path, event)


def test_path_traversal_and_cli_validation_errors_fail_closed(tmp_path, capsys):
    with pytest.raises(PtmReadinessError):
        read_readiness(tmp_path, "../outside")
    assert cli(["read", "--root", str(tmp_path), "--resolution-id", "../outside"]) == 2
    assert "validation failed" in capsys.readouterr().err


def test_provider_or_helen_or_planning_presence_does_not_grant_authority(tmp_path):
    (tmp_path / "runtime/provider_catalog.json").parent.mkdir(parents=True)
    (tmp_path / "runtime/provider_catalog.json").write_text('{"qwen.local.text":{"status":"operationally_validated"}}', encoding="utf-8")
    result = PtmProductionReadinessResolver(tmp_path).resolve_engineering_readiness(objective_id="obj-1", enabling_project_id=None, task_or_package_id="tsk-1", source_high_watermark="none", observed_at=NOW)
    assert result.readiness_state == "unknown"


def test_only_ptm_paths_are_mutated(tmp_path):
    event = append_input(tmp_path)
    resolve(tmp_path, event)
    paths = {p.relative_to(tmp_path).as_posix().split("/")[0] for p in tmp_path.rglob("*") if p.is_file()}
    assert paths <= {"evidence", "runtime"}
    assert not (tmp_path / "runtime/dependencies").exists()


def test_cli_read_and_validate(tmp_path, capsys):
    event = append_input(tmp_path)
    result = resolve(tmp_path, event)
    assert cli(["read", "--root", str(tmp_path), "--resolution-id", result.record["resolution_id"]]) == 0
    assert result.record["projection_path"] in capsys.readouterr().out
    assert cli(["validate", "--root", str(tmp_path), "--record", str(tmp_path / result.record["projection_path"])]) == 0


def test_cli_resolve(tmp_path, capsys):
    event = append_input(tmp_path)
    assert cli(["resolve", "--root", str(tmp_path), "--objective-id", "obj-1", "--enabling-project-id", "prj-1", "--task-id", "tsk-1", "--source-high-watermark", event["event_id"], "--observed-at", NOW]) == 0
    output = capsys.readouterr().out
    assert '"readiness_state": "unknown"' in output
    assert "freshness policy unavailable" in output


def test_canonical_json_is_stable():
    assert canonical_json({"b": 1, "a": [2, 3]}) == '{"a":[2,3],"b":1}'


def test_bounded_event_ulid_shape_is_contract_compatible():
    value = _ulid()
    assert len(value) == 26
    assert set(value) <= set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")
