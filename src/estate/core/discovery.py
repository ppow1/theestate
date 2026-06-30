from pathlib import Path
import json
from estate.core.paths import ESTATE_ROOT
from estate.core.time import now

AI_HOME = Path(r"A:\AI")
OBS_DIR = ESTATE_ROOT / "observations"

def observe_ai_environment():
    OBS_DIR.mkdir(parents=True, exist_ok=True)

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
        "model_categories": sorted([p.name for p in models_dir.iterdir() if p.is_dir()]) if models_dir.exists() else []
    }

    out = OBS_DIR / "ai_environment_latest.json"
    out.write_text(json.dumps(observations, indent=2), encoding="utf-8")
    return observations, out
