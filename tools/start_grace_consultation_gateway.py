from pathlib import Path
import sys

# The Resident Gateway must execute the workspace source that was accepted by
# tests, not an older globally installed Estate package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from estate.core.resident_gateway import serve


if __name__ == "__main__":
    serve(host="127.0.0.1", port=11435, root=r"A:\theestate")
