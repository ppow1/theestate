import json

from estate.core.institutional_search import (
    build_institutional_search_index,
    classify_path,
    search_institutional_index,
)


def test_indexing_representative_documents(tmp_path):
    (tmp_path / "AI_START_HERE.md").write_text("# Start Here\nChief Architect orientation.", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/policy.md").write_text("# Policy Title\nEstate guidance.", encoding="utf-8")
    index = build_institutional_search_index(tmp_path)

    paths = {record["path"]: record for record in index["records"]}
    assert paths["AI_START_HERE.md"]["title"] == "Start Here"
    assert paths["docs/policy.md"]["artifact_type"] == "document"
    assert (tmp_path / "runtime/search/institutional_search_index.json").exists()


def test_generated_artifacts_are_labeled_not_authoritative(tmp_path):
    path = tmp_path / "operations/alfred/operational_briefing.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Briefing\nGenerated Chief Architect view.", encoding="utf-8")

    index = build_institutional_search_index(tmp_path)
    record = next(r for r in index["records"] if r["path"] == "operations/alfred/operational_briefing.md")
    assert record["policy_classification"] == "generated_operational_projection"
    assert record["authoritative"] is False
    assert classify_path("collaboration/messages/msg.json")["authoritative"] is True


def test_keyword_search_returns_path_and_excerpt(tmp_path):
    msg = tmp_path / "collaboration/messages/msg.json"
    msg.parent.mkdir(parents=True)
    msg.write_text(json.dumps({"id": "msg", "payload": {"title": "Chief Architect memorandum", "body": "Searchable institutional note."}}), encoding="utf-8")

    result = search_institutional_index("Chief Architect", tmp_path)
    assert result["match_count"] == 1
    assert result["matches"][0]["path"] == "collaboration/messages/msg.json"
    assert "Chief Architect" in result["matches"][0]["excerpt"]


def test_missing_directory_warnings(tmp_path):
    (tmp_path / "AI_HINTS.md").write_text("# Hints", encoding="utf-8")
    index = build_institutional_search_index(tmp_path)
    assert any("missing location: docs" == warning for warning in index["warnings"])


def test_cli_json_output(tmp_path, monkeypatch, capsys):
    doc = tmp_path / "archive/institutional_memory/memo.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Chief Architect Memorandum\nInstitutional search evidence.", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    from estate.cli.main import main
    import sys

    monkeypatch.setattr(sys, "argv", ["estate", "estate-search", "Chief Architect", "--json"])
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["query"] == "Chief Architect"
    assert payload["matches"][0]["path"] == "archive/institutional_memory/memo.md"
