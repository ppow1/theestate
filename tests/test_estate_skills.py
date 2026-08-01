import json
from pathlib import Path
import pytest
from estate.core.estate_skills import SkillAmbiguity, SkillError, SkillRegistry, assess_readiness, grace_discover
from estate.core.repository_health_skill import execute

ROOT = Path(__file__).parents[1]
REGISTRY = ROOT / "config/skills/estate_skill_registry.json"

def test_closed_registry_and_alias_discovery():
    reg=SkillRegistry.load(REGISTRY)
    assert reg.discover("Check Git")[0]["skill_id"] == "repository-health"
    result=grace_discover(reg,"Could you check Git?")
    assert result["executed"] is False and result["request_provenance"] == "Could you check Git?"

def test_manifest_rejects_placeholder_absolute_and_hidden_authority():
    data=json.loads(REGISTRY.read_text())
    bad=json.loads(json.dumps(data["skills"][0])); bad["scope"]["reads"]=["A:\\secret"]
    with pytest.raises(SkillError):
        from estate.core.estate_skills import validate_manifest
        validate_manifest(bad)
    bad=json.loads(json.dumps(data["skills"][0])); bad["authority"]["implicit"] = True
    with pytest.raises(SkillError): validate_manifest(bad)

def test_alias_collision_and_readiness_gaps():
    data=json.loads(REGISTRY.read_text()); data["skills"].append(json.loads(json.dumps(data["skills"][0])))
    p=ROOT/".pytest-skill-registry.json"; p.write_text(json.dumps(data))
    try:
        with pytest.raises(SkillAmbiguity): SkillRegistry.load(p)
    finally: p.unlink()
    manifest=json.loads(REGISTRY.read_text())["skills"][0]
    readiness=assess_readiness(manifest,capabilities={"read_repository_state":{"available":False,"maturity":0}},providers={},workers={},authority=False)
    assert readiness["dispatchable"] is False and readiness["gaps"]

def test_receipt_replay_conflict_and_read_only_skill(tmp_path):
    import subprocess
    before=subprocess.check_output(["git","-C",str(ROOT),"status","--porcelain"],text=True)
    out=tmp_path/"reports"; report,receipt=execute(ROOT,output_dir=out,invocation_id="test-repository-health")
    assert receipt["status"] == "completed" and report["institutional_acceptance"] == "not_granted"
    with pytest.raises(SkillError): execute(ROOT,output_dir=out,invocation_id="test-repository-health")
    after=subprocess.check_output(["git","-C",str(ROOT),"status","--porcelain"],text=True)
    assert before == after

def test_diagnostic_discovery_never_executes():
    reg=SkillRegistry.load(REGISTRY)
    proposal=reg.proposal("Repo Health", "Repo Health")
    assert proposal["executed"] is False and proposal["status"] == "proposal_only"
