import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from estate.core.governed_provider_scheduler import GovernedProviderScheduler
from estate.core.worker_assignment_runtime import WorkerAssignmentRuntime
from estate.core.provider_capacity import ProviderCapacityRecord, write_capacity_record
from estate.core.provider_health import ProviderHealthRecord, write_health_record


def assignment(tmp_path, *, priority="normal", provider="codex_cli_openai"):
    rt = WorkerAssignmentRuntime(tmp_path)
    rec, _ = rt.create_assignment(
        assigned_by="Grace",
        assigned_to="Codex",
        mission="Implement governed queue",
        summary="safe summary",
        priority=priority,
        provider_id=provider,
        work_package_id="WP-0541",
        validation_required=True,
        metadata={"summary_safe": True},
    )
    return rec


def health(tmp_path, provider="codex_cli_openai", state="available", capacity="available", max_jobs=1):
    write_health_record(ProviderHealthRecord.create(provider_id=provider, status=state, reported_by="test", message="test health", metadata={"authentication_state": "valid"}), root=tmp_path, validate_catalog=False)
    write_capacity_record(ProviderCapacityRecord.create(provider_id=provider, capacity_state=capacity, reported_by="test", max_jobs=max_jobs), root=tmp_path, validate_catalog=False)


def test_enqueue_is_idempotent_and_recommend_orders_by_priority(tmp_path):
    health(tmp_path, max_jobs=2)
    low = assignment(tmp_path, priority="low")
    high = assignment(tmp_path, priority="high")
    sched = GovernedProviderScheduler(tmp_path)
    sched.enqueue(low.assignment_id, actor="test")
    sched.enqueue(low.assignment_id, actor="test")
    sched.enqueue(high.assignment_id, actor="test")
    report = sched.recommend(actor="test")
    assert [d["assignment_id"] for d in report["decisions"][:2]] == [high.assignment_id, low.assignment_id]
    assert len(sched._queue()["items"]) == 2


def test_unhealthy_provider_excluded_with_reason(tmp_path):
    health(tmp_path, state="offline")
    rec = assignment(tmp_path)
    sched = GovernedProviderScheduler(tmp_path)
    sched.enqueue(rec.assignment_id, actor="test")
    decision = sched.recommend(actor="test")["decisions"][0]
    assert decision["eligible"] is False
    assert any("health" in r for r in decision["reasons"])


def test_reserve_release_and_expired_recovery_do_not_dispatch(tmp_path):
    health(tmp_path)
    rec = assignment(tmp_path)
    sched = GovernedProviderScheduler(tmp_path)
    sched.enqueue(rec.assignment_id, actor="test")
    reserved = sched.reserve(actor="test", ttl_minutes=30)
    assert reserved["reserved"] is True
    assert reserved["item"]["reservation"]["dispatch_required"] is True
    released = sched.release(rec.assignment_id, actor="test")
    assert released["state"] == "released_to_dispatch"
    assert released["release"]["dispatch_required"] is True

    rec2 = assignment(tmp_path, priority="urgent")
    sched.enqueue(rec2.assignment_id, actor="test")
    reserved2 = sched.reserve(actor="test", ttl_minutes=1)["item"]
    q = sched._queue()
    item = next(i for i in q["items"] if i["assignment_id"] == rec2.assignment_id)
    item["reservation"]["expires_at"] = (datetime.now(timezone.utc) - timedelta(minutes=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    sched._save_queue(q)
    recovery = sched.recover(actor="test")
    assert rec2.assignment_id in recovery["recovered_assignment_ids"]
    assert next(i for i in sched._queue()["items"] if i["assignment_id"] == rec2.assignment_id)["state"] == "queued"


def test_pause_and_provider_exclusion_are_auditable_and_reversible(tmp_path):
    health(tmp_path)
    rec = assignment(tmp_path)
    sched = GovernedProviderScheduler(tmp_path)
    sched.enqueue(rec.assignment_id, actor="test")
    sched.exclude_provider("codex_cli_openai", actor="test", reason="maintenance")
    assert sched.recommend(actor="test")["decisions"][0]["eligible"] is False
    sched.exclude_provider("codex_cli_openai", actor="test", reason="maintenance over", excluded=False)
    sched.pause(actor="test", reason="emergency")
    assert sched.recommend(actor="test")["decisions"][0]["eligible"] is False
    sched.pause(actor="test", reason="resume", paused=False)
    assert sched.recommend(actor="test")["decisions"][0]["eligible"] is True
    history = (tmp_path / "runtime/engineering_scheduler/decisions.jsonl").read_text()
    assert "provider_exclusion" in history and "resume" in history
