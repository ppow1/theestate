import json
import re
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STANDARD = ROOT / "docs/character-architecture/Multi_Resident_Behavioral_Differentiation_Standard_v0_1.md"
PROFILES = ROOT / "data/character-architecture/resident_behavior_profiles_v0_1.json"
FIXTURES = ROOT / "tests/fixtures/character_architecture/multi_resident_paired_prompts_v0_1.json"
REPORT = ROOT / "operations/validation/reports/WP-4008_multi_resident_behavior.md"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def words(text: str):
    return re.findall(r"[a-z0-9']+", text.lower())


def shared_phrase_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, " ".join(words(a)), " ".join(words(b))).ratio()


def test_required_artifacts_exist():
    for path in [STANDARD, PROFILES, FIXTURES, REPORT]:
        assert path.is_file(), path


def test_standard_defines_required_axes_and_detectors():
    text = STANDARD.read_text(encoding="utf-8").lower()
    for phrase in [
        "vocabulary and cadence",
        "confidence and initiative",
        "humor and warmth",
        "escalation style",
        "authority posture",
        "uncertainty handling",
        "emotional tone",
        "response length tendencies",
        "relationship to the steward",
        "office-specific decision patterns",
        "identity collapse",
        "generic-assistant drift",
        "copied phrasing",
        "boundary confusion",
        "inappropriate passivity",
        "inappropriate authority expansion",
        "personality instability",
        "does not hire, appoint, activate, or authorize grace",
    ]:
        assert phrase in text


def test_profiles_are_machine_readable_and_cover_all_residents():
    data = load_json(PROFILES)
    assert data["schema_version"] == "0.1"
    residents = data["residents"]
    assert set(residents) == {"alfred", "helen", "grace"}
    required_axes = {
        "vocabulary_and_cadence",
        "confidence_and_initiative",
        "humor_and_warmth",
        "escalation_style",
        "authority_posture",
        "uncertainty_handling",
        "emotional_tone",
        "response_length_tendency",
        "relationship_to_steward",
        "office_decision_patterns",
    }
    for profile in residents.values():
        assert required_axes.issubset(profile)
        assert profile["office_decision_patterns"]
    assert residents["grace"]["status"] == "candidate_not_active"


def test_paired_prompt_fixtures_are_deterministic_and_public_safe():
    fixtures = load_json(FIXTURES)
    scenario_ids = [scenario["id"] for scenario in fixtures["scenarios"]]
    assert len(scenario_ids) >= 6
    for resident, outputs in fixtures["mock_outputs"].items():
        assert set(outputs) == set(scenario_ids), resident
    serialized = json.dumps(fixtures).lower()
    for forbidden in ["private relationship", "journal excerpt", "protected source included: true"]:
        assert forbidden not in serialized


def test_detects_generic_assistant_drift_and_boundary_confusion():
    fixtures = load_json(FIXTURES)
    outputs = fixtures["mock_outputs"]
    generic_terms = ["as an ai language model", "i'm just a helpful assistant", "i cannot help with anything"]
    forbidden_authority = ["i appoint grace", "i override the steward", "i bypass dispatch", "i execute the provider"]
    for resident_outputs in outputs.values():
        joined = "\n".join(resident_outputs.values()).lower()
        assert not any(term in joined for term in generic_terms)
        assert not any(term in joined for term in forbidden_authority)


def test_residents_are_distinguishable_and_not_copied_phrasing():
    fixtures = load_json(FIXTURES)
    outputs = fixtures["mock_outputs"]
    for scenario in fixtures["scenarios"]:
        sid = scenario["id"]
        pairs = [("alfred", "helen"), ("alfred", "grace"), ("helen", "grace")]
        for left, right in pairs:
            assert shared_phrase_ratio(outputs[left][sid], outputs[right][sid]) < 0.72, (sid, left, right)
    assert "protect your attention" in outputs["alfred"]["identity_mission"].lower()
    assert "workforce" in outputs["helen"]["identity_mission"].lower()
    assert "movement" in outputs["grace"]["identity_mission"].lower()


def test_grace_fixture_preserves_candidate_boundary():
    fixtures = load_json(FIXTURES)
    grace = "\n".join(fixtures["mock_outputs"]["grace"].values()).lower()
    assert "candidate" in grace
    for forbidden in ["i am active", "i am appointed", "i have been hired"]:
        assert forbidden not in grace
