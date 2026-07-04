import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.estate_service_catalog import generate_estate_service_catalog, format_estate_service_catalog


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed_impl(root):
    write(root / "src/estate/cli/main.py", "parser commands")
    write(root / "src/estate/core/hr_onboarding.py", "impl")
    write(root / "docs/onboarding/Helen_HR_Operational_Onboarding.md", "doc")


def test_service_discovery_owner_mapping_and_command_aliases(tmp_path):
    seed_impl(tmp_path)
    write_json(tmp_path / "data/registry/services.json", [{"id": "SVC-HR", "name": "Registry HR Service", "status": "Active", "owner": "Human Resources", "resident": "Helen", "command_aliases": ["hr-onboard"]}])
    write_json(tmp_path / "data/registry/capabilities.json", [{"id": "CAP-HR", "name": "HR", "related_services": ["SVC-HR"]}])
    write_json(tmp_path / "data/registry/providers.json", [])

    catalog = generate_estate_service_catalog(tmp_path, write=False)

    registry_service = next(s for s in catalog["services"] if s["id"] == "SVC-HR")
    assert registry_service["owner"] == "Human Resources"
    assert registry_service["capabilities"] == ["CAP-HR"]
    assert registry_service["command_aliases"] == ["hr-onboard"]
    assert any(s["name"] == "Helen HR Employee Onboarding" and "helen-onboard" in s["command_aliases"] for s in catalog["services"])


def test_missing_metadata_and_source_link_integrity(tmp_path):
    seed_impl(tmp_path)
    write_json(tmp_path / "data/registry/services.json", [{"id": "SVC-MISSING"}])
    write_json(tmp_path / "data/registry/capabilities.json", [])
    write_json(tmp_path / "data/registry/providers.json", [])

    catalog = generate_estate_service_catalog(tmp_path, write=False)
    service = next(s for s in catalog["services"] if s["id"] == "SVC-MISSING")
    assert service["owner"] == "Unknown"
    assert any(w["type"] == "missing_name" for w in service["metadata_warnings"])
    assert all((tmp_path / src).exists() for item in catalog["services"] for src in item["source_artifact_links"] if src != "data/registry/services.json" or (tmp_path / src).exists())


def test_catalog_writes_outputs_and_markdown_notes_read_only(tmp_path):
    write_json(tmp_path / "data/registry/services.json", [])
    write_json(tmp_path / "data/registry/capabilities.json", [])
    write_json(tmp_path / "data/registry/providers.json", [])
    write(tmp_path / "src/estate/cli/main.py", "cli")

    payload = generate_estate_service_catalog(tmp_path, write=True)
    markdown = format_estate_service_catalog(payload)

    assert (tmp_path / "runtime/services/estate_service_catalog.json").exists()
    assert (tmp_path / "operations/services/estate_service_catalog.md").exists()
    assert "not the source of truth" in markdown
    assert "duplicate command registry" in markdown


def test_estate_service_catalog_cli(tmp_path):
    write_json(tmp_path / "data/registry/services.json", [])
    write_json(tmp_path / "data/registry/capabilities.json", [])
    write_json(tmp_path / "data/registry/providers.json", [])

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "estate-service-catalog", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["service_count"] >= 0
    assert (tmp_path / "runtime/services/estate_service_catalog.json").exists()
