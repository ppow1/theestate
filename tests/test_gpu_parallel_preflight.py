import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "gpu-parallel-preflight.ps1"
P100 = "GPU-6785b322-899d-8eec-e817-31d83279a414"
RTX = "GPU-46f3fd00-5454-4536-4196-5d8b727e14f2"


def _smi(p100_free=12000, rtx_free=16000, p100_util=0, rtx_util=0, p100_power=34, rtx_power=35, p100_name="Tesla P100-PCIE-16GB", rtx_name="NVIDIA GeForce RTX 4090", p100_pci="00000000:04:00.0", rtx_pci="00000000:07:00.0", p100_uuid=P100, rtx_uuid=RTX, p100_driver="TCC", rtx_driver="WDDM"):
    return "\n".join(
        [
            f"{rtx_uuid},{rtx_name},{rtx_pci},{24564-rtx_free},{rtx_free},24564,{rtx_util},42,{rtx_power},{rtx_driver}",
            f"{p100_uuid},{p100_name},{p100_pci},{16384-p100_free},{p100_free},16384,{p100_util},42,{p100_power},{p100_driver}",
        ]
    )


def _pnp(p100_status="OK", rtx_status="OK"):
    return [
        {"FriendlyName": "NVIDIA GeForce RTX 4090", "Status": rtx_status, "InstanceId": "PCI\\VEN_10DE&DEV_2684\\RTX", "ConfigManagerErrorCode": 0, "Present": True},
        {"FriendlyName": "Tesla P100-PCIE-16GB", "Status": p100_status, "InstanceId": "PCI\\VEN_10DE&DEV_15F8\\P100", "ConfigManagerErrorCode": 0, "Present": True},
    ]


def _run(tmp_path, smi=None, apps="", pnp=None, processes=None, ports=None):
    pnp_path = tmp_path / "pnp.json"
    process_path = tmp_path / "processes.json"
    port_path = tmp_path / "ports.json"
    pnp_path.write_text(json.dumps(_pnp() if pnp is None else pnp), encoding="utf-8")
    process_path.write_text(json.dumps([] if processes is None else processes), encoding="utf-8")
    port_path.write_text(json.dumps([] if ports is None else ports), encoding="utf-8")
    command = [
        "pwsh",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SCRIPT),
        "-Json",
        "-NvidiaSmiOutput",
        smi or _smi(),
        "-ComputeAppsOutput",
        apps,
        "-PnpOutput",
        str(pnp_path),
        "-ProcessFixture",
        str(process_path),
        "-PortFixture",
        str(port_path),
        "-RepoRoot",
        str(ROOT),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    payload = json.loads(result.stdout)
    return result.returncode, payload


def test_healthy_idle_fixture_passes(tmp_path):
    code, result = _run(tmp_path)
    assert code == 0
    assert result["status"] == "PASS"
    assert all(item["ready"] for item in result["resources"])


def test_capacity_floor_blocks_each_gpu(tmp_path):
    code, result = _run(tmp_path, smi=_smi(rtx_free=8191))
    assert code == 2, result
    assert result["status"] == "PRECHECK_BLOCKED"
    code, result = _run(tmp_path, smi=_smi(p100_free=4095))
    assert code == 2, result
    assert result["status"] == "PRECHECK_BLOCKED"


def test_missing_and_wrong_uuid_are_health_failures(tmp_path):
    missing = _smi().splitlines()[0]
    assert _run(tmp_path, smi=missing)[1]["status"] == "GPU_HEALTH_FAILURE"
    assert _run(tmp_path, smi=_smi(rtx_uuid="GPU-wrong"))[1]["status"] == "GPU_HEALTH_FAILURE"


def test_stable_uuid_with_pci_reenumeration_passes_with_topology_warning(tmp_path):
    code, result = _run(tmp_path, smi=_smi(rtx_pci="00000000:06:00.0", p100_pci="00000000:09:00.0"))
    assert code == 0
    assert result["status"] == "PASS"
    assert result["policy"]["canonical_identity"] == "host_id + NVIDIA UUID"
    for resource in result["resources"]:
        assert resource["ready"] is True
        assert resource["pci_topology_changed"] is True
        assert resource["pci_bus"] != resource["prior_observed_pci_bus"]
        assert "stable UUID" in resource["warnings"][0]
    assert len(result["warnings"]) == 2


def test_pnp_and_malformed_output_fail_safely(tmp_path):
    code, result = _run(tmp_path, pnp=_pnp(p100_status="Error"))
    assert code == 3
    assert result["status"] == "GPU_HEALTH_FAILURE"
    code, result = _run(tmp_path, smi="not,csv")
    assert code == 4
    assert result["status"] == "PREFLIGHT_TOOL_ERROR"


def test_pnp_optional_problem_fields_absent_are_null_and_healthy(tmp_path):
    pnp = _pnp()
    for device in pnp:
        del device["ConfigManagerErrorCode"]
    code, result = _run(tmp_path, pnp=pnp)
    assert code == 0
    assert result["status"] == "PASS"
    for resource in result["resources"]:
        assert resource["pnp_status"] == "OK"
        assert resource["pnp_instance_id"].startswith("PCI\\")
        assert resource["pnp_problem_code"] is None
        assert resource["pnp_config_manager_error_code"] is None


def test_pnp_realistic_name_and_identity_variants_match(tmp_path):
    pnp = _pnp()
    pnp[1] = {"FriendlyName": "NVIDIA Tesla P100-PCIE-16GB", "Status": "OK", "InstanceId": "PCI\\VEN_10DE&DEV_15F8\\P100", "ConfigManagerErrorCode": None}
    code, result = _run(tmp_path, pnp=pnp)
    assert code == 0
    p100 = next(item for item in result["resources"] if item["gpu_uuid"] == P100)
    assert p100["pnp_status"] == "OK"
    assert p100["pnp_friendly_name"] == "NVIDIA Tesla P100-PCIE-16GB"

    pnp[1] = {"Name": "Display adapter - NVIDIA Tesla P100", "Status": "OK", "PNPDeviceID": "PCI\\VEN_10DE&DEV_15F8\\P100", "ConfigManagerErrorCode": 0}
    code, result = _run(tmp_path, pnp=pnp)
    assert code == 0
    p100 = next(item for item in result["resources"] if item["gpu_uuid"] == P100)
    assert p100["pnp_name"] == "Display adapter - NVIDIA Tesla P100"
    assert p100["pnp_config_manager_error_code"] == 0


def test_pnp_phantom_missing_and_unrelated_devices_fail_closed(tmp_path):
    pnp = _pnp()
    pnp[1]["Present"] = False
    assert _run(tmp_path, pnp=pnp)[1]["status"] == "GPU_HEALTH_FAILURE"
    assert _run(tmp_path, pnp=_pnp()[:1])[1]["status"] == "GPU_HEALTH_FAILURE"
    unrelated = _pnp()[:1] + [{"FriendlyName": "NVIDIA GeForce RTX 4080", "Status": "OK", "InstanceId": "PCI\\VEN_10DE&DEV_2704\\OTHER"}]
    code, result = _run(tmp_path, pnp=unrelated)
    assert code == 3
    p100 = next(item for item in result["resources"] if item["gpu_uuid"] == P100)
    assert p100["pnp_status"] == "MISSING"


def test_pnp_explicit_problem_code_is_health_failure(tmp_path):
    pnp = _pnp()
    pnp[0]["ProblemCode"] = 43
    code, result = _run(tmp_path, pnp=pnp)
    assert code == 3
    assert result["status"] == "GPU_HEALTH_FAILURE"
    rtx = next(item for item in result["resources"] if item["gpu_uuid"] == RTX)
    assert rtx["pnp_problem_code"] == 43
    assert "explicit problem code" in rtx["reasons"][0]


def test_pnp_missing_required_identity_field_fails_closed(tmp_path):
    pnp = _pnp()
    del pnp[0]["InstanceId"]
    code, result = _run(tmp_path, pnp=pnp)
    assert code == 3
    assert result["status"] == "GPU_HEALTH_FAILURE"
    assert any("missing required" in reason for reason in result["reasons"])


def test_external_material_compute_blocks(tmp_path):
    apps = f"15868, C:\\ollama\\llama-server.exe, 8706, {P100}"
    code, result = _run(tmp_path, smi=_smi(p100_util=53, p100_power=98), apps=apps, processes=[{"pid": 15868, "name": "llama-server.exe", "executable_path": "C:\\ollama\\llama-server.exe", "command_line": "llama-server.exe", "parent_pid": 1}])
    assert code == 2
    assert result["status"] == "PRECHECK_BLOCKED"
    p100 = next(item for item in result["resources"] if item["gpu_uuid"] == P100)
    assert p100["material_external_load"] is True


def test_external_model_worker_blocks_even_when_current_load_is_low(tmp_path):
    apps = f"15868, C:\\ollama\\llama-server.exe, 8706, {P100}"
    code, result = _run(tmp_path, smi=_smi(p100_util=0, p100_power=34), apps=apps, processes=[{"pid": 15868, "name": "llama-server.exe", "executable_path": "C:\\ollama\\llama-server.exe", "command_line": "llama-server.exe", "parent_pid": 1}])
    assert code == 2
    assert result["status"] == "PRECHECK_BLOCKED"


def test_wddm_graphics_clients_with_low_load_are_non_conflicting(tmp_path):
    apps = "\n".join([
        f"77, C:\\Windows\\System32\\ShellHost.exe, [N/A], {RTX}",
        f"78, C:\\Browser\\browser.exe, [N/A], {RTX}",
    ])
    processes = [
        {"pid": 77, "name": "ShellHost.exe", "executable_path": "C:\\Windows\\System32\\ShellHost.exe", "command_line": "ShellHost.exe", "parent_pid": 1, "gpu_engine_types": ["3d", "copy"]},
        {"pid": 78, "name": "browser.exe", "executable_path": "C:\\Browser\\browser.exe", "command_line": "browser.exe --type=gpu-process", "parent_pid": 1, "gpu_engine_types": ["3d", "videodecode"]},
    ]
    code, result = _run(tmp_path, apps=apps, processes=processes)
    assert code == 0
    rtx = next(item for item in result["resources"] if item["gpu_uuid"] == RTX)
    assert rtx["unknown_compute_ownership"] is False
    assert {item["ownership"] for item in rtx["compute_processes"]} == {"NON_CONFLICTING_WDDM"}


def test_wddm_process_without_engine_context_blocks_conservatively(tmp_path):
    apps = f"79, unknown.exe, [N/A], {RTX}"
    processes = [{"pid": 79, "name": "unknown.exe", "executable_path": "C:\\Unknown\\unknown.exe", "command_line": "unknown.exe", "parent_pid": 1}]
    code, result = _run(tmp_path, apps=apps, processes=processes)
    assert code == 2, result
    rtx = next(item for item in result["resources"] if item["gpu_uuid"] == RTX)
    assert rtx["unknown_compute_ownership"] is True


def test_wddm_ui_context_still_blocks_when_aggregate_load_is_material(tmp_path):
    apps = f"80, ui.exe, [N/A], {RTX}"
    processes = [{"pid": 80, "name": "ui.exe", "executable_path": "C:\\UI\\ui.exe", "command_line": "ui.exe", "parent_pid": 1, "gpu_engine_types": ["3d"]}]
    code, result = _run(tmp_path, smi=_smi(rtx_util=25), apps=apps, processes=processes)
    assert code == 2, result
    rtx = next(item for item in result["resources"] if item["gpu_uuid"] == RTX)
    assert rtx["material_external_load"] is True


def test_unknown_compute_process_ownership_blocks_conservatively(tmp_path):
    apps = f"15868, unknown-worker.exe, 128, {P100}"
    code, result = _run(tmp_path, apps=apps, processes=[])
    assert code == 2
    assert result["status"] == "PRECHECK_BLOCKED"
    p100 = next(item for item in result["resources"] if item["gpu_uuid"] == P100)
    assert p100["unknown_compute_ownership"] is True
    assert p100["compute_processes"][0]["ownership"] == "UNKNOWN"


def test_unknown_worker_with_material_memory_and_utilization_blocks(tmp_path):
    apps = f"15869, mystery-worker.exe, 2048, {P100}"
    processes = [{"pid": 15869, "name": "mystery-worker.exe", "executable_path": "C:\\Workers\\mystery-worker.exe", "command_line": "mystery-worker.exe", "parent_pid": 1}]
    code, result = _run(tmp_path, smi=_smi(p100_util=35), apps=apps, processes=processes)
    assert code == 2
    p100 = next(item for item in result["resources"] if item["gpu_uuid"] == P100)
    assert p100["unknown_compute_ownership"] is True
    assert p100["material_external_load"] is True


def test_external_and_unknown_lane_ports_block(tmp_path):
    external = [{"port": 12409, "pid": 77}]
    processes = [{"pid": 77, "name": "ollama.exe", "executable_path": "C:\\ollama\\ollama.exe", "command_line": "ollama.exe serve", "parent_pid": 1}]
    assert _run(tmp_path, ports=external, processes=processes)[1]["status"] == "PRECHECK_BLOCKED"
    unknown = [{"port": 12100, "pid": 78}]
    assert _run(tmp_path, ports=unknown, processes=[])[1]["status"] == "PRECHECK_BLOCKED"


def test_expected_estate_lane_port_is_allowed(tmp_path):
    processes = [{"pid": 99, "name": "python.exe", "executable_path": str(ROOT / "python.exe"), "command_line": f"python {ROOT} --lane qwen.local.text.4090", "parent_pid": 1}]
    code, result = _run(tmp_path, ports=[{"port": 12409, "pid": 99}], processes=processes)
    assert code == 0
    assert result["status"] == "PASS"
    rtx = next(item for item in result["resources"] if item["gpu_uuid"] == RTX)
    assert rtx["lane_port_owner"]["ownership"] == "ESTATE_OWNED"


def test_json_contract_and_script_is_read_only():
    source = SCRIPT.read_text(encoding="utf-8").lower()
    for forbidden in (
        "stop-process", "taskkill", "stop-service", "restart-service",
        "ollama unload", "nvidia-smi.*--gpu-reset", "disable-pnpdevice",
        "enable-pnpdevice", "restart-computer", "stop-computer", "shutdown",
        "pnputil", "devcon", "torch", "diffusers", "llama-server.*--prompt",
    ):
        assert forbidden not in source
    assert all(token in source for token in ('status', 'resources', 'exit_code', 'uuid', 'pci_bus', 'pci_topology_changed', 'warnings', 'lane_port'))
    assert "gpu0" not in source and "gpu1" not in source
