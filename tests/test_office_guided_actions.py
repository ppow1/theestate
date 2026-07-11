from estate.core.office_guided_actions import (
    advance, browser_contract, cancel, confirm, create_validate_review_promote_workflow,
    evaluate_readiness, provide_input, satisfy_precondition, start_session, GuidedActionSession
)


def handlers(prefix="evidence"):
    return {
        "validate": lambda s, step: {"evidence_link": f"{prefix}/validate.json", "summary": "validation passed"},
        "review": lambda s, step: {"evidence_link": f"{prefix}/review.md", "summary": "review accepted"},
        "promote": lambda s, step: {"evidence_link": f"{prefix}/promote.json", "summary": "promotion receipt"},
    }


def ready_validate_session():
    session = start_session(create_validate_review_promote_workflow(), "S-1")
    provide_input(session, "artifact", "staged/change.json")
    satisfy_precondition(session, "workspace_clean", "evidence/git-status.txt")
    return session


def test_deterministic_step_progression_validate_review_promote():
    session = ready_validate_session()
    assert advance(session, handlers())["completed_step"] == "validate"
    confirm(session, "reviewer_accepts_evidence")
    assert advance(session, handlers())["completed_step"] == "review"
    confirm(session, "steward_promote_approval")
    assert advance(session, handlers())["completed_step"] == "promote"
    assert session.status == "completed"
    assert session.completed_steps == ["validate", "review", "promote"]


def test_interruption_resume_uses_snapshot_without_skipping_authority():
    session = ready_validate_session()
    advance(session, handlers())
    snapshot = session.to_snapshot()
    resumed = GuidedActionSession.from_snapshot(snapshot)
    assert evaluate_readiness(resumed)["state"] == "awaiting_confirmation"
    assert advance(resumed, handlers())["advanced"] is False
    confirm(resumed, "reviewer_accepts_evidence")
    assert advance(resumed, handlers())["completed_step"] == "review"


def test_authority_preserved_no_hidden_promotion_approval():
    session = ready_validate_session()
    advance(session, handlers())
    confirm(session, "reviewer_accepts_evidence")
    advance(session, handlers())
    readiness = evaluate_readiness(session)
    assert readiness["step_id"] == "promote"
    assert readiness["state"] == "awaiting_confirmation"
    assert "steward_promote_approval" in readiness["missing_confirmations"]
    assert advance(session, handlers())["advanced"] is False


def test_idempotent_terminal_advance_does_not_duplicate_evidence():
    session = ready_validate_session()
    advance(session, handlers())
    confirm(session, "reviewer_accepts_evidence")
    advance(session, handlers())
    confirm(session, "steward_promote_approval")
    advance(session, handlers())
    evidence_count = len(session.evidence)
    assert advance(session, handlers())["advanced"] is False
    assert len(session.evidence) == evidence_count


def test_cancellation_before_irreversible_step_and_block_when_irreversible_ready():
    session = ready_validate_session()
    assert cancel(session, "operator stopped before validation")["cancelled"] is True
    session = ready_validate_session()
    advance(session, handlers())
    confirm(session, "reviewer_accepts_evidence")
    advance(session, handlers())
    confirm(session, "steward_promote_approval")
    result = cancel(session, "too late")
    assert result["cancelled"] is False
    assert result["state"] == "blocked"


def test_truthful_blocked_failed_and_evidence_generation_with_fake_handlers():
    session = ready_validate_session()
    assert advance(session, {"validate": lambda s, step: {"blocked": True, "reason": "missing external review"}})["state"] == "blocked"
    session = ready_validate_session()
    assert advance(session, {"validate": lambda s, step: {"summary": "no evidence"}})["state"] == "failed"
    session = ready_validate_session()
    advance(session, handlers("fake"))
    assert session.evidence[0]["evidence_link"] == "fake/validate.json"
    assert any(event["event"] == "step_completed" for event in session.audit_log)


def test_reusable_browser_contract_discloses_staged_authority_and_actions():
    session = ready_validate_session()
    contract = browser_contract(session)
    assert contract["kind"] == "estate.guided_action.browser_contract.v1"
    assert contract["installed_by_wp_0531"] is True
    assert contract["authority"]["automatic_approval"] is False
    assert "advance" in contract["allowed_actions"]
    assert contract["readiness"]["state"] == "ready"
