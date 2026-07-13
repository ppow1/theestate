from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Ensure subprocess CLI invocations can import the src-layout package during pytest.
import os
from pathlib import Path

_repo_src = str(Path(__file__).resolve().parents[1] / "src")
os.environ["PYTHONPATH"] = _repo_src + (os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")
