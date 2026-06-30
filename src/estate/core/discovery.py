import json
import subprocess
from pathlib import Path
from estate.core.paths import ESTATE_ROOT
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
