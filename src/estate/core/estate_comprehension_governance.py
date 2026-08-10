"""Governed candidate assertion review and indexed application.

This module extends the existing SQLite knowledge-index owner. Provider output
remains immutable candidate material; only deterministic corroboration and an
explicit non-provider review policy can make a low-risk assertion eligible for
the rebuildable indexed projection. Canonical Cookbook files are never edited.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from estate.core.estate_knowledge_store import connect, database_path
from estate.core.estate_population import validate_requested_scope
from estate.core.estate_deterministic_evidence import extract_evidence, link_facts

CORROBORATION_STATES = {"CORROBORATED", "PARTIALLY_CORROBORATED", "NOT_CORROBORATED", "CONTRADICTED", "NOT_DETERMINISTICALLY_VERIFIABLE"}
REVIEW_STATES = {"PENDING", "APPROVED", "PARTIALLY_APPROVED", "REQUEST_MORE_CONTEXT", "REJECTED", "ESCALATED", "DEFERRED"}
APPLICATION_STATES = {"NOT_ELIGIBLE", "ELIGIBLE", "APPLIED", "REVALIDATION_REQUIRED", "REVERSED", "SUPERSEDED"}
DECISIONS = {"APPROVE_FOR_INDEX_APPLICATION", "APPROVE_PARTIAL", "REQUEST_MORE_CONTEXT", "REJECT_UNSUPPORTED", "REJECT_CONTRADICTED", "ESCALATE_STRONGER_REASONING", "ESCALATE_HUMAN", "DEFER"}
LOW_RISK_KINDS = {"PURPOSE", "OWNER", "DETERMINISTIC_TAG", "SCHEMA_CLASSIFICATION", "COMPONENT_LINKAGE"}
FORBIDDEN_REVIEWER_TYPES = {"local_ai", "provider", "model"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") if not isinstance(value, str) else value.encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _root(root: str | Path | None) -> Path:
    return validate_requested_scope(root)["root"]


def _rows(connection: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(sql, params).fetchall()]


def _assertion_rows(connection: sqlite3.Connection, assertion_ids: Iterable[str] | None = None, *, asset_id: str | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if assertion_ids is not None:
        ids = list(assertion_ids)
        if not ids:
            return []
        clauses.append("ca.assertion_id IN (" + ",".join("?" for _ in ids) + ")")
        params.extend(ids)
    if asset_id:
        clauses.append("ca.asset_id=?")
        params.append(asset_id)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return _rows(connection, "SELECT ca.*,a.current_path,a.current_content_hash,a.current_source_revision,a.owner,a.purpose_summary,a.comprehension_status,a.current_state FROM candidate_assertions ca JOIN assets a ON a.asset_id=ca.asset_id" + where + " ORDER BY ca.created_at,ca.assertion_id", tuple(params))


def extract_assertions(root: str | Path | None = None, *, interpretation_id: str | None = None) -> dict[str, Any]:
    """Normalize provider candidate fields into assertion-level records."""
    base = _root(root)
    created = 0
    with connect(base, create=False) as connection:
        clauses = "WHERE ci.interpretation_id=?" if interpretation_id else ""
        params = (interpretation_id,) if interpretation_id else ()
        candidates = _rows(connection, "SELECT ci.*,cr.provider_type AS result_provider_type,cr.provider_model AS result_provider_model,cr.worker_identity AS result_worker_identity,a.current_content_hash FROM candidate_interpretations ci JOIN comprehension_results cr ON cr.result_id=ci.result_id JOIN assets a ON a.asset_id=ci.asset_id " + clauses + " ORDER BY ci.created_at", params)
        for candidate in candidates:
            data = json.loads(candidate["candidate_json"])
            values: list[tuple[str, str | None, str, list[str], str]] = []
            if data.get("purpose"):
                values.append(("PURPOSE", str(data["purpose"]), "MEDIUM", list(data.get("evidence_refs") or []), "PROVIDER_INFERENCE"))
            if data.get("owner_candidate"):
                values.append(("OWNER", str(data["owner_candidate"]), "MEDIUM", list(data.get("evidence_refs") or []), "PROVIDER_INFERENCE"))
            for tag in data.get("tags") or []:
                values.append(("DETERMINISTIC_TAG", str(tag), "LOW", list(data.get("evidence_refs") or []), "PROVIDER_INFERENCE"))
            if data.get("summary"):
                values.append(("SUMMARY", str(data["summary"]), "LOW", list(data.get("evidence_refs") or []), "PROVIDER_INFERENCE"))
            for question in data.get("unresolved_questions") or []:
                values.append(("UNRESOLVED_QUESTION", str(question), "UNKNOWN", list(data.get("evidence_refs") or []), "PROVIDER_INFERENCE"))
            if not values:
                values.append(("NO_ASSERTABLE_CLAIM", None, "UNKNOWN", list(data.get("evidence_refs") or []), "PROVIDER_INFERENCE"))
            for kind, value, confidence, evidence, strength in values:
                assertion_id = "assertion:" + _sha(candidate["interpretation_id"] + ":" + kind + ":" + str(value))
                now = _now()
                cursor = connection.execute("INSERT OR IGNORE INTO candidate_assertions(assertion_id,interpretation_id,result_id,asset_id,assertion_kind,proposed_value,evidence_refs,confidence,evidence_strength,corroboration_state,corroboration_reason,review_state,application_state,conflict_state,provider_type,provider_model,worker_identity,source_revision,source_hash,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (assertion_id,candidate["interpretation_id"],candidate["result_id"],candidate["asset_id"],kind,value,_json(evidence),confidence,strength,"NOT_CORROBORATED",None,"PENDING","NOT_ELIGIBLE","NONE",candidate["provider_type"],candidate["provider_model"],candidate["worker_identity"],candidate["source_revision"],candidate["content_hash"],now,now))
                created += cursor.rowcount
    return {"status":"READY","assertions_created":created,"interpretation_id":interpretation_id,"canonical_mutation":False}


def corroborate(root: str | Path | None = None, *, assertion_ids: Iterable[str] | None = None, asset_id: str | None = None) -> dict[str, Any]:
    """Derive assertion state from revision-grounded, provider-independent facts."""
    base = _root(root)
    counts: dict[str, int] = {}
    selected_assets: set[str] = set()
    with connect(base, create=False) as connection:
        selected_assets = {row["asset_id"] for row in _assertion_rows(connection, assertion_ids, asset_id=asset_id)}
    evidence_run = extract_evidence(base, asset_ids=selected_assets)
    with connect(base, create=False) as connection:
        rows = _assertion_rows(connection, assertion_ids, asset_id=asset_id)
        for row in rows:
            state = "NOT_DETERMINISTICALLY_VERIFIABLE"
            reason = "assertion kind has no deterministic corroboration rule"
            strength = "PROVIDER_INFERENCE"
            linked: list[str] = []
            current_hash = row["current_content_hash"]
            if row["source_hash"] != current_hash:
                state, reason = "NOT_DETERMINISTICALLY_VERIFIABLE", "candidate source changed; corroboration requires revalidation"
            elif row["assertion_kind"] == "OWNER":
                facts = _rows(connection, "SELECT * FROM evidence_facts WHERE target_asset_id=? AND fact_kind='OWNER_EVIDENCE' AND current_state='CURRENT'", (row["asset_id"],))
                matching = [fact for fact in facts if json.loads(fact["value_json"]).get("owner") == row["proposed_value"]]
                if matching:
                    state, reason = "CORROBORATED", "candidate owner matches independent ownership evidence"
                    strength = matching[0]["certainty"]
                    linked = [fact["fact_id"] for fact in matching]
                elif facts:
                    state, reason = "CONTRADICTED", "candidate owner conflicts with independent ownership evidence"
                    strength = facts[0]["certainty"]
                    linked = [fact["fact_id"] for fact in facts]
                else:
                    state, reason = "NOT_CORROBORATED", "no deterministic owner is currently indexed"
            elif row["assertion_kind"] == "PURPOSE":
                facts = _rows(connection, "SELECT * FROM evidence_facts WHERE target_asset_id=? AND current_state='CURRENT' AND fact_kind IN ('SCHEMA_METADATA','SCHEMA_STRUCTURE','PYTHON_REFERENCE','TEST_REFERENCE','DOCUMENTATION_REFERENCE','SOURCE_REFERENCE')", (row["asset_id"],))
                candidate_tokens = {token for token in re.findall(r"[a-z0-9]+", (row["proposed_value"] or "").lower()) if len(token) > 2}
                metadata = [fact for fact in facts if fact["fact_kind"] in {"SCHEMA_METADATA", "SCHEMA_STRUCTURE"}]
                metadata_tokens = set()
                for fact in metadata:
                    value = json.loads(fact["value_json"])
                    metadata_tokens |= {token for token in re.findall(r"[a-z0-9]+", json.dumps(value).lower()) if len(token) > 2}
                overlap = candidate_tokens & metadata_tokens
                relationships = [fact for fact in facts if fact["fact_kind"] not in {"SCHEMA_METADATA", "SCHEMA_STRUCTURE"}]
                linked = [fact["fact_id"] for fact in metadata if overlap]
                linked.extend(fact["fact_id"] for fact in relationships)
                if "not" in candidate_tokens and "schema" in metadata_tokens:
                    state, reason = "CONTRADICTED", "candidate explicitly denies the deterministic schema classification"
                    strength = "DERIVED_STATIC_ANALYSIS"
                elif len(overlap) >= 2 and relationships:
                    state, reason = "CORROBORATED", "purpose terms align with schema metadata and independent repository references"
                    strength = "DERIVED_STATIC_ANALYSIS"
                elif overlap:
                    state, reason = "PARTIALLY_CORROBORATED", "purpose terms align with schema metadata but independent relationship evidence is limited"
                    strength = "DERIVED_STATIC_ANALYSIS"
                elif facts:
                    state, reason = "NOT_CORROBORATED", "repository facts exist but do not support the proposed purpose wording"
                    strength = "DETERMINISTIC_SOURCE_RELATIONSHIP"
                else:
                    state, reason = "NOT_CORROBORATED", "no deterministic purpose is currently indexed"
            elif row["assertion_kind"] == "DETERMINISTIC_TAG":
                facts = _rows(connection, "SELECT * FROM evidence_facts WHERE target_asset_id=? AND fact_kind='TAG_DERIVATION' AND current_state='CURRENT'", (row["asset_id"],))
                matching = [fact for fact in facts if json.loads(fact["value_json"]).get("tag") == row["proposed_value"]]
                linked = [fact["fact_id"] for fact in matching]
                strength = "DETERMINISTIC_SOURCE_RELATIONSHIP"
                state, reason = (("CORROBORATED", "tag is derived from independent inventory/schema evidence") if matching else ("NOT_CORROBORATED", "no independent deterministic tag derivation found"))
            elif row["assertion_kind"] == "COMPONENT_LINKAGE":
                facts = _rows(connection, "SELECT * FROM evidence_facts WHERE target_asset_id=? AND fact_kind='COMPONENT_LINKAGE' AND current_state='CURRENT'", (row["asset_id"],))
                matching = [fact for fact in facts if row["proposed_value"] in fact["value_json"]]
                linked = [fact["fact_id"] for fact in matching or facts]
                state, reason = (("CORROBORATED", "component linkage is explicitly indexed from source evidence") if matching else ("NOT_CORROBORATED", "no explicit component linkage evidence found"))
                strength = "DETERMINISTIC_SOURCE_RELATIONSHIP"
            elif row["assertion_kind"] == "UNRESOLVED_QUESTION":
                state, reason = "NOT_DETERMINISTICALLY_VERIFIABLE", "candidate explicitly preserved an unresolved question"
            link_facts(connection, row["assertion_id"], linked, "SUPPORTS" if state in {"CORROBORATED", "PARTIALLY_CORROBORATED"} else "CONTEXT")
            next_review = row["review_state"]
            if row["review_state"] in {"PENDING", "EXCEPTION"}:
                next_review = "EXCEPTION" if state in {"CONTRADICTED", "NOT_DETERMINISTICALLY_VERIFIABLE"} else "PENDING"
            connection.execute("UPDATE candidate_assertions SET corroboration_state=?,corroboration_reason=?,evidence_strength=?,review_state=?,updated_at=? WHERE assertion_id=?", (state,reason,strength,next_review,_now(),row["assertion_id"]))
            counts[state] = counts.get(state, 0) + 1
    return {"status":"CORROBORATED","counts":counts,"assertions":sum(counts.values()),"evidence_run":evidence_run,"canonical_mutation":False}


def review_summary(root: str | Path | None = None, *, asset_id: str | None = None) -> dict[str, Any]:
    base = _root(root)
    with connect(base, create=False) as connection:
        rows = _assertion_rows(connection, asset_id=asset_id)
        def count(field: str) -> dict[str, int]:
            out: dict[str, int] = {}
            for row in rows: out[row[field]] = out.get(row[field], 0) + 1
            return dict(sorted(out.items()))
        exception_states = {"EXCEPTION", "REQUEST_MORE_CONTEXT", "REJECTED", "ESCALATED", "DEFERRED"}
        return {"assertion_count":len(rows),"corroboration":count("corroboration_state"),"review":count("review_state"),"application":count("application_state"),"exceptions":[r for r in rows if r["review_state"] in exception_states],"canonical_mutation":False}


def _decision_state(decision: str) -> str:
    return {"APPROVE_FOR_INDEX_APPLICATION":"APPROVED","APPROVE_PARTIAL":"PARTIALLY_APPROVED","REQUEST_MORE_CONTEXT":"REQUEST_MORE_CONTEXT","REJECT_UNSUPPORTED":"REJECTED","REJECT_CONTRADICTED":"REJECTED","ESCALATE_STRONGER_REASONING":"ESCALATED","ESCALATE_HUMAN":"ESCALATED","DEFER":"DEFERRED"}[decision]


def decide(root: str | Path | None, assertion_id: str, *, decision: str, reviewer_id: str, reviewer_type: str, rationale: str, evidence_refs: Iterable[str] = ()) -> dict[str, Any]:
    base = _root(root)
    if decision not in DECISIONS: raise ValueError(f"unsupported review decision: {decision}")
    if reviewer_type.lower() in FORBIDDEN_REVIEWER_TYPES: raise ValueError("provider identity cannot approve or review its own candidate")
    refs = list(evidence_refs)
    if not rationale.strip() or not reviewer_id.strip(): raise ValueError("reviewer identity and rationale are required")
    with connect(base, create=False) as connection:
        row = connection.execute("SELECT * FROM candidate_assertions WHERE assertion_id=?", (assertion_id,)).fetchone()
        if not row: raise ValueError(f"unknown assertion: {assertion_id}")
        if decision == "APPROVE_FOR_INDEX_APPLICATION" and (row["assertion_kind"] not in LOW_RISK_KINDS or row["corroboration_state"] != "CORROBORATED"): raise ValueError("full approval requires a low-risk, corroborated assertion")
        if decision == "APPROVE_PARTIAL" and (row["assertion_kind"] not in LOW_RISK_KINDS or row["corroboration_state"] not in {"CORROBORATED","PARTIALLY_CORROBORATED"}): raise ValueError("partial approval requires a low-risk assertion with corroboration")
        now = _now(); decision_id = "decision:" + uuid.uuid4().hex
        connection.execute("INSERT INTO review_decisions(decision_id,assertion_id,decision,reviewer_id,reviewer_type,rationale,evidence_refs,source_revision,decided_at) VALUES(?,?,?,?,?,?,?,?,?)", (decision_id,assertion_id,decision,reviewer_id,reviewer_type,rationale,_json(refs),row["source_revision"],now))
        app_state = "ELIGIBLE" if decision in {"APPROVE_FOR_INDEX_APPLICATION","APPROVE_PARTIAL"} else "NOT_ELIGIBLE"
        connection.execute("UPDATE candidate_assertions SET review_state=?,application_state=?,updated_at=? WHERE assertion_id=?", (_decision_state(decision),app_state,now,assertion_id))
    return {"status":"RECORDED","decision_id":decision_id,"assertion_id":assertion_id,"decision":decision,"application_state":app_state,"canonical_mutation":False}


def review_batch(root: str | Path | None = None, *, reviewer_id: str = "estate-level1-deterministic-review", reviewer_type: str = "deterministic_policy", asset_prefix: str | None = None, asset_id: str | None = None) -> dict[str, Any]:
    base = _root(root)
    with connect(base, create=False) as connection:
        clauses = ["ca.review_state IN ('PENDING','EXCEPTION')"]
        params: list[Any] = []
        if asset_prefix:
            clauses.append("a.current_path LIKE ?"); params.append(asset_prefix.rstrip("/") + "/%")
        if asset_id:
            clauses.append("ca.asset_id=?"); params.append(asset_id)
        ids = [r["assertion_id"] for r in connection.execute("SELECT ca.assertion_id FROM candidate_assertions ca JOIN assets a ON a.asset_id=ca.asset_id WHERE " + " AND ".join(clauses), tuple(params)).fetchall()]
    results = []
    for assertion_id in ids:
        with connect(base, create=False) as connection:
            row = connection.execute("SELECT * FROM candidate_assertions WHERE assertion_id=?", (assertion_id,)).fetchone()
        if row["corroboration_state"] == "CORROBORATED" and row["assertion_kind"] in LOW_RISK_KINDS:
            decision = "APPROVE_FOR_INDEX_APPLICATION"
        elif row["corroboration_state"] == "PARTIALLY_CORROBORATED" and row["assertion_kind"] in LOW_RISK_KINDS:
            decision = "APPROVE_PARTIAL"
        elif row["corroboration_state"] == "CONTRADICTED":
            decision = "REJECT_CONTRADICTED"
        else:
            decision = "REQUEST_MORE_CONTEXT"
        results.append(decide(base, assertion_id, decision=decision, reviewer_id=reviewer_id, reviewer_type=reviewer_type, rationale="Deterministic Level-1 review policy; provider output is not authority", evidence_refs=["SQLite deterministic corroboration", row["asset_id"]]))
    return {"status":"REVIEWED","reviewed":len(results),"decisions":results,"canonical_mutation":False}


def review_asset(root: str | Path | None, asset_id: str, *, reviewer_id: str = "estate-level1-deterministic-review", reviewer_type: str = "deterministic_policy") -> dict[str, Any]:
    corroborated = corroborate(root, asset_id=asset_id)
    reviewed = review_batch(root, reviewer_id=reviewer_id, reviewer_type=reviewer_type, asset_id=asset_id)
    reviewed["asset_id"] = asset_id
    reviewed["corroboration"] = corroborated
    return reviewed


def eligible(root: str | Path | None = None) -> dict[str, Any]:
    base = _root(root)
    with connect(base, create=False) as connection:
        rows = _rows(connection, "SELECT ca.*,a.current_path,a.current_content_hash,a.current_source_revision FROM candidate_assertions ca JOIN assets a ON a.asset_id=ca.asset_id WHERE ca.application_state='ELIGIBLE' AND ca.source_hash=a.current_content_hash AND ca.assertion_kind IN ('PURPOSE','OWNER','DETERMINISTIC_TAG','SCHEMA_CLASSIFICATION','COMPONENT_LINKAGE') AND ca.conflict_state='NONE' ORDER BY ca.created_at")
    return {"eligible_count":len(rows),"assertions":rows,"canonical_mutation":False}


def apply_eligible(root: str | Path | None = None, *, assertion_ids: Iterable[str] | None = None, actor_id: str = "estate-level1-application-policy", actor_type: str = "deterministic_policy") -> dict[str, Any]:
    base = _root(root)
    if actor_type.lower() in FORBIDDEN_REVIEWER_TYPES: raise ValueError("provider identity cannot apply indexed understanding")
    ids = set(assertion_ids or [])
    applied = []
    with connect(base, create=False) as connection:
        rows = _assertion_rows(connection, ids or None)
        rows = [r for r in rows if r["application_state"] == "ELIGIBLE" and r["source_hash"] == r["current_content_hash"] and r["assertion_kind"] in LOW_RISK_KINDS]
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault((row["asset_id"], row["assertion_kind"]), []).append(row)
        conflicted: set[str] = set()
        for group in grouped.values():
            if len({row["proposed_value"] for row in group}) > 1:
                conflicted.update(row["assertion_id"] for row in group)
        if conflicted:
            now = _now()
            connection.executemany("UPDATE candidate_assertions SET conflict_state='CONTRADICTORY_APPLICATIONS',application_state='NOT_ELIGIBLE',review_state='EXCEPTION',updated_at=? WHERE assertion_id=?", [(now, assertion_id) for assertion_id in conflicted])
            rows = [row for row in rows if row["assertion_id"] not in conflicted]
        for row in rows:
            field = {"PURPOSE":"purpose_summary","OWNER":"owner","SCHEMA_CLASSIFICATION":"purpose_summary","COMPONENT_LINKAGE":"purpose_summary","DETERMINISTIC_TAG":"tag"}[row["assertion_kind"]]
            prior = None if field == "tag" else connection.execute(f"SELECT {field} FROM assets WHERE asset_id=?", (row["asset_id"],)).fetchone()[0]
            application_id = "application:" + uuid.uuid4().hex
            now = _now()
            connection.execute("INSERT INTO applied_comprehension(application_id,assertion_id,asset_id,field_name,applied_value,source_revision,source_hash,reviewer_id,applied_at,state) VALUES(?,?,?,?,?,?,?,?,?,?)", (application_id,row["assertion_id"],row["asset_id"],field,row["proposed_value"],row["current_source_revision"],row["current_content_hash"],actor_id,now,"APPLIED"))
            connection.execute("INSERT INTO application_history(history_id,application_id,event_type,prior_value,new_value,evidence_refs,source_revision,actor_id,actor_type,occurred_at,reason) VALUES(?,?,?,?,?,?,?,?,?,?,?)", ("history:" + uuid.uuid4().hex,application_id,"APPLIED",prior,row["proposed_value"],row["evidence_refs"],row["current_source_revision"],actor_id,actor_type,now,"Governed low-risk candidate application"))
            if field == "tag":
                connection.execute("INSERT OR REPLACE INTO tags(asset_id,tag,source_kind,confidence,source_ref,source_revision,current_state) VALUES(?,?,?,?,?,?,?)", (row["asset_id"],row["proposed_value"],"GOVERNED_APPLICATION","MEDIUM",row["assertion_id"],row["current_source_revision"],"CURRENT"))
            else:
                connection.execute(f"UPDATE assets SET {field}=?,last_comprehended=?,current_state='CURRENT' WHERE asset_id=?", (row["proposed_value"],now,row["asset_id"]))
            connection.execute("UPDATE candidate_assertions SET application_state='APPLIED',updated_at=? WHERE assertion_id=?", (now,row["assertion_id"]))
            applied.append({"application_id":application_id,"assertion_id":row["assertion_id"],"asset_id":row["asset_id"],"field":field,"value":row["proposed_value"]})
        connection.execute("UPDATE assets SET comprehension_status=CASE WHEN purpose_summary IS NOT NULL AND owner IS NOT NULL THEN 'COMPREHENDED' WHEN purpose_summary IS NOT NULL OR owner IS NOT NULL THEN 'PARTIAL' ELSE 'UNKNOWN' END WHERE asset_id IN (SELECT DISTINCT asset_id FROM applied_comprehension WHERE state='APPLIED')")
    return {"status":"APPLIED","applied_count":len(applied),"applications":applied,"canonical_mutation":False}


def application_history(root: str | Path | None = None, *, asset_id: str | None = None) -> dict[str, Any]:
    base = _root(root)
    with connect(base, create=False) as connection:
        where = " WHERE ac.asset_id=?" if asset_id else ""
        rows = _rows(connection, "SELECT h.*,ac.assertion_id,ac.asset_id,ac.field_name,ac.applied_value,ac.state FROM application_history h JOIN applied_comprehension ac ON ac.application_id=h.application_id" + where + " ORDER BY h.occurred_at", (asset_id,) if asset_id else ())
    return {"history":rows,"count":len(rows),"canonical_mutation":False}


def reverse_application(root: str | Path | None, application_id: str, *, actor_id: str, actor_type: str, reason: str) -> dict[str, Any]:
    base = _root(root)
    if actor_type.lower() in FORBIDDEN_REVIEWER_TYPES: raise ValueError("provider identity cannot reverse indexed understanding")
    with connect(base, create=False) as connection:
        row = connection.execute("SELECT ac.*,a.current_source_revision,a.current_content_hash FROM applied_comprehension ac JOIN assets a ON a.asset_id=ac.asset_id WHERE ac.application_id=? AND ac.state='APPLIED'", (application_id,)).fetchone()
        if not row: raise ValueError("application is not currently applied")
        hist = connection.execute("SELECT * FROM application_history WHERE application_id=? AND event_type='APPLIED' ORDER BY occurred_at DESC LIMIT 1", (application_id,)).fetchone()
        prior = hist["prior_value"]
        now = _now()
        if row["field_name"] == "tag":
            connection.execute("DELETE FROM tags WHERE asset_id=? AND tag=? AND source_ref=?", (row["asset_id"],row["applied_value"],row["assertion_id"]))
        else:
            connection.execute(f"UPDATE assets SET {row['field_name']}=?,current_state='CURRENT' WHERE asset_id=?", (prior,row["asset_id"]))
        connection.execute("UPDATE applied_comprehension SET state='REVERSED' WHERE application_id=?", (application_id,))
        connection.execute("UPDATE candidate_assertions SET application_state='REVERSED',updated_at=? WHERE assertion_id=?", (now,row["assertion_id"]))
        connection.execute("INSERT INTO application_history(history_id,application_id,event_type,prior_value,new_value,evidence_refs,source_revision,actor_id,actor_type,occurred_at,reason) VALUES(?,?,?,?,?,?,?,?,?,?,?)", ("history:" + uuid.uuid4().hex,application_id,"REVERSED",row["applied_value"],prior,hist["evidence_refs"],row["current_source_revision"],actor_id,actor_type,now,reason))
    return {"status":"REVERSED","application_id":application_id,"canonical_mutation":False}


def revalidate_applications(root: str | Path | None = None) -> dict[str, Any]:
    base = _root(root); queued = []
    with connect(base, create=False) as connection:
        rows = _rows(connection, "SELECT ac.*,a.current_source_revision,a.current_content_hash FROM applied_comprehension ac JOIN assets a ON a.asset_id=ac.asset_id WHERE ac.state='APPLIED'")
        for row in rows:
            if row["source_hash"] == row["current_content_hash"]: continue
            now = _now()
            connection.execute("UPDATE applied_comprehension SET state='REVALIDATION_REQUIRED' WHERE application_id=?", (row["application_id"],))
            connection.execute("UPDATE candidate_assertions SET application_state='REVALIDATION_REQUIRED',updated_at=? WHERE assertion_id=?", (now,row["assertion_id"]))
            connection.execute("UPDATE assets SET current_state='REVALIDATION_REQUIRED' WHERE asset_id=?", (row["asset_id"],))
            qid = "revalidation:" + uuid.uuid4().hex
            connection.execute("INSERT INTO revalidation_queue(queue_id,assertion_id,asset_id,prior_source_revision,current_source_revision,prior_source_hash,current_source_hash,state,reason,queued_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (qid,row["assertion_id"],row["asset_id"],row["source_revision"],row["current_source_revision"],row["source_hash"],row["current_content_hash"],"OPEN","applied assertion source content changed",now))
            queued.append(qid)
    return {"status":"REVALIDATION_REQUIRED" if queued else "CURRENT","queued_count":len(queued),"queue_ids":queued,"canonical_mutation":False}


def resident_query(root: str | Path | None = None, *, role: str = "researcher", query: str = "") -> dict[str, Any]:
    base = _root(root)
    with connect(base, create=False) as connection:
        clauses = ["ac.state='APPLIED'"]; params: list[Any] = []
        if query:
            clauses.append("(a.current_path LIKE ? OR ac.applied_value LIKE ?)"); params.extend(["%" + query + "%", "%" + query + "%"])
        rows = _rows(connection, "SELECT ac.application_id,ac.assertion_id,ac.asset_id,a.current_path,ac.field_name,ac.applied_value,ac.source_revision,ac.source_hash,ac.applied_at FROM applied_comprehension ac JOIN assets a ON a.asset_id=ac.asset_id WHERE " + " AND ".join(clauses) + " ORDER BY a.current_path", tuple(params))
        history = _rows(connection, "SELECT h.* FROM application_history h JOIN applied_comprehension ac ON ac.application_id=h.application_id WHERE ac.state='APPLIED' ORDER BY h.occurred_at")
        related = _rows(connection, "SELECT asset_id,current_path,owner,purpose_summary,comprehension_status FROM assets WHERE current_path LIKE ? ORDER BY current_path LIMIT 100", ("%" + query + "%",)) if query else []
    return {"role":role,"query":query,"applied_understanding":rows,"application_history":history if role == "historian" else [],"related_assets":related if role == "researcher" else [],"unresolved_questions":[] if role != "researcher" else [r["current_path"] for r in related if r.get("comprehension_status") != "COMPREHENDED"],"canonical_mutation":False}


def governance_coverage(root: str | Path | None = None) -> dict[str, Any]:
    base = _root(root)
    with connect(base, create=False) as connection:
        out = {"assertions_total":connection.execute("SELECT COUNT(*) FROM candidate_assertions").fetchone()[0],"corroborated":connection.execute("SELECT COUNT(*) FROM candidate_assertions WHERE corroboration_state='CORROBORATED'").fetchone()[0],"partially_corroborated":connection.execute("SELECT COUNT(*) FROM candidate_assertions WHERE corroboration_state='PARTIALLY_CORROBORATED'").fetchone()[0],"contradicted":connection.execute("SELECT COUNT(*) FROM candidate_assertions WHERE corroboration_state='CONTRADICTED'").fetchone()[0],"unverifiable":connection.execute("SELECT COUNT(*) FROM candidate_assertions WHERE corroboration_state='NOT_DETERMINISTICALLY_VERIFIABLE'").fetchone()[0],"review_exceptions":connection.execute("SELECT COUNT(*) FROM candidate_assertions WHERE review_state IN ('EXCEPTION','REQUEST_MORE_CONTEXT','ESCALATED','DEFERRED')").fetchone()[0],"applied":connection.execute("SELECT COUNT(*) FROM candidate_assertions WHERE application_state='APPLIED'").fetchone()[0],"revalidation_required":connection.execute("SELECT COUNT(*) FROM candidate_assertions WHERE application_state='REVALIDATION_REQUIRED'").fetchone()[0],"assets_partial":connection.execute("SELECT COUNT(*) FROM assets WHERE comprehension_status='PARTIAL'").fetchone()[0],"assets_comprehended":connection.execute("SELECT COUNT(*) FROM assets WHERE comprehension_status='COMPREHENDED'").fetchone()[0]}
    return {**out,"canonical_mutation":False,"database":str(database_path(base))}
