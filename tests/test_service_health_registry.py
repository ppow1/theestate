import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.service_health_registry import generate_service_health_registry, format_service_health_registry


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path, payload):
    write(path, json.dumps(payload))


def seed(root, services):
    write(root / "src/estate/cli/main.py", "cli")
    write_json(root / "data/registry/capabilities.json", [])
    write_json(root / "data/registry/providers.json", [])
    write_json(root / "data/registry/services.json", services)


def entry(payload, service_id):
    return next(e for e in payload["health_entries"] if e["service_id"] == service_id)


def test_health_registry_reports_required_states_and_source_links(tmp_path):
    seed(tmp_path, [
        {"id": "SVC-HEALTHY", "name": "Healthy", "status": "Active", "owner": "Ops", "dependencies": []},
        {"id": "SVC-DEGRADED", "name": "Degraded", "status": "Degraded", "owner": "Ops", "dependencies": ["SVC-HEALTHY"]},
        {"id": "SVC-UNAVAILABLE", "name": "Unavailable", "status": "Unavailable", "owner": "Ops", "dependencies": []},
        {"id": "SVC-UNKNOWN", "name": "Unknown", "status": "Draft", "owner": "Ops", "dependencies": []},
        {"id": "SVC-MISSING", "status": "Active", "dependencies": []},
    ])

    payload = generate_service_health_registry(tmp_path, write=False)

    assert entry(payload, "SVC-HEALTHY")["health_status"] == "healthy"
    assert entry(payload, "SVC-DEGRADED")["health_status"] == "degraded"
    assert entry(payload, "SVC-UNAVAILABLE")["health_status"] == "unavailable"
    assert entry(payload, "SVC-UNKNOWN")["health_status"] == "unknown"
    assert entry(payload, "SVC-MISSING")["health_status"] == "degraded"
    assert entry(payload, "SVC-DEGRADED")["dependency_health"]["dependencies"] == [{"service_id": "SVC-HEALTHY", "health_status": "healthy"}]
    for health_entry in payload["health_entries"]:
        assert health_entry["authoritative_sources"]
        assert all(link["path"] and link["available"] for link in health_entry["authoritative_sources"])


def test_unavailable_sources_are_graceful_and_markdown_read_only(tmp_path):
    seed(tmp_path, [{"id": "SVC-A", "name": "A", "status": "Active", "owner": "Ops", "dependencies": []}])
    (tmp_path / "data/registry/services.json").unlink()

    payload = generate_service_health_registry(tmp_path, write=True)
    markdown = format_service_health_registry(payload)

    assert payload["summary"]["service_count"] >= 0
    assert any(item.endswith("services.json") for item in payload["inputs"]["unavailable"])
    assert "does not replace monitoring systems" in markdown
    assert (tmp_path / "runtime/services/service_health_registry.json").exists()
    assert (tmp_path / "operations/services/service_health_registry.md").exists()


def test_service_health_registry_cli(tmp_path):
    seed(tmp_path, [{"id": "SVC-A", "name": "A", "status": "Active", "owner": "Ops", "dependencies": []}])

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "service-health-registry", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["service_count"] >= 1
    assert (tmp_path / "runtime/services/service_health_registry.json").exists()
