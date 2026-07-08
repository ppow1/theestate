import json
import subprocess
import sys

import pytest

from estate.core.provider_catalog import ProviderDescriptor, load_provider_catalog, write_office_status


def test_valid_provider_descriptor_accepted():
    provider = ProviderDescriptor.from_dict({
        "provider_id":"x.test", "display_name":"X", "provider_type":"planning",
        "implementation_kind":"stub", "status":"designed", "classification_ceiling":"Estate Internal",
        "capabilities":["planning"]
    })
    assert provider.provider_id == "x.test"
    assert provider.cost_model == "unknown"


def test_missing_provider_id_rejected():
    with pytest.raises(ValueError, match="provider_id is required"):
        ProviderDescriptor.from_dict({"display_name":"X","provider_type":"planning","implementation_kind":"stub","status":"designed","classification_ceiling":"Estate Internal","capabilities":["planning"]})


def test_unknown_provider_type_rejected():
    with pytest.raises(ValueError, match="unknown provider type"):
        ProviderDescriptor.from_dict({"provider_id":"x","display_name":"X","provider_type":"bad","implementation_kind":"stub","status":"designed","classification_ceiling":"Estate Internal","capabilities":["planning"]})


def test_unknown_status_rejected():
    with pytest.raises(ValueError, match="unknown status"):
        ProviderDescriptor.from_dict({"provider_id":"x","display_name":"X","provider_type":"planning","implementation_kind":"stub","status":"bad","classification_ceiling":"Estate Internal","capabilities":["planning"]})


def test_catalog_loads_successfully():
    catalog = load_provider_catalog()
    assert catalog.get_provider("chatgpt.planning.external").implementation_kind == "chatgpt"


def test_provider_lookup_by_id_works():
    assert load_provider_catalog().get_provider("stub.planning.echo").provider_type == "planning"


def test_provider_filtering_by_type_works():
    ids = [p.provider_id for p in load_provider_catalog().providers_by_type("planning")]
    assert "stub.planning.echo" in ids


def test_provider_filtering_by_capability_works():
    ids = [p.provider_id for p in load_provider_catalog().providers_with_capability("work_package_draft")]
    assert ids == ["chatgpt.planning.external"]


def test_office_catalog_status_export_is_generated(tmp_path):
    out = tmp_path / "catalog_status.json"
    write_office_status(load_provider_catalog(), out)
    payload = json.loads(out.read_text())
    assert payload["provider_count"] >= 5
    assert "planning" in payload["available_capabilities"]


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "estate.cli.main", *args], text=True, capture_output=True)


def test_cli_providers_list_succeeds():
    result = run_cli("providers-list")
    assert result.returncode == 0
    assert "chatgpt.planning.external" in result.stdout


def test_cli_providers_show_succeeds_for_known_provider():
    result = run_cli("providers-show", "--provider-id", "chatgpt.planning.external")
    assert result.returncode == 0
    assert "Capabilities:" in result.stdout


def test_cli_providers_show_fails_for_unknown_provider():
    result = run_cli("providers-show", "--provider-id", "missing.provider")
    assert result.returncode != 0
    assert "missing.provider" in result.stdout


def test_cli_providers_find_returns_matching_providers():
    result = run_cli("providers-find", "--capability", "work_package_draft")
    assert result.returncode == 0
    assert "chatgpt.planning.external" in result.stdout
