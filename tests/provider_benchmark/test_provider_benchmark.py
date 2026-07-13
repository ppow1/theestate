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
