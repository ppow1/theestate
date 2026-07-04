import os
from pathlib import Path

def _discover_estate_root() -> Path:
    configured = os.environ.get("ESTATE_ROOT")
    if configured:
        return Path(configured)
    for candidate in (Path.cwd(), *Path.cwd().parents):
        if (candidate / "src" / "estate").exists() and (candidate / "README.md").exists():
            return candidate
    legacy = Path(r"A:\theestate")
    return legacy if legacy.exists() else Path.cwd()

ESTATE_ROOT = _discover_estate_root()
DATA_DIR = ESTATE_ROOT / "data"
REGISTRY_DIR = DATA_DIR / "registry"
OBJECTS_DIR = DATA_DIR / "objects"
LEDGER_PATH = ESTATE_ROOT / "estate_ledger" / "ledger.md"
DEVLOG_PATH = ESTATE_ROOT / "development" / "devlog.md"
RESIDENTS_DIR = ESTATE_ROOT / "residents"
