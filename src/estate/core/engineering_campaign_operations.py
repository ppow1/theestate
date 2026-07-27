"""WP-4228 production composition for governed Engineering campaign actions.

This module composes existing institutional authorities; it is deliberately not a
scheduler, provider runner, worker registry, or Dispatch implementation.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "engineering_campaign_operations.v1"
DECISIONS = {"accepted", "accepted_with_conditions", "deferred", "rejected", "superseded", "expired", "withdrawn", "requires_more_evidence"}
ACTIONS = {
    "create_Grace_operational_objective", "create_Engineering_internal_work_item",
    "create_Helen_capability_development_request", "request_Steward_decision",
    "create_validation_task", "create_Git_readiness_task", "create_review_task",
    "defer_until_condition", "no_action_advisory_only",
}
AUTHORITIES = {"Grace", "Helen", "Engineering", "Steward"}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


def stable_id(kind: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:24]
    return f"{kind}-{digest}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class CampaignOperationError(ValueError):
    """A fail-closed campaign validation error."""


@dataclass
class CampaignStore:
    """Append-only JSONL store with deterministic idempotency indexes."""

    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.ledger = self.root / "record_chain.jsonl"

    def records(self) -> list[dict[str, Any]]:
        if not self.ledger.exists():
            return []
        return [json.loads(line) for line in self.ledger.read_text(encoding="utf-8").splitlines() if line.strip()]

    def append(self, record: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        for existing in self.records():
            if existing["idempotency_key"] == idempotency_key:
                return existing
        records = self.records()
        envelope = {
            **record,
            "schema_version": SCHEMA_VERSION,
            "recorded_at": record.get("recorded_at", _now()),
            "idempotency_key": idempotency_key,
            "previous_record_hash": records[-1]["record_hash"] if records else None,
        }
        envelope["record_hash"] = content_hash(envelope)
        with self.ledger.open("a", encoding="utf-8") as handle:
            handle.write(_canonical(envelope) + "\n")
        return envelope

    def verify(self) -> bool:
        previous = None
        for record in self.records():
            claimed = record["record_hash"]
            unsigned = {k: v for k, v in record.items() if k != "record_hash"}
            if record["previous_record_hash"] != previous or content_hash(unsigned) != claimed:
                return False
            previous = claimed
        return True


class EngineeringCampaignOperations:
    """Governed recommendation-to-action coordinator.

    Fixture execution is explicit and can only follow Engineering authorization.
    No external process, network, shell, Git mutation, or provider is invoked.
    """

    def __init__(self, store: CampaignStore):
        self.store = store

    def reconcile(self, sources: list[dict[str, Any]]) -> dict[str, Any]:
        normalized = sorted(sources, key=lambda x: (x.get("canonical_id", ""), x.get("record_id", "")))
        snapshot = {
            "record_type": "EngineeringQueueSnapshot",
            "record_id": stable_id("queue", content_hash(normalized)),
            "correlation_id": stable_id("campaign", content_hash(normalized)),
            "sources": normalized,
            "source_hash": content_hash(normalized),
            "provenance": [{"classification": x.get("source_class", "authoritative"), "record_id": x.get("record_id")} for x in normalized],
        }
        return self.store.append(snapshot, f"reconcile:{snapshot['source_hash']}")

    def recommend(self, snapshot: dict[str, Any], action_classification: str = "create_Grace_operational_objective") -> dict[str, Any]:
        if snapshot.get("record_type") != "EngineeringQueueSnapshot":
            raise CampaignOperationError("unsupported queue snapshot")
        if action_classification not in ACTIONS:
            raise CampaignOperationError("unknown action classification")
        evidence = snapshot["source_hash"]
        completeness = 1.0 if snapshot["sources"] else 0.4
        confidence = "high" if completeness >= .8 else "low"
        basis = {"snapshot_id": snapshot["record_id"], "evidence_hash": evidence, "action_classification": action_classification}
        recommendation = {
            "record_type": "EngineeringRecommendation",
            "record_id": stable_id("recommendation", content_hash(basis)),
            "correlation_id": snapshot["correlation_id"],
            "state": "presented",
            "content": "Advance the highest-priority eligible Engineering work through governed action.",
            "action_classification": action_classification,
            "confidence": {"level": confidence, "evidence_completeness": completeness, "missing_provider_flags": [] if snapshot["sources"] else ["authoritative_queue"], "stale_evidence_flags": [], "conflicting_evidence_flags": [], "evidence_references": [snapshot["record_id"]], "evidence_hash": evidence},
            "content_hash": content_hash(basis),
        }
        return self.store.append(recommendation, f"recommend:{recommendation['content_hash']}")

    def decide(self, recommendation: dict[str, Any], disposition: str, authority: str, rationale: str, conditions: list[str] | None = None) -> dict[str, Any]:
        if disposition not in DECISIONS or authority not in AUTHORITIES:
            raise CampaignOperationError("unknown decision or authority")
        if recommendation.get("record_type") != "EngineeringRecommendation":
            raise CampaignOperationError("recommendation is unavailable")
        if disposition.startswith("accepted") and recommendation["confidence"]["level"] == "low":
            raise CampaignOperationError("low-confidence recommendation requires more evidence")
        conditions = conditions or []
        if disposition == "accepted_with_conditions" and not conditions:
            raise CampaignOperationError("accepted_with_conditions requires explicit conditions")
        decision = {
            "record_type": "RecommendationDecision",
            "record_id": stable_id("decision", recommendation["record_id"], disposition, authority),
            "correlation_id": recommendation["correlation_id"], "recommendation_id": recommendation["record_id"],
            "recommendation_content_hash": recommendation["content_hash"], "disposition": disposition,
            "decision_authority": authority, "rationale": rationale, "conditions": conditions,
            "resulting_action_disposition": "eligible_for_translation" if disposition.startswith("accepted") else "no_action",
        }
        return self.store.append(decision, f"decision:{decision['record_id']}")

    def translate(self, recommendation: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
        if not decision.get("disposition", "").startswith("accepted"):
            raise CampaignOperationError("only accepted decisions may translate")
        if decision.get("recommendation_content_hash") != recommendation.get("content_hash"):
            raise CampaignOperationError("recommendation content changed")
        action = recommendation["action_classification"]
        kind = {"create_Grace_operational_objective": "GraceOperationalObjective", "create_Engineering_internal_work_item": "EngineeringWorkItem", "create_Helen_capability_development_request": "CapabilityDevelopmentRequest"}.get(action, "RecommendationActionTranslation")
        translation_id = stable_id("translation", decision["record_id"], action)
        translated = {"record_type": "RecommendationActionTranslation", "record_id": translation_id, "correlation_id": recommendation["correlation_id"], "state": "translated", "action_classification": action, "decision_id": decision["record_id"], "created_record": {"record_type": kind, "record_id": stable_id(kind.lower(), translation_id), "state": "proposed"}}
        return self.store.append(translated, f"translate:{decision['record_id']}")

    def fixture_execute(self, translation: dict[str, Any]) -> list[dict[str, Any]]:
        """Produce the bounded authority chain; never invoke a real provider."""
        if translation.get("state") != "translated" or translation["action_classification"] not in {"create_Grace_operational_objective", "create_Engineering_internal_work_item"}:
            raise CampaignOperationError("translation is not executable")
        correlation = translation["correlation_id"]
        types = ["CapabilityVerificationRequest", "HelenCapabilityDetermination", "EngineeringCommission", "EngineeringExecutionPlan", "EngineeringExecutionAuthorization", "DispatchExecutionRecord", "EngineeringValidationRecord", "EngineeringCompletion"]
        if translation["action_classification"] == "create_Grace_operational_objective":
            types.append("GraceCompletionReceipt")
        output = []
        previous = translation["record_id"]
        for kind in types:
            state = "completed"
            record = {"record_type": kind, "record_id": stable_id(kind.lower(), correlation), "correlation_id": correlation, "state": state, "authority_record_id": previous, "fixture": True, "provider_invoked": False}
            output.append(self.store.append(record, f"fixture:{kind}:{correlation}"))
            previous = output[-1]["record_id"]
        return output

    def inspect(self) -> dict[str, Any]:
        records = self.store.records()
        return {"schema_version": SCHEMA_VERSION, "read_only": True, "ledger_valid": self.store.verify(), "record_count": len(records), "records": records}

