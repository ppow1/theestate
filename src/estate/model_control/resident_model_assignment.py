"""Staged local model assignment and failover for WP-4026.

This module is intentionally uninstalled. It provides deterministic,
resident-aware model selection semantics for WP-4031 to integrate with the
Estate model-control authority after conflict review. It does not create a
second active registry, call cloud providers, or download models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

LOCAL_PROVIDER_TYPES = {"local", "lan_local"}
UNAVAILABLE_STATES = {"missing", "unavailable", "offline", "prohibited", "timeout"}
COLD_START_STATES = {"cold", "starting"}
READY_STATES = {"ready", "warm"}


@dataclass(frozen=True)
class ModelCandidate:
    provider_id: str
    model_id: str
    capabilities: tuple[str, ...]
    provider_type: str = "local"
    priority: int = 100
    cold_start_seconds: float = 0.0
    timeout_seconds: float = 30.0
    allow_residents: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.provider_id}:{self.model_id}"


@dataclass(frozen=True)
class Availability:
    provider_id: str
    model_id: str
    state: str
    detail: str = ""
    inspected_at: str | None = None
    latency_ms: int | None = None

    @property
    def key(self) -> str:
        return f"{self.provider_id}:{self.model_id}"


class LocalModelAssignmentEngine:
    """Deterministic resident/capability selector with explicit failover.

    The engine consumes staged candidate records and externally supplied health
    inspection snapshots. It never probes providers directly; integration code
    must provide availability facts from the authorized model-control layer.
    """

    def __init__(
        self,
        candidates: Iterable[ModelCandidate],
        *,
        resident_assignments: dict[str, list[str]] | None = None,
        capability_assignments: dict[str, list[str]] | None = None,
        prohibited_provider_types: Iterable[str] = ("cloud", "hosted"),
        no_cloud: bool = True,
        now: str | None = None,
    ) -> None:
        self.candidates = {candidate.key: candidate for candidate in candidates}
        self.resident_assignments = resident_assignments or {}
        self.capability_assignments = capability_assignments or {}
        self.prohibited_provider_types = set(prohibited_provider_types)
        self.no_cloud = no_cloud
        self.now = now
        self.audit_log: list[dict[str, Any]] = []
        self.evaluations: list[dict[str, Any]] = []

    def inspect(self, availability: Iterable[Availability]) -> dict[str, dict[str, Any]]:
        facts = {item.key: item for item in availability}
        rows: dict[str, dict[str, Any]] = {}
        for key, candidate in sorted(self.candidates.items(), key=lambda item: (item[1].priority, item[0])):
            fact = facts.get(key)
            if candidate.provider_type in self.prohibited_provider_types or (self.no_cloud and candidate.provider_type not in LOCAL_PROVIDER_TYPES):
                state = "prohibited"
                detail = "provider boundary prohibits selection"
            elif fact is None:
                state = "unknown"
                detail = "no model-control availability inspection supplied"
            else:
                state = fact.state
                detail = fact.detail
            rows[key] = {
                "provider_id": candidate.provider_id,
                "model_id": candidate.model_id,
                "provider_type": candidate.provider_type,
                "capabilities": list(candidate.capabilities),
                "state": state,
                "detail": detail,
                "cold_start_seconds": candidate.cold_start_seconds,
                "timeout_seconds": candidate.timeout_seconds,
                "latency_ms": fact.latency_ms if fact else None,
                "inspected_at": fact.inspected_at if fact else None,
            }
        return rows

    def select(self, resident_id: str, capability: str, availability: Iterable[Availability]) -> dict[str, Any]:
        diagnostics = self.inspect(availability)
        fallback_order = self._fallback_order(resident_id, capability)
        considered = []
        selection = None
        for key in fallback_order:
            candidate = self.candidates.get(key)
            row = diagnostics.get(key)
            if not candidate or not row:
                considered.append({"key": key, "selected": False, "reason": "assignment references unknown candidate"})
                continue
            reason = self._rejection_reason(candidate, resident_id, capability, row)
            selected_here = reason is None and selection is None
            considered.append({"key": key, "selected": selected_here, "state": row["state"], "reason": reason or ("selected" if selected_here else "not selected; earlier candidate selected")})
            if selected_here:
                selection = candidate
        result = {
            "resident_id": resident_id,
            "capability": capability,
            "selected": selection.key if selection else None,
            "fallback_order": fallback_order,
            "considered": considered,
            "diagnostics": diagnostics,
            "selected_at": self._timestamp(),
        }
        self.audit_log.append({"event": "model_selected" if selection else "model_unavailable", **result})
        return result

    def record_evaluation(self, resident_id: str, capability: str, candidate_key: str, *, score: float, notes: str, evaluator: str) -> dict[str, Any]:
        if candidate_key not in self.candidates:
            raise KeyError(candidate_key)
        record = {
            "resident_id": resident_id,
            "capability": capability,
            "candidate_key": candidate_key,
            "score": float(score),
            "notes": notes,
            "evaluator": evaluator,
            "self_authorizing": False,
            "recorded_at": self._timestamp(),
        }
        self.evaluations.append(record)
        self.audit_log.append({"event": "evaluation_recorded", **record})
        return record

    def _fallback_order(self, resident_id: str, capability: str) -> list[str]:
        ordered = []
        for source in (self.resident_assignments.get(resident_id, []), self.capability_assignments.get(capability, [])):
            for key in source:
                if key not in ordered:
                    ordered.append(key)
        for key, candidate in sorted(self.candidates.items(), key=lambda item: (item[1].priority, item[0])):
            if capability in candidate.capabilities and key not in ordered:
                ordered.append(key)
        return ordered

    def _rejection_reason(self, candidate: ModelCandidate, resident_id: str, capability: str, row: dict[str, Any]) -> str | None:
        if capability not in candidate.capabilities:
            return "capability not supported"
        if candidate.allow_residents and resident_id not in candidate.allow_residents:
            return "resident not allowed for candidate"
        if row["state"] in UNAVAILABLE_STATES:
            return f"state is {row['state']}"
        if row["state"] in COLD_START_STATES:
            return f"state is {row['state']}; cold start not complete"
        if row["state"] not in READY_STATES:
            return f"state is {row['state']}; availability not confirmed"
        if candidate.timeout_seconds <= 0:
            return "timeout policy prohibits request"
        return None

    def _timestamp(self) -> str:
        return self.now or datetime.now(timezone.utc).isoformat()
