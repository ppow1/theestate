import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "staged" / "local_ai_service_supervision.py"
spec = importlib.util.spec_from_file_location("local_ai_service_supervision", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

ServiceSpec = mod.ServiceSpec
RuntimeFact = mod.RuntimeFact
RecoveryPolicy = mod.RecoveryPolicy
LocalAIServiceSupervisor = mod.LocalAIServiceSupervisor


def supervisor():
    return LocalAIServiceSupervisor(
        [
            ServiceSpec("ollama", "Ollama", ("ollama", "serve"), port=11434, cold_load_seconds=120, max_recovery_attempts=2),
            ServiceSpec("open-webui", "Open WebUI", ("open-webui", "serve"), port=8080, dependencies=("ollama",)),
            ServiceSpec("gateway", "Resident Gateway", ("estate", "gateway"), port=8765, dependencies=("ollama", "open-webui"), resident_impact="resident chat gateway unavailable"),
        ],
        now="2026-07-11T00:00:00+00:00",
    )


def test_truthful_dependency_state_and_resident_availability():
    runtime = supervisor()
    rows = runtime.inspect([
        RuntimeFact("ollama", "ready", pid=11, port_owner_pid=11),
        RuntimeFact("open-webui", "stopped"),
        RuntimeFact("gateway", "ready", pid=13, port_owner_pid=13),
    ])
    assert rows["gateway"]["state"] == "ready"
    assert rows["gateway"]["dependency_states"] == {"ollama": "ready", "open-webui": "stopped"}
    assert rows["gateway"]["resident_available"] is False
    assert rows["gateway"]["resident_impact"] == "resident chat gateway unavailable"


def test_start_plan_is_dependency_ordered_and_approval_bound():
    runtime = supervisor()
    plan = runtime.plan("start", "gateway", [RuntimeFact("ollama", "ready", pid=11, port_owner_pid=11), RuntimeFact("open-webui", "ready", pid=12, port_owner_pid=12)])
    assert [step["service_id"] for step in plan["steps"]] == ["ollama", "open-webui", "gateway"]
    assert plan["approval_bound"] is True
    assert all(step["auto_execute"] is False for step in plan["steps"])
    assert runtime.audit_events[-1]["event"] == "service_plan_created"


def test_occupied_port_and_stale_process_are_diagnosable_and_block_recovery():
    runtime = supervisor()
    plan = runtime.plan("start", "ollama", [RuntimeFact("ollama", "stopped", pid=44, port_owner_pid=99, port_owner_name="other-server")])
    diagnostics = plan["steps"][0]["diagnostics"]
    assert diagnostics["occupied_port"] is True
    assert diagnostics["stale_process"] is True
    assert "ollama: port occupied by non-service process" in plan["blocked_reasons"]
    assert plan["resident_available"] is False


def test_bounded_recovery_policy_blocks_exhausted_restart():
    runtime = supervisor()
    plan = runtime.plan("restart", "ollama", [RuntimeFact("ollama", "failed")], RecoveryPolicy(attempts_by_service={"ollama": 2}))
    assert plan["blocked"] is True
    assert "ollama: bounded recovery attempts exhausted" in plan["blocked_reasons"]
    assert plan["steps"][0]["requires_approval"] is True


def test_status_payload_does_not_require_approval_or_fabricate_availability_for_cold_load():
    runtime = supervisor()
    plan = runtime.plan("status", "ollama", [RuntimeFact("ollama", "cold_loading", pid=11, port_owner_pid=11, detail="loading model weights")])
    assert plan["approval_bound"] is False
    assert plan["resident_available"] is False
    assert plan["status"]["diagnostics"]["cold_loading"] is True
    assert plan["status"]["cold_load_seconds"] == 120
