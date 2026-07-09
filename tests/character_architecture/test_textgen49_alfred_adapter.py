import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ADAPTER_DOC = ROOT / "docs" / "character-architecture" / "platform-adapters" / "TextGen_4_9_Resident_Adapter_v0_1.md"
SCRIPT = ROOT / "scripts" / "character-architecture" / "Install-Alfred-TextGen49.ps1"
EXPORT = ROOT / "docs" / "residents" / "alfred" / "platform-exports" / "textgen-4_9-alfred-v0_1.yaml"
CHECKLIST = ROOT / "docs" / "residents" / "alfred" / "platform-exports" / "testing-checklist.md"
RECEIPT = ROOT / "collaboration" / "work_packages" / "completions" / "WP-0221_codex_cloud_web_done.json"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_required_textgen49_artifacts_exist():
    for path in [ADAPTER_DOC, SCRIPT, EXPORT, CHECKLIST]:
        assert path.is_file(), f"Missing required artifact: {path}"


def test_setup_helper_backs_up_settings_before_updates():
    text = read(SCRIPT)
    assert "Copy-Item -LiteralPath $SettingsPath -Destination $BackupPath -Force" in text
    assert "wp0221" in text
    assert "Backed up TextGen settings" in text


def test_setup_helper_targets_alfred_only_and_not_private_character_files():
    text = read(SCRIPT)
    assert "Alfred.yaml" in text
    assert "textgen-4_9-alfred-v0_1.yaml" in text
    assert "character" in text and "Alfred" in text
    forbidden = ["Get-ChildItem $CharactersDir", "Get-ChildItem -Path $CharactersDir", "*.png", "*.yaml |"]
    for phrase in forbidden:
        assert phrase not in text, f"Helper appears to inspect non-Alfred character files: {phrase}"


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


def test_completion_receipt_records_required_wp0221_fields():
    data = json.loads(read(RECEIPT))
    assert data["work_package_id"] == "WP-0221"
    assert data["provider"] == "codex_cloud_web"
    assert data["local_runtime_requirement"]["required"] is True
    assert data["skipped_live_calls"] is True
    assert data["manual_textgen_validation"]["status"] == "pending"
    assert any("test_textgen49_alfred_adapter.py" in item for item in data["tests_run"])
