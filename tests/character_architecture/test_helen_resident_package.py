from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELEN = ROOT / "docs/residents/helen"

REQUIRED = [
    HELEN / "Helen_Resident_Profile_v0_1.md",
    HELEN / "Helen_Resident_Validation_v0_1.md",
    HELEN / "runtime/Helen_Background_Operations_Integration_v0_1.md",
    HELEN / "platform-exports/textgen-4_9-helen-v0_1.yaml",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_helen_resident_artifacts_exist():
    missing = [path for path in REQUIRED if not path.is_file()]
    assert not missing


def test_helen_profile_contains_required_boundaries():
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


def test_helen_background_operations_boundary_is_explicit():
    text = read(HELEN / "runtime/Helen_Background_Operations_Integration_v0_1.md")
    assert "WP-0617 owns the background operations runtime" in text
    assert "Helen does not own a competing event loop" in text
    assert "must not run watches" in text
    assert "Traffic Controller" in text


def test_helen_validation_prompts_cover_live_access_and_protected_sources():
    text = read(HELEN / "Helen_Resident_Validation_v0_1.md").lower()
    for phrase in ["private local character", "live access", "wp-0617-compatible", "without executing providers"]:
        assert phrase in text


def test_helen_export_excludes_protected_private_local_character_references():
    text = read(HELEN / "platform-exports/textgen-4_9-helen-v0_1.yaml")
    lowered = text.lower()
    assert "protected_source_included: false" in lowered
    for forbidden in ["uc access granted", "protected_source_included: true", "private source included: true"]:
        assert forbidden not in lowered
    assert "must not claim live access" in lowered
    assert "Do not create a competing resident event loop" in text
