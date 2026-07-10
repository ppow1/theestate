import json
from pathlib import Path

from estate.core.estate_knowledge_index import incremental_update, inspect_index, query_index, rebuild_index, status


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_rebuild_indexes_metadata_ranking_and_provenance(tmp_path):
    write(tmp_path / "constitution" / "constitution.md", "# Estate Constitution\nconstitutional recall doctrine")
    write(tmp_path / "collaboration" / "work_packages" / "pending" / "WP.md", "# Recall Work\nrecall recall alfred")
    write(tmp_path / "data" / "registry" / "documents.json", json.dumps({"documents": [{"id": "DOC-1", "path": "constitution/constitution.md", "category": "constitution", "source_of_truth": True}]}))

    payload = rebuild_index(tmp_path)

    assert payload["schema_version"] == "estate.knowledge_index.v1"
    assert payload["record_count"] >= 3
    constitution = next(r for r in payload["records"] if r["path"] == "constitution/constitution.md")
    assert constitution["artifact_type"] == "constitutional_record"
    assert constitution["owner"] == "constitution"
    assert constitution["provenance"]["registry_id"] == "DOC-1"
    assert constitution["source_hash"]

    result = query_index("recall", root=tmp_path)
    assert result["results"][0]["score"] >= result["results"][-1]["score"]
    assert result["results"][0]["path"] == "collaboration/work_packages/pending/WP.md"
    assert "not newly approved institutional truth" in result["truth_notice"]


def test_incremental_refresh_and_stale_missing_detection(tmp_path):
    target = tmp_path / "operations" / "validation" / "report.md"
    write(target, "# Validation\nfirst")
    rebuild_index(tmp_path)

    target.write_text("# Validation\nsecond", encoding="utf-8")
    inspection = inspect_index(tmp_path)
    assert inspection["stale_entries"] == ["operations/validation/report.md"]

    updated = incremental_update(tmp_path)
    assert updated["last_incremental"]["changed"] == ["operations/validation/report.md"]
    assert inspect_index(tmp_path)["ok"]

    target.unlink()
    missing = inspect_index(tmp_path)
    assert missing["missing_entries"] == ["operations/validation/report.md"]


def test_query_filters_private_content_by_default(tmp_path):
    write(tmp_path / "residents" / "public.md", "# Public\nshared keyword")
    write(tmp_path / "residents" / "private" / "secret.md", "# Secret\nprivate keyword")
    rebuild_index(tmp_path)

    public = query_index("keyword", root=tmp_path)
    assert [r["path"] for r in public["results"]] == ["residents/public.md"]

    private = query_index("keyword", root=tmp_path, include_private=True, classification="protected_private")
    assert [r["path"] for r in private["results"]] == ["residents/private/secret.md"]

    filtered = query_index("keyword", root=tmp_path, artifact_type="resident_artifact", owner="resident_office")
    assert filtered["match_count"] == 1
    assert status(tmp_path)["record_count"] >= 2
