import json
import subprocess
from datetime import datetime, timedelta, timezone

from estate.core.codex_seat_telemetry import collect_codex_seat, collect_codex_seat_telemetry
from estate.core.engineering_capacity_runtime import _codex_seat_observations, generate_engineering_capacity_dashboard


def rpc_output(used_percent=25, reset=1786825960, include_weekly=True):
    rate_limits = {
        "rateLimits": {
            "primary": {"usedPercent": used_percent, "windowDurationMins": 10080 if include_weekly else 300, "resetsAt": reset},
            "secondary": None,
            "rateLimitReachedType": None,
        },
        "rateLimitsByLimitId": {},
    }
    return "\n".join([
        json.dumps({"id": 1, "result": {"codexHome": "test"}}),
        json.dumps({"id": 2, "result": {"account": {"type": "chatgpt", "planType": "team"}}}),
        json.dumps({"id": 3, "result": rate_limits}),
    ])


def test_each_seat_uses_its_own_child_home_and_preserves_native_weekly_fields():
    captured = []

    def runner(*args, **kwargs):
        captured.append((args[0], kwargs["env"]))
        seat = kwargs["env"]["CODEX_HOME"].rsplit("\\", 1)[-1]
        used = {"C1": 12, "C2": 37, "C3": 64}[seat]
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout=rpc_output(used), stderr="")

    payload = collect_codex_seat_telemetry(run_process=runner, write=False)
    observations = {item["seat_id"]: item for item in payload["seats"]}

    assert [item["seat_id"] for item in payload["seats"]] == ["C1", "C2", "C3"]
    assert [env["CODEX_HOME"] for _, env in captured] == [r"A:\AI\CodexProfiles\C1", r"A:\AI\CodexProfiles\C2", r"A:\AI\CodexProfiles\C3"]
    assert observations["C1"]["weekly_limit_percent_left"] == 88
    assert observations["C2"]["weekly_limit_percent_left"] == 63
    assert observations["C3"]["weekly_limit_percent_left"] == 36
    assert observations["C1"]["windows"][0]["window_minutes"] == 10080
    assert observations["C1"]["windows"][0]["resets_at_epoch"] == 1786825960
    assert observations["C1"]["weekly_limit_reset_at"] is not None
    assert observations["C1"]["capacity_identity"] == "codex.seat.C1"
    assert observations["C1"]["execution_modes"] == ["cli"]


def test_missing_weekly_data_is_unknown_without_fabricated_percentage():
    result = collect_codex_seat("C1", run_process=lambda *args, **kwargs: subprocess.CompletedProcess(args=args[0], returncode=0, stdout=rpc_output(include_weekly=False), stderr=""))

    assert result["collection_status"] == "unavailable"
    assert result["weekly_limit_percent_left"] is None
    assert result["weekly_limit_reset_at"] is None
    assert result["failure_reason"] == "no weekly rate-limit window was returned"


def test_runtime_marks_old_seat_observation_stale_and_keeps_native_data(tmp_path):
    old = (datetime.now(timezone.utc) - timedelta(hours=2)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    payload = {"version": 1, "seats": [{
        "seat_id": "C1", "capacity_identity": "codex.seat.C1", "execution_modes": ["cli", "cloud"],
        "execution_surface": "codex-cli", "source": "test", "observed_at": old,
        "collection_status": "available", "failure_reason": None, "account": {"type": "chatgpt"},
        "native_rate_limits": {"rateLimits": {"primary": {"usedPercent": 10, "windowDurationMins": 10080, "resetsAt": 1786825960}}},
        "windows": [{"window_minutes": 10080, "used_percent": 10, "remaining_percent": 90, "resets_at_epoch": 1786825960}],
        "weekly_limit_percent_left": 90, "weekly_limit_reset_at": "2026-08-15T16:32:00Z",
    }]}
    path = tmp_path / "runtime/engineering_capacity/codex_seat_telemetry.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

    observations = {item["logical_seat_id"]: item for item in _codex_seat_observations(tmp_path, stale_after_minutes=30)}

    assert observations["C1"]["freshness"]["state"] == "stale"
    assert observations["C1"]["weekly_limit_percent_left"] == 90
    assert observations["C2"]["weekly_limit_percent_left"] is None
    assert observations["C2"]["collection_success"] is False


def test_real_seat_telemetry_replaces_generic_codex_heuristic_in_dashboard(tmp_path):
    generated = collect_codex_seat_telemetry(root=tmp_path, run_process=lambda *args, **kwargs: subprocess.CompletedProcess(args=args[0], returncode=0, stdout=rpc_output(20), stderr=""))
    assert generated["seats"][0]["weekly_limit_percent_left"] == 80
    dashboard = generate_engineering_capacity_dashboard(root=tmp_path, write=False, stale_after_minutes=30)

    assert dashboard["codex_seat_telemetry_available"] is True
    assert all(item["capacity_identity"].startswith("codex.seat.") for item in dashboard["codex_seat_observations"])
    assert dashboard["codex_seat_observations"][0]["weekly_limit_percent_left"] == 80
