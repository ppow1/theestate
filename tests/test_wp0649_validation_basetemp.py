from pathlib import Path

from estate.core.work_package_validation import get_validation_recipe


def test_wp0618_repository_local_basetemp_parent_is_materialized() -> None:
    temp_parent = Path("Temp")

    assert temp_parent.is_dir()
    assert (temp_parent / ".gitkeep").is_file()


def test_wp0618_recipe_uses_tracked_repository_local_basetemp() -> None:
    recipe = get_validation_recipe("WP-0618")

    assert recipe is not None
    commands = [entry["command"] for entry in recipe["commands"]]
    pytest_commands = [command for command in commands if "pytest" in command]

    assert len(pytest_commands) == 1
    assert "--basetemp Temp/pytest-operational-targets-post-merge-audit" in pytest_commands[0]
