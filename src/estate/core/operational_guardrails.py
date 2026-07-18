"""Machine-evaluable projections of existing Estate policy and authority."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Iterable

SCHEMA_VERSION = "estate.operational-guardrail-evaluation.v1"
PRECEDENCE = {"constitutional": 100, "protected_decision": 90, "office": 80, "campaign": 70, "work_package": 60, "delegation": 50}
DISPOSITIONS = {"allow", "deny", "defer", "escalate"}


def _time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=parsed.tzinfo or timezone.utc).astimezone(timezone.utc)


def evaluate_guardrails(
    proposal: dict[str, Any], rules: Iterable[dict[str, Any]], *, evaluated_at: str,
) -> dict[str, Any]:
    """Evaluate a proposal; rules describe authority but never create it."""
    item = deepcopy(proposal)
    copied = [deepcopy(rule) for rule in rules]
    now = _time(evaluated_at)
    if now is None:
        raise ValueError("evaluated_at must be a valid timestamp")
    problems: list[str] = []
    if not item.get("action_id") or not item.get("action_class") or not item.get("source_refs"):
        problems.append("proposal lacks action identity, class, or source evidence")
    applicable: list[dict[str, Any]] = []
    stale_or_invalid = False
    for rule in copied:
        kind = str(rule.get("policy_kind") or "")
        disposition = str(rule.get("disposition") or "")
        start = _time(rule.get("effective_from"))
        end = _time(rule.get("effective_until"))
        valid = bool(
            rule.get("rule_id") and rule.get("authority_source") and
            kind in PRECEDENCE and disposition in DISPOSITIONS and start and
            start <= now and (end is None or now <= end)
        )
        scope = rule.get("scope") or {}
        matches = all(
            not scope.get(field) or item.get(field) == scope[field]
            for field in ("action_class", "authority_scope", "target_mechanism")
        ) and (
            not scope.get("protected_surface") or
            scope["protected_surface"] in (item.get("protected_surfaces") or [])
        )
        if matches and valid:
            applicable.append({**rule, "precedence": PRECEDENCE[kind]})
        elif matches:
            stale_or_invalid = True
    applicable.sort(key=lambda rule: (-rule["precedence"], str(rule["rule_id"])))
    disposition = "defer"
    controlling: list[dict[str, Any]] = []
    explanation = "No current canonical rule proves permission; silence is not authority."
    if problems:
        disposition = "escalate"
        explanation = "The proposal is incomplete or ambiguous and fails closed."
    elif applicable:
        highest = applicable[0]["precedence"]
        controlling = [rule for rule in applicable if rule["precedence"] == highest]
        outcomes = {rule["disposition"] for rule in controlling}
        if len(outcomes) > 1:
            disposition = "escalate"
            problems.append("equally authoritative current policies conflict")
            explanation = "Conflicting controlling policy requires its named authority."
        else:
            disposition = next(iter(outcomes))
            explanation = str(controlling[0].get("explanation") or f"Controlling policy disposition is {disposition}.")
    elif stale_or_invalid:
        problems.append("matching policy is stale, future, expired, or malformed")
    if item.get("permission") in {"protected", "prohibited"} and disposition == "allow":
        disposition = "escalate" if item.get("permission") == "protected" else "deny"
        problems.append("operational policy cannot convert protected or prohibited action into permission")
    owner = next((str(rule.get("decision_owner")) for rule in controlling if rule.get("decision_owner")), "canonical policy authority")
    return {
        "schema_version": SCHEMA_VERSION,
        "evaluation_id": f"guardrail:{item.get('action_id', 'unknown')}:{evaluated_at}",
        "evaluated_at": evaluated_at,
        "action_id": item.get("action_id"),
        "disposition": disposition,
        "controlling_rule_ids": [rule["rule_id"] for rule in controlling],
        "controlling_authority_sources": sorted({str(rule["authority_source"]) for rule in controlling}),
        "decision_owner": owner,
        "missing_or_conflicting_evidence": sorted(set(problems)),
        "explanation": explanation,
        "audit_record": {
            "proposal": item,
            "applicable_rule_ids": [rule["rule_id"] for rule in applicable],
            "controlling_rule_ids": [rule["rule_id"] for rule in controlling],
            "disposition": disposition,
            "evaluated_at": evaluated_at,
        },
        "authorizes_action": False,
        "creates_authority": False,
        "action_may_proceed_to_existing_authorization_lane": disposition == "allow",
    }
