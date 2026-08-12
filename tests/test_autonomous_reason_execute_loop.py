from estate.core.autonomous_reason_execute_loop import AutonomousReasonExecuteLoop, classify_reasoning_response
from estate.core.consultation_execution import ConsultationExecutionRouter, ProviderBinding
from estate.core.consultation_store import ConsultationStore
from estate.core.execution_provider_adapter import ExecutionProviderAdapter, ExecutionProviderAdapterResult, utc_now


class HiddenConstraintProvider(ExecutionProviderAdapter):
    provider_id = "fixture-executor"
    provider_type = "fixture"
    adapter_id = "hidden-constraint-fixture"

    def dry_run(self, request):
        return self.submit(request)

    def submit(self, request):
        return ExecutionProviderAdapterResult(
            adapter_request_id=request.adapter_request_id,
            dispatch_id=request.dispatch_id,
            provider_id=request.provider_id,
            status="completed",
            started_at=utc_now(),
            finished_at=utc_now(),
            summary="Fixture observed the hidden browser-session constraint.",
            validation_status="passed",
            metadata={"provider_neutral": True},
        )


def build_loop(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = store.allocate_root(status="response_received", objective="bounded diagnostic")
    router = ConsultationExecutionRouter(store, [ProviderBinding(HiddenConstraintProvider(), frozenset({"software_engineering_test"}))], runtime_root=tmp_path)
    return store, consultation, AutonomousReasonExecuteLoop(store, router)


def execution_decision(consultation_id):
    return {
        "classification": "EXECUTION_RECOMMENDED",
        "rationale": "A bounded read-only inspection is warranted.",
        "execution": {
            "consultation_id": consultation_id,
            "objective": "diagnostic.md",
            "required_capability": "software_engineering_test",
            "allowed_scope": ["src"],
            "prohibited_scope": ["archive", "runtime"],
            "evidence_required": ["observed constraint"],
            "validation_criteria": "report the observed constraint",
        },
    }


def test_prose_does_not_become_execution(tmp_path):
    store, consultation, loop = build_loop(tmp_path)
    result = loop.accept_reasoning(consultation.logical_consultation_id, "Run this command now.")
    assert result["status"] == "information_only"
    assert store.execution_requests(consultation.logical_consultation_id) == []


def test_execution_recommendation_is_provider_neutral_and_hidden_constraint_continues(tmp_path):
    store, consultation, loop = build_loop(tmp_path)
    accepted = loop.accept_reasoning(consultation.logical_consultation_id, execution_decision(consultation.logical_consultation_id))
    assert accepted["status"] == "execution_requested"
    assert accepted["execution_request_id"].startswith("exec-")
    assert store.execution_request(accepted["execution_request_id"]).provider_id == "fixture-executor"

    observed = loop.execute_and_observe(accepted["execution_request_id"], {
        "classification": "ASSUMPTION_INVALID",
        "evidence": {"browser_session": "not durable across restart"},
        "revised_question": "Revise the recommendation for a restartable browser session.",
    })

    assert observed["status"] == "reasoning_continuation_required"
    assert observed["continuation_id"] == "1.01"
    continuation = store.get("1.01")
    assert continuation.current_evidence["execution_request_id"] == accepted["execution_request_id"]
    assert continuation.current_evidence["execution_provider_id"] == "fixture-executor"


def test_invalid_structured_execution_request_fails_closed():
    try:
        classify_reasoning_response({"classification": "EXECUTION_RECOMMENDED", "execution": {}})
    except ValueError as exc:
        assert str(exc).startswith("execution_spec_missing:")
    else:
        raise AssertionError("incomplete execution request was accepted")


def test_execution_specification_alias_is_normalized():
    decision = execution_decision("1.00")
    decision["execution_specification"] = decision.pop("execution")
    parsed = classify_reasoning_response({"content": __import__("json").dumps({"reasoning": "inspect", "decision": decision})})
    assert parsed.classification == "EXECUTION_RECOMMENDED"
    assert parsed.execution["consultation_id"] == "1.00"


def test_descriptive_fixture_evidence_capability_normalizes_provider_neutrally():
    response = {
        "classification": "MORE_REASONING_REQUIRED",
        "evidence_request": {
            "objective": "Inspect the isolated fixture.",
            "evidence_type": "fixture_and_invariant_validation_evidence",
            "target": "Temp/fixture/fixture.json",
            "required_capability": "Read the fixture and authoritative invariant.",
            "allowed_scope": ["Temp/fixture"],
            "prohibited_scope": ["production", "runtime"],
            "evidence_requirements": ["fixture contents"],
            "consultation_correlation": {"consultation_id": "1.00"},
        },
    }
    parsed = classify_reasoning_response(response)
    assert parsed.evidence_request["required_capability"] == "filesystem_read"


def test_execution_correlation_accepts_canonical_consultation_id_object():
    decision = execution_decision("1.00")
    decision["execution"]["consultation_correlation"] = {"consultation_id": "1.00", "root_consultation_id": "1.00"}
    parsed = classify_reasoning_response(decision)
    assert parsed.execution["consultation_id"] == "1.00"


def test_fixture_repair_requires_explicit_write_scope_and_path_scopes():
    decision = execution_decision("1.00")
    decision["execution"]["objective"] = "Repair the controlled fixture."
    try:
        classify_reasoning_response(decision)
    except ValueError as exc:
        assert str(exc) == "execution_spec_missing:write_scope"
    else:
        raise AssertionError("fixture repair without write_scope was accepted")


def test_completed_evidence_does_not_suppress_distinct_execution(tmp_path):
    store, consultation, loop = build_loop(tmp_path)
    evidence = loop.accept_reasoning(consultation.logical_consultation_id, execution_decision(consultation.logical_consultation_id))
    loop.execute_and_observe(evidence["execution_request_id"], {"classification": "VALIDATED", "evidence": {"fixture": "inspected"}})
    execution = loop.accept_reasoning(consultation.logical_consultation_id, execution_decision(consultation.logical_consultation_id))
    assert execution["status"] == "execution_requested"
    assert execution["execution_request_id"] != evidence["execution_request_id"]
