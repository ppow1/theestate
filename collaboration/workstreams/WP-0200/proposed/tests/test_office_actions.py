import pytest
from estate.core.office_actions import AuthorityClass, ConfirmationRequirement, HookMode, OfficeAction, SAMPLE_ACTIONS, bulk_confirmation_summary


def by_id(action_id):
    return next(a for a in SAMPLE_ACTIONS if a.action_id == action_id)


def test_authority_classes_represent_required_surface():
    assert {a.authority_class for a in SAMPLE_ACTIONS} >= set(AuthorityClass)


def test_authority_gated_action_cannot_be_no_confirmation():
    with pytest.raises(ValueError):
        OfficeAction("bad", "Bad", "work-packages", "bad", "review", AuthorityClass.AUTHORITY_GATED_INSTITUTIONAL_ACTION, ConfirmationRequirement.NONE)


def test_copy_command_is_not_executable_and_reports_output_paths():
    action = by_id("office.validation.copy_command")
    assert action.command_hook.mode == HookMode.COPY_ONLY
    assert action.command_hook.execution_allowed is False


def test_generated_artifact_and_bulk_summary():
    action = by_id("office.snapshot.export")
    assert action.confirmation == ConfirmationRequirement.CONFIRM_GENERATED_ARTIFACT
    summary = bulk_confirmation_summary([action, by_id("office.review.request")])
    assert summary["requires_authority_route"] is True
    assert "browser download: office-snapshot.zip" in summary["expected_output_paths"]
