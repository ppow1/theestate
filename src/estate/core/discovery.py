import json
import subprocess
from pathlib import Path
from estate.core.paths import ESTATE_ROOT

RUNTIME_DISCOVERY_DIR = ESTATE_ROOT / "runtime" / "discovery"
from estate.core.time import now

AI_HOME = Path(r"A:\AI")
OBS_DIR = ESTATE_ROOT / "observations"

def parse_ollama_models(models_raw):
    lines = [line.rstrip() for line in models_raw.splitlines() if line.strip()]
    if len(lines) <= 1:
        return []

    models = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 4:
            models.append({
                "name": parts[0],
                "id": parts[1],
                "size": " ".join(parts[2:4]),
                "modified": " ".join(parts[4:]) if len(parts) > 4 else ""
            })
    return models

def observe_ollama():
    try:
        version = subprocess.check_output(["ollama", "--version"], text=True, stderr=subprocess.STDOUT).strip()
        models_raw = subprocess.check_output(["ollama", "list"], text=True, stderr=subprocess.STDOUT).strip()
        return {
            "installed": True,
            "running": True,
            "version": version,
            "models_raw": models_raw,
            "models": parse_ollama_models(models_raw)
        }
    except Exception as e:
        return {
            "installed": False,
            "running": False,
            "error": str(e),
            "models": []
        }

def _as_names(items):
    if not items:
        return []
    if isinstance(items[0], dict):
        return sorted([item.get("name", "") for item in items if item.get("name")])
    return sorted(items)

def compare_lists(previous, current):
    prev = set(_as_names(previous))
    curr = set(_as_names(current))
    return {
        "added": sorted(curr - prev),
        "removed": sorted(prev - curr),
        "unchanged": sorted(curr & prev)
    }

def compare_observations(previous, current):
    if not previous:
        return {
            "first_observation": True,
            "changes": {
                "python_envs": compare_lists([], current.get("python_envs", [])),
                "tts_items": compare_lists([], current.get("tts_items", [])),
                "tool_items": compare_lists([], current.get("tool_items", [])),
                "model_categories": compare_lists([], current.get("model_categories", [])),
                "ollama_models": compare_lists([], current.get("ollama", {}).get("models", []))
            }
        }

    return {
        "first_observation": False,
        "changes": {
            "python_envs": compare_lists(previous.get("python_envs", []), current.get("python_envs", [])),
            "tts_items": compare_lists(previous.get("tts_items", []), current.get("tts_items", [])),
            "tool_items": compare_lists(previous.get("tool_items", []), current.get("tool_items", [])),
            "model_categories": compare_lists(previous.get("model_categories", []), current.get("model_categories", [])),
            "ollama_models": compare_lists(previous.get("ollama", {}).get("models", []), current.get("ollama", {}).get("models", []))
        }
    }

def has_changes(change_report):
    for section in change_report.get("changes", {}).values():
        if section.get("added") or section.get("removed"):
            return True
    return False

def observe_ai_environment():
    OBS_DIR.mkdir(parents=True, exist_ok=True)

    latest = OBS_DIR / "ai_environment_latest.json"
    previous = json.loads(latest.read_text(encoding="utf-8")) if latest.exists() else None

    envs_dir = AI_HOME / "envs"
    tts_dir = AI_HOME / "TTS"
    tools_dir = AI_HOME / "Tools"
    models_dir = AI_HOME / "Models"

    observations = {
        "timestamp": now(),
        "ai_home": str(AI_HOME),
        "paths": {
            "envs": str(envs_dir),
            "tts": str(tts_dir),
            "tools": str(tools_dir),
            "models": str(models_dir)
        },
        "exists": {
            "ai_home": AI_HOME.exists(),
            "envs": envs_dir.exists(),
            "tts": tts_dir.exists(),
            "tools": tools_dir.exists(),
            "models": models_dir.exists()
        },
        "python_envs": sorted([p.name for p in envs_dir.iterdir() if p.is_dir()]) if envs_dir.exists() else [],
        "tts_items": sorted([p.name for p in tts_dir.iterdir() if p.is_dir()]) if tts_dir.exists() else [],
        "tool_items": sorted([p.name for p in tools_dir.iterdir() if p.is_dir()]) if tools_dir.exists() else [],
        "model_categories": sorted([p.name for p in models_dir.iterdir() if p.is_dir()]) if models_dir.exists() else [],
        "ollama": observe_ollama()
    }

    change_report = compare_observations(previous, observations)
    observations["change_report"] = change_report
    observations["changed_since_previous"] = has_changes(change_report)

    latest.write_text(json.dumps(observations, indent=2), encoding="utf-8")

    stamp = observations["timestamp"].replace(":", "-").replace(" ", "_")
    history = OBS_DIR / f"ai_environment_{stamp}.json"
    history.write_text(json.dumps(observations, indent=2), encoding="utf-8")

    return observations, latest
from pathlib import Path
import json

def generate_discovery_report():
    latest = OBS_DIR / "ai_environment_latest.json"
    if not latest.exists():
        return "No discovery observation found. Run: estate discover-ai"

    data = json.loads(latest.read_text(encoding="utf-8"))
    report = []

    report.append("=" * 41)
    report.append("Estate Discovery Report")
    report.append("=" * 41)
    report.append("")
    report.append(f"Observation: {data.get('timestamp', '')}")
    report.append(f"AI_HOME: {data.get('ai_home', '')}")
    report.append("")
    report.append("Overall:")
    report.append("Healthy" if data.get("exists", {}).get("ai_home") else "Warning")
    report.append("")
    report.append("Changes since previous observation:")

    changes = data.get("change_report", {}).get("changes", {})
    any_change = False
    labels = {
        "python_envs": "Python Environment",
        "tts_items": "TTS Item",
        "tool_items": "Tool",
        "model_categories": "Model Category",
        "ollama_models": "Ollama Model"
    }

    for key, label in labels.items():
        section = changes.get(key, {})
        for item in section.get("added", []):
            report.append(f"  + {label}: {item}")
            any_change = True
        for item in section.get("removed", []):
            report.append(f"  - {label}: {item}")
            any_change = True

    if not any_change:
        report.append("  No changes detected.")

    report.append("")
    report.append("Python Environments:")
    for item in data.get("python_envs", []):
        report.append(f"  - {item}")

    report.append("")
    report.append("TTS Items:")
    for item in data.get("tts_items", []):
        report.append(f"  - {item}")

    report.append("")
    report.append("Tools:")
    for item in data.get("tool_items", []):
        report.append(f"  - {item}")

    report.append("")
    report.append("Ollama:")
    ollama = data.get("ollama", {})
    report.append("  Running" if ollama.get("running") else "  Not running")

    report.append("")
    report.append("Ollama Models:")
    for model in ollama.get("models", []):
        report.append(f"  - {model.get('name')} | {model.get('size')} | {model.get('modified')}")

    report.append("")
    report.append(f"Observation written to: {latest}")

    return "\n".join(report)




def _estate_contain_legacy_observation_writes(before_files):
    import shutil

    versioned_dir = ESTATE_ROOT / "observations"
    runtime_observations = RUNTIME_DISCOVERY_DIR / "observations"
    runtime_observations.mkdir(parents=True, exist_ok=True)

    # The legacy observer may still write a tracked/latest file.
    # Runtime owns latest state, so remove the versioned latest after mirroring.
    legacy_latest = versioned_dir / "ai_environment_latest.json"
    if legacy_latest.exists():
        legacy_latest.unlink()

    # Normal Discovery execution should not create versioned timestamp snapshots.
    # Move new timestamped observations into runtime history.
    after_files = set(versioned_dir.glob("ai_environment_*.json"))
    for path in sorted(after_files - before_files):
        if path.name.endswith("_latest.json"):
            continue
        target = runtime_observations / path.name
        shutil.move(str(path), str(target))


def _estate_write_runtime_latest(observation):
    import json
    RUNTIME_DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)
    runtime_latest = RUNTIME_DISCOVERY_DIR / "ai_environment_latest.json"
    runtime_latest.write_text(json.dumps(observation, indent=2, sort_keys=True), encoding="utf-8")


# Discovery Catalog integration.
# Wrapped here so every normal Discovery observation updates persistent catalog memory.
from estate.core.discovery_catalog import update_discovery_catalog as _estate_update_discovery_catalog

_estate_catalog_observe_ai_environment = observe_ai_environment

def observe_ai_environment():
    RUNTIME_DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)
    versioned_dir = ESTATE_ROOT / "observations"
    before_files = set(versioned_dir.glob("ai_environment_*.json"))

    observed = _estate_catalog_observe_ai_environment()

    if isinstance(observed, tuple):
        observation = observed[0]
    else:
        observation = observed

    if not isinstance(observation, dict):
        raise TypeError(f"observation root is {type(observation).__name__}, expected dict")

    _estate_write_runtime_latest(observation)
    _estate_contain_legacy_observation_writes(before_files)
    _estate_update_discovery_catalog(observation)
    return observation


# Runtime report fallback.
# Ensures discovery-report reads runtime latest state after runtime migration.
if "_estate_runtime_generate_discovery_report" not in globals():
    _estate_runtime_generate_discovery_report = generate_discovery_report

    def generate_discovery_report():
        import json

        report = _estate_runtime_generate_discovery_report()
        if "No discovery observation found" not in report:
            return report

        latest = RUNTIME_DISCOVERY_DIR / "ai_environment_latest.json"
        if not latest.exists():
            return report

        data = json.loads(latest.read_text(encoding="utf-8"))
        ollama = data.get("ollama", {}) or {}

        lines = [
            "=========================================",
            "Estate Discovery Report",
            "=========================================",
            f"Timestamp: {data.get('timestamp')}",
            f"AI Home: {data.get('ai_home')}",
            f"Changed Since Previous: {data.get('changed_since_previous')}",
            "",
            "Ollama:",
            f"  Running: {ollama.get('running')}",
            f"  Installed: {ollama.get('installed')}",
            f"  Version: {ollama.get('version')}",
            "",
            "Ollama Models:",
        ]

        for model in ollama.get("models", []) or []:
            if isinstance(model, dict):
                lines.append(f"  - {model.get('name')} | {model.get('size')} | {model.get('modified')}")
            else:
                lines.append(f"  - {model}")

        lines.extend([
            "",
            "Python Environments:",
        ])

        for env in data.get("python_envs", []) or []:
            lines.append(f"  - {env}")

        lines.extend([
            "",
            "AI Model Categories:",
        ])

        for category in data.get("model_categories", []) or []:
            lines.append(f"  - {category}")

        return "\n".join(lines)
