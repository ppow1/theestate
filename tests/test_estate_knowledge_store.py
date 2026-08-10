import json
import sqlite3
import time
from pathlib import Path

import pytest

from estate.core.estate_knowledge_store import (
    KnowledgeStoreError,
    build_index_packet,
    coverage,
    graph,
    init_store,
    lifecycle_candidates,
    query_assets,
    rebuild,
    scan,
    stale_assets,
    store_status,
    unknown_assets,
)


def _root(tmp_path: Path) -> Path:
    (tmp_path / "src/demo").mkdir(parents=True)
    (tmp_path / "docs/operations/troubleshooting").mkdir(parents=True)
    (tmp_path / "src/demo/known.py").write_text("# known component\n", encoding="utf-8")
    (tmp_path / "src/demo/unknown.xyz").write_text("opaque\n", encoding="utf-8")
    (tmp_path / "docs/operations/troubleshooting/note.md").write_text("# operational note\n", encoding="utf-8")
    return tmp_path


def test_fresh_store_migrates_and_newer_schema_fails_closed(tmp_path):
    root = _root(tmp_path)
    result = init_store(root)
    assert result["migration_version"] == 6
    db = root / "runtime/search/estate_knowledge_index.sqlite3"
    with sqlite3.connect(db) as connection:
        connection.execute("PRAGMA user_version=99")
    with pytest.raises(KnowledgeStoreError, match="newer than supported"):
        store_status(root)


def test_bounded_scan_is_incremental_and_preserves_unknown_reason(tmp_path):
    root = _root(tmp_path)
    first = scan(root, scope="src/demo")
    second = scan(root, scope="src/demo")
    assert first["files_processed"] == 2
    assert second["files_unchanged"] == 2
    unknown = unknown_assets(root)
    assert any(row["current_path"].endswith("unknown.xyz") for row in unknown["results"])
    assert any("purpose unresolved" in row["unknown_reason"] for row in unknown["results"])
    (root / "src/demo/known.py").write_text("# changed component\n", encoding="utf-8")
    changed = scan(root, scope="src/demo")
    assert changed["files_processed"] == 2
    assert changed["files_unchanged"] == 1


def test_comprehension_model_links_graph_packet_and_staleness(tmp_path):
    root = _root(tmp_path)
    model = {
        "components": [{
            "component_id": "demo",
            "title": "Demo component",
            "class": "service",
            "owner": "Operations",
            "source_paths": ["src/demo/known.py"],
            "knowledge_refs": ["candidate.demo"],
        }],
        "relationships": [],
        "workflows": [{"workflow_id": "WF.DEMO", "title": "Demo flow", "component_ids": ["demo"]}],
        "checkpoints": [{"checkpoint_id": "CP.DEMO", "workflow_id": "WF.DEMO", "component_id": "demo", "sequence": 1, "probe": "read the file", "evidence_source": "src/demo/known.py"}],
        "failure_seams": [{"seam_id": "SEAM.DEMO", "title": "Demo seam", "workflow_id": "WF.DEMO", "certainty": "CANDIDATE", "validation_state": "CANDIDATE"}],
    }
    model_path = root / "docs/operations/troubleshooting/comprehension.json"
    model_path.write_text(json.dumps(model), encoding="utf-8")
    scan(root, scope="src/demo")
    result = graph(root)
    assert {node["id"] for node in result["nodes"]} == {"demo"}
    packet = build_index_packet(root, "WF.DEMO")
    assert packet["provider_neutral"] is True
    assert packet["checkpoints"][0]["checkpoint_id"] == "CP.DEMO"
    assert packet["forbidden_actions"]
    assert query_assets("implementation", root=root)["match_count"] == 1
    (root / "src/demo/known.py").write_text("# changed\n", encoding="utf-8")
    scan(root, scope="src/demo")
    stale = stale_assets(root)
    assert any(row["current_path"] == "src/demo/known.py" for row in stale["results"])


def test_coverage_and_rebuild_are_queryable_and_non_authoritative(tmp_path):
    root = _root(tmp_path)
    scan(root, scope="src/demo")
    result = coverage(root)
    assert result["asset_count"] == 2
    assert result["scanned_count"] == 2
    assert lifecycle_candidates(root)["mutation_authorized"] is False
    rebuilt = rebuild(root, scope="src/demo")
    assert rebuilt["status"] == "COMPLETED"
    assert store_status(root)["asset_count"] == 2
