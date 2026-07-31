"""Canonical PTM readiness freshness policy loading and evaluation."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .ptm_production_readiness import PtmReadinessError, canonical_json, digest

POLICY_PATH = Path("config/ptm/readiness_freshness_policy.json")
POLICY_SCHEMA_PATH = Path("schemas/ptm/readiness_freshness_policy_v1.schema.json")


def _time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise PtmReadinessError("freshness policy timestamp invalid") from exc
    if parsed.tzinfo is None:
        raise PtmReadinessError("freshness policy timestamp requires timezone")
    return parsed.astimezone(timezone.utc)


def load_freshness_policy(root: Path, *, observed_at: str | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    path = root / POLICY_PATH
    schema_path = root / POLICY_SCHEMA_PATH
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PtmReadinessError("freshness policy missing or malformed") from exc
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(policy), key=lambda error: list(error.path))
    if errors:
        raise PtmReadinessError("freshness policy schema invalid: " + errors[0].message)
    unsigned = dict(policy)
    declared = unsigned.pop("policy_digest", None)
    computed = digest(unsigned)
    if declared not in (None, computed):
        raise PtmReadinessError("freshness policy digest mismatch")
    policy["policy_digest"] = computed
    if observed_at is not None and _time(observed_at) < _time(policy["effective_at"]):
        raise PtmReadinessError("freshness policy is not yet effective")
    return policy


def evaluate_evidence(policy: dict[str, Any], evidence: dict[str, Any], *, evidence_class: str, observed_at: str) -> list[str]:
    rules = policy.get("evidence_classes", {})
    rule = rules.get(evidence_class)
    if not isinstance(rule, dict):
        return [f"unsupported evidence class: {evidence_class}"]
    timestamp = evidence.get("observed_at")
    if not timestamp:
        return [f"missing timestamp for evidence class: {evidence_class}"]
    try:
        observed = _time(observed_at)
        evidence_time = _time(timestamp)
    except PtmReadinessError as exc:
        return [str(exc)]
    skew = timedelta(seconds=int(policy["allowed_clock_skew_seconds"]))
    if evidence_time > observed + skew:
        return [f"future timestamp exceeds allowed skew: {evidence_class}"]
    max_age = rule.get("maximum_age_seconds")
    if max_age is not None and observed - evidence_time > timedelta(seconds=int(max_age)):
        return [f"stale evidence: {evidence_class}"]
    expires = evidence.get("expires_at")
    if expires:
        try:
            if _time(expires) <= observed:
                return [f"expired evidence: {evidence_class}"]
        except PtmReadinessError as exc:
            return [str(exc)]
    if not expires and rule.get("requires_explicit_expiry"):
        return [f"missing explicit expiry: {evidence_class}"]
    if evidence_class == "waiver":
        granted = evidence.get("granted_at")
        try:
            duration = _time(evidence.get("expires_at", "")) - _time(granted or "")
        except PtmReadinessError as exc:
            return [str(exc)]
        if not granted or duration > timedelta(seconds=86400):
            return ["waiver duration exceeds 24 hours or expiry is missing"]
    return []
