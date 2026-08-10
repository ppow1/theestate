"""Evidence-backed model/class routing for the governed comprehension worker."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from estate.core.estate_knowledge_store import _now, connect

ROUTE_STATES = {"PRIMARY", "FALLBACK", "REVIEW_REQUIRED", "DISALLOWED_FOR_CLASS", "TEMPORARILY_SUSPENDED", "NOT_YET_QUALIFIED"}
MODELS = ("qwen3:8b", "qwen3-coder:30b-qwencode-20k")


def work_class(path: str) -> str:
    value = path.lower().replace("\\", "/")
    if value.startswith("data/registry/"):
        return "REGISTRIES_CONTRACTS"
    if value.startswith("data/") or value.endswith((".yaml", ".yml")):
        return "SIMPLE_CONFIGURATION"
    if "/migrations/" in value or value.startswith("migrations/"):
        return "MIGRATIONS"
    if value.endswith(".md"):
        return "DOCUMENTATION"
    if value.endswith(".json"):
        return "JSON_SCHEMA"
    return "OTHER_LEVEL1"


def _stats(connection, model: str, cls: str) -> dict[str, int]:
    rows = connection.execute("""SELECT ca.validation_state,ca.validation_code FROM comprehension_attempts ca
      JOIN comprehension_batch_assets ba ON ba.batch_id=ca.batch_id JOIN assets a ON a.asset_id=ba.asset_id
      WHERE ca.provider_model=? AND (?='OTHER_LEVEL1' OR (?='REGISTRIES_CONTRACTS' AND a.current_path LIKE 'data/registry/%') OR (?='SIMPLE_CONFIGURATION' AND a.current_path LIKE 'data/%' AND a.current_path NOT LIKE 'data/registry/%') OR (?='DOCUMENTATION' AND a.current_path LIKE '%.md') OR (?='MIGRATIONS' AND a.current_path LIKE 'migrations/%') OR (?='JSON_SCHEMA' AND a.current_path LIKE 'schemas/%.json'))""", (model, cls, cls, cls, cls, cls, cls)).fetchall()
    return {"attempts": len(rows), "valid": sum(r[0] == "VALIDATED_CANDIDATE" for r in rows), "invalid_results": sum(r[0] == "INVALID_RESULT" for r in rows), "invalid_citations": sum(r[1] in {"MISSING_EVIDENCE_CITATION", "MALFORMED_EVIDENCE_ID", "EVIDENCE_ID_NOT_IN_PACKET", "EVIDENCE_ID_UNKNOWN", "EVIDENCE_NOT_AUTHORIZED_FOR_ASSERTION"} for r in rows), "timeouts": sum(r[0] == "PROVIDER_FAILURE" for r in rows)}


def select_route(root: str | Path, cls: str, *, requested_model: str | None = None) -> dict[str, Any]:
    with connect(root, create=False) as connection:
        stats = {model: _stats(connection, model, cls) for model in MODELS}
        if requested_model:
            candidates = [requested_model]
        else:
            candidates = list(MODELS)
        selected = None
        decisions = []
        for model in candidates:
            s = stats.get(model, {"attempts": 0, "valid": 0, "invalid_citations": 0, "timeouts": 0})
            if model == "qwen3:8b" and cls == "REGISTRIES_CONTRACTS" and (s.get("invalid_citations", 0) or s.get("invalid_results", 0)):
                state, reason = "DISALLOWED_FOR_CLASS", f"{model} has {s.get('invalid_results', 0)} invalid results ({s.get('invalid_citations', 0)} classified citation failures) for {cls}"
            elif s["timeouts"] >= 2:
                state, reason = "TEMPORARILY_SUSPENDED", f"{model} has repeated provider failures for {cls}"
            elif s["attempts"] and s["valid"] == s["attempts"]:
                state, reason = "PRIMARY", f"{model} has {s['valid']}/{s['attempts']} valid bounded attempts for {cls}"
            else:
                state, reason = "NOT_YET_QUALIFIED", f"insufficient evidence for {model} in {cls}"
            decisions.append((model, state, reason, s))
            if selected is None and state in {"PRIMARY", "FALLBACK"}:
                selected = model
        if selected is None and not requested_model:
            qualified = [d for d in decisions if d[1] not in {"DISALLOWED_FOR_CLASS", "TEMPORARILY_SUSPENDED"}]
            selected = qualified[0][0] if qualified and qualified[0][3]["attempts"] else None
        if selected is None and requested_model:
            candidate = next((d for d in decisions if d[0] == requested_model), None)
            if candidate and candidate[1] == "NOT_YET_QUALIFIED":
                selected = requested_model
                decisions = [(m, "REVIEW_REQUIRED" if m == requested_model else st, ("explicit bounded comparison; qualification evidence is pending" if m == requested_model else rs), ev) for m, st, rs, ev in decisions]
        decision_id = "route:" + uuid.uuid4().hex
        for model, state, reason, evidence in decisions:
            connection.execute("INSERT INTO comprehension_route_decisions(decision_id,work_class,model_id,route_state,selected,reason,evidence_json,decided_at) VALUES(?,?,?,?,?,?,?,?)", (decision_id + ":" + model, cls, model, state, int(model == selected), reason, json.dumps(evidence, sort_keys=True), _now()))
        if selected:
            chosen = next(d for d in decisions if d[0] == selected)
            return {"work_class": cls, "selected_model": selected, "route_state": chosen[1], "reason": chosen[2], "decisions": [{"model": m, "state": st, "reason": rs, "evidence": ev} for m, st, rs, ev in decisions]}
        return {"work_class": cls, "selected_model": None, "route_state": "NOT_YET_QUALIFIED", "reason": "no qualified local model", "decisions": [{"model": m, "state": st, "reason": rs, "evidence": ev} for m, st, rs, ev in decisions]}


def record_escalation(root: str | Path, *, work_class_name: str, initial_batch_id: str, fallback_batch_id: str | None, initial_attempt_id: str | None, fallback_attempt_id: str | None, reason: str, state: str) -> str:
    escalation_id = "escalation:" + uuid.uuid4().hex
    with connect(root, create=False) as connection:
        connection.execute("INSERT INTO comprehension_escalations(escalation_id,work_class,initial_batch_id,fallback_batch_id,initial_attempt_id,fallback_attempt_id,reason,state,created_at) VALUES(?,?,?,?,?,?,?,?,?)", (escalation_id, work_class_name, initial_batch_id, fallback_batch_id, initial_attempt_id, fallback_attempt_id, reason, state, _now()))
    return escalation_id


def routing_status(root: str | Path) -> dict[str, Any]:
    with connect(root, create=False) as connection:
        return {"routes": [dict(r) for r in connection.execute("SELECT * FROM comprehension_route_decisions ORDER BY decided_at DESC LIMIT 100")], "escalations": [dict(r) for r in connection.execute("SELECT * FROM comprehension_escalations ORDER BY created_at DESC")], "canonical_mutation": False}
