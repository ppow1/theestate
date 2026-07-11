from estate.core.codex_status_cost_characterization import characterize_codex_status_cost


def test_codex_status_characterization_is_conservative(tmp_path):
    payload = characterize_codex_status_cost(root=tmp_path, probe=False, write=True)
    assert payload["safe_polling_policy"] == "disabled_until_verified"
    assert payload["constraints"]["does_not_run_prompts"] is True
    assert payload["constraints"]["assumes_status_is_not_free"] is True
    assert (tmp_path / "runtime/engineering_capacity/codex_status_cost_characterization.json").exists()
    assert (tmp_path / "operations/engineering_capacity/codex_status_cost_characterization.md").exists()
