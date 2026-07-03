import json

import pytest

from estate.core.interaction_adapters import (
    InteractionAdapterRegistryError,
    adapters_by_type,
    get_interaction_adapter,
    load_interaction_adapter_registry,
)


def write_registry(path, adapters):
    path.write_text(
        json.dumps({"version": "test", "adapters": adapters}), encoding="utf-8"
    )


def adapter(adapter_id="voice.stt.mock", adapter_type="voice_stt"):
    return {
        "adapter_id": adapter_id,
        "display_name": "Mock Adapter",
        "adapter_type": adapter_type,
        "status": "available",
        "local_first": True,
        "provider": "estate.test.MockAdapter",
        "configuration_required": False,
        "secrets_required": False,
        "authority_boundary": "Routes significant actions to governed Estate services.",
        "source_of_truth_boundary": "Does not replace institutional source artifacts.",
        "related_workspace": "Test workspace",
        "notes": "Test adapter.",
    }


def test_registry_loading_returns_adapter_entries(tmp_path):
    registry_path = tmp_path / "interaction_adapters.json"
    write_registry(registry_path, [adapter()])

    registry = load_interaction_adapter_registry(registry_path)

    assert registry["ok"] is True
    assert registry["version"] == "test"
    assert registry["adapters"][0].adapter_id == "voice.stt.mock"


def test_missing_registry_degrades_gracefully(tmp_path):
    missing_path = tmp_path / "missing.json"

    registry = load_interaction_adapter_registry(missing_path)

    assert registry["ok"] is False
    assert registry["reason"] == "interaction_adapter_registry_missing"
    assert get_interaction_adapter("voice.stt.mock", missing_path) is None
    assert adapters_by_type("voice_stt", missing_path) == []


def test_duplicate_adapter_ids_are_rejected(tmp_path):
    registry_path = tmp_path / "interaction_adapters.json"
    write_registry(registry_path, [adapter(), adapter()])

    with pytest.raises(
        InteractionAdapterRegistryError, match="duplicate interaction adapter IDs"
    ):
        load_interaction_adapter_registry(registry_path)


def test_adapter_category_filtering(tmp_path):
    registry_path = tmp_path / "interaction_adapters.json"
    write_registry(
        registry_path,
        [
            adapter("voice.stt.mock", "voice_stt"),
            adapter("voice.tts.mock", "voice_tts"),
            adapter("voice.stt.local", "voice_stt"),
        ],
    )

    stt_adapters = adapters_by_type("voice_stt", registry_path)

    assert [entry.adapter_id for entry in stt_adapters] == [
        "voice.stt.mock",
        "voice.stt.local",
    ]
    assert (
        get_interaction_adapter("voice.tts.mock", registry_path).adapter_type
        == "voice_tts"
    )
