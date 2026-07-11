from estate.model_control.resident_model_assignment import Availability, LocalModelAssignmentEngine, ModelCandidate


def engine():
    return LocalModelAssignmentEngine(
        [
            ModelCandidate("ollama", "llama3.1", ("chat", "summarize"), priority=1, cold_start_seconds=12),
            ModelCandidate("llamacpp", "mistral", ("chat",), priority=2),
            ModelCandidate("openai", "gpt", ("chat",), provider_type="cloud", priority=0),
        ],
        resident_assignments={"alfred": ["ollama:llama3.1", "openai:gpt", "llamacpp:mistral"]},
        capability_assignments={"chat": ["llamacpp:mistral"]},
        now="2026-07-11T00:00:00+00:00",
    )


def test_resident_aware_deterministic_selection_and_audit():
    runtime = engine()
    facts = [Availability("ollama", "llama3.1", "ready"), Availability("llamacpp", "mistral", "ready")]
    first = runtime.select("alfred", "chat", facts)
    second = runtime.select("alfred", "chat", facts)
    assert first["selected"] == "ollama:llama3.1"
    assert first["fallback_order"] == second["fallback_order"]
    assert runtime.audit_log[-1]["event"] == "model_selected"


def test_failover_never_crosses_cloud_boundary():
    runtime = engine()
    result = runtime.select("alfred", "chat", [Availability("ollama", "llama3.1", "offline"), Availability("llamacpp", "mistral", "ready"), Availability("openai", "gpt", "ready")])
    assert result["selected"] == "llamacpp:mistral"
    cloud = result["diagnostics"]["openai:gpt"]
    assert cloud["state"] == "prohibited"
    assert any(row["key"] == "openai:gpt" and row["reason"] == "state is prohibited" for row in result["considered"])


def test_unavailable_unknown_and_cold_start_are_truthful_not_selected():
    runtime = engine()
    result = runtime.select("alfred", "chat", [Availability("ollama", "llama3.1", "cold", "loading weights")])
    assert result["selected"] is None
    assert result["diagnostics"]["ollama:llama3.1"]["state"] == "cold"
    assert result["diagnostics"]["llamacpp:mistral"]["state"] == "unknown"


def test_evaluation_records_are_not_self_authorizing():
    runtime = engine()
    record = runtime.record_evaluation("alfred", "chat", "ollama:llama3.1", score=0.91, notes="comparison only", evaluator="resident-runtime")
    assert record["self_authorizing"] is False
    assert runtime.evaluations == [record]
