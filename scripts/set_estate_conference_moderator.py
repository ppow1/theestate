"""Supported Estate CLI for conference moderator configuration."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from estate.core.conference_room_lifecycle import load_config, resolve_active_resident, update_default_moderator

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--resident"); parser.add_argument("--verify",action="store_true"); parser.add_argument("--root",default=Path(__file__).resolve().parents[1]); args=parser.parse_args()
    if args.verify:
        config=load_config(args.root); resident=resolve_active_resident(config["default_moderator_resident_id"],args.root)
        print(json.dumps({"default_moderator":resident["name"],"resident_id":resident["id"],"restart_required":False},indent=2)); return
    if not args.resident: parser.error("--resident is required unless --verify is used")
    result=update_default_moderator(args.resident,args.root)
    print(json.dumps({"former":result["former"]["name"],"new":result["new"]["name"],"backup_path":result["backup_path"],"restart_required":False,"verification_command":"python scripts/set_estate_conference_moderator.py --verify"},indent=2))

if __name__ == "__main__": main()
