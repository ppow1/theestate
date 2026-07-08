import pytest

from estate.core.provider_capabilities import ProviderCapability


def test_valid_capability_accepted():
    cap = ProviderCapability.from_dict({"capability_id":"planning","display_name":"Planning","category":"planning"})
    assert cap.capability_id == "planning"
    assert cap.input_artifacts == []


def test_capability_missing_id_rejected():
    with pytest.raises(ValueError, match="capability_id is required"):
        ProviderCapability.from_dict({"display_name":"Planning","category":"planning"})
