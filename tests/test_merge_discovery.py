import json, subprocess
from pathlib import Path
from estate.core.operational_targets import OperationalTarget
from estate.core.operational_targets_runtime import OperationalTargetRuntime
from estate.core.merge_discovery import MergeDiscovery


def git(repo,*a): return subprocess.run(["git",*a],cwd=repo,text=True,capture_output=True,check=True).stdout.strip()
def repo(tmp):
    r=tmp/"repo"; r.mkdir(parents=True); git(r,"init","-b","main"); git(r,"config","user.email","t@example.com"); git(r,"config","user.name","T")
    (r/"README.md").write_text("init"); git(r,"add","."); git(r,"commit","-m","init")
    return r
def target(tmp,r, tid="estate-main"):
    OperationalTargetRuntime(tmp).write_targets([OperationalTarget(tid,"Estate Main","git_repository","Estate",local_path=str(r),aliases=["estate"],base_branch="main",capabilities=["git","validation","audit"],watch_state="enabled")])
def receipt_commit(r, wp="WP-0623", content_wp=None, msg=None, fname_wp=None):
    d=r/"collaboration/work_packages/completions"; d.mkdir(parents=True,exist_ok=True)
    data={"codex_status":"done","ready_for_ca_review":True,"files_changed":["README.md"]}
    if content_wp is not False: data["work_package_id"]=content_wp or wp
    (d/f"{fname_wp or wp}_codex_done.json").write_text(json.dumps(data))
    git(r,"add","."); git(r,"commit","-m",msg or f"Complete {wp}"); return git(r,"rev-parse","HEAD")

def test_first_bounded_scan_creates_cursor_and_receipt_resolves_work_package(tmp_path):
    r=repo(tmp_path); sha=receipt_commit(r,"WP-0623"); target(tmp_path,r)
    out=MergeDiscovery(tmp_path).scan("estate",max_commits=100)
    assert (tmp_path/"runtime/merge_discovery/targets/estate-main/cursor.json").exists()
    rec=out["records"][-1]; assert rec["work_package_id"]=="WP-0623"; assert rec["correlation_method"]=="receipt_work_package_id"
    assert out["summary"]["quarantined_discoveries"] == 1

def test_later_scan_only_new_commits_and_duplicate_suppresses_repeat(tmp_path):
    r=repo(tmp_path); receipt_commit(r,"WP-0623"); target(tmp_path,r)
    first=MergeDiscovery(tmp_path).scan("estate-main")
    second=MergeDiscovery(tmp_path).scan("estate-main")
    assert first["summary"]["quarantined_discoveries"]==1
    assert second["records"]==[]
    replay=MergeDiscovery(tmp_path).scan("estate-main", replay=True)
    assert replay["summary"]["requests_suppressed_by_grouping"]>=0

def test_changed_receipt_filename_and_commit_message_fallback(tmp_path):
    r=repo(tmp_path); receipt_commit(r,"WP-0504",content_wp=False); target(tmp_path,r)
    out=MergeDiscovery(tmp_path).scan("estate-main")
    assert out["records"][-1]["correlation_method"]=="receipt_filename"
    (r/"note.txt").write_text("x"); git(r,"add","."); git(r,"commit","-m","Promote WP-0505")
    out2=MergeDiscovery(tmp_path).scan("estate-main")
    assert out2["records"][-1]["work_package_id"]=="WP-0505"
    assert out2["records"][-1]["correlation_method"]=="commit_message"

def test_conflicting_ids_ambiguous_and_incomplete_receipt_warning(tmp_path):
    r=repo(tmp_path); receipt_commit(r,"WP-0504",content_wp="WP-0505",fname_wp="WP-0504"); target(tmp_path,r)
    out=MergeDiscovery(tmp_path).scan("estate-main")
    assert out["records"][-1]["state"]=="ambiguous"
    r2=repo(tmp_path/"b"); receipt_commit(r2,"WP-0506",content_wp=False); target(tmp_path/"b",r2)
    out2=MergeDiscovery(tmp_path/"b").scan("estate-main")
    assert "completion_receipt_missing_work_package_id" in out2["records"][-1]["warnings"]

def test_existing_final_verdict_suppresses_and_canonical_target_used(tmp_path):
    r=repo(tmp_path); receipt_commit(r,"WP-0623"); target(tmp_path,r)
    vd=tmp_path/"runtime/post_merge_audit/verdicts"; vd.mkdir(parents=True)
    (vd/"v.json").write_text(json.dumps({"target_id":"estate-main","work_package_id":"WP-0623","verdict":"ring2_required"}))
    out=MergeDiscovery(tmp_path).scan("estate")
    rec=out["records"][-1]
    assert rec["target_id"]=="estate-main"; assert rec["state"]=="already_processed"


def test_pending_only_work_package_commit_is_not_admitted(tmp_path):
    r=repo(tmp_path); target(tmp_path,r)
    d=r/"collaboration/work_packages/pending"; d.mkdir(parents=True,exist_ok=True)
    (d/"WP-0637_plan.md").write_text("plan")
    git(r,"add","."); git(r,"commit","-m","Plan WP-0637")
    out=MergeDiscovery(tmp_path).scan("estate-main")
    assert out["records"] == []


def test_origin_main_source_of_truth_with_local_main_behind_and_dirty(tmp_path):
    remote=tmp_path/"remote.git"; git(tmp_path,"init","--bare",str(remote))
    work=tmp_path/"work"; git(tmp_path,"clone",str(remote),str(work)); git(work,"checkout","-b","main"); git(work,"config","user.email","t@example.com"); git(work,"config","user.name","T")
    (work/"README.md").write_text("init"); git(work,"add","."); git(work,"commit","-m","init"); git(work,"push","-u","origin","main")
    local=tmp_path/"local"; git(tmp_path,"clone",str(remote),str(local)); git(local,"checkout","main"); git(local,"config","user.email","t@example.com"); git(local,"config","user.name","T")
    receipt_commit(work,"WP-0637"); git(work,"push","origin","main")
    (local/"dirty.txt").write_text("active edits")
    target(tmp_path,local)
    out=MergeDiscovery(tmp_path).scan("estate-main")
    assert out["summary"]["watched_remote_ref"] == "origin/main"
    assert out["records"][-1]["work_package_id"] == "WP-0637"
    assert out["cursor"]["last_scanned_commit"] == git(local,"rev-parse","origin/main")
    assert not (local/"collaboration/work_packages/completions/WP-0637_codex_done.json").exists()


def test_failed_fetch_preserves_cursor(tmp_path, monkeypatch):
    r=repo(tmp_path); receipt_commit(r,"WP-0637"); target(tmp_path,r)
    first=MergeDiscovery(tmp_path).scan("estate-main")
    from estate.core import merge_discovery as md
    real=md._git_ok
    def fake(repo_path,*args):
        if args[:2] == ("remote","get-url"):
            return ("bad", "", 0)
        if args[:2] == ("fetch","--quiet"):
            return ("", "network down", 1)
        return real(repo_path,*args)
    monkeypatch.setattr(md,"_git_ok",fake)
    second=MergeDiscovery(tmp_path).scan("estate-main")
    assert second["summary"]["fetch_failed"] is True
    assert second["cursor"]["last_scanned_commit"] == first["cursor"]["last_scanned_commit"]
