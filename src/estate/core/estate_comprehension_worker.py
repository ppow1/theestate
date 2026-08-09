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
    PopulationScopeError, batch_packet, ingest_result, next_batch, validate_result,
)
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
        "Use only supplied asset_id values and cite evidence_refs using supplied asset_id values. "
        "Unknown or ambiguous owner/purpose must remain null and be explained in unresolved_questions. "
        "Every non-null purpose, owner_candidate, or summary needs at least one evidence_refs value. "
        "The lifecycle must remain CANDIDATE. Contract and exact fields: "
        '{"contract":"estate.troubleshooting.comprehension.result.v1",'
        '"result_id":"provider-generated", "batch_id":"same batch", "source_revision":"same revision",'
        '"provider":{"type":"local_ai","model":"model","worker_identity":"worker"},'
        '"quality":"PARTIAL_CANDIDATE", "items":[{"asset_id":"supplied",'
        '"lifecycle":"CANDIDATE","purpose":null,"owner_candidate":null,"summary":null,'
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
    supplied = {a["asset_id"] for a in packet.get("assets", [])}
    reasons: list[str] = []
    for item in payload.get("items", []):
        refs = item.get("evidence_refs") or []
        if not refs and any(item.get(k) for k in ("purpose", "owner_candidate", "summary")):
            reasons.append(f"{item.get('asset_id')}: assertion without evidence_refs")
        if not set(refs).issubset(supplied):
            reasons.append(f"{item.get('asset_id')}: evidence_refs outside supplied packet")
    if payload.get("context_requests"):
        return "NEEDS_MORE_CONTEXT", reasons
    if reasons:
        return "PARTIAL_CANDIDATE", reasons
    return "ACCEPTED_CANDIDATE", []


def _persist_telemetry(root: Path, *, batch_id: str, telemetry: dict[str, Any]) -> None:
    with connect(root, create=False) as connection:
        state = "RETRYABLE" if telemetry["quality"] == "RETRYABLE_PROVIDER_FAILURE" else ("FAILED" if telemetry["quality"] == "INVALID_RESULT" else None)
        if state:
            connection.execute("UPDATE comprehension_batches SET state=?, result_state=?, failure_reason=?, updated_at=? WHERE batch_id=?", (state, telemetry["quality"], "; ".join(telemetry.get("reasons", [])) or None, _now(), batch_id))
        else:
            connection.execute("UPDATE comprehension_batches SET result_state=?, failure_reason=?, updated_at=? WHERE batch_id=?", (telemetry["quality"], "; ".join(telemetry.get("reasons", [])) or None, _now(), batch_id))


def run_local(root: str | Path, *, limit: int = 1, max_bytes: int = 65536, model: str | None = None, worker_identity: str = "estate-local-comprehension-worker", asset_prefix: str | None = None, timeout: float = 120.0) -> dict[str, Any]:
    base = _root(root)
    health = provider_status(timeout=min(timeout, 4.0), model=model)
    if not health["available"]:
        return {"status": "PROVIDER_UNAVAILABLE", "provider_health": health, "work_units": []}
    results: list[dict[str, Any]] = []
    adapter = LocalOllamaAdapter(timeout=timeout)
    for _ in range(max(1, min(limit, 20))):
        batch = next_batch(base, limit=1, provider_type="local_ai", provider_model=health.get("model"), worker_identity=worker_identity, asset_prefix=asset_prefix)
        if batch.get("status") == "NO_WORK":
            break
        batch_id = batch["batch_id"]
        started = time.perf_counter()
        try:
            packet = batch_packet(base, batch_id, max_bytes=max_bytes)
            difficulty = difficulty_for(packet)
            response = adapter.generate(resident="comprehension-worker", prompt=_prompt(packet, difficulty), model=health.get("model"))
            if not response.get("ok"):
                telemetry = {"quality": "RETRYABLE_PROVIDER_FAILURE", "reasons": [response.get("metadata", {}).get("fallback_reason", "local provider failed")], "duration_ms": round((time.perf_counter() - started) * 1000, 2), "difficulty": difficulty}
                _persist_telemetry(base, batch_id=batch_id, telemetry=telemetry)
                results.append({"batch_id": batch_id, **telemetry})
                continue
            payload = _extract_json(response["text"])
            payload["batch_id"] = batch_id
            payload["source_revision"] = packet["source_revision"]
            # Provider result IDs are advisory only. Estate owns identity so a
            # model placeholder cannot collide across independent work units.
            payload["result_id"] = _estate_result_id(batch_id, payload)
            payload["provider"] = {"type": "local_ai", "model": health.get("model"), "worker_identity": worker_identity}
            for item in payload.get("items", []):
                item.setdefault("lifecycle", "CANDIDATE")
                item.setdefault("evidence_refs", [])
            quality, reasons = _quality(payload, packet)
            payload["quality"] = quality
            payload["telemetry"] = {"difficulty": difficulty, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "packet_bytes": len(json.dumps(packet).encode())}
            payload["unsupported_assertions"] = payload.get("unsupported_assertions", [])
            if quality == "PARTIAL_CANDIDATE":
                # Preserve a structured candidate but make the review state explicit.
                payload["context_requests"] = payload.get("context_requests", [])
            validate_result(base, payload)
            ingested = ingest_result(base, payload)
            telemetry = {"quality": quality, "reasons": reasons, "duration_ms": payload["telemetry"]["duration_ms"], "difficulty": difficulty, "candidate_count": ingested.get("candidate_count", 0), "result_id": payload["result_id"]}
            _persist_telemetry(base, batch_id=batch_id, telemetry=telemetry)
            results.append({"batch_id": batch_id, **telemetry})
        except (ValueError, json.JSONDecodeError, PopulationScopeError) as exc:
            telemetry = {"quality": "INVALID_RESULT", "reasons": [str(exc)[:500]], "duration_ms": round((time.perf_counter() - started) * 1000, 2)}
            _persist_telemetry(base, batch_id=batch_id, telemetry=telemetry)
            results.append({"batch_id": batch_id, **telemetry})
    return {"status": "COMPLETED", "provider_health": health, "work_units": results, "counts": {quality: sum(1 for row in results if row.get("quality") == quality) for quality in sorted(QUALITY)}}


def review_queue(root: str | Path) -> dict[str, Any]:
    with connect(_root(root), create=False) as connection:
        rows = connection.execute("SELECT batch_id,state,result_state,failure_reason,attempt_count,updated_at FROM comprehension_batches WHERE state IN ('FAILED','RETRYABLE') OR result_state IN ('PARTIAL_CANDIDATE','NEEDS_MORE_CONTEXT','INVALID_RESULT','CONFLICT_REVIEW_REQUIRED','HIGHER_REASONING_REQUIRED','HUMAN_REVIEW_REQUIRED') ORDER BY updated_at DESC").fetchall()
        return {"results": [dict(row) for row in rows], "count": len(rows)}
