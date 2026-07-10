import json

from estate.core.background_operations_extension_runtime import BackgroundOperationsExtensionRuntime
from estate.core.background_operations_runtime import BackgroundOperationsRuntime
from estate.core.office_command_surface import execute_office_action


def test_runtime_discovers_only_committed_configuration_and_dry_runs(tmp_path):
    rt = BackgroundOperationsExtensionRuntime(tmp_path)
    payload = rt.dry_run()
    assert payload["dry_run"] is True
    assert payload["provider_execution_performed"] is False
    assert payload["dispatch_execution_performed"] is False
    assert {w["watch_id"] for w in payload["would_register_watches"]} >= {"pending_routing_recommendation_watch", "cue_mastery_briefing_watch"}
    assert (tmp_path / "config/background_operations/extensions.json").exists()


def test_invalid_extension_is_quarantined_and_reported(tmp_path):
    path = tmp_path / "config/background_operations/extensions.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 1, "extensions": [{"extension_id": "bad!", "name": "Bad", "version": "no", "enabled": True, "classification": "Estate Internal", "capabilities": ["watch_provider"]}]}), encoding="utf-8")
    payload = BackgroundOperationsExtensionRuntime(tmp_path).validate()
    assert payload["valid"] is False
    assert payload["quarantined_extensions"][0]["state"] == "quarantined"


def test_disable_hides_extension_watches_and_office_control_reports_state(tmp_path):
    rt = BackgroundOperationsExtensionRuntime(tmp_path)
    rt.disable("cue_mastery_monitoring")
    watches, failures = rt.extension_watches()
    assert failures == []
    assert "cue_mastery_briefing_watch" not in {w.watch_id for w in watches}
    result = execute_office_action("operations_surface.extension_control", root=tmp_path, extension_action="inspect")
    assert result["outcome"] == "completed"
    status = json.loads((tmp_path / "runtime/background_operations/extensions/status.json").read_text())
    assert status["summary"]["enabled_count"] == 1


def test_background_runtime_includes_extension_state_and_isolates_failing_watch(tmp_path):
    path = tmp_path / "config/background_operations/extensions.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema_version": 1, "extensions": [{"extension_id": "estate_builtin_monitoring", "name": "Estate", "version": "1.0.0", "enabled": True, "classification": "Estate Internal", "capabilities": ["watch_provider"], "watch_provider": {"watches": [{"watch_id": "broken_watch"}]}}]}), encoding="utf-8")
    status = BackgroundOperationsRuntime(tmp_path).run_cycle(write=True)
    assert status["extensions"]["summary"]["quarantined_count"] == 0
    assert "background_operations_extensions_count" in status["summary"]
