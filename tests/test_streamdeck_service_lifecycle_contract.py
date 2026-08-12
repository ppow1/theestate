from pathlib import Path


MVP_ROOT = Path(r"A:\AI\Tools\EstateStreamDeckMVP")
CORE = MVP_ROOT / "Core"
PLUGIN = Path(r"A:\AI\Tools\EstateStreamDeckPlugin") / "src"
CANONICAL_PLUGIN = Path("tools/streamdeck/estate-status-bridge")
CANONICAL_RUNTIME = Path("tools/streamdeck/estate-service-runtime")


def test_streamdeck_launcher_is_transient_and_not_cmd_k_start():
    source = (PLUGIN / "plugin.js").read_text(encoding="utf-8")
    assert 'command: "cmd.exe"' in source
    assert 'args: ["/d", "/s", "/c", commandPath]' in source
    assert '"start", "", commandPath' not in source


def test_service_runtime_has_identity_and_serialized_start_contract():
    source = (CORE / "Estate-Service-Lib.ps1").read_text(encoding="utf-8")
    assert "Estate.Service.Start.$($Service.Id)" in source
    assert "identityHealthy" in source
    assert '"DUPLICATE"' in source
    assert "already_running" in source


def test_open_webui_canonical_runtime_contract_is_preserved():
    config = (CORE / "Estate-Service-Config.ps1").read_text(encoding="utf-8")
    assert 'WorkingDirectory = "A:\\AI\\OpenWebUI"' in config
    assert 'DATA_DIR = "A:\\AI\\OpenWebUI\\EstateCanonicalData"' in config
    assert '"Start-OpenWebUI.cmd"' in config


def test_governed_status_probe_exists_and_wrappers_are_exactly_named():
    assert (CORE / "Get-EstateServiceStatus.ps1").is_file()
    config = (CORE / "Estate-Service-Config.ps1").read_text(encoding="utf-8")
    for wrapper in (
        "Start-Ollama.cmd",
        "Start-ResidentGateway.cmd",
        "Start-OpenWebUI.cmd",
        "Start-TextGen.cmd",
        "Start-ComfyUI.cmd",
    ):
        assert wrapper in config


def test_all_mvp_start_wrappers_do_not_request_persistent_cmd_shells():
    for path in CORE.glob("Start-*.cmd"):
        text = path.read_text(encoding="utf-8").lower()
        assert "/k" not in text


def test_streamdeck_runtime_is_reproducible_from_repository_sources():
    assert (CANONICAL_PLUGIN / "src" / "status.js").is_file()
    assert (CANONICAL_PLUGIN / "src" / "plugin.js").is_file()
    assert (CANONICAL_PLUGIN / "scripts" / "build.ps1").is_file()
    assert (CANONICAL_RUNTIME / "Core" / "Estate-Service-Lib.ps1").is_file()
    assert (CANONICAL_RUNTIME / "Core" / "Get-EstateServiceStatus.ps1").is_file()
    source = (CANONICAL_PLUGIN / "src" / "status.js").read_text(encoding="utf-8")
    assert "DIAGNOSTIC_MAX_BYTES" in source
    assert "resources.find((resource) => resource.resource_id === action.resourceId)" in source
