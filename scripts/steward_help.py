"""Generate or query the current read-only Steward help surface."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from estate.core.steward_help import answer, build_snapshot, write_surfaces

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("action",choices=["snapshot","cheat-sheet","ask"]); ap.add_argument("request",nargs="?"); ap.add_argument("--resident",default="Grace"); ap.add_argument("--root",type=Path,default=Path(__file__).parents[1]); ap.add_argument("--no-live-probes",action="store_true")
    a=ap.parse_args()
    if a.action in {"snapshot","cheat-sheet"}: print(json.dumps(write_surfaces(a.root),indent=2,sort_keys=True,default=str))
    else:
        s=build_snapshot(a.root,include_live_probes=not a.no_live_probes); print(json.dumps(answer(s,a.request or "help",resident=a.resident),indent=2,sort_keys=True))
if __name__ == "__main__": main()
