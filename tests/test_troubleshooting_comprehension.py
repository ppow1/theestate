from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from estate.diagnostics.comprehension import ComprehensionError, build_model, comprehension_packet, query_model, render_mermaid, validate_model


ROOT = Path(__file__).resolve().parents[1]


def test_three_subsystems_have_revision_grounded_model_and_views(tmp_path: Path):
    model = build_model(ROOT, tmp_path / "comprehension")
    assert {x["component_id"] for x in model["components"]} == {"living_diagnostics", "grace_reasoning_execution", "operations_scheduler"}
    assert len(model["relationships"]) >= 4
    assert len(model["workflows"]) == 3
    assert len(model["checkpoints"]) >= 7
    assert len(model["failure_seams"]) == 3
    assert model["provenance"]["repository_revision"]
    assert model["provenance"]["source_evidence"]["src/estate/diagnostics/living.py"]["sha256"]
    assert "SEAM.GRACE.EVIDENCE_GAP" in render_mermaid(model, "WF.GRACE.EXECUTION")
    packet = comprehension_packet(ROOT, model, "WF.GRACE.EXECUTION")
    assert packet["provider_neutral"] is True
    assert packet["forbidden_actions"] and packet["source_revision"] == model["provenance"]["repository_revision"]
    assert packet["linked_cookbook_knowledge"]
    assert (tmp_path / "comprehension/component-graph.mmd").read_text().startswith("flowchart LR")


def test_model_query_and_staleness_are_deterministic(tmp_path: Path):
    output = tmp_path / "model"
    first = build_model(ROOT, output)
    second = build_model(ROOT, output)
    assert first["provenance"]["source_evidence"] == second["provenance"]["source_evidence"]
    assert second["staleness"] == {"state": "CURRENT", "changed_sources": [], "revalidation_required": False}
    assert query_model(second, "evidence")


def test_controlled_source_change_requires_revalidation(tmp_path: Path):
    model_path = ROOT / "docs/operations/troubleshooting/comprehension.json"
    authored = json.loads(model_path.read_text(encoding="utf-8"))
    source_paths = set()
    for key in ("components", "workflows", "checkpoints"):
        for item in authored[key]: source_paths.update(item.get("source_paths", []))
    for item in authored["relationships"] + authored["failure_seams"]: source_paths.update(item.get("evidence_refs", []))
    sandbox = tmp_path / "estate"
    for relative in {"docs/operations/troubleshooting/comprehension.json", *source_paths}:
        destination = sandbox / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    output = sandbox / "out"
    first = build_model(sandbox, output)
    assert first["staleness"]["state"] == "CURRENT"
    target = sandbox / "src/estate/diagnostics/living.py"
    target.write_text(target.read_text(encoding="utf-8") + "\n# controlled source-change simulation\n", encoding="utf-8")
    second = build_model(sandbox, output)
    assert second["staleness"]["state"] == "REVALIDATION_REQUIRED"
    assert "src/estate/diagnostics/living.py" in second["staleness"]["changed_sources"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda model: model["components"][0].update({"component_id": ""}),
        lambda model: model["relationships"][0].update({"target": "missing"}),
        lambda model: model["checkpoints"][0].update({"source_paths": ["../secret"]}),
        lambda model: model["failure_seams"][0].update({"workflow_id": "missing"}),
    ],
)
def test_invalid_model_fails_closed(tmp_path: Path, mutation):
    model = json.loads((ROOT / "docs/operations/troubleshooting/comprehension.json").read_text(encoding="utf-8"))
    mutation(model)
    assert validate_model(ROOT, model)


def test_unknown_packet_scope_fails_closed(tmp_path: Path):
    model = build_model(ROOT)
    with pytest.raises(ComprehensionError, match="unknown comprehension scope"):
        comprehension_packet(ROOT, model, "not-a-scope")
