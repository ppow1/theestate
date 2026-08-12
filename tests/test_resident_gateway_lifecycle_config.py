from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "tools/streamdeck/estate-service-runtime/Core/Estate-Service-Config.ps1"
LIB = ROOT / "tools/streamdeck/estate-service-runtime/Core/Estate-Service-Lib.ps1"
START = ROOT / "tools/streamdeck/estate-service-runtime/Core/Start-ResidentGateway.ps1"


def test_global_paths_remain_unchanged_and_gateway_has_narrow_override():
    text = CONFIG.read_text(encoding="utf-8")
    assert 'EstateRoot = "A:\\theestate"' in text
    assert 'PythonPath = "A:\\theestate\\src"' in text
    assert '$residentGatewayRuntimeRoot = "A:\\EstateRuntime\\host\\estate-main\\current"' in text
    assert '$residentGatewayPythonPath = "A:\\EstateRuntime\\host\\estate-main\\current\\src"' in text
    assert 'WorkingDirectory = $residentGatewayRuntimeRoot' in text
    assert 'PYTHONPATH = $residentGatewayPythonPath' in text


def test_other_services_continue_using_shared_paths():
    text = CONFIG.read_text(encoding="utf-8")
    assert text.count('WorkingDirectory = "A:\\theestate"') >= 1
    assert text.count('PYTHONPATH = "A:\\theestate\\src"') >= 1


def test_gateway_fails_closed_on_missing_runtime_paths():
    text = LIB.read_text(encoding="utf-8")
    assert 'RequiredPaths' in text
    assert 'Required runtime path not found' in text
    for required in ("src", "src\\estate", "src\\estate\\cli\\main.py", "src\\estate\\core\\resident_gateway.py"):
        assert required in CONFIG.read_text(encoding="utf-8")


def test_existing_governed_identity_and_port_contract_remain_present():
    config = CONFIG.read_text(encoding="utf-8")
    lib = LIB.read_text(encoding="utf-8")
    assert 'Ports = @(11435)' in config
    assert 'resident-gateway' in config
    assert 'Start-ResidentGateway.cmd' in config
    assert 'foreignPortProcesses' in lib
    assert 'already_running' in lib
    assert 'Start-Process' in lib
    assert '/k' not in (config + lib + START.read_text(encoding="utf-8")).lower()
