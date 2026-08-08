import copy
import json
import subprocess

import pytest

from estate.diagnostics.impact import create_packet, local_ai_delta, preserve_candidate, query_candidates
from estate.diagnostics.living import validate_impact_packet


def repository(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "src").mkdir(); (tmp_path / "src/example.py").write_text("before\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=tmp_path, check=True)
    return tmp_path


def request():
    return {"change_id":"LD-TEST", "author_provenance":{"kind":"HUMAN"},
            "changed_files":["src/example.py"], "confidence":"CANDIDATE",
            "preliminary_troubleshooting_notes":["candidate only"]}


def test_create_captures_clean_dirty_and_does_not_mutate_request(tmp_path):
    root=repository(tmp_path); original=request(); snapshot=copy.deepcopy(original)
    clean=create_packet(root,original)
    assert original==snapshot and clean["changed_artifacts"][0]["state"]=="CLEAN"
    assert clean["changed_artifacts"][0]["head_git_blob"]==clean["changed_artifacts"][0]["worktree_git_blob"]
    (root/"src/example.py").write_text("after\n")
    dirty=create_packet(root,original)
    assert dirty["changed_artifacts"][0]["state"]=="DIRTY"
    assert dirty["changed_artifacts"][0]["head_git_blob"]!=dirty["changed_artifacts"][0]["worktree_git_blob"]


@pytest.mark.parametrize("path", ["../escape", "/absolute", "src/missing.py"])
def test_create_rejects_unsafe_or_missing_paths(tmp_path,path):
    root=repository(tmp_path); value=request(); value["changed_files"]=[path]
    with pytest.raises(ValueError): create_packet(root,value)


def test_strict_validation_and_candidate_projection(tmp_path):
    root=repository(tmp_path); packet=create_packet(root,request())
    bad={**packet,"surprise":True}
    assert validate_impact_packet(bad,root)
    path=preserve_candidate(root,packet)
    candidate=json.loads(path.read_text())
    assert candidate["canonical_promotion"] is False
    assert query_candidates(root,"candidate only")[0]["change_id"]=="LD-TEST"
    delta=local_ai_delta(root)
    assert delta["may_advance_accepted_baseline"] is False
    assert delta["may_promote_canonical_knowledge"] is False
