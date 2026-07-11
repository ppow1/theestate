import json

from estate.core.unified_institutional_search import search_institutional


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_unified_search_ranking_filters_privacy_provenance_navigation(tmp_path):
    write(tmp_path / "collaboration/work_packages/pending/WP-4020.md", "# Search Package\nWP-4020 unified search search accepted status pending")
    write(tmp_path / "operations/validation/reports/report.md", "# Validation Search\nunified search validation")
    write(tmp_path / "residents/private/reflection.md", "# Private Search\nprivate unified search")

    payload = search_institutional({"query": "unified search", "source_type": "work_package", "office": "collaboration", "limit": 5}, root=tmp_path, refresh=True)

    assert payload["schema_version"] == "estate.institutional_search.v1"
    assert payload["results"][0]["path"] == "collaboration/work_packages/pending/WP-4020.md"
    assert payload["results"][0]["source_type"] == "work_package"
    assert payload["results"][0]["owning_office"] == "collaboration"
    assert payload["results"][0]["navigation"]["tab"] == "work-packages"
    assert payload["results"][0]["provenance"]["truth_kind"] == "institutional_source_projection"
    assert payload["diagnostics"]["permission_filtered_count"] >= 1

    private = search_institutional({"query": "private unified", "include_private": True, "caller_context": {"role": "steward"}}, root=tmp_path)
    assert private["results"][0]["classification"] == "protected_private"


def test_unified_search_diagnostics_zero_and_stale(tmp_path):
    target = tmp_path / "docs/manual.md"
    write(target, "# Manual\nsearch box")
    search_institutional("search box", root=tmp_path, refresh=True)
    target.write_text("# Manual\nchanged", encoding="utf-8")

    payload = search_institutional({"query": "nothing-matches", "source_type": "manual"}, root=tmp_path, refresh=False)

    assert payload["diagnostics"]["zero_results"] is True
    assert payload["diagnostics"]["stale_index"] is True
    assert "docs/manual.md" in payload["diagnostics"]["stale_entries"]


def test_unified_cli_json_contract(tmp_path, monkeypatch, capsys):
    write(tmp_path / "operations/validation/report.md", "# Search Validation\nidentifier US-123")
    from estate.cli.main import main
    import sys

    monkeypatch.setattr(sys, "argv", ["estate", "institutional-search", "US-123", "--source-type", "validation", "--json", "--root", str(tmp_path)])
    main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["results"][0]["source_type"] == "validation_report"
    assert payload["results"][0]["navigation"]["tab"] == "validation"
