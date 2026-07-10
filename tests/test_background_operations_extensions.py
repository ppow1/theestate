import pytest

from estate.core.background_operations import default_background_operation_watches
from estate.core.background_operations_extensions import BackgroundOperationsExtension, extension_from_watch_provider


def test_extension_contract_accepts_builtin_watch_provider():
    ext = extension_from_watch_provider(
        extension_id="estate_builtin_monitoring",
        name="Estate built-in monitoring",
        version="1.0.0",
        classification="Estate Internal",
        watches=default_background_operation_watches(),
    )
    payload = ext.to_dict()
    assert "watch_provider" in payload["capabilities"]
    assert payload["canonical_boundaries"]["no_traffic_controller_bypass"] is True


def test_extension_contract_rejects_invalid_identity_and_capability():
    with pytest.raises(ValueError):
        BackgroundOperationsExtension.from_dict({
            "extension_id": "Bad Extension!",
            "name": "Bad",
            "version": "1.0.0",
            "enabled": True,
            "classification": "Estate Internal",
            "capabilities": ["execute_any_file"],
        })
