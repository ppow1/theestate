import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.dependency_graph import generate_dependency_graph, format_dependency_graph_markdown


def write_text(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_json(root, rel, payload):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_valid_dependency_extraction(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [
        {"id": "CAP-1", "name": "Capability One", "depends_on": ["SVC-1"]}
    ])
    write_json(tmp_path, "data/registry/services.json", [{"id": "SVC-1", "name": "Service One"}])
    write_text(tmp_path, "collaboration/work_packages/WP-1.md", "# WP-1\n\n## Dependencies\n- CAP-1\n")

    graph = generate_dependency_graph(tmp_path)

    assert {edge["source"] for edge in graph["edges"]} >= {"CAP-1", "WP-1"}
    assert any(edge["target"] == "SVC-1" and edge["dependency_type"] == "depends_on" for edge in graph["edges"])
    assert any(edge["target"] == "CAP-1" and edge["dependency_type"] == "dependencies" for edge in graph["edges"])
    assert (tmp_path / "runtime" / "dependencies" / "dependency_graph.json").exists()
    assert (tmp_path / "operations" / "dependencies" / "dependency_graph.md").exists()


def test_missing_dependency_fields_warn_and_orphan(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [{"id": "CAP-ORPHAN", "name": "Orphan"}])

    graph = generate_dependency_graph(tmp_path, write=False)

    assert any(w["type"] == "missing_dependency_field" and "CAP-ORPHAN" in w["message"] for w in graph["warnings"])
    assert any(node["id"] == "CAP-ORPHAN" for node in graph["orphaned_items"])


def test_malformed_json_warns_without_failure(tmp_path):
    write_text(tmp_path, "collaboration/messages/bad.json", "{not-json")

    graph = generate_dependency_graph(tmp_path, write=False)

    assert any(w["type"] == "malformed_json" and w["path"] == "collaboration/messages/bad.json" for w in graph["warnings"])


def test_markdown_generation_documents_schema_and_limitations(tmp_path):
    write_text(tmp_path, "operations/runbook.md", "# Runbook\n\nRequires: CAP-1, SVC-1\n")
    graph = generate_dependency_graph(tmp_path, write=False)

    markdown = format_dependency_graph_markdown(graph)

    assert markdown.startswith("# Estate Dependency Graph")
    assert "## Supported dependency sources" in markdown
    assert "## Graph schema" in markdown
    assert "does not infer hidden dependencies" in markdown
    assert "`Runbook` -> `CAP-1`" in markdown


def test_dependency_graph_cli_registration(tmp_path):
    write_json(tmp_path, "data/registry/capabilities.json", [
        {"id": "CAP-1", "dependencies": ["CAP-0"]}
    ])

    result = subprocess.run(
        [sys.executable, "-m", "estate.cli.main", "dependency-graph", "--json"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["edge_count"] == 1
    assert payload["edges"][0]["source"] == "CAP-1"
