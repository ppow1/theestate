"""Local Research Office evidence management and source intelligence runtime."""
from __future__ import annotations

import hashlib, json, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from estate.core.paths import ESTATE_ROOT

SCHEMA_VERSION = "estate.research_office.v1"
STORE = Path("runtime/research_office")
QUALITY = {"primary", "secondary", "tertiary", "vendor", "community", "unknown"}
CONFIDENCE = {"low", "medium", "high"}
SOURCE_TYPES = {"web", "uploaded_document", "technical_paper", "product_finding", "manual_evidence"}


def root_path(root: str | Path | None = None) -> Path:
    return Path(root) if root else (ESTATE_ROOT if ESTATE_ROOT.exists() else Path.cwd())


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:48] or "research"


def digest(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


class ResearchOfficeRuntime:
    def __init__(self, root: str | Path | None = None):
        self.root = root_path(root)
        self.base = self.root / STORE

    def _path(self, kind: str, item_id: str) -> Path:
        return self.base / kind / f"{item_id}.json"

    def _all(self, kind: str) -> list[dict[str, Any]]:
        folder = self.base / kind
        return [read_json(p, {}) for p in sorted(folder.glob("*.json"))] if folder.exists() else []

    def create_request(self, title: str, question: str, requested_by: str, scope: str = "external_research", tags: list[str] | None = None) -> dict[str, Any]:
        item_id = f"rr-{slug(title)}-{uuid4().hex[:8]}"
        payload = {"schema_version": SCHEMA_VERSION, "request_id": item_id, "title": title, "question": question, "scope": scope, "requested_by": requested_by, "status": "open", "created_at": now(), "updated_at": now(), "tags": tags or [], "knowledge_boundary": "External research evidence is kept distinct from accepted institutional truth."}
        write_json(self._path("requests", item_id), payload); self._refresh_index(); return payload

    def intake_source(self, request_id: str, title: str, source_type: str, locator: str, summary: str, *, publication_date: str | None = None, retrieval_date: str | None = None, provenance: str = "manual_intake", quality_rating: str = "unknown", confidence: str = "medium", citation: str | None = None, content_hash: str | None = None) -> dict[str, Any]:
        if source_type not in SOURCE_TYPES: raise ValueError("unknown source_type")
        if quality_rating not in QUALITY: raise ValueError("unknown quality_rating")
        if confidence not in CONFIDENCE: raise ValueError("unknown confidence")
        retrieval_date = retrieval_date or now()[:10]
        content_hash = content_hash or digest(locator, title, publication_date or "")
        for src in self._all("sources"):
            if src.get("content_hash") == content_hash or (src.get("locator") == locator and locator):
                src.setdefault("linked_request_ids", [])
                if request_id not in src["linked_request_ids"]: src["linked_request_ids"].append(request_id)
                src["duplicate_notice"] = "Existing source reused; duplicate intake preserved by request link."
                write_json(self._path("sources", src["source_id"]), src); self._refresh_index(); return src
        item_id = f"src-{uuid4().hex[:10]}"
        payload = {"schema_version": SCHEMA_VERSION, "source_id": item_id, "linked_request_ids": [request_id], "title": title, "source_type": source_type, "locator": locator, "summary": summary, "publication_date": publication_date, "retrieval_date": retrieval_date, "provenance": provenance, "quality_rating": quality_rating, "confidence": confidence, "citation": citation or locator, "content_hash": content_hash, "created_at": now()}
        write_json(self._path("sources", item_id), payload); self._refresh_index(); return payload

    def record_finding(self, request_id: str, statement: str, source_ids: list[str], *, claim_type: str = "evidence", confidence: str = "medium", conflicting_source_ids: list[str] | None = None, inference: str | None = None, stale_after_days: int = 180) -> dict[str, Any]:
        if confidence not in CONFIDENCE: raise ValueError("unknown confidence")
        sources = {s["source_id"] for s in self._all("sources")}
        missing = [s for s in source_ids + (conflicting_source_ids or []) if s not in sources]
        if missing: raise ValueError(f"unknown source ids: {missing}")
        fid = f"find-{uuid4().hex[:10]}"; created = now()
        payload = {"schema_version": SCHEMA_VERSION, "finding_id": fid, "request_id": request_id, "statement": statement, "claim_type": claim_type, "confidence": confidence, "source_ids": source_ids, "citation_links": [f"sources/{s}.json" for s in source_ids], "conflicting_source_ids": conflicting_source_ids or [], "inference": inference, "created_at": created, "reviewed_at": created, "stale_after_days": stale_after_days, "stale": False}
        write_json(self._path("findings", fid), payload); self._refresh_index(); return payload

    def recommend(self, request_id: str, recommendation: str, finding_ids: list[str], rationale: str) -> dict[str, Any]:
        findings = {f["finding_id"]: f for f in self._all("findings")}
        missing = [f for f in finding_ids if f not in findings]
        if missing: raise ValueError(f"unsupported recommendation; missing findings: {missing}")
        unsupported = [f for f in finding_ids if not findings[f].get("source_ids")]
        if unsupported: raise ValueError(f"unsupported recommendation; uncited findings: {unsupported}")
        rid = f"rec-{uuid4().hex[:10]}"
        payload = {"schema_version": SCHEMA_VERSION, "recommendation_id": rid, "request_id": request_id, "recommendation": recommendation, "finding_ids": finding_ids, "rationale": rationale, "created_at": now(), "evidence_notice": "Recommendation is derived from external evidence and is not institutional truth until separately accepted."}
        write_json(self._path("recommendations", rid), payload); self._refresh_index(); return payload

    def create_monitor(self, request_id: str, topic: str, cadence: str, source_queries: list[str]) -> dict[str, Any]:
        mid = f"mon-{slug(topic)}-{uuid4().hex[:8]}"
        payload = {"schema_version": SCHEMA_VERSION, "monitoring_id": mid, "request_id": request_id, "topic": topic, "cadence": cadence, "source_queries": source_queries, "status": "watching", "last_checked_at": None, "next_check_hint": cadence, "runtime_reuse": "Use existing background operations watches; no Research Office scheduler is introduced.", "created_at": now()}
        write_json(self._path("monitoring", mid), payload); self._refresh_index(); return payload

    def review(self) -> dict[str, Any]:
        findings = self._all("findings"); cutoff = now()
        stale = []
        for f in findings:
            age = parse_time(cutoff) - parse_time(f["reviewed_at"])
            f["stale"] = age > timedelta(days=int(f.get("stale_after_days", 180)))
            if f["stale"]: stale.append(f["finding_id"])
            write_json(self._path("findings", f["finding_id"]), f)
        unsupported = [r["recommendation_id"] for r in self._all("recommendations") if not r.get("finding_ids")]
        conflicts = [f["finding_id"] for f in findings if f.get("conflicting_source_ids")]
        report = {"schema_version": SCHEMA_VERSION, "generated_at": now(), "request_count": len(self._all("requests")), "source_count": len(self._all("sources")), "finding_count": len(findings), "recommendation_count": len(self._all("recommendations")), "monitoring_count": len(self._all("monitoring")), "stale_findings": stale, "conflicting_findings": conflicts, "unsupported_recommendations": unsupported, "truth_boundary": "Research Office records are external evidence, inference, and recommendations; they do not update the Estate knowledge index as accepted truth."}
        write_json(self.base / "reports" / "latest_status.json", report); return report

    def inspect_source(self, source_id: str) -> dict[str, Any]:
        source = read_json(self._path("sources", source_id), None)
        if not source: raise ValueError("source not found")
        source["findings"] = [f for f in self._all("findings") if source_id in f.get("source_ids", []) or source_id in f.get("conflicting_source_ids", [])]
        return source

    def report_markdown(self) -> str:
        s = self.review()
        lines = ["# WP-4015 Research Office Runtime Validation", "", f"Generated: {s['generated_at']}", "", "## Summary", f"- Requests: {s['request_count']}", f"- Sources: {s['source_count']}", f"- Findings: {s['finding_count']}", f"- Recommendations: {s['recommendation_count']}", f"- Monitoring records: {s['monitoring_count']}", "", "## Boundary", f"- {s['truth_boundary']}", "", "## Validation Signals", f"- Stale findings: {s['stale_findings']}", f"- Conflicting findings: {s['conflicting_findings']}", f"- Unsupported recommendations: {s['unsupported_recommendations']}"]
        return "\n".join(lines) + "\n"

    def _refresh_index(self) -> None:
        payload = {"schema_version": SCHEMA_VERSION, "projection_type": "external_research_distinct_from_institutional_truth", "updated_at": now(), "requests": [r.get("request_id") for r in self._all("requests")], "sources": [s.get("source_id") for s in self._all("sources")], "findings": [f.get("finding_id") for f in self._all("findings")], "recommendations": [r.get("recommendation_id") for r in self._all("recommendations")], "monitoring": [m.get("monitoring_id") for m in self._all("monitoring")]}
        write_json(self.root / "runtime/search/research_office_external_evidence_index.json", payload)


def format_summary(report: dict[str, Any]) -> str:
    return (f"Research Office: {report['request_count']} requests, {report['source_count']} sources, "
            f"{report['finding_count']} findings, {len(report['conflicting_findings'])} conflicts, "
            f"{len(report['stale_findings'])} stale findings. External evidence remains distinct from institutional truth.")
