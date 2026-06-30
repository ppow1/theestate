import json
from pathlib import Path

from estate.core.paths import ESTATE_ROOT
from estate.core.discovery_service import get_discovery_service

SERVICE_RUNTIME_PATH = ESTATE_ROOT / "runtime" / "services" / "status.json"


SERVICE_DEFINITIONS = [
    {
        "id": "image.generation",
        "name": "Image Generation",
        "resident": "Marie",
        "capabilities": ["image.generate", "image.workflow"],
        "providers": ["ComfyUI", "SDXL"],
        "requires": [
            "A:\\AI\\ComfyUI",
            "A:\\AI\\Models\\SDXL",
        ],
        "alfred_use": "Generate images using local ComfyUI and installed model assets.",
    },
    {
        "id": "speech.transcription",
        "name": "Speech Transcription",
        "resident": "Marie",
        "capabilities": ["audio.transcribe", "speech.to_text"],
        "providers": ["Whisper"],
        "requires": [
            "A:\\AI\\envs\\whisper_py311",
        ],
        "alfred_use": "Transcribe audio files into text using local Whisper tooling.",
    },
    {
        "id": "speech.synthesis",
        "name": "Speech Synthesis",
        "resident": "Marie",
        "capabilities": ["text.to_speech", "voice.generate"],
        "providers": ["Kokoro", "F5-TTS"],
        "requires": [
            "A:\\AI\\TTS",
        ],
        "alfred_use": "Generate voice/audio output from text using local TTS tooling.",
    },
    {
        "id": "code.assistance",
        "name": "Code Assistance",
        "resident": "Alfred",
        "capabilities": ["code.read", "code.write", "code.review", "debug"],
        "providers": ["Ollama", "qwen2.5-coder:7b"],
        "requires": [
            "ollama:qwen2.5-coder:7b",
        ],
        "alfred_use": "Assist with local code analysis, implementation, debugging, and review.",
    },
    {
        "id": "reasoning.local_llm",
        "name": "Local Reasoning",
        "resident": "Alfred",
        "capabilities": ["reason", "summarize", "plan"],
        "providers": ["Ollama", "llama3.2:3b"],
        "requires": [
            "ollama:llama3.2:3b",
        ],
        "alfred_use": "Use local lightweight LLM reasoning for planning, summaries, and private tasks.",
    },
]


def _path_requirement_ok(requirement):
    if requirement.startswith("ollama:"):
        model = requirement.split(":", 1)[1]
        latest = get_discovery_service().latest_observation()
        models = latest.get("ollama", {}).get("models", []) or []
        names = []
        for item in models:
            if isinstance(item, dict):
                names.append(item.get("name"))
            else:
                names.append(str(item))
        return model in names

    return Path(requirement).exists()


def list_services():
    return SERVICE_DEFINITIONS


def service_status():
    services = []

    for service in SERVICE_DEFINITIONS:
        requirements = []
        for requirement in service.get("requires", []):
            ok = _path_requirement_ok(requirement)
            requirements.append({
                "requirement": requirement,
                "ok": ok,
            })

        available = all(item["ok"] for item in requirements)

        services.append({
            "id": service["id"],
            "name": service["name"],
            "resident": service["resident"],
            "capabilities": service["capabilities"],
            "providers": service["providers"],
            "requirements": requirements,
            "available": available,
            "alfred_use": service["alfred_use"],
        })

    payload = {
        "version": 1,
        "services": services,
        "available": [service["id"] for service in services if service["available"]],
        "unavailable": [service["id"] for service in services if not service["available"]],
    }

    SERVICE_RUNTIME_PATH.parent.mkdir(parents=True, exist_ok=True)
    SERVICE_RUNTIME_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    return payload


def route_capability(capability):
    status = service_status()
    matches = []

    for service in status["services"]:
        if capability in service.get("capabilities", []):
            matches.append(service)

    return {
        "capability": capability,
        "matches": matches,
        "available": [service for service in matches if service.get("available")],
    }


def alfred_capabilities():
    status = service_status()
    capabilities = []

    for service in status["services"]:
        for capability in service.get("capabilities", []):
            capabilities.append({
                "capability": capability,
                "service": service["id"],
                "service_name": service["name"],
                "available": service["available"],
                "resident": service["resident"],
                "alfred_use": service["alfred_use"],
            })

    return {
        "version": 1,
        "services": status["services"],
        "capabilities": sorted(capabilities, key=lambda item: (item["available"] is False, item["capability"])),
    }


def format_service_status(payload=None):
    payload = payload or service_status()

    lines = [
        "=========================================",
        "Estate Service Status",
        "=========================================",
        f"Services: {len(payload.get('services', []))}",
        f"Available: {len(payload.get('available', []))}",
        f"Unavailable: {len(payload.get('unavailable', []))}",
        "",
    ]

    for service in payload.get("services", []):
        mark = "AVAILABLE" if service.get("available") else "UNAVAILABLE"
        lines.append(f"{mark} | {service['id']} | {service['name']}")
        lines.append(f"     Resident: {service['resident']}")
        lines.append(f"     Providers: {', '.join(service.get('providers', []))}")
        lines.append(f"     Capabilities: {', '.join(service.get('capabilities', []))}")
        lines.append(f"     Alfred: {service.get('alfred_use')}")
        for requirement in service.get("requirements", []):
            req_mark = "PASS" if requirement["ok"] else "MISS"
            lines.append(f"       {req_mark} {requirement['requirement']}")
        lines.append("")

    return "\n".join(lines)


def format_alfred_capabilities(payload=None):
    payload = payload or alfred_capabilities()

    lines = [
        "=========================================",
        "Alfred Capability Surface",
        "=========================================",
        "Alfred can route requests to the following Estate services:",
        "",
    ]

    for item in payload.get("capabilities", []):
        mark = "READY" if item.get("available") else "BLOCKED"
        lines.append(f"{mark} | {item['capability']} -> {item['service']}")
        lines.append(f"     {item['alfred_use']}")

    return "\n".join(lines)
