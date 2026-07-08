import pytest

from estate.core.planning_provider_registry import default_planning_provider_registry


def test_registry_resolves_stub_provider():
    provider = default_planning_provider_registry().resolve("stub.planning.echo")
    assert provider.provider_id == "stub.planning.echo"


def test_missing_provider_fails_clearly():
    with pytest.raises(KeyError, match="not registered"):
        default_planning_provider_registry().resolve("missing.provider")
