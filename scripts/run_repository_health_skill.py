"""Explicit operator entry point for the bounded Repository Health Skill."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from estate.core.estate_skills import SkillRegistry
from estate.core.repository_health_skill import execute

def main():
    ap=argparse.ArgumentParser(description="Run the read-only Repository Health Skill.")
    ap.add_argument("--root", required=True); ap.add_argument("--output-dir", required=True); ap.add_argument("--invocation-id")
    a=ap.parse_args(); registry=SkillRegistry.load(Path(a.root)/"config/skills/estate_skill_registry.json")
    skill=next(x for x in registry.skills if x["skill_id"]=="repository-health")
    report,receipt=execute(a.root,output_dir=a.output_dir,invocation_id=a.invocation_id,approved_worktrees=[a.root])
    print(json.dumps({"skill":skill["skill_id"],"status":receipt["status"],"report":receipt["artifacts"][0],"receipt":str(Path(a.output_dir)/(a.invocation_id or receipt["invocation_id"])).replace("\\", "/") + ".receipt.json"},indent=2))
if __name__ == "__main__": main()
