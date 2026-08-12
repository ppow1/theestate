from pathlib import Path


CANONICAL_SCRIPT = Path("tools/start_openwebui_canonical.ps1")
MVP_ROOT = Path(r"A:\AI\Tools\EstateStreamDeckMVP\Core")


def test_canonical_launcher_contract_is_explicit_and_fail_closed():
    source = CANONICAL_SCRIPT.read_text(encoding="utf-8")

    assert "param([switch]$ValidateOnly)" in source
    assert "$dataRoot = 'A:\\AI\\OpenWebUI\\EstateCanonicalData'" in source
    assert "GetFullPath($dataRoot) -ne 'A:\\AI\\OpenWebUI\\EstateCanonicalData'" in source
    assert "Test-Path -LiteralPath $dataRoot -PathType Container" in source
    assert "Test-Path -LiteralPath $databasePath -PathType Leaf" in source
    assert "[System.IO.File]::Open($databasePath" in source
    assert "$env:DATA_DIR = $dataRoot" in source
    assert "WorkingDirectory $appRoot" in source

    assert "A:\\AI\\OpenWebUI\\data" not in source
    assert "A:\\AI\\OpenWebUI\\webui.db" not in source


def test_governed_mvp_config_supplies_canonical_data_dir():
    config = MVP_ROOT / "Estate-Service-Config.ps1"
    if not config.exists():
        return
    source = config.read_text(encoding="utf-8")
    open_webui = source[source.index("open_webui = @{") :]
    assert 'WorkingDirectory = "A:\\AI\\OpenWebUI"' in open_webui
    assert 'DATA_DIR = "A:\\AI\\OpenWebUI\\EstateCanonicalData"' in open_webui


def test_governed_wrappers_run_repository_preflight():
    for name in ("Start-EstateCore.ps1", "Start-OpenWebUI.ps1"):
        wrapper = MVP_ROOT / name
        if not wrapper.exists():
            continue
        source = wrapper.read_text(encoding="utf-8")
        assert "A:\\theestate\\tools\\start_openwebui_canonical.ps1" in source
        assert "-ValidateOnly" in source


def test_existing_service_library_retains_idempotent_and_foreign_port_gates():
    library = MVP_ROOT / "Estate-Service-Lib.ps1"
    if not library.exists():
        return
    source = library.read_text(encoding="utf-8")
    assert "if ($initialStatus.healthy)" in source
    assert "foreignPortProcesses" in source
    assert "Cannot start $($Service.Name). An expected port is owned by a foreign process" in source
