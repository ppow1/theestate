import pytest

from estate.core.worker_assignments import WorkerAssignmentRecord, safe_assignment_summary


def valid_record(**overrides):
    data = dict(assigned_by="Steward", assigned_to="A2C1", assignment_label="A2C1", mission="Test mission", summary="Visible summary", classification="Estate Internal")
    data.update(overrides)
    return WorkerAssignmentRecord.create(**data)


def test_valid_assignment_accepted():
    rec = valid_record()
    assert rec.assignment_id.startswith("wa-")
    assert rec.assigned_to == "A2C1"
    assert rec.state == "assigned"


def test_missing_assignment_id_rejected():
    rec = valid_record()
    data = rec.to_dict()
    data["assignment_id"] = ""
    with pytest.raises(ValueError, match="assignment_id is required"):
        WorkerAssignmentRecord.from_dict(data)


def test_unknown_state_rejected():
    rec = valid_record(state="running")
    data = rec.to_dict()
    data["state"] = "mystery"
    with pytest.raises(ValueError, match="unknown assignment state"):
        WorkerAssignmentRecord.from_dict(data)


def test_unknown_classification_rejected():
    with pytest.raises(ValueError, match="unknown classification"):
        valid_record(classification="Secret") .validate()


def test_sensitive_summaries_redacted_by_default():
    rec = valid_record(classification="Restricted", summary="Private source detail")
    assert safe_assignment_summary(rec) == "Sensitive assignment summary redacted."


def test_summary_safe_metadata_displays_summary():
    rec = valid_record(classification="Restricted", summary="Approved summary", metadata={"summary_safe": True})
    assert safe_assignment_summary(rec) == "Approved summary"


def test_a2c_labels_preserved():
    for label in ["A2C1", "A2C2", "A2C3"]:
        rec = valid_record(assigned_to=label, assignment_label=label)
        assert rec.assignment_label == label
        assert rec.assigned_to == label
