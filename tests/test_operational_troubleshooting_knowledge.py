import copy
import json
from pathlib import Path

import pytest

from estate.diagnostics.knowledge import KnowledgeError, ingest_candidate, query_knowledge, validate_knowledge

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "operations/diagnostics/candidates/knowledge/PL0040-GPU-DUAL-INCIDENT.json"

def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["knowledge"]

def test_gpu_fixture_preserves_layers_actions_and_provenance():
    item = payload()
    assert validate_knowledge(item) == []
    kinds = {record["kind"] for record in item["records"]}
    assert {"symptom", "observation", "known_good_baseline", "hypothesis", "contradictory_evidence", "unresolved_diagnosis", "recovery_attempt", "recovery_verification", "explicit_non_action"} <= kinds
    outcomes = {record.get("action_outcome") for record in item["records"]}
    assert {"FAILED", "SUCCEEDED"} <= outcomes
    assert any("C:/Windows/MEMORY.DMP" in ref for record in item["records"] for ref in record["evidence_refs"])
    assert any("WinError 1224" in record["statement"] for record in item["records"])

@pytest.mark.parametrize("mutation", [
    lambda value: value.update(extra=True),
    lambda value: value.update(lifecycle="VERIFIED"),
    lambda value: value["records"][0].update(kind="made_up"),
    lambda value: value["records"][0].update(evidence_refs=[]),
    lambda value: value["records"][0].update(verification_state="VERIFIED", kind="hypothesis"),
])
def test_malformed_or_unsafe_knowledge_fails_closed(mutation):
    value = copy.deepcopy(payload())
    mutation(value)
    assert validate_knowledge(value)

def test_local_ai_cannot_self_promote():
    value = copy.deepcopy(payload())
    value["source"] = {"kind": "LOCAL_AI", "actor": "local-model", "evidence_refs": ["review"]}
    value["lifecycle"] = "VERIFIED"
    value["promotion"] = {"actor": "local-model", "evidence_refs": ["review"], "decision": "VALIDATED"}
    assert any("self-promote" in error for error in validate_knowledge(value))

def test_candidate_ingestion_never_promotes_or_mutates_canonical(tmp_path):
    value = payload()
    path = ingest_candidate(tmp_path, value)
    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored["canonical_promotion"] is False
    assert not (tmp_path / "docs/operations/troubleshooting/cookbook.json").exists()
    assert query_knowledge(tmp_path, "cold electrical")
    promoted = copy.deepcopy(value)
    promoted["lifecycle"] = "CANONICAL"
    promoted["promotion"] = {"actor": "local-model", "evidence_refs": ["review"], "decision": "PROMOTED"}
    with pytest.raises(KnowledgeError): ingest_candidate(tmp_path, promoted)
