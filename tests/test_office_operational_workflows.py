from estate.core.office_operational_workflows import (
    OperationalWorkflowSession,
    advance,
    browser_contract,
    confirm,
    evaluate_readiness,
    provide_input,
    recovery_guidance,
    satisfy_precondition,
    start_session,
    workflow_catalog,
)


def handler_calls(calls, prefix="evidence"):
    def make(name):
        def _handler(session, step):
            calls.append((name, step.id))
            return {
                "evidence_link": f"{prefix}/{step.id}.json",
                "summary": f"{step.id} complete",
                "generated_artifacts": [{"path": f"artifacts/{step.id}.md", "kind": "operator_note"}],
            }
        return _handler

    return {name: make(name) for wf in workflow_catalog().values() for name in wf.canonical_handlers}


def ready_wp_review_session():
    workflow = workflow_catalog()["ops.work_package_review_promotion.v1"]
    session = start_session(workflow, "S-WP")
    provide_input(session, "work_package_path", "collaboration/work_packages/pending/WP.md")
    satisfy_precondition(session, "workspace_clean", "evidence/git-status.txt")
    return session


def test_catalog_contains_required_initial_workflow_families():
    families = {workflow.family for workflow in workflow_catalog().values()}
    assert families == {
        "work-package review and promotion",
        "validation request, evidence review, and next action",
        "resident onboarding preparation",
        "project intake and assignment",
        "local service readiness and approved launch",
        "incident or failure triage",
        "operational handoff and follow-up",
    }


def test_work_package_review_promotion_requires_confirmation_and_invokes_canonical_handlers():
    calls = []
    session = ready_wp_review_session()
    assert advance(session, handler_calls(calls))["completed_step"] == "review"
    readiness = evaluate_readiness(session)
    assert readiness["state"] == "awaiting_confirmation"
    assert "steward_promotion_approval" in readiness["missing_confirmations"]
    assert advance(session, handler_calls(calls))["advanced"] is False
    confirm(session, "steward_promotion_approval")
    assert advance(session, handler_calls(calls))["completed_step"] == "promote"
    assert calls[:2] == [("canonical_work_package_review", "review"), ("canonical_promotion_request", "promote")]
    assert session.status == "completed"


def test_save_resume_does_not_skip_preconditions_or_confirmations():
    session = ready_wp_review_session()
    advance(session, handler_calls([]))
    snapshot = session.to_snapshot()
    resumed = OperationalWorkflowSession.from_snapshot(snapshot)
    assert evaluate_readiness(resumed)["state"] == "awaiting_confirmation"
    assert advance(resumed, handler_calls([]))["advanced"] is False
    confirm(resumed, "steward_promotion_approval")
    assert advance(resumed, handler_calls([]))["advanced"] is True


def test_blocked_precondition_is_truthful_before_handler_runs():
    workflow = workflow_catalog()["ops.local_service_ready_launch.v1"]
    session = start_session(workflow, "S-SVC")
    provide_input(session, "service_id", "office-local")
    calls = []
    result = advance(session, handler_calls(calls))
    assert result["state"] == "awaiting_input"
    assert "workspace_clean" in result["missing_preconditions"]
    assert calls == []


def test_handler_block_failure_evidence_and_artifacts_are_reported_truthfully():
    session = ready_wp_review_session()
    assert advance(session, {"canonical_work_package_review": lambda s, step: {"blocked": True, "reason": "missing signoff"}})["state"] == "blocked"
    session = ready_wp_review_session()
    assert advance(session, {"canonical_work_package_review": lambda s, step: {"summary": "no evidence"}})["state"] == "failed"
    session = ready_wp_review_session()
    advance(session, handler_calls([]))
    assert session.evidence[0]["evidence_link"] == "evidence/review.json"
    assert session.generated_artifacts[0]["path"] == "artifacts/review.md"


def test_browser_contract_and_recovery_guidance_disallow_automatic_authority_bypass():
    session = ready_wp_review_session()
    contract = browser_contract(session)
    assert contract["installed_by_wp_0531"] is True
    assert contract["authority"] == {
        "authority_gate": "existing_office_authority_gate_required_for_each_step",
        "automatic_approval": False,
        "automatic_acceptance": False,
        "automatic_merge": False,
        "automatic_retry": False,
        "automatic_provider_selection": False,
    }
    assert recovery_guidance(session)["no_automatic_retry"] is True
