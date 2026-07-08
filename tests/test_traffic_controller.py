import pytest
from estate.core.traffic_controller import OperationsReview, RecommendedAction, redact_summary


def test_operations_review_model_validates():
    review = OperationsReview.create(classification="Estate Internal")
    assert review.created_by == "traffic_controller.operations_manager"
    assert review.to_dict()["pending_intake_count"] == 0


def test_unknown_classification_rejected():
    with pytest.raises(ValueError):
        OperationsReview.create(classification="Secret").validate()


def test_unknown_action_type_rejected():
    with pytest.raises(ValueError):
        RecommendedAction.create(action_type="execute", target_type="system", reason="bad", safe_summary="bad").validate()


def test_sensitive_summaries_are_redacted_by_default():
    assert redact_summary("Restricted", "private") == "Sensitive operations summary redacted."
    assert redact_summary("Restricted", "private", {"summary_safe": True}) == "private"
