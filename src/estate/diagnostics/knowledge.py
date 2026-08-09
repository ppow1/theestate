"""Fail-closed, provider-neutral operational troubleshooting knowledge."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .living import canonical_json

KNOWLEDGE_SCHEMA = Path("schemas/troubleshooting/operational_knowledge_v1.schema.json")
KNOWLEDGE_CANDIDATE_DIR = Path("operations/diagnostics/candidates/knowledge")
LIFECYCLES = {"RAW_EVIDENCE", "OBSERVATION", "HYPOTHESIS", "CANDIDATE", "VERIFIED", "CANONICAL"}
RECORD_KINDS = {"symptom", "observation", "measurement", "state_transition", "known_good_baseline", "hypothesis", "supporting_evidence", "contradictory_evidence", "disproven_hypothesis", "verified_diagnosis", "unresolved_diagnosis", "diagnostic_probe", "recovery_attempt", "recovery_verification", "explicit_non_action", "risky_action", "stop_condition", "escalation_condition", "evidence_reference"}


class KnowledgeError(ValueError):
    pass


def validate_knowledge(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["knowledge must be an object"]
    required = {"schema_version", "knowledge_id", "title", "lifecycle", "records", "source"}
    allowed = required | {"promotion"}
    errors = [f"missing required field: {x}" for x in sorted(required - payload.keys())]
    errors += [f"unknown field: {x}" for x in sorted(payload.keys() - allowed)]
    if payload.get("schema_version") != "1.0": errors.append("schema_version must be 1.0")
    if not isinstance(payload.get("knowledge_id"), str) or not payload.get("knowledge_id"): errors.append("knowledge_id must be non-empty")
    if not isinstance(payload.get("title"), str) or not payload.get("title"): errors.append("title must be non-empty")
    lifecycle = payload.get("lifecycle")
    if lifecycle not in LIFECYCLES: errors.append("lifecycle is invalid")
    records = payload.get("records")
    if not isinstance(records, list) or not records: errors.append("records must be a non-empty array")
    else:
        ids = [r.get("record_id") for r in records if isinstance(r, dict)]
        if len(ids) != len(set(ids)): errors.append("record_id values must be unique")
        for index, record in enumerate(records):
            if not isinstance(record, dict): errors.append(f"record {index} must be an object"); continue
            required_record = {"record_id", "kind", "statement", "evidence_refs", "confidence", "verification_state"}
            errors += [f"record {index} missing {x}" for x in sorted(required_record - record.keys())]
            if record.get("kind") not in RECORD_KINDS: errors.append(f"record {index} kind is invalid")
            if not isinstance(record.get("statement"), str) or not record.get("statement"): errors.append(f"record {index} statement must be non-empty")
            if not isinstance(record.get("evidence_refs"), list) or not record.get("evidence_refs") or any(not isinstance(x, str) or not x for x in (record.get("evidence_refs") or [])): errors.append(f"record {index} evidence_refs must contain strings")
            if record.get("confidence") not in {"UNKNOWN", "LOW", "MEDIUM", "HIGH"}: errors.append(f"record {index} confidence is invalid")
            if record.get("verification_state") not in {"UNVERIFIED", "SUPPORTED", "CONTRADICTED", "DISPROVEN", "VERIFIED"}: errors.append(f"record {index} verification_state is invalid")
            if record.get("kind") == "recovery_attempt" and record.get("action_outcome") not in {"FAILED", "SUCCEEDED", "NOT_PERFORMED"}: errors.append(f"record {index} recovery attempt requires outcome")
            if record.get("kind") == "recovery_verification" and not record.get("evidence_refs"): errors.append(f"record {index} recovery verification requires evidence")
            if record.get("kind") in {"hypothesis", "unresolved_diagnosis"} and record.get("verification_state") == "VERIFIED": errors.append(f"record {index} unresolved claim cannot be verified")
            if record.get("kind") == "verified_diagnosis" and record.get("verification_state") != "VERIFIED": errors.append(f"record {index} verified diagnosis requires VERIFIED state")
    source = payload.get("source")
    if not isinstance(source, dict) or source.get("kind") not in {"DETERMINISTIC", "LOCAL_AI", "EXTERNAL_AI", "HUMAN", "MIXED"} or not isinstance(source.get("actor"), str) or not source.get("actor") or not isinstance(source.get("evidence_refs"), list) or not source.get("evidence_refs"): errors.append("source provenance is incomplete")
    promotion = payload.get("promotion")
    if lifecycle in {"VERIFIED", "CANONICAL"}:
        if not isinstance(promotion, dict) or promotion.get("decision") not in {"VALIDATED", "PROMOTED"} or not promotion.get("actor") or not promotion.get("evidence_refs"): errors.append("verified knowledge requires governed promotion evidence")
        elif source.get("kind") == "LOCAL_AI": errors.append("local AI cannot self-promote knowledge")
    if lifecycle == "CANONICAL" and (not isinstance(promotion, dict) or promotion.get("decision") != "PROMOTED"): errors.append("canonical knowledge requires PROMOTED decision")
    return errors


def ingest_candidate(root: Path, payload: dict[str, Any]) -> Path:
    errors = validate_knowledge(payload)
    if errors: raise KnowledgeError("invalid operational knowledge: " + "; ".join(errors))
    if payload["lifecycle"] in {"VERIFIED", "CANONICAL"}: raise KnowledgeError("promotion is a governed operation, not candidate ingestion")
    destination = root / KNOWLEDGE_CANDIDATE_DIR / f"{payload['knowledge_id']}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        try:
            existing = json.loads(destination.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise KnowledgeError(f"existing candidate is unreadable: {destination}") from exc
        if existing.get("knowledge") == payload and existing.get("canonical_promotion") is False:
            return destination
        raise KnowledgeError(f"conflicting candidate already exists for knowledge_id: {payload['knowledge_id']}")
    candidate = {"candidate_version": "1.0", "canonical_promotion": False, "knowledge": payload}
    destination.write_text(canonical_json(candidate), encoding="utf-8")
    return destination


def query_knowledge(root: Path, phrase: str | None = None) -> list[dict[str, Any]]:
    result = []
    directory = root / KNOWLEDGE_CANDIDATE_DIR
    for path in sorted(directory.glob("*.json")) if directory.exists() else []:
        try: item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError): continue
        if not phrase or phrase.lower() in canonical_json(item).lower(): result.append(item)
    return result
