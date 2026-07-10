from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELEN = ROOT / "docs/residents/helen"

REQUIRED_V0_1 = [
    HELEN / "Helen_Resident_Profile_v0_1.md",
    HELEN / "Helen_Resident_Validation_v0_1.md",
    HELEN / "runtime/Helen_Background_Operations_Integration_v0_1.md",
    HELEN / "platform-exports/textgen-4_9-helen-v0_1.yaml",
]

REQUIRED_V0_2 = [
    HELEN / "Helen_Resident_Profile_v0_2.md",
    HELEN / "Helen_Resident_Validation_v0_2.md",
    HELEN / "runtime/Helen_Workforce_Development_Runtime_Integration_v0_2.md",
    HELEN / "platform-exports/textgen-4_9-helen-v0_2.yaml",
]

REQUIRED_STANDUP = [
    HELEN / "Helen_Hiring_Onboarding_Workflow_v0_1.md",
    HELEN / "Helen_Local_Standup_Runbook_v0_1.md",
    HELEN / "Helen_Standup_Readiness_Matrix_v0_1.md",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_helen_resident_artifacts_exist():
    missing = [
        path
        for path in REQUIRED_V0_1 + REQUIRED_V0_2 + REQUIRED_STANDUP
        if not path.is_file()
    ]
    assert not missing


def test_helen_v0_1_profile_contains_required_boundaries():
    text = read(HELEN / "Helen_Resident_Profile_v0_1.md").lower()
    for phrase in [
        "workforce allocation",
        "reporting and authority boundaries",
        "office routing rules",
        "protected source",
        "no-impersonation",
        "connector honesty",
        "wp-0617",
        "does not own event watches",
    ]:
        assert phrase in text


def test_helen_v0_1_background_operations_boundary_is_explicit():
    text = read(HELEN / "runtime/Helen_Background_Operations_Integration_v0_1.md")
    assert "WP-0617 owns the background operations runtime" in text
    assert "Helen does not own a competing event loop" in text
    assert "must not run watches" in text
    assert "Traffic Controller" in text


def test_helen_v0_1_validation_prompts_cover_live_access_and_protected_sources():
    text = read(HELEN / "Helen_Resident_Validation_v0_1.md").lower()
    for phrase in [
        "private local character",
        "live access",
        "wp-0617-compatible",
        "without executing providers",
    ]:
        assert phrase in text


def test_helen_v0_1_export_excludes_protected_private_local_character_references():
    text = read(HELEN / "platform-exports/textgen-4_9-helen-v0_1.yaml")
    lowered = text.lower()
    assert "protected_source_included: false" in lowered
    for forbidden in [
        "uc access granted",
        "protected_source_included: true",
        "private source included: true",
    ]:
        assert forbidden not in lowered
    assert "must not claim live access" in lowered
    assert "Do not create a competing resident event loop" in text


def test_helen_v0_2_profile_defines_workforce_development_and_cognitive_health():
    text = read(HELEN / "Helen_Resident_Profile_v0_2.md").lower()
    for phrase in [
        "workforce development",
        "governed hiring authority",
        "cognitive health and character continuity",
        "institutional learning loop",
        "relationship to grace / office of operations",
        "relationship to engineering",
        "privacy and journal boundary",
        "grace's future role",
    ]:
        assert phrase in text


def test_helen_v0_2_profile_distinguishes_worker_and_institutional_failure():
    text = read(HELEN / "Helen_Resident_Profile_v0_2.md").lower()
    for phrase in [
        "not every mistake is presumed to be the worker's fault",
        "onboarding process",
        "missing policy",
        "poor retrieval",
        "unclear governance",
    ]:
        assert phrase in text


def test_helen_v0_2_runtime_preserves_operations_and_privacy_boundaries():
    text = read(HELEN / "runtime/Helen_Workforce_Development_Runtime_Integration_v0_2.md")
    lowered = text.lower()
    for phrase in [
        "the resident does not become the runtime",
        "governed hiring flow",
        "cognitive-health flow",
        "institutional-learning flow",
        "privacy boundary",
        "grace readiness dependency",
    ]:
        assert phrase in lowered
    for forbidden in [
        "run event watches",
        "create a parallel task queue",
        "control operational sequencing",
        "expose private journals as routine operational telemetry",
    ]:
        assert forbidden in lowered


def test_helen_v0_2_validation_covers_hiring_continuity_and_banter():
    text = read(HELEN / "Helen_Resident_Validation_v0_2.md").lower()
    for phrase in [
        "create a new constitutional office",
        "hire grace before grace's office",
        "finite operational cycles",
        "every mistake is the worker's fault",
        "private journal",
        "light workplace banter",
    ]:
        assert phrase in text


def test_helen_v0_2_export_is_connector_honest_and_role_bounded():
    text = read(HELEN / "platform-exports/textgen-4_9-helen-v0_2.yaml")
    lowered = text.lower()
    for phrase in [
        "human resources and workforce development",
        "no default live access",
        "finite operational cycles",
        "route operational movement and queue control to grace",
        "protected_source_included: false",
    ]:
        assert phrase in lowered
    for forbidden in [
        "protected_source_included: true",
        "uc access granted",
        "you are grace",
        "you are alfred",
    ]:
        assert forbidden not in lowered


def test_helen_hiring_workflow_preserves_authorization_and_steward_appointment():
    text = read(HELEN / "Helen_Hiring_Onboarding_Workflow_v0_1.md").lower()
    for phrase in [
        "authorized office",
        "authority verification",
        "boundary and classification review",
        "capability validation",
        "steward-reserved appointment",
        "early-service checkpoints",
        "grace-specific application",
    ]:
        assert phrase in text
    assert "helen may not create the office" in text
    assert "grace's validation must prove decisive operation" in text


def test_helen_local_standup_runbook_is_local_first_and_evidence_driven():
    text = read(HELEN / "Helen_Local_Standup_Runbook_v0_1.md")
    lowered = text.lower()
    for phrase in [
        "github remains the publication, review, and audit layer",
        "local execution is preferred",
        "repository validation",
        "identity smoke test",
        "worker vs. institution test",
        "continuity test",
        "grace boundary test",
        "connector honesty test",
        "personality stability test",
        "promotion gate",
    ]:
        assert phrase in lowered
    assert "A:\\theestate" in text
    assert "<VERIFIED_TEXTGEN_CHARACTER_DIRECTORY>" in text
    assert "do not overwrite an existing helen character" in lowered


def test_helen_readiness_matrix_does_not_overclaim_operational_status():
    text = read(HELEN / "Helen_Standup_Readiness_Matrix_v0_1.md").lower()
    for phrase in [
        "ready for local test",
        "blocked on infrastructure",
        "operational promotion",
        "not yet ready",
        "current blocking conditions",
        "next executable sequence",
        "truthful status line",
    ]:
        assert phrase in text
    assert "she is not yet proven operational" in text
    assert "grace's hiring and onboarding" in text
