"""Deterministic, append-only records over published WP-4223 output."""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

LEDGER_VERSION = "estate.engineering-recommendation-ledger/v1"
RECOMMENDATION_VERSION = "estate.engineering-recommendation-record/v1"
DECISION_VERSION = "estate.engineering-review-decision/v1"
AUDIT_VERSION = "estate.engineering-recommendation-audit/v1"
SOURCE_VERSION = "estate.engineering-campaign-recommendations/v1"
STATES = {"generated", "presented", "acknowledged", "accepted_for_future_planning", "deferred", "rejected", "superseded", "expired"}
UNRESOLVED = {"generated", "presented", "acknowledged", "deferred"}


class LedgerError(ValueError):
    """A published input or ledger violates its versioned contract."""


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _hashed(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["deterministic_content_hash"] = digest(result)
    return result


def _records(published: dict[str, Any]) -> list[dict[str, Any]]:
    sets = published.get("recommendation_sets")
    if not isinstance(sets, dict):
        raise LedgerError("recommendation_sets must be an object")
    rows = [row for category in sorted(sets) for row in sets[category] if isinstance(row, dict)]
    if any(not isinstance(sets[k], list) for k in sets):
        raise LedgerError("recommendation sets must be arrays")
    return rows


def create_ledger(published: dict[str, Any], *, generated_at: str | None = None) -> dict[str, Any]:
    """Capture WP-4223 output without changing it or independently recommending."""
    if not isinstance(published, dict) or published.get("recommendation_schema_version") != SOURCE_VERSION:
        raise LedgerError("unsupported recommendation_schema_version")
    source_hash = published.get("deterministic_content_hash")
    if not isinstance(source_hash, str):
        raise LedgerError("published deterministic_content_hash is required")
    timestamp = generated_at or "unspecified"
    seen: set[str] = set()
    recommendations = []
    for source in _records(published):
        identifier = source.get("recommendation_id")
        if not isinstance(identifier, str):
            raise LedgerError("recommendation_id is required")
        if identifier in seen:
            raise LedgerError(f"duplicate recommendation_id: {identifier}")
        seen.add(identifier)
        provenance = source.get("provenance", {})
        record = {
            "recommendation_schema_version": RECOMMENDATION_VERSION,
            "recommendation_identifier": identifier,
            "recommendation_version": published.get("policy_version", "unspecified"),
            "category": source.get("category"), "score": source.get("score"),
            "explanation": source.get("reason"), "supporting_evidence": source.get("score_components", []),
            "source_snapshot_identifier": provenance.get("snapshot_identifier"),
            "queue_generation_identifier": provenance.get("queue_generation_identifier"),
            "dashboard_snapshot_identifier": provenance.get("snapshot_identifier"),
            "generation_timestamp": timestamp, "provenance": provenance,
            "source_recommendation_hash": digest(source), "initial_state": "generated",
        }
        recommendations.append(_hashed(record))
    logical = {
        "ledger_schema_version": LEDGER_VERSION, "advisory_only": True, "authority": "none",
        "source_recommendations_hash": source_hash,
        "recommendations": sorted(recommendations, key=lambda r: r["recommendation_identifier"]),
        "decisions": [], "audit_records": [],
    }
    return _hashed(logical)


def append_decision(ledger: dict[str, Any], *, recommendation_id: str, state: str, reviewer: str,
                    review_timestamp: str, rationale: str, comments: str = "",
                    linked_snapshot: str | None = None, linked_work_packages: list[str] | None = None,
                    linked_validation_evidence: list[str] | None = None) -> dict[str, Any]:
    """Return a new ledger; the supplied ledger and all historical entries remain untouched."""
    validate_ledger(ledger)
    if state not in STATES - {"generated"}: raise LedgerError(f"unsupported review state: {state}")
    if recommendation_id not in {r["recommendation_identifier"] for r in ledger["recommendations"]}:
        raise LedgerError(f"unknown recommendation: {recommendation_id}")
    previous_hash = ledger["decisions"][-1]["deterministic_content_hash"] if ledger["decisions"] else None
    decision = _hashed({
        "decision_schema_version": DECISION_VERSION,
        "decision_identifier": f"decision:{len(ledger['decisions']) + 1:06d}",
        "linked_recommendation": recommendation_id, "state": state, "reviewer": reviewer,
        "review_timestamp": review_timestamp, "rationale": rationale, "comments": comments,
        "linked_snapshot": linked_snapshot, "linked_work_packages": sorted(linked_work_packages or []),
        "linked_validation_evidence": sorted(linked_validation_evidence or []), "previous_decision_hash": previous_hash,
    })
    result = copy.deepcopy(ledger)
    result.pop("deterministic_content_hash", None)
    result["decisions"].append(decision)
    audit = _hashed({"audit_schema_version": AUDIT_VERSION, "sequence": len(result["audit_records"]) + 1,
                     "event": "review_state_appended", "record_hash": decision["deterministic_content_hash"],
                     "previous_audit_hash": result["audit_records"][-1]["deterministic_content_hash"] if result["audit_records"] else None})
    result["audit_records"].append(audit)
    return _hashed(result)


def _without_hash(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value); result.pop("deterministic_content_hash", None); return result


def validate_ledger(ledger: Any) -> list[str]:
    if not isinstance(ledger, dict) or ledger.get("ledger_schema_version") != LEDGER_VERSION:
        raise LedgerError("unsupported ledger_schema_version")
    if ledger.get("deterministic_content_hash") != digest(_without_hash(ledger)):
        raise LedgerError("ledger deterministic_content_hash mismatch")
    ids = [r.get("recommendation_identifier") for r in ledger.get("recommendations", [])]
    if len(ids) != len(set(ids)): raise LedgerError("duplicate recommendation identifiers")
    for collection in ("recommendations", "decisions", "audit_records"):
        for record in ledger.get(collection, []):
            if record.get("deterministic_content_hash") != digest(_without_hash(record)):
                raise LedgerError(f"{collection} record hash mismatch")
    previous = None
    for decision in ledger.get("decisions", []):
        if decision.get("previous_decision_hash") != previous: raise LedgerError("decision chain mismatch")
        previous = decision["deterministic_content_hash"]
    previous = None
    for index, audit in enumerate(ledger.get("audit_records", []), 1):
        if audit.get("sequence") != index or audit.get("previous_audit_hash") != previous: raise LedgerError("audit chain mismatch")
        previous = audit["deterministic_content_hash"]
    return []


def _state(ledger: dict[str, Any], identifier: str) -> str:
    values = [d["state"] for d in ledger["decisions"] if d["linked_recommendation"] == identifier]
    return values[-1] if values else "generated"


def query(ledger: dict[str, Any], view: str, recommendation_id: str | None = None) -> Any:
    """Read-only views; returns deep copies so callers cannot mutate ledger state."""
    validate_ledger(ledger)
    records = ledger["recommendations"]
    if recommendation_id:
        records = [r for r in records if r["recommendation_identifier"] == recommendation_id]
    if view in {"current", "historical"}: result = records
    elif view == "history": result = [d for d in ledger["decisions"] if not recommendation_id or d["linked_recommendation"] == recommendation_id]
    elif view == "decisions": result = ledger["decisions"]
    elif view == "unresolved": result = [r for r in records if _state(ledger, r["recommendation_identifier"]) in UNRESOLVED]
    elif view == "expired": result = [r for r in records if _state(ledger, r["recommendation_identifier"]) == "expired"]
    elif view == "superseded": result = [r for r in records if _state(ledger, r["recommendation_identifier"]) == "superseded"]
    elif view == "lineage":
        result = [{"recommendation_identifier": r["recommendation_identifier"], "source_recommendation_hash": r["source_recommendation_hash"],
                   "decision_hashes": [d["deterministic_content_hash"] for d in ledger["decisions"] if d["linked_recommendation"] == r["recommendation_identifier"]]} for r in records]
    elif view == "trends":
        result = {state: sum(_state(ledger, r["recommendation_identifier"]) == state for r in records) for state in sorted(STATES)}
    else: raise LedgerError(f"unknown query: {view}")
    return copy.deepcopy(result)
