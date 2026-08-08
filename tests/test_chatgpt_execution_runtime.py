from estate.core.chatgpt_execution_runtime import build_live_execution_router
from estate.core.consultation_store import ConsultationStore


def test_live_composition_uses_neutral_router_and_capability_binding(tmp_path):
    store = ConsultationStore(tmp_path / "consultations.sqlite3")
    router = build_live_execution_router(store, runtime_root=tmp_path)
    assert len(router.bindings) == 1
    binding = router.bindings[0]
    assert "software_engineering_test" in binding.capabilities
    assert binding.adapter.provider_id == "codex-cli-openai"
    assert binding.adapter.provider_type == "codex-cli"

