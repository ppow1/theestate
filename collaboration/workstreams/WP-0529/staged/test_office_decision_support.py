from pathlib import Path

from office_decision_support import WorkItem, build_decision_support, explain_work_item, summarize_next_actions


def sample_items(tmp_path: Path):
    for path in [
        "docs/control.md",
        "workspaces/ready",
        "docs/dep.md",
        "workspaces/dep",
        "evidence/validation.json",
    ]:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(path, encoding="utf-8")
    return [
        WorkItem(
            id="DEP-1",
            title="Accepted dependency",
            state="accepted",
            controlling_artifact="docs/dep.md",
            workspace="workspaces/dep",
            updated_at="2026-07-09T00:00:00Z",
        ),
        WorkItem(
            id="READY-1",
            title="Ready recommendation",
            state="validated",
            controlling_artifact="docs/control.md",
            workspace="workspaces/ready",
            dependencies=("DEP-1",),
            evidence={"validation": "evidence/validation.json"},
            alternatives=({"path": "defer", "reason": "Operator may wait for business window."},),
            updated_at="2026-07-09T00:00:00Z",
        ),
        WorkItem(
            id="BLOCKED-1",
            title="Blocked work",
            state="proposed",
            controlling_artifact="docs/missing.md",
            workspace="workspaces/missing",
            dependencies=("UNKNOWN-DEP",),
            blockers=("pending executive acceptance",),
            evidence={"validation": "evidence/missing.json"},
            updated_at="not-a-date",
        ),
    ]


def test_explains_blockers_dependencies_missing_evidence_and_alternatives(tmp_path):
    support = build_decision_support(sample_items(tmp_path), root=tmp_path)
    blocked = explain_work_item(support, "BLOCKED-1")
    assert blocked["status"] == "blocked"
    assert "pending executive acceptance" in blocked["explanation"]["blockers"]
    assert blocked["explanation"]["dependencies"] == [{"id": "UNKNOWN-DEP", "status": "missing", "state": None, "controlling_artifact": None, "workspace": None}]
    assert {item["kind"] for item in blocked["explanation"]["missing_evidence"]} == {"controlling_artifact", "workspace", "validation"}
    ready = explain_work_item(support, "READY-1")
    assert ready["status"] == "ready"
    assert ready["explanation"]["dependencies"][0]["status"] == "satisfied"
    assert ready["alternatives"][0]["path"] == "defer"


def test_recommendations_are_advisory_and_ranked_without_state_mutation(tmp_path):
    items = sample_items(tmp_path)
    before = [item.state for item in items]
    support = build_decision_support(items, root=tmp_path)
    after = [item.state for item in items]
    assert before == after
    ready = explain_work_item(support, "READY-1")
    assert ready["governance_boundary"] == {
        "recommendation": True,
        "authorization": False,
        "execution": False,
        "validation": False,
        "acceptance": False,
        "note": "This staged decision support output is advisory only and does not mutate authority or state.",
    }
    assert ready["indicators"]["confidence"]["level"] == "high"
    blocked = explain_work_item(support, "BLOCKED-1")
    assert blocked["indicators"]["freshness"]["status"] == "unknown"
    summary = summarize_next_actions(support)
    assert [row["id"] for row in summary] == ["BLOCKED-1", "READY-1", "DEP-1"]
