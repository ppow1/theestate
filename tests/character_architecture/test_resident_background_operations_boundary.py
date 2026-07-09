import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ALFRED_INTEGRATION = ROOT / "docs/residents/alfred/runtime/Alfred_Background_Operations_Integration_v0_1.md"
BOUNDARY = ROOT / "docs/character-architecture/Resident_Background_Operations_Boundary_v0_1.md"
CUEMASTERY_GATE = ROOT / "docs/character-architecture/CueMastery_Return_Gate_After_Resident_Standup.md"
OLD_CUEMASTERY_GATE = ROOT / "docs/character-architecture/Qmaster_Return_Gate_After_Resident_Standup.md"
NOMENCLATURE_GUARD = ROOT / "docs/character-architecture/Canonical_Nomenclature_Guard_v0_1.md"
FIXTURE = ROOT / "tests/fixtures/background_operations/resident_operation_requests_wp0224.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_alfred_background_operations_integration_exists_and_names_wp0617_owner():
    text = read(ALFRED_INTEGRATION)
    assert "WP-0617 owns the background operations runtime" in text
    assert "Alfred does not own a competing event loop" in text


def test_alfred_integration_does_not_define_competing_resident_runtime():
    text = read(ALFRED_INTEGRATION).lower()
    prohibited = [
        "resident-specific watch daemon",
        "resident event feed",
        "resident dispatch queue",
        "parallel status system",
    ]
    for phrase in prohibited:
        assert phrase in text
    assert "must never" in text
    assert "run the wp-0617 evaluator loop" in text


def test_boundary_artifact_preserves_role_separation():
    text = read(BOUNDARY).lower()
    assert "wp-0617 owns event watches" in text
    for role in ["residents", "personas", "workers", "providers", "offices", "background operations"]:
        assert role in text
    assert "distinct roles" in text
    assert "traffic controller" in text
    assert "replace validation" in text


def test_resident_operation_examples_are_wp0617_request_concepts():
    requests = json.loads(read(FIXTURE))
    expected = {
        "resident_standup_status_request",
        "resident_validation_review_request",
        "resident_identity_boundary_review_request",
        "cuemastery_return_gate_status_request",
    }
    assert {request["request_type"] for request in requests} == expected
    for request in requests:
        assert request["runtime_owner"] == "WP-0617"
        assert request["status"]
        assert isinstance(request["requires_steward_attention"], bool)


def test_cuemastery_return_gate_contains_required_principle_and_wp0617_transition():
    text = read(CUEMASTERY_GATE)
    assert "Resident work exists to support Estate execution and CueMastery progress. It must not become an indefinite blocker to CueMastery." in text
    assert "WP-0617 background operations" in text
    assert "separate resident watch daemon or event runtime" in text


def test_cuemastery_nomenclature_repair_has_no_forbidden_active_terms():
    forbidden = [
        "Qmaster",
        "qmaster",
        "Q Master",
        "Q mastery",
        "Q Mastery",
        "queue mastery",
        "Queue Mastery",
        "QueueMastery",
        "Cue Mastery",
        "CUEMASTERY",
    ]
    active_paths = [
        CUEMASTERY_GATE,
        ALFRED_INTEGRATION,
        ROOT / "docs/residents/helen/Helen_Resident_Profile_v0_1.md",
        ROOT / "docs/residents/helen/runtime/Helen_Background_Operations_Integration_v0_1.md",
        ROOT / "collaboration/work_packages/pending/WP-0224_CHARACTER_ARCHITECTURE_resident_standup_sprint_qmaster_return_gate.md",
        ROOT / "collaboration/work_packages/completions/WP-0224_codex_cloud_web_done.json",
        FIXTURE,
    ]
    assert not OLD_CUEMASTERY_GATE.exists()
    for path in active_paths:
        text = read(path)
        assert "CueMastery" in text or "cuemastery" in text
        for term in forbidden:
            assert term not in text, (path, term)


def test_canonical_nomenclature_guard_records_cuemastery_and_ionoge():
    text = read(NOMENCLATURE_GUARD)
    assert "CueMastery" in text
    assert "`cuemastery`" in text
    assert "IONOGE" in text
    assert "eye-oh-no-gee" in text
    assert "`ionoge`" in text
