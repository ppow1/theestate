import json

from estate.core.paths import ESTATE_ROOT

RUNTIME_DISCOVERY_DIR = ESTATE_ROOT / "runtime" / "discovery"
RUNTIME_OBSERVATIONS_DIR = RUNTIME_DISCOVERY_DIR / "observations"
RUNTIME_LATEST_OBSERVATION_PATH = RUNTIME_DISCOVERY_DIR / "ai_environment_latest.json"


def ensure_runtime_discovery_dirs():
    RUNTIME_DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_OBSERVATIONS_DIR.mkdir(parents=True, exist_ok=True)


def read_runtime_latest(default=None):
    if not RUNTIME_LATEST_OBSERVATION_PATH.exists():
        return default
    return json.loads(RUNTIME_LATEST_OBSERVATION_PATH.read_text(encoding="utf-8"))
