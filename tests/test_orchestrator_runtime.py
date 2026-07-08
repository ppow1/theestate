from estate.core.orchestrator_runtime import OrchestratorRuntimeState


def test_runtime_state_model_validates():
    state = OrchestratorRuntimeState.create(cycle_id="cyc-test", mode="dry_run")
    state.items_evaluated = 1
    state.finish()
    data = state.to_dict()
    assert data["orchestrator_id"] == "estate.orchestrator.local"
    assert data["state"] == "completed"
