from pathlib import Path

from estate.core.multi_repository_targets import MultiRepositoryOperationalTarget, default_multi_repository_targets


def test_default_targets_separate_estate_and_cue_mastery(tmp_path):
    targets = default_multi_repository_targets(tmp_path)
    by_id = {target.target_id: target for target in targets}

    assert set(by_id) == {"estate-main", "cue-mastery"}
    assert by_id["estate-main"].audit_enabled is True
    assert by_id["cue-mastery"].mode == "observe_only"
    assert by_id["cue-mastery"].read_only_observation is True
    assert by_id["cue-mastery"].audit_enabled is False
    assert by_id["estate-main"].workspace_root != by_id["cue-mastery"].workspace_root
    assert by_id["estate-main"].evidence_root != by_id["cue-mastery"].evidence_root


def test_target_scoped_paths_keep_state_isolated(tmp_path):
    target = MultiRepositoryOperationalTarget(
        target_id="repo-a",
        display_name="Repo A",
        repository_url="https://example.invalid/repo-a.git",
        repository_path=None,
        base_branch="trunk",
        workspace_root=str(tmp_path / "ws"),
        evidence_root=str(tmp_path / "evidence"),
        enabled_capabilities=["git", "validation"],
        watch_profile="generic",
        validation_binding={"kind": "custom", "command": "make check"},
        department_owner="Engineering",
    )

    assert target.scoped_path(tmp_path, "cursor") == tmp_path / "runtime/merge_discovery/targets/repo-a"
    assert target.scoped_path(tmp_path, "workspace") == tmp_path / "ws/repo-a"
    assert target.scoped_path(tmp_path, "evidence") == tmp_path / "evidence/repo-a"


def test_target_does_not_require_estate_work_package_validation_recipe(tmp_path):
    target = MultiRepositoryOperationalTarget(
        target_id="external-repo",
        display_name="External Repo",
        repository_url="https://example.invalid/external.git",
        repository_path=None,
        base_branch="main",
        workspace_root=str(tmp_path / "ws"),
        evidence_root=str(tmp_path / "evidence"),
        enabled_capabilities=["git"],
        watch_profile="manual",
        validation_binding={"kind": "none"},
        department_owner="Research",
        mode="observe_only",
    )

    data = target.to_dict()
    assert data["validation_binding"] == {"kind": "none"}
    assert data["read_only_observation"] is True
