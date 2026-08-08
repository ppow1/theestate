from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest

from estate.diagnostics.impact import PacketError, artifact_identity, baseline, create_packet, local_ai_delta, reconcile


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "docs/operations/troubleshooting").mkdir(parents=True)
    (tmp_path / "docs/operations/troubleshooting/checkpoints.json").write_text(json.dumps({"checkpoints": [{"id": "CP-1", "title": "fixture", "state": "VALIDATED", "artifact_globs": ["fixture/**"], "canonical_knowledge": {"probe": "old canonical probe"}}]}))
    (tmp_path / "fixture").mkdir()
    (tmp_path / "fixture/software.py").write_text("VALUE = 1\n")
    git(tmp_path, "init", "-q"); git(tmp_path, "config", "user.email", "test@example.invalid"); git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "add", "."); git(tmp_path, "commit", "-qm", "baseline")
    return tmp_path


def request() -> dict:
    return {"packet_id": "TEST-1", "component": "synthetic-fixture", "intended_behavior": "change fixture value", "changed_files": ["fixture/software.py"], "dependencies": ["python"], "invariants": ["canonical text is immutable"], "failure_seams": ["wrong value"], "probes": ["python fixture/software.py"], "evidence": ["tests/test_living_diagnostics_ingestion.py"], "boundaries": ["reconcile"], "affected_checkpoints": ["CP-1"], "proposed_knowledge": [{"state": "CANDIDATE", "text": "Inspect VALUE."}], "confidence": "HIGH", "source": {"kind": "ai", "actor": "provider-neutral-test"}}


def changed(repo: Path) -> Path:
    base = baseline(repo, ["fixture/software.py"])
    path = repo / "baseline.json"; path.write_text(json.dumps(base))
    (repo / "fixture/software.py").write_text("VALUE = 2\n")
    return path


def test_no_packet_fails_closed_and_revalidates(repo: Path):
    result = reconcile(repo, changed(repo), [])
    assert result["classification"] == "CHANGE_WITHOUT_DIAGNOSTIC_IMPACT_METADATA"
    assert result["uncovered_changes"] == ["fixture/software.py"]
    assert result["affected_checkpoints"] == [{"id": "CP-1", "state": "REVALIDATION_REQUIRED"}]


def test_packet_creation_captures_dirty_provenance_and_valid_packet_covers(repo: Path):
    base = changed(repo)
    packet = create_packet(repo, request())
    assert packet["changed_artifacts"][0]["worktree_state"] == "dirty"
    packet_path = repo / "packet.json"; packet_path.write_text(json.dumps(packet))
    canonical_before = (repo / "docs/operations/troubleshooting/checkpoints.json").read_bytes()
    result = reconcile(repo, base, [packet_path])
    assert result["accepted_packets"] == ["TEST-1"] and not result["uncovered_changes"]
    assert result["candidates"][0]["canonical_promotion"] is False
    assert result["candidates"][0]["proposed_knowledge"][0]["text"] == "Inspect VALUE."
    assert (repo / "docs/operations/troubleshooting/checkpoints.json").read_bytes() == canonical_before


def test_untracked_capture(repo: Path):
    (repo / "fixture/new.py").write_text("NEW = True\n")
    req = request(); req["changed_files"] = ["fixture/new.py"]
    assert create_packet(repo, req)["changed_artifacts"][0]["worktree_state"] == "untracked"


@pytest.mark.parametrize("mutation", [
    lambda p: p.update(confidence="CERTAIN"),
    lambda p: p.update(source={"kind": "ai"}),
    lambda p: p.update(affected_checkpoints=["UNKNOWN"]),
    lambda p: p.update(probes=["same", "same"]),
    lambda p: p.update(proposed_knowledge=[{"state": "VALIDATED", "text": "unsafe"}]),
])
def test_invalid_declarations_are_rejected_and_do_not_cover(repo: Path, mutation):
    base = changed(repo); req = request(); mutation(req)
    packet_path = repo / "bad.json"
    try:
        packet_path.write_text(json.dumps(create_packet(repo, req)))
    except PacketError:
        packet_path.write_text(json.dumps(req))
    result = reconcile(repo, base, [packet_path])
    assert result["rejected_packets"] and result["uncovered_changes"] == ["fixture/software.py"]
    assert result["classification"] == "CHANGE_WITHOUT_DIAGNOSTIC_IMPACT_METADATA"


@pytest.mark.parametrize("path", ["../secret", "/etc/passwd", "missing.py"])
def test_path_and_secret_boundary(repo: Path, path: str):
    req = request(); req["changed_files"] = [path]
    with pytest.raises(PacketError): create_packet(repo, req)


def test_malformed_packet_is_rejected(repo: Path):
    base = changed(repo); bad = repo / "bad.json"; bad.write_text("{not json")
    assert reconcile(repo, base, [bad])["uncovered_changes"] == ["fixture/software.py"]


def test_stale_or_contradictory_artifact_identity_is_rejected(repo: Path):
    base = changed(repo); packet = create_packet(repo, request()); packet["changed_artifacts"][0]["sha256"] = "0" * 64
    path = repo / "stale.json"; path.write_text(json.dumps(packet))
    assert reconcile(repo, base, [path])["accepted_packets"] == []


def test_candidate_query_fields_and_bounded_delta_are_deterministic(repo: Path):
    base = changed(repo); packet = create_packet(repo, request()); path = repo / "packet.json"; path.write_text(json.dumps(packet))
    first = reconcile(repo, base, [path]); second = reconcile(repo, base, [path])
    assert first == second
    candidate = first["candidates"][0]
    assert {"implementation_revision", "affected_checkpoints", "probes", "evidence", "local_ai_interpretation_required", "canonical_promotion"} <= candidate.keys()
    delta = local_ai_delta(repo, first)
    assert delta["canonical_knowledge"] == [{"probe": "old canonical probe"}]
    assert "rewrite_canonical_cookbook" in delta["forbidden_actions"]
    assert "candidate_checkpoint_edits" in delta["allowed_outputs"]


def test_clean_capture(repo: Path):
    identity = artifact_identity(repo, "fixture/software.py")
    assert identity["worktree_state"] == "clean"
    assert identity["git_blob"] == identity["head_git_blob"]
