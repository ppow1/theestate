"""Deterministic fake runtime facts for WP-4028 staged tests."""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

MODULE_PATH = Path(__file__).parents[1] / "staged" / "local_ai_service_supervision.py"
spec = importlib.util.spec_from_file_location("local_ai_service_supervision", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

ServiceSpec = mod.ServiceSpec
RuntimeFact = mod.RuntimeFact


def service_specs():
    return [
        ServiceSpec("ollama", "Ollama", ("ollama", "serve"), port=11434, startup_timeout_seconds=45, cold_load_seconds=120, recovery_hints=("verify model store before restart",)),
        ServiceSpec("textgen", "TextGen", ("python", "server.py"), port=7860, dependencies=("ollama",), cold_load_seconds=180),
        ServiceSpec("open-webui", "Open WebUI", ("open-webui", "serve"), port=8080, dependencies=("ollama",)),
        ServiceSpec("resident-gateway", "Estate Resident Gateway", ("estate", "gateway"), port=8765, dependencies=("ollama", "open-webui"), resident_impact="resident chat gateway unavailable"),
    ]


def healthy_facts():
    return [
        RuntimeFact("ollama", "ready", pid=101, port_owner_pid=101, log_path="logs/ollama.log"),
        RuntimeFact("textgen", "ready", pid=102, port_owner_pid=102, log_path="logs/textgen.log"),
        RuntimeFact("open-webui", "ready", pid=103, port_owner_pid=103, log_path="logs/open-webui.log"),
        RuntimeFact("resident-gateway", "ready", pid=104, port_owner_pid=104, log_path="logs/gateway.log"),
    ]
