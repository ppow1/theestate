from pathlib import Path

from estate.core.office_unified_search import SafeAction, SearchDocument, build_query_contract, invoke_registered_action, pin_query, record_recent_search, unified_search


def docs(tmp_path: Path):
    (tmp_path / "collaboration/work_packages").mkdir(parents=True, exist_ok=True)
    (tmp_path / "collaboration/work_packages/WP-1.md").write_text("search work package", encoding="utf-8")
    return [
        SearchDocument("WP-1", "work_package", "Unified Search WP", "cross domain search command", "collaboration/work_packages/WP-1.md", "office://work-packages/WP-1", "2026-07-10T00:00:00Z", ("office",)),
        SearchDocument("RES-1", "resident", "Helen Resident", "resident command collaboration", None, "office://residents/RES-1", "2026-07-10T00:00:00Z", ("people",)),
        SearchDocument("VAL-1", "validation", "Search validation", "validation evidence", "missing/VAL-1.json", "office://validation/VAL-1", "2020-01-01T00:00:00Z", ("evidence",)),
        SearchDocument("DEC-1", "decision", "Decision record", "architecture decision for search", None, "office://decisions/DEC-1", None, ("governance",)),
        SearchDocument("GIT-1", "git_evidence", "Git evidence", "commit evidence for staged work", None, "office://git/GIT-1", "2026-07-10T00:00:00Z", ("evidence",)),
        SearchDocument("ART-1", "artifact", "Source artifact", "artifact navigation", None, "office://artifacts/ART-1", "2026-07-10T00:00:00Z", ("artifact",)),
        SearchDocument("CONV-1", "conversation", "Conversation", "conversation about unified search", None, "office://conversations/CONV-1", "2026-07-10T00:00:00Z", ("mail",)),
    ]


def test_cross_domain_search_filtering_navigation_and_freshness(tmp_path):
    contract = build_query_contract("search", categories=["work_package", "resident", "validation", "decision", "git_evidence", "artifact", "conversation"], filters={}, limit=10)
    result = unified_search(contract, docs(tmp_path), root=tmp_path, stale_after_days=30)
    categories = {item["category"] for item in result["results"]}
    assert {"work_package", "validation", "decision", "conversation"}.issubset(categories)
    assert result["results"][0]["navigation"]["destination"].startswith("office://")
    assert "missing source: VAL-1" in result["warnings"]

    filtered = unified_search(build_query_contract("evidence", filters={"tag": "evidence"}), docs(tmp_path), root=tmp_path)
    assert {item["id"] for item in filtered["results"]} == {"VAL-1", "GIT-1"}

    fresh_only = unified_search(build_query_contract("validation", include_stale=False), docs(tmp_path), root=tmp_path, stale_after_days=30)
    assert fresh_only["results"] == []


def test_safe_registered_action_invocation_and_arbitrary_command_rejection():
    registry = {"office.open.validation": SafeAction("office.open.validation", "Open Validation", "office://validation", lambda payload: {"status": "opened", "payload": dict(payload)})}
    ok = invoke_registered_action("office.open.validation", registry, {"id": "VAL-1"})
    assert ok["ok"] and ok["status"] == "opened" and ok["destination"] == "office://validation"
    assert invoke_registered_action("shell:rm -rf /", registry)["status"] == "rejected"
    assert invoke_registered_action("python:print(1)", registry)["status"] == "rejected"
    assert invoke_registered_action("https://example.com", registry)["status"] == "rejected"
    assert invoke_registered_action("unknown.action", registry)["status"] == "unregistered"


def test_recent_searches_and_pins_only_when_settings_permit():
    settings = {}
    assert record_recent_search(settings, "alpha", allow_recent_searches=False)["recent_searches"] == []
    assert pin_query(settings, "alpha", allow_pinned_queries=False)["pinned_queries"] == []
    settings = record_recent_search(settings, "alpha", allow_recent_searches=True)
    settings = record_recent_search(settings, "beta", allow_recent_searches=True)
    settings = pin_query(settings, "alpha", allow_pinned_queries=True)
    assert settings["recent_searches"] == ["beta", "alpha"]
    assert settings["pinned_queries"] == ["alpha"]
