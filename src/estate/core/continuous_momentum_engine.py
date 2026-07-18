"""Bounded Continuous Momentum Engine over canonical projections and adapters."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

SCHEMA_VERSION = "estate.continuous-momentum-cycle.v1"
MODES = {"simulation", "dry_run", "live"}
PERMISSIONS = {"recommendation", "preauthorized", "delegated", "protected", "prohibited"}
STAGES = ("observe", "reconcile", "classify", "propose", "authorize", "act", "verify", "record")


def _time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def run_momentum_cycle(
    *, cycle_id: str, observed_at: str, inputs: dict[str, Any],
    candidates: Iterable[dict[str, Any]], mode: str = "dry_run",
    prior_action_keys: Iterable[str] = (), cooldown_seconds: int = 300,
    last_action_at: str | None = None,
    action_adapter: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run one reproducible cycle; only a supplied canonical adapter may act."""
    copied_inputs = deepcopy(inputs)
    copied_candidates = [deepcopy(item) for item in candidates]
    prior_keys = sorted(set(prior_action_keys))
    now = _time(observed_at)
    if not cycle_id or now is None or mode not in MODES or cooldown_seconds < 0:
        raise ValueError("cycle identity, timestamp, mode, and cooldown must be valid")
    warnings: list[str] = []
    holds: list[str] = []
    references: set[str] = set()
    for name, projection in sorted(copied_inputs.items()):
        refs = projection.get("evidence_references") or projection.get("canonical_evidence_references") or []
        references.update(str(ref) for ref in refs if ref)
        if projection.get("authorizes_action") is not False:
            holds.append(f"{name}: input projection does not explicitly deny authority")
        if projection.get("stale") or projection.get("state") in {"stale", "indeterminate", "contradictory"}:
            holds.append(f"{name}: evidence is stale or indeterminate")
        if projection.get("warnings"):
            warnings.extend(f"{name}: {warning}" for warning in projection["warnings"])
        if projection.get("protected_decision"):
            holds.append(f"{name}: protected decision required")
    if not copied_inputs:
        holds.append("no canonical input projections supplied")

    normalized: list[dict[str, Any]] = []
    for candidate in copied_candidates:
        permission = str(candidate.get("permission") or "").strip()
        key = str(candidate.get("idempotency_key") or "").strip()
        refs = sorted({str(ref) for ref in candidate.get("source_refs") or [] if ref})
        problems: list[str] = []
        if permission not in PERMISSIONS:
            problems.append("unknown permission classification")
        if not candidate.get("action_id") or not key or not refs or not candidate.get("canonical_mechanism"):
            problems.append("candidate lacks identity, idempotency, source evidence, or canonical mechanism")
        if permission in {"preauthorized", "delegated"} and not candidate.get("authority_refs"):
            problems.append("actionable candidate lacks explicit authority evidence")
        if permission in {"protected", "prohibited"}:
            problems.append("candidate is protected or prohibited")
        if key in prior_keys:
            problems.append("duplicate idempotency key")
        references.update(refs)
        normalized.append({
            **candidate,
            "permission": permission,
            "idempotency_key": key,
            "source_refs": refs,
            "priority": int(candidate.get("priority", 0)),
            "authorization_problems": problems,
            "eligible": not problems and permission in {"recommendation", "preauthorized", "delegated"},
        })
    normalized.sort(key=lambda item: (-item["priority"], str(item.get("action_id"))))

    last = _time(last_action_at)
    cooldown_active = bool(last and (now - last).total_seconds() < cooldown_seconds)
    if cooldown_active:
        holds.append("cycle cooldown has not elapsed")
    selected = next((item for item in normalized if item["eligible"]), None)
    disposition = "safe_idle"
    proposed = None
    result = None
    executed = False
    if holds:
        disposition = "escalate" if any("protected" in hold or "indeterminate" in hold for hold in holds) else "safe_idle"
    elif selected:
        proposed = selected
        if selected["permission"] == "recommendation":
            disposition = "recommend"
        elif mode in {"simulation", "dry_run"}:
            disposition = "simulate" if mode == "simulation" else "authorized_dry_run"
        elif action_adapter is None:
            disposition = "safe_idle"
            holds.append("live action requires an existing canonical action adapter")
        else:
            result = action_adapter(deepcopy(selected))
            executed = True
            disposition = "attempted"
            if not isinstance(result, dict) or not result.get("evidence_reference"):
                holds.append("action adapter did not return canonical outcome evidence")
                disposition = "verification_failed"
    elif normalized:
        disposition = "escalate" if any(item["permission"] == "protected" for item in normalized) else "safe_idle"

    stage_records = []
    for stage in STAGES:
        stage_records.append({
            "stage": stage,
            "status": "completed",
            "evidence": sorted(references),
            "note": {
                "act": "canonical adapter invoked" if executed else "no side effect performed",
                "verify": "adapter evidence recorded" if result and result.get("evidence_reference") else "no executed outcome to verify",
            }.get(stage, "deterministic cycle stage"),
        })
    record = {
        "schema_version": SCHEMA_VERSION,
        "cycle_id": cycle_id,
        "observed_at": observed_at,
        "mode": mode,
        "input_digest": _digest(copied_inputs),
        "candidate_digest": _digest(sorted(copied_candidates, key=lambda item: (str(item.get("action_id")), str(item.get("idempotency_key"))))),
        "stages": stage_records,
        "disposition": disposition,
        "selected_action": proposed,
        "action_executed": executed,
        "action_result": result,
        "holds": sorted(set(holds)),
        "warnings": sorted(set(warnings)),
        "evidence_references": sorted(references | ({result["evidence_reference"]} if result and result.get("evidence_reference") else set())),
        "deduplication": {"prior_action_keys": prior_keys, "selected_key": proposed.get("idempotency_key") if proposed else None},
        "cooldown": {"seconds": cooldown_seconds, "last_action_at": last_action_at, "active": cooldown_active},
        "safe_idle": disposition == "safe_idle",
        "creates_authority": False,
        "canonical_records_mutated_only_by_adapter": executed,
    }
    record["record_digest"] = _digest(record)
    return record
