from __future__ import annotations

import json
from pathlib import Path

import pytest

from estate.core.authority_schema_runtime import canonical_record_digest, load_registry, require_valid, validation_errors
from estate.core.execution_adapter_handoff_runtime import prepare_handoff, validate_handoff
from estate.core.operations_control_runtime import OperationsControlRuntime
from estate.core.operations_manager import OperationsDecision
from estate.core.execution_provider_adapter import utc_now

from test_dispatch_adapter_authority_propagation import _governed


def _records(tmp_path: Path) -> tuple[dict, dict, dict]:
    result = _governed(tmp_path)
    auth = result["authorization"]
    auth_path = tmp_path / "runtime/grace_helen_engineering/engineering_authorizations" / f"{auth['authorization_id']}.json"
    decision_ref = result["dispatch"]["provider_metadata"]["decision_reference"]
    decision_id = decision_ref.removeprefix("operations-control/")
    decision_path = next((tmp_path / "runtime/operations/control/decisions").glob(f"*_{decision_id}.json"))
    return result, json.loads(auth_path.read_text(encoding="utf-8")), json.loads(decision_path.read_text(encoding="utf-8"))


def test_authority_registry_has_unique_resolvable_closed_schemas(tmp_path):
    registry, schemas = load_registry(tmp_path)
    assert {
        "estate.engineering.authorization.v1",
        "estate.operations-control.decision.v1",
        "estate.engineering.commission-execution-authority.v1",
        "estate.engineering.commission-ptm-evidence.v1",
    } <= set(schemas)
    for schema_id, schema in schemas.items():
        assert schema.get("$id") == schema_id
    assert registry is not None


def test_valid_authorization_and_operations_decision_validate_at_creation_and_handoff(tmp_path):
    result, auth, decision = _records(tmp_path)
    require_valid(auth, "estate.engineering.authorization.v1", tmp_path)
    require_valid(decision, "estate.operations-control.decision.v1", tmp_path)
    assert auth["record_digest"] == canonical_record_digest(auth)
    assert decision["record_digest"] == canonical_record_digest(decision)
    prepared = validate_handoff(result["dispatch"]["dispatch_id"], tmp_path)
    assert prepared["status"] == "handoff_validated"


@pytest.mark.parametrize(
    "field, value",
    [
        ("schema_version", "unknown.v9"),
        ("engineering_commission_id", None),
        ("dispatch_id", "dispatch-other"),
        ("provider_id", "provider-other"),
        ("adapter_reference", "adapter-other@1"),
        ("grace_objective_id", "grace-other"),
        ("grace_action_id", "grace-other"),
        ("helen_determination_id", "helen-other"),
        ("prompt_source_digest", "0" * 64),
        ("allowed_read_paths", ["."]),
        ("allowed_write_paths", ["runtime"]),
        ("expected_outputs", ["other/output.md"]),
        ("institutional_acceptance_state", "granted"),
        ("record_digest", "f" * 64),
    ],
)
def test_authorization_mutation_fails_at_final_boundary(tmp_path, field, value):
    result, auth, _ = _records(tmp_path)
    auth_path = tmp_path / "runtime/grace_helen_engineering/engineering_authorizations" / f"{auth['authorization_id']}.json"
    auth[field] = value
    auth_path.write_text(json.dumps(auth), encoding="utf-8")
    checked = validate_handoff(result["dispatch"]["dispatch_id"], tmp_path)
    assert checked["status"] == "blocked"
    assert not (tmp_path / "runtime/execution_adapters/requests").exists()


@pytest.mark.parametrize(
    "field, value",
    [
        ("schema_version", "unknown.v9"),
        ("decision_type", "execute_anything"),
        ("decision_state", "unknown"),
        ("decided_by", ""),
        ("engineering_commission_id", "engcom-other"),
        ("dispatch_id", "dispatch-other"),
        ("engineering_authorization_id", "engauth-other"),
        ("selected_provider_id", "provider-other"),
        ("selected_adapter_reference", "adapter-other@1"),
        ("prompt_source_digest", "0" * 64),
        ("institutional_acceptance_state", "granted"),
        ("record_digest", "f" * 64),
    ],
)
def test_operations_decision_mutation_fails_at_final_boundary(tmp_path, field, value):
    result, _, decision = _records(tmp_path)
    decision_id = decision["decision_id"]
    decision_path = next((tmp_path / "runtime/operations/control/decisions").glob(f"*_{decision_id}.json"))
    decision[field] = value
    decision_path.write_text(json.dumps(decision), encoding="utf-8")
    checked = validate_handoff(result["dispatch"]["dispatch_id"], tmp_path)
    assert checked["status"] == "blocked"
    assert not (tmp_path / "runtime/execution_adapters/requests").exists()


def test_creation_rejects_invalid_operations_decision_without_publishing(tmp_path):
    decision = OperationsDecision.create(decided_by="Engineering", decision_type="authorize_dispatch", target_type="dispatch", reason="invalid", technical_execution=True)
    with pytest.raises(ValueError):
        OperationsControlRuntime(tmp_path).record_decision(decision)
    assert not (tmp_path / "runtime/operations/control/decisions").exists()


def test_arbitrary_operations_reference_and_missing_schema_fail_closed(tmp_path):
    result, _, _ = _records(tmp_path)
    queue_path = tmp_path / "runtime/execution_dispatch/queue.json"
    payload = json.loads(queue_path.read_text(encoding="utf-8"))
    payload["items"][0]["provider_metadata"]["decision_reference"] = "operations-control/arbitrary"
    queue_path.write_text(json.dumps(payload), encoding="utf-8")
    checked = prepare_handoff(result["dispatch"]["dispatch_id"], tmp_path, write=True)
    assert checked["status"] == "blocked"
    assert not (tmp_path / "runtime/execution_adapters/requests").exists()
