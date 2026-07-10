from estate.core.operational_target_validation_binding import OperationalTargetValidationBinder
from estate.core.operational_targets import OperationalTarget
from estate.core.operational_targets_runtime import OperationalTargetRuntime


def write(root, target):
    OperationalTargetRuntime(root).write_targets([target])


def test_ready_default_estate_binding(tmp_path):
    res = OperationalTargetValidationBinder(tmp_path).bind("estate")
    assert res.ready
    assert res.canonical_target_id == "estate-main"


def test_blocking_states_and_import_candidate_do_not_bind(tmp_path):
    for state in ["paused", "disabled", "retired", "blocked", "import_candidate"]:
        write(tmp_path, OperationalTarget("x", "X", "git_repository", "D", local_path=str(tmp_path), base_branch="main", capabilities=["git", "validation", "audit"], watch_state=state))
        res = OperationalTargetValidationBinder(tmp_path).bind("x")
        assert not res.ready
        assert f"state:{state}" in res.missing_requirements


def test_missing_capability_and_paths_block(tmp_path):
    write(tmp_path, OperationalTarget("x", "X", "git_repository", "D", local_path=None, workspace_root="", base_branch="", validation_root="", capabilities=["git"], watch_state="enabled"))
    res = OperationalTargetValidationBinder(tmp_path).bind("x")
    assert not res.ready
    assert "capability:audit" in res.missing_requirements
    assert "capability:validation" in res.missing_requirements
    assert "local_path_or_workspace_source" in res.missing_requirements
    assert "base_branch" in res.missing_requirements
