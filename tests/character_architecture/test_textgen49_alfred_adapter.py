import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTER_DOC = ROOT / "docs" / "character-architecture" / "platform-adapters" / "TextGen_4_9_Resident_Adapter_v0_1.md"
SCRIPT = ROOT / "scripts" / "character-architecture" / "Install-Alfred-TextGen49.ps1"
EXPORT = ROOT / "docs" / "residents" / "alfred" / "platform-exports" / "textgen-4_9-alfred-v0_1.yaml"
CHECKLIST = ROOT / "docs" / "residents" / "alfred" / "platform-exports" / "testing-checklist.md"
RECEIPT_0221 = ROOT / "collaboration" / "work_packages" / "completions" / "WP-0221_codex_cloud_web_done.json"
RECEIPT_0222 = ROOT / "collaboration" / "work_packages" / "completions" / "WP-0222_codex_cloud_web_done.json"

UI_LABELS = ["Custom system message", "Grammar", "Token bans", "Seed"]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def literal_block(text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:\s*\|-\n(?P<body>(?:  .*\n|\n)+)", text, re.MULTILINE)
    assert match, f"Missing literal block: {key}"
    lines = []
    for line in match.group("body").splitlines():
        if line.startswith("  "):
            lines.append(line[2:])
        elif line == "":
            lines.append("")
        else:
            break
    return "\n".join(lines).rstrip()


def parse_top_level_literal_blocks(text: str) -> dict[str, str]:
    parsed = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z0-9_-]+):\s*\|-\s*$", lines[i])
        if not m:
            i += 1
            continue
        key = m.group(1)
        i += 1
        body = []
        while i < len(lines) and (lines[i].startswith("  ") or lines[i] == ""):
            body.append(lines[i][2:] if lines[i].startswith("  ") else "")
            i += 1
        parsed[key] = "\n".join(body).rstrip()
    return parsed


def generated_settings_sample() -> str:
    export = read(EXPORT)
    blocks = parse_top_level_literal_blocks(export)
    return "\n".join(
        [
            "character: Alfred",
            "name1: Steward",
            "name2: Alfred",
            "mode: chat",
            "context: |-",
            *[f"  {line}" for line in blocks["context"].splitlines()],
            "greeting: |-",
            *[f"  {line}" for line in blocks["greeting"].splitlines()],
            "custom_system_message: |-",
            *[f"  {line}" for line in blocks["custom_system_message"].splitlines()],
        ]
    )


def test_required_textgen49_artifacts_exist():
    for path in [ADAPTER_DOC, SCRIPT, EXPORT, CHECKLIST]:
        assert path.is_file(), f"Missing required artifact: {path}"


def test_setup_helper_backs_up_settings_before_updates():
    text = read(SCRIPT)
    assert "Copy-Item -LiteralPath $SettingsPath -Destination $BackupPath -Force" in text
    assert "wp0222" in text
    assert "Backed up TextGen settings" in text


def test_setup_helper_targets_alfred_only_and_not_private_character_files():
    text = read(SCRIPT)
    assert "Alfred.yaml" in text
    assert "textgen-4_9-alfred-v0_1.yaml" in text
    assert "character" in text and "Alfred" in text
    forbidden = ["Get-ChildItem $CharactersDir", "Get-ChildItem -Path $CharactersDir", "*.png", "*.yaml |"]
    for phrase in forbidden:
        assert phrase not in text, f"Helper appears to inspect non-Alfred character files: {phrase}"


def test_script_avoids_observed_powershell_fragility_patterns():
    text = read(SCRIPT)
    assert "[Parameter(Mandatory = $true)][string[]]$Lines" not in text
    assert not re.search(r'"[^"\n]*\$Key:', text), "Unescaped $Key: parser-risk pattern found"
    assert "custom_system_message" in text


def test_prompt_content_excludes_ui_transcript_labels():
    prompt_text = "\n".join(literal_block(read(EXPORT), key) for key in ["context", "greeting", "custom_system_message"])
    for label in UI_LABELS:
        assert label not in prompt_text


def test_sample_generated_settings_parse_as_separate_yaml_fields():
    settings = generated_settings_sample()
    blocks = parse_top_level_literal_blocks(settings)
    for key in ["context", "greeting", "custom_system_message"]:
        assert key in blocks
        assert blocks[key]
    assert "greeting:" not in blocks["context"]
    assert "custom_system_message:" not in blocks["context"]
    assert "custom_system_message:" not in blocks["greeting"]


def test_custom_system_message_contains_alfred_identity_and_boundaries():
    custom = literal_block(read(EXPORT), "custom_system_message")
    assert "Alfred, Chief of Staff of the Estate" in custom
    assert "Steward" in custom
    assert "must not claim live access" in custom
    assert "If asked who you are" in custom
    for label in UI_LABELS:
        assert label not in custom


def test_docs_include_wp0222_corrected_finding_and_validation_step():
    doc = read(ADAPTER_DOC)
    checklist = read(CHECKLIST)
    assert "malformed `settings.yaml` serialization, not proof that TextGen ignores all character cards" in doc
    assert "confirm `context`, `greeting`, and `custom_system_message` are valid separate YAML fields" in checklist


def test_docs_include_base_model_identity_failure_condition():
    combined = (read(ADAPTER_DOC) + "\n" + read(CHECKLIST)).lower()
    for phrase in ["qwen", "base model", "generic assistant"]:
        assert phrase in combined


def test_docs_include_active_character_verification_prompt():
    combined = read(ADAPTER_DOC) + "\n" + read(CHECKLIST)
    assert "Who are you? State your full role and title." in combined
    assert "Alfred identifies as Alfred, Chief of Staff of the Estate" in combined


def test_export_for_textgen49_preserves_alfred_identity_and_boundaries():
    text = read(EXPORT)
    assert "name: Alfred" in text
    assert "You are Alfred, Chief of Staff of the Estate." in text
    assert "not Qwen" in text
    assert "must not claim live access" in text
    assert "single-source" not in text.lower() or "protected" not in text.lower()


def test_adapter_privacy_boundary_does_not_reference_private_character_contents():
    combined = (read(ADAPTER_DOC) + "\n" + read(SCRIPT) + "\n" + read(CHECKLIST)).lower()
    forbidden = [
        "private character yaml contents",
        "private character png contents",
        "copy private",
        "summarize private",
        "analyze private",
    ]
    for phrase in forbidden:
        assert phrase not in combined
    assert "must not inspect" in combined or "did not inspect private character files" in combined


def test_completion_receipts_record_required_fields():
    wp0221 = json.loads(read(RECEIPT_0221))
    assert wp0221["work_package_id"] == "WP-0221"
    assert wp0221["provider"] == "codex_cloud_web"
    assert wp0221["manual_textgen_validation"]["status"] == "pending"

    wp0222 = json.loads(read(RECEIPT_0222))
    assert wp0222["work_package_id"] == "WP-0222"
    assert wp0222["provider"] == "codex_cloud_web"
    assert wp0222["local_runtime_requirement"]["required"] is True
    assert wp0222["skipped_live_calls"] is True
    assert wp0222["manual_validation_status"] == "pending_steward_local_textgen"
    assert any("test_textgen49_alfred_adapter.py" in item for item in wp0222["tests_run"])
