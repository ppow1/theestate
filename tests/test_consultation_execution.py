import json
from pathlib import Path

from estate.core.codex_bridge import run_codex_bridge_request
from estate.core.codex_bridge_execution_provider_adapter import CodexBridgeExecutionProviderAdapter
from estate.core.consultation_execution import ConsultationExecutionRouter, ProviderBinding
from estate.core.consultation_store import ConsultationStore
from estate.core.execution_provider_adapter import ExecutionProviderAdapter, ExecutionProviderAdapterRequest, ExecutionProviderAdapterResult, utc_now


class FixtureExecutor(ExecutionProviderAdapter):
    provider_id = "fixture-executor"
    provider_type = "fixture"
    adapter_id = "fixture-adapter"

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
            summary="Fixture provider completed bounded diagnostic.",
            validation_status="passed",
            metadata={"provider_neutral": True, "evidence": {"tests_run": ["fixture-check"]}},
        )


def router(tmp_path, *bindings):
    store = ConsultationStore(tmp_path / "consultations.db")
    consultation = store.allocate_root(status="awaiting_reasoning", objective="Bounded execution consultation")
    return store, consultation, ConsultationExecutionRouter(store, bindings, runtime_root=tmp_path)


def test_fixture_provider_is_selected_through_neutral_router_and_correlated(tmp_path):
    store, consultation, router_instance = router(tmp_path, ProviderBinding(FixtureExecutor(), frozenset({"software_engineering_test"})))
    request = router_instance.create_request(
        consultation.logical_consultation_id,
        required_capability="software_engineering_test",
        dispatch_id="dispatch-fixture-1",
        prompt_source="diagnostic.md",
        classification="Estate Internal",
        read_scope_paths=["src"],
    )

    result = router_instance.execute(request.adapter_request_id)
    link = store.execution_request(request.adapter_request_id)
    attempts = store.execution_attempts(request.adapter_request_id)

    assert result.status == "completed"
    assert link.logical_consultation_id == consultation.logical_consultation_id
    assert link.provider_id == "fixture-executor"
    assert link.status == "completed"
    assert len(attempts) == 1
    assert attempts[0].status == "completed"
    assert attempts[0].execution_attempt_id.startswith("attempt-")
    assert "codex" not in json.dumps(request.to_dict()).lower()


def test_codex_provider_can_be_selected_without_codex_fields_in_consultation(tmp_path):
    prompt = tmp_path / "diagnostic.md"
    prompt.write_text("Read-only diagnostic.\n", encoding="utf-8")

    def fake_bridge(bridge_request, **kwargs):
        result = run_codex_bridge_request(bridge_request, root=tmp_path, dry_run=True)
        result.status = "succeeded"
        result.final_message = "Bounded provider diagnostic completed."
        result.tests_run = ["fixture-check"]
        return result

    codex = CodexBridgeExecutionProviderAdapter(root=tmp_path, bridge_runner=fake_bridge)
    store, consultation, router_instance = router(tmp_path, ProviderBinding(codex, frozenset({"software_engineering_test"})))
    request = router_instance.create_request(
        consultation.logical_consultation_id,
        required_capability="software_engineering_test",
        dispatch_id="dispatch-codex-1",
        prompt_source="diagnostic.md",
        classification="Estate Internal",
        read_scope_paths=["."],
        decision_reference="test-authorized",
        metadata={"sandbox": "read-only", "codex_home_profile": "default", "approval_policy": "never"},
        preferred_provider="codex-cli-openai",
    )

    result = router_instance.execute(request.adapter_request_id)

    assert result.status == "completed"
    assert result.provider_id == "codex-cli-openai"
    assert store.execution_request(request.adapter_request_id).status == "completed"


def test_completed_execution_is_not_duplicated(tmp_path):
    store, consultation, router_instance = router(tmp_path, ProviderBinding(FixtureExecutor(), frozenset({"software_engineering_test"})))
    request = router_instance.create_request(
        consultation.logical_consultation_id,
        required_capability="software_engineering_test",
        dispatch_id="dispatch-once",
        prompt_source="diagnostic.md",
        classification="Estate Internal",
        read_scope_paths=["src"],
    )
    router_instance.execute(request.adapter_request_id)

    try:
        router_instance.execute(request.adapter_request_id)
    except ValueError as exc:
        assert str(exc) == "execution_request_already_completed"
    else:
        raise AssertionError("completed execution was duplicated")


def test_execution_evidence_can_explicitly_create_reasoning_continuation(tmp_path):
    store, consultation, router_instance = router(tmp_path, ProviderBinding(FixtureExecutor(), frozenset({"software_engineering_test"})))
    request = router_instance.create_request(
        consultation.logical_consultation_id,
        required_capability="software_engineering_test",
        dispatch_id="dispatch-continuation",
        prompt_source="diagnostic.md",
        classification="Estate Internal",
        read_scope_paths=["src"],
    )
    router_instance.execute(request.adapter_request_id)

    continuation = router_instance.continue_from_execution(
        consultation.logical_consultation_id,
        request.adapter_request_id,
        question="The diagnostic exposed a constraint; revise the recommendation.",
        continuation_reason="execution_failed_with_new_evidence",
    )

    assert continuation.logical_consultation_id == "1.01"
    assert continuation.current_evidence["execution_request_id"] == request.adapter_request_id
    assert continuation.continuation_reason == "execution_failed_with_new_evidence"


def test_provider_runtime_failure_retries_same_logical_request_without_new_turn(tmp_path):
    class FlakyExecutor(FixtureExecutor):
        def __init__(self):
            self.calls = 0

        def submit(self, request):
            self.calls += 1
            result = super().submit(request)
            if self.calls == 1:
                result.status = "failed"
                result.validation_status = "failed"
                result.errors = ["temporary provider outage"]
            return result

    provider = FlakyExecutor()
    store, consultation, router_instance = router(tmp_path, ProviderBinding(provider, frozenset({"software_engineering_test"})))
    request = router_instance.create_request(
        consultation.logical_consultation_id,
        required_capability="software_engineering_test",
        dispatch_id="dispatch-retry",
        prompt_source="diagnostic.md",
        classification="Estate Internal",
        read_scope_paths=["src"],
    )

    assert router_instance.execute(request.adapter_request_id).status == "failed"
    assert router_instance.execute(request.adapter_request_id).status == "completed"
    assert len(store.execution_attempts(request.adapter_request_id)) == 2
    assert store.get(consultation.logical_consultation_id).logical_consultation_id == consultation.logical_consultation_id
    assert store.execution_request(request.adapter_request_id).status == "completed"
