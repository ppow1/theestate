from estate.core.multi_repository_runtime import MultiRepositoryOperationalRuntime
from estate.core.multi_repository_targets import MultiRepositoryOperationalTarget


def _target(target_id, department="Engineering", mode="enabled"):
    return MultiRepositoryOperationalTarget(
        target_id=target_id,
        display_name=target_id.title(),
        repository_url=f"https://example.invalid/{target_id}.git",
        repository_path=None,
        base_branch="main",
        workspace_root=f"/tmp/ws/{target_id}",
        evidence_root=f"/tmp/evidence/{target_id}",
        enabled_capabilities=["git", "validation", "audit"],
        watch_profile="generic",
        validation_binding={"kind": "custom"},
        department_owner=department,
        mode=mode,
    )


def test_runtime_monitors_two_repositories_without_state_collision(tmp_path):
    rt = MultiRepositoryOperationalRuntime(tmp_path)
    rt.write_targets([_target("estate-main", "Estate"), _target("cue-mastery", "Engineering", "observe_only")])

    estate_paths = rt.isolated_paths("estate-main")
    cue_paths = rt.isolated_paths("cue-mastery")

    assert estate_paths["cursor"] != cue_paths["cursor"]
    assert estate_paths["workspace"] != cue_paths["workspace"]
    assert estate_paths["evidence"] != cue_paths["evidence"]
    assert estate_paths["holds"] != cue_paths["holds"]
    assert estate_paths["verdicts"] != cue_paths["verdicts"]


def test_runtime_failure_in_one_target_does_not_stop_other(tmp_path):
    rt = MultiRepositoryOperationalRuntime(tmp_path)
    rt.write_targets([_target("bad"), _target("good")])

    def handler(target):
        if target.target_id == "bad":
            raise RuntimeError("boom")
        return {"state": "observed", "target_id": target.target_id}

    payload = rt.run_cycle(handler)
    by_id = {item["target_id"]: item for item in payload["results"]}

    assert by_id["bad"]["state"] == "failed"
    assert by_id["good"]["state"] == "observed"
    assert payload["summary"]["failed_count"] == 1


def test_observe_only_can_later_enable_audits(tmp_path):
    rt = MultiRepositoryOperationalRuntime(tmp_path)
    rt.write_targets([_target("cue-mastery", mode="observe_only")])

    assert rt.get("cue-mastery").audit_enabled is False
    enabled = rt.set_mode("cue-mastery", "enabled")

    assert enabled["mode"] == "enabled"
    assert enabled["read_only_observation"] is False
    assert enabled["audit_enabled"] is True


def test_office_status_groups_by_repository_and_department(tmp_path):
    rt = MultiRepositoryOperationalRuntime(tmp_path)
    rt.write_targets([_target("estate-main", "Estate"), _target("cue-mastery", "Engineering", "observe_only")])

    status = rt.office_status()

    assert set(status["repositories_by_department"]) == {"Estate", "Engineering"}
    assert status["repositories_by_department"]["Engineering"][0]["target_id"] == "cue-mastery"
    assert status["repositories_by_department"]["Engineering"][0]["isolated_paths"]["cursor"].endswith("cue-mastery")
