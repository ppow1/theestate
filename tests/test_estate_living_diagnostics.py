from __future__ import annotations

import json
import subprocess
from pathlib import Path

from estate.diagnostics.living import (
    DiagnosticsRepository, applicability, build, component_for, excluded,
    generate_manifest, reconcile, sha256,
)

ROOT = Path(__file__).resolve().parents[1]


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.PIPE)


def synthetic(tmp_path: Path) -> tuple[Path, str]:
    root=tmp_path/"estate"; (root/"src").mkdir(parents=True); (root/"docs/operations/troubleshooting").mkdir(parents=True)
    target=root/"src/component.py"; target.write_text("A\n")
    h="sha256:"+sha256(target)
    cp={"checkpoint_id":"1.1.1","checkpoint_revision":"1","title":"Synthetic","workflow":"test","subsystem":"test","component_id":"test","symptoms":["broken"],"keywords":["broken"],"expected_input":"A","expected_output":"B","authority":"file","probe_summary":"read","known_failures":["BROKEN"],"failure_codes":["BROKEN"],"recovery_summary":"restore","prohibited_actions":["guess"],"source_dependencies":["src/component.py"],"validated_against":{"files":{"src/component.py":h}},"knowledge_provenance":{"method":"HUMAN"},"status":"VALIDATED"}
    (root/"docs/operations/troubleshooting/cookbook.json").write_text(json.dumps({"document_revision":"1","checkpoints":[cp],"diagrams":{"seven_step":"flowchart LR\nA-->B"}}))
    git(root,"init");git(root,"config","user.email","test@example.invalid");git(root,"config","user.name","test");git(root,"add",".");git(root,"commit","-m","A")
    return root,h


def test_manifest_schema_order_hash_blob_component_and_clean_state(tmp_path):
    root,_=synthetic(tmp_path); manifest=generate_manifest(root,"2000-01-01T00:00:00Z")
    assert manifest["manifest_version"]=="1.0.0"
    assert [x["path"] for x in manifest["artifacts"]]==sorted(x["path"] for x in manifest["artifacts"])
    artifact=next(x for x in manifest["artifacts"] if x["path"]=="src/component.py")
    assert artifact["content_hash"].startswith("sha256:") and artifact["git_blob_sha"] not in {"UNKNOWN","LOCAL_REVISION"}
    assert artifact["state"]=="TRACKED" and manifest["dirty_state"]["dirty"] is False
    assert component_for("src/estate/model_control/policy.py")=="model_control"
    assert artifact["component_version"]=="NOT_DECLARED"


def test_dirty_untracked_and_security_exclusions(tmp_path):
    root,_=synthetic(tmp_path); (root/"src/component.py").write_text("B\n"); (root/"src/new.py").write_text("new\n"); (root/"src/api_token.txt").write_text("nope")
    manifest=generate_manifest(root); by_path={x["path"]:x for x in manifest["artifacts"]}
    assert by_path["src/component.py"]["state"]=="MODIFIED"
    assert by_path["src/new.py"]["state"]=="UNTRACKED" and by_path["src/new.py"]["git_blob_sha"]=="LOCAL_REVISION"
    assert "src/api_token.txt" not in by_path and excluded(Path("runtime/cookies.json"))


def test_staleness_change_restore_and_missing(tmp_path):
    root,h=synthetic(tmp_path); cp=json.loads((root/"docs/operations/troubleshooting/cookbook.json").read_text())["checkpoints"][0]
    artifact=lambda: {x["path"]:x for x in generate_manifest(root)["artifacts"]}
    assert applicability(cp,artifact())[0]=="VALIDATED"
    (root/"src/component.py").write_text("B\n"); assert applicability(cp,artifact())[0]=="REVALIDATION_REQUIRED"
    (root/"src/component.py").write_text("A\n"); assert applicability(cp,artifact())[0]=="VALIDATED"
    (root/"src/component.py").unlink(); status,diff=applicability(cp,artifact()); assert status=="REVALIDATION_REQUIRED" and diff[0]["reason"]=="MISSING_DEPENDENCY"
    assert h.startswith("sha256:")


def test_build_query_html_mermaid_json_and_determinism(tmp_path):
    root,_=synthetic(tmp_path); first=build(root,"2000-01-01T00:00:00Z"); before={p.name:p.read_bytes() for p in (root/"docs/operations/troubleshooting/generated").iterdir()}; second=build(root,"2000-01-01T00:00:00Z")
    assert before=={p.name:p.read_bytes() for p in (root/"docs/operations/troubleshooting/generated").iterdir()}
    repo=DiagnosticsRepository(root); assert repo.search("broken")[0]["checkpoint_id"]=="1.1.1"
    assert repo.checkpoint("1.1.1")["title"]=="Synthetic" and repo.affected(["src/component.py"])
    assert "mermaid" in (root/"docs/operations/troubleshooting/generated/index.html").read_text()
    assert json.loads((root/"docs/operations/troubleshooting/generated/search-index.json").read_text())["entries"]
    assert first["checkpoint_count"]==second["checkpoint_count"]==1


def test_no_provider_negative_reconciliation_and_no_false_validation(tmp_path):
    root,_=synthetic(tmp_path); accepted=root/"accepted.json"; accepted.write_text(json.dumps(generate_manifest(root)))
    (root/"src/component.py").write_text("B\n")
    result=reconcile(root,accepted)
    assert result["reconciliation_outcome"]=="REVALIDATION_REQUIRED"
    assert "CHANGE_WITHOUT_DIAGNOSTIC_IMPACT_METADATA" in result["classifications"]
    assert result["checkpoint_counts"]["REVALIDATION_REQUIRED"]==1
    assert result["provider_independence"].endswith("without an AI provider")
    assert (root/"docs/operations/troubleshooting/generated/index.html").exists()


def test_incremental_packet_candidate_never_auto_validates(tmp_path):
    root,_=synthetic(tmp_path); accepted=root/"accepted.json"; accepted.write_text(json.dumps(generate_manifest(root))); (root/"src/component.py").write_text("B\n")
    packet=root/"packet.json"; packet.write_text(json.dumps({"packet_version":"1.0.0","change_id":"EC-X","author_provenance":{"kind":"HUMAN"},"changed_files":["src/component.py"],"source_revision":"local","confidence":"CANDIDATE"}))
    result=reconcile(root,accepted,[packet],"incremental")
    assert result["mode"]=="incremental" and result["impact_packets_consumed"]==1
    assert result["pending_candidate_knowledge"]==["EC-X"] and result["canonical_knowledge_auto_modified"] is False
    assert result["classifications"]==[] and result["checkpoint_counts"]["REVALIDATION_REQUIRED"]==1


def test_seeded_search_replays_and_failure_codes():
    build(ROOT,"2000-01-01T00:00:00Z"); repo=DiagnosticsRepository(ROOT)
    queries={"composer missing":"5.1.1","queued but never claimed":"2.1.1","codex says done grace did not answer":"8.1.1","which model is grace using":"10.1.1","cme owner stale":"3.1.1","execution evidence missing":"8.1.1","worktree dirty":"11.1.1","provider quota exhausted":"7.1.1"}
    for query, expected in queries.items(): assert repo.search(query)[0]["checkpoint_id"]==expected
    codes={c for x in repo.generated("search-index.json")["entries"] for c in x["failure_codes"]}
    assert {"COMPOSER_NOT_READY","MCP_NOT_INVOKED","ACTIVE_LEASE","PROCESS_OBSERVER_EFFECT"} <= codes
