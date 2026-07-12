from pathlib import Path
import json, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from wp4053_preferences.engine import Evidence, PreferenceRecord, PreferenceStore, SENSITIVITY_RELATIONSHIP

def ev(ref, day=1, model=False):
    return Evidence(ref, ref, f"2026-07-{day:02d}T00:00:00Z", model_generated=model)

def load_fixture(name):
    data = json.loads((ROOT / "fixtures" / name).read_text())
    return [PreferenceRecord(**r) for r in data]

def test_seeded_wardrobe_preference_remains_stable_without_new_evidence():
    store = PreferenceStore(load_fixture("grace_preferences.json"))
    rec = store.get("grace", "clothing_wardrobe", "work_blazer")
    assert rec.state == "seeded"
    assert rec.value == "structured navy blazer"
    assert rec.evidence_refs == ["docs/residents/grace/Grace_Resident_Profile_v0_1.md"]

def test_repeated_accepted_experiences_promote_emerging_to_established():
    store = PreferenceStore()
    for i in range(1,4):
        store.observe("grace","food_drink","afternoon_tea","mint tea", ev(f"accepted-summary:tea-{i}", i))
    rec = store.promote("grace","food_drink","afternoon_tea", authority="accepted-continuity-review")
    assert rec.state == "established"
    assert rec.confidence >= 0.75

def test_one_off_response_does_not_create_durable_preference_and_model_cannot_self_authorize():
    store = PreferenceStore()
    rec = store.observe("grace","humor_conversational_style","puns","likes puns", ev("accepted-summary:one", 1))
    assert rec.state == "emerging"
    try:
        store.promote("grace","humor_conversational_style","puns", authority="model-output")
    except ValueError as exc:
        assert "approved authority" in str(exc)
    else:
        raise AssertionError("promotion should fail")
    try:
        store.observe("grace","food_drink","coffee","espresso", ev("llm-response:raw", 2, model=True))
    except ValueError as exc:
        assert "model output" in str(exc)

def test_resident_can_experiment_without_abandoning_established_identity():
    store = PreferenceStore(load_fixture("grace_preferences.json"))
    exp = store.experiment("grace","clothing_wardrobe","weekend_scarf","bright red scarf", ev("resident-journal:experiment", 3))
    seeded = store.get("grace", "clothing_wardrobe", "work_blazer")
    assert exp.state == "experimenting"
    assert seeded.state == "seeded"

def test_changed_preference_preserves_prior_value_and_reason():
    store = PreferenceStore()
    for i in range(1,4): store.observe("ingrid","routines_rituals","morning_start","early quiet review", ev(f"sum:{i}", i))
    store.promote("ingrid","routines_rituals","morning_start", authority="accepted-continuity-review")
    changed = store.change("ingrid","routines_rituals","morning_start","later collaborative standup", reason="new team rhythm", authority="Steward-approved", evidence=ev("steward:approved-change", 5))
    assert changed.state == "changed"
    assert changed.prior_value_lineage[-1]["value"] == "early quiet review"
    assert changed.reason_for_change == "new team rhythm"

def test_contextual_preferences_do_not_leak_across_settings():
    store = PreferenceStore()
    store.observe("ingrid","office_environment","lighting","dim", ev("sum:focus", 1), context_scope={"setting":"focus"})
    assert store.get("ingrid","office_environment","lighting", {"setting":"focus"}).value == "dim"
    assert store.get("ingrid","office_environment","lighting", {"setting":"briefing"}).state == "unknown"

def test_evelyn_private_relationship_preferences_hidden_from_unauthorized_surfaces():
    store = PreferenceStore(load_fixture("evelyn_preferences.json"))
    assert store.visible_records("alfred", resident_id="evelyn") == []
    assert store.visible_records("helen", resident_id="evelyn") == []
    assert store.visible_records("grace", resident_id="evelyn") == []
    assert store.visible_records("global_search", resident_id="evelyn") == []
    assert store.visible_records("office", resident_id="evelyn", office_payload=True) == []
    assert store.visible_records("steward", resident_id="evelyn")[0]["sensitivity"] == SENSITIVITY_RELATIONSHIP

def test_conflicting_evidence_creates_disputed_not_overwrite():
    store = PreferenceStore()
    for i in range(1,4): store.observe("grace","food_drink","tea","mint", ev(f"sum:{i}", i))
    store.promote("grace","food_drink","tea", authority="accepted-continuity-review")
    rec = store.observe("grace","food_drink","tea","black coffee", ev("accepted-summary:conflict", 4))
    assert rec.state == "disputed"
    assert rec.value == "mint"

def test_forget_request_retires_with_minimum_audit_metadata():
    store = PreferenceStore(load_fixture("ingrid_preferences.json"))
    rec = store.retire("ingrid","music_books_film_art","focus_music", reason="resident forget request", authority="Steward-approved", evidence_ref="request:forget-001", context_scope={"setting":"office_focus"}, forget=True)
    assert rec.state == "retired"
    assert rec.value is None and rec.evidence_refs == []
    assert rec.forget_retire_markers["minimal_audit_only"] is True

def test_provider_replacement_does_not_erase_established_preferences():
    store = PreferenceStore(load_fixture("ingrid_preferences.json"))
    before = store.get("ingrid","music_books_film_art","focus_music", {"setting":"office_focus"})
    after = PreferenceStore([before]).get("ingrid","music_books_film_art","focus_music", {"setting":"office_focus"})
    assert after.state == "established" and after.value == before.value

def test_identity_anchor_changes_are_blocked_without_review():
    store = PreferenceStore()
    try:
        store.observe("grace","authority","tool_access","merge rights", ev("raw:bad", 1))
    except ValueError as exc:
        assert "identity anchors" in str(exc)
    else:
        raise AssertionError("identity anchor update should fail")
