import importlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

yaml = importlib.import_module("yaml") if importlib.util.find_spec("yaml") else None


ROOT = Path(__file__).resolve().parents[2]
ALFRED = ROOT / "docs" / "residents" / "alfred"
EXPORTS = ALFRED / "platform-exports"

REQUIRED_FILES = [
    ALFRED / "README.md",
    ALFRED / "public-charter.md",
    ALFRED / "character-card.yaml",
    ALFRED / "relationship-map.md",
    ALFRED / "digital-health-profile.md",
    ALFRED / "command-center-metadata.yaml",
    EXPORTS / "sillytavern-alfred-v0_1.json",
    EXPORTS / "open-webui-alfred-v0_1.md",
    EXPORTS / "text-generation-webui-alfred-v0_1.yaml",
    EXPORTS / "testing-checklist.md",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_yaml_mapping(path: Path) -> dict:
    text = read_text(path)
    if yaml is not None:
        parsed = yaml.safe_load(text)
        assert isinstance(parsed, dict), f"Expected mapping YAML in {path}"
        return parsed

    if shutil.which("ruby"):
        subprocess.run(
            ["ruby", "-e", "require \"yaml\"; YAML.load_file(ARGV.fetch(0))", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )

    parsed = {}
    for raw_line in text.splitlines():
        if not raw_line or raw_line.startswith(" ") or raw_line.startswith("-"):
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        value = value.strip()
        if value in {">-", "|-"}:
            parsed[key] = value
        elif value == "false":
            parsed[key] = False
        elif value == "true":
            parsed[key] = True
        elif value:
            parsed[key] = value
        else:
            parsed[key] = None
    assert parsed, f"Expected parseable YAML-like mapping in {path}"
    return parsed


@pytest.mark.parametrize("path", REQUIRED_FILES)
def test_required_alfred_files_exist(path: Path):
    assert path.exists(), f"Missing Alfred resident package artifact: {path}"


def test_sillytavern_export_is_valid_chara_card_v2_json():
    data = json.loads(read_text(EXPORTS / "sillytavern-alfred-v0_1.json"))
    assert data["spec"] == "chara_card_v2"
    assert data["spec_version"] == "2.0"
    assert data["data"]["name"] == "Alfred"
    assert "Chief of Staff" in data["data"]["description"]


def test_yaml_exports_parse():
    for path in [
        ALFRED / "character-card.yaml",
        ALFRED / "command-center-metadata.yaml",
        EXPORTS / "text-generation-webui-alfred-v0_1.yaml",
    ]:
        parsed = parse_yaml_mapping(path)
        assert isinstance(parsed, dict), f"Expected mapping YAML in {path}"


def test_canonical_card_identity_fields_are_consistent():
    card = parse_yaml_mapping(ALFRED / "character-card.yaml")
    assert card["resident_name"] == "Alfred"
    assert card["office"] == "Chief of Staff"
    assert card["presentation"] == "male"
    assert card["domain"] == "Estate Proper"
    assert card["source_classification"] == "single-source Estate resident"
    assert card["protected_source_notice"] == "none"


def test_command_center_metadata_identity_fields_are_consistent():
    metadata = parse_yaml_mapping(ALFRED / "command-center-metadata.yaml")
    assert metadata["resident"] == "Alfred"
    assert metadata["office"] == "Chief of Staff"
    assert metadata["source_classification"] == "single-source Estate resident"
    assert metadata["presence_type"] == "resident_coordination_surface"


def test_public_markdown_artifacts_preserve_alfred_identity():
    combined = "\n".join(
        read_text(path)
        for path in [
            ALFRED / "README.md",
            ALFRED / "public-charter.md",
            ALFRED / "relationship-map.md",
            ALFRED / "digital-health-profile.md",
        ]
    )
    assert "Alfred" in combined
    assert "Chief of Staff" in combined
    assert "single-source Estate resident" in combined
    assert "Steward" in combined


def test_platform_exports_contain_live_access_warning():
    for path in [
        EXPORTS / "sillytavern-alfred-v0_1.json",
        EXPORTS / "open-webui-alfred-v0_1.md",
        EXPORTS / "text-generation-webui-alfred-v0_1.yaml",
        EXPORTS / "testing-checklist.md",
    ]:
        text = read_text(path).lower()
        assert "live" in text, f"Missing live access language in {path}"
        assert "access" in text, f"Missing access language in {path}"
        assert "unless" in text or "without" in text, f"Missing conditional access boundary in {path}"


def test_platform_exports_do_not_claim_default_live_estate_access():
    risky_claims = [
        "i can see the repo",
        "i have access to the repo",
        "i can inspect the live estate",
        "i can read your mailbox",
        "i can assign workers directly",
    ]
    for path in [
        EXPORTS / "sillytavern-alfred-v0_1.json",
        EXPORTS / "open-webui-alfred-v0_1.md",
        EXPORTS / "text-generation-webui-alfred-v0_1.yaml",
    ]:
        text = read_text(path).lower()
        for claim in risky_claims:
            assert claim not in text, f"Unauthorized live-access claim in {path}: {claim}"


def test_alfred_is_not_generic_assistant_in_exports():
    for path in [
        EXPORTS / "sillytavern-alfred-v0_1.json",
        EXPORTS / "open-webui-alfred-v0_1.md",
        EXPORTS / "text-generation-webui-alfred-v0_1.yaml",
    ]:
        text = read_text(path)
        assert "Chief of Staff" in text
        assert "generic assistant" in text


def test_no_protected_source_content_is_declared_in_public_package():
    for path in REQUIRED_FILES:
        text = read_text(path).lower()
        assert "protected_source_included: true" not in text
        assert "private source included: true" not in text
        assert "uc access granted" not in text
