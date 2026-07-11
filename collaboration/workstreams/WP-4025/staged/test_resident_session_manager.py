from pathlib import Path
import json

import pytest

from resident_session_manager import ResidentSessionIdentity, ResidentSessionStore


def identity(resident_id="RES-000003"):
    return ResidentSessionIdentity(resident_id=resident_id, resident_name="Helen")


def test_sessions_survive_restart_resume_with_cycle_checkpoint_and_open_webui_mapping(tmp_path: Path):
    store = ResidentSessionStore(tmp_path, now="2026-07-11T00:00:00Z")
    session = store.create_session(
        identity(),
        name=" Grace onboarding recovery ",
        active_cycle_id="CYCLE-2026-07-11-A",
        open_webui_conversation_id="owui-conv-1",
        existing_chat_record_refs=["runtime/resident_chat/legacy-helen-1.jsonl"],
    )
    checkpoint = store.checkpoint(
        "RES-000003",
        session["session_id"],
        message_count=4,
        digest="sha256:checkpoint-a",
        conversation_record_ref="runtime/resident_chat/legacy-helen-2.jsonl",
    )

    restarted = ResidentSessionStore(tmp_path, now="2026-07-11T00:05:00Z")
    resumed = restarted.resume_session("RES-000003", session["session_id"])
    mapped = restarted.map_open_webui("RES-000003", "owui-conv-1")

    assert resumed["resume_from_checkpoint"]["checkpoint_id"] == checkpoint.checkpoint_id
    assert resumed["resume_from_checkpoint"]["active_cycle_id"] == "CYCLE-2026-07-11-A"
    assert resumed["conversation_record_refs"] == [
        "runtime/resident_chat/legacy-helen-1.jsonl",
        "runtime/resident_chat/legacy-helen-2.jsonl",
    ]
    assert mapped["session_id"] == session["session_id"]
    assert mapped["private_to_resident"] is True


def test_resident_identity_cannot_drift_and_public_office_surface_is_rejected(tmp_path: Path):
    store = ResidentSessionStore(tmp_path, now="2026-07-11T00:00:00Z")
    session = store.create_session(identity(), name="Private Helen session")

    with pytest.raises(PermissionError, match="resident identity mismatch"):
        store.resume_session("RES-000004", session["session_id"])

    with pytest.raises(PermissionError, match="public Office"):
        store.create_session(
            ResidentSessionIdentity(resident_id="RES-000003", office_surface="office_public"),
            name="Leaky session",
        )


def test_archive_and_forget_are_distinct_auditable_and_not_active_memory(tmp_path: Path):
    store = ResidentSessionStore(tmp_path, now="2026-07-11T00:00:00Z")
    archived = store.create_session(identity(), name="Archive me")
    forgotten = store.create_session(identity(), name="Forget me", open_webui_conversation_id="owui-forget")
    store.checkpoint("RES-000003", forgotten["session_id"], message_count=2, digest="sha256:secret")

    archived_row = store.archive_session("RES-000003", archived["session_id"], reason="operator closed loop")
    forgotten_row = store.forget_session("RES-000003", forgotten["session_id"], reason="resident privacy request")

    assert archived_row["status"] == "archived"
    assert archived_row["checkpoints"] == []
    assert forgotten_row["status"] == "forgotten"
    assert forgotten_row["checkpoints"] == []
    assert forgotten_row["conversation_record_refs"] == []
    assert "archived" in [entry["action"] for entry in archived_row["audit_log"]]
    assert "forgotten" in [entry["action"] for entry in forgotten_row["audit_log"]]
    assert store.list_sessions("RES-000003") == []
    assert len(store.list_sessions("RES-000003", include_archived=True, include_forgotten=True)) == 2
    with pytest.raises(ValueError, match="archived"):
        store.resume_session("RES-000003", archived["session_id"])
    assert store.map_open_webui("RES-000003", "owui-forget") is None


def test_interrupted_write_recovery_is_safe_and_listing_is_deterministic(tmp_path: Path):
    store = ResidentSessionStore(tmp_path, now="2026-07-11T00:00:00Z")
    first = store.create_session(identity(), name="B session")
    second = store.create_session(identity(), name="A session")

    registry_path = tmp_path / "resident_sessions.json"
    registry = json.loads(registry_path.read_text())
    registry["sessions"][first["session_id"]]["write_in_progress"] = True
    (tmp_path / "resident_sessions.json.tmp").write_text(json.dumps({"partial": True}))
    registry_path.write_text(json.dumps(registry))

    restarted = ResidentSessionStore(tmp_path, now="2026-07-11T00:10:00Z")
    recovery = restarted.recover()
    rows = restarted.list_sessions("RES-000003")

    assert recovery["recovered_session_ids"] == [first["session_id"]]
    assert (tmp_path / "resident_sessions.recovered.json").exists()
    assert [row["session_id"] for row in rows] == sorted([first["session_id"], second["session_id"]])
    assert {row["session_id"]: row["status"] for row in rows}[first["session_id"]] == "interrupted"
