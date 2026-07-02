import json
import subprocess
import sys
from pathlib import Path

from estate.core.document_registry import validate_document_registry

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data/registry/documents.json"


def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_registry_file_exists():
    assert REGISTRY.exists()


def test_required_paths_exist_or_are_explicitly_unresolved():
    registry = load_registry()
    for doc in registry["documents"]:
        if doc["resolved"]:
            assert (ROOT / doc["path"]).exists(), doc["path"]
        else:
            assert doc["status"] == "unresolved"
            assert doc["path"] == ""


def test_stale_constitution_path_is_not_current_path():
    paths = {doc["path"] for doc in load_registry()["documents"]}
    assert "constitution/constitution.md" in paths
    assert "constitution/Estate_Constitution.md" not in paths


def test_stable_ids_are_unique():
    ids = [doc["id"] for doc in load_registry()["documents"]]
    assert len(ids) == len(set(ids))


def test_json_schema_basics():
    registry = load_registry()
    assert registry["schema_version"] == "1.0"
    assert registry["registry_id"] == "REG-DOCUMENTS-0001"
    assert isinstance(registry["documents"], list)
    required = {"id", "title", "path", "category", "status", "audience", "source_of_truth", "notes", "superseded_paths", "resolved"}
    for doc in registry["documents"]:
        assert required <= set(doc)
        assert isinstance(doc["superseded_paths"], list)
        assert isinstance(doc["resolved"], bool)


def test_document_registry_validator_ok():
    assert validate_document_registry(ROOT)["ok"]


def test_cli_document_registry_json():
    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "document-registry", "--json"],
        cwd=ROOT,
        env={"PYTHONPATH": str(ROOT / "src")},
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["registry_id"] == "REG-DOCUMENTS-0001"
    assert any(doc["id"] == "DOC-CONSTITUTION" for doc in payload["documents"])
