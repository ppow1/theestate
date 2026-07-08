import pytest

from estate.core.orchestrator_dispatch import DispatchRecord, safe_dispatch_summary


def schedule(**overrides):
    data = {
        "schedule_id": "sch-1", "intake_id": "int-1", "classification": "Estate Internal", "priority": "normal",
        "provider_id": "prov-1", "mission": "Do work", "summary": "Visible summary", "approval_reference": "dec-1",
    }
    data.update(overrides)
    return data


def test_dispatch_record_model_validates():
    rec = DispatchRecord.create(cycle_id="cyc-1", state="pending_dispatch", schedule=schedule())
    assert rec.dispatch_id.startswith("disp-")
    assert rec.state == "pending_dispatch"


def test_blocked_dispatch_requires_reason():
    with pytest.raises(ValueError):
        DispatchRecord.create(cycle_id="cyc-1", state="blocked", schedule=schedule())


def test_sensitive_summaries_redacted_by_default():
    rec = DispatchRecord.create(cycle_id="cyc-1", state="pending_dispatch", schedule=schedule(classification="Restricted", summary="secret"))
    assert safe_dispatch_summary(rec.to_dict()) == "Sensitive summary redacted."
