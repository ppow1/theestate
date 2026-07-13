import json
from pathlib import Path
import pytest
from estate.core import provider_benchmark as pb


def test_schema_fixture_and_versioning():
    spec = pb.BenchmarkSpec(pb.benchmark001_spec())
    spec.validate()
    assert spec.benchmark_id == "benchmark-001"
    bad = dict(pb.benchmark001_spec()); bad.pop("required_metrics")
    with pytest.raises(pb.BenchmarkError): pb.BenchmarkSpec(bad).validate()


def test_ollama_discovery_and_missing_model(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "BENCH_ROOT", tmp_path)
    spec = pb.BenchmarkSpec(pb.benchmark001_spec())
    ws = pb.WorkspaceManager("benchmark-001", "run-missing"); ws.create(spec)
    adapter = pb.OllamaAdapter()
    monkeypatch.setattr(adapter, "discover", lambda: {"available": True, "provider": "ollama", "models": ["other:1"], "source": "test"})
    meta = adapter.run(spec, ws, model="qwen2.5-coder:7b")
    assert meta["validation_status"] == "failed_provider"
    assert meta["failure_classification"] == "ProviderUnavailable"


def test_mock_ollama_metrics_validation_and_compare(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "BENCH_ROOT", tmp_path)
    spec = pb.BenchmarkSpec(pb.benchmark001_spec())
    ws = pb.WorkspaceManager("benchmark-001", "run-ok"); ws.create(spec)
    meta = pb.OllamaAdapter().run(spec, ws, mock=True)
    assert meta["model"] == "qwen2.5-coder:7b"
    assert meta["prompt_tokens"] == 120
    v = pb.ValidationRunner().validate(spec, ws, "local", hidden=True)
    assert v["validation_status"] == "passed"
    report = pb.compare(spec, ws)
    assert report["results"][0]["aggregate_score"] == 100


def test_import_adapters_and_path_traversal(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "BENCH_ROOT", tmp_path)
    src = tmp_path / "src"; src.mkdir(); (src / "dependency_batcher.py").write_text(pb.mock_benchmark001_code())
    spec = pb.BenchmarkSpec(pb.benchmark001_spec())
    ws = pb.WorkspaceManager("benchmark-001", "run-import"); ws.create(spec)
    codex = pb.ImportAdapter("codex", "codex").run(spec, ws, str(src), seat_reference="seat:codex-business-1", model="codex")
    ref = pb.ImportAdapter("chief_architect", "manual_reference").run(spec, ws, str(src))
    assert codex["estate_seat_reference"] == "seat:codex-business-1"
    assert ref["files_produced"] == ["dependency_batcher.py"]
    with pytest.raises(pb.IsolationError): pb.safe_join(ws.executor_dir("local"), "..", "codex", "metadata.json")


def test_repeat_runs_do_not_overwrite_and_atomic_metadata(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "BENCH_ROOT", tmp_path)
    spec = pb.BenchmarkSpec(pb.benchmark001_spec())
    ws = pb.WorkspaceManager("benchmark-001", "same"); ws.create(spec)
    with pytest.raises(pb.BenchmarkError): pb.WorkspaceManager("benchmark-001", "same").create(spec)
    pb.atomic_write_json(ws.executor_dir("local") / "metadata.json", {"ok": True})
    assert json.loads((ws.executor_dir("local") / "metadata.json").read_text())["ok"] is True


def test_canonical_packet_identical_for_codex_ollama_and_reference(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "BENCH_ROOT", tmp_path)
    spec = pb.BenchmarkSpec(pb.benchmark001_spec())
    ws = pb.WorkspaceManager("benchmark-001", "run-packet"); ws.create(spec)
    packet = pb.canonical_packet_text(spec)
    assert "## Public specification" in packet
    assert "## Exact task schema" in packet
    assert "## Function signature" in packet
    assert "## Scheduling rules" in packet
    assert "## Validation rules" in packet
    assert "## CLI contract" in packet
    assert "## Dependency constraints" in packet
    assert "## Required files" in packet
    assert "## Visible tests" in packet
    assert "## Isolation rules" in packet
    assert "## Acceptance criteria" in packet
    assert "Hidden-review tests" in packet
    assert pb.build_assignment_prompt(spec) == packet
    local = pb.OllamaAdapter().run(spec, ws, mock=True)
    src = tmp_path / "src"; src.mkdir(); (src / "dependency_batcher.py").write_text(pb.mock_benchmark001_code())
    codex = pb.ImportAdapter("codex", "codex").run(spec, ws, str(src))
    ref = pb.ImportAdapter("chief_architect", "manual_reference").run(spec, ws, str(src))
    expected = pb.canonical_packet_hash(spec)
    assert {local["canonical_packet_sha256"], codex["canonical_packet_sha256"], ref["canonical_packet_sha256"]} == {expected}
    assert json.loads((ws.executor_dir("local") / "raw_request.json").read_text())["prompt"] == packet


def test_abbreviated_or_altered_packets_rejected_from_fair_compare(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "BENCH_ROOT", tmp_path)
    spec = pb.BenchmarkSpec(pb.benchmark001_spec())
    ws = pb.WorkspaceManager("benchmark-001", "run-mismatch"); ws.create(spec)
    src = tmp_path / "src"; src.mkdir(); (src / "dependency_batcher.py").write_text(pb.mock_benchmark001_code())
    pb.ImportAdapter("codex", "codex").run(spec, ws, str(src))
    meta_path = ws.executor_dir("codex") / "metadata.json"
    meta = json.loads(meta_path.read_text())
    meta["canonical_packet_sha256"] = pb.sha256_text("abbreviated prompt")
    meta["canonical_packet_eligible"] = False
    pb.atomic_write_json(meta_path, meta)
    report = pb.compare(spec, ws)
    assert report["comparison_status"] == "refused_mismatched_packet_hashes"
    assert report["results"][0]["fair_comparison_eligible"] is False
    assert report["results"][0]["aggregate_score"] == 0


def test_prior_pilot_evidence_manifest_preserved():
    manifest = Path("experiments/provider_benchmarks/benchmark-001/pilot_evidence/abbreviated_prompt_pilot_ineligible.json")
    data = json.loads(manifest.read_text())
    assert data["status"] == "preserved_ineligible_for_provider_ranking"
    for run in data["preserved_runs"]:
        assert Path(run).exists()


def test_reruns_create_new_run_ids(monkeypatch, tmp_path):
    monkeypatch.setattr(pb, "BENCH_ROOT", tmp_path)
    first = pb.WorkspaceManager("benchmark-001").run_id
    second = pb.WorkspaceManager("benchmark-001").run_id
    assert first != second
