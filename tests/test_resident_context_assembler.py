from pathlib import Path

from estate.core.resident_context_assembler import AssemblyRequest, ResidentContextAssembler, SourceItem

ROOT = Path(__file__).resolve().parents[1]


def assemble(extra_sources, **kwargs):
    request = AssemblyRequest(
        resident_id="RES-000003",
        task="Prepare Helen for Grace onboarding; blocker: pending privacy review.",
        query_terms=("onboarding", "Grace"),
        **kwargs,
    )
    return ResidentContextAssembler(ROOT).assemble(request, extra_sources)


def test_context_is_resident_specific_source_linked_and_contains_required_core_sections():
    packet = assemble([
        SourceItem(
            id="mail.grace",
            kind="recent_relevant_communication",
            title="Grace onboarding notice",
            body="Helen recommended Grace for governed onboarding.",
            resident_id="RES-000003",
            path="collaboration/messages/msg_helen_20260710_0001_grace_hiring_recommendation.json",
            modified_at="2026-07-10T00:00:00Z",
            relevance=500,
        ),
        SourceItem(
            id="knowledge.grace",
            kind="knowledge_index_record",
            title="Grace hiring gate",
            body="Knowledge index hit about Grace onboarding dependencies.",
            path="runtime/search/estate_knowledge_index.json",
            relevance=400,
        ),
    ])

    kinds = {section["kind"] for section in packet["sections"]}
    assert "canonical_resident_profile" in kinds
    assert "office_role_state" in kinds
    assert "current_task" in kinds
    assert "recent_relevant_communication" in kinds
    assert "knowledge_index_record" in kinds
    assert all(section["source_citation"]["id"] for section in packet["sections"])
    assert packet["resident_id"] == "RES-000003"


def test_privacy_and_classification_filter_before_assembly_with_reasons():
    packet = assemble([
        SourceItem(
            id="journal.private",
            kind="continuity_artifact",
            title="Private journal",
            body="Protected reflections must never enter prompt assembly.",
            resident_id="RES-000003",
            tags=("protected_private_character_material",),
            classification="Protected",
            relevance=9999,
        ),
        SourceItem(
            id="continuity.unapproved",
            kind="continuity_artifact",
            title="Draft continuity",
            body="Unapproved memory draft.",
            resident_id="RES-000003",
            approved=False,
        ),
    ])

    omitted = {item["id"]: item["reason"] for item in packet["omitted_sources"]}
    assert omitted["journal.private"] == "privacy boundary: prohibited source category"
    assert omitted["continuity.unapproved"] == "continuity artifact is not approved"
    assert "journal.private" not in {section["id"] for section in packet["sections"]}


def test_stale_unavailable_irrelevant_and_budget_omissions_are_explicit_and_deterministic():
    sources = [
        SourceItem(
            id="continuity.approved.stale",
            kind="continuity_artifact",
            title="Approved but old continuity",
            body="Approved continuity artifact.",
            resident_id="RES-000003",
            approved=True,
            modified_at="2026-05-01T00:00:00Z",
            relevance=300,
        ),
        SourceItem(
            id="knowledge.irrelevant",
            kind="knowledge_index_record",
            title="Garden inventory",
            body="Unrelated seed catalog.",
            relevance=200,
        ),
        SourceItem(
            id="empty.communication",
            kind="recent_relevant_communication",
            title="Missing message body",
            body="",
            resident_id="RES-000003",
            relevance=100,
        ),
        SourceItem(
            id="large.low.priority",
            kind="source_citation",
            title="Large citation appendix",
            body="x" * 10_000,
            relevance=1,
        ),
    ]

    first = assemble(sources, max_chars=2500)
    second = assemble(reversed(sources), max_chars=2500)
    assert first == second
    assert any(section["id"] == "continuity.approved.stale" and section["stale_warning"] for section in first["sections"])
    omitted = {item["id"]: item["reason"] for item in first["omitted_sources"]}
    assert omitted["knowledge.irrelevant"] == "knowledge record is not relevant to request terms"
    assert omitted["empty.communication"] == "source unavailable or empty"
    assert omitted["large.low.priority"] == "deterministic context budget exceeded"
