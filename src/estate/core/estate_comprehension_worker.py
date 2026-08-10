"""Bounded, provider-neutral comprehension worker for governed population.

The worker owns selection, packet construction, response parsing, quality
classification, and candidate ingestion.  The local Ollama adapter is only a
transport provider; it never receives filesystem authority or promotion power.
"""
from __future__ import annotations

import json
import hashlib
import re
import time
import uuid
from pathlib import Path
from typing import Any

from estate.core.estate_population import (
    PACKET_VERSION, PopulationScopeError, batch_packet, ingest_result, next_batch, packet_citation_errors,
    record_comprehension_attempt, validate_result,
)
from estate.core.estate_deterministic_evidence import extract_evidence
from estate.core.estate_comprehension_routing import record_escalation, select_route, work_class
from estate.core.estate_knowledge_store import connect, _now
from estate.core.resident_interaction import LocalOllamaAdapter

QUALITY = {
    "ACCEPTED_CANDIDATE", "PARTIAL_CANDIDATE", "NEEDS_MORE_CONTEXT",
    "RETRYABLE_PROVIDER_FAILURE", "INVALID_RESULT", "CONFLICT_REVIEW_REQUIRED",
    "HIGHER_REASONING_REQUIRED", "HUMAN_REVIEW_REQUIRED",
}


def _root(root: str | Path) -> Path:
    return Path(root)


def provider_status(*, timeout: float = 4.0, model: str | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    adapter = LocalOllamaAdapter(timeout=timeout)
    discovery = adapter.discover_models()
    # The governed provider contract names qwen3:8b as its preferred model;
    # discovery remains authoritative for actual availability.
    preferred = "qwen3:8b"
    selected = model if model in (discovery.get("models") or []) else (preferred if preferred in (discovery.get("models") or []) else discovery.get("model"))
    return {
        "provider": "ollama",
        "provider_type": "local",
        "endpoint": discovery.get("endpoint"),
        "available": bool(discovery.get("available")),
        "models": discovery.get("models") or [],
        "model": selected,
        "structured_output": "prompt_json_validation",
        "context_capability": "configured_packet_bound",
        "response_status": "available" if discovery.get("available") else "offline",
        "checked_at": _now(),
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        "diagnostic": discovery.get("discovery"),
        "scope_authority": "Estate deterministic population tooling",
        "canonical_authority": False,
    }


def difficulty_for(packet: dict[str, Any]) -> str:
    assets = packet.get("assets") or []
    paths = [str(a.get("path", "")).lower() for a in assets]
    joined = " ".join(paths)
    if any(x in joined for x in ("parking_lot", "legacy", "historical", "deprecated", "supersession", "conflict")):
        return "LEVEL_4"
    if len(assets) > 3 or any(x in joined for x in ("workflow", "scheduler", "grace", "diagnostic")):
        return "LEVEL_3"
    if any(x.endswith((".md", ".json", ".yaml", ".yml")) for x in paths):
        return "LEVEL_1"
    if any(x.endswith(".py") for x in paths):
        return "LEVEL_2"
    return "LEVEL_4"


def _prompt(packet: dict[str, Any], difficulty: str) -> str:
    safe_packet = dict(packet)
    safe_packet["assets"] = [{k: v for k, v in asset.items() if k != "content"} | {"content": asset.get("content", "")} for asset in packet.get("assets", [])]
    return (
        "You are a bounded Estate comprehension provider. Return ONLY one JSON object, no markdown. "
        "Do not browse files, call tools, invent paths, promote truth, or recommend remediation. "
        "Use only supplied asset_id values for asset_id fields. Evidence citations are a separate namespace. "
        "ALLOWED_EVIDENCE_FACT_IDS are the exact fact:... IDs in packet.evidence_fact_ids and deterministic_evidence. "
        "For every positive assertion, evidence_refs MUST contain only one or more exact IDs from ALLOWED_EVIDENCE_FACT_IDS. "
        "Never cite an asset_id, path, filename, prose description, global fact ID not in this packet, or invented ID. "
        "If no allowed supplied fact supports a positive claim, emit unresolved/no-claim instead. "
        "Each items[].asset_id MUST exactly equal one of the packet asset IDs; never output placeholders such as supplied, same batch, or same revision. "
        "Return one item for each supplied asset, using its exact asset_id. "
        "Use the deterministic_evidence supplied inside each asset; do not browse files or databases. "
        "If supplied evidence supports a narrow low-risk claim, emit it rather than defaulting to unresolved. "
        "Every positive purpose, owner_candidate, summary, classification, or tag needs one or more exact evidence_fact_id values in evidence_refs. "
        "Use classification for a mechanically supported class such as SCHEMA, TEST, CONFIG, MIGRATION, or DOCUMENTATION. "
        "Use tags only for deterministic tags supported by supplied facts. Owner may be non-null only with authoritative owner evidence. "
        "Unknown or ambiguous claims must remain null and be explained in unresolved_questions. "
        "The lifecycle must remain CANDIDATE. Contract and exact fields: "
        '{"contract":"estate.troubleshooting.comprehension.result.v1",'
        '"result_id":"provider-generated", "batch_id":"same batch", "source_revision":"same revision",'
        '"provider":{"type":"local_ai","model":"model","worker_identity":"worker"},'
        '"packet_version":"estate.troubleshooting.comprehension.work_packet.v2", "prompt_contract_version":"estate.troubleshooting.evidence_enriched_prompt.v2",'
        '"quality":"PARTIAL_CANDIDATE", "items":[{"asset_id":"EXACT_PACKET_ASSET_ID",'
        '"lifecycle":"CANDIDATE","purpose":null,"owner_candidate":null,"summary":null,"classification":null,'
        '"tags":[],"evidence_refs":[],"unresolved_questions":[]}],'
        '"context_requests":[],"unsupported_assertions":[]}\n'
        f"Difficulty: {difficulty}. Packet:\n{json.dumps(safe_packet, sort_keys=True)}"
    )


def _extract_json(text: str) -> dict[str, Any]:
    candidate = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", candidate, re.S | re.I)
    if fence:
        candidate = fence.group(1)
    if not candidate.startswith("{"):
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("provider response did not contain a JSON object")
        candidate = candidate[start:end + 1]
    value = json.loads(candidate)
    if not isinstance(value, dict):
        raise ValueError("provider response JSON must be an object")
    return value


def _estate_result_id(batch_id: str, payload: dict[str, Any]) -> str:
    material = json.dumps({"batch_id": batch_id, "source_revision": payload.get("source_revision"), "items": payload.get("items", [])}, sort_keys=True, separators=(",", ":"))
    return "result:" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]


def _quality(payload: dict[str, Any], packet: dict[str, Any]) -> tuple[str, list[str]]:
    supplied_facts = set(packet.get("evidence_fact_ids") or [])
    reasons: list[str] = []
    for item in payload.get("items", []):
        reasons.extend(f"{item.get('asset_id')}: {error['code']} - {error['message']}" for error in packet_citation_errors(item, supplied_facts))
    if payload.get("context_requests"):
        return "NEEDS_MORE_CONTEXT", reasons
    if reasons:
        return "INVALID_RESULT", reasons
    return "ACCEPTED_CANDIDATE", []


def _persist_telemetry(root: Path, *, batch_id: str, telemetry: dict[str, Any]) -> None:
    with connect(root, create=False) as connection:
        state = "RETRYABLE" if telemetry["quality"] == "RETRYABLE_PROVIDER_FAILURE" else ("FAILED" if telemetry["quality"] == "INVALID_RESULT" else None)
        reason = "; ".join(telemetry.get("reasons", [])) or None
        if telemetry.get("provider_metadata"):
            reason = json.dumps({"message": reason, "provider_metadata": telemetry["provider_metadata"]}, sort_keys=True, separators=(",", ":"))
        if state:
            connection.execute("UPDATE comprehension_batches SET state=?, result_state=?, failure_reason=?, updated_at=? WHERE batch_id=?", (state, telemetry["quality"], reason, _now(), batch_id))
        else:
            connection.execute("UPDATE comprehension_batches SET result_state=?, failure_reason=?, updated_at=? WHERE batch_id=?", (telemetry["quality"], reason, _now(), batch_id))


def run_local(root: str | Path, *, limit: int = 1, max_bytes: int = 65536, model: str | None = None, worker_identity: str = "estate-local-comprehension-worker", asset_prefix: str | None = None, timeout: float = 120.0, allow_reprocess: bool = False) -> dict[str, Any]:
    base = _root(root)
    health = provider_status(timeout=min(timeout, 4.0), model=model)
    if not health["available"]:
        return {"status": "PROVIDER_UNAVAILABLE", "provider_health": health, "work_units": []}
    results: list[dict[str, Any]] = []
    adapter = LocalOllamaAdapter(timeout=timeout)
    processed_assets: set[str] = set()
    for _ in range(max(1, min(limit, 20))):
        batch = next_batch(base, limit=1, provider_type="local_ai", provider_model=health.get("model"), worker_identity=worker_identity, asset_prefix=asset_prefix, allow_reprocess=allow_reprocess, exclude_asset_ids=processed_assets)
        if batch.get("status") == "NO_WORK":
            break
        batch_id = batch["batch_id"]
        attempt_id = "attempt:" + uuid.uuid4().hex
        processed_assets.update(batch.get("asset_ids") or [])
        started = time.perf_counter()
        try:
            extract_evidence(base, asset_ids=batch.get("asset_ids") or [])
            packet = batch_packet(base, batch_id, max_bytes=max_bytes)
            packet_hash = hashlib.sha256(json.dumps(packet, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
            difficulty = difficulty_for(packet)
            cls = work_class(packet.get("assets", [{}])[0].get("path", ""))
            route = select_route(base, cls, requested_model=model)
            selected_model = route.get("selected_model")
            if not selected_model:
                telemetry = {"quality": "ROUTE_BLOCKED", "reasons": [route.get("reason", "no qualified route")], "route": route, "duration_ms": round((time.perf_counter() - started) * 1000, 2)}
                _persist_telemetry(base, batch_id=batch_id, telemetry={"quality": "INVALID_RESULT", "reasons": telemetry["reasons"]})
                results.append({"batch_id": batch_id, **telemetry})
                break
            with connect(base, create=False) as connection:
                connection.execute("UPDATE comprehension_batches SET provider_model=? WHERE batch_id=?", (selected_model, batch_id))
                prior = connection.execute("""SELECT b.batch_id,ca.attempt_id FROM comprehension_batches b
                  JOIN comprehension_batch_assets ba ON ba.batch_id=b.batch_id
                  JOIN assets a ON a.asset_id=ba.asset_id
                  LEFT JOIN comprehension_attempts ca ON ca.batch_id=b.batch_id
                  WHERE a.current_path=? AND b.state='FAILED' AND b.provider_model=?
                  ORDER BY b.created_at DESC LIMIT 1""", (packet["assets"][0]["path"], health.get("model"))).fetchone()
            if model is None and prior and selected_model != health.get("model"):
                weaker = next((row for row in route.get("decisions", []) if row.get("model") == health.get("model")), {})
                record_escalation(base, work_class_name=cls, initial_batch_id=prior[0], fallback_batch_id=batch_id, initial_attempt_id=prior[1], fallback_attempt_id=attempt_id, reason=weaker.get("reason", "weaker route disallowed by recorded failures"), state="FALLBACK_ROUTED")
            response = adapter.generate(resident="comprehension-worker", prompt=_prompt(packet, difficulty), model=selected_model)
            if not response.get("ok"):
                metadata = response.get("metadata", {})
                reason = metadata.get("fallback_reason", "local provider failed")
                telemetry = {"quality": "RETRYABLE_PROVIDER_FAILURE", "reasons": [reason], "duration_ms": round((time.perf_counter() - started) * 1000, 2), "difficulty": difficulty, "provider_metadata": metadata}
                record_comprehension_attempt(base, attempt_id=attempt_id, batch_id=batch_id, result_id=None, provider_type="local_ai", provider_model=selected_model, worker_identity=worker_identity, source_revision=packet["source_revision"], packet_version=packet.get("packet_version"), prompt_contract_version=packet.get("prompt_contract_version"), packet_hash=packet_hash, raw_output=None, validation_state="PROVIDER_FAILURE", validation_code=metadata.get("timeout_phase"), validation_message=reason, telemetry={**telemetry, "route": route, "work_class": cls})
                _persist_telemetry(base, batch_id=batch_id, telemetry=telemetry)
                results.append({"batch_id": batch_id, **telemetry})
                # A provider timeout is a circuit-breaker event for this
                # bounded invocation. Preserve the retryable batch and stop
                # dequeuing further work until an operator explicitly resumes.
                break
            payload = _extract_json(response["text"])
            payload["batch_id"] = batch_id
            payload["source_revision"] = packet["source_revision"]
            payload["packet_version"] = packet.get("packet_version")
            payload["prompt_contract_version"] = packet.get("prompt_contract_version")
            # Provider result IDs are advisory only. Estate owns identity so a
            # model placeholder cannot collide across independent work units.
            payload["result_id"] = _estate_result_id(batch_id, payload)
            payload["provider"] = {"type": "local_ai", "model": selected_model, "worker_identity": worker_identity}
            for item in payload.get("items", []):
                item.setdefault("lifecycle", "CANDIDATE")
                item.setdefault("evidence_refs", [])
            quality, reasons = _quality(payload, packet)
            payload["quality"] = quality
            payload["telemetry"] = {"difficulty": difficulty, "work_class": cls, "route": route, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "packet_bytes": len(json.dumps(packet).encode()), "provider": response.get("metadata", {})}
            payload["unsupported_assertions"] = payload.get("unsupported_assertions", [])
            if quality == "PARTIAL_CANDIDATE":
                # Preserve a structured candidate but make the review state explicit.
                payload["context_requests"] = payload.get("context_requests", [])
            record_comprehension_attempt(base, attempt_id=attempt_id, batch_id=batch_id, result_id=payload["result_id"], provider_type="local_ai", provider_model=selected_model, worker_identity=worker_identity, source_revision=packet["source_revision"], packet_version=packet.get("packet_version"), prompt_contract_version=packet.get("prompt_contract_version"), packet_hash=packet_hash, raw_output=response.get("text"), validation_state="RECEIVED", telemetry=payload["telemetry"])
            validate_result(base, payload, packet=packet)
            ingested = ingest_result(base, payload, packet=packet)
            record_comprehension_attempt(base, attempt_id=attempt_id, batch_id=batch_id, result_id=payload["result_id"], provider_type="local_ai", provider_model=selected_model, worker_identity=worker_identity, source_revision=packet["source_revision"], packet_version=packet.get("packet_version"), prompt_contract_version=packet.get("prompt_contract_version"), packet_hash=packet_hash, raw_output=response.get("text"), validation_state="VALIDATED_CANDIDATE", telemetry=payload["telemetry"])
            telemetry = {"quality": quality, "reasons": reasons, "duration_ms": payload["telemetry"]["duration_ms"], "difficulty": difficulty, "candidate_count": ingested.get("candidate_count", 0), "result_id": payload["result_id"]}
            _persist_telemetry(base, batch_id=batch_id, telemetry=telemetry)
            results.append({"batch_id": batch_id, **telemetry})
        except (ValueError, json.JSONDecodeError, PopulationScopeError) as exc:
            message = str(exc)[:500]
            code = message.split(":", 1)[0] if ":" in message else "INVALID_RESULT"
            telemetry = {"quality": "INVALID_RESULT", "reasons": [message], "duration_ms": round((time.perf_counter() - started) * 1000, 2)}
            record_comprehension_attempt(base, attempt_id=attempt_id, batch_id=batch_id, result_id=locals().get("payload", {}).get("result_id"), provider_type="local_ai", provider_model=locals().get("selected_model") or health.get("model"), worker_identity=worker_identity, source_revision=locals().get("packet", {}).get("source_revision", "UNKNOWN"), packet_version=locals().get("packet", {}).get("packet_version"), prompt_contract_version=locals().get("packet", {}).get("prompt_contract_version"), packet_hash=locals().get("packet_hash"), raw_output=response.get("text") if "response" in locals() and response else None, validation_state="INVALID_RESULT", validation_code=code, validation_message=message, telemetry=telemetry)
            _persist_telemetry(base, batch_id=batch_id, telemetry=telemetry)
            results.append({"batch_id": batch_id, **telemetry})
            # Invalid packet-local citations are a direct circuit-breaker event.
            # Preserve the raw attempt and stop this bounded checkpoint.
            if code in {"MISSING_EVIDENCE_CITATION", "MALFORMED_EVIDENCE_ID", "EVIDENCE_ID_NOT_IN_PACKET", "EVIDENCE_ID_UNKNOWN", "EVIDENCE_NOT_AUTHORIZED_FOR_ASSERTION"}:
                break
    return {"status": "COMPLETED", "provider_health": health, "work_units": results, "counts": {quality: sum(1 for row in results if row.get("quality") == quality) for quality in sorted(QUALITY)}}


def review_queue(root: str | Path) -> dict[str, Any]:
    with connect(_root(root), create=False) as connection:
        rows = connection.execute("SELECT batch_id,state,result_state,failure_reason,attempt_count,updated_at FROM comprehension_batches WHERE state IN ('FAILED','RETRYABLE') OR result_state IN ('PARTIAL_CANDIDATE','NEEDS_MORE_CONTEXT','INVALID_RESULT','CONFLICT_REVIEW_REQUIRED','HIGHER_REASONING_REQUIRED','HUMAN_REVIEW_REQUIRED') ORDER BY updated_at DESC").fetchall()
        return {"results": [dict(row) for row in rows], "count": len(rows)}
