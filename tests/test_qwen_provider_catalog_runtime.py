import json
from pathlib import Path

import pytest

from estate.core.provider_catalog import load_provider_catalog
from estate.core.gpu_runtime_lanes import load_registered_lanes


ROOT = Path(__file__).resolve().parents[1]


def test_canonical_catalog_registers_qwen_local_text():
    provider = load_provider_catalog(ROOT / "config/providers/catalog.json").get_provider("qwen.local.text")
    assert provider.provider_id == "qwen.local.text"
    assert provider.provider_type == "execution"


def test_unknown_provider_still_fails_closed():
    with pytest.raises(KeyError, match="not registered"):
        load_provider_catalog(ROOT / "config/providers/catalog.json").get_provider("unknown.provider")


def test_qualified_lanes_share_qwen_provider_identity():
    lanes = {lane.runtime_lane_id: lane for lane in load_registered_lanes(ROOT)}
    assert lanes["qwen.local.text.4090"].provider_id == "qwen.local.text"
    assert lanes["qwen.local.text.p100-1"].provider_id == "qwen.local.text"


def test_catalog_is_the_deployment_artifact():
    payload = json.loads((ROOT / "config/providers/catalog.json").read_text(encoding="utf-8"))
    assert any(item.get("provider_id") == "qwen.local.text" for item in payload["providers"])
