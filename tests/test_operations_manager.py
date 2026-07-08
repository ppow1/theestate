import pytest
from estate.core.operations_manager import OperationsDecision


def test_operations_decision_model_validates():
    decision = OperationsDecision.create(decided_by="Steward", decision_type="assign", target_type="work_package", target_id="WP-0609", reason="Assign", assignment_label="A2C2")
    assert decision.to_dict()["assignment_label"] == "A2C2"


def test_unknown_decision_type_rejected():
    with pytest.raises(ValueError):
        OperationsDecision.create(decided_by="Steward", decision_type="execute", target_type="system", reason="bad").validate()


def test_a2c_assignment_label_is_preserved():
    decision = OperationsDecision.create(decided_by="Steward", decision_type="assign", target_type="work_package", target_id="WP-0610", reason="Assign", assignment_label="A2C2")
    loaded = OperationsDecision.from_dict(decision.to_dict())
    assert loaded.assignment_label == "A2C2"
